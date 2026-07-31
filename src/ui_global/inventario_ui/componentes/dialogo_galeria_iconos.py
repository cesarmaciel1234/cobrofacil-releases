import os
import shutil
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QWidget, QGridLayout, QFrame,
    QFileDialog, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QIcon

# Qt6 Enum compatibility helpers
if hasattr(Qt, 'AlignmentFlag'):
    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
if hasattr(Qt, 'CursorShape'):
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor


class DialogoGaleriaIconos(QDialog):
    """
    Diálogo para explorar, seleccionar y cargar íconos PNG/JPG/SVG
    guardados en la carpeta local 'Catalogos/iconos_rubros/'.
    """
    def __init__(self, icono_actual=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 Galería de Íconos de Rubros")
        self.setFixedSize(680, 560)
        self.setStyleSheet("background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif;")
        
        self.target_dir = os.path.join(os.getcwd(), "Catalogos", "iconos_rubros")
        os.makedirs(self.target_dir, exist_ok=True)
        
        self._icono_seleccionado = icono_actual
        self._cards = {}
        
        self._setup_ui()
        self.cargar_iconos()

    def _setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(16)

        # ── Encabezado ────────────────────────────────────────────────────────
        header_lay = QHBoxLayout()
        lbl_tit = QLabel("🎨 Galería de Íconos para Departamentos")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B;")
        header_lay.addWidget(lbl_tit)
        header_lay.addStretch()

        btn_cargar = QPushButton("➕ Cargar Ícono desde PC")
        btn_cargar.setCursor(Qt.PointingHandCursor)
        btn_cargar.setStyleSheet("""
            QPushButton {
                background: #059669; color: white; border: none;
                border-radius: 8px; padding: 8px 16px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #047857; }
        """)
        btn_cargar.clicked.connect(self._importar_icono_desde_pc)
        header_lay.addWidget(btn_cargar)
        main_lay.addLayout(header_lay)

        # ── Buscador ──────────────────────────────────────────────────────────
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar ícono por nombre (ej: carne, pollo, bebidas)...")
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #CBD5E1; border-radius: 8px;
                padding: 10px 14px; font-size: 13px; color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #2563EB; }
        """)
        self.txt_buscar.textChanged.connect(self.filtrar_iconos)
        main_lay.addWidget(self.txt_buscar)

        # ── Área de Desplazamiento de Íconos (Grid Gallery) ───────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: 1px solid #E2E8F0; border-radius: 12px; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: white; border-radius: 12px;")
        self.grid_lay = QGridLayout(self.grid_widget)
        self.grid_lay.setContentsMargins(16, 16, 16, 16)
        self.grid_lay.setSpacing(14)
        
        self.scroll.setWidget(self.grid_widget)
        main_lay.addWidget(self.scroll)

        # ── Footer y Botones ──────────────────────────────────────────────────
        footer_lay = QHBoxLayout()
        self.lbl_seleccion = QLabel(f"Ícono seleccionado: {self._icono_seleccionado or 'Ninguno'}")
        self.lbl_seleccion.setStyleSheet("font-weight: bold; color: #64748B; font-size: 12px;")
        footer_lay.addWidget(self.lbl_seleccion)
        footer_lay.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("padding: 10px 20px; border-radius: 8px; font-weight: bold; background: #E2E8F0; color: #475569;")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✔ Confirmar Selección")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; border: none;
                border-radius: 8px; padding: 10px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_ok.clicked.connect(self._confirmar)

        footer_lay.addWidget(btn_cancel)
        footer_lay.addWidget(btn_ok)
        main_lay.addLayout(footer_lay)

    def cargar_iconos(self):
        # Limpiar grid previo
        for i in reversed(range(self.grid_lay.count())):
            w = self.grid_lay.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._cards.clear()

        exts = ('.png', '.jpg', '.jpeg', '.svg', '.webp')
        files = [f for f in os.listdir(self.target_dir) if f.lower().endswith(exts)]
        files.sort()

        if not files:
            lbl_empty = QLabel("No hay íconos guardados en la carpeta Catalogos/iconos_rubros.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #94A3B8; font-weight: bold; padding: 30px;")
            self.grid_lay.addWidget(lbl_empty, 0, 0)
            return

        cols = 5
        row, col = 0, 0
        for fname in files:
            fpath = os.path.join(self.target_dir, fname)
            card = self._crear_tarjeta_icono(fname, fpath)
            self._cards[fname] = card
            self.grid_lay.addWidget(card, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Si ya hay un ícono seleccionado, remarcarlo
        if self._icono_seleccionado in self._cards:
            self._seleccionar_tarjeta(self._icono_seleccionado)

    def _crear_tarjeta_icono(self, filename, filepath):
        card = QFrame()
        card.setFixedSize(108, 115)
        card.setCursor(Qt.PointingHandCursor)
        card.setObjectName("IconCard")
        card.setStyleSheet("""
            QFrame#IconCard {
                background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px;
            }
            QFrame#IconCard:hover {
                background: #F1F5F9; border: 2px solid #3B82F6;
            }
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(8, 8, 8, 6)
        lay.setSpacing(4)

        pixmap = QPixmap(filepath)
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setStyleSheet("background: transparent; border: none;")
        if not pixmap.isNull():
            lbl_img.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_img.setText("🖼️")

        name_clean = os.path.splitext(filename)[0].capitalize()
        lbl_name = QLabel(name_clean)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setStyleSheet("font-size: 10px; font-weight: 700; color: #334155; background: transparent; border: none;")

        lay.addWidget(lbl_img)
        lay.addWidget(lbl_name)

        card.mousePressEvent = lambda e, f=filename: self._seleccionar_tarjeta(f)
        return card

    def _seleccionar_tarjeta(self, filename):
        self._icono_seleccionado = filename
        self.lbl_seleccion.setText(f"Ícono seleccionado: {filename}")

        for fname, card in self._cards.items():
            if fname == filename:
                card.setStyleSheet("""
                    QFrame#IconCard {
                        background: #EFF6FF; border: 2px solid #2563EB; border-radius: 12px;
                    }
                """)
            else:
                card.setStyleSheet("""
                    QFrame#IconCard {
                        background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px;
                    }
                    QFrame#IconCard:hover {
                        background: #F1F5F9; border: 2px solid #3B82F6;
                    }
                """)

    def filtrar_iconos(self, texto):
        t = texto.strip().lower()
        for fname, card in self._cards.items():
            if not t or t in fname.lower():
                card.show()
            else:
                card.hide()

    def _importar_icono_desde_pc(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de ícono", "",
            "Imágenes (*.png *.jpg *.jpeg *.svg *.webp)"
        )
        if not filePath:
            return

        base_name = os.path.basename(filePath)
        dest_path = os.path.join(self.target_dir, base_name)
        try:
            shutil.copy2(filePath, dest_path)
            self.cargar_iconos()
            self._seleccionar_tarjeta(base_name)
            QMessageBox.information(self, "Ícono importado", f"El ícono '{base_name}' fue guardado exitosamente en la galería.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo copiar el archivo: {e}")

    def _confirmar(self):
        if not self._icono_seleccionado:
            QMessageBox.warning(self, "Aviso", "Por favor selecciona un ícono de la galería.")
            return
        self.accept()

    def get_selected_icon(self):
        return self._icono_seleccionado
