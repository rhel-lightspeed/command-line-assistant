FROM registry.access.redhat.com/ubi10/ubi:latest@sha256:eaa1ccdf1533e02d59eeed435cfb19cab37d4a4ae2d7a0801fa9f1f575654f62 AS base

# Build the python wheel
FROM base AS build

WORKDIR /project

COPY ./pyproject.toml ./uv.lock README.md LICENSE ./
COPY command_line_assistant/ ./command_line_assistant/

RUN subscription-manager --refresh

# Install Python, pip, and development tools
RUN dnf install -y --enablerepo=rhel-CRB-latest \
        python3.12 \
        python3.12-pip \
        python3-setuptools \
        python3-wheel \
        python3-devel \
        gcc \
        cairo-devel \
        cairo-gobject \
        cairo-gobject-devel \
        gobject-introspection \
        gobject-introspection-devel \
        cmake \
    && dnf clean all

RUN pip install uv \
    && uv sync \
    && uv build --wheel

FROM base

# Add in data about the build. (These come from Konflux.)
ARG COMMIT_SHA=development
ARG COMMIT_TIMESTAMP=development
ARG VERSION=0.4.2

# Labels for enterprise contract
LABEL com.redhat.component=rhel-lightspeed-command-line-assistant
LABEL description="Red Hat Enterprise Linux Lightspeed"
LABEL distribution-scope=private
LABEL io.k8s.description="Red Hat Enterprise Linux Lightspeed"
LABEL io.k8s.display-name="RHEL Lightspeed"
LABEL io.openshift.tags="rhel,lightspeed,ai,assistant,rag"
LABEL name=rhel-lightspeed-command-line-assistant
LABEL release="${VERSION}"
LABEL version=${VERSION}
LABEL url="https://github.com/rhel-lightspeed/command-line-assistant"
LABEL vendor="Red Hat, Inc."
LABEL summary="Red Hat Enterprise Linux Lightspeed"

# Config
COPY data/release/xdg/config.toml /etc/xdg/command-line-assistant/config.toml
RUN sed -i 's/^cert_file = .*/cert_file = "\/run\/secrets\/etc-pki-entitlement\/cert.pem"/' /etc/xdg/command-line-assistant/config.toml \
    && sed -i 's/^key_file = .*/key_file = "\/run\/secrets\/etc-pki-entitlement\/key.pem"/' /etc/xdg/command-line-assistant/config.toml

# Systemd specifics
COPY data/release/systemd/clad.service /usr/lib/systemd/system/clad.service
COPY data/release/systemd/clad.tmpfiles.conf /usr/lib/tmpfiles.d/clad.tmpfiles.conf

# Dbus specifics
COPY data/release/dbus/*.service /usr/share/dbus-1/system-services/
COPY data/release/dbus/com.redhat.lightspeed.conf /usr/share/dbus-1/system.d/com.redhat.lightspeed.conf

# Manpages
COPY data/release/man/c.1 /usr/share/man/man1/
COPY data/release/man/c.1 /usr/share/man/man1/cla.1
COPY data/release/man/clad.8 /usr/share/man/man/8

# The wheel build
COPY --from=build /project/dist/command_line_assistant-*.whl /tmp/

# Setup required packages
RUN dnf install -y --nodocs --setopt=keepcache=0 --setopt=tsflags=nodocs shadow-utils python3-pip python3-PyMySQL python3-psycopg2

# Install command-line-assistant
RUN pip install --prefix=/usr --no-cache-dir /tmp/command_line_assistant-*.whl \
    && rm -rf /tmp/command_line_assistant-*

# Cleanup
RUN dnf remove -y python3-pip \
    && dnf clean all && rm -rf /var/cache/{dnf,yum}*/var/tmp/*

# This directory is checked by ecosystem-cert-preflight-checks task in Konflux
RUN mkdir /licenses
COPY LICENSE /licenses/

RUN useradd --system --create-home lightspeed
USER lightspeed

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
