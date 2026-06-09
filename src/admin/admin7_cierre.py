import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from datetime import datetime

try:
    from src.base_de_datos.database import db_manager
    from src.config import config
    from src.utils.theme_manager import theme_manager
except ImportError:
    from database import db_manager
    from config import config
    from utils.theme_manager import theme_manager

def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"

class Admin7Cierre(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent_main=None):
        super().__init__()
        self.parent_main = parent_main
        self.user = (config.current_user or {}).get("username", "Admin")
        self._setup_ui()
        self._load_data()
        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    def _setup_ui(self):
        self.setObjectName("CierreRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # TOP BAR
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(45)
        top_lay = QHBoxLayout(self.top_bar)
        top_lay.setContentsMargins(10, 0, 10, 0)

        self.btn_back = QPushButton("← Volver")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        top_lay.addWidget(self.btn_back)

        self.btn_corte_cajero = QPushButton("✂ Hacer corte de cajero")
        self.btn_corte_dia = QPushButton("✂ Hacer corte del día")
        top_lay.addWidget(self.btn_corte_cajero)
        top_lay.addWidget(self.btn_corte_dia)
        
        top_lay.addStretch()

        self.btn_imprimir = QPushButton("🖨️ Imprimir")
        self.btn_cerrar_turno = QPushButton("🔒 Cerrar turno...")
        top_lay.addWidget(self.btn_imprimir)
        top_lay.addWidget(self.btn_cerrar_turno)
        root.addWidget(self.top_bar)

        # SCROLL AREA
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("CierreScroll")
        
        container = QWidget()
        container.setObjectName("CierreContainer")
        self.main_lay = QVBoxLayout(container)
        self.main_lay.setContentsMargins(30, 20, 30, 30)

        # HEADER INFO
        self.lbl_header = QLabel(f"Corte de <b>{self.user}</b> iniciado el <u>{datetime.now().strftime('%d/%b/%Y')}</u>")
        self.lbl_header.setStyleSheet("font-size: 18px;")
        self.lbl_sub = QLabel(f"De {datetime.now().strftime('%d/%b/%Y %I:%M %p')} - (Turno Actual)")
        self.lbl_sub.setStyleSheet("font-size: 12px;")
        
        self.main_lay.addWidget(self.lbl_header)
        self.main_lay.addWidget(self.lbl_sub)
        self.main_lay.addSpacing(20)

        # Separator Line
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setStyleSheet("border-top: 1px dashed #CBD5E1;")
        self.main_lay.addWidget(self.line1)
        self.main_lay.addSpacing(20)

        # 2 COLUMNS
        cols_lay = QHBoxLayout()
        cols_lay.setSpacing(40)
        
        # LEFT COLUMN
        self.left_col = QVBoxLayout()
        
        # Ventas Totales
        h_ventas = QHBoxLayout()
        self.lbl_tit_vt = QLabel("💲 Ventas Totales")
        self.lbl_tit_vt.setStyleSheet("font-size: 16px;")
        self.lbl_val_vt = QLabel("$0.00")
        self.lbl_val_vt.setStyleSheet("font-size: 16px; font-weight: bold; color: #0EA5E9;")
        self.lbl_val_vt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h_ventas.addWidget(self.lbl_tit_vt)
        h_ventas.addWidget(self.lbl_val_vt)
        self.left_col.addLayout(h_ventas)
        self.left_col.addSpacing(15)

        # Dinero en Caja
        self.lbl_tit_dc = QLabel("🧮 Dinero en Caja")
        self.lbl_tit_dc.setStyleSheet("font-size: 16px;")
        self.left_col.addWidget(self.lbl_tit_dc)

        self.grid_caja = QGridLayout()
        self.grid_caja.setHorizontalSpacing(20)
        self.grid_caja.setVerticalSpacing(8)
        
        # We will populate these dynamically or statically
        self.lbl_fondo_val = QLabel("$0.00")
        self.lbl_ventas_efec_val = QLabel("+ $0.00")
        self.lbl_abonos_val = QLabel("+ $0.00")
        self.lbl_entradas_val = QLabel("+ $0.00")
        self.lbl_salidas_val = QLabel("- $0.00")
        self.lbl_devol_efec_val = QLabel("- $0.00")
        self.lbl_total_caja_val = QLabel("$0.00")

        self._add_row(self.grid_caja, 0, "Fondo de caja", self.lbl_fondo_val, color="#64748B")
        self._add_row(self.grid_caja, 1, "Ventas en Efectivo", self.lbl_ventas_efec_val, color="#10B981")
        self._add_row(self.grid_caja, 2, "Abonos en efectivo", self.lbl_abonos_val, color="#10B981")
        self._add_row(self.grid_caja, 3, "Entradas", self.lbl_entradas_val, color="#10B981")
        self._add_row(self.grid_caja, 4, "Salidas", self.lbl_salidas_val, color="#EF4444")
        self._add_row(self.grid_caja, 5, "Devoluciones en efectivo", self.lbl_devol_efec_val, color="#EF4444")
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("border-top: 1px solid #CBD5E1;")
        self.grid_caja.addWidget(line, 6, 0, 1, 2)
        
        self.lbl_total_caja_val.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_total_caja_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.grid_caja.addWidget(self.lbl_total_caja_val, 7, 1)

        self.left_col.addLayout(self.grid_caja)
        self.left_col.addSpacing(30)

        # Entradas de efectivo
        self.lbl_tit_ee = QLabel("⬇️ Entradas de efectivo")
        self.lbl_tit_ee.setStyleSheet("font-size: 16px;")
        self.left_col.addWidget(self.lbl_tit_ee)
        self.lbl_no_entradas = QLabel("- No hubo Entradas en Efectivo -")
        self.lbl_no_entradas.setAlignment(Qt.AlignCenter)
        self.lbl_no_entradas.setStyleSheet("background: #E0F2FE; color: #0369A1; border-radius: 4px; padding: 5px;")
        self.left_col.addWidget(self.lbl_no_entradas)

        self.left_col.addStretch()
        cols_lay.addLayout(self.left_col)


        # RIGHT COLUMN
        self.right_col = QVBoxLayout()

        # Ganancia
        h_ganancia = QHBoxLayout()
        self.lbl_tit_g = QLabel("📊 Ganancia")
        self.lbl_tit_g.setStyleSheet("font-size: 16px;")
        self.lbl_val_g = QLabel("$0.00")
        self.lbl_val_g.setStyleSheet("font-size: 16px; font-weight: bold; color: #0EA5E9;")
        self.lbl_val_g.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h_ganancia.addWidget(self.lbl_tit_g)
        h_ganancia.addWidget(self.lbl_val_g)
        self.right_col.addLayout(h_ganancia)
        self.right_col.addSpacing(15)

        # Ventas Desglose
        self.lbl_tit_v = QLabel("🛒 Ventas")
        self.lbl_tit_v.setStyleSheet("font-size: 16px;")
        self.right_col.addWidget(self.lbl_tit_v)

        self.grid_ventas = QGridLayout()
        self.grid_ventas.setHorizontalSpacing(20)
        self.grid_ventas.setVerticalSpacing(8)

        self.lbl_v_efec = QLabel("+ $0.00")
        self.lbl_v_tarj = QLabel("+ $0.00")
        self.lbl_v_cred = QLabel("+ $0.00")
        self.lbl_v_vales = QLabel("+ $0.00")
        self.lbl_v_trans = QLabel("+ $0.00")
        self.lbl_v_cheq = QLabel("+ $0.00")
        self.lbl_v_devol = QLabel("- $0.00")
        self.lbl_total_v = QLabel("$0.00")

        self._add_row(self.grid_ventas, 0, "En Efectivo", self.lbl_v_efec, color="#10B981")
        self._add_row(self.grid_ventas, 1, "Con Tarjeta de Crédito", self.lbl_v_tarj, color="#10B981")
        self._add_row(self.grid_ventas, 2, "A Crédito", self.lbl_v_cred, color="#10B981")
        self._add_row(self.grid_ventas, 3, "Con Vales de Despensa", self.lbl_v_vales, color="#10B981")
        self._add_row(self.grid_ventas, 4, "Con Transferencia", self.lbl_v_trans, color="#10B981")
        self._add_row(self.grid_ventas, 5, "Con Cheque", self.lbl_v_cheq, color="#10B981")
        self._add_row(self.grid_ventas, 6, "Devoluciones de Ventas", self.lbl_v_devol, color="#EF4444")

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("border-top: 1px solid #CBD5E1;")
        self.grid_ventas.addWidget(line2, 7, 0, 1, 2)

        self.lbl_total_v.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_total_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.grid_ventas.addWidget(self.lbl_total_v, 8, 1)

        self.right_col.addLayout(self.grid_ventas)
        self.right_col.addSpacing(30)

        # Ingresos de contado
        self.lbl_tit_ic = QLabel("💵 Ingresos de contado")
        self.lbl_tit_ic.setStyleSheet("font-size: 16px;")
        self.right_col.addWidget(self.lbl_tit_ic)
        self.lbl_no_ingresos = QLabel("- No hubo ingresos de contado -")
        self.lbl_no_ingresos.setAlignment(Qt.AlignCenter)
        self.lbl_no_ingresos.setStyleSheet("background: #E0F2FE; color: #0369A1; border-radius: 4px; padding: 5px;")
        self.right_col.addWidget(self.lbl_no_ingresos)

        self.right_col.addStretch()
        cols_lay.addLayout(self.right_col)

        self.main_lay.addLayout(cols_lay)

        scroll.setWidget(container)
        root.addWidget(scroll)

    def _add_row(self, layout, row, text, val_lbl, color="#64748B"):
        lbl = QLabel(text)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(lbl, row, 0)
        layout.addWidget(val_lbl, row, 1)

    def _apply_theme(self):
        bg_app = theme_manager.get_color("app_bg")
        nav_bg = theme_manager.get_color("nav_bg")
        nav_border = theme_manager.get_color("nav_border")
        text_primary = theme_manager.get_color("text_title")
        text_secondary = theme_manager.get_color("text_desc")
        btn_bg = theme_manager.get_color("btn_bg")
        btn_border = theme_manager.get_color("btn_border")
        btn_text = theme_manager.get_color("btn_text")

        # Eliminado self.setStyleSheet para no sobreescribir el global de theme_manager.apply_to_admin
        # Solo aplicaremos estilos específicos a los componentes.
        self.lbl_header.setStyleSheet(f"font-size: 18px; color: {theme_manager.get_color('nav_brand')}; background: transparent;")
        self.lbl_sub.setStyleSheet(f"font-size: 12px; color: {text_secondary}; background: transparent;")
        self.line1.setStyleSheet(f"border-top: 1px dashed {nav_border}; background: transparent;")

        self.top_bar.setStyleSheet(f"""
            QFrame {{ background: {nav_bg}; border-bottom: 1px solid {nav_border}; }}
        """)

        btn_style = f"""
            QPushButton {{
                background: {btn_bg}; color: {btn_text};
                border: 1px solid {btn_border}; border-radius: 4px;
                padding: 4px 12px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {theme_manager.get_color('btn_hover')}; }}
        """
        for btn in [self.btn_back, self.btn_corte_cajero, self.btn_corte_dia, self.btn_imprimir, self.btn_cerrar_turno]:
            btn.setStyleSheet(btn_style)

        # Labels headers ya se configuran arriba
        self.lbl_tit_vt.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")
        self.lbl_tit_dc.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")
        self.lbl_tit_ee.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")
        self.lbl_tit_g.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")
        self.lbl_tit_v.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")
        self.lbl_tit_ic.setStyleSheet(f"font-size: 16px; color: {theme_manager.get_color('nav_brand')};")

        # Specific colored backgrounds for empty states based on theme
        empty_bg = "#E0F2FE" if theme_manager.current_theme == "light" else "#0C4A6E"
        empty_text = "#0369A1" if theme_manager.current_theme == "light" else "#7DD3FC"
        empty_style = f"background: {empty_bg}; color: {empty_text}; border-radius: 4px; padding: 5px;"
        self.lbl_no_entradas.setStyleSheet(empty_style)
        self.lbl_no_ingresos.setStyleSheet(empty_style)

    def _load_data(self):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            # Fondo
            fondo = float(db_manager.execute_scalar(
                "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' ORDER BY id DESC LIMIT 1"
            ) or 0)
            
            # Ventas Efectivo
            res_efec = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND metodo_pago='Efectivo' AND date(fecha) = ?",
                (today_str,)
            ) or 0
            v_efectivo = float(res_efec)

            # Ventas Tarjeta
            res_tarj = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND metodo_pago LIKE '%%Tarjeta%%' AND date(fecha) = ?",
                (today_str,)
            ) or 0
            v_tarjeta = float(res_tarj)

            # Transferencia
            res_trans = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE estado='COMPLETADA' AND (metodo_pago='Transferencia' OR metodo_pago='Fiado') AND date(fecha) = ?",
                (today_str,)
            ) or 0
            v_trans = float(res_trans)

            v_totales = v_efectivo + v_tarjeta + v_trans
            v_caja_total = fondo + v_efectivo

            self.lbl_fondo_val.setText(fmt_moneda(fondo))
            self.lbl_ventas_efec_val.setText(f"+ {fmt_moneda(v_efectivo)}")
            self.lbl_total_caja_val.setText(fmt_moneda(v_caja_total))

            self.lbl_v_efec.setText(f"+ {fmt_moneda(v_efectivo)}")
            self.lbl_v_tarj.setText(f"+ {fmt_moneda(v_tarjeta)}")
            self.lbl_v_trans.setText(f"+ {fmt_moneda(v_trans)}")
            
            self.lbl_total_v.setText(fmt_moneda(v_totales))
            self.lbl_val_vt.setText(fmt_moneda(v_totales))

        except Exception as e:
            print(f"Error cargando datos de corte: {e}")
