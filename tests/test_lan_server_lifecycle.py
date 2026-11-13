import http.client
import socket
import threading
from http.server import BaseHTTPRequestHandler

from src.central_red_global import lan_server


def _puerto_libre():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_api_lan_atiende_solicitudes_concurrentes_y_limita_hilos(monkeypatch):
    inicio = threading.Event()
    liberar = threading.Event()
    activos = 0
    max_activos = 0
    candado = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal activos, max_activos
            with candado:
                activos += 1
                max_activos = max(max_activos, activos)
                if activos >= 2:
                    inicio.set()
            liberar.wait(2)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            with candado:
                activos -= 1

        def log_message(self, *_args):
            pass

    monkeypatch.setattr(lan_server, "_HTTP_WORKERS", 2)
    server = lan_server._BoundedThreadingHTTPServer(("127.0.0.1", _puerto_libre()), Handler)
    hilo_servidor = threading.Thread(target=server.serve_forever, daemon=True)
    hilo_servidor.start()
    resultados = []

    def solicitar():
        conn = http.client.HTTPConnection(*server.server_address, timeout=3)
        try:
            conn.request("GET", "/")
            response = conn.getresponse()
            resultados.append(response.status)
            response.read()
        except (OSError, http.client.HTTPException):
            resultados.append(None)
        finally:
            conn.close()

    c1 = threading.Thread(target=solicitar)
    c2 = threading.Thread(target=solicitar)
    c3 = threading.Thread(target=solicitar)
    try:
        c1.start()
        c2.start()
        assert inicio.wait(2), "el servidor no atendió dos solicitudes en paralelo"
        # Con ambos slots ocupados, la 3ra solicitud debe ser rechazada por límite
        c3.start()
        c3.join(2)
        liberar.set()
        c1.join(3)
        c2.join(3)

        assert not c1.is_alive() and not c2.is_alive() and not c3.is_alive()
        assert max_activos == 2
        assert resultados.count(200) == 2
        assert resultados.count(None) == 1
    finally:
        liberar.set()
        server.shutdown()
        server.server_close()
        hilo_servidor.join(2)


def test_supervisor_http_reintenta_despues_de_falla_de_servicio(monkeypatch):
    salida = threading.Event()
    segunda_instancia = threading.Event()
    construcciones = []

    class ServidorFalso:
        def __init__(self, _address, _handler):
            construcciones.append(self)

        def serve_forever(self, poll_interval):
            if len(construcciones) == 1:
                raise OSError("fallo simulado")
            segunda_instancia.set()
            salida.wait(2)

        def server_close(self):
            pass

        def shutdown(self):
            salida.set()

    monkeypatch.setattr(lan_server, "lan_exit_event", threading.Event())
    monkeypatch.setattr(lan_server, "_http_server_instance", None)
    monkeypatch.setattr(lan_server, "_BoundedThreadingHTTPServer", ServidorFalso)
    monkeypatch.setattr(lan_server, "_RETRY_SECONDS", 0.01)
    monkeypatch.setattr(lan_server, "API_PORT", _puerto_libre())

    hilo = threading.Thread(target=lan_server.start_http_server, daemon=True)
    hilo.start()
    try:
        assert segunda_instancia.wait(1), "el servidor no reintentó después del fallo"
        assert len(construcciones) >= 2
    finally:
        lan_server.stop_lan_server()
        hilo.join(2)
    assert not hilo.is_alive()


def test_supervisor_udp_reintenta_despues_de_falla_de_enlace(monkeypatch):
    enlazado = threading.Event()
    salida = threading.Event()
    sockets = []

    class SocketFalso:
        def __init__(self, *_args):
            sockets.append(self)

        def setsockopt(self, *_args):
            pass

        def bind(self, _address):
            if len(sockets) == 1:
                raise OSError("puerto ocupado")
            enlazado.set()

        def settimeout(self, _timeout):
            pass

        def recvfrom(self, _size):
            salida.wait(0.01)
            raise socket.timeout()

        def connect(self, *_args, **_kwargs):
            raise OSError("simulacion offline")

        def close(self):
            pass

    monkeypatch.setattr(lan_server, "lan_exit_event", threading.Event())
    monkeypatch.setattr(lan_server.socket, "socket", SocketFalso)
    monkeypatch.setattr(lan_server, "_RETRY_SECONDS", 0.01)

    hilo = threading.Thread(target=lan_server.start_udp_discovery_server, daemon=True)
    hilo.start()
    try:
        assert enlazado.wait(1), "el servicio UDP no reintentó después del fallo de enlace"
        assert len(sockets) >= 2
    finally:
        salida.set()
        lan_server.stop_lan_server()
        hilo.join(2)
    assert not hilo.is_alive()
