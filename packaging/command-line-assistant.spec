%global python_package_src command_line_assistant
%global binary_name c
%global daemon_binary_name clad

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

Requires:       python3-dasbus
Requires:       python3-requests
Requires:       systemd

# Not needed after RHEL 10 as it is native in Python 3.11+
%if 0%{?rhel} && 0%{?rhel} < 10
BuildRequires:  python3-tomli
Requires:       python3-tomli
%endif

%description
A simple wrapper to interact with RAG

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build_wheel

%install
%py3_install_wheel %{python_package_src}-%{version}-py3-none-any.whl

# Create needed directories in buildroot
%{__install} -d %{buildroot}/%{_sbindir}
%{__install} -d %{buildroot}/%{_sysconfdir}/xdg/%{python_package_src}
%{__install} -d %{buildroot}/%{_sharedstatedir}/%{name}
%{__install} -d %{buildroot}/%{_mandir}/man1
%{__install} -d %{buildroot}/%{_mandir}/man8

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
%{__install} -D -m 0644 data/release/xdg/config.toml %{buildroot}/%{_sysconfdir}/xdg/%{python_package_src}/config.toml

# History file
%{__install} -D -m 0644 data/release/xdg/history.json %{buildroot}/%{_sharedstatedir}/%{name}/history.json

# Manpages
%{__install} -D -m 0644 data/release/man/%{binary_name}.1 %{buildroot}/%{_mandir}/man1/%{binary_name}.1
%{__install} -D -m 0644 data/release/man/%{daemon_binary_name}.8 %{buildroot}/%{_mandir}/man8/%{daemon_binary_name}.8

%post
%systemd_post %{daemon_binary_name}.service

%preun
%systemd_preun %{daemon_binary_name}.service

%postun
%systemd_postun_with_restart %{daemon_binary_name}.service

%doc
README.md

%license
LICENSE

%files
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
%config %{_sysconfdir}/xdg/%{python_package_src}/config.toml

# History file
%{_sharedstatedir}/%{name}/history.json

# Manpages
%{_mandir}/man1/%{binary_name}.1.gz
%{_mandir}/man8/%{daemon_binary_name}.8.gz

%changelog
