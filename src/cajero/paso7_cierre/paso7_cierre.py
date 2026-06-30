from src.utils.qt_compat import qt_exec
import os, sys
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QMessageBox, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap
from datetime import datetime

try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    from database import db_manager

from src.cajero.paso7_cierre.logica.cierre_controller import CierreController
from src.cajero.paso7_cierre.componentes_paso7_cierre.metric_card import MetricCard
from src.cajero.paso7_cierre.componentes_paso7_cierre.panel_arqueo import PanelArqueo
from src.cajero.paso7_cierre.componentes_paso7_cierre.corte_diario_admin import CorteDiarioDialog

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

    def apply_glow(self):
        # Se elimina QGraphicsDropShadowEffect por rendimiento.
        pass

    def _get_data(self):
        from src.config import config
        c_id = config.get("caja_id", 1)
        
        datos = CierreController.obtener_datos_cierre(self.user, c_id)
        self._apertura_fecha = datos.get("apertura_fecha")
        return datos

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.main_container = QFrame()
        self.main_container.setObjectName("CierreMain")
        layout.addWidget(self.main_container)
        
        root = QVBoxLayout(self.main_container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header Premium
        header = QFrame()
        header.setObjectName("CierreHeader")
        header.setFixedHeight(60)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(30, 0, 30, 0)
        
        lbl_tit = QLabel("💎 CAJAFACIL PRO - CONTROL DE CIERRE")
        lbl_tit.setObjectName("CierreTitle")
        h_lay.addWidget(lbl_tit)
        h_lay.addStretch()
        
        if self.datos["f_hist"] > 0:
            self.lbl_sos = QLabel(f"⚠️ DEUDA: $ {self.datos['f_hist']:,.2f}")
            self.lbl_sos.setObjectName("CierreSos")
            h_lay.addWidget(self.lbl_sos)
            h_lay.addStretch()

        lbl_u = QLabel(f"👤 {self.user.upper()} | {datetime.now().strftime('%H:%M')}")
        lbl_u.setObjectName("CierreUser")
        h_lay.addWidget(lbl_u)
        root.addWidget(header)

        # Banner de Fase
        self.banner = QLabel("FASE 1: ARQUEO CIEGO - Ingresa el efectivo físico contado")
        self.banner.setObjectName("CierreBanner")
        self.banner.setFixedHeight(40)
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        
        self.panel_arq = PanelArqueo(self)
        
        v_arq.addWidget(self.panel_arq)
        body.addLayout(v_arq, 6)
        root.addLayout(body)

        # Footer
        footer = QFrame()
        footer.setObjectName("CierreFooter")
        footer.setFixedHeight(90)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(30, 0, 30, 0)
        
        if self.role == "admin":
            btn_corte = QPushButton("📊 CORTE DIARIO")
            btn_corte.setObjectName("BtnCorteDiario")
            btn_corte.clicked.connect(self.mostrar_corte_diario)
            f_lay.addWidget(btn_corte)
        else:
            btn_exit = QPushButton("Salir")
            btn_exit.setObjectName("BtnCloseHist")
            btn_exit.clicked.connect(self.reject)
            f_lay.addWidget(btn_exit)
            
        f_lay.addStretch()
        
        self.btn_cierre = QPushButton("🏁 FINALIZAR CIERRE DE TURNO")
        self.btn_cierre.setObjectName("BtnCierreTurno")
        self.btn_cierre.setFixedSize(260, 50)
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
        
        self.panel_arq.set_esperado(d['esperado'])
        
        self.banner.setText("🔓 CONTROL Y CONCILIACIÓN DE CAJA EN VIVO")
        
        root.addWidget(footer)
        QTimer.singleShot(100, self.panel_arq.focus_fisico)

    def finalizar_turno_accion(self):
        self.modo = "turno"
        self._finalizar()

    def _finalizar(self):
        # Confirmación amigable de seguridad
        msg = "¿Está seguro de que desea registrar el CIERRE DE CAJA de su turno?\\n\\nEsta acción cerrará el turno actual e imprimirá el reporte físico."
            
        res = QMessageBox.question(self, "Confirmar Cierre", msg, QMessageBox.Yes | QMessageBox.No)
        if res != QMessageBox.Yes:
            return
            
        try:
            fisico, dif = self.panel_arq.get_fisico_y_dif()
            from src.config import config
            c_id = self.datos.get("caja_id", config.get("caja_id", 1))
            
            exito = CierreController.finalizar_cierre(
                username=self.user,
                caja_id=c_id,
                fisico=fisico,
                dif=dif,
                esperado=self.datos['esperado'],
                apertura_fecha=getattr(self, "_apertura_fecha", None),
                t_total=self.datos["t_total"],
                modo=self.modo
            )
            
            if exito:
                QMessageBox.information(self, "CIERRE EXITOSO", f"Cierre de Turno registrado correctamente.\\nDiferencia: $ {dif:,.2f}")
                self.accept()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def mostrar_corte_diario(self):
        # Vista simplificada para Admin
        self.main_container.hide()
        dlg = CorteDiarioDialog(self)
        dlg.mostrar()
        self.main_container.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.panel_arq.has_focus_fisico():
                self.finalizar_turno_accion()
        else: super().keyPressEvent(event)