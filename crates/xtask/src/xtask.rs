//! See https://github.com/matklad/cargo-xtask
//! This project now has a Justfile and a Makefile.
//! Commands here are not always intended to be run directly
//! by the user - add commands here which otherwise might
//! end up as a lot of nontrivial bash code.

use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::process::Command;

use anyhow::{Context, Result};
use camino::{Utf8Path, Utf8PathBuf};
use fn_error_context::context;
use xshell::{cmd, Shell};

mod man;

const NAME: &str = "command-line-assistant";
const TAR_REPRODUCIBLE_OPTS: &[&str] = &[
    "--sort=name",
    "--owner=0",
    "--group=0",
    "--numeric-owner",
    "--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime",
];

fn main() {
    use std::io::Write as _;

    use owo_colors::OwoColorize;
    if let Err(e) = try_main() {
        let mut stderr = anstream::stderr();
        // Don't panic if writing fails.
        let _ = writeln!(stderr, "{}{:#}", "error: ".red(), e);
        std::process::exit(1);
    }
}

#[allow(clippy::type_complexity)]
const TASKS: &[(&str, fn(&Shell) -> Result<()>)] = &[
    ("manpages", man::generate_man_pages),
    ("update-generated", update_generated),
    ("package", package),
    ("package-srpm", package_srpm),
    ("spec", spec),
];

fn try_main() -> Result<()> {
    // Ensure our working directory is the toplevel (if we're in a git repo)
    {
        if let Ok(toplevel_path) = Command::new("git")
            .args(["rev-parse", "--show-toplevel"])
            .output()
        {
            if toplevel_path.status.success() {
                let path = String::from_utf8(toplevel_path.stdout)?;
                std::env::set_current_dir(path.trim()).context("Changing to toplevel")?;
            }
        }
        // Otherwise verify we're in the toplevel
        if !Utf8Path::new("README.md")
            .try_exists()
            .context("Checking for toplevel")?
        {
            anyhow::bail!("Not in toplevel")
        }
    }

    let task = std::env::args().nth(1);

    let sh = xshell::Shell::new()?;
    if let Some(cmd) = task.as_deref() {
        let f = TASKS
            .iter()
            .find_map(|(k, f)| (*k == cmd).then_some(*f))
            .unwrap_or(print_help);
        f(&sh)
    } else {
        print_help(&sh)?;
        Ok(())
    }
}

fn gitrev_to_version(v: &str) -> String {
    let v = v.trim().trim_start_matches('v');
    v.replace('-', ".")
}

#[context("Finding gitrev")]
fn gitrev(sh: &Shell) -> Result<String> {
    if let Ok(rev) = cmd!(sh, "git describe --tags --exact-match")
        .ignore_stderr()
        .read()
    {
        Ok(gitrev_to_version(&rev))
    } else {
        // Grab the abbreviated commit
        let abbrev_commit = cmd!(sh, "git rev-parse HEAD")
            .read()?
            .chars()
            .take(10)
            .collect::<String>();
        let timestamp = git_timestamp(sh)?;
        // We always inject the timestamp first to ensure that newer is better.
        Ok(format!("{timestamp}.g{abbrev_commit}"))
    }
}

/// Return a string formatted version of the git commit timestamp, up to the minute
/// but not second because, well, we're not going to build more than once a second.
#[context("Finding git timestamp")]
fn git_timestamp(sh: &Shell) -> Result<String> {
    let ts = cmd!(sh, "git show -s --format=%ct").read()?;
    let ts = ts.trim().parse::<i64>()?;
    let ts = chrono::DateTime::from_timestamp(ts, 0)
        .ok_or_else(|| anyhow::anyhow!("Failed to parse timestamp"))?;
    Ok(ts.format("%Y%m%d%H%M").to_string())
}

struct Package {
    version: String,
    srcpath: Utf8PathBuf,
    vendorpath: Utf8PathBuf,
}

