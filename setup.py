# Legacy setup.py used mainly for building the RPMs in RHEL 8 and 9.

import sys

from setuptools import find_packages, setup

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

pyproject_settings = {}
with open("pyproject.toml", "rb") as f:
    pyproject_settings = tomllib.load(f)

# We might not have a lot of console scripts in pyproject, but let's compose it as a loop in case we add more in the
# future.
entry_points: dict[str, list[str]] = {"console_scripts": []}
for script_name, script_path in pyproject_settings["project"]["scripts"].items():
    entry_points["console_scripts"].append(f"{script_name} = {script_path}")

description = None
with open(
    pyproject_settings["project"]["readme"], mode="r", encoding="utf-8"
) as handler:
    description = handler.read()

setup(
    name=pyproject_settings["project"]["name"],
    version=pyproject_settings["project"]["version"],
    author=pyproject_settings["project"]["authors"][0]["name"],
    author_email=pyproject_settings["project"]["authors"][0]["email"],
    description=pyproject_settings["project"]["description"],
    long_description=description,
    long_description_content_type="text/markdown",
    url=pyproject_settings["project"]["urls"]["Repository"],
    packages=find_packages(
        include=pyproject_settings["tool"]["setuptools"]["packages"]["find"]["include"]
    ),
    install_requires=pyproject_settings["project"]["dependencies"],
    entry_points=entry_points,
    classifiers=pyproject_settings["project"]["classifiers"],
    python_requires=pyproject_settings["project"]["requires-python"],
)
