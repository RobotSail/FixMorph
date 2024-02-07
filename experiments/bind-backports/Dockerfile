# this dockerfile assumes that working directory
# is the bind source directory
# FROM ubuntu:20.04 as builder
FROM fixmorph:local as fixmorph

USER root

RUN apt update

# WORKDIR /bind

# enable vim keybinds
RUN echo "set -o vi" >> /root/.bashrc

RUN DEBIAN_FRONTEND=noninteractive apt install -y make gcc g++ git wget curl \
    autoconf \
    automake \
    libtool \
    openssl \
    libssl-dev \
    pkg-config \
    libuv1-dev \
    libcap-dev \
    vim

# COPY . .

# RUN ./configure --without-python


WORKDIR /FixMorph

ENV SRC_PATH_A='/dirs/bind-a'
ENV SRC_PATH_B='/dirs/bind-b'
ENV SRC_PATH_C='/dirs/bind-c'

ENV CONFIG_COMMAND_A="CC='clang' ./configure --without-python --with-libtool"
ENV CONFIG_COMMAND_B="CC='clang' ./configure --without-python --with-libtool"
ENV CONFIG_COMMAND_C="CC='clang' ./configure --without-python --with-libtool"

ENV BUILD_COMMAND_A="CC='clang' make all depend"
ENV BUILD_COMMAND_C="CC='clang' make all depend"
ENV BUILD_COMMAND_B="CC='clang' make all depend"

# now create 3 different copies of the source
COPY . "${SRC_PATH_A}"
COPY . "${SRC_PATH_B}"
COPY . "${SRC_PATH_C}"

# create a repair.conf file
RUN printf 'path_a:%s\npath_b:%s\npath_c:%s\nconfig_command_a:%s\nconfig_command_b:%s\nconfig_command_c:%s\nbuild_command_a:%s\nbuild_command_b:%s\nbuild_command_c:%s\n' \
    "${SRC_PATH_A}" \
    "${SRC_PATH_B}" \
    "${SRC_PATH_C}" \
    "${CONFIG_COMMAND_A}" \
    "${CONFIG_COMMAND_B}" \
    "${CONFIG_COMMAND_C}" \
    "${BUILD_COMMAND_A}" \
    "${BUILD_COMMAND_B}" \
    "${BUILD_COMMAND_C}" > /FixMorph/repair.conf

# now we want to slightly modify a file in the source of bind-c
RUN sed -i 's/send_forward_event/new_send_forward_event/g' /dirs/bind-c/lib/ns/update.c

# now we want to make modifications to the bind-b source
RUN sed -i '13i#include <stdio.h>' /dirs/bind-b/lib/ns/update.c
RUN sed -i '3574i        printf("Hello world!");' /dirs/bind-b/lib/ns/update.c

# make running the script easier
RUN echo "python FixMorph.py --conf=repair.conf --debug" > /FixMorph/cmd
RUN chmod +x /FixMorph/cmd



ENTRYPOINT bash