from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class CajaRepoMixin:
    def get_efectivo_en_caja(self, caja_id: int = 1) -> float:
        """
        Calcula el efectivo neto en caja para el turno activo de una caja específica,
        sumando el fondo de apertura, las ventas en efectivo (completadas o cerradas)
        desde la apertura, más los ingresos manuales, y restando los retiros.
        """
        # 1. Encontrar el último movimiento de apertura para esta caja
        query_apertura = """
            SELECT fecha, monto 
            FROM movimientos_caja 
            WHERE caja_id = ? AND tipo = 'APERTURA' 
            ORDER BY id DESC LIMIT 1
        """
        aperturas = self.execute_query(query_apertura, (caja_id,))
        if not aperturas:
            # Si no hay apertura registrada para esta caja, hacemos fallback histórico para esta caja
            # Solo Efectivo/Mixto mueven cajón; vuelto (cambio>0) se resta del bruto recibido
            query_ventas = """
                SELECT SUM(
                    CASE
                        WHEN metodo_pago IN ('Efectivo', 'Mixto')
                             OR UPPER(COALESCE(metodo_pago, '')) LIKE '%EFECTIVO%'
                        THEN COALESCE(pago_efectivo, 0)
                             - CASE WHEN COALESCE(cambio, 0) > 0 THEN COALESCE(cambio, 0) ELSE 0 END
                        ELSE 0
                    END
                )
                FROM ventas
                WHERE caja_id = ? AND estado IN ('COMPLETADA', 'COMPLETADO')
            """
            query_retiros = "SELECT SUM(monto) FROM movimientos_caja WHERE caja_id = ? AND tipo='RETIRO'"
            v = self.execute_scalar(query_ventas, (caja_id,)) or 0.0
            r = self.execute_scalar(query_retiros, (caja_id,)) or 0.0
            return float(v) - float(r)
            
        apertura_fecha = aperturas[0]['fecha']
        fondo_apertura = float(aperturas[0]['monto'] or 0.0)
        
        # 2. Efectivo neto del turno: bruto recibido − vuelto (solo medios que mueven cajón)
        query_ventas = """
            SELECT SUM(
                CASE
                    WHEN metodo_pago IN ('Efectivo', 'Mixto')
                         OR UPPER(COALESCE(metodo_pago, '')) LIKE '%EFECTIVO%'
                    THEN COALESCE(pago_efectivo, 0)
                         - CASE WHEN COALESCE(cambio, 0) > 0 THEN COALESCE(cambio, 0) ELSE 0 END
                    ELSE 0
                END
            )
            FROM ventas 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND estado IN ('COMPLETADA', 'COMPLETADO', 'CERRADA', 'CERRADO')
        """
        ventas_efectivo = float(self.execute_scalar(query_ventas, (caja_id, apertura_fecha)) or 0.0)
        
        # 3. Sumar otros ingresos manuales en este turno
        query_ingresos = """
            SELECT SUM(monto) 
            FROM movimientos_caja 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND tipo = 'INGRESO'
        """
        ingresos_manuales = float(self.execute_scalar(query_ingresos, (caja_id, apertura_fecha)) or 0.0)
        
        # 4. Restar retiros en este turno
        query_retiros = """
            SELECT SUM(monto) 
            FROM movimientos_caja 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND tipo = 'RETIRO'
        """
        retiros = float(self.execute_scalar(query_retiros, (caja_id, apertura_fecha)) or 0.0)
        
        return fondo_apertura + ventas_efectivo + ingresos_manuales - retiros

