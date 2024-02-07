#!/bin/bash

# prevent the script from progressing on error
set -e -o pipefail

## The purpose of this script is to demonstrate
## how to configure a system to be able to build
## the bind9 package from source.

function install_prereqs() {
    sudo dnf install -y libuv libuv-devel \
        openssl openssl-devel \
        libcap libcap-devel
    
    # install python pre-reqs, using system python
    /usr/bin/python -m pip install -r requirements.txt
}

function build_bind() {
    local include_deps=false
    if [[ "${1}" == "--include-deps" ]]; then
        printf "Including dependencies\n"
        include_deps=true
    fi
    # path to the bind repository
    local bind_directory='./bind/bind-9.16.23'
    pushd $bind_directory

    # configure bind
    ./configure --without-python

    # compiles bind
    make
    
    # installs all dependencies
    if [[ "${include_deps}" == true ]]; then
        make depend
    fi
    popd
}


case "${1}" in
    install_prereqs)
        install_prereqs
        ;;
    build_bind)
        # pass in all remaining arguments to build_bind
        build_bind "${@:2}"
        ;;
    *)
        echo "Usage: $0 {install_prereqs|build_bind [--include-deps]}"
        exit 1
esac