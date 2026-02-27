#!/usr/bin/env bash
# Launch CompLaB Studio
# Usage:  ./run_gui.sh              (normal)
#         ./run_gui.sh --install    (install deps first)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "${1:-}" == "--install" ]]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    shift
fi

exec python main.py "$@"
