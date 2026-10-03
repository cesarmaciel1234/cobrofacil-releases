import logging
from datetime import date, datetime
from src.base_de_datos.database import db_manager as db_maestra
from src.contabilidad.database import Database

logger = logging.getLogger(__name__)

class SincronizadorMaestra:
    """
    Se encarga de leer de MariaDB (la TPV) e insertar en la base de Contabilidad.
    
    ENTERPRISE: Ahora genera automÃ¡ticamente:
    - Asientos contables con desglose de IVA
    - Comprobantes fiscales
    - Todo lo contable para aprendizaje
    """
    def __init__(self, db_contabilidad: Database):
        self.db_contabilidad = db_contabilidad
        self._motor_asientos = None
        self._motor_impuestos = None
        self._integrador_iva = None
        
        # Inicializar motores enterprise si estÃ¡n disponibles
        try:
            from src.contabilidad.motor_asientos import MotorAsientos
            from src.contabilidad.motor_impuestos import MotorImpuestos
            from src.contabilidad.integracion_iva import IntegradorIVA
            
            self._motor_asientos = MotorAsientos(db_contabilidad.db_name)
            self._motor_impuestos = MotorImpuestos(db_contabilidad.db_name)
            self._integrador_iva = IntegradorIVA(db_contabilidad.db_name)
            
            logger.info("Motores enterprise inicializados en sincronizador")
        except Exception as e:
            logger.warning(f"No se pudieron inicializar motores enterprise: {e}")

    def traer_ventas_del_dia(self, fecha: date = None):
        """
        Agrupa las ventas de la TPV de una fecha (o de hoy) por medio de pago, 
        y las inyecta como Ingresos en Contabilidad.
        
        ENTERPRISE: TambiÃ©n genera asientos contables y comprobantes fiscales automÃ¡ticamente.
        """
        if not fecha:
            fecha = date.today()
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_str_like = f"{fecha_str}%"
        
        logger.info(f"Sincronizando ventas del {fecha_str} desde la base Maestra...")

        try:
            # 1. Limpiar ingresos y costos previos de la misma fecha importados automaticamente
            with self.db_contabilidad.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM income WHERE date = ? AND source = 'Ventas TPV'",
                    (fecha_str,)
                )
                cursor.execute(
                    "DELETE FROM expenses WHERE date = ? AND description = 'Costo de Ventas TPV'",
                    (fecha_str,)
                )
                conn.commit()

            # 2. Traer Ventas (Ingresos)
            query_ventas = """
                SELECT 
                    COALESCE(metodo_pago, 'Efectivo') as m_pago, 
                    SUM(total) as total
                FROM ventas 
                WHERE fecha LIKE ? AND estado IN ('COMPLETADA', 'CERRADA')
                GROUP BY m_pago
            """
            resultados = db_maestra.execute_query(query_ventas, (fecha_str_like,))
            
            ventas_existen = False
            if resultados:
                ventas_existen = True
                for fila in resultados:
                    m_pago = fila.get('m_pago', 'Desconocido')
                    total = float(fila.get('total', 0.0))
                    
                    self.db_contabilidad.add_income(
                        date=fecha_str,
                        amount=total,
                        description=f"Ventas del dÃ­a - {m_pago}",
                        source="Ventas TPV"
                    )
                    
                    # ENTERPRISE: Generar asiento contable automÃ¡ticamente
                    if self._motor_asientos:
                        try:
                            from src.config import config
                            iva_tasa = float(config.get("tax_percentage", 21.0))
                            
                            exito, mensaje, asiento_id = self._motor_asientos.generar_asiento_venta(
                                fecha=fecha,
                                monto_total=total,
                                metodo_pago=m_pago,
                                iva_tasa=iva_tasa,
                                costo_mercaderia=0.0,
                                referencia=f"SYNC-VENTAS-{fecha_str}"
                            )
                            
                            if exito:
                                logger.info(f"Asiento contable generado para ventas {m_pago}: {asiento_id}")
                        except Exception as e:
                            logger.warning(f"Error generando asiento contable: {e}")

            # 3. Traer Costos de Mercaderia (Egresos/Costo)
            query_costos = """
                SELECT SUM(dv.cantidad * p.costo) as costo_total
                FROM detalles_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                JOIN productos p ON dv.id_producto = p.id
                WHERE v.fecha LIKE ? AND v.estado IN ('COMPLETADA', 'CERRADA')
                  AND p.costo IS NOT NULL AND p.costo > 0
            """
            res_costos = db_maestra.execute_query(query_costos, (fecha_str_like,))
            if res_costos and res_costos[0] and res_costos[0].get('costo_total'):
                costo_total = float(res_costos[0]['costo_total'])
                if costo_total > 0:
                    self.db_contabilidad.add_expense(
                        date=fecha_str,
                        amount=costo_total,
                        category="MercaderÃ­a",
                        description="Costo de Ventas TPV"
                    )
            
            # 4. ENTERPRISE: Generar comprobantes fiscales individuales por venta
            if self._integrador_iva:
                try:
                    query_ventas_detalle = """
                        SELECT id, fecha, total, metodo_pago
                        FROM ventas 
                        WHERE fecha LIKE ? AND estado IN ('COMPLETADA', 'CERRADA')
                        ORDER BY id
                    """
                    ventas_detalle = db_maestra.execute_query(query_ventas_detalle, (fecha_str_like,))
                    
                    for venta in ventas_detalle:
                        venta_id = venta['id']
                        venta_fecha = venta['fecha']
                        venta_total = float(venta['total'])
                        venta_metodo = venta.get('metodo_pago', 'Efectivo')
                        
                        # Obtener items de la venta
                        query_items = """
                            SELECT dv.id_producto, dv.cantidad, dv.subtotal, p.nombre
                            FROM detalles_ventas dv
                            JOIN productos p ON dv.id_producto = p.id
                            WHERE dv.id_venta = ?
                        """
                        items = db_maestra.execute_query(query_items, (venta_id,))
                        
                        items_formato = []
                        for item in items:
                            items_formato.append({
                                "id": item['id_producto'],
                                "subtotal": float(item['subtotal'])
                            })
                        
                        # Generar comprobante fiscal
                        exito, mensaje, comp_id = self._integrador_iva.generar_comprobante_fiscal_venta(
                            num_venta=venta_id,
                            items=items_formato,
                            total=venta_total,
                            metodo_pago=venta_metodo
                        )
                        
                        if exito:
                            logger.debug(f"Comprobante fiscal generado para venta #{venta_id}")
                except Exception as e:
                    logger.warning(f"Error generando comprobantes fiscales: {e}")
            
            if ventas_existen:
                logger.info(f"SincronizaciÃ³n de ventas y costos de {fecha_str} exitosa.")
                return True
            else:
                logger.info("No hay ventas para sincronizar en esa fecha.")
                return False
                
        except Exception as e:
            logger.error(f"Error al sincronizar ventas: {e}")
            return False

    def traer_ventas_con_detalle_enterprise(self, fecha: date = None):
        """
        ENTERPRISE: Trae ventas con detalle y genera:
        - Asiento contable por venta individual
        - Comprobante fiscal por venta
        - Completamente automÃ¡tico para aprendizaje contable
        """
        if not fecha:
            fecha = date.today()
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_str_like = f"{fecha_str}%"
        
        logger.info(f"Sincronizando ventas con detalle enterprise del {fecha_str}...")
        
        if not self._motor_asientos or not self._integrador_iva:
            logger.warning("Motores enterprise no disponibles. Use traer_ventas_del_dia().")
            return False
        
        try:
            # Traer ventas individuales
            query_ventas = """
                SELECT id, fecha, total, metodo_pago, cliente_nombre
                FROM ventas 
                WHERE fecha LIKE ? AND estado IN ('COMPLETADA', 'CERRADA')
                ORDER BY id
            """
            ventas = db_maestra.execute_query(query_ventas, (fecha_str_like,))
            
            if not ventas:
                logger.info("No hay ventas para sincronizar.")
                return False
            
            from src.config import config
            iva_general = float(config.get("tax_percentage", 21.0))
            
            cont_ventas = 0
            cont_asientos = 0
            cont_comprobantes = 0
            
            for venta in ventas:
                venta_id = venta['id']
                venta_fecha_str = venta['fecha']
                venta_fecha = datetime.strptime(venta_fecha_str.split()[0], "%Y-%m-%d").date()
                venta_total = float(venta['total'])
                venta_metodo = venta.get('metodo_pago', 'Efectivo')
                cliente_nombre = venta.get('cliente_nombre')
                
                # Obtener items de la venta
                query_items = """
                    SELECT dv.id_producto, dv.cantidad, dv.subtotal, p.nombre, p.departamento
                    FROM detalles_ventas dv
                    JOIN productos p ON dv.id_producto = p.id
                    WHERE dv.id_venta = ?
                """
                items = db_maestra.execute_query(query_items, (venta_id,))
                
                # Calcular IVA por departamento
                total_iva = 0.0
                items_formato = []
                
                for item in items:
                    item_subtotal = float(item['subtotal'])
                    departamento = item.get('departamento', '')
                    
                    # Obtener IVA del departamento
                    iva_item = iva_general
                    try:
                        query_iva = "SELECT iva FROM departamentos WHERE nombre = ?"
                        res_iva = db_maestra.execute_query(query_iva, (departamento,))
                        if res_iva and res_iva[0]:
                            iva_item = float(res_iva[0]['iva'])
                    except:
                        pass
                    
                    items_formato.append({
                        "id": item['id_producto'],
                        "subtotal": item_subtotal
                    })
                    
                    # Calcular IVA del item
                    neto_item = item_subtotal / (1 + iva_item / 100)
                    iva_item_monto = item_subtotal - neto_item
                    total_iva += iva_item_monto
                
                # Generar asiento contable
                iva_promedio = (total_iva / venta_total * 100) if venta_total > 0 else iva_general
                
                exito, mensaje, asiento_id = self._motor_asientos.generar_asiento_venta(
                    fecha=venta_fecha,
                    monto_total=venta_total,
                    metodo_pago=venta_metodo,
                    iva_tasa=iva_promedio,
                    costo_mercaderia=0.0,
                    referencia=f"VENTA-{venta_id}"
                )
                
                if exito:
                    cont_asientos += 1
                
                # Generar comprobante fiscal
                exito, mensaje, comp_id = self._integrador_iva.generar_comprobante_fiscal_venta(
                    num_venta=venta_id,
                    items=items_formato,
                    total=venta_total,
                    metodo_pago=venta_metodo,
                    cliente_razon_social=cliente_nombre
                )
                
                if exito:
                    cont_comprobantes += 1
                
                cont_ventas += 1
            
            logger.info(f"SincronizaciÃ³n enterprise completada:")
            logger.info(f"  Ventas procesadas: {cont_ventas}")
            logger.info(f"  Asientos generados: {cont_asientos}")
            logger.info(f"  Comprobantes fiscales: {cont_comprobantes}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en sincronizaciÃ³n enterprise: {e}")
            return False

    def traer_compras_con_detalle_enterprise(self, fecha: date = None):
        """
        ENTERPRISE: Trae compras (gastos de mercadería) de MariaDB y genera:
        - Asiento contable de compra
        - Comprobante fiscal de compra
        """
        if not fecha:
            fecha = date.today()
            
        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_str_like = f"{fecha_str}%"
        
        logger.info(f"Sincronizando compras enterprise del {fecha_str}...")
        
        if not self._motor_asientos or not self._integrador_iva:
            return False
            
        try:
            query = "SELECT id, fecha, descripcion, monto, status FROM gastos WHERE categoria LIKE 'Mercader%' AND fecha LIKE ?"
            compras = db_maestra.execute_query(query, (fecha_str_like,))
            
            if not compras:
                return False
                
            from src.config import config
            iva_general = float(config.get("tax_percentage", 21.0))
            
            for compra in compras:
                compra_id = compra['id']
                compra_fecha_str = compra['fecha']
                compra_fecha = datetime.strptime(compra_fecha_str.split()[0], "%Y-%m-%d").date()
                monto = float(compra['monto'])
                proveedor = compra.get('descripcion', 'Proveedor Gral')
                
                # Asiento de compra
                self._motor_asientos.generar_asiento_compra(
                    fecha=compra_fecha,
                    monto_total=monto,
                    proveedor=proveedor,
                    iva_tasa=iva_general,
                    metodo_pago='Efectivo',
                    referencia=f"COMPRA-{compra_id}"
                )
                
                # Comprobante de compra
                neto = monto / (1 + iva_general/100)
                self._integrador_iva.generar_comprobante_fiscal_compra(
                    num_compra=compra_id,
                    proveedor_razon_social=proveedor,
                    total=monto,
                    neto_gravado=neto,
                    iva_monto=monto - neto,
                    iva_tasa=iva_general
                )
                
            return True
        except Exception as e:
            logger.error(f"Error en sincronización de compras enterprise: {e}")
            return False

    def traer_retiros_y_cierres(self, fecha: date = None):
        """
        Lee los movimientos de caja (retiros, faltantes) de MariaDB
        y los inyecta como Gastos o Ingresos Extra en Contabilidad.
        """
        pass


