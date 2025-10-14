//! Command Line Assistant (c) - Your Quick AI Helper
//!
//! This wrapper provides convenient shortcuts for AI assistance:
//! - c "query" → Quick query (defaults to chat subcommand)
//! - c -i → Interactive chat session
//! - c chat "query" → Explicit chat command
//! - c history → View chat history
//! - c shell → Shell integration features

mod commands;
mod config;
mod helpers;

#[cfg(feature = "docgen")]
mod cli_json;

use clap::{CommandFactory, Parser, Subcommand};
use log::info;
use std::process::exit;

use crate::commands::chat::ChatArgs;
use crate::commands::history::HistoryArgs;
use crate::commands::shell::ShellArgs;

/// Command Line Assistant (c) - Your Quick AI Helper
#[derive(Parser, Debug)]
#[command(
    name = "c",
    author,
    version,
    about = "Command Line Assistant",
    disable_help_subcommand = true
)]
pub struct Cli {
    /// Subcommand to execute (defaults to chat if not specified)
    #[command(subcommand)]
    pub command: Option<Commands>,
}

/// Available subcommands for the CLI
#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Start a chat session (default)
    Chat(ChatArgs),

    /// View and manage chat history
    History(HistoryArgs),

    /// Shell integration and features
    Shell(ShellArgs),

    /// Internal commands for tooling (not for end users)
    #[command(hide = true)]
    Internals {
        /// Internal subcommand to execute
        #[command(subcommand)]
        command: InternalsCommands,
    },
}

/// Internal subcommands for tooling and doc generation
#[derive(Subcommand, Debug)]
pub enum InternalsCommands {
    /// Dump CLI structure as JSON for man page generation
    DumpCliJson,
}

impl Cli {
    /// Execute the CLI command - dispatches to appropriate subcommand
    pub fn execute(self) {
        // Handle internal commands first (for doc generation)
        if let Some(Commands::Internals { command }) = &self.command {
            self.execute_internals(command);
            return;
        }

        // Dispatch to subcommand
        match self.command {
            Some(Commands::Chat(args)) => args.execute(),
            Some(Commands::History(args)) => args.execute(),
            Some(Commands::Shell(args)) => args.execute(),
            Some(Commands::Internals { .. }) => unreachable!("Already handled above"),

            // No subcommand specified - show help
            None => {
                let _ = Cli::command().print_help();
                eprintln!();
                exit(1);
            }
        }
    }

    /// Execute internal commands (for tooling/doc generation)
    #[cfg(feature = "docgen")]
    fn execute_internals(&self, command: &InternalsCommands) {
        match command {
            InternalsCommands::DumpCliJson => {
                let cmd = Cli::command();
                crate::cli_json::dump_cli_json(&cmd);
                exit(0);
            }
        }
    }

    /// Execute internal commands (stub for when docgen is not enabled)
    #[cfg(not(feature = "docgen"))]
    fn execute_internals(&self, _command: &InternalsCommands) {
        eprintln!("Error: Internal commands require the 'docgen' feature to be enabled");
        exit(1);
    }
}

fn main() {
    // Initialize logging - responds to RUST_LOG environment variable
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("warn"))
        .format_timestamp(None)
        .init();

    info!("Command Line Assistant CLI starting");

    // Get raw arguments
    let args: Vec<String> = std::env::args().collect();

    // Check if we should route to default chat subcommand
    let should_default_to_chat = should_route_to_chat(&args);

    // Parse command-line arguments and execute
    if should_default_to_chat {
        // Prepend "chat" to route to chat subcommand
        let mut new_args = vec![args[0].clone(), "chat".to_string()];
        new_args.extend_from_slice(&args[1..]);

        match Cli::try_parse_from(&new_args) {
            Ok(cli) => cli.execute(),
            Err(e) => e.exit(),
        }
    } else {
        let cli = Cli::parse();
        cli.execute();
    }
}

