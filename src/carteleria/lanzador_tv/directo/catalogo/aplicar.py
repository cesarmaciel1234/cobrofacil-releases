"""Normaliza y aplica precios. Una lista vacía no borra la anterior."""

import hashlib
import logging

logger = logging.getLogger("LanzadorDirectoTV")


class CatalogoMixin:
    def _normalizar_productos(self, productos):
        result = []
        for item in productos or []:
            try:
                prod = _una_fila(item)
            except Exception:
                continue
            if not prod:
                continue
            result.append(prod)
        return result

    def _marcar_publicidad(self, productos):
        try:
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

            return motor_publicidad.marcar_lista(productos)
        except Exception:
            return productos

    def _huella_catalogo(self):
        h = hashlib.md5()
        for item in self.rows_precios or []:
            h.update(
                f"{item.get('nombre')}|{item.get('precio')}|{item.get('precio_oferta')}|"
                f"{item.get('precio_oferta_relampago')}|{item.get('icono')}|"
                f"{item.get('icono_url')}|{item.get('es_publicidad')}\n".encode("utf-8", "ignore")
            )
        for clave, filas in (self._ranking_remoto or {}).items():
            h.update(str(clave).encode())
            for row in (filas or [])[:8]:
                if isinstance(row, dict):
                    h.update(f"{row.get('nombre')}|{row.get('cantidad')}\n".encode("utf-8", "ignore"))
        return h.hexdigest()

    def _aplicar_catalogo(self, productos):
        try:
            from src.carteleria.motor_carteleria import iconos_tv

            iconos_tv._png_nombre_cache.clear()
            iconos_tv._png_indice_cache = None
        except Exception:
            pass
        normalized = self._normalizar_productos(productos)
        if not normalized:
            if self.rows_precios:
                logger.warning("Catálogo nuevo vacío — se conserva el que ya se ve")
                self._publicar_estado()
                return
            logger.warning("Sin productos válidos para pintar")
            self._refrescar_paneles(force=False)
            return
        self.rows_precios = self._marcar_publicidad(normalized)
        self._refrescar_paneles(force=False)


def _una_fila(item):
    if isinstance(item, dict):
        nombre = (item.get("nombre") or "").strip()
        if not nombre:
            return None
        precio = float(item.get("precio") or 0)
        oferta = float(item.get("precio_oferta") or 0)
        if precio <= 0 and oferta <= 0:
            return None
        return {
            "id": item.get("id"),
            "nombre": nombre,
            "precio": precio,
            "precio_oferta": oferta,
            "precio_oferta_relampago": float(item.get("precio_oferta_relampago") or 0),
            "precio_oferta_promedio": float(item.get("precio_oferta_promedio") or 0),
            "cant_oferta": float(item.get("cant_oferta") or 0),
            "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
            "unidad": item.get("unidad") or "",
            "es_pesable": item.get("es_pesable") or 0,
            "departamento": item.get("departamento") or item.get("categoria") or "",
            "categoria": item.get("categoria") or "",
            "stock": float(item.get("stock") or 0),
            "icono": item.get("icono") or "",
            "es_publicidad": bool(item.get("es_publicidad")),
        }
    row = list(item) if isinstance(item, (list, tuple)) else []
    if len(row) < 3:
        return None
    nombre = str(row[1] or "").strip()
    if not nombre:
        return None
    precio = float(row[2] or 0) if len(row) > 2 else 0
    oferta = float(row[3] or 0) if len(row) > 3 else 0
    if precio <= 0 and oferta <= 0:
        return None
    return {
        "id": row[13] if len(row) > 13 else None,
        "categoria": row[0] if row else "",
        "nombre": nombre,
        "precio": precio,
        "precio_oferta": oferta,
        "precio_oferta_relampago": float(row[4] or 0) if len(row) > 4 else 0,
        "cant_oferta": float(row[6] or 0) if len(row) > 6 else 0,
        "tipo_unidad_oferta": row[7] if len(row) > 7 else "",
        "stock": float(row[8] or 0) if len(row) > 8 else 0,
        "unidad": row[9] if len(row) > 9 else "",
        "es_pesable": row[10] if len(row) > 10 else 0,
        "departamento": (row[11] if len(row) > 11 else "") or (row[0] if row else ""),
        "icono": row[12] if len(row) > 12 else "",
        "es_publicidad": False,
    }
