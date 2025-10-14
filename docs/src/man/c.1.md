# NAME

c - Command Line Assistant

# SYNOPSIS

**c** \[*OPTIONS...*\] <*SUBCOMMAND*>

# DESCRIPTION

The 'c' command provides a simplified interface for quick AI assistance. Simply type your question or request as natural text after 'c'.

The Command Line Assistant can help with several tasks such as:
- Answering questions
- Assisting with troubleshooting
- Assisting with understanding log entries
- And many other tasks

<!-- BEGIN GENERATED OPTIONS -->
<!-- END GENERATED OPTIONS -->

# SUBCOMMANDS

<!-- BEGIN GENERATED SUBCOMMANDS -->
| Command | Description |
|---------|-------------|
| **c chat** | Start a chat session (default) |
| **c history** | View and manage chat history |
| **c shell** | Shell integration and features |
| **c internals** | Internal commands for tooling (not for end users) |

<!-- END GENERATED SUBCOMMANDS -->

# EXAMPLES

## Start an interactive session

```bash
c -i
```

## Ask a quick question

```bash
c "how do I list files"
```

## Multi-word queries work naturally

```bash
c explain this code
```

## Redirect output to c

If you have any program that is erroring out, or a log file that contains something you want to understand:

```bash
cat log_with_error.log | c
```

You can combine the redirect output with a question:

```bash
cat log_with_error.log | c "how do I solve this?"
```

# EXIT STATUS

- `0` - success
- `1` - general failure
- `64` - incorrect usage
- `65` - incorrect input data
- `69` - a required service was unavailable
- `70` - an internal software error

# FILES

- `~/.bashrc.d/cla-interactive.bashrc` - Bash script to add keyboard binding to enable interactive mode
- `~/.local/state/command-line-assistant/terminal.log` - State file that captures the terminal screen and stores it as JSON

# BUGS

To submit bug reports, please use:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=1&components=12410340>

For feature requests, please use:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=3&components=12410340>

# SEE ALSO

**clad**(8)

# VERSION

<!-- VERSION PLACEHOLDER -->
