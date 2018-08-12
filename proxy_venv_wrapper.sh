#!/bin/bash

DIR=$( dirname "$(readlink -f "$0")" )

source "${DIR}/venv/bin/activate"

"${DIR}/proxy.py" "$@"
