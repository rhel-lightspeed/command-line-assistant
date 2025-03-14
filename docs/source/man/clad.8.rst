.. _clad.8:

=============================
Command Line Assistant Daemon
=============================

Synopsis
--------

The command line assistant daemon (clad), is a dbus activated daemon, meaning
that, any interaction with it will activate the service when it receive a
message in the expected channels, like this::

    $ c "what is selinux?"

To check status and logs, run the following::

    $ systemctl status clad

Description
-----------

Command line assistant daemon (clad) is the core of the command line assistant
tooling. It manages the communication with Red Hat RHEL Lightspeed service,
user history management and much more.

Examples
--------

* **Setting a proxy configuration**

    `clad` supports proxy configuration via config file or via environment
    variables. To update them through the configuration file, one must change
    the following block::

        # Backend settings for communicating with the external API.
        [backend]
        ...
        # proxies = { http = "http://example-host:8002", https = "https://example-host:8002" }

    First, uncomment the `proxies` key and then you can define your `http` or
    `http(s)` proxy host as following::

        [backend]
        ...
        # For a http proxy host
        proxies = { http = "http://my-super-proxy-host:1234"}

        [backend]
        ...
        # For a http proxy host
        proxies = { https = "https://my-super-https-proxy-host:1234"}

* **Database management**

    * **Changing databases in the config file**

        By default, `clad` will use an uncrypted sqlite database to hold
        history and some other informations. If you want to change this
        default, you can simply comment the sqlite configuration and add either
        `postgres` or `mysql`/ `mariadb` configs instead, like this::

            # History Database settings. By default, sqlite is used.
            [database]
            # type = "sqlite"
            # connection_string = "/var/lib/command-line-assistant/history.db"

        To add a `postgres` database config, add the following keys under the
        `[database]` field and configure to use the correct host, username and
        password::

            # type = "postgresql"
            # host = "localhost"
            # port = "5432"
            # username = "your-user"
            # password = "your-password"
            # database = "history"

        In case you prefer `mysql` or `mariadb`, please use the following::

            # type = "mysql"
            # host = "localhost"
            # port = "3306"
            # username = "your-user"
            # password = "your-password"
            # database = "history"

        After changing the database type, restart `clad` unit to apply the changes::

            systemctl restart clad

    * **Adding new secrets for database management**

        This setting will only work for `postgres` and `mysql` databases for
        now. This is a more secure option as we use systemd to store the
        credentials for the database using `systemd-creds`. How it works is
        very simple, first, remove the `username` and `password` from the
        configuration file, like this::

            [database]
            type = "postgresql"
            host = "localhost"
            port = "5432"
            database = "history"

        After that, you can use the below `systemd-ask-password` commands to
        generate encrypted credentials for your username/password::

            # Generate an encrypted username
            systemd-ask-password -n | ( echo "[Service]" && systemd-creds encrypt --name=database-username -p - - ) >/etc/systemd/system/clad.service.d/50-username.conf

            # Generate an encrypted password
            systemd-ask-password -n | ( echo "[Service]" && systemd-creds encrypt --name=database-password -p - - ) >/etc/systemd/system/clad.service.d/50-password.conf

        After changing the database type, restart `clad` unit to apply the changes::

            systemctl restart clad

        > WARNING: `clad` needs the name to follow the above schema of
        `database-username` and `database-password`, otherwise, it won't load
        up the credentials properly.

Files
-----

*/etc/xdg/command-line-assistant/config.toml*
    System configuration file

*/var/lib/command-line-assistant/history.db*
    SQlite3 history database

*/etc/dbus-1/system.d/com.redhat.lightspeed.conf*
    D-Bus conf to control access of bus activation

*/usr/share/dbus-1/system-services/com.redhat.lightspeed.chat.service*
    Service to enable dbus activation from chat endpoint

*/usr/share/dbus-1/system-services/com.redhat.lightspeed.history.service*
    Service to enable dbus activation from history endpoint

*/usr/lib/systemd/system/clad.service*
    Systemd service file for clad

*/etc/systemd/system/clad.service.d/*
    Folder to override systemd unit configurations for clad. Mainly used for adding database secrets.

Reference
---------

1. Command Line Assistant Daemon source code: <https://github.com/rhel-lightspeed/command-line-assistant>

Bugs
----

To submit bug reports, please use the following link:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=1&components=12410340>

In case to submit feature requests, please use the following link:
<https://issues.redhat.com/secure/CreateIssueDetails!init.jspa?pid=12332745&priority=10200&issuetype=3&components=12410340>

See Also
--------

**c(1)**
