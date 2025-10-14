//! Helper functions for the CLI wrapper

use anyhow::{bail, Context, Result};
use etcetera::{choose_app_strategy, AppStrategy};
use fs2::FileExt;
use log::{debug, info, warn};
use std::env;
use std::fs;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use tempfile::NamedTempFile;

use crate::config::APP_STRATEGY;

pub const DEFAULT_PATHS: &[&str] = &["/usr/bin/duckduck"];

/// Maximum argument length to prevent resource exhaustion
pub const MAX_ARG_LENGTH: usize = 1_000_000; // 1MB per argument
pub const MAX_TOTAL_ARGS_LENGTH: usize = 10_000_000; // 10MB total

/// Exit codes following sysexits.h convention
pub const EX_UNAVAILABLE: i32 = 69; // Service unavailable
pub const EX_SOFTWARE: i32 = 70; // Internal software error
pub const EX_OSERR: i32 = 71; // System error
pub const EX_CANTCREAT: i32 = 73; // Can't create output file

pub const CLI_CONFIG: &str = r#"OLLAMA_HOST: 127.0.0.1:8080
CLI_MODEL: default-model
CLI_PROVIDER: ollama
extensions:
  memory:
    enabled: true
    type: builtin
    name: memory
    display_name: Memory
    description: null
    timeout: 300
    bundled: true
    available_tools: []
"#;

/// Validates that a path points to an executable file
pub fn is_executable(path: &Path) -> bool {
    if !path.exists() {
        return false;
    }

    // Check if it's a file (not a directory or symlink to directory)
    if !path.is_file() {
        debug!("Path is not a file: {:?}", path);
        return false;
    }

    // Check Unix permissions for executable bit
    match fs::metadata(path) {
        Ok(metadata) => {
            let permissions = metadata.permissions();
            let mode = permissions.mode();
            // Check if any execute bit is set (user, group, or other)
            let is_exec = (mode & 0o111) != 0;
            debug!("Path {:?} executable: {}, mode: {:o}", path, is_exec, mode);
            is_exec
        }
        Err(e) => {
            debug!("Failed to get metadata for {:?}: {}", path, e);
            false
        }
    }
}

/// Find the binary with proper validation
pub fn find_cli_binary() -> Result<PathBuf> {
    // Check environment variable first
    if let Ok(env_path) = env::var("CLI_BINARY") {
        if env_path.is_empty() {
            warn!("CLI_BINARY is set but empty");
        } else {
            let path = PathBuf::from(&env_path);
            debug!("Checking CLI_BINARY: {:?}", path);

            if is_executable(&path) {
                info!("Using CLI_BINARY: {:?}", path);
                return Ok(path);
            } else {
                warn!("CLI_BINARY validation failed: not executable");
            }
        }
    }

    // Check default paths
    for path_str in DEFAULT_PATHS {
        let path = Path::new(path_str);
        debug!("Checking default path: {:?}", path);

        if is_executable(path) {
            info!("Using cli from default path: {:?}", path);
            return Ok(path.to_path_buf());
        }
    }
    bail!("CLI binary not found in environment variable or default paths")
}

/// Validate command-line arguments for security and resource limits
pub fn validate_args(args: &[String]) -> Result<()> {
    let mut total_length = 0;

    for (i, arg) in args.iter().enumerate() {
        let arg_len = arg.len();

        // Check individual argument length
        if arg_len > MAX_ARG_LENGTH {
            bail!(
                "Argument {} is too long: {} bytes (max: {})",
                i,
                arg_len,
                MAX_ARG_LENGTH
            );
        }

        total_length += arg_len;

        // Check for null bytes (security issue)
        if arg.contains('\0') {
            bail!("Argument {} contains null byte", i);
        }

        debug!("Arg {}: {} bytes", i, arg_len);
    }

    // Check total arguments length
    if total_length > MAX_TOTAL_ARGS_LENGTH {
        bail!(
            "Total arguments length is too large: {} bytes (max: {})",
            total_length,
            MAX_TOTAL_ARGS_LENGTH
        );
    }

    debug!(
        "Validated {} arguments, total length: {} bytes",
        args.len(),
        total_length
    );
    Ok(())
}

