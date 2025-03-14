.. _command-line-assistant.1:

======================
Command Line Assistant
======================

.. sphinx_argparse_cli::
  :module: command_line_assistant.initialize
  :func: register_subcommands
  :prog: c
  :title: Synopsis

Description
-----------

The command line assistant powered by RHEL Lightspeed is an optional generative
AI assistant available within the RHEL command line interface. The Command Line
Assistant can help with several tasks such as::

    *. Answering RHEL related questions
    *. Assisting with troubleshooting
    *. Assisting with understanding log entries
    *. And many other tasks.

The command line assistant provides a natural language interface, and can
incorporate information from resources such as the RHEL documentation.

Examples
--------

* **Interacting and asking questions through `c`**

    * **Asking a simple question**

        Asking questions with `c` is relatively simple. One can start using the
        program by simply doing::

            $ c "What is RHEL?"

        Alternatively, you can strictly specify that you want a query with::

            $ c chat "What is RHEL?"

        In case a `query` is not placed, the program will assume that anything that
        comes after is a potential query. That includes the options for `chat`
        as well.

        Alternatively, you can also use `--interactive` to start an interactive session::

            $ c --interactive

    * **Redirecting output to `c`**

        If you have any program in your system that is erroring out, or a log file
        that contain something that you want to understand, you can redirect that
        output to `c` and ask the tool to give you an answer on how to solve it::

            $ cat log_with_error.log | c

        If you want to redirect directly from a command, that is also possible
        with::

            $ my-command | c

        Sometimes, only providing the error output might not be enough. For that, you
        can combine your redirect output with a question like this::

            $ cat log_with_error.log | c "how do I solve this?"

    * **Attaching a file with your question**

        Alternatively to redirecting the output, you can attach a file to `c` with
        the following::

            $ c --attachment log_with_error.log

        Optionally, you can use the short version::

            $ c -a log_with_error.log

        You can also combine the attachment with a question::

            $ c -a log_with_error.log "how do I solve this?"

        And lastly, you can use redirect output as well::

            echo "how do I solve this?" | c -a log_with_error.log

        However, if you specify a redirect output and a query at the same time that you have
        an attachment, only the attachment plus the query will be used. The
        redirect output will be ignored::

            # The redirection output here will be ignored, as the query has precedence over redirection in this scenario.
            echo "how do I solve this?" | c -a log_with_error.log "please?"

* **History management**

    With command line assistant, you can also check your conversation history. For that, use the following command to retrieve all user
    history::

        $ c history --all

    If you don't want all history, you can filter it for either the first or last
    result with::

        $ c history --first
        $ c history --last

    In the case that a more granular filtering is needed, you can filter with
    keywords your history, like this::

        # This will retrieve all questions/responses that contain the work "selinux"
        $ c history --filter "selinux"

    And finally, to start a clean history, you can clear all the user history with::

        $ c history --clear

* **Shell integrations**

    With command line assistant, you can also enable shell integrations to help
    in your experience::

        $ c shell --enable-interactive

    The above command will place a file under ~/.bashrc.d folder that will
    be sourced by bash after the next time you open up your terminal.

    Currently, we only have one integration that aims to start the
    interactive mode with a keybind, like the following::

        $ c shell --enable-interactive

        # After enabling the interactive, restart your terminal or run
        $ source ~/.bashrc

        # After the interactive was sourced, you can hit Ctrl + J in your terminal to enable interactive mode.

    If you wish to disable the interactive, it can be done with::

        $ c shell --disabled-interactive

    You can also enable terminal capture to aid in adding context to your queries with::

        # This will create a file under the ~/.local/state/command-line-assistant/terminal.log
        $ c shell --enable-capture

    To quit the capture, just press `Ctrl + D`

Notes
-----

In the above examples, we mention that one particular use case where redirected
output will be ignored. That happens because we have a set of rules defined in
order to maintain a correct order of querying. The rules can be seen here::

    1. Positional query only -> use positional query
    2. Stdin query only -> use stdin query
    3. File query only -> use file query
    4. Stdin + positional query -> combine as "{positional_query} {stdin}"
    5. Stdin + file query -> combine as "{stdin} {file_query}"
    6. Positional + file query -> combine as "{positional_query} {file_query}"
    7. Positional + last output -> combine as "{positional_query} {last_output}"
    8. Positional + attachment + last output -> combine as "{positional_query} {attachment} {last_output}"
    99. All three sources -> use only positional and file as "{positional_query} {file_query}"

Files
-----

*~/.bashrc.d/cla-interactive.bashrc*
    Bash script to add keyboard binding to enable interactive mode.

*~/.local/state/command-line-assistant/terminal.log*
    State file that captures the terminal screen and store it as json.

Reference
---------

1. Command line assistant source code: <https://github.com/rhel-lightspeed/command-line-assistant>

Bugs
----

To submit bug reports, please use the following link:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=1&components=12410340>

In case it is a feature request, please use the following link:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=3&components=12410340>

See Also
--------

**clad(8)**
