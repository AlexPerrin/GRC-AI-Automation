#!/bin/sh
set -e

# Substitute environment variables into the nginx config template
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec "$@"
