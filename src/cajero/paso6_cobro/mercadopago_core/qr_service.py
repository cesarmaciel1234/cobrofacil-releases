import io
import uuid
import qrcode
from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtGui import QImage, QPixmap
from src.config import config
from src.utils.qt_compat import qt_exec
from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
from src.cajero.paso6_cobro.mercadopago_core.ui_dialogs import QRDialog

class QRService:
    def __init__(self, parent_cobro):
        self.parent = parent_cobro

    def procesar_cobro_qr_pantalla(self, token, monto):
        user_id = config.get("mp_user_id", "")
        external_pos_id = config.get("mp_external_pos_id", "")

        if not user_id or not external_pos_id:
            return False

        ref = str(uuid.uuid4())

        url_crear_qr = lambda: f"https://api.mercadopago.com/instore/orders/qr/seller/collectors/{user_id}/pos/{external_pos_id}/qrs"

        payload_mp = {
            "external_reference": ref,
            "title": "Compra en Punto de Venta",
            "description": "Cobro de ticket via sistema POS",
            "total_amount": float(monto),
            "items": [
                {
                    "sku_number": "TICKET-ACTUAL",
                    "category": "marketplace",
                    "title": "Cobro Venta",
                    "description": "Total de compra en tienda",
                    "unit_price": float(monto),
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": float(monto)
                }
            ]
        }

        try:
            url_qr = url_crear_qr()
            resp = MPApiClient.put(url_qr, payload_mp, token, timeout=10)
        except Exception as e:
            QMessageBox.critical(self.parent, "Error de Conexión", f"Error al contactar Mercado Pago:\n{e}")
            return

        if resp.status_code not in [200, 201]:
            try:
                err_data = resp.json()
                err_code = err_data.get("code", "")
                err_msg  = err_data.get("message", "")
            except Exception:
                err_code = ""
                err_msg  = resp.text

            if resp.status_code == 403 or "UNAUTHORIZED" in err_code:
                msg_usuario = (
                    "Tu token NO tiene permiso para crear órdenes QR (Error 403).\n\n"
                    "Causas más comunes:\n"
                    "  1. El token es de PRUEBA (TEST-...) pero la cuenta es productiva.\n"
                    "  2. La app en developers no tiene el producto 'Código QR' habilitado.\n"
                    "  3. El external_pos_id no coincide con un Punto de Venta de tu cuenta.\n\n"
                    "Solución:\n"
                    "  1. mercadopago.com/developers → Tu integración\n"
                    "  2. Agregá el producto 'Código QR' / 'Pagos presenciales'\n"
                    "  3. Credenciales de Producción → copiá Access Token (APP_USR-...)\n"
                    "  4. Admin → Terminales TPV → Auto-configurar → Guardar"
                )
            elif resp.status_code == 401:
                msg_usuario = (
                    "❌ Token inválido o expirado (Error 401).\n\n"
                    "Actualizá el Access Token en Admin → Configuración → Mercado Pago."
                )
            elif resp.status_code == 404:
                msg_usuario = (
                    "❌ El POS no fue encontrado (Error 404).\n\n"
                    "El 'external_pos_id' configurado no existe en tu cuenta de MP.\n"
                    "Verificá el ID en mercadopago.com → Tu negocio → Puntos de venta."
                )
            else:
                msg_usuario = (
                    f"Error al crear la orden QR (HTTP {resp.status_code}).\n\n"
                    f"Código: {err_code}\n"
                    f"Detalle: {err_msg}"
                )

            QMessageBox.critical(self.parent, "⚠️ Error Mercado Pago QR", msg_usuario)
            return

        data = resp.json()
        qr_data = data.get("qr_data", "")

        if not qr_data:
            QMessageBox.critical(self.parent, "Error MP", "Mercado Pago no devolvió datos de QR.")
            return

        qr_img = qrcode.make(qr_data)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        qimage = QImage()
        qimage.loadFromData(buf.read())
        pixmap = QPixmap.fromImage(qimage)

        headers_mp = MPApiClient.get_headers(token)
        dlg = QRDialog(self.parent, pixmap, monto, token, ref, url_crear_qr, headers_mp)
        if qt_exec(dlg) == QDialog.DialogCode.Accepted and dlg.pagado:
            self.parent.txt_pago.setText(str(monto))
            self.parent.finalizar(True)
