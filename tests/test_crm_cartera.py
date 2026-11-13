"""El motor de cartera no abre la ventana ni pone la clave en el comando."""
import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.central_red_global.servidor.crm_salida.motor import enviar, huella, leer_clientes, main
from src.central_red_global.servidor.crm_salida.proceso import comando
from src.central_red_global.servidor.crm_salida.vigilante import leer_credenciales, turno


def _db(tmp_path):
    ruta = tmp_path / "punpro.db"
    conn = sqlite3.connect(ruta)
    conn.execute(
        """
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            dni TEXT,
            deuda_actual REAL,
            uid TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO clientes (id, nombre, dni, deuda_actual, uid) VALUES (1, 'Ana', '20111', 50, 'u-1')"
    )
    conn.execute("INSERT INTO clientes (id, nombre, dni, deuda_actual, uid) VALUES (2, '  ', '0', 0, 'u-2')")
    conn.commit()
    conn.close()
    return str(ruta)


def test_lee_solo_clientes_con_nombre(tmp_path):
    clientes = leer_clientes(_db(tmp_path))
    assert len(clientes) == 1
    assert clientes[0]["nombre"] == "Ana"
    assert clientes[0]["deuda_actual"] == 50
    assert clientes[0]["uid"] == "u-1"


def test_enviar_postea_el_lote(tmp_path):
    recibido = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            recibido["path"] = self.path
            recibido["clave"] = self.headers.get("X-API-Key")
            recibido["empresa"] = self.headers.get("X-Empresa-ID")
            largo = int(self.headers.get("Content-Length") or 0)
            recibido["cuerpo"] = json.loads(self.rfile.read(largo).decode("utf-8"))
            cuerpo = b'{"ok": true, "creados": 1, "actualizados": 0, "errores": []}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    try:
        puerto = server.server_address[1]
        clientes = leer_clientes(_db(tmp_path))
        respuesta = enviar(
            f"http://127.0.0.1:{puerto}",
            "clave-crm",
            clientes,
            timeout=5,
            empresa_id="2",
            sucursal_id=3,
            sucursal="Norte",
        )
    finally:
        server.shutdown()
    assert recibido["path"] == "/api/pos/clientes/lote"
    assert recibido["clave"] == "clave-crm"
    assert recibido["empresa"] == "2"
    assert recibido["cuerpo"]["sucursal_id"] == 3
    assert recibido["cuerpo"]["sucursal"] == "Norte"
    assert recibido["cuerpo"]["clientes"][0]["nombre"] == "Ana"
    assert respuesta["creados"] == 1


def test_la_clave_no_viaja_en_el_comando():
    programa, args = comando()
    texto = " ".join([programa, *args])
    assert "--crm-cartera" in args
    assert "api_key" not in texto
    assert "MT_API_KEY" not in texto


def test_main_imprime_el_resultado(tmp_path, monkeypatch, capsys):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            largo = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(largo)
            cuerpo = b'{"ok": true, "creados": 1, "actualizados": 0, "errores": []}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    puerto = server.server_address[1]
    monkeypatch.setenv("CRM_URL", f"http://127.0.0.1:{puerto}")
    monkeypatch.setenv("CRM_API_KEY", "clave-crm")
    monkeypatch.setenv("PUNPRO_DB", _db(tmp_path))
    try:
        codigo = main()
    finally:
        server.shutdown()
    assert codigo == 0
    linea = capsys.readouterr().out.strip().splitlines()[-1]
    dato = json.loads(linea)
    assert dato["ok"] is True
    assert dato["leidos"] == 1
    assert "clave-crm" not in linea


def test_la_esclava_tambien_envia():
    llamadas = []
    cred = {"url": "http://crm"}
    assert turno("esclava", cred, lambda dato: llamadas.append(dato)) == "enviado"
    assert llamadas == [cred]


def test_mas_adelante_solo_la_maestra_envia():
    llamadas = []
    assert turno(
        "esclava",
        {"url": "http://crm"},
        lambda cred: llamadas.append(cred),
        solo_maestra=True,
    ) == "esclava"
    assert llamadas == []


def test_la_maestra_envia_y_un_fallo_no_sale():
    llamadas = []
    cred = {"url": "http://crm", "clave": "secreta"}
    assert turno("maestra", cred, lambda dato: llamadas.append(dato)) == "enviado"
    assert llamadas == [cred]

    def rompe(_dato):
        raise RuntimeError("el CRM no contestó")

    assert turno("maestra", cred, rompe) == "fallo"


def test_sin_nombre_de_empresa_no_hay_envio():
    assert leer_credenciales(
        {"crm_url": "http://crm", "crm_api_key": "secreta", "crm_sucursal": "Centro"}
    ) is None
    dato = leer_credenciales(
        {
            "crm_url": "http://crm",
            "crm_usuario": "maciel",
            "crm_password": "secreta",
            "crm_sucursal_id": "2",
        }
    )
    assert dato["usuario"] == "maciel"
    assert dato["empresa"] == "maciel"
    assert dato["sucursal"] == "maciel"
    assert dato["sucursal_id"] == "2"
    assert "secreta" not in dato["url"]


def test_la_huella_cambia_si_cambia_la_deuda():
    uno = [{"uid": "a", "deuda_actual": 10, "nombre": "Ana"}]
    igual = [{"nombre": "Ana", "deuda_actual": 10, "uid": "a"}]
    otro = [{"uid": "a", "deuda_actual": 11, "nombre": "Ana"}]
    assert huella(uno) == huella(igual)
    assert huella(uno) != huella(otro)


def test_la_cuenta_entra_y_el_lote_lleva_la_sesion(tmp_path, monkeypatch, capsys):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            largo = int(self.headers.get("Content-Length") or 0)
            cuerpo = json.loads(self.rfile.read(largo).decode("utf-8"))
            if self.path == "/auth/login":
                assert cuerpo["username"] == "maciel"
                resp = b'{"ok": true, "user": {"empresa_id": 4, "username": "maciel"}}'
                self.send_response(200)
                self.send_header("Set-Cookie", "session=abc; Path=/")
            elif self.path == "/api/pos/base/tabla":
                resp = b'{"ok": true}'
                self.send_response(200)
            else:
                assert self.path == "/api/pos/clientes/lote"
                assert "session=abc" in (self.headers.get("Cookie") or "")
                assert self.headers.get("X-Empresa-ID") == "4"
                resp = b'{"ok": true, "creados": 1, "actualizados": 0, "errores": []}'
                self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    puerto = server.server_address[1]
    monkeypatch.setenv("CRM_URL", f"http://127.0.0.1:{puerto}")
    monkeypatch.setenv("CRM_USER", "maciel")
    monkeypatch.setenv("CRM_PASSWORD", "clave-de-prueba")
    monkeypatch.setenv("PUNPRO_DB", _db(tmp_path))
    monkeypatch.delenv("CRM_API_KEY", raising=False)
    try:
        codigo = main()
    finally:
        server.shutdown()
    assert codigo == 0
    linea = capsys.readouterr().out
    assert "clave-de-prueba" not in linea
    assert json.loads(linea.strip().splitlines()[-1])["leidos"] == 1
