import os
import sys
import json

def get_base_path():
    """
    Retorna la carpeta raíz de la aplicación.
    - Ejecutable (PyInstaller): carpeta donde está el .exe
    - Código fuente: carpeta raíz del proyecto (donde está main.py)
    """
    if hasattr(sys, '_MEIPASS'):
        # En modo ejecutable: usar la carpeta del .exe (no el temp de _MEIPASS)
        exe_dir = os.path.dirname(sys.executable)
        if os.path.basename(exe_dir).lower() == 'bin':
            return os.path.dirname(exe_dir)
        return exe_dir

    # En modo desarrollo: raíz del proyecto (2 niveles arriba de src/utils/paths.py)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_path(relative_path):
    """
    Retorna la ruta absoluta a un recurso (iconos, QSS, assets).
    En ejecutable: busca dentro del bundle _MEIPASS.
    En desarrollo: busca relativo a la raíz del proyecto.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(get_base_path(), relative_path)


def get_data_path(filename=""):
    """
    Retorna la ruta a datos persistentes (DB, config, logs, reportes).
    SIEMPRE es relativa a la carpeta del ejecutable / raíz del proyecto.
    NUNCA contiene rutas del desarrollador.

    En ejecutable: C:\\Program Files\\CajaFacil Pro\\datos\\
    En desarrollo: <raíz del proyecto>\\
    """
    base = get_base_path()
    if filename:
        return os.path.join(base, filename)
    return base


def sanitize_config(config_path):
    """
    Lee config.json y limpia/corrige rutas absolutas del desarrollador.
    Convierte db_path absoluto a ruta relativa si la DB no existe en esa ruta.
    Llama esto al inicio de cada sesión para garantizar portabilidad.
    """
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    changed = False
    base = get_base_path()

    # --- Limpiar db_path si apunta a una ruta que no existe (ruta del creador) ---
    db_path = data.get("db_path", "")
    if db_path:
        # Si el path tiene referencias a rutas de red UNC o rutas de otra PC
        is_unc = db_path.startswith("\\\\") or db_path.startswith("//")
        exists = os.path.exists(os.path.dirname(db_path)) if not is_unc else False

        if is_unc or not exists:
            # Resetear a ruta local automática
            data["db_path"] = ""
            changed = True

    # --- Limpiar cert_key_path y cert_crt_path si son absolutas y no existen ---
    for cert_key in ("cert_key_path", "cert_crt_path"):
        cert_val = data.get(cert_key, "")
        if cert_val and os.path.isabs(cert_val) and not os.path.exists(cert_val):
            # Convertir a ruta relativa basada en el ejecutable
            filename = os.path.basename(cert_val)
            data[cert_key] = os.path.join("certificados", filename)
            changed = True

    if changed:
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass


def ensure_app_folders():
    """
    Crea las carpetas necesarias para que la app funcione en cualquier PC.
    Se llama al primer arranque del ejecutable.
    """
    base = get_base_path()
    folders = [
        "logs",
        "reportes",
        "backups",
        "Etiquetas_Impresas",
        "Folletos_Oferta",
        "Carteles_Oferta",
        "certificados",
        "data",
    ]
    for folder in folders:
        path = os.path.join(base, folder)
        os.makedirs(path, exist_ok=True)
