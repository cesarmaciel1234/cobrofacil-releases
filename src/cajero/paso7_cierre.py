import os, sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QMessageBox, QWidget,
    QGraphicsDropShadowEffect, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap
from datetime import datetime

try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    from database import db_manager

# ─────────────────────────────────────────────────────────────
#  MetricCard Elite 2026
# ─────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.color = color
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background: white; border: 1px solid #E2E8F0; border-radius: 16px;
            }}
        """)
        
        # Sombra premium
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(15)
        
        # Contenedor del ícono para darle un fondo suave
        icon_frame = QFrame()
        icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"background: {color}20; border-radius: 25px; border: none;") # 20 es transparencia hexa
        i_lay = QVBoxLayout(icon_frame)
        i_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {color}; background: transparent; border: none;")
        i_lay.addWidget(icon_lbl)
        lay.addWidget(icon_frame)
        
        v_lay = QVBoxLayout()
        v_lay.setSpacing(2)
        v_lay.setAlignment(Qt.AlignVCenter)
        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 900; letter-spacing: 1px; border: none; background: transparent;")
        v_lay.addWidget(self.lbl_tit)
        
        self.lbl_val = QLabel("••••••")
        self.lbl_val.setStyleSheet(f"color: #CBD5E1; font-size: 24px; font-weight: 900; border: none; background: transparent;")
        v_lay.addWidget(self.lbl_val)
        lay.addLayout(v_lay)
        lay.addStretch()

    def revelar(self, valor, formato=True):
        self.lbl_val.setStyleSheet(f"color: {self.color}; font-size: 24px; font-weight: 900;")
        self._animar(valor, formato)

    def _animar(self, final, formato):
        steps = 15
        self._curr_step = 0
        def tick():
            self._curr_step += 1
            v = final * (self._curr_step / steps)
            if formato: self.lbl_val.setText(f"$ {v:,.2f}")
            else: self.lbl_val.setText(f"{int(v)}")
            if self._curr_step < steps: QTimer.singleShot(30, tick)
            else: 
                if formato: self.lbl_val.setText(f"$ {final:,.2f}")
                else: self.lbl_val.setText(f"{int(final)}")
        tick()

# ─────────────────────────────────────────────────────────────
#  Paso 7: Cierre Elite 2026
# ─────────────────────────────────────────────────────────────
class Paso7CierreCaja(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1050, 780)
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso7")
        except:
            pass
        
        self.user = (config.current_user or {}).get("username", "cajero")
        self.role = (config.current_user or {}).get("role", "cajero")
        self.datos = self._get_data()
        self.fase = 2 # Revelado automático desde el inicio
        self.modo = "turno"
        
        self.setup_ui()
        self.apply_glow()
        self._sos_timer = QTimer(self)
        self._sos_timer.timeout.connect(self._blink_sos)

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(40)
        glow.setColor(QColor(0, 0, 0, 80))
        glow.setOffset(0, 8)
        self.main_container.setGraphicsEffect(glow)

    def _get_data(self):
        # Usar la fecha local exacta de Python para blindar contra desajustes de zona horaria en SQLite
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Obtener el fondo de caja de la última apertura del usuario (con fallback al general)
        fondo = float(db_manager.execute_scalar(
            "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND LOWER(usuario) = LOWER(?) ORDER BY id DESC LIMIT 1",
            (self.user,)
        ) or db_manager.execute_scalar(
            "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' ORDER BY id DESC LIMIT 1"
        ) or 0)
        
        # Consultar ventas del usuario de hoy usando LOWER y la fecha de Python
        res_v = db_manager.execute_query(
            "SELECT SUM(total) as t, SUM(CASE WHEN metodo_pago != 'Fiado' THEN pago_otro ELSE 0 END) as ta, SUM(CASE WHEN metodo_pago = 'Fiado' THEN total ELSE 0 END) as tf FROM ventas WHERE estado='COMPLETADA' AND LOWER(usuario) = LOWER(?) AND date(fecha) = ?",
            (self.user, today_str)
        )
        v_total = float((res_v[0]["t"] if res_v else 0) or 0)
        v_tarj = float((res_v[0]["ta"] if res_v else 0) or 0)
        v_fiado = float((res_v[0]["tf"] if res_v else 0) or 0)
        
        # Fallback de Emergencia: Si las ventas personales dan 0, traemos las ventas totales del día en la estación
        if v_total == 0:
            res_v_fallback = db_manager.execute_query(
                "SELECT SUM(total) as t, SUM(CASE WHEN metodo_pago != 'Fiado' THEN pago_otro ELSE 0 END) as ta, SUM(CASE WHEN metodo_pago = 'Fiado' THEN total ELSE 0 END) as tf FROM ventas WHERE estado='COMPLETADA' AND date(fecha) = ?",
                (today_str,)
            )
            v_total = float((res_v_fallback[0]["t"] if res_v_fallback else 0) or 0)
            v_tarj = float((res_v_fallback[0]["ta"] if res_v_fallback else 0) or 0)
            v_fiado = float((res_v_fallback[0]["tf"] if res_v_fallback else 0) or 0)
        
        alertas = db_manager.execute_scalar(
            "SELECT COUNT(*) FROM movimientos_caja WHERE tipo='ALERTA_SEGURIDAD' AND LOWER(usuario) = LOWER(?) AND date(fecha) = ?",
            (self.user, today_str)
        ) or 0
        
        res_d = db_manager.execute_query(
            "SELECT SUM(total) as t, SUM(CASE WHEN metodo_pago != 'Fiado' THEN pago_otro ELSE 0 END) as ta, SUM(CASE WHEN metodo_pago = 'Fiado' THEN total ELSE 0 END) as tf FROM ventas WHERE date(fecha) = ? AND estado IN ('COMPLETADA','CERRADA')",
            (today_str,)
        )
        d_total = float((res_d[0]["t"] if res_d else 0) or 0)
        d_tarj = float((res_d[0]["ta"] if res_d else 0) or 0)
        d_fiado = float((res_d[0]["tf"] if res_d else 0) or 0)
        
        f_hist = abs(float(db_manager.execute_scalar(
            "SELECT SUM(monto) FROM movimientos_caja WHERE tipo='CIERRE_Z' AND LOWER(usuario) = LOWER(?) AND monto < 0",
            (self.user,)
        ) or 0))
        
        return {
            "fondo": fondo, "t_efec": v_total - v_tarj - v_fiado, "t_tarj": v_tarj, "t_fiado": v_fiado, "t_total": v_total,
            "d_total": d_total, "d_tarj": d_tarj, "d_fiado": d_fiado, "f_hist": f_hist, "alertas": alertas,
            "esperado": fondo + (v_total - v_tarj - v_fiado)
        }

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.main_container = QFrame()
        self.main_container.setStyleSheet("background: #F8FAFC; border-radius: 20px; border: 1px solid #E2E8F0;")
        layout.addWidget(self.main_container)
        
        root = QVBoxLayout(self.main_container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header Premium
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background: #1E3A8A; border-top-left-radius: 19px; border-top-right-radius: 19px;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(30, 0, 30, 0)
        
        lbl_tit = QLabel("💎 CAJAFACIL PRO - CONTROL DE CIERRE")
        lbl_tit.setStyleSheet("color: white; font-size: 14px; font-weight: 900; letter-spacing: 2px;")
        h_lay.addWidget(lbl_tit)
        h_lay.addStretch()
        
        if self.datos["f_hist"] > 0:
            self.lbl_sos = QLabel(f"⚠️ DEUDA: $ {self.datos['f_hist']:,.2f}")
            self.lbl_sos.setStyleSheet("color: #F87171; font-weight: 900; font-size: 14px; background: rgba(239, 68, 68, 0.1); padding: 5px 15px; border-radius: 8px;")
            h_lay.addWidget(self.lbl_sos)
            h_lay.addStretch()

        lbl_u = QLabel(f"👤 {self.user.upper()} | {datetime.now().strftime('%H:%M')}")
        lbl_u.setStyleSheet("color: #93C5FD; font-weight: 800; font-size: 12px;")
        h_lay.addWidget(lbl_u)
        root.addWidget(header)

        # Banner de Fase
        self.banner = QLabel("FASE 1: ARQUEO CIEGO - Ingresa el efectivo físico contado")
        self.banner.setFixedHeight(40)
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.setStyleSheet("background: #DBEAFE; color: #1E40AF; font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        root.addWidget(self.banner)

        body = QHBoxLayout()
        body.setContentsMargins(30, 30, 30, 30)
        body.setSpacing(30)
        
        # Izquierda: Métricas
        v_met = QVBoxLayout()
        v_met.setSpacing(15)
        self.card_efec = MetricCard("Ventas Efectivo", "💰", "#10B981")
        self.card_tarj = MetricCard("Ventas Digital", "💳", "#3B82F6")
        self.card_fiado = MetricCard("Ventas a Fiado", "👥", "#F59E0B")
        self.card_fondo = MetricCard("Fondo Apertura", "🏁", "#6366F1")
        self.card_alertas = MetricCard("Alertas Seguridad", "🚨", "#EF4444")
        for c in [self.card_efec, self.card_tarj, self.card_fiado, self.card_fondo, self.card_alertas]: v_met.addWidget(c)
        body.addLayout(v_met, 4)
        
        # Derecha: Arqueo
        v_arq = QVBoxLayout()
        v_arq.setSpacing(20)
        
        self.panel_arq = QFrame()
        self.panel_arq.setObjectName("PanelArq")
        self.panel_arq.setStyleSheet("QFrame#PanelArq { background: white; border: 1px solid #E2E8F0; border-radius: 20px; }")
        
        # Sombra de elevación para el panel derecho
        p_shadow = QGraphicsDropShadowEffect()
        p_shadow.setBlurRadius(30)
        p_shadow.setColor(QColor(0, 0, 0, 15))
        p_shadow.setOffset(0, 8)
        self.panel_arq.setGraphicsEffect(p_shadow)
        
        pa_lay = QVBoxLayout(self.panel_arq)
        pa_lay.setContentsMargins(30, 30, 30, 30)
        pa_lay.setSpacing(20)
        
        lbl_esp_tit = QLabel("EFECTIVO ESPERADO")
        lbl_esp_tit.setStyleSheet("color: #64748B; font-weight: 900; font-size: 13px; letter-spacing: 1px; border: none;")
        lbl_esp_tit.setAlignment(Qt.AlignCenter)
        pa_lay.addWidget(lbl_esp_tit)
        
        self.lbl_esp = QLabel("••••••")
        self.lbl_esp.setAlignment(Qt.AlignCenter)
        self.lbl_esp.setStyleSheet("font-size: 40px; font-weight: 900; color: #94A3B8; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;")
        pa_lay.addWidget(self.lbl_esp)
        
        pa_lay.addSpacing(10)
        lbl_fisico_tit = QLabel("INGRESA EL FÍSICO CONTADO ($)")
        lbl_fisico_tit.setStyleSheet("color: #1E293B; font-weight: 900; font-size: 14px; letter-spacing: 1px; border: none;")
        lbl_fisico_tit.setAlignment(Qt.AlignCenter)
        pa_lay.addWidget(lbl_fisico_tit)
        
        self.txt_fisico = QLineEdit("0.00")
        self.txt_fisico.setAlignment(Qt.AlignCenter)
        self.txt_fisico.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 15px;
                color: #1E293B; font-size: 60px; font-weight: 900; padding: 15px;
            }
            QLineEdit:focus { border-color: #3B82F6; background: white; }
        """)
        self.txt_fisico.textChanged.connect(self._update_diff)
        pa_lay.addWidget(self.txt_fisico)
        
        self.frame_dif = QFrame()
        self.frame_dif.setObjectName("FrameDif")
        self.frame_dif.setFixedHeight(90)
        self.frame_dif.setStyleSheet("QFrame#FrameDif { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 15px; }")
        fd_lay = QHBoxLayout(self.frame_dif)
        
        lbl_dif_tit = QLabel("DIFERENCIA:")
        lbl_dif_tit.setStyleSheet("font-weight: 900; font-size: 16px; color: #475569; border: none; background: transparent;")
        fd_lay.addWidget(lbl_dif_tit)
        
        self.lbl_dif = QLabel("--")
        self.lbl_dif.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_dif.setStyleSheet("font-size: 32px; font-weight: 900; color: #CBD5E1; border: none; background: transparent;")
        fd_lay.addWidget(self.lbl_dif)
        pa_lay.addWidget(self.frame_dif)
        
        v_arq.addWidget(self.panel_arq)
        body.addLayout(v_arq, 6)
        root.addLayout(body)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("background: #F8FAFC; border-top: 1px solid #E2E8F0; border-bottom-left-radius: 19px; border-bottom-right-radius: 19px;")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(30, 0, 30, 0)
        
        if self.role == "admin":
            btn_corte = QPushButton("📊 CORTE DIARIO")
            btn_corte.setStyleSheet("background: white; border: 2px solid #3B82F6; color: #3B82F6; padding: 12px 20px; border-radius: 10px; font-weight: 900;")
            btn_corte.clicked.connect(self.mostrar_corte_diario)
            f_lay.addWidget(btn_corte)
        else:
            btn_exit = QPushButton("✕ CANCELAR")
            btn_exit.setStyleSheet("color: #64748B; font-weight: 900; border: none; background: transparent;")
            btn_exit.clicked.connect(self.reject)
            f_lay.addWidget(btn_exit)
            
        f_lay.addStretch()
        
        self.btn_cierre = QPushButton("🏁 FINALIZAR CIERRE DE TURNO")
        self.btn_cierre.setFixedSize(260, 50)
        self.btn_cierre.setStyleSheet("background: #10B981; color: white; border-radius: 12px; font-weight: 900; font-size: 13px;")
        self.btn_cierre.clicked.connect(self.finalizar_turno_accion)
        f_lay.addWidget(self.btn_cierre)
        
        # EL CAJERO NO PUEDE VER EL CIERRE GLOBAL NI ENTRAR AL ADMIN
        # (Botones globales movidos al Panel de Administración)
            
        # Revelar valores contables inmediatamente al abrir F12
        d = self.datos
        self.card_efec.revelar(d["t_efec"])
        self.card_tarj.revelar(d["t_tarj"])
        self.card_fiado.revelar(d["t_fiado"])
        self.card_fondo.revelar(d["fondo"])
        self.card_alertas.revelar(float(d["alertas"]), formato=False)
        
        self.lbl_esp.setText(f"$ {d['esperado']:,.2f}")
        self.lbl_esp.setStyleSheet("font-size: 40px; font-weight: 900; color: #1E40AF; background: #DBEAFE; border-radius: 12px; padding: 10px; border: 1px solid #BFDBFE;")
        
        self.banner.setText("🔓 CONTROL Y CONCILIACIÓN DE CAJA EN VIVO")
        self._update_diff()
        
        root.addWidget(footer)
        QTimer.singleShot(100, self.txt_fisico.setFocus)

    def _update_diff(self):
        try:
            from src.utils.parser import parse_float_regional
            fisico = parse_float_regional(self.txt_fisico.text())
            dif = fisico - self.datos["esperado"]
            if dif >= 0:
                self.frame_dif.setStyleSheet("background: #F0FDF4; border: 2px solid #10B981; border-radius: 15px;")
                self.lbl_dif.setText(f"+ $ {abs(dif):,.2f}")
                self.lbl_dif.setStyleSheet("color: #059669; font-size: 30px; font-weight: 900;")
                self._sos_timer.stop()
            else:
                self.frame_dif.setStyleSheet("background: #FEF2F2; border: 2px solid #EF4444; border-radius: 15px;")
                self.lbl_dif.setText(f"- $ {abs(dif):,.2f}")
                self.lbl_dif.setStyleSheet("color: #DC2626; font-size: 30px; font-weight: 900;")
                if not self._sos_timer.isActive(): self._sos_timer.start(400)
        except: pass

    def _blink_sos(self):
        self.frame_dif.setStyleSheet(f"background: {'#FEE2E2' if QTimer.remainingTime(self._sos_timer)%800 < 400 else '#FEF2F2'}; border: 2px solid #EF4444; border-radius: 15px;")

    def finalizar_turno_accion(self):
        self.modo = "turno"
        self._finalizar()

    def _finalizar(self):
        # Confirmación amigable de seguridad
        msg = "¿Está seguro de que desea registrar el CIERRE DE CAJA de su turno?\n\nEsta acción cerrará el turno actual e imprimirá el reporte físico."
            
        res = QMessageBox.question(self, "Confirmar Cierre", msg, QMessageBox.Yes | QMessageBox.No)
        if res != QMessageBox.Yes:
            return
            
        try:
            from src.utils.parser import parse_float_regional
            fisico = parse_float_regional(self.txt_fisico.text())
            dif = fisico - self.datos["esperado"]
            from src.config import config
            c_id = config.get("caja_id", 1)
            db_manager.execute_non_query("INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('CIERRE_Z', ?, ?, ?, ?)", (dif, self.user, f"Modo:{self.modo} | Fis:${fisico:.2f} | Esp:${self.datos['esperado']:.2f}", c_id))
            db_manager.execute_non_query("UPDATE ventas SET estado='CERRADA' WHERE estado='COMPLETADA' AND usuario=? AND caja_id=?", (self.user, c_id))
            
            from src.hardware.printer import printer_manager
            # Pasamos modo='turno' para que el ticket lo refleje
            printer_manager.imprimir_ticket_z(self.user, fisico, dif, {**self.datos, "segunda_tiketera": True, "modo": "turno"})
            QMessageBox.information(self, "CIERRE EXITOSO", f"Cierre de Turno registrado correctamente.\nDiferencia: $ {dif:,.2f}")
            
            try:
                from src.services.email_service import enviar_reporte_cierre_z
                datos_cierre = {
                    'caja_id': c_id,
                    'usuario': self.user,
                    'tipo_cierre': 'CIERRE DE TURNO',
                    'efectivo_esperado': self.datos["esperado"],
                    'efectivo_fisico': fisico,
                    'diferencia': dif,
                    'total_ventas': self.datos["t_total"]
                }
                enviar_reporte_cierre_z(datos_cierre)
            except Exception as email_err:
                print(f"Error enviando email: {email_err}")

            from PyQt5.QtWidgets import QApplication
            QApplication.exit(888)
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def mostrar_corte_diario(self):
        # Vista simplificada para Admin
        self.main_container.hide()
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dlg.setFixedSize(900, 600)
        dlg.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #E2E8F0;")
        l = QVBoxLayout(dlg)
        lbl = QLabel("📊 REPORTE DE CORTE DIARIO")
        lbl.setStyleSheet("background: #1E3A8A; color: white; padding: 15px; font-weight: 900; border-top-left-radius: 14px; border-top-right-radius: 14px;")
        l.addWidget(lbl)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Usuario", "Efectivo", "Tarjeta", "Total", "Faltante"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("QTableWidget { border: none; font-size: 13px; } QHeaderView::section { background: #F8FAFC; font-weight: 900; }")
        l.addWidget(table)
        
        btn = QPushButton("VOLVER")
        btn.setStyleSheet("background: #1E3A8A; color: white; padding: 10px; border-radius: 8px; font-weight: 900;")
        btn.clicked.connect(lambda: [dlg.accept(), self.main_container.show()])
        l.addWidget(btn)
        dlg.exec_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.txt_fisico.hasFocus():
                self.finalizar_turno_accion()
        else: super().keyPressEvent(event)
