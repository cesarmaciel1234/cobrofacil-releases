from datetime import datetime
from src.base_de_datos.database import db_manager
from src.utils.barcode_parser import BarcodeParser
from src.logger import logger


def _avisar_formula(cursor, items):
    """La recepción no parte el huevo. Le dice a la fórmula cuántos cajones entraron."""
    aviso = None
    for it in items or []:
        if not it.get("desde_formula"):
            continue
        aviso = it
        break
    if not aviso:
        return
    try:
        bultos = float(aviso.get("bultos") or 0)
    except (TypeError, ValueError):
        bultos = 0.0
    if bultos <= 0:
        return
    try:
        precio = float(aviso.get("precio_bulto") or 0)
    except (TypeError, ValueError):
        precio = 0.0
    formula = str(aviso.get("formula") or "")
    if not formula:
        from src.proveedor_global.frontend.formula.motores.verdad import huevos_de
        if huevos_de(aviso.get("nombre")):
            formula = "Huevo"
    if formula == "Huevo":
        from src.proveedor_global.frontend.formula.motores.verdad import entrar
        entrar(cursor, "Huevo", bultos, precio)
        return
    if formula in ("Mocho", "Pecho", "Media res", "Pollo", "Cerdo", "Congelado"):
        from src.proveedor_global.frontend.formula.motores.carne_stock import entrar as entrar_carne
        cortes = []
        for it in items or []:
            if it.get("extension") or not it.get("kilos"):
                continue
            cortes.append((it.get("nombre") or "", it.get("kilos")))
        entrar_carne(cursor, db_manager, formula, bultos, precio, cortes or None)
        try:
            from src.proveedor_global.frontend.formula.motores.extension import escribir
            escribir(cursor, items)
        except Exception:
            pass


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
    def buscar_productos_por_iniciales(texto_raw: str, limit: int = 12, departamento: str = "") -> list[dict]:
        """Nombre, segunda palabra o código de barras. Si hay departamento, solo ese."""
        query = (texto_raw or "").strip()
        if len(query) < 2 and not query.isdigit():
            return []
        exacto = query.upper()
        prefijo = exacto + "%"
        segunda = "% " + exacto + "%"
        depto = (departamento or "").strip().upper()
        filtro = ""
        params = [prefijo, segunda, prefijo, prefijo]
        if depto:
            filtro = " AND UPPER(TRIM(COALESCE(departamento, ''))) = ?"
            params.append(depto)
        params.extend([exacto, exacto, prefijo, segunda, limit])
        sql = f"""
            SELECT id, codigo, nombre, departamento
            FROM productos
            WHERE (
                UPPER(nombre) LIKE ?
                OR UPPER(nombre) LIKE ?
                OR UPPER(COALESCE(codigo, '')) LIKE ?
                OR CAST(id AS TEXT) LIKE ?
            ){filtro}
            ORDER BY
                CASE
                    WHEN UPPER(COALESCE(codigo, '')) = ? OR CAST(id AS TEXT) = ? THEN 0
                    WHEN UPPER(nombre) LIKE ? THEN 1
                    WHEN UPPER(nombre) LIKE ? THEN 2
                    ELSE 3
                END,
                LENGTH(nombre),
                nombre
            LIMIT ?
        """
        try:
            rows = db_manager.execute_query(sql, tuple(params)) or []
        except Exception as e:
            logger.error(f"Error en buscar_productos_por_iniciales: {e}")
            return []
        salida = []
        for r in rows:
            if isinstance(r, dict):
                salida.append({
                    "id": r.get("id"),
                    "codigo": r.get("codigo") or str(r.get("id") or ""),
                    "nombre": r.get("nombre") or "Sin nombre",
                    "departamento": r.get("departamento") or "",
                })
            else:
                salida.append({
                    "id": r[0],
                    "codigo": r[1] or str(r[0] or ""),
                    "nombre": r[2] or "Sin nombre",
                    "departamento": r[3] or "",
                })
        return salida

    @staticmethod
    def _fechas(fecha=None):
        ahora = datetime.now()
        texto = str(fecha or "").strip()
        if len(texto) >= 10:
            corta = texto[:10]
            if len(texto) > 10:
                return corta, texto
            return corta, f"{corta} {ahora.strftime('%H:%M:%S')}"
        return ahora.strftime("%Y-%m-%d"), ahora.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def procesar_ingreso_mercaderia(proveedor_nombre: str, items: list, condicion_pago: str = "A Pagar", perfil: str = "admin", fecha=None) -> tuple[bool, str, dict]:
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

        fecha_corta, fecha_hoy = RecepcionService._fechas(fecha)
        total_monto = 0.0
        total_bultos = 0.0

        for it in items:
            cant = float(it.get("cantidad", 1.0))
            costo = float(it.get("costo", 0.0))
            if it.get("desde_formula"):
                subt = float(it.get("subtotal") or 0)
            else:
                subt = cant * costo
            total_monto += subt
            if not it.get("extension"):
                total_bultos += cant

        from src.proveedor_global.backend.moneda import texto

        es_contado = "contado" in condicion_pago.lower()
        estado_pago_val = "Pagado" if es_contado else "Pendiente"
        condicion = "Contado" if es_contado else "Fiado"
        detalle_desc = f"Recepción Escáner - Proveedor: {prov_clean}\nCondición: {condicion}\n"
        for it in items:
            if it.get("extension"):
                continue
            cant = float(it.get("cantidad", 1.0))
            costo_nuevo = float(it.get("costo", 0.0))
            nom = it.get("nombre", "")
            detalle_desc += f"• {cant}x {nom} ({texto(costo_nuevo)})\n"
        try:
            from src.proveedor_global.frontend.formula.motores.extension import texto as texto_extension
            detalle_desc += texto_extension(items)
        except Exception:
            pass
        formula_carga = ""
        bultos_carga = 0.0
        for it in items:
            nombre_formula = str(it.get("formula") or "")
            if nombre_formula in ("Mocho", "Pecho", "Media res", "Pollo", "Cerdo", "Congelado"):
                formula_carga = nombre_formula
                try:
                    bultos_carga = float(it.get("bultos") or 0)
                except (TypeError, ValueError):
                    bultos_carga = 0.0
                break
        if formula_carga and bultos_carga > 0:
            detalle_desc += f"Fórmula: {formula_carga} · {bultos_carga:g} bultos\n"
            utiles = [
                f"{it.get('nombre')} {float(it.get('kilos') or 0):g}"
                for it in items
                if it.get("kilos")
            ]
            if utiles:
                detalle_desc += "Útiles: " + ", ".join(utiles) + "\n"

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
                if it.get("extension"):
                    continue
                if not it.get("desde_formula"):
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

            _avisar_formula(cursor, items)
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
            if getattr(db_manager, "db_engine_type", "") != "mariadb" or not db_manager.is_connected() or getattr(db_manager, "_forced_local_offline", False):
                try:
                    from src.base_de_datos.offline_nutricion import offline_nutricion_manager
                    offline_nutricion_manager.encolar_recepcion(
                        prov_clean, items, total_bultos, total_monto, condicion_pago, perfil,
                        fecha=fecha_hoy,
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
            if it.get("extension"):
                continue
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
