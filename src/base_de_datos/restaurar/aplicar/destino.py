"""A qué tienda se restaura: la MariaDB de la maestra, o el punpro.db si la tienda es SQLite sola."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class SinTienda(RuntimeError):
    pass


LOCALES = ("", "localhost", "127.0.0.1", "::1")


@dataclass
class Destino:
    motor: str  # mariadb | sqlite
    host: str = ""
    archivo: str = ""
    servidor: str = ""
    conexion: dict = field(default_factory=dict)

    @property
    def es_local(self) -> bool:
        if self.motor == "sqlite":
            return True
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

        return AutoBlindajeDB._host_es_esta_pc(self.host)

    def conectar(self):
        """Conexión propia con transacción. MariaDB nunca cae a SQLite."""
        if self.motor == "sqlite":
            import sqlite3

            return sqlite3.connect(self.archivo, timeout=30)
        import pymysql

        kw = dict(self.conexion)
        kw.update(autocommit=False, connect_timeout=5, read_timeout=300, write_timeout=300)
        return pymysql.connect(**kw)


def destino_actual() -> Destino:
    """La tienda con la que trabaja esta PC. Una caja sin maestra no restaura: escribiría su SQLite de emergencia."""
    from src.base_de_datos.database import db_manager
    from src.config import config
    from src.utils.paths import get_base_path

    host_cfg = str(config.get("db_host", "") or "").strip()
    motor = getattr(db_manager, "db_engine_type", "sqlite")
    if motor == "mariadb" and not getattr(db_manager, "_forced_local_offline", False):
        eng = getattr(db_manager, "mariadb_engine", None)
        if eng is None:
            raise SinTienda("No hay conexión con la base de la tienda.")
        kw = eng._connect_kwargs()
        destino = Destino("mariadb", host=str(kw.get("host") or host_cfg or "127.0.0.1"), conexion=kw)
        try:
            conn = destino.conectar()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT @@hostname")
                    destino.servidor = str((cur.fetchone() or [""])[0] or "")
            finally:
                conn.close()
        except Exception as e:
            raise SinTienda(f"La maestra no contesta ({e}).") from e
        return destino
    if host_cfg.lower() not in LOCALES or config.get("is_master") is False:
        raise SinTienda(
            "Esta PC es caja y no está conectada a la maestra. Restaurá con la maestra conectada o sentado en ella."
        )
    return Destino("sqlite", archivo=os.path.join(get_base_path(), "punpro.db"))
