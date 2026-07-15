import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QSizePolicy, QSpacerItem, QInputDialog, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

try:
    from src.config import config
    from src.utils.theme_manager import theme_manager
    from src.cerebro_global.cierre_caja_cerebro.motor_cierre import MotorCierre
except ImportError:
    from config import config
    from utils.theme_manager import theme_manager
    from cerebro_global.cierre_caja_cerebro.motor_cierre import MotorCierre

def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"

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
        self.modo_vista = "cajero"  # 'cajero' o 'dia'
        self._setup_ui()
        self._apply_theme()
        self._load_data()
        theme_manager.theme_changed.connect(self._apply_theme)
        # Retrasar levemente la aplicación del tema para que gane precedencia
        QTimer.singleShot(50, self._apply_theme)

    def _create_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15) if theme_manager.current_theme == "light" else QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        return shadow

    def _setup_ui(self):
        self.setObjectName("CierreGlobalRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── TOP BAR ───
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        top_lay = QHBoxLayout(self.top_bar)
        top_lay.setContentsMargins(20, 0, 20, 0)
        top_lay.setSpacing(12)

        self.btn_back = QPushButton("← Volver")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        top_lay.addWidget(self.btn_back)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setFixedWidth(120)
        self.date_picker.setStyleSheet("font-size: 14px; padding: 5px;")
        self.date_picker.dateChanged.connect(self._load_data)
        top_lay.addWidget(self.date_picker)

        # --- SELECTOR DE VISTA (Botones Profesionales) ---
        self.btn_corte_cajero = QPushButton("👤 Corte Cajero")
        self.btn_corte_cajero.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_cajero.clicked.connect(lambda: self._cambiar_modo("cajero"))
        top_lay.addWidget(self.btn_corte_cajero)

        self.btn_corte_admin = QPushButton("🏢 Corte Admin")
        self.btn_corte_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_admin.clicked.connect(lambda: self._cambiar_modo("dia"))
        top_lay.addWidget(self.btn_corte_admin)

        self.combo_caja = QComboBox()
        self.combo_caja.addItem("Todas las Cajas", None)
        for i in range(1, 11):
            self.combo_caja.addItem(f"Caja {i}", i)
        self.combo_caja.setStyleSheet("font-size: 14px; padding: 5px;")
        self.combo_caja.currentIndexChanged.connect(self._load_data)
        
        # Ocultar selector de caja y botón admin si no es admin/jefe O si estamos en la vista de Terminal (privacidad)
        if self.rol not in ["ADMIN", "JEFE"] or self.is_terminal:
            self.combo_caja.hide()
            self.btn_corte_admin.hide()
            
        top_lay.addWidget(self.combo_caja)
        
        top_lay.addStretch()

        self.btn_imprimir = QPushButton("🖨️ Imprimir")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.clicked.connect(self._imprimir_reporte)
        
        self.btn_cerrar_turno = QPushButton("🔒 Cerrar turno...")
        self.btn_cerrar_turno.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar_turno.clicked.connect(self._cerrar_turno)
        
        top_lay.addWidget(self.btn_imprimir)
        top_lay.addWidget(self.btn_cerrar_turno)
        root.addWidget(self.top_bar)

        # ─── SCROLL AREA ───
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("CierreScroll")
        
        container = QWidget()
        container.setObjectName("CierreContainer")
        self.main_lay = QVBoxLayout(container)
        self.main_lay.setContentsMargins(40, 30, 40, 40)
        self.main_lay.setSpacing(25)

        # ─── HEADER INFO ───
        header_lay = QVBoxLayout()
        header_lay.setSpacing(5)
        
        self.lbl_header = QLabel("Dashboard de Corte de Caja")
        self.lbl_header.setStyleSheet("font-size: 28px; font-weight: 900; font-family: 'Segoe UI', sans-serif;")
        
        self.lbl_sub = QLabel(f"👤 Operador: <b>{self.user.capitalize()}</b>  |  🕒 Turno actual")
        self.lbl_sub.setStyleSheet("font-size: 14px; font-family: 'Segoe UI', sans-serif;")
        
        header_lay.addWidget(self.lbl_header)
        header_lay.addWidget(self.lbl_sub)
        self.main_lay.addLayout(header_lay)

        # ─── HERO CARDS (3 BIG METRICS) ───
        hero_lay = QHBoxLayout()
        hero_lay.setSpacing(20)

        self.card_vt, self.lbl_val_vt = self._build_hero_card("💲 Ventas Totales", "$0.00", "#3B82F6", "#EFF6FF", "#1D4ED8")
        self.card_dc, self.lbl_total_caja_val = self._build_hero_card("🧮 Dinero en Caja", "$0.00", "#10B981", "#ECFDF5", "#047857")
        self.card_g, self.lbl_val_g = self._build_hero_card("📊 Ganancia Estimada", "$0.00", "#F59E0B", "#FFFBEB", "#B45309")

        hero_lay.addWidget(self.card_vt)
        hero_lay.addWidget(self.card_dc)
        hero_lay.addWidget(self.card_g)
        
        # Ocultar Ganancia Estimada si el rol no es JEFE
        if self.rol != "JEFE":
            self.card_g.hide()
            
        self.main_lay.addLayout(hero_lay)

        # ─── DETAILED CARDS ───
        cols_lay = QHBoxLayout()
        cols_lay.setSpacing(20)

        # LEFT COLUMN (Flujo de Efectivo)
        self.card_flujo = QFrame()
        self.card_flujo.setObjectName("DetailCard")
        self.card_flujo.setGraphicsEffect(self._create_shadow())
        flujo_lay = QVBoxLayout(self.card_flujo)
        flujo_lay.setContentsMargins(25, 25, 25, 25)
        flujo_lay.setSpacing(15)

        lbl_tit_flujo = QLabel("💵 Movimientos de Efectivo")
        lbl_tit_flujo.setStyleSheet("font-size: 18px; font-weight: bold;")
        flujo_lay.addWidget(lbl_tit_flujo)

        self.grid_caja = QGridLayout()
        self.grid_caja.setHorizontalSpacing(30)
        self.grid_caja.setVerticalSpacing(12)
        
        self.lbl_fondo_val = QLabel("$0.00")
        self.lbl_ventas_efec_val = QLabel("+ $0.00")
        self.lbl_abonos_val = QLabel("+ $0.00")
        self.lbl_entradas_val = QLabel("+ $0.00")
        self.lbl_salidas_val = QLabel("- $0.00")
        self.lbl_devol_efec_val = QLabel("- $0.00")

        self._add_row(self.grid_caja, 0, "Fondo de caja", self.lbl_fondo_val, neutral=True)
        self._add_row(self.grid_caja, 1, "Ventas en Efectivo", self.lbl_ventas_efec_val, positive=True)
        self._add_row(self.grid_caja, 2, "Abonos en efectivo", self.lbl_abonos_val, positive=True)
        self._add_row(self.grid_caja, 3, "Entradas", self.lbl_entradas_val, positive=True)
        self._add_row(self.grid_caja, 4, "Salidas", self.lbl_salidas_val, positive=False)
        self._add_row(self.grid_caja, 5, "Devoluciones en efectivo", self.lbl_devol_efec_val, positive=False)
        
        flujo_lay.addLayout(self.grid_caja)
        
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.Shape.HLine)
        flujo_lay.addWidget(self.line1)

        self.lbl_no_entradas = QLabel("ℹ️ No hubo otras entradas de efectivo")
        self.lbl_no_entradas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flujo_lay.addWidget(self.lbl_no_entradas)
        flujo_lay.addStretch()
        cols_lay.addWidget(self.card_flujo)

        # RIGHT COLUMN (Desglose Ventas)
        self.card_ventas = QFrame()
        self.card_ventas.setObjectName("DetailCard")
        self.card_ventas.setGraphicsEffect(self._create_shadow())
        ventas_lay = QVBoxLayout(self.card_ventas)
        ventas_lay.setContentsMargins(25, 25, 25, 25)
        ventas_lay.setSpacing(15)

        lbl_tit_ventas = QLabel("🛒 Desglose de Ventas")
        lbl_tit_ventas.setStyleSheet("font-size: 18px; font-weight: bold;")
        ventas_lay.addWidget(lbl_tit_ventas)

        self.grid_ventas = QGridLayout()
        self.grid_ventas.setHorizontalSpacing(30)
        self.grid_ventas.setVerticalSpacing(12)

        self.lbl_v_efec = QLabel("+ $0.00")
        self.lbl_v_tarj = QLabel("+ $0.00")
        self.lbl_v_cred = QLabel("+ $0.00")
        self.lbl_v_vales = QLabel("+ $0.00")
        self.lbl_v_trans = QLabel("+ $0.00")
        self.lbl_v_cheq = QLabel("+ $0.00")
        self.lbl_v_devol = QLabel("- $0.00")
        self.lbl_total_v = QLabel("$0.00")

        self._add_row(self.grid_ventas, 0, "En Efectivo", self.lbl_v_efec, positive=True)
        self._add_row(self.grid_ventas, 1, "Con Tarjeta de Crédito", self.lbl_v_tarj, positive=True)
        self._add_row(self.grid_ventas, 2, "A Crédito", self.lbl_v_cred, positive=True)
        self._add_row(self.grid_ventas, 3, "Con Vales de Despensa", self.lbl_v_vales, positive=True)
        self._add_row(self.grid_ventas, 4, "Con Transferencia", self.lbl_v_trans, positive=True)
        self._add_row(self.grid_ventas, 5, "Con Cheque", self.lbl_v_cheq, positive=True)
        self._add_row(self.grid_ventas, 6, "Devoluciones de Ventas", self.lbl_v_devol, positive=False)

        ventas_lay.addLayout(self.grid_ventas)

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.Shape.HLine)
        ventas_lay.addWidget(self.line2)
        
        # Total Row
        h_tot_v = QHBoxLayout()
        lbl_tv_t = QLabel("Total Calculado:")
        lbl_tv_t.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.lbl_total_v.setStyleSheet("font-weight: 900; font-size: 18px;")
        self.lbl_total_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h_tot_v.addWidget(lbl_tv_t)
        h_tot_v.addWidget(self.lbl_total_v)
        ventas_lay.addLayout(h_tot_v)

        ventas_lay.addStretch()
        cols_lay.addWidget(self.card_ventas)

        self.main_lay.addLayout(cols_lay)
        self.main_lay.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    def _build_hero_card(self, title, initial_val, accent_color, light_bg, dark_text):
        card = QFrame()
        card.setObjectName("HeroCard")
        card.setGraphicsEffect(self._create_shadow())
        
        lay = QVBoxLayout(card)
        lay.setContentsMargins(25, 25, 25, 25)
        lay.setSpacing(10)
        
        lbl_tit = QLabel(title)
        lbl_tit.setStyleSheet("font-size: 15px; font-weight: 600; opacity: 0.8;")
        
        lbl_val = QLabel(initial_val)
        lbl_val.setStyleSheet(f"font-size: 34px; font-weight: 900; color: {accent_color}; letter-spacing: -1px;")
        
        lay.addWidget(lbl_tit)
        lay.addWidget(lbl_val)
        lay.addStretch()
        
        card.setProperty("accent", accent_color)
        
        return card, lbl_val

    def _add_row(self, layout, row, text, val_lbl, positive=True, neutral=False):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px;")
        
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_lbl.setStyleSheet("font-size: 14px; font-weight: 600;")
        
        if neutral:
            val_lbl.setProperty("color_type", "neutral")
        elif positive:
            val_lbl.setProperty("color_type", "positive")
        else:
            val_lbl.setProperty("color_type", "negative")
            
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
        
        is_dark = theme_manager.current_theme == "dark"
        card_bg = "#111827" if is_dark else "#FFFFFF"
        card_border = "#1F2937" if is_dark else "#E5E7EB"
        
        # Colores semánticos
        color_pos = "#34D399" if is_dark else "#059669"
        color_neg = "#F87171" if is_dark else "#DC2626"
        color_neu = "#94A3B8" if is_dark else "#475569"

        self.lbl_header.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {text_primary}; background: transparent;")
        self.lbl_sub.setStyleSheet(f"font-size: 14px; color: {text_secondary}; background: transparent;")
        
        self.line1.setStyleSheet(f"border-top: 1px dashed {nav_border}; background: transparent; margin: 10px 0px;")
        self.line2.setStyleSheet(f"border-top: 1px dashed {nav_border}; background: transparent; margin: 10px 0px;")

        self.top_bar.setStyleSheet(f"QFrame {{ background: {nav_bg}; border-bottom: 1px solid {nav_border}; }}")

        btn_style = f"""
            QPushButton {{
                background: {btn_bg}; color: {btn_text};
                border: 1px solid {btn_border}; border-radius: 8px;
                padding: 8px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme_manager.get_color('btn_hover')}; }}
        """
        for btn in [self.btn_back, self.btn_corte_cajero, self.btn_corte_admin, self.btn_imprimir, self.btn_cerrar_turno]:
            btn.setStyleSheet(btn_style)
            
        # Hero Cards Style
        hero_style = f"""
            QFrame#HeroCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 16px;
            }}
        """
        self.card_vt.setStyleSheet(hero_style)
        self.card_dc.setStyleSheet(hero_style)
        self.card_g.setStyleSheet(hero_style)

        # Detail Cards Style
        detail_style = f"""
            QFrame#DetailCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 16px;
            }}
        """
        self.card_flujo.setStyleSheet(detail_style)
        self.card_ventas.setStyleSheet(detail_style)
        
        # Info Badge
        info_bg = "#1E3A8A" if is_dark else "#DBEAFE"
        info_txt = "#BFDBFE" if is_dark else "#1D4ED8"
        self.lbl_no_entradas.setStyleSheet(f"background: {info_bg}; color: {info_txt}; border-radius: 6px; padding: 10px; font-weight: 500;")
        
        # Re-aplicar colores semánticos a las etiquetas de la grilla
        for lbl in self.findChildren(QLabel):
            c_type = lbl.property("color_type")
            if c_type == "positive":
                lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {color_pos}; background: transparent;")
            elif c_type == "negative":
                lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {color_neg}; background: transparent;")
            elif c_type == "neutral":
                lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {color_neu}; background: transparent;")
            elif lbl.objectName() == "":
                pass

    def _cambiar_modo(self, modo):
        self.modo_vista = modo
        self._load_data()

    def _load_data(self):
        try:
            fecha_str = self.date_picker.date().toString("yyyy-MM-dd")
            
            # Por defecto (modo_vista = 'dia') vemos global. Si el admin usa el combo, filtramos por esa caja.
            caja_id_filter = None
            cajero_filter = None
            modo_text = "Todos los cajeros"
            
            if self.modo_vista == "cajero":
                cajero_filter = self.user
                caja_id_filter = config.get("caja_id", 1)
                modo_text = f"Turno de {self.user.capitalize()}"
            else:
                # Si es ADMIN y eligió una caja específica
                caja_sel = self.combo_caja.currentData()
                if caja_sel is not None:
                    caja_id_filter = caja_sel
                    modo_text = f"Solo {self.combo_caja.currentText()}"
                
            fecha_display = self.date_picker.date().toString("dd MMM yyyy")
            self.lbl_sub.setText(f"👤 Operador: <b>{self.user.capitalize()}</b>  |  📅 Fecha: <b>{fecha_display}</b>  |  🕒 Modo: {modo_text}")
            
            datos = MotorCierre.obtener_datos_cierre_diario(fecha_str=fecha_str, cajero=cajero_filter, caja_id=caja_id_filter)
            
            fondo = datos["fondo"]
            v_efectivo = datos["v_efectivo"]
            v_tarjeta = datos["v_tarjeta"]
            v_trans = datos["v_trans"]
            v_totales = datos["v_totales"]
            v_caja_total = datos["v_caja_total"]
            ganancia_estimada = datos["ganancia_estimada"]

            self.lbl_fondo_val.setText(fmt_moneda(fondo))
            self.lbl_ventas_efec_val.setText(f"+ {fmt_moneda(v_efectivo)}")
            self.lbl_total_caja_val.setText(fmt_moneda(v_caja_total))

            self.lbl_v_efec.setText(f"+ {fmt_moneda(v_efectivo)}")
            self.lbl_v_tarj.setText(f"+ {fmt_moneda(v_tarjeta)}")
            self.lbl_v_trans.setText(f"+ {fmt_moneda(v_trans)}")
            
            self.lbl_total_v.setText(fmt_moneda(v_totales))
            self.lbl_val_vt.setText(fmt_moneda(v_totales))
            
            self.lbl_val_g.setText(fmt_moneda(ganancia_estimada))

        except Exception as e:
            print(f"Error cargando datos de corte: {e}")

    def _get_efectivo_esperado(self):
        try:
            val_str = self.lbl_total_caja_val.text().replace("$", "").replace(".", "").replace(",", ".")
            return float(val_str)
        except:
            return 0.0



    def _realizar_corte(self, modo="turno"):
        esperado = self._get_efectivo_esperado()
        
        fisico, ok = QInputDialog.getDouble(
            self, 
            "Cuadre Físico", 
            f"Efectivo esperado en caja: ${esperado:,.2f}\\n\\nIngresa el dinero en efectivo real (físico):",
            value=esperado,
            min=0.0,
            max=9999999.0,
            decimals=2
        )
        
        if not ok:
            return

        dif = fisico - esperado
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Resumen de Corte")
        
        if abs(dif) < 0.01:
            msg.setText("✅ ¡El corte de caja cuadra perfectamente!")
        elif dif > 0:
            msg.setText(f"⚠️ Sobrante en caja de: ${dif:,.2f}")
        else:
            msg.setText(f"❌ Faltante en caja de: ${abs(dif):,.2f}")
            
        msg.exec()

    def _imprimir_reporte(self):
        try:
            from src.hardware.printer import printer_manager
            
            def _parse_val(txt):
                try:
                    return float(txt.replace('$', '').replace(' ', '').replace(',', '').replace('+', '').replace('-', ''))
                except:
                    return 0.0

            fondo = _parse_val(self.lbl_fondo_val.text())
            efec = _parse_val(self.lbl_ventas_efec_val.text())
            tarj = _parse_val(self.lbl_v_tarj.text())
            tot = _parse_val(self.lbl_val_vt.text())
            esp = _parse_val(self.lbl_total_caja_val.text())
            
            datos_z = {
                'fondo': fondo,
                't_efec': efec,
                't_tarj': tarj,
                't_tot': tot,
                'esperado': esp,
                'modo': 'turno' if self.modo_vista == 'cajero' else 'global',
                'd_tarj': tarj,
                'd_tot': tot
            }
            
            # Para el reporte previo pasamos el esperado como físico para que la dif sea 0.
            printer_manager.imprimir_ticket_z(self.user, esp, 0.0, datos_z)
            
            QMessageBox.information(self, "Impresión", "Reporte enviado a la impresora.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error de impresión: {e}")

    def _cerrar_turno(self):
        reply = QMessageBox.question(self, "Cerrar Turno", "¿Estás seguro que deseas cerrar el turno actual?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Turno Cerrado", "El turno ha sido cerrado exitosamente.")
            self.turno_cerrado.emit()
