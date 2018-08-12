#!/bin/bash

set -e

DIR=$( dirname "$(readlink -f "$0")" )
CONTAINER_NAME=hilfmir_test
IMAGE_NAME="hilfmir/${CONTAINER_NAME}"

echo 'building image to run tests...'
docker build -t "$IMAGE_NAME" "${DIR}/test"

echo 'running test container...'
docker run \
    --rm \
    --name "$CONTAINER_NAME" \
    --volume "${DIR}/..:/hilfmir" \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    "$IMAGE_NAME"
