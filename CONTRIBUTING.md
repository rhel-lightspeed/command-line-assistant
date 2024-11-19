# Contributing to Command Line Assistant

The following is a set of guidelines for contributing to Command Line Assistant codebase, which are hosted in the [RHEL Lightspeed
Organization](https://github.com/rhel-lightspeed) on GitHub. These are mostly guidelines, not rules.

* [Road Core Service](https://github.com/road-core/service)

## What should I know before I get started?

Below are a list of things to keep in mind when developing and submitting
contributions to this repository.

1. All Python code must be compatible with versions 3.9+.
2. The code should follow linting from ruff.
3. All commits should have passed the pre-commit checks.
4. Don't change code that is not related to your issue/ticket, open a new issue/ticket if that's the case.

### Working with GitHub

If you are not sure on how GitHub works, you can read the quickstart guide from GitHub to introduce you on how to get
started at the platform. [GitHub Quickstart - Hello
World](https://docs.github.com/en/get-started/quickstart/hello-world).

### Setting up Git

If you never used `git` before, GitHub has a nice quickstart on how to set it up and get things ready. [GitHub
Quickstart - Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)

### Forking a repository

Forking is necessary if you want to contribute with Command Line Assistant, but if you are unsure on how this work (Or what a fork is),
head out to this quickstart guide from GitHub. [GitHub Quickstart - Fork a
repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)

As an additional material, check out this Red Hat blog post about [What is an open source
upstream?](https://www.redhat.com/en/blog/what-open-source-upstream)

### Collaborating with Pull Requests

Check out this guide from GitHub on how to collaborate with pull requests. This is an in-depth guide on everything you
need to know about PRs, forks, contributions and much more. [GitHub - Collaborating with pull
requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests)

## Getting started with development

### Seting up the environment

The commands below will create a python3 virtual environment with all the necessary dependencies installed. This is done
via [pdm](https://pdm-project.org/en/latest/). If you don't have `pdm` installed, the command below will take care of it
for you.

Required packages:
- Python 3.9 or greater
- pip

```sh
make install
```

### Getting a backend to manage your queries

Command Line Assistant depends on a backend service to interact with LLM providers (such as OpenAI, IBM WatsonX, etc...). For that
purpose, we strongly recommend setting up [Road Core Service](https://github.com/road-core/service). After you have
everything in order, the next steps should work without extra configuration.

### Update config to your needs

The project root contains a [basic configuration](./config.yaml) file that captures a set of options for Command Line Assistant. You
can use it the way it is, or, if needed, can update to your needs.

```yml
# Example config.yaml
output_capture: # if '^' is used, last command output will be used for query context
  enforce_script: false  # otherwise recording via script session will be enforced
  output_file: /tmp/command-line-assistant_output.txt  # file with output(s) of regular commands (e.g. ls, echo, etc.)
  prompt_separator: '$'  # Keep non-empty if your file contains only output of commands (not prompt itself)
backend_service:
  # proxy: http://todo:8080
  query_endpoint: http://0.0.0.0:8080/v1/query/
history:
  enabled: true
  filepath: command-line-assistant_history.json
  max_size: 100  # max number of queries in history (including responses)
```

### Asking questions through Command Line Assistant

```sh
c --record
c "How to uninstall RHEL?"
c --history-clear "How to uninstall RHEL?"
c --config <custom config path> "How to uninstall RHEL?"

# OR with stdin

echo "How to uninstall RHEL?" | c
echo "How to uninstall RHEL?" | c "Text that will be appended to the stdin"

# Usage of caret '^'
# Takes last command output as query context (must be available from output_file value in config)
c "How to uninstall RHEL? ^"
#
# The query then is in following format:
# 2024-09-11 14:27:01,667 - INFO - Query:
# Context data: context text from file specified in config
# Question: How to uninstall RHEL?
```

### How to capture cmd output for usage of `^`

1. Use `script` tool and it's session
2. Use `tee` command to simply save output of command to some file
3. Use `tmux` workaround below

#### `tmux` workaround to capture output of every command

Please note that this is up to the user to decide if this is the best way to capture output of every command including
potential sensitive data.

Install `tmux` and put the following code in your `~/.bashrc`. It will invoke `tmux`, capturing the output of the
previous command and store it in a temporary file for `Command Line Assistant` to use. (Desclaimer: I didn't test it with other shells
other than `bash`.)

``` bash
# Set the PROMPT_COMMAND to capture the output after each command
SHELL_OUTPUT="$/tmp/command-line-assistant_output.tmp"
SHELL_OUTPUT_CLEANED="/tmp/command-line-assistant/command-line-assistant_output_cleaned.tmp"
# Function to capture the pane's output
function capture_pane_output() {
    tmux capture-pane -p > "$SHELL_OUTPUT"
    grep -v '^$' ${SHELL_OUTPUT} > ${SHELL_OUTPUT_CLEANED}
    rm -f ${SHELL_OUTPUT}
}
PROMPT_COMMAND="capture_pane_output"
```

If you get `ImportError: urllib3 v2.0 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with LibreSSL
2.8.3`, try this:

```sh
pip uninstall urllib3
pip install 'urllib3<2.0'
```

All temporary files created during the usage (context, code blocks, command call output, captured shell output) are
stored in `/tmp/command-line-assistant/*`
