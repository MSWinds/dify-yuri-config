#!/bin/bash

HTTPS_CONFIG=''
NGINX_REDIRECT_CONF=''
# When HTTPS is enabled with redirect, the main server only listens on SSL.
# When HTTPS is disabled, the main server listens on the HTTP port.
LISTEN_DIRECTIVE="listen ${NGINX_PORT};"

if [ "${NGINX_HTTPS_ENABLED}" = "true" ]; then
    # Check if the certificate and key files for the specified domain exist
    if [ -n "${CERTBOT_DOMAIN}" ] && \
       [ -f "/etc/letsencrypt/live/${CERTBOT_DOMAIN}/${NGINX_SSL_CERT_FILENAME}" ] && \
       [ -f "/etc/letsencrypt/live/${CERTBOT_DOMAIN}/${NGINX_SSL_CERT_KEY_FILENAME}" ]; then
        SSL_CERTIFICATE_PATH="/etc/letsencrypt/live/${CERTBOT_DOMAIN}/${NGINX_SSL_CERT_FILENAME}"
        SSL_CERTIFICATE_KEY_PATH="/etc/letsencrypt/live/${CERTBOT_DOMAIN}/${NGINX_SSL_CERT_KEY_FILENAME}"
    else
        SSL_CERTIFICATE_PATH="/etc/ssl/${NGINX_SSL_CERT_FILENAME}"
        SSL_CERTIFICATE_KEY_PATH="/etc/ssl/${NGINX_SSL_CERT_KEY_FILENAME}"
    fi
    export SSL_CERTIFICATE_PATH
    export SSL_CERTIFICATE_KEY_PATH

    # set the HTTPS_CONFIG environment variable to the content of the https.conf.template
    HTTPS_CONFIG=$(envsubst < /etc/nginx/https.conf.template)
    export HTTPS_CONFIG
    # Substitute the HTTPS_CONFIG in the default.conf.template with content from https.conf.template
    envsubst '${HTTPS_CONFIG}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

    # Generate HTTP -> HTTPS redirect config as a separate file (avoids multiline env var issues)
    envsubst '${NGINX_PORT} ${NGINX_SERVER_NAME}' < /etc/nginx/redirect.conf.template > /etc/nginx/conf.d/redirect.conf

    # When redirect is enabled, remove the HTTP listen from the main server block.
    # The SSL listen directive comes from HTTPS_CONFIG (https.conf.template).
    LISTEN_DIRECTIVE=""
fi
export HTTPS_CONFIG
export LISTEN_DIRECTIVE

if [ "${NGINX_ENABLE_CERTBOT_CHALLENGE}" = "true" ]; then
    ACME_CHALLENGE_LOCATION='location /.well-known/acme-challenge/ { root /var/www/html; }'
else
    ACME_CHALLENGE_LOCATION=''
fi
export ACME_CHALLENGE_LOCATION

env_vars=$(printenv | cut -d= -f1 | sed 's/^/$/g' | paste -sd, -)

envsubst "$env_vars" < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
envsubst "$env_vars" < /etc/nginx/proxy.conf.template > /etc/nginx/proxy.conf

envsubst "$env_vars" < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start Nginx using the default entrypoint
exec nginx -g 'daemon off;'
