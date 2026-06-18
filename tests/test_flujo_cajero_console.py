"""Diagnóstico paso a paso del perfil CAJERO (consola, sin GUI interactiva)."""
import os
import sys
import hashlib
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt, QCoreApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

OK = "OK"
FAIL = "FAIL"
steps = []


def step(n, name, fn):
    print(f"\n{'='*60}")
    print(f"PASO {n}: {name}")
    print("=" * 60)
    try:
        fn()
        steps.append((n, name, OK, ""))
        print(f"  -> {OK}")
    except Exception as e:
        steps.append((n, name, FAIL, str(e)))
        print(f"  -> {FAIL}: {e}")
        traceback.print_exc()


def paso1_config():
    from src.config import config
    config._load_config()
    assert config.get("business_name"), "business_name vacío"
    print(f"  Negocio: {config.get('business_name')}")
    print(f"  DB engine: {config.get('db_engine', 'sqlite')}")


def paso2_database():
    from src.base_de_datos.database import db_manager
    db_manager._init_db()
    rows = db_manager.execute_query("SELECT 1 AS ok")
    assert rows, "Sin respuesta de BD"
    print(f"  Motor: {getattr(db_manager, 'db_engine_type', '?')}")
    print(f"  Ping BD: {rows[0]}")


def paso3_candados():
    from src.utils.candados import PerfilLocker
    assert hasattr(PerfilLocker, "check_is_locked"), "Falta check_is_locked"
    assert hasattr(PerfilLocker, "lock_profile"), "Falta lock_profile"
    locked = PerfilLocker.check_is_locked("cajero")
    print(f"  Cajero bloqueado por otra instancia: {locked}")


def paso4_usuarios_cajero():
    from src.base_de_datos.database import db_manager
    rows = db_manager.execute_query(
        "SELECT username, rol FROM usuarios WHERE LOWER(rol) IN ('cajero','admin') ORDER BY username"
    )
    assert rows, "No hay usuarios cajero/admin en BD"
    for r in rows:
        if isinstance(r, dict):
            print(f"  Usuario: {r.get('username')} ({r.get('rol')})")
        else:
            print(f"  Usuario: {r[0]} ({r[1]})")


def paso5_login_simulado():
    from src.base_de_datos.database import db_manager
    from src.config import config

    rows = db_manager.execute_query(
        "SELECT username, password_hash, rol FROM usuarios WHERE LOWER(rol)='cajero' LIMIT 1"
    )
    assert rows, "Sin usuario cajero"
    row = rows[0]
    if isinstance(row, dict):
        user, pwd_hash, rol = row["username"], row["password_hash"], row["rol"]
    else:
        user, pwd_hash, rol = row[0], row[1], row[2]

    for test_pwd in ("cajero", "1234", "admin"):
        h = hashlib.sha256(test_pwd.encode()).hexdigest()
        if h == pwd_hash:
            config.current_user = {"username": user, "role": rol.lower(), "nombre": user}
            print(f"  Login simulado: {user} / {'*'*len(test_pwd)}")
            return
    print(f"  Usuario cajero encontrado: {user} (password de prueba no coincide)")
    config.current_user = {"username": user, "role": "cajero", "nombre": user}


def paso6_caja_service():
    from src.services.caja_service import verificar_y_realizar_autocierre
    hizo, monto = verificar_y_realizar_autocierre()
    print(f"  Autocierre ejecutado: {hizo}, monto: ${monto:.2f}")


def paso7_import_paso5():
    from src.cajero.paso5_terminal import Paso5Terminal
    print(f"  Paso5Terminal: {Paso5Terminal.__name__}")
    mixins = [b.__name__ for b in Paso5Terminal.__mro__ if "Mixin" in b.__name__]
    print(f"  Mixins: {mixins or '(ninguno explícito)'}")


def paso8_import_paso6():
    from src.cajero.paso6_cobro import Paso6Cobro
    mp_methods = [
        m for m in dir(Paso6Cobro)
        if "mercadopago" in m.lower() or "transferencia_mp" in m.lower() or "qr" in m.lower()
    ]
    print(f"  Paso6Cobro cargado")
    print(f"  MP/QR: {mp_methods}")


def paso9_main_window_cajero():
    from src.main_window import MainWindow
    from src.config import config
    if not config.current_user:
        config.current_user = {"username": "cajero", "role": "cajero", "nombre": "Cajero Test"}

    mw = MainWindow()
    mw.apply_roles()
    idx = mw.stacked_widget.currentIndex()
    pantalla = mw.screens[idx] if idx < len(mw.screens) else None
    print(f"  Tab activo index: {idx}")
    print(f"  Widget: {type(pantalla).__name__ if pantalla else 'None'}")
    assert pantalla is not None, "Pantalla cajero no instanciada"
    assert hasattr(pantalla, "refresh_terminal_data") or hasattr(pantalla, "carrito"), "Paso5 incompleto"


def paso10_ui_components():
    mods = [
        "src.cajero.ui_components.terminal_ui_mixin",
        "src.cajero.ui_components.terminal_buscador_mixin",
        "src.cajero.ui_components.terminal_caja_mixin",
        "src.cajero.widgets.pagos_mixtos",
        "src.services.carteleria_service",
    ]
    for m in mods:
        __import__(m)
        print(f"  Import {m.split('.')[-1]}: OK")


if __name__ == "__main__":
    print("\nDIAGNÓSTICO FLUJO CAJERO — Cobro Fácil POS\n")
    step(1, "Configuración", paso1_config)
    step(2, "Base de datos", paso2_database)
    step(3, "Candados de perfil", paso3_candados)
    step(4, "Usuarios cajero en BD", paso4_usuarios_cajero)
    step(5, "Login simulado (cajero)", paso5_login_simulado)
    step(6, "Servicio de caja / autocierre", paso6_caja_service)
    step(7, "Import Paso5 Terminal", paso7_import_paso5)
    step(8, "Import Paso6 Cobro (MP)", paso8_import_paso6)
    step(9, "MainWindow perfil cajero", paso9_main_window_cajero)
    step(10, "UI components cajero", paso10_ui_components)

    print(f"\n{'='*60}")
    print("RESUMEN")
    print("=" * 60)
    fails = [s for s in steps if s[2] == FAIL]
    for n, name, status, err in steps:
        mark = "[OK]" if status == OK else "[FAIL]"
        extra = f" — {err}" if err else ""
        print(f"  {mark} Paso {n}: {name}{extra}")
    print(f"\nTotal: {len(steps)-len(fails)}/{len(steps)} OK")
    sys.exit(1 if fails else 0)
