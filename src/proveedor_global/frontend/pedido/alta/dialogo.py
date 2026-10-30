from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
)

from src.proveedor_global.backend.ficha import FichaProveedor


class DialogoAltaProveedor(QDialog):
    """Da de alta la ficha. El id lo pone la maestra."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ficha = None
        self.setWindowTitle("Alta de proveedor")
        self.setFixedSize(420, 240)
        self.setStyleSheet("""
            QDialog { background: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
            QLabel { font-size: 12px; font-weight: 700; color: #1E293B; }
            QLineEdit {
                border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px;
                font-size: 13px; color: #0F172A; background: #F8FAFC;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Nombre:"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: La Serenísima")
        lay.addWidget(self.txt_nombre)
        lay.addWidget(QLabel("Teléfono (opcional):"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Ej: 5491122334455")
        lay.addWidget(self.txt_telefono)
        botones = QHBoxLayout()
        botones.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.setStyleSheet("background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        cancelar.clicked.connect(self.reject)
        botones.addWidget(cancelar)
        guardar = QPushButton("Crear id")
        guardar.setStyleSheet("background: #2563EB; color: white; border: none; border-radius: 8px; padding: 8px 18px; font-weight: bold;")
        guardar.clicked.connect(self._crear)
        botones.addWidget(guardar)
        lay.addLayout(botones)

    def _crear(self):
        ok, resultado = FichaProveedor.crear(self.txt_nombre.text(), self.txt_telefono.text())
        if not ok:
            QMessageBox.warning(self, "No se creó", str(resultado))
            return
        self.ficha = resultado
        codigo = str(resultado.get("codigo") or "").strip()
        if codigo and codigo.upper() != "EN CASA":
            aviso = f"Quedó {codigo}  {resultado['nombre']}."
        else:
            aviso = f"Quedó {resultado['nombre']}."
        QMessageBox.information(self, "Proveedor creado", aviso)
        self.accept()
