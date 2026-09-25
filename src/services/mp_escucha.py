"""Escucha Mercado Pago con el token del TPV. Un solo hilo para admin y cajero."""

import os
import subprocess
import sys
import time

from src.config import config

CLAVE_SONIDO = "mp_aviso_sonido"


class EscuchaMP:
    _hilo = None
    _vistos = set()

    @staticmethod
    def con_sonido():
        config._load_config()
        return bool(config.get(CLAVE_SONIDO, False))

    @staticmethod
    def fijar_sonido(activo):
        config.set(CLAVE_SONIDO, bool(activo))

    @staticmethod
    def token():
        config._load_config()
        return str(config.get("mp_access_token", "") or "").strip()

    @staticmethod
    def asegurar():
        """Arranca la escucha si hay token en la config. No pide otro."""
        token = EscuchaMP.token()
        if not token:
            return False
        hilo = EscuchaMP._hilo
        if hilo is not None and hilo.isRunning():
            if getattr(hilo, "token", "") == token:
                return True
            hilo.stop()
            hilo.wait(1500)
        from src.admin.mercadopago.componentes.mp_polling_thread import MPPollingThread

        hilo = MPPollingThread(token)
        hilo.new_payment.connect(EscuchaMP.publicar)
        hilo.start()
        EscuchaMP._hilo = hilo
        return True

    @staticmethod
    def publicar(pago):
        id_pago = str((pago or {}).get("id", ""))
        if not id_pago or id_pago in EscuchaMP._vistos:
            return
        EscuchaMP._vistos.add(id_pago)
        from src.admin.mercadopago.historial.archivo import _rotulo

        _, nombre = _rotulo(pago or {})
        monto = float((pago or {}).get("transaction_amount") or 0)
        from src.admin.mercadopago.mercadopago_main import Admin10MP

        Admin10MP.ultimo_pago_detectado = {
            "id": id_pago,
            "monto": monto,
            "nombre": nombre,
            "timestamp": time.time(),
        }
        try:
            from src.admin.mercadopago.historial.archivo import guardar

            guardar([pago])
        except Exception:
            pass
        if EscuchaMP.con_sonido():
            EscuchaMP.avisar(nombre, monto)

    @staticmethod
    def avisar(nombre, monto):
        texto = f"Llegó {float(monto):.0f} pesos, gracias por su compra."
        try:
            escaped = texto.replace('"', '""')
            subprocess.Popen(
                [
                    "powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
                    'Add-Type -AssemblyName System.Speech; '
                    f'$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{escaped}");',
                ]
            )
        except Exception:
            pass
        try:
            from src.utils.paths import get_resource_path

            monto_str = f"${monto:.0f}" if float(monto) == int(monto) else f"${float(monto):.2f}"
            script = get_resource_path(os.path.join("src", "admin", "mp_explosion.py"))
            cmd = [sys.executable, script, str(nombre), monto_str]
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen(cmd, creationflags=flags)
        except Exception:
            pass
