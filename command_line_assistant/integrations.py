"""Hold any shell integration that powers the tool."""

#: Bash interactive session for c.
BASH_INTERACTIVE: str = r"""
# Command Line Assistant Interactive Mode Integration
__c_interactive() {
    # Save current terminal state
    local old_tty=$(stty -g)
    local c_binary=/usr/bin/c

    # Function to restore terminal state
    cleanup() {
        stty "$old_tty"
    }

    # Set cleanup on exit
    trap cleanup EXIT

    # Configure terminal for interactive input
    stty sane  # Reset terminal to sane state
    stty echo  # Ensure input is echoed (visible)
    stty icanon # Enable canonical mode (line-by-line input)

    # Start interactive mode
    if command -v $c_binary >/dev/null 2>&1; then
        $c_binary --interactive
    else
        echo "Error: Command Line Assistant is not installed"
        return 1
    fi

    # Explicitly restore terminal state after c --interactive exits
    cleanup
}

# Bind Ctrl+J to the interactive function
bind -x '"\C-j": __c_interactive'
"""

#: Exports the $PROMPT_COMMAND variable to an internal variable managed by CLA.
#: This will allow us to inject our marker to enable the caret feature.
BASH_ESSENTIAL_EXPORTS: str = r"""
export CLA_USER_SHELL_PS1=$PS1
export CLA_USER_SHELL_PROMPT_COMMAND=$PROMPT_COMMAND
"""
