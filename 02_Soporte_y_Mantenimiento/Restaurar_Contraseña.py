# -*- coding: utf-8 -*-
"""
Restaurar_Contraseña.py — Soporte Cobro Fácil POS

Restablece contraseñas de usuarios (admin / jefe / cajero).
Detecta config.json del proyecto o de %USERPROFILE%\\CobroFacil_POS_Install.
Compatible con MariaDB portable (actual) y SQLite legacy.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _hash_pin(pin: str) -> str:
    return _hash_password(pin or "1234")


def _install_roots() -> list[str]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    roots = [project_root]
    install = os.path.join(os.environ.get("USERPROFILE", ""), "CobroFacil_POS_Install")
    if os.path.isdir(install) and install not in roots:
        roots.append(install)
    return roots


def _pick_config() -> tuple[dict, str] | tuple[None, None]:
    found: list[tuple[str, dict]] = []
    for root in _install_roots():
        path = os.path.join(root, "config.json")
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    found.append((root, json.load(f)))
            except Exception:
                pass
    if not found:
        return None, None
    if len(found) == 1:
        return found[0][1], found[0][0]
    print("\nInstalaciones detectadas:")
    for i, (root, _) in enumerate(found, 1):
        print(f"  [{i}] {root}")
    while True:
        sel = input(f"Elija instalación [1-{len(found)}]: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(found):
            idx = int(sel) - 1
            return found[idx][1], found[idx][0]
        print("Opción inválida.")


class DbBackend:
    def list_users(self) -> list[dict]:
        raise NotImplementedError

    def reset_user(self, username: str, password: str, pin: str = "1234") -> bool:
        raise NotImplementedError

    def ensure_defaults(self) -> None:
        raise NotImplementedError

    def create_user(self, username: str, password: str, rol: str, pin: str = "1234") -> None:
        raise NotImplementedError


class MariaBackend(DbBackend):
    def __init__(self, host: str, port: int, database: str, passwords: list[str]):
        import pymysql

        self._pymysql = pymysql
        self.host = host
        self.port = port
        self.database = database
        self.user = "root"
        self.password = ""
        last_err = None
        for pwd in passwords:
            try:
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user="root",
                    password=pwd,
                    database=database,
                    charset="utf8mb4",
                    cursorclass=pymysql.cursors.DictCursor,
                )
                conn.close()
                self.password = pwd
                return
            except Exception as e:
                last_err = e
        raise RuntimeError(f"No se pudo conectar a MariaDB ({host}:{port}/{database}): {last_err}")

    def _connect(self):
        return self._pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            cursorclass=self._pymysql.cursors.DictCursor,
        )

    def _ensure_table(self, cur) -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE,
                password_hash TEXT,
                rol VARCHAR(64),
                pin TEXT DEFAULT '1234'
            )
            """
        )

    def list_users(self) -> list[dict]:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT id, username, rol FROM usuarios ORDER BY id")
                return list(cur.fetchall())
            except Exception as e:
                if "doesn't exist" in str(e).lower():
                    return []
                raise

    def reset_user(self, username: str, password: str, pin: str = "1234") -> bool:
        h = _hash_password(password)
        h_pin = _hash_pin(pin)
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            cur.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row:
                return False
            cur.execute(
                "UPDATE usuarios SET password_hash = %s, pin = %s WHERE username = %s",
                (h, h_pin, username),
            )
            conn.commit()
            return True

    def ensure_defaults(self) -> None:
        defaults = [
            ("admin", "admin", "admin"),
            ("cajero", "cajero", "cajero"),
            ("jefe", "jefe", "jefe"),
        ]
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            for username, password, rol in defaults:
                h = _hash_password(password)
                h_pin = _hash_pin("1234")
                cur.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                if cur.fetchone():
                    cur.execute(
                        "UPDATE usuarios SET password_hash = %s, rol = %s, pin = %s WHERE username = %s",
                        (h, rol, h_pin, username),
                    )
                else:
                    cur.execute(
                        "INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (%s, %s, %s, %s)",
                        (username, h, rol, h_pin),
                    )
            conn.commit()


    def create_user(self, username: str, password: str, rol: str, pin: str = "1234") -> None:
        h = _hash_password(password)
        h_pin = _hash_pin(pin)
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (%s, %s, %s, %s)",
                (username, h, rol, h_pin),
            )
            conn.commit()