/// Return the timestamp of the latest git commit in seconds since the Unix epoch.
fn git_source_date_epoch(dir: &Utf8Path) -> Result<u64> {
    let o = Command::new("git")
        .args(["log", "-1", "--pretty=%ct"])
        .current_dir(dir)
        .output()?;
    if !o.status.success() {
        anyhow::bail!("git exited with an error: {:?}", o);
    }
    let buf = String::from_utf8(o.stdout).context("Failed to parse git log output")?;
    let r = buf.trim().parse()?;
    Ok(r)
}

/// When using cargo-vendor-filterer --format=tar, the config generated has a bogus source
/// directory. This edits it to refer to vendor/ as a stable relative reference.
#[context("Editing vendor config")]
fn edit_vendor_config(config: &str) -> Result<String> {
    let mut config: toml::Value = toml::from_str(config)?;
    let config = config.as_table_mut().unwrap();
    let source_table = config.get_mut("source").unwrap();
    let source_table = source_table.as_table_mut().unwrap();
    let vendored_sources = source_table.get_mut("vendored-sources").unwrap();
    let vendored_sources = vendored_sources.as_table_mut().unwrap();
    let previous =
        vendored_sources.insert("directory".into(), toml::Value::String("vendor".into()));
    assert!(previous.is_some());

    Ok(config.to_string())
}

#[context("Packaging")]
fn impl_package(sh: &Shell) -> Result<Package> {
    let source_date_epoch = git_source_date_epoch(".".into())?;
    let v = gitrev(sh)?;

    let namev = format!("{NAME}-{v}");
    let p = Utf8Path::new("target").join(format!("{namev}.tar"));
    let prefix = format!("{namev}/");
    cmd!(sh, "git archive --format=tar --prefix={prefix} -o {p} HEAD").run()?;
    // Generate the vendor directory now, as we want to embed the generated config to use
    // it in our source.
    let vendorpath = Utf8Path::new("target").join(format!("{namev}-vendor.tar.zstd"));
    let vendor_config = cmd!(
        sh,
        "cargo vendor-filterer --prefix=vendor --format=tar.zstd {vendorpath}"
    )
    .read()?;
    let vendor_config = edit_vendor_config(&vendor_config)?;
    // Append .cargo/vendor-config.toml (a made up filename) into the tar archive.
    {
        let tmpdir = tempfile::tempdir_in("target")?;
        let tmpdir_path = tmpdir.path();
        let path = tmpdir_path.join("vendor-config.toml");
        std::fs::write(&path, vendor_config)?;
        let source_date_epoch = format!("{source_date_epoch}");
        cmd!(
            sh,
            "tar -r -C {tmpdir_path} {TAR_REPRODUCIBLE_OPTS...} --mtime=@{source_date_epoch} --transform=s,^,{prefix}.cargo/, -f {p} vendor-config.toml"
        )
        .run()?;
    }
    // Compress with zstd
    let srcpath: Utf8PathBuf = format!("{p}.zstd").into();
    cmd!(sh, "zstd --rm -f {p} -o {srcpath}").run()?;

    Ok(Package {
        version: v,
        srcpath,
        vendorpath,
    })
}

fn package(sh: &Shell) -> Result<()> {
    let p = impl_package(sh)?.srcpath;
    println!("Generated: {p}");
    Ok(())
}

fn update_spec(sh: &Shell) -> Result<Utf8PathBuf> {
    let p = Utf8Path::new("target");
    let pkg = impl_package(sh)?;
    let srcpath = pkg.srcpath.file_name().unwrap();
    let v = pkg.version;
    let src_vendorpath = pkg.vendorpath.file_name().unwrap();
    {
        let specin = File::open(format!("packaging/{NAME}.spec"))
            .map(BufReader::new)
            .context("Opening spec")?;
        let mut o = File::create(p.join(format!("{NAME}.spec"))).map(BufWriter::new)?;
        for line in specin.lines() {
            let line = line?;
            if line.starts_with("Version:") {
                writeln!(o, "# Replaced by cargo xtask spec")?;
                writeln!(o, "Version: {v}")?;
            } else if line.starts_with("Source0") {
                writeln!(o, "Source0: {srcpath}")?;
            } else if line.starts_with("Source1") {
                writeln!(o, "Source1: {src_vendorpath}")?;
            } else {
                writeln!(o, "{line}")?;
            }
        }
    }
    let spec_path = p.join(format!("{NAME}.spec"));
    Ok(spec_path)
}

