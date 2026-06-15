#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PWD/bin:$PATH"
exec python3 alass_gui.py
