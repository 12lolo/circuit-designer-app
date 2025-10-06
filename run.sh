#!/usr/bin/env bash
set -euo pipefail

# Optional: allow user to force a platform (Wayland issues etc.)
: "${QT_QPA_PLATFORM:=}"

have_pyqt6() {
  python - <<'EOF'
try:
    import PyQt6  # noqa: F401
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
    sudo pacman -S --needed python-pip  # if pip missing
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

Re-run ./run.sh afterwards.
MSG
  exit 1
fi

exec python main_window.py "$@"