fn spec(sh: &Shell) -> Result<()> {
    let s = update_spec(sh)?;
    println!("Generated: {s}");
    Ok(())
}

fn impl_srpm(sh: &Shell) -> Result<Utf8PathBuf> {
    {
        let _g = sh.push_dir("target");
        for name in sh.read_dir(".")? {
            if let Some(name) = name.to_str() {
                if name.ends_with(".src.rpm") {
                    sh.remove_path(name)?;
                }
            }
        }
    }
    let pkg = impl_package(sh)?;
    let td = tempfile::tempdir_in("target").context("Allocating tmpdir")?;
    let td = td.keep();
    let td: &Utf8Path = td.as_path().try_into().unwrap();
    let srcpath = &pkg.srcpath;
    cmd!(sh, "mv {srcpath} {td}").run()?;
    let v = pkg.version;
    let src_vendorpath = &pkg.vendorpath;
    cmd!(sh, "mv {src_vendorpath} {td}").run()?;
    {
        let specin = File::open(format!("packaging/{NAME}.spec"))
            .map(BufReader::new)
            .context("Opening spec")?;
        let mut o = File::create(td.join(format!("{NAME}.spec"))).map(BufWriter::new)?;
        for line in specin.lines() {
            let line = line?;
            if line.starts_with("Version:") {
                writeln!(o, "# Replaced by cargo xtask package-srpm")?;
                writeln!(o, "Version: {v}")?;
            } else {
                writeln!(o, "{line}")?;
            }
        }
    }
    let d = sh.push_dir(td);
    let mut cmd = cmd!(sh, "rpmbuild");
    for k in [
        "_sourcedir",
        "_specdir",
        "_builddir",
        "_srcrpmdir",
        "_rpmdir",
    ] {
        cmd = cmd.arg("--define");
        cmd = cmd.arg(format!("{k} {td}"));
    }
    cmd.arg("--define")
        .arg(format!("_buildrootdir {td}/.build"))
        .args(["-bs", &format!("{NAME}.spec")])
        .run()?;
    drop(d);
    let mut srpm = None;
    for e in std::fs::read_dir(td)? {
        let e = e?;
        let n = e.file_name();
        let Some(n) = n.to_str() else {
            continue;
        };
        if n.ends_with(".src.rpm") {
            srpm = Some(td.join(n));
            break;
        }
    }
    let srpm = srpm.ok_or_else(|| anyhow::anyhow!("Failed to find generated .src.rpm"))?;
    let dest = Utf8Path::new("target").join(srpm.file_name().unwrap());
    std::fs::rename(&srpm, &dest)?;
    Ok(dest)
}

fn package_srpm(sh: &Shell) -> Result<()> {
    let srpm = impl_srpm(sh)?;
    println!("Generated: {srpm}");
    Ok(())
}

/// Update all generated files
/// This is the main command developers should use to update generated content.
/// It handles:
/// - Creating new man page templates for new commands
/// - Syncing CLI options to existing man pages
/// - Updating JSON schema files
#[context("Updating generated files")]
fn update_generated(sh: &Shell) -> Result<()> {
    // Update man pages (create new templates + sync options)
    man::update_manpages(sh)?;

    Ok(())
}

fn print_help(_sh: &Shell) -> Result<()> {
    println!("Tasks:");
    for (name, _) in TASKS {
        println!("  - {name}");
    }
    Ok(())
}
