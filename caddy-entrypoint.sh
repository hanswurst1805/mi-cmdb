#!/bin/sh
set -e

HASH=$(printf '%s' "${ADMIN_PASSWORD}" | caddy hash-password)

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
