"""Cálculo de diferencias acumuladas de caja (mes e histórica).

Este módulo proporciona funciones para calcular las diferencias acumuladas
de efectivo (sobrantes/faltantes) desde movimientos de cierre registrados.

Funciones:
    - calcular_diferencia_mes: Acumulado desde el 1° del mes actual
    - calcular_diferencia_historica: Acumulado total desde el inicio
"""

from __future__ import annotations
from typing import Any
from datetime import datetime
import re


def _extraer_diferencia_de_observacion(observacion: str) -> float:
    """Extrae el valor numérico de la diferencia de una observación de cierre.

    Las observaciones de cierre tienen el formato:
    "Cierre TURNO. Esperado: 1000.00. Dif: 50.00. Total ventas: 5000.00"

    Args:
        observacion: Texto de la observación del movimiento de caja

    Returns:
        Valor de la diferencia (positivo para sobrante, negativo para faltante)
    """
    if not observacion or 'Dif:' not in observacion:
        return 0.0

    try:
        match = re.search(r'Dif:\s*([+-]?\d+\.?\d*)', observacion)
        if match:
            return float(match.group(1))
    except (ValueError, AttributeError):
        pass

    return 0.0


def calcular_diferencia_mes(
    caja_id: int | None = None,
    db: Any = None,
) -> float:
    """Calcula la diferencia acumulada del mes actual.

    Suma todas las diferencias (sobrantes/faltantes) de los cierres de caja
    registrados desde el primer día del mes actual hasta hoy.

    Args:
        caja_id: ID de la caja específica (None para todas las cajas)
        db: Instancia del gestor de base de datos

    Returns:
        Acumulado de diferencias del mes (positivo = sobrante total, negativo = faltante total)
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    try:
        # Primer día del mes actual a las 00:00:00
        primer_dia_mes = datetime.now().replace(day=1).strftime("%Y-%m-%d 00:00:00")

        # Construir consulta
        cond = "tipo IN ('CIERRE_TURNO', 'CIERRE_Z') AND fecha >= ?"
        params = [primer_dia_mes]

        if caja_id is not None:
            cond += " AND caja_id = ?"
            params.append(caja_id)

        # Obtener todos los movimientos de cierre del mes
        rows = db.execute_query(
            f"SELECT observaciones FROM movimientos_caja WHERE {cond}",
            tuple(params)
        ) or []

        # Sumar diferencias
        acumulado = 0.0
        for row in rows:
            obs = row.get('observaciones', '')
            acumulado += _extraer_diferencia_de_observacion(obs)

        return acumulado

    except Exception as e:
        print(f"Error calculando diferencia del mes: {e}")
        return 0.0


def calcular_diferencia_historica(
    caja_id: int | None = None,
    db: Any = None,
) -> float:
    """Calcula la diferencia acumulada histórica (desde el inicio del sistema).

    Suma todas las diferencias (sobrantes/faltantes) de todos los cierres de caja
    registrados en el sistema para la caja especificada.

    Args:
        caja_id: ID de la caja específica (None para todas las cajas)
        db: Instancia del gestor de base de datos

    Returns:
        Acumulado histórico de diferencias (positivo = sobrante total, negativo = faltante total)
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    try:
        # Construir consulta para todos los cierres
        cond = "tipo IN ('CIERRE_TURNO', 'CIERRE_Z')"
        params = []

        if caja_id is not None:
            cond += " AND caja_id = ?"
            params.append(caja_id)

        # Obtener todos los movimientos de cierre históricos
        rows = db.execute_query(
            f"SELECT observaciones FROM movimientos_caja WHERE {cond}",
            tuple(params)
        ) or []

        # Sumar diferencias
        acumulado = 0.0
        for row in rows:
            obs = row.get('observaciones', '')
            acumulado += _extraer_diferencia_de_observacion(obs)

        return acumulado

    except Exception as e:
        print(f"Error calculando diferencia histórica: {e}")
        return 0.0
