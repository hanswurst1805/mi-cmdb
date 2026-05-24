#!/bin/bash
# Lynis-Audit durchführen und Ergebnis an Mini-CMDB senden.
#
# Verwendung:
#   ./lynis-push.sh https://micb.kiste.org
#
# Voraussetzungen:
#   - lynis installiert (apt install lynis / yum install lynis)
#   - curl installiert
#   - Root-Rechte (für lynis audit system)

set -euo pipefail

CMDB_URL="${1:-https://micb.kiste.org}"
FQDN=$(hostname -f)
REPORT_FILE="/var/log/lynis-report.dat"

echo "==> Starte Lynis-Audit auf ${FQDN}..."
lynis audit system --quiet --report-file "${REPORT_FILE}" || true

if [ ! -f "${REPORT_FILE}" ]; then
  echo "FEHLER: Report-Datei nicht gefunden: ${REPORT_FILE}"
  exit 1
fi

echo "==> Sende Ergebnis an ${CMDB_URL}/api/v1/import/lynis/${FQDN}/raw ..."
CONTENT=$(cat "${REPORT_FILE}")

HTTP_STATUS=$(curl -s -o /tmp/lynis-push-response.json -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"content\": $(echo "${CONTENT}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
  "${CMDB_URL}/api/v1/import/lynis/${FQDN}/raw")

if [ "${HTTP_STATUS}" = "200" ]; then
  echo "==> Erfolgreich übertragen:"
  cat /tmp/lynis-push-response.json
  echo
else
  echo "FEHLER: HTTP ${HTTP_STATUS}"
  cat /tmp/lynis-push-response.json
  exit 1
fi