/// Determine if the arguments should route to the chat subcommand
///
/// This handles the default routing logic:
/// - `c chat ...` -> don't route (already explicit chat)
/// - `c history` -> history subcommand
/// - `c history -l` -> history subcommand (flag detected)
/// - `c history from yesterday` -> chat mode (natural language query)
/// - `c shell --install` -> shell subcommand (flag detected)
/// - `c shell is broken` -> chat mode (natural language query)
/// - `c -i` -> chat mode
/// - `c hello world` -> chat mode
fn should_route_to_chat(args: &[String]) -> bool {
    if args.len() <= 1 {
        return false;
    }

    let first_arg = args[1].as_str();
    let help_version_flags = ["--help", "-h", "--version", "-V"];

    // If it's already the chat subcommand, don't route (already explicit)
    if first_arg == "chat" {
        return false;
    }

    // If it's internals, don't route
    if first_arg == "internals" {
        return false;
    }

    // For other known subcommands (history, shell), check if there are additional args
    let other_subcommands = ["history", "shell"];
    if other_subcommands.contains(&first_arg) {
        // If there are more args after the subcommand name
        if args.len() > 2 {
            let second_arg = &args[2];
            // If the second arg starts with '-', it's likely a flag for the subcommand
            // So don't route to chat
            if second_arg.starts_with('-') {
                return false;
            }
            // Otherwise, it's a natural language query, so route to chat
            // e.g., "c history from yesterday" -> chat query
            return true;
        }
        // Just the subcommand with no args -> don't route
        return false;
    }

    // If it's a help/version flag, don't route to chat
    if help_version_flags.contains(&first_arg) {
        return false;
    }

    // Otherwise, route to chat (handles -i, queries, etc.)
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Helper to convert string slices to Vec<String> for testing
    fn args_vec(args: &[&str]) -> Vec<String> {
        args.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn test_no_args_shows_help() {
        let args = args_vec(&["c"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_explicit_chat_subcommand() {
        let args = args_vec(&["c", "chat", "hello"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_explicit_history_subcommand_no_args() {
        let args = args_vec(&["c", "history"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_explicit_shell_subcommand_no_args() {
        let args = args_vec(&["c", "shell"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_history_with_args_routes_to_chat() {
        // "c history from yesterday" should be treated as a chat query
        let args = args_vec(&["c", "history", "from", "yesterday"]);
        assert!(
            should_route_to_chat(&args),
            "Expected 'c history from yesterday' to route to chat"
        );
    }

    #[test]
    fn test_shell_with_args_routes_to_chat() {
        // "c shell is broken" should be treated as a chat query
        let args = args_vec(&["c", "shell", "is", "broken"]);
        assert!(
            should_route_to_chat(&args),
            "Expected 'c shell is broken' to route to chat"
        );
    }

    #[test]
    fn test_simple_query_routes_to_chat() {
        let args = args_vec(&["c", "hello"]);
        assert!(should_route_to_chat(&args));
    }

    #[test]
    fn test_multi_word_query_routes_to_chat() {
        let args = args_vec(&["c", "hello", "world"]);
        assert!(should_route_to_chat(&args));
    }

    #[test]
    fn test_interactive_flag_routes_to_chat() {
        let args = args_vec(&["c", "-i"]);
        assert!(should_route_to_chat(&args));
    }

    #[test]
    fn test_help_flag_does_not_route_to_chat() {
        let args = args_vec(&["c", "--help"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_version_flag_does_not_route_to_chat() {
        let args = args_vec(&["c", "--version"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_query_starting_with_dash_routes_to_chat() {
        let args = args_vec(&["c", "-x"]);
        assert!(should_route_to_chat(&args));
    }

    #[test]
    fn test_chat_subcommand_with_no_args() {
        // "c chat" with no query should be handled by chat subcommand
        let args = args_vec(&["c", "chat"]);
        assert!(!should_route_to_chat(&args));
    }

    #[test]
    fn test_history_with_short_flag_goes_to_subcommand() {
        // "c history -l" should go to history subcommand (flag detected)
        let args = args_vec(&["c", "history", "-l"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c history -l' to go to history subcommand"
        );
    }

    #[test]
    fn test_history_with_long_flag_goes_to_subcommand() {
        // "c history --list" should go to history subcommand (flag detected)
        let args = args_vec(&["c", "history", "--list"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c history --list' to go to history subcommand"
        );
    }

    #[test]
    fn test_history_with_help_flag_goes_to_subcommand() {
        // "c history --help" should go to history subcommand
        let args = args_vec(&["c", "history", "--help"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c history --help' to go to history subcommand"
        );
    }

    #[test]
    fn test_shell_with_short_flag_goes_to_subcommand() {
        // "c shell -i" should go to shell subcommand (flag detected)
        let args = args_vec(&["c", "shell", "-i"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c shell -i' to go to shell subcommand"
        );
    }

    #[test]
    fn test_shell_with_long_flag_goes_to_subcommand() {
        // "c shell --install" should go to shell subcommand (flag detected)
        let args = args_vec(&["c", "shell", "--install"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c shell --install' to go to shell subcommand"
        );
    }

    #[test]
    fn test_shell_with_status_flag_goes_to_subcommand() {
        // "c shell --status" should go to shell subcommand
        let args = args_vec(&["c", "shell", "--status"]);
        assert!(
            !should_route_to_chat(&args),
            "Expected 'c shell --status' to go to shell subcommand"
        );
    }

    #[test]
    fn test_parse_history_subcommand() {
        let cli = Cli::try_parse_from(&["c", "history"]).expect("Failed to parse");
        assert!(matches!(cli.command, Some(Commands::History(_))));
    }

    #[test]
    fn test_parse_shell_subcommand() {
        let cli = Cli::try_parse_from(&["c", "shell"]).expect("Failed to parse");
        assert!(matches!(cli.command, Some(Commands::Shell(_))));
    }

    #[test]
    fn test_parse_chat_subcommand_with_query() {
        let cli = Cli::try_parse_from(&["c", "chat", "hello", "world"]).expect("Failed to parse");
        if let Some(Commands::Chat(args)) = cli.command {
            assert_eq!(args.query, vec!["hello", "world"]);
            assert!(!args.interactive);
        } else {
            panic!("Expected Chat command");
        }
    }

    #[test]
    fn test_parse_chat_subcommand_with_interactive() {
        let cli = Cli::try_parse_from(&["c", "chat", "-i"]).expect("Failed to parse");
        if let Some(Commands::Chat(args)) = cli.command {
            assert!(args.interactive);
            assert!(args.query.is_empty());
        } else {
            panic!("Expected Chat command");
        }
    }

    #[test]
    fn test_parse_chat_subcommand_interactive_with_query() {
        // This should fail due to conflicts_with
        let result = Cli::try_parse_from(&["c", "chat", "-i", "hello"]);
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_no_subcommand() {
        let cli = Cli::try_parse_from(&["c"]).expect("Failed to parse");
        assert!(cli.command.is_none());
    }

    #[test]
    fn test_chat_args_with_special_characters() {
        let cli = Cli::try_parse_from(&["c", "chat", "what's", "up?"]).expect("Failed to parse");
        if let Some(Commands::Chat(args)) = cli.command {
            assert_eq!(args.query, vec!["what's", "up?"]);
        } else {
            panic!("Expected Chat command");
        }
    }

    #[test]
    fn test_chat_args_with_quoted_string() {
        // When shell passes a quoted string, it comes as a single argument
        let cli = Cli::try_parse_from(&["c", "chat", "hello world"]).expect("Failed to parse");
        if let Some(Commands::Chat(args)) = cli.command {
            assert_eq!(args.query, vec!["hello world"]);
        } else {
            panic!("Expected Chat command");
        }
    }

    #[test]
    fn test_history_command_structure() {
        let cli = Cli::try_parse_from(&["c", "history"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::History(_)) => {
                // Success - history command parsed correctly
            }
            _ => panic!("Expected History command"),
        }
    }

    #[test]
    fn test_shell_command_structure() {
        let cli = Cli::try_parse_from(&["c", "shell"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::Shell(_)) => {
                // Success - shell command parsed correctly
            }
            _ => panic!("Expected Shell command"),
        }
    }

    #[test]
    fn test_internals_command_is_hidden() {
        // Internals command should be hidden but still work
        let cli = Cli::try_parse_from(&["c", "internals", "dump-cli-json"]);
        assert!(cli.is_ok());
    }

    #[test]
    fn test_history_with_list_flag_parses() {
        let cli = Cli::try_parse_from(&["c", "history", "-l"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::History(args)) => {
                assert!(args.list, "Expected list flag to be true");
            }
            _ => panic!("Expected History command"),
        }
    }

    #[test]
    fn test_history_with_verbose_flag_parses() {
        let cli = Cli::try_parse_from(&["c", "history", "--verbose"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::History(args)) => {
                assert!(args.verbose, "Expected verbose flag to be true");
            }
            _ => panic!("Expected History command"),
        }
    }

    #[test]
    fn test_history_with_limit_flag_parses() {
        let cli = Cli::try_parse_from(&["c", "history", "-n", "20"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::History(args)) => {
                assert_eq!(args.limit, 20, "Expected limit to be 20");
            }
            _ => panic!("Expected History command"),
        }
    }

    #[test]
    fn test_shell_with_install_flag_parses() {
        let cli = Cli::try_parse_from(&["c", "shell", "--install"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::Shell(args)) => {
                assert!(args.install, "Expected install flag to be true");
            }
            _ => panic!("Expected Shell command"),
        }
    }

    #[test]
    fn test_shell_with_status_flag_parses() {
        let cli = Cli::try_parse_from(&["c", "shell", "-s"]).expect("Failed to parse");
        match cli.command {
            Some(Commands::Shell(args)) => {
                assert!(args.status, "Expected status flag to be true");
            }
            _ => panic!("Expected Shell command"),
        }
    }

    #[test]
    fn test_shell_with_shell_type_parses() {
        let cli = Cli::try_parse_from(&["c", "shell", "--install", "--shell-type", "zsh"])
            .expect("Failed to parse");
        match cli.command {
            Some(Commands::Shell(args)) => {
                assert!(args.install, "Expected install flag to be true");
                assert_eq!(
                    args.shell_type,
                    Some("zsh".to_string()),
                    "Expected shell type to be zsh"
                );
            }
            _ => panic!("Expected Shell command"),
        }
    }
}
