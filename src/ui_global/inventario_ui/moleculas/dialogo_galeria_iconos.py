import os
import re
import shutil
import unicodedata
from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QWidget, QGridLayout, QFrame,
    QFileDialog, QMessageBox, QGraphicsDropShadowEffect, QToolButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QIcon

PNG_LADO_IDEAL = 1024
PNG_LADO_MINIMO = 512
PNG_DPI = 150

# Qt6 Enum compatibility helpers
if hasattr(Qt, 'AlignmentFlag'):
    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
if hasattr(Qt, 'CursorShape'):
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
if hasattr(Qt, 'ToolButtonStyle') and not hasattr(Qt, 'ToolButtonTextUnderIcon'):
    Qt.ToolButtonTextUnderIcon = Qt.ToolButtonStyle.ToolButtonTextUnderIcon


def slug_png(nombre):
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto[:60]


class DialogoCargarPng(QDialog):
    """Después de elegir el archivo: medidas recomendadas + nombre obligatorio."""

    def __init__(self, origen, destino_dir, nombre_sugerido="", parent=None):
        super().__init__(parent)
        self.origen = origen
        self.destino_dir = destino_dir
        self.filename_guardado = None
        self.setWindowTitle("Cargar PNG de vitrina")
        self.setFixedSize(460, 520)
        self.setStyleSheet("background: #F8FAFC; font-family: 'Segoe UI', sans-serif;")
        self._setup_ui(nombre_sugerido)

    def _setup_ui(self, nombre_sugerido):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(12)

        titulo = QLabel("Cargar PNG")
        titulo.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B;")
        lay.addWidget(titulo)

        specs = QLabel(
            "Medidas recomendadas para TV\n"
            f"• {PNG_LADO_IDEAL} × {PNG_LADO_IDEAL} px (cuadrado)\n"
            f"• Mínimo {PNG_LADO_MINIMO} × {PNG_LADO_MINIMO} px\n"
            f"• Resolución {PNG_DPI} dpi · formato PNG\n"
            "• Fondo transparente (foto recortada)"
        )
        specs.setStyleSheet(
            "background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; "
            "border-radius: 10px; padding: 12px 14px; font-size: 12px; font-weight: 600;"
        )
        lay.addWidget(specs)

        preview = QLabel()
        preview.setFixedHeight(160)
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet(
            "background: #111827; border: 1px solid #CBD5E1; border-radius: 12px;"
        )
        pm = QPixmap(self.origen)
        ancho = alto = 0
        if not pm.isNull():
            ancho, alto = pm.width(), pm.height()
            preview.setPixmap(pm.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            preview.setText("No se pudo leer la imagen")
        lay.addWidget(preview)

        aviso = ""
        if ancho and alto:
            aviso = f"Archivo elegido: {ancho} × {alto} px"
            if min(ancho, alto) < PNG_LADO_MINIMO:
                aviso += f"  ·  bajo el mínimo ({PNG_LADO_MINIMO} px)"
            elif ancho == alto == PNG_LADO_IDEAL:
                aviso += "  ·  medida ideal"
            elif min(ancho, alto) >= PNG_LADO_IDEAL:
                aviso += "  ·  se va a ajustar a 1024 × 1024"
        self.lbl_info = QLabel(aviso or "No se pudieron leer las medidas.")
        self.lbl_info.setStyleSheet("color: #475569; font-size: 12px; font-weight: 600;")
        self.lbl_info.setWordWrap(True)
        lay.addWidget(self.lbl_info)

        lbl_n = QLabel("Nombre del PNG (obligatorio)")
        lbl_n.setStyleSheet("font-weight: 800; color: #1E293B; font-size: 13px;")
        lay.addWidget(lbl_n)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: asado  ·  vacio  ·  pollo_entero")
        self.txt_nombre.setText(slug_png(nombre_sugerido) or slug_png(os.path.splitext(os.path.basename(self.origen))[0]))
        self.txt_nombre.setStyleSheet(
            "background: white; border: 2px solid #2563EB; border-radius: 8px; "
            "padding: 10px 12px; font-size: 14px; font-weight: 700; color: #0F172A;"
        )
        lay.addWidget(self.txt_nombre)

        hint = QLabel(
            f"Sin espacios ni acentos. Se crea en:\n{self.destino_dir}\\nombre.png"
        )
        hint.setStyleSheet("color: #94A3B8; font-size: 11px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch()

        botones = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "padding: 10px 18px; border-radius: 8px; font-weight: bold; background: #E2E8F0; color: #475569;"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Guardar PNG")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background: #059669; color: white; border: none;
                border-radius: 8px; padding: 10px 22px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #047857; }
        """)
        btn_ok.clicked.connect(self._guardar)
        botones.addWidget(btn_cancel)
        botones.addStretch()
        botones.addWidget(btn_ok)
        lay.addLayout(botones)

    def _guardar(self):
        nombre = slug_png(self.txt_nombre.text())
        if not nombre:
            QMessageBox.warning(self, "Nombre obligatorio", "Escribí un nombre para el PNG.")
            self.txt_nombre.setFocus()
            return
        os.makedirs(self.destino_dir, exist_ok=True)
        dest = os.path.join(self.destino_dir, f"{nombre}.png")
        if os.path.exists(dest):
            if QMessageBox.question(
                self,
                "Ya existe",
                f"Ya hay un archivo «{nombre}.png». ¿Reemplazarlo?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
        try:
            self._escribir_png(dest)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el PNG:\n{exc}")
            return
        self.filename_guardado = f"{nombre}.png"
        self.accept()

    def _escribir_png(self, dest):
        try:
            from PIL import Image
            img = Image.open(self.origen).convert("RGBA")
            w, h = img.size
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
            if max(w, h) > PNG_LADO_IDEAL:
                escala = PNG_LADO_IDEAL / max(w, h)
                img = img.resize(
                    (max(1, int(w * escala)), max(1, int(h * escala))),
                    resample,
                )
            canvas = Image.new("RGBA", (PNG_LADO_IDEAL, PNG_LADO_IDEAL), (0, 0, 0, 0))
            canvas.paste(
                img,
                ((PNG_LADO_IDEAL - img.width) // 2, (PNG_LADO_IDEAL - img.height) // 2),
                img,
            )
            canvas.save(dest, "PNG", dpi=(PNG_DPI, PNG_DPI))
            try:
                from src.carteleria.png_productos.fondo_transparente import quitar_fondo_negro
                quitar_fondo_negro(dest)
            except Exception:
                pass
            return
        except Exception:
            shutil.copy2(self.origen, dest)


class DialogoGaleriaIconos(QDialog):
    """
    Diálogo para explorar, seleccionar y cargar íconos PNG/JPG/SVG
    guardados en la carpeta local 'Catalogos/'.
    """
    def __init__(self, icono_actual=None, parent=None, titulo=None, target_dir=None, extra_dirs=None, nombre_sugerido=""):
        super().__init__(parent)
        self._titulo = titulo or "🎨 Galería de Íconos de Rubros"
        self._nombre_sugerido = nombre_sugerido or ""
        self.setWindowTitle(self._titulo)
        self.setFixedSize(680, 620)
        self.setStyleSheet("background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif;")

        if target_dir:
            self.target_dir = target_dir
        else:
            try:
                from src.carteleria.assets_paths import catalogos_dir
                self.target_dir = catalogos_dir()
            except Exception:
                self.target_dir = os.path.join(os.getcwd(), "Catalogos")
        os.makedirs(self.target_dir, exist_ok=True)
        self.extra_dirs = [d for d in (extra_dirs or []) if d and os.path.isdir(d)]

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
        lbl_tit = QLabel(self._titulo)
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B;")
        header_lay.addWidget(lbl_tit)
        header_lay.addStretch()

        btn_cargar = QPushButton("➕ Cargar PNG desde PC")
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

        specs = QLabel(
            f"Los PNG se crean y cargan en:\n{self.target_dir}\n"
            f"Medidas: {PNG_LADO_IDEAL}×{PNG_LADO_IDEAL} px  ·  mínimo {PNG_LADO_MINIMO} px  ·  "
            f"{PNG_DPI} dpi  ·  fondo transparente"
        )
        specs.setStyleSheet(
            "background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; "
            "border-radius: 8px; padding: 8px 12px; font-size: 11px; font-weight: 700;"
        )
        specs.setWordWrap(True)
        main_lay.addWidget(specs)

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
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        junk = ("attractor", "-16px")
        seen = set()
        files = []
        for folder in [self.target_dir, *self.extra_dirs]:
            if not folder or not os.path.isdir(folder):
                continue
            for dirpath, _dirnames, filenames in os.walk(folder):
                for fname in filenames:
                    clave = fname.lower()
                    if clave in seen or not clave.endswith(exts):
                        continue
                    if any(marca in clave for marca in junk):
                        continue
                    fpath = os.path.join(dirpath, fname)
                    if not os.path.isfile(fpath):
                        continue
                    try:
                        if os.path.getsize(fpath) < 400:
                            continue
                    except OSError:
                        continue
                    seen.add(clave)
                    files.append((fname, fpath))
        files.sort(key=lambda item: item[0].lower())

        if not files:
            lbl_empty = QLabel("No hay PNG en la galería. Cargá una foto desde la PC.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #94A3B8; font-weight: bold; padding: 30px;")
            self.grid_lay.addWidget(lbl_empty, 0, 0)
            return

        cols = 5
        row, col = 0, 0
        for fname, fpath in files:
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
        card = QToolButton()
        card.setCheckable(True)
        card.setAutoExclusive(False)
        card.setFixedSize(108, 115)
        card.setCursor(Qt.PointingHandCursor)
        card.setObjectName("IconCard")
        card.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        card.setStyleSheet("""
            QToolButton#IconCard {
                background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px;
                font-size: 10px; font-weight: 700; color: #334155;
                padding: 6px 4px;
            }
            QToolButton#IconCard:hover {
                background: #F1F5F9; border: 2px solid #3B82F6;
            }
            QToolButton#IconCard:checked {
                background: #EFF6FF; border: 2px solid #2563EB;
            }
        """)
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            card.setIcon(QIcon(pixmap))
            card.setIconSize(QSize(56, 56))
        name_clean = os.path.splitext(filename)[0].replace("_", " ")
        card.setText(name_clean)
        card.setToolTip(filename)
        card.clicked.connect(lambda _checked=False, f=filename: self._seleccionar_tarjeta(f))
        return card

    def _seleccionar_tarjeta(self, filename):
        self._icono_seleccionado = filename
        self.lbl_seleccion.setText(f"Ícono seleccionado: {filename}")
        for fname, card in self._cards.items():
            card.setChecked(fname == filename)

    def filtrar_iconos(self, texto):
        t = texto.strip().lower()
        for fname, card in self._cards.items():
            if not t or t in fname.lower():
                card.show()
            else:
                card.hide()

    def _importar_icono_desde_pc(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PNG", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        if not filePath:
            return

        dlg = DialogoCargarPng(
            origen=filePath,
            destino_dir=self.target_dir,
            nombre_sugerido=self._nombre_sugerido,
            parent=self,
        )
        if not qt_exec(dlg):
            return
        nombre = dlg.filename_guardado
        if not nombre:
            return
        self.cargar_iconos()
        self._seleccionar_tarjeta(nombre)

    def _confirmar(self):
        if not self._icono_seleccionado:
            QMessageBox.warning(self, "Aviso", "Por favor selecciona un ícono de la galería.")
            return
        self.accept()

    def get_selected_icon(self):
        return self._icono_seleccionado
