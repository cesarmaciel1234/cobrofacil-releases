import datetime
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QDialog
from PyQt6.QtCore import Qt
from src.config import config
from src.utils.qt_compat import qt_exec
from src.utils.parser import parse_float_regional
from src.base_de_datos.database import db_manager
from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient

class PollingService:
    def __init__(self, parent_cobro):
        self.parent = parent_cobro

    def verificar_transferencia_mp(self):
        token = config.get("mp_access_token", "")
        if not token:
            QMessageBox.warning(self.parent, "Configuración Faltante", "Falta el Access Token de Mercado Pago en la configuración.")
            return
            
        monto_str = self.parent.txt_pago.text().replace("$", "").replace(" ", "").strip()
        try:
            monto = parse_float_regional(monto_str)
        except:
            monto = self.parent.total_final
            
        if self.parent.current_metodo == "Mixto" and getattr(self.parent, 'valores_mixtos', None):
            monto = self.parent.valores_mixtos.get("mercadopago", 0.0)
            
        if monto <= 0:
            msg = "El monto a verificar es cero. Asegúrese de haber ingresado un monto válido en Transf./QR."
            QMessageBox.warning(self.parent, "Monto inválido", msg)
            return

        progreso = QProgressDialog("Buscando transferencias y QR recientes en Mercado Pago...", "Cancelar", 0, 0, self.parent)
        progreso.setWindowTitle("Verificando Pagos MP")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.show()

        try:
            now = datetime.datetime.utcnow()
            begin_date = (now - datetime.timedelta(hours=2)).isoformat() + "Z"
            end_date = now.isoformat() + "Z"
            
            url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=50&status=approved&range=date_created&begin_date={begin_date}&end_date={end_date}"
            
            resp = MPApiClient.get(url, token, timeout=15)
            progreso.close()
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                transferencia_encontrada = None
                
                for p in results:
                    p_amount = p.get("transaction_amount")
                    p_id = str(p.get("id"))
                    
                    if p_amount == monto:
                        existe = db_manager.execute_query("SELECT id FROM mp_transferencias_usadas WHERE payment_id = ?", (p_id,))
                        if not existe:
                            transferencia_encontrada = p
                            break
                            
                if transferencia_encontrada:
                    p_id = str(transferencia_encontrada.get("id"))
                    payer = transferencia_encontrada.get("payer", {})
                    payer_info = payer.get("first_name", "") + " " + payer.get("last_name", "")
                    if not payer_info.strip():
                        payer_info = payer.get("email", "Desconocido")
                        
                    reply = QMessageBox.question(
                        self.parent, "Pago Encontrado", 
                        f"Se encontró un pago/transferencia reciente por ${monto:,.2f}.\n\n"
                        f"Origen: {payer_info.strip()}\n"
                        f"ID: {p_id}\n\n"
                        f"¿Confirmar y asociar este pago a la venta actual?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            db_manager.execute_non_query("INSERT INTO mp_transferencias_usadas (payment_id) VALUES (?)", (p_id,))
                        except:
                            pass 
                            
                        QMessageBox.information(self.parent, "Cobro Aprobado", "Pago validado correctamente. Emitiendo ticket...")
                        self.parent.txt_pago.setText(str(monto))
                        self.parent.finalizar(True)
                else:
                    msg_box = QMessageBox(self.parent)
                    msg_box.setWindowTitle("No Encontrada")
                    msg_box.setText(f"No se encontró ninguna transferencia o código QR reciente, nueva y no utilizada por el monto exacto de ${monto:,.2f}.")
                    msg_box.setInformativeText("Si confías en este cliente y quieres dejar el cobro en espera de que llegue la transferencia, presiona 'Forzar Pendiente'.")
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    
                    btn_ok = msg_box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
                    btn_forzar = msg_box.addButton("Forzar Pendiente", QMessageBox.ButtonRole.ActionRole)
                    
                    qt_exec(msg_box)
                    
                    if msg_box.clickedButton() == btn_forzar:
                        from PyQt6.QtWidgets import QInputDialog
                        nombre, ok = QInputDialog.getText(self.parent, "Cobro Pendiente", "Ingrese el nombre del cliente para buscarlo luego:")
                        if ok and nombre.strip():
                            self.parent.nombre_pendiente = nombre.strip()
                            self.parent.txt_pago.setText(str(monto))
                            self.parent.finalizar(True)
            else:
                QMessageBox.critical(self.parent, "Error MP", f"No se pudieron buscar las transferencias:\n{resp.text}")
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self.parent, "Error de Conexión", f"Error de conexión con Mercado Pago:\n{e}")
