#!/usr/bin/env bash
# Prueba de red: un anfitrión y un invitado en la misma máquina.
# Uso: tools/test_net.sh   (variable GODOT para usar otro ejecutable)
set -u
GODOT="${GODOT:-godot}"
cd "$(dirname "$0")/.."
LOG_DIR="$(mktemp -d)"

"$GODOT" --headless --path . -s tests/net/net_smoke.gd -- --role=host >"$LOG_DIR/host.log" 2>&1 &
HOST_PID=$!
sleep 1.5
"$GODOT" --headless --path . -s tests/net/net_smoke.gd -- --role=client >"$LOG_DIR/client.log" 2>&1
CLIENT_STATUS=$?
wait "$HOST_PID"
HOST_STATUS=$?

grep -h -E "^\[(host|client)\]" "$LOG_DIR/host.log" "$LOG_DIR/client.log"
if [ "$HOST_STATUS" -ne 0 ] || [ "$CLIENT_STATUS" -ne 0 ]; then
    echo "--- registro del anfitrión ---"; cat "$LOG_DIR/host.log"
    echo "--- registro del invitado ---"; cat "$LOG_DIR/client.log"
    echo "Prueba de red: FALLO (anfitrión $HOST_STATUS, invitado $CLIENT_STATUS)"
    exit 1
fi
echo "Prueba de red: OK"
