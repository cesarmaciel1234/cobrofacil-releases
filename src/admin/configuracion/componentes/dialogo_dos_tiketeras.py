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


class DialogoDosTiketeras(QDialog):
    """Asigna una tiketera a cada cajero. Al desbloquear, se usa la del cajero activo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tiketeras por Cajero")
        self.setFixedSize(500, 520)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 22)
        layout.setSpacing(14)

        lbl_title = QLabel("🖨️  TIKETERA POR CAJERO")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel("Asigná una tiketera y cajón a cada operador.\nEl sistema usa automáticamente la del que desbloquó la terminal.")
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        layout.addSpacing(6)

        # CAJERO (principal)
        box1 = QFrame()
        box1.setStyleSheet("QFrame {  border: 2px solid #1E3A8A; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b1 = QVBoxLayout(box1); b1.setContentsMargins(16, 12, 16, 12); b1.setSpacing(6)
        b1.addWidget(QLabel("🔵  [1]  CAJERO — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; "))
        
        row1 = QHBoxLayout()
        self.cmb_p1 = QComboBox()
        self.cmb_p1.setStyleSheet("padding: 7px; border: 1px solid #93C5FD; border-radius: 6px; font-size: 13px; background: white;")
        row1.addWidget(QLabel("🖨️ Impresora:"), 0)
        row1.addWidget(self.cmb_p1, 1)
        
        btn_test1 = QPushButton("📄 Test P1")
        btn_test1.setCursor(Qt.PointingHandCursor)
        btn_test1.setStyleSheet(" background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test1.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p1.currentText()))
        row1.addWidget(btn_test1)
        b1.addLayout(row1)

        row1_com = QHBoxLayout()
        self.cmb_serial_port_1 = QComboBox()
        self.cmb_serial_port_1.setStyleSheet("padding: 7px; border: 1px solid #93C5FD; border-radius: 6px; font-size: 13px; background: white;")
        row1_com.addWidget(QLabel("🔌 Sensor COM (Cajón):"), 0)
        row1_com.addWidget(self.cmb_serial_port_1, 1)
        b1.addLayout(row1_com)
        
        layout.addWidget(box1)

        # AUXILIAR (secundario)
        box2 = QFrame()
        box2.setStyleSheet("QFrame {  border: 2px solid #059669; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        b2 = QVBoxLayout(box2); b2.setContentsMargins(16, 12, 16, 12); b2.setSpacing(6)
        b2.addWidget(QLabel("🟢  [2]  AUXILIAR — Tiketera / Cajón:", styleSheet="font-size: 13px; font-weight: 900; "))
        
        row2 = QHBoxLayout()
        self.cmb_p2 = QComboBox()
        self.cmb_p2.setStyleSheet("padding: 7px; border: 1px solid #6EE7B7; border-radius: 6px; font-size: 13px; background: white;")
        row2.addWidget(QLabel("🖨️ Impresora:"), 0)
        row2.addWidget(self.cmb_p2, 1)
        
        btn_test2 = QPushButton("📄 Test P2")
        btn_test2.setCursor(Qt.PointingHandCursor)
        btn_test2.setStyleSheet(" background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; padding: 7px 15px;")
        btn_test2.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p2.currentText()))
        row2.addWidget(btn_test2)
        b2.addLayout(row2)

        row2_com = QHBoxLayout()
        self.cmb_serial_port_2 = QComboBox()
        self.cmb_serial_port_2.setStyleSheet("padding: 7px; border: 1px solid #6EE7B7; border-radius: 6px; font-size: 13px; background: white;")
        row2_com.addWidget(QLabel("🔌 Sensor COM (Cajón):"), 0)
        row2_com.addWidget(self.cmb_serial_port_2, 1)
        b2.addLayout(row2_com)
        
        layout.addWidget(box2)

        # Botón Recargar (Movido arriba o abajo, lo pondremos junto al stretch)
        btn_ref = QPushButton("🔄 Actualizar Puertos e Impresoras")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.setStyleSheet("  padding: 8px; border-radius: 6px; font-weight: bold;")
        btn_ref.clicked.connect(self._load_printers_and_ports)
        layout.addWidget(btn_ref)

        self._load_printers_and_ports()
        layout.addStretch()

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("  padding: 10px 22px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾  Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px 22px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self._guardar)
        h_btns.addWidget(btn_cancel); h_btns.addStretch(); h_btns.addWidget(btn_save)
        layout.addLayout(h_btns)

    def print_test_ticket_generic(self, printer_name):
        if not printer_name or printer_name == "(Sin impresora)":
            QMessageBox.warning(self, "Error", "No hay impresora seleccionada para probar.")
            return
        
        try:
            import datetime
            from src.hardware.printer import PosPrinter
            test_printer = PosPrinter()
            test_printer.printer_name = printer_name
            
            # Formatear un ticket simple de prueba
            data = bytearray()
            data.extend(b"\x1B\x40") # Reset
            data.extend(b"\x1B\x61\x01") # Centro
            data.extend(f"CAJAFACIL PRO 2026\n".encode())
            data.extend(f"TEST IMPRESION OK\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(f"Impresora: {printer_name}\n".encode())
            data.extend(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(b"ESTADO: OPERATIVA / ACTIVA\n\n\n\n\n")
            data.extend(b"\x1D\x56\x41\x00") # Corte de papel
            
            test_printer._send_raw_data(bytes(data))
            QMessageBox.information(self, "Éxito", f"Prueba de impresión enviada a {printer_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al imprimir: {e}")

    def _load_printers_and_ports(self):
        try:
            from src.utils.qt_printer import available_printer_names

            printers = list(available_printer_names())
            for cmb in [self.cmb_p1, self.cmb_p2]:
                cmb.blockSignals(True)
                cmb.clear()
                cmb.addItem("(Sin impresora)")
                cmb.addItems(printers)
                cmb.blockSignals(False)

            p1 = config.get("ticket_printer", "")
            p2 = config.get("ticket_printer_2", "")
            if p1 in printers: self.cmb_p1.setCurrentText(p1)
            if p2 in printers: self.cmb_p2.setCurrentText(p2)
            
            # Cargar puertos COM dinámicamente
            for cmb_com in [self.cmb_serial_port_1, self.cmb_serial_port_2]:
                cmb_com.blockSignals(True)
                cmb_com.clear()
            
            ports_list = ["Ninguno (USB Directo / OPOS)"] + [f"COM{i}" for i in range(1, 31)]
            try:
                import serial.tools.list_ports
                detected = [p.device for p in serial.tools.list_ports.comports()]
                for d in detected:
                    if d not in ports_list:
                        ports_list.insert(1, d)
            except Exception:
                pass
                
            self.cmb_serial_port_1.addItems(ports_list)
            self.cmb_serial_port_2.addItems(ports_list)
            
            saved_port_1 = config.get("printer_name", "")
            saved_port_2 = config.get("drawer_com_port_2", "")
            
            if saved_port_1:
                idx1 = self.cmb_serial_port_1.findText(saved_port_1)
                if idx1 != -1: self.cmb_serial_port_1.setCurrentIndex(idx1)
                else:
                    self.cmb_serial_port_1.addItem(saved_port_1)
                    self.cmb_serial_port_1.setCurrentText(saved_port_1)

            if saved_port_2:
                idx2 = self.cmb_serial_port_2.findText(saved_port_2)
                if idx2 != -1: self.cmb_serial_port_2.setCurrentIndex(idx2)
                else:
                    self.cmb_serial_port_2.addItem(saved_port_2)
                    self.cmb_serial_port_2.setCurrentText(saved_port_2)
                    
            for cmb_com in [self.cmb_serial_port_1, self.cmb_serial_port_2]:
                cmb_com.blockSignals(False)
        except Exception: pass

    def _guardar(self):
        p1 = self.cmb_p1.currentText()
        p2 = self.cmb_p2.currentText()
        if p1 == "(Sin impresora)": p1 = ""
        if p2 == "(Sin impresora)": p2 = ""
        config.set("ticket_printer", p1)
        config.set("ticket_printer_2", p2)
        
        com_val_1 = self.cmb_serial_port_1.currentText()
        if "Ninguno" in com_val_1: config.set("printer_name", "")
        else: config.set("printer_name", com_val_1)
            
        com_val_2 = self.cmb_serial_port_2.currentText()
        if "Ninguno" in com_val_2: config.set("drawer_com_port_2", "")
        else: config.set("drawer_com_port_2", com_val_2)
            
        QMessageBox.information(self, "✅ Guardado con Éxito",
            f"Cajero 1 → Impresora: {p1 or 'Ninguna'} | COM: {config.get('printer_name', 'Ninguno')}\n"
            f"Cajero 2 → Impresora: {p2 or 'Ninguna'} | COM: {config.get('drawer_com_port_2', 'Ninguno')}")
        self.accept()


