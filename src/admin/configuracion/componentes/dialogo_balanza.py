from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoBalanza(QDialog):
    """Configuración avanzada de balanzas (Systel, Kretz, Moretti, etc.)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Configuración de Báscula / Balanza")
        self.setFixedSize(540, 750)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(15)

        # --- TÍTULO ---
        header = QLabel("⚖️ Configuración de Balanza")
        header.setStyleSheet("font-size: 20px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Ajusta cómo el sistema lee tus etiquetas EAN-13.")
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_desc)

        # --- CARD DE CONFIGURACIÓN ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {  border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold;  font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 10px; font-weight: normal;  font-size: 13px;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 20, 20, 20)
        card_lay.setSpacing(12)

        # Estado
        card_lay.addWidget(QLabel("ESTADO DEL SISTEMA:"))
        self.chk_enabled = QComboBox()
        self.chk_enabled.addItems(["Desactivada", "Activada (Modo Inteligente)"])
        self.chk_enabled.setCurrentIndex(1 if config.get("balanza_habilitada", True) else 0)
        card_lay.addWidget(self.chk_enabled)

        # Modo de Interpretación
        card_lay.addWidget(QLabel("INTERPRETAR VALOR COMO:"))
        self.cmb_modo = QComboBox()
        self.cmb_modo.addItems(["Peso Neto (Kg)", "Importe Total ($)"])
        self.cmb_modo.setCurrentText(config.get("balanza_modo", "Peso Neto (Kg)"))
        card_lay.addWidget(self.cmb_modo)

        # Grid de Parámetros EAN-13
        grid = QGridLayout()
        grid.setSpacing(12)

        # Prefijo
        grid.addWidget(QLabel("PREFIJO BASE (20):"), 0, 0)
        self.txt_pref = QLineEdit(str(config.get("balanza_prefijo", "20")))
        grid.addWidget(self.txt_pref, 0, 1)

        # PLU (Donde empieza y cuántos dígitos)
        grid.addWidget(QLabel("PLU (Inicio / Largo):"), 1, 0)
        h_plu = QHBoxLayout()
        self.txt_plu_start = QLineEdit(str(config.get("balanza_plu_inicio", 3)))
        self.txt_plu_len = QLineEdit(str(config.get("balanza_plu_largo", 4)))
        h_plu.addWidget(self.txt_plu_start); h_plu.addWidget(self.txt_plu_len)
        grid.addLayout(h_plu, 1, 1)

        # Valor (Donde empieza y cuántos dígitos)
        grid.addWidget(QLabel("VALOR (Inicio / Largo):"), 2, 0)
        h_val = QHBoxLayout()
        self.txt_val_start = QLineEdit(str(config.get("balanza_val_inicio", 8)))
        self.txt_val_len = QLineEdit(str(config.get("balanza_val_largo", 5)))
        h_val.addWidget(self.txt_val_start); h_val.addWidget(self.txt_val_len)
        grid.addLayout(h_val, 2, 1)

        # Divisor
        grid.addWidget(QLabel("DIVISOR (Ej: 1000):"), 3, 0)
        self.txt_divisor = QLineEdit(str(config.get("balanza_divisor", 1000)))
        grid.addWidget(self.txt_divisor, 3, 1)

        card_lay.addLayout(grid)
        main_lay.addWidget(card)

        # --- SIMULADOR ---
        sim_card = QFrame()
        sim_card.setStyleSheet(" border: 1px solid #BFDBFE; border-radius: 12px;")
        sim_lay = QVBoxLayout(sim_card)
        sim_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_sim = QLabel("🧪 PROBADOR DE CÓDIGOS")
        lbl_sim.setStyleSheet(" font-weight: 900; border: none; font-size: 11px;")
        sim_lay.addWidget(lbl_sim)

        self.txt_test = QLineEdit()
        self.txt_test.setPlaceholderText("Pega un código EAN-13 aquí para probar...")
        self.txt_test.setStyleSheet("background: white; border: 1px solid #3B82F6; padding: 10px; font-family: 'Consolas';")
        self.txt_test.textChanged.connect(self.simular_prueba)
        sim_lay.addWidget(self.txt_test)

        self.lbl_res_test = QLabel("Resultado: —")
        self.lbl_res_test.setStyleSheet(" font-weight: bold; border: none;")
        sim_lay.addWidget(self.lbl_res_test)
        main_lay.addWidget(sim_card)

        # --- AYUDA ---
        btn_help = QPushButton("❓ Ver Formatos Comunes (Systel, Kretz, etc.)")
        btn_help.setStyleSheet(" font-weight: bold; border: none; background: transparent; font-size: 11px;")
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.clicked.connect(self._sugerir_formatos)
        main_lay.addWidget(btn_help)

        # --- BOTONES ---
        main_lay.addStretch()
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold;   border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px;")
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def simular_prueba(self):
        txt = self.txt_test.text().strip()
        if len(txt) != 13:
            self.lbl_res_test.setText("Esperando código de 13 dígitos...")
            return
        try:
            pref = self.txt_pref.text().strip()
            p_start = int(self.txt_plu_start.text()) - 1
            p_len = int(self.txt_plu_largo.text()) if hasattr(self, 'txt_plu_largo') else int(self.txt_plu_len.text())
            plu = txt[p_start : p_start + p_len]
            
            v_start = int(self.txt_val_start.text()) - 1
            v_len = int(self.txt_val_largo.text()) if hasattr(self, 'txt_val_largo') else int(self.txt_val_len.text())
            v_raw = txt[v_start : v_start + v_len]
            divisor = int(self.txt_divisor.text())
            
            valor = int(v_raw) / divisor
            modo = self.cmb_modo.currentText()
            simb = "$" if "Importe" in modo else "Kg"
            self.lbl_res_test.setText(f"✅ PLU: {plu} | {simb}: {valor:.3f}")
        except:
            self.lbl_res_test.setText("❌ Error en configuración.")

    def _sugerir_formatos(self):
        msg = ("<b>Formatos Comunes:</b><br><br>"
               "• <b>Estándar Eleventa / Systel (5-Dig):</b> Inicio PLU: 3, Largo: 5 | Inicio Valor: 8, Largo: 5 | Divisor: 1000<br>"
               "• <b>Systel Clásico (4-Dig):</b> Inicio PLU: 3, Largo: 4 | Inicio Valor: 8, Largo: 5 | Divisor: 1000<br>"
               "• <b>Moretti:</b> Inicio PLU: 2, Largo: 5 | Inicio Valor: 7, Largo: 5 | Divisor: 1000<br>"
               "• <b>Kretz (Precio):</b> Divisor: 100")
        QMessageBox.information(self, "Guía de Balanzas", msg)

    def _guardar(self):
        try:
            config.set("balanza_habilitada", self.chk_enabled.currentIndex() == 1)
            config.set("balanza_prefijo", self.txt_pref.text().strip())
            config.set("balanza_modo", self.cmb_modo.currentText())
            config.set("balanza_plu_inicio", int(self.txt_plu_start.text()))
            config.set("balanza_plu_largo", int(self.txt_plu_len.text()))
            config.set("balanza_val_inicio", int(self.txt_val_start.text()))
            config.set("balanza_val_largo", int(self.txt_val_len.text()))
            config.set("balanza_divisor", int(self.txt_divisor.text()))
            QMessageBox.information(self, "Éxito", "Configuración guardada.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Verifica los campos: {e}")





