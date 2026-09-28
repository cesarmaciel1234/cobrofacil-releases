"""Token MP de la tienda (MariaDB `configuracion`). Maestra publica; esclava lee."""

from __future__ import annotations

CLAVES = (
    "mp_access_token",
    "mp_user_id",
    "mp_device_id",
    "mp_qr_pos_external_id",
)


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def publicar() -> bool:
    """
    Maestra: escribe el token TPV en `configuracion` de la tienda.
    Las esclavas lo leen por MariaDB; no hace falta pegar el token en cada notebook.
    """
    try:
        from src.config import config
        from src.central_red_global.sync_tienda.rol import es_esclava

        if es_esclava():
            return False
        config._load_config()
        db = _db()
        for clave in CLAVES:
            valor = str(config.get(clave, "") or "").strip()
            ok = db.execute_non_query(
                "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
                (clave, valor),
            )
            if not ok:
                return False
        return True
    except Exception:
        return False


def leer_clave(clave: str) -> str:
    try:
        filas = _db().execute_query(
            "SELECT valor FROM configuracion WHERE clave = ? LIMIT 1",
            (clave,),
        )
        if not filas:
            return ""
        fila = filas[0]
        # Soporte para pymysql.DictCursor y sqlite3.Row
        try:
            return str(fila["valor"] or "").strip()
        except Exception:
            try:
                return str(fila[0] or "").strip()
            except Exception:
                return str(fila or "").strip()
    except Exception:
        return ""


def traer() -> str:
    """
    Esclava: copia el token (y claves MP) de la tienda al config local.
    Devuelve el access token vigente (tienda o local).
    """
    try:
        from src.config import config

        config._load_config()
        local = str(config.get("mp_access_token", "") or "").strip()
        remoto = leer_clave("mp_access_token")
        if remoto:
            if remoto != local:
                config.set("mp_access_token", remoto)
            for clave in CLAVES:
                if clave == "mp_access_token":
                    continue
                valor = leer_clave(clave)
                if valor and valor != str(config.get(clave, "") or "").strip():
                    config.set(clave, valor)
            return remoto
        return local
    except Exception:
        try:
            from src.config import config

            return str(config.get("mp_access_token", "") or "").strip()
        except Exception:
            return ""
