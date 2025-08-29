FROM registry.access.redhat.com/ubi10/ubi:latest@sha256:eaa1ccdf1533e02d59eeed435cfb19cab37d4a4ae2d7a0801fa9f1f575654f62 AS base

ENV DNF_DEFAULT_OPTIONS "-y --nodocs --setopt=keepcache=0 --setopt=tsflags=nodocs --setopt=install_weak_deps=False"

# Build the python wheel
FROM base AS build

WORKDIR /project

COPY ./pyproject.toml setup.py requirements.txt README.md LICENSE ./
COPY command_line_assistant/ ./command_line_assistant/

# Install Python, pip, and development tools
RUN dnf install $DNF_DEFAULT_OPTIONS \
        python3.12 \
        python3-setuptools \
        python3-wheel \
        python3-devel \
        cairo-devel \
        gcc \
        g++ \
    && dnf clean all

RUN python3 -m venv --system-site-packages  /opt/venvs/build \
    && /opt/venvs/build/bin/pip install -r requirements.txt \
    && /opt/venvs/build/bin/python setup.py bdist_wheel

FROM base AS final

# Add in data about the build. (These come from Konflux.)
ARG COMMIT_SHA=development
ARG COMMIT_TIMESTAMP=development
ARG VERSION=0.4.2
ARG SOURCE_DATE_EPOCH

# Labels for enterprise contract
LABEL com.redhat.component=rhel-lightspeed-command-line-assistant
LABEL description="Red Hat Enterprise Linux Lightspeed"
LABEL distribution-scope=private
LABEL io.k8s.description="Red Hat Enterprise Linux Lightspeed"
LABEL io.k8s.display-name="RHEL Lightspeed"
LABEL io.openshift.tags="rhel,lightspeed,ai,assistant,rag"
LABEL name=rhel-lightspeed-command-line-assistant
LABEL org.opencontainers.image.created=${SOURCE_DATE_EPOCH}
LABEL release="${VERSION}"
LABEL version=${VERSION}
LABEL url="https://github.com/rhel-lightspeed/command-line-assistant"
LABEL vendor="Red Hat, Inc."
LABEL summary="Red Hat Enterprise Linux Lightspeed"

ENV CLA_VENV /opt/venvs/cla

# Config
COPY data/release/xdg/config.toml /etc/xdg/command-line-assistant/config.toml

RUN sed -i 's/^cert_file = .*/cert_file = "\/run\/secrets\/etc-pki-entitlement\/cert.pem"/' /etc/xdg/command-line-assistant/config.toml \
    && sed -i 's/^key_file = .*/key_file = "\/run\/secrets\/etc-pki-entitlement\/key.pem"/' /etc/xdg/command-line-assistant/config.toml

# Systemd specifics
COPY data/release/systemd/clad.service /usr/lib/systemd/system/clad.service
COPY data/release/systemd/clad.tmpfiles.conf /usr/lib/tmpfiles.d/clad.tmpfiles.conf

# Update ExecStart to match the future cla virtualenv
RUN sed -i "s|^ExecStart=.*|ExecStart=${CLA_VENV}/bin/clad|" /usr/lib/systemd/system/clad.service

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
RUN dnf install $DNF_DEFAULT_OPTIONS python3-gobject-base python3-PyMySQL python3-psycopg2 g++ python3-devel \
    && dnf clean all \
    && rm -rf /var/cache/{dnf,yum}/*

# Install command-line-assistant
RUN python3 -m venv --system-site-packages $CLA_VENV \
    && $CLA_VENV/bin/pip install --no-cache-dir /tmp/command_line_assistant-*.whl \
    && rm -rf /tmp/command_line_assistant-*

# Add cla virtualenv to the PATH env variable
ENV PATH "$CLA_VENV/bin:$PATH"

# This directory is checked by ecosystem-cert-preflight-checks task in Konflux
RUN mkdir /licenses
COPY LICENSE /licenses/

RUN useradd --system --create-home lightspeed
USER lightspeed

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
