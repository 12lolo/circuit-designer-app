#!/usr/bin/env bash
set -euo pipefail

# Optional: allow user to force a platform (Wayland issues etc.)
: "${QT_QPA_PLATFORM:=}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Use virtual environment if it exists, otherwise use system Python
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python"
    echo "Using virtual environment Python: $PYTHON"
else
    PYTHON="python"
    echo "Using system Python: $PYTHON"
fi

have_pyqt6() {
  "$PYTHON" - <<'EOF'
try:
    import PyQt6  # noqa: F401
    exit(0)
except Exception:
    exit(1)
EOF
}

have_pyspice() {
  "$PYTHON" - <<'EOF'
try:
    import PySpice  # noqa: F401
    exit(0)
except Exception:
    exit(1)
EOF
}

if ! have_pyqt6; then
  cat <<'MSG'
[ERROR] PyQt6 not found.

Arch Linux quick fixes:
  Option A (system package, simplest):
    sudo pacman -S --needed python python-pyqt6

  Option B (isolated virtual environment):
    python -m venv venv
    ./venv/bin/pip install PyQt6 PySpice

Re-run ./run.sh afterwards.
MSG
  exit 1
fi

if ! have_pyspice; then
  cat <<'MSG'
[WARNING] PySpice not found.

To enable circuit simulation:
  If using venv:
    ./venv/bin/pip install PySpice

  If using system Python:
    pip install --user PySpice

  Also install ngspice:
    sudo pacman -S ngspice

Re-run ./run.sh afterwards.
MSG
  # Don't exit, allow running without PySpice
fi

exec "$PYTHON" "$SCRIPT_DIR/main_window.py" "$@"

