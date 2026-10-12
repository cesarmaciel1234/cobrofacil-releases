#!/usr/bin/env bash
#
# Cloud Agent install for Cobro Fácil POS (PyQt6 desktop POS).
#
# The product targets Windows, but the pure-Python + Qt layers run headless on
# Linux (this is what CI does in .github/workflows/pr-smoke.yml and pyqt6-prep).
# This script installs the Qt/WebEngine runtime libraries plus a virtual display
# (Xvfb), then creates a .venv with the cross-platform dependency subset. The
# Windows-only wheels (pywin32/pypiwin32/comtypes) are skipped; the hardware
# layer already guards their absence and runs in "simulation" mode.
#
# Idempotent: safe to re-run. Reuses the existing .venv and apt cache.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; else SUDO=""; fi
export DEBIAN_FRONTEND=noninteractive

echo "==> Installing system libraries for PyQt6 + QtWebEngine (headless)"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq \
  python3-venv python3-dev build-essential \
  xvfb x11-utils \
  libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-util1 \
  libegl1 libgl1-mesa-dri libglx-mesa0 libopengl0 libfontconfig1 libdbus-1-3 \
  libnss3 libxcomposite1 libxdamage1 libxrandr2 libxtst6 \
  libxslt1.1 libxml2 fonts-dejavu-core
# ALSA runtime for pyttsx3 (optional; package renamed to *t64 on Ubuntu 24.04).
$SUDO apt-get install -y -qq libasound2t64 || $SUDO apt-get install -y -qq libasound2 || true

echo "==> Creating Python virtual environment (.venv)"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --quiet --upgrade pip wheel setuptools

echo "==> Installing Python dependencies (cross-platform subset)"
# requirements.txt is the source of truth; drop Windows-only wheels that have no
# Linux distribution so the install succeeds on the Cloud Agent VM.
grep -viE '^[[:space:]]*#|^[[:space:]]*$|pywin32|pypiwin32|comtypes' requirements.txt \
  | sed 's/\r$//' > /tmp/requirements-linux.txt
python -m pip install --quiet -r /tmp/requirements-linux.txt

echo "==> Done. CobroFacil POS Linux dev environment is ready."
echo "    Headless Qt:  export QT_QPA_PLATFORM=offscreen TPV_QT=6"
echo "    GUI (Xvfb):   xvfb-run -a python main.py --role cajero"