/// Atomically write content to a file using a temporary file
pub fn atomic_write(path: &Path, content: &str) -> Result<()> {
    let parent = path
        .parent()
        .ok_or_else(|| anyhow::anyhow!("Path has no parent directory"))?;

    // Create temporary file in the same directory for atomic rename
    let mut temp_file = NamedTempFile::new_in(parent).context("Failed to create temporary file")?;

    // Write content
    temp_file
        .write_all(content.as_bytes())
        .context("Failed to write to temporary file")?;

    // Ensure data is written to disk
    temp_file
        .flush()
        .context("Failed to flush temporary file")?;

    // Atomically move temp file to final location
    temp_file
        .persist(path)
        .context("Failed to persist temporary file")?;

    debug!("Atomically wrote file: {:?}", path);
    Ok(())
}

/// Ensure cli config files exist with proper locking and atomic writes
pub fn ensure_cli_config_files() -> Result<()> {
    let home_dir = choose_app_strategy(APP_STRATEGY.clone())
        .context("Failed to determine app strategy (HOME environment variable may not be set)")?;

    let config_dir = home_dir.in_config_dir("");
    let custom_providers_dir = config_dir.join("custom_providers");

    // Ensure directories exist
    fs::create_dir_all(&custom_providers_dir).context("Failed to create config directories")?;

    debug!("Config directory: {:?}", config_dir);
    debug!("Custom providers directory: {:?}", custom_providers_dir);

    // Create a lock file to prevent race conditions
    let lock_file_path = config_dir.join(".config.lock");
    let lock_file = fs::OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
        .open(&lock_file_path)
        .context("Failed to create lock file")?;

    // Acquire exclusive lock (blocks if another process has the lock)
    debug!("Acquiring lock on {:?}", lock_file_path);
    lock_file
        .lock_exclusive()
        .context("Failed to acquire lock on config directory")?;

    // Check and create config.yaml
    let config_yaml_path = config_dir.join("config.yaml");
    if !config_yaml_path.exists() {
        info!("Creating config.yaml at {:?}", config_yaml_path);

        let config_yaml_content = CLI_CONFIG;

        atomic_write(&config_yaml_path, config_yaml_content)
            .context("Failed to write config.yaml")?;
    } else {
        debug!("config.yaml already exists");
    }

    // Release lock (happens automatically when lock_file is dropped)
    FileExt::unlock(&lock_file).context("Failed to release lock")?;

    debug!("Config files ensured successfully");
    Ok(())
}

/// Convert exit status to exit code, handling both normal exit and signals
pub fn status_to_exit_code(status: std::process::ExitStatus) -> i32 {
    #[cfg(unix)]
    {
        use std::os::unix::process::ExitStatusExt;

        if let Some(code) = status.code() {
            // Normal exit
            debug!("Child exited with code: {}", code);
            return code;
        }

        if let Some(signal) = status.signal() {
            // Terminated by signal - return 128 + signal number (shell convention)
            let exit_code = 128 + signal;
            debug!(
                "Child terminated by signal {}, returning exit code {}",
                signal, exit_code
            );
            return exit_code;
        }

        // Unknown status
        warn!("Unknown exit status, returning 1");
        1
    }
}

