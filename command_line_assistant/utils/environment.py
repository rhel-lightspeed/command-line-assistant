"""
Utilitary module to interact with environment variables.
"""

import os
from pathlib import Path

#: The wanted xdg path where the configuration files will live.
WANTED_XDG_PATH = Path("/etc/xdg")

#: The wanted xdg state path in case $XDG_STATE_HOME is not defined.
WANTED_XDG_STATE_PATH = Path("~/.local/state/command-line-assistant").expanduser()

#: The wanted xdg data path in case $XDG_DATA_HOME is not defined.
WANTED_XDG_DATA_PATH = Path("~/.local/share/command-line-assistant").expanduser()


def get_xdg_state_path() -> Path:
    """Check for the existence of XDG_STATE_HOME environment variable.

    In case it is not present, this function will return the default path that
    is `~/.local/state`, which is where we want to place temporary state files for
    Command Line Assistant.

    See: https://specifications.freedesktop.org/basedir-spec/latest/
    """
    xdg_state_home = os.getenv("XDG_STATE_HOME", "")

    # We call expanduser() for the xdg_state_home in case someone do "~/"
    return (
        Path(xdg_state_home, "command-line-assistant").expanduser()
        if xdg_state_home
        else WANTED_XDG_STATE_PATH
    )


def get_xdg_data_path() -> Path:
    """Check for the existence of XDG_DATA_HOME environment variable.

    In case it is not present, this function will return the default path that
    is `~/.local/share`, which is where we want to place data files for
    Command Line Assistant.

    See: https://specifications.freedesktop.org/basedir-spec/latest/
    """
    xdg_data_home = os.getenv("XDG_DATA_HOME", "")

    # We call expanduser() for the xdg_data_home in case someone do "~/"
    return Path(xdg_data_home).expanduser() if xdg_data_home else WANTED_XDG_DATA_PATH


def get_xdg_config_path() -> Path:
    """Check for the existence of XDG_CONFIG_DIRS environment variable.

    In case it is not present, this function will return the default path that
    is `/etc/xdg`, which is where we want to locate our configuration file for
    Command Line Assistant.

    $XDG_CONFIG_DIRS defines the preference-ordered set of base directories to
    search for configuration files in addition to the $XDG_CONFIG_HOME base
    directory.

        .. note::
            Usually, XDG_CONFIG_DIRS is represented as multi-path separated by a
            ":" where all the configurations files could live. This is not
            particularly useful to us, so we read the environment (if present),
            parse that, and extract only the wanted path (/etc/xdg).

    Ref: https://specifications.freedesktop.org/basedir-spec/latest/
    """
    xdg_config_dirs = os.getenv("XDG_CONFIG_DIRS", "")
    xdg_config_dirs = xdg_config_dirs.split(os.pathsep) if xdg_config_dirs else []

    # In case XDG_CONFIG_DIRS is not set yet, we return the path we want.
    if not xdg_config_dirs:
        return WANTED_XDG_PATH

    # If the total length of XDG_CONFIG_DIRS is just 1, we don't need to
    # proceed on the rest of the conditions. This probably means that the
    # XDG_CONFIG_DIRS was overridden and pointed to a specific location.
    # We hope to find the config file there.
    if len(xdg_config_dirs) == 1:
        return Path(xdg_config_dirs[0])

    # Try to find the first occurrence of the wanted_xdg_dir in the path, in
    # case it is not present, return the default value.
    xdg_dir_found = next(
        (dir for dir in xdg_config_dirs if dir == WANTED_XDG_PATH), WANTED_XDG_PATH
    )
    return Path(xdg_dir_found)
