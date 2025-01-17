# RPM Specific
%define python_package_src command_line_assistant
%define binary_name c
%define daemon_binary_name clad

# SELinux specific
%define relabel_files() \
restorecon -R /usr/sbin/clad; \
restorecon -R /etc/xdg/command-line-assistant/config.toml; \
restorecon -R /etc/xdg/command-line-assistant; \
restorecon -R /var/lib/command-line-assistant; \
restorecon -R /var/log/command-line-assistant; \
restorecon -R /var/log/command-line-assistant/audit.log; \

%define selinux_policyver 41.27-1

%define selinuxtype targeted
%define modulename %{daemon_binary_name}

Name:           command-line-assistant
Version:        0.1.0
Release:        1%{?dist}
Summary:        A simple wrapper to interact with RAG

License:        Apache-2.0
URL:            https://github.com/rhel-lightspeed/command-line-assistant
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
# noarch because there is no extension module for this package.
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  python3-pip
BuildRequires:  systemd-units

# Build dependencies for SELinux policy
BuildRequires:  selinux-policy-devel

Requires:       python3-dasbus
Requires:       python3-requests
Requires:       python3-sqlalchemy
Requires:       systemd
# Add selinux subpackge as dependency
Requires:       %{name}-selinux

# Not needed after RHEL 10 as it is native in Python 3.11+
%if 0%{?rhel} && 0%{?rhel} < 10
BuildRequires:  python3-tomli
Requires:       python3-tomli
%endif

# Ref: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python_201x/#_automatically_generated_dependencies
%{?python_disable_dependency_generator}

%description
A simple wrapper to interact with RAG

%package selinux
Summary:	CLAD SELinux policy
BuildArch:	noarch

Requires:       selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-%{selinuxtype}

%description selinux
This package installs and sets up the  SELinux policy security module for clad.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build_wheel

# Build selinux policy file
pushd data/release/selinux
%{__make} %{modulename}.pp.bz2
popd

%install
%py3_install_wheel %{python_package_src}-%{version}-py3-none-any.whl

# Create needed directories in buildroot
%{__install} -d %{buildroot}/%{_sbindir}
%{__install} -d %{buildroot}/%{_sysconfdir}/xdg/%{name}
%{__install} -d %{buildroot}/%{_sharedstatedir}/%{name}
%{__install} -d %{buildroot}/%{_localstatedir}/log/%{name}
%{__install} -d %{buildroot}/%{_mandir}/man1
%{__install} -d %{buildroot}/%{_mandir}/man8
%{__install} -d %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}

# Move the daemon to /usr/sbin instead of /usr/bin
%{__install} -m 0755 %{buildroot}/%{_bindir}/%{daemon_binary_name} %{buildroot}/%{_sbindir}/%{daemon_binary_name}
%{__rm} %{buildroot}/%{_bindir}/%{daemon_binary_name}

# System units
%{__install} -D -m 0644 data/release/systemd/%{daemon_binary_name}.service %{buildroot}/%{_unitdir}/%{daemon_binary_name}.service

# d-bus policy config
%{__install} -D -m 0644 data/release/dbus/com.redhat.lightspeed.conf %{buildroot}/%{_sysconfdir}/dbus-1/system.d/com.redhat.lightspeed.conf
%{__install} -D -m 0644 data/release/dbus/com.redhat.lightspeed.query.service %{buildroot}/%{_datadir}/dbus-1/system-services/com.redhat.lightspeed.query.service
%{__install} -D -m 0644 data/release/dbus/com.redhat.lightspeed.history.service %{buildroot}/%{_datadir}/dbus-1/system-services/com.redhat.lightspeed.history.service

# Config file
%{__install} -D -m 0644 data/release/xdg/config.toml %{buildroot}/%{_sysconfdir}/xdg/%{name}/config.toml

# Manpages
%{__install} -D -m 0644 data/release/man/%{binary_name}.1 %{buildroot}/%{_mandir}/man1/%{binary_name}.1
%{__install} -D -m 0644 data/release/man/%{daemon_binary_name}.8 %{buildroot}/%{_mandir}/man8/%{daemon_binary_name}.8

# selinux
%{__install} -m 0644 data/release/selinux/%{modulename}.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2

%preun
%systemd_preun %{daemon_binary_name}.service

%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post
%systemd_post %{daemon_binary_name}.service

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2

%postun
%systemd_postun_with_restart %{daemon_binary_name}.service

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{modulename}
fi

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files
%doc README.md
%license LICENSE
%{python3_sitelib}/%{python_package_src}/
%{python3_sitelib}/%{python_package_src}-%{version}.dist-info/

# Binaries
%{_bindir}/%{binary_name}
%{_sbindir}/%{daemon_binary_name}

# System units
%{_unitdir}/%{daemon_binary_name}.service

# d-bus policy config
%config %{_sysconfdir}/dbus-1/system.d/com.redhat.lightspeed.conf
%{_datadir}/dbus-1/system-services/com.redhat.lightspeed.query.service
%{_datadir}/dbus-1/system-services/com.redhat.lightspeed.history.service

# Config file
%config %{_sysconfdir}/xdg/%{name}/config.toml

# Manpages
%{_mandir}/man1/%{binary_name}.1.gz
%{_mandir}/man8/%{daemon_binary_name}.8.gz

# Needed directories
%dir %{_sharedstatedir}/%{name}
%dir %{_localstatedir}/log/%{name}

%files selinux
%attr(0600,root,root) %{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{modulename}

%changelog
* Wed Jan 22 2025 Rodolfo Olivieri <rolivier@redhat.com> 0.2.0
- Add workaround for SQLite UUID types
- Update packaging to include selinux custom policy
- Fix returncode when running commands
- Refactor the CLI to be separate commands
- Add an experimental rendering module for client
- Add Command Line Assistant Daemon
- Update specfile to include config from release dir
- Split the query and history dbus implementations
- Switch to system bus instead of session bus
- Add schema for input/output queries and history
- The connect_signals was triggered the API request twice
- Add local history management and improve the command
- Query against rlsrag
- Improve error handling
- Update systemd units to be socket activated
- Add 100% docstring coverage
- Fix query read from stdin
- Remove colorama dep
- Apply NO_COLOR to colored output
- Generate manpages for CLA and CLAD
- Prevent binary stdin
- Add audit logging capability to CLAD
- Add exception handling for SSL certificates
- Normalize the folder name to command-line-assistant
- Small code refactor for outputting text
- Update legal message
- Remove record command
- Fix config.toml for release and devel
- Add audit logging to stdout
- Add filter history option
- Implement a basic user session management
- Add input field for query by
- Migrate JSON history cache to database solution
- Fix ordering from history results
- Add user_id to history tables.
- Update manpages for RH1

* Mon Nov 25 2024 Rodolfo Olivieri <rolivier@redhat.com> 0.1.0
- Initial release of Command Line Assistant
- Rework config file handler and history
- Remove leftover yaml import from utils
- Fix config and history wrong paths
- Add option to disable SSL verification on backend
- Drop builds for EPEL 8
- Remove leftover yaml config file
- Refactor to use dataclasses instead of namedtuple
- Improve logging
- Transform dict to schema config
- Append stdin to the user query
- Convert the config class to be a dataclass
- Remove use of slots in dataclasses
