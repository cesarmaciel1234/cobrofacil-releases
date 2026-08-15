"""Launcher para UI (interfaz gráfica).

Permite arrancar `main.py` indicando un `--role` opcional.
"""
import os
import sys
import subprocess

def main(role=None):
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    py = sys.executable
    main_py = os.path.join(base, "main.py")
    cmd = [py, main_py]
    if role:
        cmd += ["--role", role]
    return subprocess.call(cmd)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--role", default=None)
    args = p.parse_args()
    sys.exit(main(args.role))
