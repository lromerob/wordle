#!/bin/sh
set -eu
: "${WORDLE_APP_USER:?Set WORDLE_DB_USER}"
: "${WORDLE_APP_PASSWORD:?Set WORDLE_DB_PASSWORD outside the repository}"
if [ "$WORDLE_APP_USER" = "$POSTGRES_USER" ]; then
    echo 'Application and initialization roles must be different' >&2
    exit 1
fi
