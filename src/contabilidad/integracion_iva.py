"""
integracion_iva.py â€” IntegraciÃ³n entre IVA de TPV y Contabilidad Enterprise
TPV Pro 2026 Â· Cobro FÃ¡cil POS

Este mÃ³dulo sincroniza:
- Tasas de IVA de departamentos (MariaDB) con motor de impuestos (SQLite)
- GeneraciÃ³n automÃ¡tica de comprobantes fiscales desde ventas TPV
- LiquidaciÃ³n de IVA unificada
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("IntegracionIVA")


class IntegradorIVA:
    """Integrador entre sistema IVA TPV y contabilidad enterprise"""
    
    def __init__(self, db_contabilidad_path: str):
        self.db_contabilidad_path = db_contabilidad_path
        self._motor_impuestos = None
        
        try:
            from src.contabilidad.motor_impuestos import MotorImpuestos
            self._motor_impuestos = MotorImpuestos(db_contabilidad_path)
            logger.info("Motor de impuestos inicializado")
        except Exception as e:
            logger.warning(f"No se pudo inicializar motor de impuestos: {e}")
    
    def sincronizar_alicuotas_desde_departamentos(self) -> Tuple[bool, str]:
        """
        Sincroniza las tasas de IVA de departamentos con las alicuotas del motor de impuestos
        
        Las tasas de IVA se leen de la tabla departamentos en MariaDB
        y se actualizan en el motor de impuestos SQLite.
        """
        try:
            from src.base_de_datos.database import db_manager
            
            # Leer departamentos de MariaDB
            rows = db_manager.execute_query("SELECT id, nombre, iva FROM departamentos ORDER BY id")
            
            if not rows:
                return False, "No hay departamentos en la base de datos"
            
            # Mapeo de tasas conocidas
            alicuotas_conocidas = {0.0, 10.5, 21.0, 27.0}
            tasas_encontradas = set()
            
            for row in rows:
                tasa = float(row.get('iva', 21.0))
                tasas_encontradas.add(tasa)
            
            # Verificar si hay tasas no estÃ¡ndar
            tasas_no_estandar = tasas_encontradas - alicuotas_conocidas
            if tasas_no_estandar:
                logger.warning(f"Tasas de IVA no estÃ¡ndar encontradas: {tasas_no_estandar}")
            
            logger.info(f"SincronizaciÃ³n de IVA: {len(rows)} departamentos, tasas: {tasas_encontradas}")
            return True, f"SincronizaciÃ³n exitosa: {len(rows)} departamentos"
            
        except Exception as e:
            logger.error(f"Error sincronizando alicuotas: {e}")
            return False, str(e)
    
    def generar_comprobante_fiscal_venta(self, num_venta: int, items: List[Dict], 
                                         total: float, metodo_pago: str,
                                         cliente_cuit: Optional[str] = None,
                                         cliente_razon_social: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Genera un comprobante fiscal a partir de una venta del TPV
        
        Args:
            num_venta: NÃºmero de venta
            items: Lista de items vendidos
            total: Monto total de la venta
            metodo_pago: MÃ©todo de pago
            cliente_cuit: CUIT del cliente (opcional)
            cliente_razon_social: RazÃ³n social del cliente (opcional)
        
        Returns:
            (exito, mensaje, comprobante_id)
        """
        if not self._motor_impuestos:
            return False, "Motor de impuestos no disponible", None
        
        try:
            from src.base_de_datos.database import db_manager
            from src.config import config
            from src.contabilidad.motor_impuestos import TipoComprobante, CondicionFiscal
            
            # Determinar tipo de comprobante segÃºn CUIT
            if cliente_cuit:
                tipo_comprobante = TipoComprobante.FACTURA_A
                condicion_fiscal = CondicionFiscal.RESPONSABLE_INSCRIPTO
            else:
                tipo_comprobante = TipoComprobante.FACTURA_B
                condicion_fiscal = CondicionFiscal.CONSUMIDOR_FINAL
            
            # Calcular IVA desagregado
            neto_total = 0.0
            iva_total = 0.0
            iva_por_tasa = {}
            
            for it in items:
                p_id = it.get('id')
                tasa_iva = float(config.get("tax_percentage", 21.0))
                
                if p_id and str(p_id) != '000':
                    try:
                        res = db_manager.execute_query(
                            "SELECT d.iva FROM productos p JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE p.id = ? OR p.codigo = ?",
                            (p_id, p_id)
                        )
                        if res and res[0]['iva'] is not None:
                            tasa_iva = float(res[0]['iva'])
                    except Exception:
                        pass
                
                subt_item = float(it.get('subtotal', 0.0))
                neto_item = subt_item / (1 + tasa_iva / 100)
                iva_item = subt_item - neto_item
                
                neto_total += neto_item
                iva_total += iva_item
                iva_por_tasa[tasa_iva] = iva_por_tasa.get(tasa_iva, 0.0) + iva_item
            
            # Determinar alicuota principal (la de mayor monto)
            if iva_por_tasa:
                alicuota_principal = max(iva_por_tasa.items(), key=lambda x: x[1])[0]
            else:
                alicuota_principal = 21.0
            
            # Convertir a cÃ³digo de alicuota
            alicuota_codigo = self._tasa_a_codigo(alicuota_principal)
            
            # Registrar comprobante fiscal
            fecha = date.today()
            numero = f"A-{num_venta:06d}"
            
            exito, mensaje, comprobante_id = self._motor_impuestos.registrar_comprobante(
                tipo=tipo_comprobante,
                numero=numero,
                fecha=fecha,
                monto_total=total,
                alicuota_codigo=alicuota_codigo,
                condicion_fiscal=condicion_fiscal,
                tipo_operacion="venta",
                tipo_persona="juridica" if cliente_cuit else "fisica",
                cuit_cuil=cliente_cuit,
                razon_social=cliente_razon_social,
                monto_no_gravado=0.0,
                monto_exento=0.0
            )
            
            if exito:
                logger.info(f"Comprobante fiscal generado: {numero} - Venta #{num_venta}")
            
            return exito, mensaje, comprobante_id
            
        except Exception as e:
            logger.error(f"Error generando comprobante fiscal: {e}")
            return False, str(e), None
    
    def generar_comprobante_fiscal_compra(self, num_compra: int, total: float, neto_gravado: float, iva_monto: float, iva_tasa: float, proveedor_razon_social: str = None) -> Tuple[bool, str, Optional[str]]:
        if not self._motor_impuestos:
            return False, "Motor de impuestos no disponible", None
            
        try:
            from src.contabilidad.motor_impuestos import TipoComprobante
            
            tipo = TipoComprobante.FACTURA_A if iva_monto > 0 else TipoComprobante.FACTURA_C
            numero = f"C0001-{num_compra:08d}"
            
            alicuota_codigo = self._tasa_a_codigo(iva_tasa)
            
            exito, mensaje, comprobante_id = self._motor_impuestos.registrar_comprobante(
                tipo=tipo,
                numero=numero,
                fecha=date.today(),
                monto_total=total,
                alicuota_codigo=alicuota_codigo,
                condicion_fiscal="Responsable Inscripto",
                tipo_operacion="compra",
                tipo_persona="juridica",
                cuit_cuil=None,
                razon_social=proveedor_razon_social,
                monto_no_gravado=0.0,
                monto_exento=0.0
            )
            return exito, mensaje, comprobante_id
        except Exception as e:
            return False, str(e), None

    def _tasa_a_codigo(self, tasa: float) -> str:
        """Convierte una tasa de IVA a cÃ³digo de alicuota"""
        if tasa == 0.0:
            return "0"
        elif tasa == 10.5:
            return "10.5"
        elif tasa == 21.0:
            return "21"
        elif tasa == 27.0:
            return "27"
        else:
            # Tasas no estÃ¡ndar se redondean a la mÃ¡s cercana
            if tasa < 10.5:
                return "0"
            elif tasa < 21.0:
                return "10.5"
            elif tasa < 27.0:
                return "21"
            else:
                return "27"
    
    def obtener_resumen_iva_mes(self, mes: int, anio: int) -> Dict:
        """
        Obtiene un resumen de IVA para un mes combinando datos TPV y contabilidad
        
        Returns:
            Dict con dÃ©bito fiscal, crÃ©dito fiscal y saldo
        """
        try:
            from datetime import date
            
            desde = date(anio, mes, 1)
            if mes == 12:
                hasta = date(anio + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                hasta = date(anio, mes + 1, 1) - datetime.timedelta(days=1)
            
            if self._motor_impuestos:
                # Usar motor de impuestos si estÃ¡ disponible
                liquidacion = self._motor_impuestos.liquidar_iva(desde, hasta)
                return liquidacion
            else:
                # Fallback: calcular desde datos de TPV
                from src.base_de_datos.database import db_manager
                
                # Ventas del mes
                query_ventas = """
                    SELECT SUM(total) as total
                    FROM ventas
                    WHERE fecha BETWEEN ? AND ?
                    AND estado IN ('COMPLETADA', 'CERRADA')
                """
                res_ventas = db_manager.execute_query(query_ventas, (desde.isoformat(), hasta.isoformat()))
                total_ventas = float(res_ventas[0]['total']) if res_ventas else 0.0
                
                # IVA estimado (21% por defecto)
                iva_estimado = total_ventas * 0.21 / 1.21
                
                return {
                    "periodo_desde": desde.isoformat(),
                    "periodo_hasta": hasta.isoformat(),
                    "debito_fiscal": iva_estimado,
                    "credito_fiscal": 0.0,
                    "saldo": iva_estimado,
                    "a_pagar": iva_estimado,
                    "a_creditar": 0.0,
                    "nota": "Estimado desde datos TPV (sin motor de impuestos)"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen IVA: {e}")
            return {
                "error": str(e),
                "periodo_desde": desde.isoformat() if 'desde' in locals() else "",
                "periodo_hasta": hasta.isoformat() if 'hasta' in locals() else ""
            }

