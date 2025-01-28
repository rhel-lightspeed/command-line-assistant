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

*/etc/dbus-1/systemd/com.redhat.lightspeed.conf*
    D-Bus conf to control access of bus activation

*/usr/share/dbus-1/system-services/com.redhat.lightspeed.chat.srvice*
    Service to enable dbus activation from chat endpoint

*/usr/share/dbus-1/system-services/com.redhat.lightspeed.history.srvice*
    Service to enable dbus activation from history endpoint

*/usr/lib/systemd/system/clad.service*
    Systemd service file for clad

Reference
---------

1. Command Line Assistant Daemon source code: https://github.com/rhel-lightspeed/command-line-assistant

Bugs
----

Please send bug reports to our bug tracker, see https://issues.redhat.com/browse/RSPEED

See Also
--------

**c(1)**
