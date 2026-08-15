"""Launcher para Cerebro (servicios backend).

Este script arranca el proceso principal en modo servidor/backend.
"""
import os
import sys
import subprocess

def main():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    py = sys.executable
    main_py = os.path.join(base, "main.py")
    # Ejecutar main.py en modo servidor para servicios backend
    cmd = [py, main_py, "--server"]
    return subprocess.call(cmd)

if __name__ == "__main__":
    sys.exit(main())