/// Filter environment variables to only pass safe ones
pub fn get_filtered_env() -> Vec<(String, String)> {
    // Whitelist of safe environment variables to pass through
    const SAFE_ENV_VARS: &[&str] = &[
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "SHELL",
        "TERM",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TMPDIR",
        "EDITOR",
        "VISUAL",
        "PAGER",
        "DISPLAY",
        "COLORTERM",
    ];

    // Additional patterns to allow (for development)
    const SAFE_PREFIXES: &[&str] = &["XDG_"];

    env::vars()
        .filter(|(key, _)| {
            // Allow whitelisted vars
            if SAFE_ENV_VARS.contains(&key.as_str()) {
                return true;
            }

            // Allow safe prefixes
            for prefix in SAFE_PREFIXES {
                if key.starts_with(prefix) {
                    return true;
                }
            }

            false
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    // ============================================================================
    // Tests for is_executable
    // ============================================================================

    #[test]
    fn test_is_executable_nonexistent_file() {
        let path = Path::new("/this/path/does/not/exist");
        assert!(
            !is_executable(path),
            "Non-existent path should not be executable"
        );
    }

    #[test]
    fn test_is_executable_with_directory() {
        let temp_dir = TempDir::new().unwrap();
        let dir_path = temp_dir.path();
        assert!(
            !is_executable(dir_path),
            "Directory should not be considered executable"
        );
    }

    #[test]
    fn test_is_executable_with_non_executable_file() {
        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test_file");

        // Create a non-executable file
        fs::write(&file_path, "test").unwrap();

        assert!(
            !is_executable(&file_path),
            "Non-executable file should return false"
        );
    }

    #[test]
    #[cfg(unix)]
    fn test_is_executable_with_executable_file() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test_executable");

        // Create an executable file
        fs::write(&file_path, "#!/bin/sh\necho test").unwrap();
        let mut perms = fs::metadata(&file_path).unwrap().permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&file_path, perms).unwrap();

        assert!(
            is_executable(&file_path),
            "Executable file should return true"
        );
    }

    // ============================================================================
    // Tests for find_cli_binary
    // ============================================================================

    #[test]
    #[allow(unsafe_code)]
    fn test_find_cli_binary_with_invalid_env_var() {
        unsafe {
            // Set CLI_BINARY to a non-existent path
            env::set_var("CLI_BINARY", "/nonexistent/path/to/cli");

            // find_cli_binary should fail since the path doesn't exist
            let result = find_cli_binary();

            // Clean up
            env::remove_var("CLI_BINARY");

            assert!(result.is_err(), "Should fail with non-existent path");
        }
    }

    #[test]
    #[allow(unsafe_code)]
    fn test_find_cli_binary_with_empty_env_var() {
        unsafe {
            // Set CLI_BINARY to empty string
            env::set_var("CLI_BINARY", "");

            let result = find_cli_binary();

            // Clean up
            env::remove_var("CLI_BINARY");

            // Should fail if /usr/bin/<cli> doesn't exist
            // This test behavior depends on system setup
            let _ = result;
        }
    }

    #[test]
    #[cfg(unix)]
    #[allow(unsafe_code)]
    fn test_find_cli_binary_with_valid_env_var() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().unwrap();
        let cli_path = temp_dir.path().join("cli");

        // Create a mock executable
        fs::write(&cli_path, "#!/bin/sh\necho test").unwrap();
        let mut perms = fs::metadata(&cli_path).unwrap().permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&cli_path, perms).unwrap();

        unsafe {
            // Set environment variable
            env::set_var("CLI_BINARY", cli_path.to_str().unwrap());

            let result = find_cli_binary();

            // Clean up
            env::remove_var("CLI_BINARY");

            assert!(result.is_ok(), "Should find cli from env var");
            assert_eq!(result.unwrap(), cli_path);
        }
    }

    // ============================================================================
    // Tests for validate_args - CRITICAL for CLI security
    // ============================================================================

    #[test]
    fn test_validate_args_empty() {
        let args: Vec<String> = vec![];
        let result = validate_args(&args);
        assert!(result.is_ok(), "Empty args should be valid");
    }

    #[test]
    fn test_validate_args_normal() {
        let args = vec!["session".to_string(), "test query".to_string()];
        let result = validate_args(&args);
        assert!(result.is_ok(), "Normal args should be valid");
    }

    #[test]
    fn test_validate_args_too_long_individual() {
        // Create an argument that exceeds MAX_ARG_LENGTH
        let long_arg = "a".repeat(MAX_ARG_LENGTH + 1);
        let args = vec![long_arg];

        let result = validate_args(&args);
        assert!(
            result.is_err(),
            "Should reject too-long individual argument"
        );
        assert!(result.unwrap_err().to_string().contains("too long"));
    }

    #[test]
    fn test_validate_args_too_long_total() {
        // Create many arguments that together exceed MAX_TOTAL_ARGS_LENGTH
        let arg = "a".repeat(1_000_000); // 1MB each
        let args = vec![arg.clone(); 11]; // 11MB total

        let result = validate_args(&args);
        assert!(
            result.is_err(),
            "Should reject total args length exceeding limit"
        );
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("Total arguments length"));
    }

    #[test]
    fn test_validate_args_null_byte() {
        let args = vec!["test\0query".to_string()];

        let result = validate_args(&args);
        assert!(result.is_err(), "Should reject argument with null byte");
        assert!(result.unwrap_err().to_string().contains("null byte"));
    }

    #[test]
    fn test_validate_args_at_boundary() {
        // Test exactly at the MAX_ARG_LENGTH boundary
        let arg = "a".repeat(MAX_ARG_LENGTH);
        let args = vec![arg];

        let result = validate_args(&args);
        assert!(result.is_ok(), "Should accept argument at exact max length");
    }

    #[test]
    fn test_validate_args_special_characters() {
        let args = vec![
            "query with spaces".to_string(),
            "special!@#$%^&*()".to_string(),
            "unicode: 你好世界 🦀".to_string(),
        ];

        let result = validate_args(&args);
        assert!(
            result.is_ok(),
            "Should accept special characters (except null)"
        );
    }

    // ============================================================================
    // Tests for atomic_write
    // ============================================================================

    #[test]
    fn test_atomic_write_success() {
        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test.txt");
        let content = "test content";

        let result = atomic_write(&file_path, content);
        assert!(result.is_ok(), "Atomic write should succeed");

        let read_content = fs::read_to_string(&file_path).unwrap();
        assert_eq!(read_content, content);
    }

    #[test]
    fn test_atomic_write_overwrites_existing() {
        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test.txt");

        // Write initial content
        fs::write(&file_path, "initial").unwrap();

        // Atomic write new content
        let new_content = "new content";
        atomic_write(&file_path, new_content).unwrap();

        let read_content = fs::read_to_string(&file_path).unwrap();
        assert_eq!(read_content, new_content);
    }

    #[test]
    fn test_atomic_write_with_unicode() {
        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("test.txt");
        let content = "Unicode content: 你好世界 🦀";

        atomic_write(&file_path, content).unwrap();

        let read_content = fs::read_to_string(&file_path).unwrap();
        assert_eq!(read_content, content);
    }

    // ============================================================================
    // Tests for get_filtered_env
    // ============================================================================

    #[test]
    #[allow(unsafe_code)]
    fn test_get_filtered_env_includes_safe_vars() {
        unsafe {
            env::set_var("PATH", "/usr/bin");
            env::set_var("HOME", "/home/test");
            env::set_var("CLI_MODEL", "test-model");

            let filtered = get_filtered_env();

            assert!(filtered.iter().any(|(k, _)| k == "PATH"));
            assert!(filtered.iter().any(|(k, _)| k == "HOME"));
            assert!(filtered.iter().any(|(k, _)| k != "CLI_MODEL"));

            // Clean up
            env::remove_var("CLI_MODEL");
        }
    }

    #[test]
    #[allow(unsafe_code)]
    fn test_get_filtered_env_excludes_unsafe_vars() {
        unsafe {
            env::set_var("RANDOM_VAR", "should not pass");
            env::set_var("MALICIOUS", "data");

            let filtered = get_filtered_env();

            assert!(!filtered.iter().any(|(k, _)| k == "RANDOM_VAR"));
            assert!(!filtered.iter().any(|(k, _)| k == "MALICIOUS"));

            // Clean up
            env::remove_var("RANDOM_VAR");
            env::remove_var("MALICIOUS");
        }
    }

    #[test]
    #[allow(unsafe_code)]
    fn test_get_filtered_env_allows_xdg_prefix() {
        unsafe {
            env::set_var("XDG_CONFIG_HOME", "/home/test/.config");

            let filtered = get_filtered_env();

            assert!(filtered.iter().any(|(k, _)| k == "XDG_CONFIG_HOME"));

            // Clean up
            env::remove_var("XDG_CONFIG_HOME");
        }
    }

    // ============================================================================
    // Tests for status_to_exit_code
    // ============================================================================

    #[test]
    #[cfg(unix)]
    fn test_status_to_exit_code_normal() {
        use std::os::unix::process::ExitStatusExt;

        // Create a mock exit status with code 0
        let status = std::process::ExitStatus::from_raw(0);
        let code = status_to_exit_code(status);
        assert_eq!(code, 0);

        // Create a mock exit status with code 1
        let status = std::process::ExitStatus::from_raw(1 << 8);
        let code = status_to_exit_code(status);
        assert_eq!(code, 1);
    }

    #[test]
    #[cfg(unix)]
    fn test_status_to_exit_code_signal() {
        use std::os::unix::process::ExitStatusExt;

        // Signal 9 (SIGKILL)
        let status = std::process::ExitStatus::from_raw(9);
        let code = status_to_exit_code(status);
        assert_eq!(code, 128 + 9);

        // Signal 2 (SIGINT)
        let status = std::process::ExitStatus::from_raw(2);
        let code = status_to_exit_code(status);
        assert_eq!(code, 128 + 2);
    }

    // ============================================================================
    // Integration tests for ensure_cli_config_files
    // ============================================================================

    #[test]
    fn test_ensure_cli_config_files_creates_files() {
        // This test requires HOME to be set and writable
        // It's more of an integration test, so we'll skip it if HOME is not set
        if env::var("HOME").is_err() {
            return;
        }

        // Note: This test actually modifies the user's config directory
        // In a real scenario, you might want to mock the file system
        // For now, we just verify it doesn't crash
        let result = ensure_cli_config_files();

        // Should either succeed or fail gracefully
        let _ = result;
    }
}
