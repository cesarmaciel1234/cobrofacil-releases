import json
import os

from src.utils.paths import get_base_path


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
            cls._instance.cargar_configuracion()
        return cls._instance

    def cargar_configuracion(self, forzar=False):
        """Solo lo marcado a mano o al azar en el gestor (no las ofertas)."""
        mtime = 0
        try:
            if os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
        except OSError:
            mtime = 0
        if not forzar and mtime and mtime == getattr(self, "_mtime", 0):
            return
        self._mtime = mtime
        self._nombres = set()
        self._ids = set()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("promocionados") or []:
                    clave = _norm(item)
                    if clave:
                        self._nombres.add(clave)
                for pid in data.get("ids") or []:
                    try:
                        self._ids.add(int(pid))
                    except (TypeError, ValueError):
                        pass
            except Exception:
                pass

    def guardar_configuracion(self, lista_nombres, lista_ids=None):
        data = {
            "promocionados": [str(item).strip() for item in lista_nombres if str(item).strip()],
            "ids": [int(pid) for pid in (lista_ids or []) if pid is not None],
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError:
            pass
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
        # "asado" pega "asado de tira"; "aceite" no pega "aceituna"
        for marcado in self._nombres:
            if clave == marcado or clave.startswith(marcado + " "):
                return True
        return False

    def marcar_lista(self, productos):
        self.cargar_configuracion()
        for item in productos or []:
            item["es_publicidad"] = self.is_promocionado(item.get("nombre"), item.get("id"))
        return productos


motor_publicidad = MotorPublicidad()