class SqliteBackend(DbBackend):
    def __init__(self, db_path: str):
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"No se encuentra la base SQLite: {db_path}")
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self, cur) -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                rol TEXT,
                pin TEXT DEFAULT '1234'
            )
            """
        )

    def list_users(self) -> list[dict]:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT id, username, rol FROM usuarios ORDER BY id")
                return [dict(r) for r in cur.fetchall()]
            except sqlite3.OperationalError:
                return []

    def reset_user(self, username: str, password: str, pin: str = "1234") -> bool:
        h = _hash_password(password)
        h_pin = _hash_pin(pin)
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if not cur.fetchone():
                return False
            cur.execute(
                "UPDATE usuarios SET password_hash = ?, pin = ? WHERE username = ?",
                (h, h_pin, username),
            )
            conn.commit()
            return True

    def ensure_defaults(self) -> None:
        defaults = [
            ("admin", "admin", "admin"),
            ("cajero", "cajero", "cajero"),
            ("jefe", "jefe", "jefe"),
        ]
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            for username, password, rol in defaults:
                h = _hash_password(password)
                h_pin = _hash_pin("1234")
                cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
                if cur.fetchone():
                    cur.execute(
                        "UPDATE usuarios SET password_hash = ?, rol = ?, pin = ? WHERE username = ?",
                        (h, rol, h_pin, username),
                    )
                else:
                    cur.execute(
                        "INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (?, ?, ?, ?)",
                        (username, h, rol, h_pin),
                    )
            conn.commit()

    def create_user(self, username: str, password: str, rol: str, pin: str = "1234") -> None:
        h = _hash_password(password)
        h_pin = _hash_pin(pin)
        with self._connect() as conn:
            cur = conn.cursor()
            self._ensure_table(cur)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (?, ?, ?, ?)",
                (username, h, rol, h_pin),
            )
            conn.commit()


def _open_backend(config: dict, root: str) -> DbBackend:
    engine = str(config.get("db_engine", "sqlite")).strip().lower()
    if engine == "mariadb":
        host = str(config.get("db_host", "")).strip() or "127.0.0.1"
        passwords = [""]
        for key in ("server_password",):
            val = str(config.get(key, "")).strip()
            if val and val not in passwords:
                passwords.append(val)
        for val in ("1234",):
            if val not in passwords:
                passwords.append(val)
        return MariaBackend(host=host, port=3306, database="punpro_db", passwords=passwords)

    db_name = str(config.get("db_name", "punpro.db")).strip() or "punpro.db"
    db_path = str(config.get("db_path", "")).strip()
    if db_path and not db_path.startswith("\\\\"):
        if os.path.isabs(db_path):
            sqlite_path = db_path
        else:
            sqlite_path = os.path.join(root, db_path)
    else:
        sqlite_path = os.path.join(root, db_name)
    return SqliteBackend(sqlite_path)


def _mostrar_usuarios(users: list[dict]) -> None:
    if not users:
        print("  (sin usuarios — use opción 2 para crear los de fábrica)")
        return
    for u in users:
        print(f"  - id={u.get('id')}  usuario={u.get('username')}  rol={u.get('rol')}")


def main() -> int:
    print("=" * 50)
    print("  Cobro Fácil POS — Restaurar contraseña")
    print("=" * 50)

    config, root = _pick_config()
    if not config:
        print("\n[ERROR] No se encontró config.json en el proyecto ni en CobroFacil_POS_Install.")
        input("\nPulse Enter para salir...")
        return 1

    print(f"\nInstalación: {root}")
    print(f"Motor BD: {config.get('db_engine', 'sqlite')}")

    try:
        backend = _open_backend(config, root)
    except Exception as e:
        print(f"\n[ERROR] No se pudo abrir la base de datos:\n  {e}")
        print("\nAsegúrese de que MariaDB esté en marcha (abra el POS una vez o inicie mysqld).")
        input("\nPulse Enter para salir...")
        return 1

    while True:
        print("\n--- MENÚ ---")
        print("[1] Listar usuarios")
        print("[2] Restaurar usuarios de fábrica (admin/admin, cajero/cajero, jefe/jefe)")
        print("[3] Cambiar contraseña de un usuario")
        print("[4] Salir")
        opc = input("\nOpción: ").strip()

        if opc == "1":
            try:
                users = backend.list_users()
                print("\nUsuarios registrados:")
                _mostrar_usuarios(users)
            except Exception as e:
                print(f"\n[ERROR] {e}")

        elif opc == "2":
            print("\nSe crearán o restablecerán:")
            print("  admin / admin  (rol admin)")
            print("  cajero / cajero  (rol cajero)")
            print("  jefe / jefe  (rol jefe)")
            print("  PIN de cajero en terminal: 1234")
            conf = input("\n¿Continuar? (s/n): ").strip().lower()
            if conf == "s":
                try:
                    backend.ensure_defaults()
                    print("\n[OK] Usuarios de fábrica listos.")
                    _mostrar_usuarios(backend.list_users())
                except Exception as e:
                    print(f"\n[ERROR] {e}")

        elif opc == "3":
            username = input("\nNombre de usuario: ").strip()
            if not username:
                continue
            password = input("Nueva contraseña: ").strip()
            if not password:
                print("[AVISO] Contraseña vacía, cancelado.")
                continue
            pin = input("PIN de cajero [1234]: ").strip() or "1234"
            try:
                if backend.reset_user(username, password, pin):
                    print(f"\n[OK] Contraseña de '{username}' actualizada.")
                else:
                    print(f"\n[ERROR] No existe el usuario '{username}'.")
                    crear = input("¿Crearlo? Indique rol (admin/jefe/cajero) o Enter para cancelar: ").strip().lower()
                    if crear in ("admin", "jefe", "cajero"):
                        try:
                            backend.create_user(username, password, crear, pin)
                            print(f"\n[OK] Usuario '{username}' creado con rol {crear}.")
                        except Exception as e:
                            print(f"\n[ERROR] No se pudo crear: {e}")
            except Exception as e:
                print(f"\n[ERROR] {e}")

        elif opc == "4":
            break
        else:
            print("Opción inválida.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelado.")
        sys.exit(0)
