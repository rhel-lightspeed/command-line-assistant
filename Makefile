.PHONY:
	install-tools \
	install \
	unit-test \
	help \
	clean \
	link-systemd-units \
	unlink-systemd-units \
	run-clad \
	status-clad \
	reload-clad \
	manpages \
	docs \
	distribution-tarball \
	html-docs

# Project directory path - /home/<user>/.../command-line-assistant
PROJECT_DIR := $(shell pwd)
DATA_DEVELOPMENT_PATH := $(PROJECT_DIR)/data/development

## Systemd specifics
# https://www.gnu.org/software/make/manual/html_node/Text-Functions.html#index-subst-1
# Virtualenv bin path for clad
CLAD_VENV_BIN := $(subst /,\/,$(PROJECT_DIR)/.venv/bin/clad)
# Systemd development unit
CLAD_SYSTEMD_DEVEL_PATH := $(DATA_DEVELOPMENT_PATH)/systemd/clad-devel.service
# Systemd user unit, which is generated from devel unit
CLAD_SYSTEMD_USER_PATH := $(DATA_DEVELOPMENT_PATH)/systemd/clad-user.service
# Systemd path on the system to place the user unit
SYSTEMD_USER_UNITS := ~/.config/systemd/user
# Path to local XDG_CONFIG_DIRS to load config file
XDG_CONFIG_DIRS := $(subst /,\/,$(DATA_DEVELOPMENT_PATH)/config)

PKGNAME := command-line-assistant
VERSION := 0.2.2

default: help

install-tools: ## Install required utilities/tools
	@command -v poetry > /dev/null || { echo >&2 "poetry is not installed. Installing..."; pip install -q poetry; }
	@poetry --version

install: install-tools ## Sync all required dependencies for Command Line Assistant to work
	@poetry install
	@poetry install --all-extras

unit-test: ## Unit test cla
	@echo "Running tests..."
	@poetry run pytest
	@echo "Tests completed."

unit-test-coverage: ## Unit test cla with coverage
	@echo "Running tests..."
	@poetry run pytest --cov --junitxml=junit.xml -o junit_family=legacy
	@echo "Tests completed."

coverage: ## Generate coverage report from unit-tests
	@poetry run coverage xml

coverage-html: ## Generate coverage report from unit-tests as html
	@poetry run coverage html

help: ## Show available make commands
	@echo 'Usage: make <OPTIONS> ... <TARGETS>'
	@echo ''
	@echo 'Available targets are:'
	@echo ''
	@grep -E '^[ a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ''

clean: ## Clean project files
	@echo 'Cleanup project specific files...'
	@find . -name '__pycache__' -exec rm -fr {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@rm -rf htmlcov \
	   .pytest_cache \
	   command_line_assistant.egg-info \
	   .ruff_cache \
	   .coverage \
	   dist \
	   .tox \
	   junit.xml \
	   coverage.xml \
	   $(PKGNAME)-$(VERSION).tar.gz
	$(MAKE) -C docs clean
	$(MAKE) -C data/release/selinux

link-systemd-units: ## Link the systemd units to ~/.config/systemd/user
	@echo "Linking the systemd units from $(CLAD_SYSTEMD_DEVEL_PATH) to $(SYSTEMD_USER_UNITS)/clad.service"
	@sed -e 's/{{ EXEC_START }}/$(CLAD_VENV_BIN)/'			   \
		 -e 's/{{ CONFIG_FILE_PATH }}/$(XDG_CONFIG_DIRS)/' \
		 -e 's/{{ DBUS_SESSION_ADDRESS }}/$(subst /,\/,$(DBUS_SESSION_BUS_ADDRESS))/' \
	     $(CLAD_SYSTEMD_DEVEL_PATH) > $(CLAD_SYSTEMD_USER_PATH)
	@ln -s $(CLAD_SYSTEMD_USER_PATH) $(SYSTEMD_USER_UNITS)/clad.service

unlink-systemd-units: ## Unlink the systemd units from ~/.config/systemd/user
	@echo "Unlinking the systemd units from $(SYSTEMD_USER_UNITS)/clad.service"
	@unlink $(SYSTEMD_USER_UNITS)/clad.service

clad: ## Run clad on the system
	@XDG_CONFIG_DIRS=$(XDG_CONFIG_DIRS) $(CLAD_VENV_BIN)

run-clad: ## Run the clad under systemd
	@systemctl start --user clad

status-clad: ## Check the status for clad
	@journalctl --user -fu clad

reload-clad: ## Reload clad systemd unit
	@systemctl --user daemon-reload
	@systemctl restart --user clad

man: ## Build manpages
	# Build the manpages and change the builddir to match data/release
	# Also change the doctrees cache to still use the original build directory.
	$(MAKE) BUILDDIR=../data/release SPHINXOPTS=-d=build -C docs man

html-docs: ## Build html docs
	$(MAKE) -C docs html

distribution-tarball: clean ## Generate distribution tarball
	tar --create \
		--gzip \
		--file /tmp/$(PKGNAME)-$(VERSION).tar.gz \
		--exclude=.git \
		--exclude=.vscode \
		--exclude=.github \
		--exclude=.gitignore \
		--exclude=.copr \
		--exclude=.venv \
		--exclude=.ruff_cache \
		--exclude=data/development \
		--exclude=scripts \
		--exclude=docs \
		--exclude=tests \
		--exclude=.roproject \
		--transform s/^\./$(PKGNAME)-$(VERSION)/ \
		. && mv /tmp/$(PKGNAME)-$(VERSION).tar.gz .
