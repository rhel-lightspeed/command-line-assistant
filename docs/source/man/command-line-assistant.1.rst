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

The Command Line Assistant powered by RHEL Lightspeed is a optional generative
AI assistant available within the RHEL command line interface. The Command Line
Assistant can help with several tasks such as::

    1. answering RHEL related questions
    2. assisting with troubleshooting
    3. assisting with deciphering log entries
    3. and many other tasks.

The Command Line Assistant provides a natural language interface, and can
incorporate information from resources such as the RHEL documentation.

Examples
--------

Example 1. Asking a simple question

    Asking questions with `c` is relatively simple. One can start using the
    program by simply doing::

        $ c "What is RHEL?"

    Alternatively, you can strictly specify that you want a query with::

        $ c query "What is RHEL?"

    In case `query` is not placed, the program will assume that anything that
    comes after is a potential query. That includes the options for `query`
    as well.

Example 2. Redirecting output to `c`

    If you have any program in your system that is erroring out, or a log file
    that contain something that you want to understand, you can redirect that
    output to `c` and ask the tool to give you an answer on how to solve it::

        $ cat log_with_error.log | c

    If you want to redirect directly from a command, that is also possible
    with::

        $ my-command | c

    Sometimes, only providing the error output may not be enough. For that, you
    can combine your redirect output with a question like this::

        $ $ cat log_with_error.log | c "how do I solve this?"

Example 3. Attaching a file with your question

    Alternatively to redirecting the output, you can attach a file to `c` with
    the following::

        $ c --attachment log_with_error.log

    Or, with it's short version::

        $ c -a log_with_error.log

    You can also combine the attachemtn with a question::

        $ c -a log_with_error.log "how do I solve this?"

    And lastly, you can use redirect output as well::

        echo "how do I solve this?" | c -a log_with_error.log

    However, if you specify a redirect output and a query at the same you have
    an attachment, only the attachment plus the query will be used. The
    redirect output will be ignored::

        # The redirection here will be ignored as the query has precedence over redirection in this scenario.
        echo "how do I solve this?" | c -a log_with_error.log "please?"

Example 4. History management

    With Command Line Assistant, you can also check your conversation history.
    To do so, one can issue the following command to retrieve all user
    history:: Check all history entries::

        $ c history

    If you don't want all history, you can filter either for the first, or last
    result with::

        $ c history --first
        $ c history --last

    In the case that a more granular filtering is needed, you can filter with
    keywords your history, like this::

        # This will retrieve all questions/responses that contain the work "selinux"
        $ c history --filter "selinux"

    And lastly, to start a clean history, you can clear all of it with::

        $ c history --clear

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
    7. All three sources -> use only positional and file as "{positional_query} {file_query}"

Reference
---------
1. Command Line Assistant source code: https://github.com/rhel-lightspeed/command-line-assistant

Bugs
----

Please send bug reports to our bug tracker, see https://issues.redhat.com/browse/RSPEED

See Also
--------

**clad(8)**
