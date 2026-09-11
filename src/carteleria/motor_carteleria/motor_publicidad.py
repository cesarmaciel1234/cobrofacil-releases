import json
import logging
import os
import time
import urllib.request

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
            cls._instance.cargar_configuracion()
        return cls._instance

    def as_dict(self):
        return {
            "promocionados": sorted(self._nombres),
            "ids": sorted(self._ids),
        }

    def aplicar_remoto(self, data):
        """Lista que manda la maestra / el JSON de sync. Pisa la memoria local."""
        if not isinstance(data, dict):
            return
        nombres = data.get("promocionados") or data.get("nombres") or []
        ids = data.get("ids") or []
        self._nombres = {_norm(x) for x in nombres if _norm(x)}
        self._ids = set()
        for pid in ids:
            try:
                self._ids.add(int(pid))
            except (TypeError, ValueError):
                pass
        self._mtime = 0
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.as_dict(), f, ensure_ascii=False, indent=4)
        except OSError:
            pass

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
            if data.get("promocionados") or data.get("ids"):
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
            from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra, url_maestra

            if not es_esclava():
                return
            host = host_maestra()
            if not host:
                return
            body = json.dumps(self.as_dict(), ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url_maestra("/api/carteleria/publicidad", host),
                data=body,
                method="POST",
                headers={"Content-Type": "application/json", "User-Agent": "CobroFacil-Esclava"},
            )
            urllib.request.urlopen(req, timeout=6).read()
        except Exception as exc:
            logger.debug("publicidad POST maestra: %s", exc)

    def cargar_configuracion(self, forzar=False):
        """JSON local + tabla compartida en MariaDB."""
        mtime = 0
        try:
            if os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
        except OSError:
            mtime = 0
        ahora = time.monotonic()
        if (
            not forzar
            and mtime
            and mtime == getattr(self, "_mtime", 0)
            and ahora - getattr(self, "_last_load", 0) < 12
        ):
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
        if remoto and (remoto.get("promocionados") or remoto.get("ids")):
            data = remoto
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
        }
        try:
            os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            logger.warning("No se pudo guardar publicidad_config.json: %s", exc)
        self.aplicar_remoto(data)
        self._guardar_db()
        self._enviar_a_maestra()
        self.cargar_configuracion(forzar=True)

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
        if clave in self._nombres:
            return True
        for marcado in self._nombres:
            if clave == marcado or clave.startswith(marcado + " "):
                return True
        return False

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
            if item.get("es_publicidad"):
                continue
            item["es_publicidad"] = self.is_promocionado(item.get("nombre"), item.get("id"))
        return lista


motor_publicidad = MotorPublicidad()
