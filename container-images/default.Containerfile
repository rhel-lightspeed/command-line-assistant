FROM registry.access.redhat.com/ubi10/ubi:latest AS base

ENV DNF_DEFAULT_OPTS -y --nodocs --setopt=keepcache=0 --setopt=tsflags=nodocs

# Add in data about the build. (These come from Konflux.)
ARG COMMIT_SHA=development
ARG COMMIT_TIMESTAMP=development
ARG VERSION=0.4.0
ENV VERSION=${VERSION}
ENV COMMIT_SHA=${COMMIT_SHA} \
    COMMIT_TIMESTAMP=${COMMIT_TIMESTAMP}

RUN dnf install ${DNF_DEFAULT_OPTS} \
    python3.12 \
    python3.12-pip

FROM base as build

WORKDIR /project

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY ./pyproject.toml ./poetry.lock* README.md LICENSE ./
COPY command_line_assistant/ ./command_line_assistant/

RUN dnf install ${DNF_DEFAULT_OPTS} \
    gcc \
    python3-devel \
    python3-setuptools \
    python3-wheel

RUN pip3.12 install -U poetry && poetry install

RUN poetry build --clean --format=wheel

FROM base as final

COPY --from=build /project/dist/command_line_assistant-${VERSION}-py3-none-any.whl /tmp/

RUN dnf install ${DNF_DEFAULT_OPTS} python3-PyMySQL python3-psycopg2 \
    && pip install --prefix=/usr --no-cache-dir /tmp/command_line_assistant-${VERSION}-py3-none-any.whl \
    && dnf remove -y python3-pip \
    && dnf clean all && rm -rf /var/cache/dnf /var/tmp/* /tmp/*

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

# Konflux specifics
# This directory is checked by ecosystem-cert-preflight-checks task in Konflux
RUN mkdir /licenses
COPY LICENSE /licenses/

# NOTE(r0x0d): As of July 2nd, we are only creating the user but not
# "activating" it with the `USER` directive. The reason for that is that we
# need to initiate systemd, and that requires root permissions. The user will
# be available to be used through the `--user` cli flag exposed in the `exec`
# command, so that is an initial start.
RUN useradd --system --create-home lightspeed

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

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
