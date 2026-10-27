from datetime import datetime
from src.base_de_datos.database import db_manager
from src.utils.barcode_parser import BarcodeParser
from src.logger import logger
from src.proveedor_global.backend.ficha import FichaProveedor

class RecepcionService:
    """
    Servicio de backend para la Recepción Rápida de Mercadería por Escáner.
    Permite buscar productos con multiplicadores (ej: 7*codigo) y registrar el ingreso
    atómico a la base de datos (actualizando stock, costo de compra y deuda del proveedor).
    """

    @staticmethod
    def buscar_producto_por_escaneo(texto_raw: str) -> tuple[dict | None, float]:
        """
        Analiza el texto ingresado en la barra de escáner.
        Soporta multiplicadores tipo Paso 5:
        - '7*77900401' -> cantidad=7, codigo='77900401'
        - '12*' -> cantidad=12
        - '77900401' -> cantidad=1, codigo='77900401'
        - Búsqueda por nombre predictiva si no es numérico.
        Retorna: (dict_producto o None, cantidad_multiplicador)
        """
        if not texto_raw:
            return None, 1.0

        codigo_limpio, multiplicador = BarcodeParser.parse_scan_text(texto_raw)
        if not codigo_limpio:
            return None, multiplicador

        codigo_str = codigo_limpio.strip()

        # 1. Búsqueda exacta por código de barras o id
        sql_exacto = """
            SELECT id, codigo, nombre, departamento, stock, costo, precio
            FROM productos
            WHERE codigo = ? OR CAST(id AS CHAR) = ?
            LIMIT 1
        """
        rows = db_manager.execute_query(sql_exacto, (codigo_str, codigo_str)) or []
        if rows:
            r = rows[0]
            return {
                "id": r["id"],
                "codigo": r["codigo"] or str(r["id"]),
                "nombre": r["nombre"] or "Sin Nombre",
                "departamento": r.get("departamento") or "GENERAL",
                "stock_actual": float(r.get("stock") or 0.0),
                "costo_actual": float(r.get("costo") or 0.0),
                "precio_actual": float(r.get("precio") or 0.0)
            }, multiplicador

        # 2. Búsqueda por nombre aproximado
        sql_nombre = """
            SELECT id, codigo, nombre, departamento, stock, costo, precio
            FROM productos
            WHERE nombre LIKE ?
            ORDER BY LENGTH(nombre) ASC
            LIMIT 1
        """
        rows_nom = db_manager.execute_query(sql_nombre, (f"%{codigo_str}%",)) or []
        if rows_nom:
            r = rows_nom[0]
            return {
                "id": r["id"],
                "codigo": r["codigo"] or str(r["id"]),
                "nombre": r["nombre"] or "Sin Nombre",
                "departamento": r.get("departamento") or "GENERAL",
                "stock_actual": float(r.get("stock") or 0.0),
                "costo_actual": float(r.get("costo") or 0.0),
                "precio_actual": float(r.get("precio") or 0.0)
            }, multiplicador

        return None, multiplicador

    @staticmethod
    def buscar_productos_coincidentes(texto_raw: str, limit: int = 15) -> tuple[list[dict], float]:
        """
        Búsqueda asistida en vivo para el autocompletado interactivo.
        Soporta multiplicadores (ej: '1*proven' -> cantidad=1, query='proven').
        Retorna: (lista_de_productos, cantidad_multiplicador)
        """
        if not texto_raw:
            return [], 1.0

        codigo_limpio, multiplicador = BarcodeParser.parse_scan_text(texto_raw)
        if not codigo_limpio:
            return [], multiplicador

        query = codigo_limpio.strip()
        if len(query) < 2 and not query.isdigit():
            return [], multiplicador

        sql = """
            SELECT id, codigo, nombre, departamento, stock, costo, precio
            FROM productos
            WHERE nombre LIKE ? OR codigo LIKE ? OR CAST(id AS CHAR) = ?
            ORDER BY 
                CASE 
                    WHEN codigo = ? THEN 1
                    WHEN nombre LIKE ? THEN 2
                    ELSE 3
                END,
                LENGTH(nombre) ASC
            LIMIT ?
        """
        exact_start = f"{query}%"
        contains = f"%{query}%"
        try:
            rows = db_manager.execute_query(sql, (contains, contains, query, query, exact_start, limit)) or []
        except Exception as e:
            logger.error(f"Error en buscar_productos_coincidentes: {e}")
            rows = []

        resultados = []
        for r in rows:
            resultados.append({
                "id": r["id"],
                "codigo": r["codigo"] or str(r["id"]),
                "nombre": r["nombre"] or "Sin Nombre",
                "departamento": r.get("departamento") or "GENERAL",
                "stock_actual": float(r.get("stock") or 0.0),
                "costo_actual": float(r.get("costo") or 0.0),
                "precio_actual": float(r.get("precio") or 0.0)
            })

        return resultados, multiplicador

    @staticmethod
    def procesar_ingreso_mercaderia(proveedor_nombre: str, items: list, condicion_pago: str = "A Pagar", perfil: str = "admin") -> tuple[bool, str, dict]:
        """
        Registra el ingreso de mercadería en un solo tiro atómico:
        1. Para cada producto: incrementa el stock (stock = stock + cantidad)
           y actualiza el costo de compra si fue editado.
        2. Registra la compra en 'romaneos' y 'romaneo_items'.
        3. Registra el gasto/deuda en 'gastos'.
        4. Genera el texto de WhatsApp de conformidad.
        """
        if not items:
            return False, "No hay productos en la lista para ingresar.", {}

        prov_clean = (proveedor_nombre or "").strip()
        if not prov_clean or prov_clean in ("Seleccionar o escribir...", "Seleccionar o escribir proveedor...", "Sin Proveedor (Proveedor General)"):
            prov_clean = "Proveedor General"

        # Asegurar ficha de proveedor en la maestra
        try:
            FichaProveedor.obtener_o_crear(prov_clean)
        except Exception:
            pass

        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_corta = datetime.now().strftime("%Y-%m-%d")
        total_monto = 0.0
        total_bultos = 0.0

        for it in items:
            cant = float(it.get("cantidad", 1.0))
            costo = float(it.get("costo", 0.0))
            subt = cant * costo
            total_monto += subt
            total_bultos += cant

        from src.proveedor_global.backend.moneda import texto

        estado_pago_val = "Pagado" if "contado" in condicion_pago.lower() else "Pendiente"
        detalle_desc = f"Recepción Escáner - Proveedor: {prov_clean}\n"
        for it in items:
            cant = float(it.get("cantidad", 1.0))
            costo_nuevo = float(it.get("costo", 0.0))
            nom = it.get("nombre", "")
            detalle_desc += f"• {cant}x {nom} ({texto(costo_nuevo)})\n"

        wa_texto = RecepcionService.generar_whatsapp_conformidad(
            prov_clean, items, total_bultos, total_monto, condicion_pago
        )

        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos, monto_total, estado_pago, registrado_por)
                VALUES (?, ?, ?, 'RECEPCION_MERCADERIA', ?, ?, ?, ?, ?)
                """,
                (fecha_corta, prov_clean, "REMITO_ESCANER", total_monto / max(1, total_bultos), total_bultos, total_monto, estado_pago_val, perfil),
            )
            romaneo_id = int(getattr(cursor, "lastrowid", 0) or 0)
            if not romaneo_id:
                raise RuntimeError("La base no devolvió el id del remito.")

            for it in items:
                p_id = it.get("id")
                cant = float(it.get("cantidad", 1.0))
                costo_nuevo = float(it.get("costo", 0.0))
                cod = it.get("codigo", "")
                cursor.execute(
                    """
                    UPDATE productos
                    SET stock = COALESCE(stock, 0) + ?,
                        costo = ?
                    WHERE id = ?
                    """,
                    (cant, costo_nuevo, p_id),
                )
                cursor.execute(
                    "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                    (romaneo_id, cod or str(p_id), cant),
                )

            cursor.execute(
                """
                INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario)
                VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)
                """,
                (fecha_hoy, detalle_desc.strip(), total_monto, estado_pago_val, perfil),
            )
            conn.commit()

            resumen = {
                "proveedor": prov_clean,
                "total_bultos": total_bultos,
                "total_monto": total_monto,
                "articulos_count": len(items),
                "whatsapp_texto": wa_texto
            }

            logger.info(f"Recepción de mercadería completada: {len(items)} productos ingresados a stock para {prov_clean}.")
            # Si estamos en modo esclavo/offline (ej: trabajando en la notebook en casa),
            # encolar la recepción en offline_nutricion para alimentar a la Maestra al reconectar.
            if getattr(db_manager, "db_engine_type", "") != "mariadb" or not db_manager.is_connected() or getattr(db_manager, "_forced_local_offline", False):
                try:
                    from src.base_de_datos.offline_nutricion import offline_nutricion_manager
                    offline_nutricion_manager.encolar_recepcion(
                        prov_clean, items, total_bultos, total_monto, condicion_pago, perfil
                    )
                except Exception as e_enc:
                    logger.warning(f"No se pudo encolar recepción offline: {e_enc}")

            try:
                from src.motor_inventario.planilla.orquestador import MotorPlanilla

                MotorPlanilla.avisar()
            except Exception as aviso:
                logger.warning("El ingreso quedó y la planilla se entera en su próximo pase: %s", aviso)
            return True, "Ingreso a stock y compra registrados con éxito.", resumen

        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"Error procesando recepción de mercadería: {e}")
            return False, f"Fallo al procesar el ingreso: {e}", {}
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    @staticmethod
    def generar_whatsapp_conformidad(proveedor: str, items: list, total_bultos: float, total_monto: float, condicion_pago: str, nombre_comercio: str = "Mi Comercio") -> str:
        """Arma el comprobante digital listo para copiar y enviar al proveedor."""
        from src.config import config
        from src.proveedor_global.backend.moneda import texto

        comercio = config.get("business_name", nombre_comercio)
        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

        lineas = [
            "--- RECEPCION DE MERCADERIA CONFORME ---",
            f"*Comercio:* {comercio}",
            f"*Proveedor:* {proveedor}",
            f"*Fecha:* {fecha_hoy}",
            "------------------------------------"
        ]

        for it in items:
            cant = int(it['cantidad']) if isinstance(it['cantidad'], (int, float)) and float(it['cantidad']).is_integer() else f"{it['cantidad']}"
            nom = it['nombre']
            cod = f" [{it['codigo']}]" if it.get('codigo') else ""
            c_unit = float(it.get('costo', 0.0))
            subt = float(it.get('subtotal', 0.0))
            lineas.append(f"- *{cant}x* {nom}{cod} | Costo: {texto(c_unit)} | Subt: {texto(subt)}")

        lineas.append("------------------------------------")
        bultos_fmt = int(total_bultos) if float(total_bultos).is_integer() else f"{total_bultos:.2f}"
        lineas.append(f"*Total bultos recibidos:* {bultos_fmt} unidades")
        lineas.append(f"*Monto total remito:* {texto(total_monto)}")
        lineas.append(f"*Condicion:* {condicion_pago}")
        lineas.append("------------------------------------")
        lineas.append("Mercaderia verificada e ingresada al stock satisfactoriamente. ¡Muchas gracias!")

        return "\n".join(lineas)
