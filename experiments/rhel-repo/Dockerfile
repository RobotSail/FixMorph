# this dockerfile assumes that working directory
# is the bind source directory
FROM fixmorph:local as fixmorph-installer

FROM fedora:40 as system

USER root

ENV HOME_PATH="/opt/fixmorph"

COPY --from=fixmorph-installer "${HOME_PATH}" "${HOME_PATH}" 

WORKDIR "${HOME_PATH}"

RUN dnf update -y

# install the fixmorph version of python3
RUN dnf install -y python3.11 
RUN python3.11 -m ensurepip
RUN python3.11 -m pip install -r requirements.txt

RUN dnf groupinstall -y 'Development Tools'
RUN dnf install -y git \
        make \
        gcc \
        g++ \
        autoconf \
        automake \
        pkg-config \
        vim \
        #  libguestfs
        libguestfs libguestfs-devel \
        # * OCaml bindings for libguestfs
        ocaml-libguestfs \
        # * OCaml bindings for libvirt (https://gitlab.com/libvirt/libvirt-ocaml)
        ocaml-libvirt \
        # * libnbd >= 1.9.3 (https://gitlab.com/nbdkit/libnbd)
        libnbd libnbd-devel \
        # * OCaml bindings for libnbd
        ocaml-libnbd-devel \
        # * nbdkit >= 1.27.4 (https://gitlab.com/nbdkit/nbdkit)
        nbdkit \
        # * These nbdkit plugins and filters:
        #   + nbdkit-curl-plugin
        nbdkit-curl-plugin \
        #   + nbdkit-file-plugin
        nbdkit-file-plugin \
        #   + nbdkit-nbd-plugin
        nbdkit-nbd-plugin \
        #   + nbdkit-null-plugin
        nbdkit-null-plugin \
        #   + nbdkit-python-plugin
        nbdkit-python-plugin \
        #   + nbdkit-ssh-plugin
        nbdkit-ssh-plugin \
        #   + nbdkit-vddk-plugin
        nbdkit-vddk-plugin \
        #   + nbdkit-cacheextents-filter
        nbdkit-cacheextents-filter \
        #   + nbdkit-cow-filter
        nbdkit-cow-filter \
        #   + nbdkit-multi-conn-filter
        nbdkit-multi-conn-filter \
        #   + nbdkit-rate-filter
        nbdkit-rate-filter \
        #   + nbdkit-retry-filter
        nbdkit-retry-filter \
        # * qemu-nbd
        # qemu-nbd may be provided by qemu-img
        # qemu-nbd \
        # * qemu-img
        qemu-img \
        # Optional, for enhancements to the basic program:
        # * OCaml gettext
        ocaml-gettext \
        # additional dependencies
        pcre2-devel \
        libvirt \
        libvirt-devel \
        gettext \
        gettext-devel \
        binutils-arc-linux-gnu \
        libtool \
        xorriso \
        libxml2 \
        libxml2-devel \
        jansson \
        jansson-devel \
        libosinfo \
        libosinfo-devel \
        ocaml-findlib

# RUN DEBIAN_FRONTEND=noninteractive apt install -y make gcc g++ git  \
#     pkg-config \
#     # libuv1-dev \
#     libcap-dev \
#     build-essential \
#     vim \
#     gettext \
#     libguestfs-tools \
#     libguestfs-ocaml \
#     libvirt-ocaml \
#     libnbd-bin \
#     libnbd-dev \
#     libnbd-ocaml \
#     libnbd-ocaml-dev \
#     libnbd0 \
#     nbdkit \
#     nbdkit-plugin-curl

# enable vim keybinds
ENV VISUAL='vim'
RUN echo "set -o vi" >> /root/.bashrc
RUN echo "export VISUAL=vim" >> /root/.bashrc

# enable settings within vim
RUN echo "set number" >> /root/.vimrc
RUN echo "set relativenumber" >> /root/.vimrc


ARG PKG_NAME='virt-v2v'
ARG GIT_EMAIL='user@example.com'
ARG GIT_NAME='user'

RUN git config --global user.email "${GIT_EMAIL}"
RUN git config --global user.name "${GIT_NAME}"

ENV SRC_PATH_A="/dirs/${PKG_NAME}-a"
ENV SRC_PATH_B="/dirs/${PKG_NAME}-b"
ENV SRC_PATH_C="/dirs/${PKG_NAME}-c"

# these commands do nothing
ARG CONFIG_COMMAND_A="echo 'hello world'"
ARG CONFIG_COMMAND_B="echo 'hello world'"
ARG CONFIG_COMMAND_C="echo 'hello world'"

ARG BUILD_COMMAND_A="make -j"
ARG BUILD_COMMAND_C="make -j"
ARG BUILD_COMMAND_B="make -j"


# now create 3 different copies of the source
# COPY ./rpms/iotop-c/iotop-1.25 "${SRC_PATH_A}"
# COPY ./rpms/iotop-c/iotop-1.25 "${SRC_PATH_B}"
# COPY ./rpms/iotop-c/iotop-1.25 "${SRC_PATH_C}"

COPY "./${PKG_NAME}" "${SRC_PATH_A}"

# # move over the patches and apply them to the relevant directories
# COPY ./iotop-c.patch "${SRC_PATH_B}/iotop-c-b.patch"
# COPY ./iotop-c-backport.patch "${SRC_PATH_C}/iotop-c-c.patch"

# we now want to make sure we can compile the source
WORKDIR "${SRC_PATH_A}"

RUN git submodule update --init
RUN autoupdate
RUN autoreconf -i 
RUN ./configure
RUN GOEXPERIMENT=cgocheck2 make

