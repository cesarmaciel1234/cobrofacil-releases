import io
import requests
import datetime
import qrcode
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressDialog, QMessageBox
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from src.config import config
from src.base_de_datos.database import db_manager
from src.utils.qt_compat import qt_exec
from src.utils.parser import parse_float_regional

class MercadoPagoIntegracion:
    def __init__(self, parent_cobro):
        self.parent = parent_cobro

    def procesar_pago_mercadopago_point(self):
        # Forzar recarga por si se editó el archivo externamente
        config._load_config()
        
        token = config.get("mp_access_token", "")
        device_id = config.get("mp_device_id", "")

        if self.parent.current_metodo == "QR":
            if not token:
                QMessageBox.warning(
                    self.parent, "Configuración Faltante",
                    "Falta el Access Token de Mercado Pago.\n\n"
                    "Admin → Configuración → Terminales TPV."
                )
                return
        elif not token or not device_id:
            QMessageBox.warning(self.parent, "Configuración Faltante", "Falta el Access Token o el Device ID de Mercado Pago Point en la configuración.")
            return

        if self.parent.current_metodo not in ["Tarjeta", "Mixto", "QR"]:
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
            QMessageBox.warning(self.parent, "Monto inválido", msg)
            return

        # QR usa un flujo completamente distinto
        if self.parent.current_metodo == "QR":
            self._procesar_cobro_qr_pantalla(token, monto)
            return

        url = f"https://api.mercadopago.com/point/integration-api/devices/{device_id}/payment-intents"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        import uuid
        intent_id = str(uuid.uuid4())
        
        # Mercado Pago requiere el monto en centavos para Argentina/Brasil
        monto_centavos = int(round(monto * 100))
        
        if self.parent.current_metodo == "QR":
            payload = {
                "amount": monto_centavos,
                "payment_mode": "qr",
                "additional_info": {
                    "external_reference": intent_id,
                    "print_on_terminal": True
                }
            }
            msg_progreso = "Enviando monto a la Terminal Point (modo QR)..."
        else:
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
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            progreso.close()
            
            if response.status_code in [200, 201]:
                # Iniciar el Polling Dialog
                data = response.json()
                mp_intent_id = data.get("id")
                
                class MPPollingDialog(QDialog):
                    def __init__(self, parent_dlg, token, device_id, intent_id, monto_original, modo="Tarjeta"):
                        super().__init__(parent_dlg)
                        self.token = token
                        self.device_id = device_id
                        self.intent_id = intent_id
                        self.monto_original = monto_original
                        self.aprobado = False
                        
                        self.setWindowTitle("Esperando Pago...")
                        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint) 
                        self.setFixedSize(350, 150)
                        
                        layout = QVBoxLayout(self)
                        if modo == "QR":
                            msg_label = f"📱 Mostre el QR de la terminal al cliente.\nEsperando pago QR por:\n${monto_original:,.2f}"
                        else:
                            msg_label = f"💳 Por favor, pida al cliente que pase la tarjeta por:\n${monto_original:,.2f}"
                        self.lbl_status = QLabel(msg_label)
                        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold;")
                        layout.addWidget(self.lbl_status)
                        
                        self.btn_cancel = QPushButton("Cancelar Cobro en la Terminal")
                        self.btn_cancel.setStyleSheet("background-color: #EF4444; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
                        self.btn_cancel.clicked.connect(self.cancelar_cobro)
                        layout.addWidget(self.btn_cancel)
                        
                        self.timer = QTimer(self)
                        self.timer.timeout.connect(self.check_status)
                        self.timer.start(2500) 
                        
                    def check_status(self):
                        poll_url = f"https://api.mercadopago.com/point/integration-api/payment-intents/{self.intent_id}"
                        head = {"Authorization": f"Bearer {self.token}"}
                        try:
                            res = requests.get(poll_url, headers=head, timeout=5)
                            if res.status_code == 200:
                                state = res.json().get("state")
                                if state == "FINISHED":
                                    self.timer.stop()
                                    self.aprobado = True
                                    self.accept()
                                elif state in ["CANCELED", "ERROR"]:
                                    self.timer.stop()
                                    QMessageBox.warning(self, "Cobro Cancelado", f"El cobro fue cancelado o rechazado en la terminal (Estado: {state}).")
                                    self.reject()
                        except:
                            pass 
                            
                    def cancelar_cobro(self):
                        self.btn_cancel.setEnabled(False)
                        self.btn_cancel.setText("Cancelando...")
                        self.timer.stop()
                        
                        cancel_url = f"https://api.mercadopago.com/point/integration-api/devices/{self.device_id}/payment-intents/{self.intent_id}"
                        head = {"Authorization": f"Bearer {self.token}"}
                        try:
                            requests.delete(cancel_url, headers=head, timeout=5)
                        except:
                            pass
                        
                        self.reject()
                        
                # Mostrar el diálogo
                dialog = MPPollingDialog(self.parent, token, device_id, mp_intent_id, monto, modo=self.parent.current_metodo)
                if qt_exec(dialog) == QDialog.DialogCode.Accepted:
                    self.parent.txt_pago.setText(str(monto))
                    self.parent.finalizar(True)
            else:
                try:
                    err_data = response.json()
                    msg = err_data.get("message", "Error desconocido")
                except:
                    msg = response.text
                QMessageBox.critical(self.parent, "Error MP", f"No se pudo enviar el monto a la terminal:\n{msg}")
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self.parent, "Error de Conexión", f"Error de conexión con Mercado Pago:\n{e}")

    def _procesar_cobro_qr_pantalla(self, token, monto):
        user_id = config.get("mp_user_id", "")
        external_pos_id = config.get("mp_external_pos_id", "")

        if not user_id or not external_pos_id:
            QMessageBox.warning(
                self.parent, "Configuración Faltante",
                "Para cobro por QR dinámico en pantalla faltan configuraciones.\n\n"
                "Asegúrate de llenar:\n- User ID (collector_id)\n- Identificador Sucursal\n- Punto de Venta (Pos ID)\n\nen Admin → Configuración → Terminales TPV."
            )
            return

        import uuid
        ref = str(uuid.uuid4())
        
        url_crear_qr = lambda user, pos: f"https://api.mercadopago.com/instore/orders/qr/seller/collectors/{user}/pos/{pos}/qrs"
        
        headers_mp = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
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
            url_qr = url_crear_qr(user_id, external_pos_id)
            resp = requests.put(url_qr, json=payload_mp, headers=headers_mp, timeout=10)
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

        parent_ref = self.parent

        class QRDialog(QDialog):
            _MP_BLUE = "#009EE3"
            _MP_BLUE_DK = "#007EB5"
            _MP_BG = "#F7FCFF"

            def __init__(self, parent_dlg):
                super().__init__(parent_dlg)
                self.pagado = False
                self.setWindowTitle("Cobro QR - Mercado Pago")
                self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
                self.setFixedSize(700, 700)
                self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {QRDialog._MP_BG};
                        border: 3px solid {QRDialog._MP_BLUE};
                        border-radius: 16px;
                    }}
                """)

                lay = QVBoxLayout(self)
                lay.setContentsMargins(28, 22, 28, 22)
                lay.setSpacing(12)

                lbl_titulo = QLabel("Que el cliente escanee con\nla app de Mercado Pago")
                lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_titulo.setStyleSheet(
                    f"font-size: 15px; font-weight: 800; color: {QRDialog._MP_BLUE_DK}; "
                    "padding: 4px; border: none; background: transparent;"
                )
                lay.addWidget(lbl_titulo)

                lbl_qr = QLabel()
                lbl_qr.setPixmap(pixmap.scaled(340, 340, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_qr.setStyleSheet(
                    f"background: white; border-radius: 12px; padding: 12px; "
                    f"border: 2px solid {QRDialog._MP_BLUE};"
                )
                lay.addWidget(lbl_qr, alignment=Qt.AlignmentFlag.AlignCenter)

                lbl_monto = QLabel(f"${monto:,.2f}")
                lbl_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_monto.setStyleSheet(
                    f"font-size: 42px; font-weight: 900; color: {QRDialog._MP_BLUE}; border: none; background: transparent;"
                )
                lay.addWidget(lbl_monto)

                self.lbl_estado = QLabel("Esperando pago...")
                self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lbl_estado.setStyleSheet(
                    "font-size: 13px; color: #64748B; font-weight: 600; border: none; background: transparent;"
                )
                lay.addWidget(self.lbl_estado)

                lay.addStretch()

                btn_cancelar = QPushButton("Cancelar")
                btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_cancelar.setStyleSheet(
                    "QPushButton { background-color: #EF4444; color: white; padding: 12px; "
                    "font-weight: 800; border-radius: 10px; font-size: 14px; border: none; }"
                    "QPushButton:hover { background-color: #DC2626; }"
                )
                btn_cancelar.clicked.connect(self.cancelar)
                lay.addWidget(btn_cancelar)

                self.timer = QTimer(self)
                self.timer.timeout.connect(self.buscar_pago)
                self.timer.start(3000)

            def buscar_pago(self):
                try:
                    now = datetime.datetime.utcnow()
                    begin = (now - datetime.timedelta(minutes=5)).isoformat() + "Z"
                    end = now.isoformat() + "Z"
                    search_url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=10&status=approved&external_reference={ref}&range=date_created&begin_date={begin}&end_date={end}"
                    head = {"Authorization": f"Bearer {token}"}
                    r = requests.get(search_url, headers=head, timeout=5)
                    if r.status_code == 200:
                        results = r.json().get("results", [])
                        if results:
                            self.timer.stop()
                            self.pagado = True
                            self.lbl_estado.setText("PAGO APROBADO!")
                            self.lbl_estado.setStyleSheet(
                                f"font-size: 15px; color: {QRDialog._MP_BLUE_DK}; font-weight: 900; border: none;"
                            )
                            QTimer.singleShot(1000, self.accept)
                except:
                    pass

            def cancelar(self):
                self.timer.stop()
                try:
                    del_url = url_crear_qr(user_id, external_pos_id)
                    requests.delete(del_url, headers=headers_mp, timeout=5)
                except:
                    pass
                self.reject()

        dlg = QRDialog(self.parent)
        if qt_exec(dlg) == QDialog.DialogCode.Accepted and dlg.pagado:
            self.parent.txt_pago.setText(str(monto))
            self.parent.finalizar(True)

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
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = requests.get(url, headers=headers, timeout=15)
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
