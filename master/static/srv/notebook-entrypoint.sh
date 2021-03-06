#!/usr/bin/env bash

set -e

export PATH="/run/determined/pythonuserbase/bin:$PATH"

# If HOME is not explicitly set for a container, libcontainer (Docker) will
# try to guess it by reading /etc/password directly, which will not work with
# our linss_determined plugin (or any user-defined NSS plugin in a container).
# The default is "/", but HOME must be a writable location for distributed
# training, so we try to query the user system for a valid HOME, or default to
# the working directory otherwise.
if [ "$HOME" = "/" ] ; then
    HOME="$(set -o pipefail; getent passwd "$(whoami)" | cut -d: -f6)" || HOME="$WORKING_DIR"
    export HOME
fi

python3.6 -m pip install -q --user /opt/determined/wheels/determined*.whl

jupyter lab --config /run/determined/workdir/jupyter-conf.py --port=${NOTEBOOK_PORT}
