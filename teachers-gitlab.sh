#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 Charles University

BASE_DIR=$(dirname -- "$(realpath -- "$0")")
[ -z "$BASE_DIR" ] && {
    echo "error: unable to find script base directory" >&2
    exit 1
}

#
# Setup virtual environment to avoid Gitlab API compatibility
# issues when using host installations of Python.
#
VENV_DIR="$BASE_DIR/.venv"
REQ_FILE="$BASE_DIR/requirements.txt"

# Update virtual environment if requirements were updated
[ ! -d "$VENV_DIR" -o "$VENV_DIR" -ot "$REQ_FILE" ] && {
    python3 -m venv "$VENV_DIR" && \
    "$VENV_DIR/bin/pip3" install --upgrade pip && \
    "$VENV_DIR/bin/pip3" install --requirement "$REQ_FILE" || {
        echo "error: failed to setup/update virtual environment" >&2
        exit 1
    }

    touch --reference "$REQ_FILE" "$VENV_DIR"
}

#
# Setup PYTHONPATH for the teachers_gitlab module.
#
exec env \
    PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$BASE_DIR/src" \
    "$VENV_DIR/bin/python3" -m teachers_gitlab.main "$@"
