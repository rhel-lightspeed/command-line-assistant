# Command Line Assistant

A simple wrapper to interact with RAG

## Contributing

Contributions are welcome. Take a look at [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to get started.

## Trying CLA

The `Command Line Assistant` client RPM is available for some versions of RHEL, currently it
is available for RHEL 10 and RHEL 9.

On a RHEL-10 system, after registering with subscription-manager(8) or rhc(8), simply install
the `command-line-assistant` RPM with dnf(8).

```sh
sudo dnf install -y command-line-assistant
```

> **NOTE:**
>
> When a non-standard subscription is being used, before one can ask
> questions through the `Command Line Assistant`, one needs to alter the
> `Command Line Assistant` configuration file to include the backend
> endpoint URL and proxy value for the non-standard subscription.
>
> The `Command Line Assistent` configuration file is maintained here:
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
> Then restart the `Command Line Assistant Daemon Service, clad.service`
>
> ```sh
> systemctl restart clad.service
> ```

Now it will be possible to ask questions through the `Command Line Assistant`.

```sh
c "How to uninstall RHEL?"
```

## Contact

For questions, troubleshooting, bug reports and feature requests:

* Create [an issue](https://github.com/rhel-lightspeed/command-line-assistant/issues/new) here on GitHub.
* Ask a question through [GitHub Discussions](https://github.com/rhel-lightspeed/command-line-assistant/discussions).
