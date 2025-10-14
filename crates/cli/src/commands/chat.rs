//! Chat command implementation
//!
//! This module handles the chat functionality, including both interactive
//! mode and quick query mode.

use clap::Args;
use log::{debug, error, info};
use std::path::PathBuf;
use std::process::{exit, Command};

use crate::helpers::{
    ensure_cli_config_files, find_cli_binary, get_filtered_env, status_to_exit_code, validate_args,
    EX_CANTCREAT, EX_OSERR, EX_SOFTWARE, EX_UNAVAILABLE,
};

/// Run the cli command with the given arguments
pub fn run_cli(binary: &PathBuf, args: &[String]) {
    // Filter environment variables for security
    let filtered_env = get_filtered_env();
    debug!(
        "Passing {} filtered environment variables",
        filtered_env.len()
    );

    // Execute binary with proper I/O inheritance
    let mut cmd = Command::new(binary);
    cmd.args(args)
        .env_clear() // Clear all env vars first
        .envs(filtered_env) // Then set only filtered ones
        .stdin(std::process::Stdio::inherit()) // Inherit stdin for interactive mode
        .stdout(std::process::Stdio::inherit()) // Inherit stdout for output
        .stderr(std::process::Stdio::inherit()); // Inherit stderr for errors

    debug!("Spawning cli process");

    match cmd.spawn() {
        Ok(mut child) => {
            debug!("Child process spawned with PID: {}", child.id());

            // Wait for child process to complete
            // Note: Signals (SIGINT, SIGTERM, etc.) are automatically sent to the
            // entire process group by the OS, so the child will receive them naturally.
            // The parent's wait() call will be interrupted by signals, allowing proper
            // cleanup and exit code propagation.
            match child.wait() {
                Ok(exit_status) => {
                    let exit_code = status_to_exit_code(exit_status);
                    info!("CLI process completed with exit code: {}", exit_code);
                    exit(exit_code);
                }
                Err(e) => {
                    error!("Failed to wait for cli process: {}", e);
                    eprintln!("Error waiting for cli process: {}", e);
                    exit(EX_OSERR);
                }
            }
        }
        Err(e) => {
            error!("Failed to execute cli: {}", e);
            eprintln!("Error executing cli: {}", e);
            eprintln!("Command: {:?}", binary);
            exit(EX_SOFTWARE);
        }
    }
}

/// Start a chat session with the AI assistant
#[derive(Args, Debug)]
pub struct ChatArgs {
    /// Start an interactive session
    #[arg(short, long, conflicts_with = "query")]
    pub interactive: bool,

    /// Your question or query
    #[arg(trailing_var_arg = true, allow_hyphen_values = false)]
    pub query: Vec<String>,
}

impl ChatArgs {
    /// Execute the chat command - dispatches to appropriate mode
    pub fn execute(&self) {
        // Early validation - check for invalid arguments before setup
        if let (false, true) = (self.interactive, self.query.is_empty()) {
            error!("Chat command requires either -i flag or a query");
            eprintln!("Error: Please provide a query or use -i for interactive mode");
            exit(EX_SOFTWARE);
        }

        // Ensure config files exist before running cli
        if let Err(e) = ensure_cli_config_files() {
            error!("Failed to ensure config files: {:#}", e);
            eprintln!("Error setting up configuration: {}", e);
            eprintln!("This may be due to insufficient permissions or disk space.");
            exit(EX_CANTCREAT);
        }

        // Find the cli binary
        let cli_binary = match find_cli_binary() {
            Ok(path) => path,
            Err(e) => {
                error!("Failed to find cli binary: {:#}", e);
                eprintln!("Error: cli binary not found");
                eprintln!("Please ensure cli is installed at /usr/bin/cli");
                eprintln!("Or set CLI_BINARY environment variable to the correct path");
                exit(EX_UNAVAILABLE);
            }
        };

        info!("Using cli binary: {:?}", cli_binary);

        // Dispatch to appropriate mode
        match (self.interactive, self.query.is_empty()) {
            // Interactive mode
            (true, _) => self.execute_interactive(&cli_binary),

            // Query mode (already validated above)
            (false, false) => self.execute_query(&cli_binary),

            // This should never happen due to early validation above
            (false, true) => unreachable!("Empty query should have been handled earlier"),
        }
    }

    /// Execute interactive session mode
    fn execute_interactive(&self, binary: &PathBuf) {
        debug!("Interactive mode requested");
        let args = Self::build_interactive_args();
        debug!("CLI arguments: {:?}", args);

        // Execute cli in interactive mode
        run_cli(&binary, &args);
    }

