#!/bin/sh
set -eu

if [ ! -r /run/secrets/redis_password ]; then
  echo "Redis password secret is missing or unreadable" >&2
  exit 1
fi

REDIS_PASSWORD="$(cat /run/secrets/redis_password)"

exec redis-server --requirepass "$REDIS_PASSWORD"
