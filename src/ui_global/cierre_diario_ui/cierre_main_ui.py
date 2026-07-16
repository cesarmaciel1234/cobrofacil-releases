import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QDateEdit, QComboBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate

try:
    from src.config import config
    from src.utils.theme_manager import theme_manager
    from src.cerebro_global.cierre_caja_cerebro.motor_cierre import MotorCierre
    from src.ui_global.cierre_diario_ui.componentes.metric_card import MetricCard
    from src.ui_global.cierre_diario_ui.componentes.panel_arqueo import PanelArqueo
except ImportError:
    from config import config
    from utils.theme_manager import theme_manager
    from cerebro_global.cierre_caja_cerebro.motor_cierre import MotorCierre
    from src.ui_global.cierre_diario_ui.componentes.metric_card import MetricCard
    from src.ui_global.cierre_diario_ui.componentes.panel_arqueo import PanelArqueo

def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"

class ClickableMetricCard(MetricCard):
    clicked = pyqtSignal()
    
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(titulo, icon, color, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self.styleSheet() + """
            QFrame#MetricCard:hover {
                background: #F1F5F9;
                border: 1px solid #94A3B8;
            }
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class DetallesDialog(QDialog):
    def __init__(self, titulo, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(450, 400)
        self.setStyleSheet("QDialog { background: white; }")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        lay.setSpacing(15)
        
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B;")
        lay.addWidget(lbl_tit)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(15)
        
        row = 0
        total = 0.0
        for desc, valor, is_negative in items:
            lbl_d = QLabel(desc)
            lbl_d.setStyleSheet("font-size: 15px; color: #475569; font-weight: bold;")
            
            val_fmt = f"{'-' if is_negative else '+'}{fmt_moneda(abs(valor))}"
            lbl_v = QLabel(val_fmt)
            if is_negative:
                lbl_v.setStyleSheet("font-size: 15px; font-weight: bold; color: #EF4444;")
                total -= abs(valor)
            else:
                lbl_v.setStyleSheet("font-size: 15px; font-weight: bold; color: #10B981;")
                total += abs(valor)
                
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl_d, row, 0)
            grid.addWidget(lbl_v, row, 1)
            row += 1
            
        lay.addLayout(grid)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #E2E8F0; margin-top: 10px; margin-bottom: 10px;")
        lay.addWidget(line)
        
        h_tot = QHBoxLayout()
        lbl_t = QLabel("TOTAL CALCULADO:")
        lbl_t.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A;")
        lbl_tv = QLabel(fmt_moneda(total))
        lbl_tv.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A;")
        lbl_tv.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        h_tot.addWidget(lbl_t)
        h_tot.addWidget(lbl_tv)
        lay.addLayout(h_tot)
        
        lay.addStretch()
        
        btn_cerrar = QPushButton("Cerrar Detalles")
        btn_cerrar.setFixedHeight(45)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #475569; font-weight: bold; font-size: 15px; border-radius: 8px; border: 1px solid #CBD5E1;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        lay.addWidget(btn_cerrar)

class CierreGlobalUI(QWidget):
    request_dashboard = pyqtSignal()
    turno_cerrado = pyqtSignal()

    def __init__(self, parent_main=None, is_terminal=False):
        super().__init__(parent_main)
        self.is_terminal = is_terminal
        self.parent_main = parent_main
        current = config.current_user or {}
        self.user = current.get("username", "Admin")
        self.rol = current.get("rol", "ADMIN").upper()
        self.modo_vista = "cajero"
        self.datos_actuales = {}
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setObjectName("CierreGlobalRoot")
        self.setStyleSheet("QWidget#CierreGlobalRoot { background: #F8FAFC; }") # Claro/Blanco
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── HEADER ESTILO PASO 7 CON CONTROLES DE DASHBOARD ───
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background: #1E3A8A;") # Azul oscuro
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(30, 0, 30, 0)
        h_lay.setSpacing(15)
        
        self.btn_back = QPushButton("← Volver")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("color: white; background: transparent; border: 1px solid white; border-radius: 8px; padding: 5px 15px; font-weight: bold;")
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        h_lay.addWidget(self.btn_back)
        
        lbl_tit = QLabel("💎 CAJAFACIL PRO - CONTROL DE CIERRE")
        lbl_tit.setStyleSheet("color: white; font-size: 20px; font-weight: 900;")
        h_lay.addWidget(lbl_tit)
        
        h_lay.addStretch()
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setFixedWidth(130)
        self.date_picker.setStyleSheet("font-size: 14px; padding: 5px; background: white; color: black; border-radius: 5px;")
        self.date_picker.dateChanged.connect(self._load_data)
        h_lay.addWidget(self.date_picker)

        self.btn_corte_cajero = QPushButton("👤 Corte Cajero")
        self.btn_corte_cajero.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_cajero.setStyleSheet("background: #3B82F6; color: white; border: none; border-radius: 5px; padding: 8px 15px; font-weight: bold;")
        self.btn_corte_cajero.clicked.connect(lambda: self._cambiar_modo("cajero"))
        h_lay.addWidget(self.btn_corte_cajero)

        self.btn_corte_admin = QPushButton("🏢 Corte Admin")
        self.btn_corte_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_admin.setStyleSheet("background: #10B981; color: white; border: none; border-radius: 5px; padding: 8px 15px; font-weight: bold;")
        self.btn_corte_admin.clicked.connect(lambda: self._cambiar_modo("dia"))
        h_lay.addWidget(self.btn_corte_admin)

        self.combo_caja = QComboBox()
        self.combo_caja.addItem("Todas las Cajas", None)
        for i in range(1, 11):
            self.combo_caja.addItem(f"Caja {i}", i)
        self.combo_caja.setStyleSheet("font-size: 14px; padding: 5px; background: white; color: black; border-radius: 5px;")
        self.combo_caja.currentIndexChanged.connect(self._load_data)
        
        if self.rol not in ["ADMIN", "JEFE"] or self.is_terminal:
            self.combo_caja.hide()
            self.btn_corte_admin.hide()
            
        h_lay.addWidget(self.combo_caja)
        
        self.btn_imprimir = QPushButton("🖨️")
        self.btn_imprimir.setToolTip("Imprimir Reporte")
        self.btn_imprimir.setStyleSheet("background: white; color: #1E3A8A; border: none; border-radius: 5px; padding: 8px 12px; font-size: 16px;")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.clicked.connect(self._imprimir_reporte)
        h_lay.addWidget(self.btn_imprimir)
        
        root.addWidget(header)

        # ─── MAIN BODY ───
        body = QHBoxLayout()
        body.setContentsMargins(40, 40, 40, 40)
        body.setSpacing(40)
        
        # Izquierda: Métricas
        v_met = QVBoxLayout()
        v_met.setSpacing(20)
        
        self.card_efec = ClickableMetricCard("Ventas Efectivo", "💰", "#10B981")
        self.card_efec.setToolTip("Click para ver detalles")
        self.card_efec.clicked.connect(lambda: self._mostrar_detalles("Ventas Efectivo", [
            ("Ventas Directas en Efectivo", self.datos_actuales.get("v_efectivo", 0), False),
            ("Abonos en Efectivo", self.datos_actuales.get("abonos_efectivo", 0), False),
            ("Devoluciones Efectivo", self.datos_actuales.get("devoluciones_efectivo", 0), True)
        ]))
        
        self.card_tarj = ClickableMetricCard("Ventas Digital", "💳", "#3B82F6")
        self.card_tarj.setToolTip("Click para ver detalles")
        self.card_tarj.clicked.connect(lambda: self._mostrar_detalles("Ventas Digital (Desglose)", [
            ("Tarjetas de Crédito/Débito", self.datos_actuales.get("v_tarjeta", 0), False),
            ("Transferencias / QR", self.datos_actuales.get("v_trans", 0), False),
            ("Vales de Despensa", self.datos_actuales.get("v_vales", 0), False),
            ("Cheques", self.datos_actuales.get("v_cheque", 0), False)
        ]))
        
        self.card_fiado = ClickableMetricCard("Ventas a Fiado", "👥", "#F59E0B")
        self.card_fiado.setToolTip("Click para ver detalles")
        self.card_fiado.clicked.connect(lambda: self._mostrar_detalles("Ventas a Crédito (Fiado)", [
            ("Crédito Otorgado (A cobrar)", self.datos_actuales.get("v_credito", 0), False)
        ]))
        
        self.card_fondo = ClickableMetricCard("Fondo Apertura", "🏁", "#6366F1")
        self.card_fondo.setToolTip("Dinero inicial en caja")
        
        self.card_movs = ClickableMetricCard("Movimientos Extra", "↔️", "#8B5CF6")
        self.card_movs.setToolTip("Click para ver entradas y salidas")
        self.card_movs.clicked.connect(lambda: self._mostrar_detalles("Entradas y Salidas de Caja", [
            ("Entradas Manuales", self.datos_actuales.get("entradas_efectivo", 0), False),
            ("Salidas Manuales", self.datos_actuales.get("salidas_efectivo", 0), True)
        ]))
        
        self.card_totales = ClickableMetricCard("Ganancia Estimada", "📈", "#14B8A6")
        self.card_totales.setToolTip("Click para ver resumen neto")
        self.card_totales.clicked.connect(lambda: self._mostrar_detalles("Resumen del Turno", [
            ("Ventas Totales Brutas", self.datos_actuales.get("v_totales", 0), False),
            ("Ganancia Estimada (Neto)", self.datos_actuales.get("ganancia_estimada", 0), False)
        ]))
        
        cards = [self.card_efec, self.card_tarj, self.card_fiado, self.card_fondo, self.card_movs]
        if self.rol == "JEFE":
            cards.append(self.card_totales)
        else:
            self.card_totales.hide()
            
        for c in cards: 
            v_met.addWidget(c)
            
        body.addLayout(v_met, 4)
        
        # Derecha: Panel de Arqueo
        v_arq = QVBoxLayout()
        v_arq.setSpacing(20)
        
        self.panel_arq = PanelArqueo(self)
        self.panel_arq.setStyleSheet("""
            QFrame#PanelArq {
                background: white; border: 1px solid #E2E8F0; border-radius: 16px;
            }
            QLabel#PanelArqTitEsp { font-weight: 900; font-size: 20px; color: #475569; }
            QLabel#PanelArqValEsp { font-weight: 900; font-size: 55px; color: #3B82F6; background: #EFF6FF; border-radius: 12px; padding: 10px; margin: 10px 0; }
            QLabel#PanelArqTitFis { font-weight: 900; font-size: 16px; color: #475569; margin-top: 15px; }
            QLineEdit#PanelArqValFis { font-weight: 900; font-size: 45px; color: #1E40AF; border: 2px solid #60A5FA; border-radius: 12px; padding: 10px; }
            QLineEdit#PanelArqValFis:focus { border: 3px solid #2563EB; }
            
            QFrame#FrameDif { border: 2px solid #E2E8F0; border-radius: 12px; margin-top: 15px; }
            QFrame#FrameDif[estado="sobrante"] { border-color: #10B981; background: #ECFDF5; }
            QFrame#FrameDif[estado="faltante"] { border-color: #EF4444; background: #FEF2F2; }
            QFrame#FrameDif[estado="sos"] { border-color: #B91C1C; background: #FCA5A5; }
            
            QLabel#FrameDifTit { font-weight: 900; font-size: 20px; color: #334155; }
            QLabel#FrameDifVal { font-weight: 900; font-size: 26px; }
            QFrame#FrameDif[estado="sobrante"] QLabel#FrameDifVal { color: #047857; }
            QFrame#FrameDif[estado="faltante"] QLabel#FrameDifVal { color: #B91C1C; }
            QFrame#FrameDif[estado="sos"] QLabel#FrameDifVal { color: white; }
        """)
        
        v_arq.addWidget(self.panel_arq)
        body.addLayout(v_arq, 6)
        
        root.addLayout(body)

        # ─── FOOTER ───
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("background: #1E3A8A;")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(30, 0, 30, 0)
        
        self.lbl_modo_activo = QLabel("")
        self.lbl_modo_activo.setStyleSheet("color: white; font-size: 16px;")
        f_lay.addWidget(self.lbl_modo_activo)
        
        f_lay.addStretch()
        
        self.btn_cierre = QPushButton("🏁 FINALIZAR CIERRE DE TURNO")
        self.btn_cierre.setFixedSize(320, 55)
        self.btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cierre.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; font-weight: 900; font-size: 17px;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_cierre.clicked.connect(lambda: self._realizar_corte("turno"))
        f_lay.addWidget(self.btn_cierre)
        
        root.addWidget(footer)
        
        QTimer.singleShot(100, self.panel_arq.focus_fisico)

    def _mostrar_detalles(self, titulo, items):
        dlg = DetallesDialog(titulo, items, self)
        dlg.exec()

    def _cambiar_modo(self, modo):
        self.modo_vista = modo
        self._load_data()

    def _load_data(self):
        try:
            fecha_str = self.date_picker.date().toString("yyyy-MM-dd")
            caja_id_filter = None
            cajero_filter = None
            modo_text = "Todos los cajeros"
            
            if self.modo_vista == "cajero":
                cajero_filter = self.user
                caja_id_filter = config.get("caja_id", 1)
                modo_text = f"Turno de {self.user.capitalize()}"
            else:
                caja_sel = self.combo_caja.currentData()
                if caja_sel is not None:
                    caja_id_filter = caja_sel
                    modo_text = f"Solo {self.combo_caja.currentText()}"
                
            fecha_display = self.date_picker.date().toString("dd MMM yyyy")
            self.lbl_modo_activo.setText(f"Mostrando: <b>{modo_text}</b> | {fecha_display}")
            
            datos = MotorCierre.obtener_datos_cierre_diario(fecha_str=fecha_str, cajero=cajero_filter, caja_id=caja_id_filter)
            self.datos_actuales = datos
            
            # Actualizar tarjetas
            self.card_efec.revelar(datos.get("v_efectivo", 0))
            v_digital = datos.get("v_tarjeta", 0) + datos.get("v_trans", 0) + datos.get("v_vales", 0) + datos.get("v_cheque", 0)
            self.card_tarj.revelar(v_digital)
            self.card_fiado.revelar(datos.get("v_credito", 0))
            self.card_fondo.revelar(datos.get("fondo", 0))
            
            movs = datos.get("entradas_efectivo", 0) - datos.get("salidas_efectivo", 0)
            self.card_movs.revelar(movs)
            
            self.card_totales.revelar(datos.get("ganancia_estimada", 0))

            # Actualizar panel de arqueo
            self.panel_arq.set_esperado(datos.get("v_caja_total", 0))

        except Exception as e:
            print(f"Error cargando datos de corte: {e}")

    def _imprimir_reporte(self):
        try:
            QMessageBox.information(self, "Imprimir", "Generando reporte de cierre...")
        except Exception as e:
            print(e)

    def _realizar_corte(self, modo="turno"):
        esperado = self.panel_arq.esperado
        fisico, dif = self.panel_arq.get_fisico_y_dif()
        
        msg = f"¿Está seguro de cerrar el {modo} con los siguientes datos?\n\nEsperado: ${esperado:,.2f}\nFísico: ${fisico:,.2f}\nDiferencia: ${dif:,.2f}"
        res = QMessageBox.question(self, "Confirmar Cierre", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            try:
                exito = MotorCierre.cerrar_caja(
                    username=self.user,
                    caja_id=config.get("caja_id", 1),
                    fisico=fisico,
                    dif=dif,
                    esperado=esperado,
                    t_total=self.datos_actuales.get("v_totales", 0.0),
                    modo=modo
                )
                if exito:
                    QMessageBox.information(self, "Éxito", f"Cierre de {modo} registrado correctamente.")
                    self.turno_cerrado.emit()
                    self.request_dashboard.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
