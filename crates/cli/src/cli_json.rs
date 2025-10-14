//! CLI structure extraction for man page generation
//!
//! This module is only compiled when the 'docgen' feature is enabled.
//! It introspects the clap Command structure and outputs JSON that
//! can be consumed by the man page generation tooling.

use serde::{Deserialize, Serialize};

/// Represents a CLI option extracted from clap
#[derive(Debug, Serialize, Deserialize)]
pub struct CliOption {
    /// The long flag (e.g., "interactive")
    pub long: String,
    /// The short flag if any (e.g., "i")
    pub short: Option<String>,
    /// The value name if the option takes an argument
    pub value_name: Option<String>,
    /// The default value if any
    pub default: Option<String>,
    /// The help text
    pub help: String,
    /// Possible values for enums
    pub possible_values: Vec<String>,
    /// Whether the option is required
    pub required: bool,
    /// Whether this is a boolean flag
    pub is_boolean: bool,
}

/// Represents a CLI command
#[derive(Debug, Serialize, Deserialize)]
pub struct CliCommand {
    pub name: String,
    pub about: Option<String>,
    pub options: Vec<CliOption>,
    pub positionals: Vec<CliPositional>,
    pub subcommands: Vec<CliCommand>,
}

/// Represents a positional argument
#[derive(Debug, Serialize, Deserialize)]
pub struct CliPositional {
    pub name: String,
    pub help: Option<String>,
    pub required: bool,
    pub multiple: bool,
}

/// Extract CLI structure from a clap Command
pub fn extract_cli_structure(cmd: &clap::Command) -> CliCommand {
    let name = cmd.get_name().to_string();
    let about = cmd.get_about().map(|s| s.to_string());

    let mut options = Vec::new();
    let mut positionals = Vec::new();

    // Extract arguments
    for arg in cmd.get_arguments() {
        if arg.is_positional() {
            // Skip help and version args
            if arg.get_id() == "help" || arg.get_id() == "version" {
                continue;
            }

            positionals.push(CliPositional {
                name: arg.get_id().to_string(),
                help: arg.get_help().map(|s| s.to_string()),
                required: arg.is_required_set(),
                multiple: matches!(
                    arg.get_action(),
                    clap::ArgAction::Append | clap::ArgAction::Count
                ),
            });
        } else {
            // Skip help and version args
            if arg.get_id() == "help" || arg.get_id() == "version" {
                continue;
            }

            let long = arg.get_long().unwrap_or(arg.get_id().as_str()).to_string();
            let short = arg.get_short().map(|c| c.to_string());

            // Determine if this is a boolean flag
            let is_boolean = matches!(
                arg.get_action(),
                clap::ArgAction::SetTrue | clap::ArgAction::SetFalse
            );

            // For boolean flags, we don't want a value name
            let value_name = if is_boolean {
                None
            } else {
                arg.get_value_names()
                    .and_then(|names| names.first())
                    .map(|n| n.to_string())
            };

            let default = arg
                .get_default_values()
                .first()
                .and_then(|v| v.to_str())
                .map(|s| s.to_string());

            let help = arg.get_help().map(|s| s.to_string()).unwrap_or_default();

            let possible_values: Vec<String> = arg
                .get_possible_values()
                .iter()
                .map(|pv| pv.get_name().to_string())
                .collect();

            options.push(CliOption {
                long,
                short,
                value_name,
                default,
                help,
                possible_values,
                required: arg.is_required_set(),
                is_boolean,
            });
        }
    }

    // Extract subcommands recursively
    let mut subcommands = Vec::new();
    for subcmd in cmd.get_subcommands() {
        // Skip the help subcommand
        if subcmd.get_name() == "help" {
            continue;
        }
        subcommands.push(extract_cli_structure(subcmd));
    }

    CliCommand {
        name,
        about,
        options,
        positionals,
        subcommands,
    }
}

/// Dump the CLI structure as JSON to stdout
pub fn dump_cli_json(cmd: &clap::Command) {
    let cli_structure = extract_cli_structure(cmd);
    let json =
        serde_json::to_string_pretty(&cli_structure).expect("Failed to serialize CLI structure");
    println!("{}", json);
}
