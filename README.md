# command-line assistant

Take advantage of the AI-driven expertise of the command-line assistant to help you configure, manage, and troubleshoot RHEL

## Contributing

Contributions are welcome. Take a look at [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to get started.

## Trying CLA

The `command-line assistant` client RPM is available for some versions of RHEL, currently it
is available for RHEL 10 and RHEL 9.

On a RHEL-10 system, after registering with subscription-manager(8) or rhc(8), simply install
the `command-line-assistant` RPM with dnf(8).

```sh
sudo dnf install -y command-line-assistant
```

> **NOTE:**
>
> When a non-standard subscription is being used, before one can ask
> questions through the `command-line assistant`, one needs to alter the
> `command-line assistant` configuration file to include the backend
> endpoint URL and proxy value for the non-standard subscription.
>
> The `command-line assistant` configuration file is maintained here:
> `/etc/xdg/command-line-assistant/config.toml`
>
> In this case modify `/etc/xdg/command-line-assistant/config.toml` to have lines of the form:
>
> ```toml
> [backend]
> endpoint = "https://<custom console hostname>/api/lightspeed/v1"
> proxies = { https = "http://<custom proxy hosthname>:<custom proxy port>" }
> ```
>
> Then restart the `command-line assistant daemon service, clad.service`
>
> ```sh
> systemctl restart clad.service
> ```

Now it will be possible to ask questions through the `command-line assistant`.

```sh
c "How to uninstall RHEL?"
```

## Contact

For questions, troubleshooting, bug reports and feature requests:

* Create [an issue](https://github.com/rhel-lightspeed/command-line-assistant/issues/new) here on GitHub.
