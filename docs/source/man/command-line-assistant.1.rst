.. sphinx_argparse_cli::
  :module: command_line_assistant.initialize
  :func: register_subcommands
  :prog: c
  :title: Command Line Assistant

Examples
--------

Asking a question:
    $ c query "How do I check disk space?"

    $ c "How do I check disk space?"

Check all history entries:
    $ c history

Check the first entry:
    $ c history --first

Check the last entry:
    $ c history --last

Clear all the history entries:
    $ c history --clear

See Also
--------

**clad(8)**
