# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys

project = "command-line-assistant"
copyright = "2024, RHEL Lightspeed Team"
author = "RHEL Lightspeed Team"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Core Sphinx library for auto html doc generation from docstrings
    "sphinx.ext.autosummary",  # Create neat summary tables for modules/classes/methods etc
    "sphinx.ext.intersphinx",  # Link to other project's documentation (see mapping below)
    "sphinx_autodoc_typehints",  # Automatically document param types (less noise in class signature)
    "sphinx.ext.napoleon",  # Google or NumPy docstrings
    "sphinx.ext.viewcode",  # View source code as html
    "sphinx.ext.todo",  # Add todo notes to the docs
    "sphinx.ext.duration",  # Inspect which module is slowing the docs build
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "dasbus": ("https://dasbus.readthedocs.io/en/latest/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "colorama": ("https://super-devops.readthedocs.io/en/latest/", None),
}

templates_path = ["_templates"]
exclude_patterns = []

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = (
    False  # Remove 'view source code' from top of page (for html, not python)
)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures
modindex_common_prefix = ["command_line_assistant."]

default_role = "code"

sys.path.append("../")

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
