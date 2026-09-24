import datetime
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QDialog
from PyQt6.QtCore import Qt
from src.config import config
from src.utils.qt_compat import qt_exec
from src.utils.parser import parse_float_regional
from src.base_de_datos.database import db_manager
from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient, fecha_busqueda_mp

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
            begin_date = fecha_busqueda_mp(datetime.timedelta(hours=2))
            end_date = fecha_busqueda_mp()

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
                        anotar = getattr(self.parent, "_anotar_pago_mp", None)
                        if anotar:
                            anotar(transferencia_encontrada, monto)

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

    def ultimo_monto_recibido(self):
        """El cobro aprobado más reciente, para corroborar una transferencia."""
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        if not token:
            aviso = getattr(self.parent, "_avisar", None)
            if aviso:
                aviso("Falta el token de Mercado Pago en la configuración del TPV.")
            return

        progreso = QProgressDialog("Buscando el último monto recibido...", "Cancelar", 0, 0, self.parent)
        progreso.setWindowTitle("Último monto")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.show()
        try:
            begin_date = fecha_busqueda_mp(datetime.timedelta(hours=2))
            end_date = fecha_busqueda_mp()
            url = (
                "https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc"
                f"&limit=10&status=approved&range=date_created&begin_date={begin_date}&end_date={end_date}"
            )
            resp = MPApiClient.get(url, token, timeout=15)
            progreso.close()
        except Exception:
            progreso.close()
            aviso = getattr(self.parent, "_avisar", None)
            if aviso:
                aviso("No se pudo consultar Mercado Pago.")
            return

        if resp.status_code != 200:
            aviso = getattr(self.parent, "_avisar", None)
            if aviso:
                aviso("No se pudo leer el último cobro.")
            return

        from src.cajero.paso6_cobro.vinculo_mp.libro import asociado

        esperado = self._monto_transferencia()
        if esperado is None:
            aviso = getattr(self.parent, "_avisar", None)
            if aviso:
                aviso("No hay transferencia nueva.")
            return

        pago = None
        for p in (resp.json() or {}).get("results") or []:
            p_id = str(p.get("id"))
            if asociado(p_id):
                continue
            existe = db_manager.execute_query(
                "SELECT id FROM mp_transferencias_usadas WHERE payment_id = ?", (p_id,)
            )
            if not existe:
                pago = p
                break
        if not pago:
            aviso = getattr(self.parent, "_avisar", None)
            if aviso:
                aviso("No hay transferencia nueva.")
            return

        monto = float(pago.get("transaction_amount") or 0)
        payer = pago.get("payer") or {}
        nombre = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
        if not nombre:
            nombre = payer.get("email") or "Desconocido"
        aviso = getattr(self.parent, "_avisar", None)
        if abs(monto - esperado) > 0.05:
            try:
                from src.admin.mercadopago.historial.archivo import guardar

                guardar([pago])
            except Exception:
                pass
            if aviso:
                aviso(
                    f"Llegó ${monto:,.2f} de {nombre}. "
                    f"El ticket es ${esperado:,.2f}."
                )
            return
        from src.services.mp_escucha import EscuchaMP
        if EscuchaMP.con_sonido():
            EscuchaMP.avisar(nombre, monto)
        elif aviso:
            aviso(f"Llegó ${monto:,.2f}. Se registra la venta.")
        try:
            db_manager.execute_non_query(
                "INSERT INTO mp_transferencias_usadas (payment_id) VALUES (?)",
                (str(pago.get("id")),),
            )
        except Exception:
            pass
        anotar = getattr(self.parent, "_anotar_pago_mp", None)
        if anotar:
            anotar(pago, monto)
        else:
            self.parent._mp_pago_usado = {"id": str(pago.get("id")), "monto": monto}
        self.parent.txt_pago.setText(f"{monto:.2f}")
        self.parent.finalizar(True)

    def _monto_transferencia(self):
        """El importe que se está esperando. None si este cobro no busca una transferencia."""
        padre = self.parent
        if padre.current_metodo == "Mixto":
            espera = getattr(padre, "_mixto_espera_transferencia", None)
            if espera is not None:
                return float(espera)
            valores = padre.panel_mixto.valores() if hasattr(padre, "panel_mixto") else {}
            parte = float(valores.get("mercadopago") or 0)
            if parte > 0.009:
                return parte
            return None
        if padre.current_metodo == "Transferencia":
            return float(padre.total_final or 0)
        return None
