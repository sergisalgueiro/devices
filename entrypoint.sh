#!/bin/sh
set -e

if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

exec "$@"
