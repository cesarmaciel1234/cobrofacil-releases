"""Convenience script en la raíz para arrancar el Cerebro (backend).

Uso: `python lanzador_cerebro.py`
"""
import sys
from src.lanzadores.cerebro import run

if __name__ == "__main__":
    sys.exit(run())
