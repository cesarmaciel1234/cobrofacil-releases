import json
import logging
import os
import time
from src.utils.paths import get_base_path

logger = logging.getLogger("PunPro")


def _norm(texto):
    return " ".join(str(texto or "").lower().split())


class MotorPublicidad:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config_path = os.path.join(get_base_path(), "publicidad_config.json")
            cls._instance._nombres = set()
            cls._instance._ids = set()
            cls._instance._mtime = 0
            cls._instance._last_load = 0
            cls._instance._rev = 0
            cls._instance._escucha = False
            cls._instance.cargar_configuracion()
        return cls._instance

    def as_dict(self):
        return {
            "promocionados": sorted(self._nombres),
            "ids": sorted(self._ids),
            "rev": int(getattr(self, "_rev", 0) or 0),
        }

    def _firma(self):
        data = self.as_dict()
        return (tuple(data["promocionados"]), tuple(data["ids"]))

    def _siguiente_rev(self) -> int:
        """Un número compartido en la base. La maestra y la esclava pisan la misma lista."""
        actual = int(getattr(self, "_rev", 0) or 0)
        previo = self._cargar_db()
        if isinstance(previo, dict):
            try:
                actual = max(actual, int(previo.get("rev") or 0))
            except (TypeError, ValueError):
                pass
        return actual + 1

    def aplicar_remoto(self, data):
        """Reemplaza la lista entera. Una revisión vieja no pisa la última que se guardó."""
        if not isinstance(data, dict):
            return False
        try:
            rev = int(data.get("rev") or 0)
        except (TypeError, ValueError):
            rev = 0
        if self._rev and rev and rev < self._rev:
            return False
        nombres = data.get("promocionados") or data.get("nombres") or []
        ids = data.get("ids") or []
        self._nombres = {_norm(x) for x in nombres if _norm(x)}
        self._ids = set()
        for pid in ids:
            try:
                self._ids.add(int(pid))
            except (TypeError, ValueError):
                pass
        if rev:
            self._rev = rev
        try:
            os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.as_dict(), f, ensure_ascii=False, indent=4)
            self._mtime = os.path.getmtime(self.config_path)
        except OSError:
            self._mtime = 0
        self._guardar_db()
        self._last_load = time.monotonic()
        return True

    def _traer_de_maestra(self):
        try:
            from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra
            from src.carteleria.vitrina.red.http_maestra import leer_publicidad_maestra

            if not es_esclava():
                return None
            host = host_maestra()
            if not host:
                return None
            return leer_publicidad_maestra(host)
        except Exception:
            return None

    def _cargar_db(self) -> dict | None:
        try:
            from src.base_de_datos.database import db_manager

            db_manager.execute_non_query(
                "CREATE TABLE IF NOT EXISTS publicidad_tv (id INT PRIMARY KEY, config_json TEXT)"
            )
            rows = db_manager.execute_query("SELECT config_json FROM publicidad_tv WHERE id = 1")
            if not rows:
                return None
            raw = rows[0]["config_json"] if isinstance(rows[0], dict) else rows[0][0]
            data = json.loads(raw or "{}")
            if isinstance(data, dict) and (
                "promocionados" in data or "ids" in data or "nombres" in data
            ):
                return data
        except Exception as exc:
            logger.debug("publicidad DB: %s", exc)
        return None

    def _guardar_db(self):
        try:
            from src.base_de_datos.database import db_manager

            payload = json.dumps(self.as_dict(), ensure_ascii=False)
            db_manager.execute_non_query(
                "CREATE TABLE IF NOT EXISTS publicidad_tv (id INT PRIMARY KEY, config_json TEXT)"
            )
            db_manager.execute_non_query("DELETE FROM publicidad_tv WHERE id = 1")
            db_manager.execute_non_query(
                "INSERT INTO publicidad_tv (id, config_json) VALUES (1, ?)", (payload,)
            )
        except Exception as exc:
            logger.debug("publicidad guardar DB: %s", exc)

    def _enviar_a_maestra(self):
        try:
            from src.central_red_global.sync_tienda.rol import (
                es_esclava,
                host_maestra,
                pedir_a_maestra,
                url_maestra,
            )

            if not es_esclava():
                return
            host = host_maestra()
            if not host:
                return
            body = json.dumps(self.as_dict(), ensure_ascii=False).encode("utf-8")
            pedir_a_maestra(
                url_maestra("/api/carteleria/publicidad", host),
                data=body,
                method="POST",
                extra={"Content-Type": "application/json"},
                timeout=6,
            ).read()
        except Exception as exc:
            logger.warning("publicidad POST maestra: %s", exc)

    def cargar_configuracion(self, forzar=False):
        """JSON local + tabla compartida en MariaDB."""
        mtime = 0
        try:
            if os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
        except OSError:
            mtime = 0
        self.asegurar_escucha()
        ahora = time.monotonic()
        if (
            not forzar
            and mtime
            and mtime == getattr(self, "_mtime", 0)
            and ahora - getattr(self, "_last_load", 0) < 12
        ):
            return
        http_pub = self._traer_de_maestra()
        if http_pub is not None:
            self.aplicar_remoto(http_pub)
            return
        remoto = self._cargar_db()
        self._last_load = ahora
        self._mtime = mtime
        self._nombres = set()
        self._ids = set()
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        if remoto is not None:
            data = remoto
        try:
            self._rev = int(data.get("rev") or 0)
        except (TypeError, ValueError):
            self._rev = 0
        for item in data.get("promocionados") or []:
            clave = _norm(item)
            if clave:
                self._nombres.add(clave)
        for pid in data.get("ids") or []:
            try:
                self._ids.add(int(pid))
            except (TypeError, ValueError):
                pass

    def guardar_configuracion(self, lista_nombres, lista_ids=None):
        data = {
            "promocionados": [str(item).strip() for item in lista_nombres if str(item).strip()],
            "ids": [int(pid) for pid in (lista_ids or []) if pid is not None],
            "rev": self._siguiente_rev(),
        }
        self.aplicar_remoto(data)
        self._enviar_a_maestra()
        self._avisar_pares()
        self._avisar_tv()

    def _avisar_pares(self):
        """La otra PC (maestra o esclava) reemplaza su lista al recibir este UDP."""
        self.asegurar_escucha()
        try:
            from src.central_red_global.network_engine import get_network_engine

            eng = get_network_engine()
            if eng is None:
                return
            eng.broadcast("PUBLICIDAD", self.as_dict())
        except Exception as exc:
            logger.debug("publicidad aviso pares: %s", exc)

    def asegurar_escucha(self):
        if getattr(self, "_escucha", False):
            return
        try:
            from src.central_red_global.network_engine import get_network_engine

            eng = get_network_engine()
            if eng is None:
                return
            eng.message_received.connect(self._al_mensaje_red)
            self._escucha = True
        except Exception as exc:
            logger.debug("publicidad escucha: %s", exc)

    def _al_mensaje_red(self, _origen, tipo, datos):
        if str(tipo or "") != "PUBLICIDAD" or not isinstance(datos, dict):
            return
        antes = self._firma()
        if self.aplicar_remoto(datos) and self._firma() != antes:
            self._avisar_tv()

    def _avisar_tv(self):
        """La cara mira el sello. Sin esto, un cambio de avisos no redibuja la TV."""
        try:
            from src.central_red_global.sync_tienda.aviso_tv import pisar_sello

            pisar_sello()
        except Exception as exc:
            logger.debug("publicidad aviso TV: %s", exc)

    def is_promocionado(self, nombre_producto, producto_id=None):
        if producto_id is not None:
            try:
                if int(producto_id) in self._ids:
                    return True
            except (TypeError, ValueError):
                pass
        clave = _norm(nombre_producto)
        if not clave:
            return False
        return clave in self._nombres

    def _traer_faltantes(self, productos):
        from src.base_de_datos.database import db_manager

        have_n = {_norm(p.get("nombre")) for p in productos or []}
        have_i = set()
        for p in productos or []:
            try:
                have_i.add(int(p.get("id")))
            except (TypeError, ValueError):
                pass
        extra = []
        for pid in self._ids:
            if pid in have_i:
                continue
            rows = db_manager.execute_query(
                "SELECT id, nombre, precio, precio_oferta, precio_oferta_relampago, cant_oferta, "
                "tipo_unidad_oferta, stock, unidad, es_pesable, departamento, categoria, icono "
                "FROM productos WHERE id = ? LIMIT 1",
                (pid,),
            )
            if rows:
                extra.append(dict(rows[0]) if not isinstance(rows[0], dict) else rows[0])
        for nombre in self._nombres:
            if nombre in have_n:
                continue
            rows = db_manager.execute_query(
                "SELECT id, nombre, precio, precio_oferta, precio_oferta_relampago, cant_oferta, "
                "tipo_unidad_oferta, stock, unidad, es_pesable, departamento, categoria, icono "
                "FROM productos WHERE LOWER(nombre) = ? LIMIT 1",
                (nombre,),
            )
            if rows:
                extra.append(dict(rows[0]) if not isinstance(rows[0], dict) else rows[0])
        return extra

    def marcar_lista(self, productos):
        self.cargar_configuracion()
        lista = list(productos or [])
        try:
            for item in self._traer_faltantes(lista):
                lista.append(item)
        except Exception as exc:
            logger.debug("publicidad extra: %s", exc)
        for item in lista:
            item["es_publicidad"] = self.is_promocionado(item.get("nombre"), item.get("id"))
        return lista


motor_publicidad = MotorPublicidad()
