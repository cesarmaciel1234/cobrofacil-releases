import uuid
from PyQt6.QtWidgets import QDialog, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt
from src.config import config
from src.utils.qt_compat import qt_exec
from src.utils.parser import parse_float_regional
from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
from src.cajero.paso6_cobro.mercadopago_core.ui_dialogs import MPPollingDialog

class PointService:
    def __init__(self, parent_cobro):
        self.parent = parent_cobro

    def procesar_pago_mercadopago_point(self, cerrar=True):
        config._load_config()
        token = config.get("mp_access_token", "")
        device_id = config.get("mp_device_id", "")

        if not token or not device_id:
            return False

        if self.parent.current_metodo not in ["Tarjeta", "Mixto"]:
            self.parent.set_metodo("Tarjeta")

        if self.parent.current_metodo == "Mixto":
            if getattr(self.parent, 'valores_mixtos', None):
                monto = self.parent.valores_mixtos.get("tarjeta", 0.0)
            else:
                monto = 0.0
        else:
            monto_str = self.parent.txt_pago.text().replace("$", "").replace(" ", "").strip()
            try:
                monto = parse_float_regional(monto_str)
            except:
                monto = self.parent.total_final

        if monto <= 0:
            msg = "El monto de Tarjeta (Point) en pago Mixto es cero." if self.parent.current_metodo == "Mixto" else "Ingrese un monto a cobrar válido."
            if cerrar:
                QMessageBox.warning(self.parent, "Monto inválido", msg)
            return None

        url = f"https://api.mercadopago.com/point/integration-api/devices/{device_id}/payment-intents"
        intent_id = str(uuid.uuid4())
        monto_centavos = int(round(monto * 100))

        payload = {
            "amount": monto_centavos,
            "additional_info": {
                "external_reference": intent_id,
                "print_on_terminal": True
            }
        }
        msg_progreso = "Enviando monto a la Terminal Point..."

        progreso = QProgressDialog(msg_progreso, "Cancelar", 0, 0, self.parent)
        progreso.setWindowTitle("Mercado Pago Point")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.show()

        try:
            response = MPApiClient.post(url, payload, token, timeout=10)
            progreso.close()

            if response.status_code in [200, 201]:
                data = response.json()
                mp_intent_id = data.get("id")

                dialog = MPPollingDialog(self.parent, token, device_id, mp_intent_id, monto, modo=self.parent.current_metodo)
                if qt_exec(dialog) == QDialog.DialogCode.Accepted:
                    if cerrar:
                        self.parent.txt_pago.setText(str(monto))
                        self.parent.finalizar(True)
                    return True
                return None
            else:
                try:
                    err_data = response.json()
                    msg = err_data.get("message", "Error desconocido")
                except:
                    msg = response.text
                QMessageBox.critical(self.parent, "Error MP", f"No se pudo enviar el monto a la terminal:\n{msg}")
                return None
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self.parent, "Error de Conexión", f"Error de conexión con Mercado Pago:\n{e}")
            return None
