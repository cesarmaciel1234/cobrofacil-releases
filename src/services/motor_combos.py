"""
Motor de combos multi-artículo para cartelería espía y futuro cobro en caja.
Tipos:
  - combo_fijo: todos los artículos del JSON deben estar en el carrito (cant mínima c/u).
  - combo_n: elegir_n artículos distintos del pool en requisitos_json.
  - cantidad_grupo: suma de unidades del pool >= elegir_n.
"""
import json
import logging

logger = logging.getLogger("MotorCombos")


class MotorCombos:
    @staticmethod
    def _row_val(row, key, idx=0):
        if isinstance(row, dict):
            return row.get(key)
        if row and len(row) > idx:
            return row[idx]
        return None

    @staticmethod
    def _cargar_combos(db):
        if not db:
            return []
        try:
            rows = db.execute_query(
                "SELECT id, nombre, tipo, precio_combo, descuento_pct, elegir_n, requisitos_json, orden "
                "FROM combos_descuento WHERE activo = 1 ORDER BY orden ASC, id ASC"
            )
            return rows or []
        except Exception as e:
            logger.debug("combos_descuento no disponible: %s", e)
            return []

    @staticmethod
    def _agregar_carrito(carrito):
        """Agrupa líneas por id de producto."""
        mapa = {}
        for linea in carrito or []:
            pid = str(linea.get("id") or linea.get("producto_id") or "").strip()
            if not pid or pid.startswith(">"):
                continue
            nombre = linea.get("producto") or linea.get("nombre") or ""
            cant = float(linea.get("cantidad") or 1)
            precio_lista = float(linea.get("precio_lista") or linea.get("precio") or 0)
            precio_unit = float(linea.get("precio_unitario") or linea.get("precio") or precio_lista)
            codigo = str(linea.get("codigo") or "").strip()
            if pid not in mapa:
                mapa[pid] = {
                    "id": pid,
                    "codigo": codigo,
                    "nombre": nombre,
                    "cantidad": 0.0,
                    "precio_lista": precio_lista,
                    "precio_unitario": precio_unit,
                }
            mapa[pid]["cantidad"] += cant
            if nombre:
                mapa[pid]["nombre"] = nombre
            if precio_lista > 0:
                mapa[pid]["precio_lista"] = precio_lista
            if precio_unit > 0:
                mapa[pid]["precio_unitario"] = precio_unit
        return mapa

    @staticmethod
    def _match_req(req, mapa):
        rid = str(req.get("id") or "").strip()
        rcod = str(req.get("codigo") or "").strip()
        cant_min = float(req.get("cant") or req.get("cantidad") or 1)
        for pid, item in mapa.items():
            if rid and pid == rid:
                if item["cantidad"] >= cant_min:
                    return item, cant_min
            if rcod and item.get("codigo") == rcod:
                if item["cantidad"] >= cant_min:
                    return item, cant_min
        return None, 0

    @staticmethod
    def _eval_combo_fijo(requisitos, mapa):
        articulos = []
        for req in requisitos:
            item, cant_uso = MotorCombos._match_req(req, mapa)
            if not item:
                return None
            nombre = req.get("nombre") or item["nombre"]
            pl = float(item["precio_lista"] or item["precio_unitario"])
            articulos.append({
                "id": item["id"],
                "nombre": nombre,
                "cantidad": cant_uso,
                "precio_lista": pl,
                "precio_unitario": float(item["precio_unitario"]),
                "subtotal_lista": pl * cant_uso,
            })
        return articulos

    @staticmethod
    def _eval_combo_n(requisitos, mapa, elegir_n):
        elegidos = []
        for req in requisitos:
            item, cant_uso = MotorCombos._match_req(req, mapa)
            if item:
                nombre = req.get("nombre") or item["nombre"]
                pl = float(item["precio_lista"] or item["precio_unitario"])
                elegidos.append({
                    "id": item["id"],
                    "nombre": nombre,
                    "cantidad": cant_uso,
                    "precio_lista": pl,
                    "precio_unitario": float(item["precio_unitario"]),
                    "subtotal_lista": pl * cant_uso,
                })
        if len(elegidos) < max(1, elegir_n):
            return None
        return elegidos[:elegir_n] if elegir_n > 0 else elegidos

    @staticmethod
    def _eval_cantidad_grupo(requisitos, mapa, unidades_min):
        total = 0.0
        articulos = []
        ids_pool = set()
        for req in requisitos:
            rid = str(req.get("id") or "").strip()
            rcod = str(req.get("codigo") or "").strip()
            if rid:
                ids_pool.add(rid)
            if rcod:
                for it in mapa.values():
                    if it.get("codigo") == rcod:
                        ids_pool.add(it["id"])
        for pid in ids_pool:
            if pid not in mapa:
                continue
            item = mapa[pid]
            cant = item["cantidad"]
            total += cant
            pl = float(item["precio_lista"] or item["precio_unitario"])
            articulos.append({
                "id": pid,
                "nombre": item["nombre"],
                "cantidad": cant,
                "precio_lista": pl,
                "precio_unitario": float(item["precio_unitario"]),
                "subtotal_lista": pl * cant,
            })
        if total < unidades_min:
            return None
        return articulos

    @staticmethod
    def _aplicar_precio_combo(articulos, precio_combo, descuento_pct):
        total_lista = sum(a["subtotal_lista"] for a in articulos)
        if total_lista <= 0:
            return None
        if precio_combo > 0:
            total_combo = precio_combo
        elif descuento_pct > 0:
            total_combo = total_lista * (1.0 - descuento_pct / 100.0)
        else:
            return None
        ratio = total_combo / total_lista if total_lista else 1.0
        for a in articulos:
            sub_combo = a["subtotal_lista"] * ratio
            a["subtotal_combo"] = sub_combo
            a["precio_combo_unit"] = sub_combo / a["cantidad"] if a["cantidad"] else sub_combo
        return {
            "articulos": articulos,
            "total_lista": total_lista,
            "total_combo": total_combo,
            "ahorro": total_lista - total_combo,
        }

    @staticmethod
    def evaluar(carrito, db=None):
        """
        Devuelve dict del mejor combo aplicable o None.
        """
        if not carrito:
            return None
        try:
            from src.base_de_datos.database import db_manager
            db = db or db_manager
        except ImportError:
            pass

        mapa = MotorCombos._agregar_carrito(carrito)
        if not mapa:
            return None

        mejor = None
        for row in MotorCombos._cargar_combos(db):
            cid = MotorCombos._row_val(row, "id", 0)
            nombre = MotorCombos._row_val(row, "nombre", 1) or "Combo"
            tipo = (MotorCombos._row_val(row, "tipo", 2) or "combo_fijo").lower()
            precio_combo = float(MotorCombos._row_val(row, "precio_combo", 3) or 0)
            descuento_pct = float(MotorCombos._row_val(row, "descuento_pct", 4) or 0)
            elegir_n = int(MotorCombos._row_val(row, "elegir_n", 5) or 0)
            req_raw = MotorCombos._row_val(row, "requisitos_json", 6) or "[]"
            try:
                requisitos = json.loads(req_raw) if isinstance(req_raw, str) else (req_raw or [])
            except json.JSONDecodeError:
                requisitos = []

            if not requisitos:
                continue

            articulos = None
            if tipo == "combo_n":
                articulos = MotorCombos._eval_combo_n(requisitos, mapa, elegir_n or len(requisitos))
            elif tipo == "cantidad_grupo":
                articulos = MotorCombos._eval_cantidad_grupo(requisitos, mapa, elegir_n or 1)
            else:
                articulos = MotorCombos._eval_combo_fijo(requisitos, mapa)

            if not articulos:
                continue

            resultado = MotorCombos._aplicar_precio_combo(articulos, precio_combo, descuento_pct)
            if not resultado or resultado["ahorro"] <= 0:
                continue

            candidato = {
                "combo_id": cid,
                "nombre": nombre,
                "tipo": tipo,
                **resultado,
            }
            if mejor is None or candidato["ahorro"] > mejor["ahorro"]:
                mejor = candidato

        return mejor
