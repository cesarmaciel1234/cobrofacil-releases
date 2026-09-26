import logging
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorOfertas:
    """Motor central para la gestión de ofertas, promociones y folletos."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def obtener_departamentos(self):
        """Obtiene la lista de departamentos que tienen productos."""
        try:
            return db_manager.execute_query(
                "SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL AND departamento != '' ORDER BY departamento"
            ) or []
        except Exception as e:
            self.logger.error(f"Error al obtener departamentos para ofertas: {e}")
            return []

    def buscar_productos(self, buscar_txt="", departamento="", solo_promos=False):
        """Busca productos aplicando filtros."""
        q = (
            "SELECT id, codigo, nombre, departamento, costo, precio, stock, unidad, "
            "cant_oferta, precio_oferta, precio_oferta_relampago, "
            "limite_oferta_relampago, ventas_oferta_relampago, tipo_unidad_oferta "
            "FROM productos WHERE 1=1"
        )
        p = []
        if departamento:
            q += " AND departamento = ?"
            p.append(departamento)
        if buscar_txt:
            q += " AND (LOWER(nombre) LIKE ? OR COALESCE(codigo,'') LIKE ? OR CAST(id AS CHAR) LIKE ?)"
            b = f"%{buscar_txt.lower()}%"
            p.extend([b, b, b])
        if solo_promos:
            q += (
                " AND (COALESCE(cant_oferta,0) > 0 OR COALESCE(precio_oferta,0) > 0"
                " OR COALESCE(precio_oferta_relampago,0) > 0)"
            )

        q += " ORDER BY nombre LIMIT 800"

        try:
            return db_manager.execute_query(q, tuple(p)) or []
        except Exception as e:
            self.logger.error(f"Error buscando productos para ofertas: {e}")
            return []

    def obtener_producto(self, id_p):
        """Obtiene un producto específico por ID."""
        try:
            res = db_manager.execute_query("SELECT * FROM productos WHERE id=?", (id_p,))
            return res[0] if res else None
        except Exception as e:
            self.logger.error(f"Error al obtener producto {id_p}: {e}")
            return None

    def obtener_productos_por_ids(self, ids):
        """Obtiene múltiples productos dados sus IDs."""
        if not ids: return []
        placeholders = ",".join("?" * len(ids))
        try:
            return db_manager.execute_query(
                f"SELECT * FROM productos WHERE id IN ({placeholders})", tuple(ids)
            ) or []
        except Exception as e:
            self.logger.error(f"Error obteniendo productos por IDs: {e}")
            return []

    def obtener_productos_en_oferta(self):
        """Obtiene todos los productos que tienen alguna oferta activa (para folletos)."""
        try:
            return db_manager.execute_query(
                "SELECT * FROM productos WHERE "
                "(COALESCE(cant_oferta,0) > 0 AND COALESCE(precio_oferta,0) > 0) "
                "OR COALESCE(precio_oferta_relampago,0) > 0 "
                "ORDER BY departamento, nombre"
            ) or []
        except Exception as e:
            self.logger.error(f"Error al obtener productos en oferta: {e}")
            return []

    def aplicar_oferta(self, id_p, cant_oferta, precio_oferta, precio_relampago=0, precio_promedio=0, es_porcentaje=False, valor_porcentaje=0, limit_date="", precio_regular=None, limite_relampago=None, costo=None, stock=None):
        """Aplica oferta. precio_oferta_promedio se fuerza a 0 (retirado; mayoreo es otro motor)."""
        try:
            if es_porcentaje and valor_porcentaje and precio_regular:
                pct = max(0.0, min(100.0, float(valor_porcentaje)))
                calculado = round(float(precio_regular) * (1.0 - pct / 100.0), 2)
                if not precio_oferta:
                    precio_oferta = calculado
            # Promedio de oferta retirado: siempre 0. Volumen = MotorMayoreo.
            precio_promedio = 0
            sets = [
                "cant_oferta=?",
                "precio_oferta=?",
                "precio_oferta_relampago=?",
                "precio_oferta_promedio=?",
            ]
            vals = [cant_oferta, precio_oferta, precio_relampago, precio_promedio]
            if precio_regular is not None:
                sets.append("precio=?")
                vals.append(precio_regular)
            if limite_relampago is not None:
                sets.append("limite_oferta_relampago=?")
                vals.append(limite_relampago)
                # Cupo nuevo: contador desde cero
                sets.append("ventas_oferta_relampago=?")
                vals.append(0)
            elif precio_relampago and float(precio_relampago) > 0:
                sets.append("ventas_oferta_relampago=?")
                vals.append(0)
            if costo is not None:
                sets.append("costo=?")
                vals.append(costo)
            if stock is not None:
                sets.append("stock=?")
                vals.append(stock)
            vals.append(id_p)
            ok = db_manager.execute_non_query(
                f"UPDATE productos SET {', '.join(sets)} WHERE id=?",
                tuple(vals),
            )
            if not ok:
                ok = db_manager.execute_non_query(
                    "UPDATE productos SET cant_oferta=?, precio_oferta=?, precio_oferta_relampago=?, precio_oferta_promedio=? WHERE id=?",
                    (cant_oferta, precio_oferta, precio_relampago, precio_promedio, id_p),
                )
            if ok:
                try:
                    from src.central_red_global.sync_tienda import empujar_producto_a_maestra

                    payload = {
                        "id": id_p,
                        "cant_oferta": cant_oferta,
                        "precio_oferta": precio_oferta,
                        "precio_oferta_relampago": precio_relampago,
                        "precio_oferta_promedio": precio_promedio,
                    }
                    if precio_regular is not None:
                        payload["precio"] = precio_regular
                    empujar_producto_a_maestra(payload)
                except Exception:
                    pass
            return ok
        except Exception as e:
            self.logger.error(f"Error aplicando oferta al producto {id_p}: {e}")
            return False

    def aplicar_oferta_por_nombre(self, nombre, cant_oferta, precio_oferta_promedio):
        """Compat: redirige a MotorMayoreo (ya no escribe precio_oferta_promedio)."""
        try:
            from src.motor_descuentos.mayoreo.motor import MotorMayoreo
            return MotorMayoreo().aplicar_desde_promedios(
                nombre, 0, 0, cant_oferta, precio_oferta_promedio
            )
        except Exception as e:
            self.logger.error(f"Error redirigiendo oferta por nombre a mayoreo ({nombre}): {e}")
            return False

    def limpiar_oferta(self, id_p):
        """Limpia la oferta de un producto especfico y sincroniza."""
        try:
            ok = db_manager.execute_non_query(
                "UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, "
                "precio_oferta_promedio=0, limite_oferta_relampago=0, ventas_oferta_relampago=0 WHERE id=?",
                (id_p,)
            )
            if ok:
                try:
                    from src.central_red_global.sync_tienda import empujar_producto_a_maestra
                    empujar_producto_a_maestra({
                        "id": id_p, "cant_oferta": 0, "precio_oferta": 0,
                        "precio_oferta_relampago": 0, "precio_oferta_promedio": 0
                    })
                except Exception:
                    pass
            return ok
        except Exception as e:
            self.logger.error(f"Error limpiando oferta del producto {id_p}: {e}")
            return False

    def limpiar_multiples_ofertas(self, ids):
        """Limpia las ofertas de una lista de IDs y sincroniza."""
        if not ids: return True
        placeholders = ",".join("?" * len(ids))
        try:
            ok = db_manager.execute_non_query(
                f"UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, "
                f"precio_oferta_promedio=0, limite_oferta_relampago=0, ventas_oferta_relampago=0 "
                f"WHERE id IN ({placeholders})",
                tuple(ids)
            )
            if ok:
                try:
                    from src.central_red_global.sync_tienda import empujar_producto_a_maestra
                    for pid in ids:
                        empujar_producto_a_maestra({
                            "id": pid, "cant_oferta": 0, "precio_oferta": 0,
                            "precio_oferta_relampago": 0, "precio_oferta_promedio": 0
                        })
                except Exception:
                    pass
            return True
        except Exception as e:
            self.logger.error(f"Error limpiando multiples ofertas: {e}")
            return False

    @staticmethod
    def _num(p, key, default=0.0):
        try:
            if hasattr(p, "get"):
                v = p.get(key)
            else:
                v = p[key]
            if v is None or v == "":
                return default
            return float(v)
        except Exception:
            return default

    @staticmethod
    def nombre_limpio(nombre):
        n = str(nombre or "")
        for tag in (
            "📦 [MAYOREO] ", "⚡ [RELÁMPAGO] ", "🔥 [OFERTA] ",
            "[MAYOREO] ", "[RELÁMPAGO] ", "[OFERTA] ",
        ):
            n = n.replace(tag, "")
        return n.strip()

    @classmethod
    def resolver_precio_venta(cls, p, cantidad):
        """
        Prioridad caja (estilo retail):
        1) Mayoreo si cantidad ≥ umbral
        2) Relámpago si hay precio flash y cupo libre (limite 0 = sin tope / no apaga)
        3) Oferta si cantidad ≥ cant_oferta
        4) Precio lista
        Returns: (precio, descuento_total, nombre_display, tipo)
        """
        cantidad = float(cantidad or 0)
        precio_base = cls._num(p, "precio")
        cant_may = cls._num(p, "cant_mayoreo")
        precio_may = cls._num(p, "precio_mayoreo")
        cant_of = cls._num(p, "cant_oferta")
        precio_of = cls._num(p, "precio_oferta")
        precio_rel = cls._num(p, "precio_oferta_relampago")
        limite = cls._num(p, "limite_oferta_relampago")
        ventas = cls._num(p, "ventas_oferta_relampago")
        nom = ""
        try:
            raw = p.get("nombre") if hasattr(p, "get") else p["nombre"]
            nom = cls.nombre_limpio(raw)
        except Exception:
            nom = ""

        if cant_may > 0 and precio_may > 0 and cantidad >= cant_may:
            return (
                precio_may,
                max(0.0, precio_base - precio_may) * cantidad,
                f"📦 [MAYOREO] {nom}",
                "mayoreo",
            )

        # Cupo útil: si hay umbral de oferta (ej. desde 2), el resto debe alcanzar ese mínimo.
        # Ej.: límite 5, vendidos 4 → queda 1 < 2 → flash no aplica (queda apagable).
        resto = (limite - ventas) if limite > 0 else float("inf")
        minimo = cant_of if cant_of > 0 else 0.0
        # Mismo “desde X” que la oferta: no flash en 1 kg si el mínimo es 2.
        # Y el resto del cupo tiene que alcanzar ese mínimo (si no, no se ofrece).
        cupo_ok = (
            precio_rel > 0
            and (minimo <= 0 or cantidad >= minimo)
            and (limite <= 0 or (resto > 0 and (minimo <= 0 or resto >= minimo)))
        )
        if cupo_ok and (precio_base <= 0 or precio_rel < precio_base):
            return (
                precio_rel,
                max(0.0, precio_base - precio_rel) * cantidad,
                f"⚡ [RELÁMPAGO] {nom}",
                "relampago",
            )

        if cant_of > 0 and precio_of > 0 and cantidad >= cant_of:
            return (
                precio_of,
                max(0.0, precio_base - precio_of) * cantidad,
                f"🔥 [OFERTA] {nom}",
                "oferta",
            )

        return precio_base, 0.0, nom, "lista"

    def _apagar_relampago(self, id_p, ventas_final):
        db_manager.execute_non_query(
            "UPDATE productos SET ventas_oferta_relampago=?, precio_oferta_relampago=0 WHERE id=?",
            (ventas_final, id_p),
        )
        try:
            from src.cerebro_global.motor_global import invalidar_catalogo
            invalidar_catalogo()
        except Exception:
            pass
        try:
            from src.central_red_global.network_engine import get_network_engine
            e = get_network_engine()
            if e:
                e.broadcast_message("PRECIOS_ACTUALIZADOS", {"relampago_apagado": str(id_p)})
        except Exception:
            pass
        try:
            from src.central_red_global.sync_tienda import empujar_producto_a_maestra
            empujar_producto_a_maestra({
                "id": id_p,
                "precio_oferta_relampago": 0,
                "ventas_oferta_relampago": ventas_final,
            })
        except Exception:
            pass

    def consumir_relampago(self, id_p, cantidad):
        """
        Suma al contador. Apaga el flash si:
        - se llegó al límite, o
        - el resto ya no alcanza el mínimo de oferta (ej. queda 1 y desde=2).
        Nunca tumba la venta.
        """
        try:
            cantidad = float(cantidad or 0)
            if cantidad <= 0 or not id_p or str(id_p) in ("000",):
                return {"apagado": False}
            res = db_manager.execute_query(
                "SELECT precio_oferta_relampago, limite_oferta_relampago, "
                "ventas_oferta_relampago, cant_oferta "
                "FROM productos WHERE id=?",
                (id_p,),
            )
            if not res:
                return {"apagado": False}
            precio_rel = float(res[0]["precio_oferta_relampago"] or 0)
            limite = float(res[0]["limite_oferta_relampago"] or 0)
            ventas = float(res[0]["ventas_oferta_relampago"] or 0)
            cant_of = float(res[0].get("cant_oferta") or 0)
            if precio_rel <= 0 or limite <= 0:
                return {"apagado": False, "ventas": ventas, "limite": limite}

            nueva = min(limite, ventas + cantidad)
            resto = limite - nueva
            minimo = cant_of if cant_of > 0 else 0.0
            # Agotado por tope o resto insuficiente para el “desde X”
            apagado = (nueva >= limite) or (minimo > 0 and resto > 0 and resto < minimo)
            if apagado:
                self._apagar_relampago(id_p, nueva if nueva >= limite else limite)
                return {"apagado": True, "ventas": nueva, "limite": limite, "resto_insuficiente": resto < minimo}
            db_manager.execute_non_query(
                "UPDATE productos SET ventas_oferta_relampago=? WHERE id=?",
                (nueva, id_p),
            )
            return {"apagado": False, "ventas": nueva, "limite": limite}
        except Exception as e:
            self.logger.error(f"Error consumiendo relámpago {id_p}: {e}")
            return {"apagado": False}

    def consumir_relampago_en_items(self, items):
        """Tras cobrar: consume cupo solo en líneas vendidas como relámpago."""
        apagados = []
        for it in items or []:
            try:
                nombre = str(it.get("nombre") or "")
                nu = nombre.upper().replace("Á", "A")
                if "RELAMPAGO" not in nu and "⚡" not in nombre:
                    continue
                pid = it.get("id")
                cant = it.get("cant", it.get("cantidad", 0))
                r = self.consumir_relampago(pid, cant)
                if r.get("apagado"):
                    apagados.append(str(pid))
            except Exception:
                continue
        return apagados
