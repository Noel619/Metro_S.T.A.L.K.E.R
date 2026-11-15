#!/usr/bin/env bash
# Pruebas de red: un anfitrión y un invitado en la misma máquina.
# Uso: tools/test_net.sh   (variable GODOT para usar otro ejecutable)
set -u
GODOT="${GODOT:-godot}"
cd "$(dirname "$0")/.."
LOG_DIR="$(mktemp -d)"
FAILED=0

# run_pair nombre guion "argumentos del anfitrión" "argumentos del invitado"
run_pair() {
    local name="$1" script="$2" host_args="$3" client_args="$4"
    # shellcheck disable=SC2086
    "$GODOT" --headless --path . -s "$script" -- --role=host $host_args >"$LOG_DIR/$name-host.log" 2>&1 &
    local host_pid=$!
    sleep 2
    # shellcheck disable=SC2086
    timeout 90 "$GODOT" --headless --path . -s "$script" -- --role=client $client_args >"$LOG_DIR/$name-client.log" 2>&1
    local client_status=$?
    local waited=0
    while kill -0 "$host_pid" 2>/dev/null && [ "$waited" -lt 60 ]; do sleep 1; waited=$((waited + 1)); done
    kill -9 "$host_pid" 2>/dev/null
    wait "$host_pid"
    local host_status=$?
    grep -h -E "^\[(host|client)\]" "$LOG_DIR/$name-host.log" "$LOG_DIR/$name-client.log"
    if [ "$host_status" -ne 0 ] || [ "$client_status" -ne 0 ]; then
        echo "--- registro del anfitrión ---"; cat "$LOG_DIR/$name-host.log"
        echo "--- registro del invitado ---"; cat "$LOG_DIR/$name-client.log"
        echo "Prueba de red '$name': FALLO (anfitrión $host_status, invitado $client_status)"
        FAILED=1
    else
        echo "Prueba de red '$name': OK"
    fi
}

run_pair "caja" tests/net/net_smoke.gd "" ""
run_pair "deposito" tests/net/net_depot.gd "--host" "--join=127.0.0.1 --chica"
exit "$FAILED"
