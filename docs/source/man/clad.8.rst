.. _clad.8:

=============================
Command Line Assistant Daemon
=============================

Synopsis
--------

In order to run Command Line Assistant Daemon (clad), one need to first enable
the systemd service with the following::

    $ systemctl enable clad

All queries submitted through ``c`` will automatically activate the service.

To check status and logs, run the following::

    $ systemctl status clad

Description
-----------

Command Line Assistant Daemon (clad) is the core of the Command Line Assistant
tooling. It manages the communication with WatsonX API through an external
backend, user history management and much more.

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
    Systemd unit override for clad

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
