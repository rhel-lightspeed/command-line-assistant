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
# Not needed after RHEL 10 as it is native in Python 3.11+
%if 0%{?rhel} && 0%{?rhel} < 10
BuildRequires:  python3-tomli
%endif

Requires:       python3-requests
# Not needed after RHEL 10 as it is native in Python 3.11+
%if 0%{?rhel} && 0%{?rhel} < 10
Requires:  python3-tomli
%endif

%global python_package_src command_line_assistant
%global binary_name c

%description
A simple wrapper to interact with RAG

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%files
%doc README.md
%license LICENSE
%{python3_sitelib}/%{python_package_src}/
%{python3_sitelib}/%{python_package_src}-*.egg-info/
# Our binary is just called "c"
%{_bindir}/%{binary_name}

%changelog
