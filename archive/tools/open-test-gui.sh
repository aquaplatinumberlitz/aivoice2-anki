#!/usr/bin/env bash
set -euo pipefail
AIVOICE_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
AIVOICE_RUNTIME_CONFIG="${AIVOICE2_CONFIG:-$AIVOICE_PROJECT_ROOT/cache/free-client-review/runtime.json}"
exec python3 "$AIVOICE_PROJECT_ROOT/src/daemon/runtime_cli.py" --config "$AIVOICE_RUNTIME_CONFIG" gui "$@"
