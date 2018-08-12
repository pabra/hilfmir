#!/bin/bash
set -e

DIR=$( dirname "$(readlink -f "$0")" )
SELF=$DIR/$( basename "$0" )
SELF_AGE=$(( $( date +%s ) - $( date -r "$SELF" +%s ) ))
AGE_THRESHOLD=86400 # one day

echo "self: '${SELF}'"
echo "age: '${SELF_AGE}'"

if [ $SELF_AGE -lt $AGE_THRESHOLD ]; then
    echo "Already checked within last $AGE_THRESHOLD seconds."
    exit
fi

cd "$DIR" || exit 1
git pull
source venv/bin/activate
pip install -r requirements.txt

touch "$SELF"
