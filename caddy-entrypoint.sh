#!/bin/sh
set -e

# htpasswd fuer bcrypt-Hash-Generierung installieren (klein, schnell)
apk add --no-cache apache2-utils > /dev/null 2>&1

# bcrypt-Hash aus ADMIN_PASSWORD generieren ($2y$ Format, von Caddy akzeptiert)
HASH=$(htpasswd -bnB "${ADMIN_USERNAME}" "${ADMIN_PASSWORD}" | cut -d: -f2 | tr -d '\n\r')

cat > /tmp/Caddyfile << EOF
micb.kiste.org {
    reverse_proxy app:8000
}

ocs.kiste.org {
    basic_auth {
        ${ADMIN_USERNAME} ${HASH}
    }
    redir / /ocsreports/ 302
    reverse_proxy ocs:80
}
EOF

exec caddy run --config /tmp/Caddyfile --adapter caddyfile
