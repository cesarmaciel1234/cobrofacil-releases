"""Convenience script en la raíz para arrancar la UI.

Uso: `python lanzador_ui.py --role carteleria`
"""
import sys
import argparse
from src.lanzadores.ui import run

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--role", default=None)
    args = p.parse_args()
    sys.exit(run(args.role))
