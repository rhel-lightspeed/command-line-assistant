import os

# The wanted xdg path where the configuration files will live.
WANTED_XDG_PATH = "/etc/xdg"


def get_xdg_path() -> str:
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
            particularily useful to us, so we read the environment (if present),
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
    # XDG_CONFIG_DIRS was overrided and pointed to a specific location.
    # We hope to find the config file there.
    if len(xdg_config_dirs) == 1:
        return xdg_config_dirs[0]

    # Try to find the first occurence of the wanted_xdg_dir in the path, in
    # case it is not present, return the default value.
    xdg_dir_found = next(
        (dir for dir in xdg_config_dirs if dir == WANTED_XDG_PATH), WANTED_XDG_PATH
    )
    return xdg_dir_found
