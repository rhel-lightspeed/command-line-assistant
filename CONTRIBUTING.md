# Contributing to Command Line Assistant

The following is a set of guidelines for contributing to Command Line Assistant
codebase, which are hosted in the [RHEL Lightspeed
Organization](https://github.com/rhel-lightspeed) on GitHub. These are mostly
guidelines, not rules.

## What should I know before I get started?

Below are a list of things to keep in mind when developing and submitting
contributions to this repository.

1. All Python code must be compatible with versions 3.9+.
2. The code should follow linting from ruff.
3. All commits should have passed the pre-commit checks.
4. Don't change code that is not related to your issue/ticket, open a new
   issue/ticket if that's the case.

### Working with GitHub

If you are not sure on how GitHub works, you can read the quickstart guide from
GitHub to introduce you on how to get started at the platform. [GitHub
Quickstart - Hello
World](https://docs.github.com/en/get-started/quickstart/hello-world).

### Setting up Git

If you never used `git` before, GitHub has a nice quickstart on how to set it
up and get things ready. [GitHub Quickstart - Set up
Git](https://docs.github.com/en/get-started/quickstart/set-up-git)

### Forking a repository

Forking is necessary if you want to contribute with Command Line Assistant, but
if you are unsure on how this work (Or what a fork is), head out to this
quickstart guide from GitHub. [GitHub Quickstart - Fork a
repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)

As an additional material, check out this Red Hat blog post about [What is an
open source
upstream?](https://www.redhat.com/en/blog/what-open-source-upstream)

### Collaborating with Pull Requests

Check out this guide from GitHub on how to collaborate with pull requests. This
is an in-depth guide on everything you need to know about PRs, forks,
contributions and much more. [GitHub - Collaborating with pull
requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests)

## Getting started with development

### Setting up the environment

Required packages:
- Python 3.9 or greater

Before installing the dependencies with `poetry`, install the necessary
development packages. This is required for running `clad`, and installing the
rest of the dependencies.

```sh
sudo dnf install 'pkgconfig(cairo)' 'pkgconfig(cairo-gobject)' 'pkgconfig(gobject-introspection-1.0)' 'pkgconfig(mariadb)' /usr/bin/pg_config
```

The commands below will create a python3 virtual environment with all the
necessary dependencies installed. This is done via
[poetry](https://python-poetry.org/docs/). If you don't have `poetry`
installed, the command below will take care of it for you.

```sh
make install
```

### Asking questions through Command Line Assistant

```sh
c "How to uninstall RHEL?"

# OR with stdin

echo "How to uninstall RHEL?" | c
echo "How to uninstall RHEL?" | c "Text that will be appended to the stdin"

# For more example usages, check out our man page
man c
```