    /// Execute query mode
    fn execute_query(&self, binary: &PathBuf) {
        // Validate arguments
        if let Err(e) = validate_args(&self.query) {
            error!("Invalid arguments: {}", e);
            eprintln!("Error: {}", e);
            exit(EX_SOFTWARE);
        }

        debug!("Query mode with {} arguments", self.query.len());

        let args = Self::build_query_args(&self.query);
        debug!("CLI arguments: {:?}", args);

        // Execute cli with query
        run_cli(&binary, &args);
    }

    /// Build arguments for interactive mode
    fn build_interactive_args() -> Vec<String> {
        vec!["session".to_string()]
    }

    /// Build arguments for query mode
    fn build_query_args(query: &[String]) -> Vec<String> {
        let mut args = vec!["run".to_string(), "-t".to_string()];
        // SECURITY: Don't join arguments - pass them separately
        // The cli binary will handle them appropriately
        args.extend_from_slice(query);
        args
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ============================================================================
    // Tests for ChatArgs Parsing
    // ============================================================================
    // Note: These tests are somewhat limited since ChatArgs is now part of a
    // subcommand structure. The main CLI tests should be in main.rs.

    // ============================================================================
    // Tests for Argument Building Functions
    // ============================================================================

    #[test]
    fn test_build_interactive_args() {
        let args = ChatArgs::build_interactive_args();
        assert_eq!(args, vec!["session"]);
    }

    #[test]
    fn test_build_query_args_single_word() {
        let query = vec!["hello".to_string()];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 3);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
        assert_eq!(args[2], "hello");
    }

    #[test]
    fn test_build_query_args_multiple_words() {
        let query = vec![
            "how".to_string(),
            "do".to_string(),
            "I".to_string(),
            "list".to_string(),
            "files".to_string(),
        ];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 7);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
        assert_eq!(args[2], "how");
        assert_eq!(args[3], "do");
        assert_eq!(args[4], "I");
        assert_eq!(args[5], "list");
        assert_eq!(args[6], "files");
    }

    #[test]
    fn test_build_query_args_with_spaces() {
        let query = vec!["query with spaces".to_string()];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 3);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
        assert_eq!(args[2], "query with spaces");
    }

    #[test]
    fn test_build_query_args_with_special_chars() {
        let query = vec![
            "what's".to_string(),
            "this!".to_string(),
            "meaning?".to_string(),
        ];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 5);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
        assert_eq!(args[2], "what's");
        assert_eq!(args[3], "this!");
        assert_eq!(args[4], "meaning?");
    }

    #[test]
    fn test_build_query_args_preserves_boundaries() {
        // Critical security test: ensure arguments are passed separately
        let query = vec!["arg1".to_string(), "arg2".to_string(), "arg3".to_string()];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 5);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
        assert_eq!(args[2], "arg1");
        assert_eq!(args[3], "arg2");
        assert_eq!(args[4], "arg3");

        // Verify no arguments were joined with spaces
        for arg in &args[2..] {
            assert!(
                !arg.contains(' ') || arg == &query[0],
                "Arguments should not be joined unless they were originally spaces in a single arg"
            );
        }
    }

    #[test]
    fn test_build_query_args_empty() {
        let query: Vec<String> = vec![];
        let args = ChatArgs::build_query_args(&query);

        assert_eq!(args.len(), 2);
        assert_eq!(args[0], "run");
        assert_eq!(args[1], "-t");
    }

    // ============================================================================
    // Tests for Mode Detection Logic
    // ============================================================================

    #[test]
    fn test_mode_detection_interactive() {
        let chat = ChatArgs {
            interactive: true,
            query: vec![],
        };

        assert!(chat.interactive);
        assert!(chat.query.is_empty());
    }

    #[test]
    fn test_mode_detection_query() {
        let chat = ChatArgs {
            interactive: false,
            query: vec!["test".to_string()],
        };

        assert!(!chat.interactive);
        assert!(!chat.query.is_empty());
    }

    #[test]
    fn test_mode_detection_no_args() {
        let chat = ChatArgs {
            interactive: false,
            query: vec![],
        };

        assert!(!chat.interactive);
        assert!(chat.query.is_empty());
    }

    // ============================================================================
    // Integration-style Tests
    // ============================================================================

    #[test]
    fn test_chat_args_construction() {
        // Test that we can construct the ChatArgs struct manually
        let chat = ChatArgs {
            interactive: true,
            query: vec![],
        };

        assert_eq!(chat.interactive, true);
        assert_eq!(chat.query.len(), 0);
    }

    #[test]
    fn test_query_vector_operations() {
        let chat = ChatArgs {
            interactive: false,
            query: vec!["test".to_string(), "query".to_string()],
        };

        assert_eq!(chat.query.len(), 2);
        assert_eq!(chat.query[0], "test");
        assert_eq!(chat.query[1], "query");
    }
}
