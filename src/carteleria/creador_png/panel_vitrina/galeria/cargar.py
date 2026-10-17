"""Cargar foto de la PC al nombre canónico del producto (pisa + respaldo)."""

from __future__ import annotations

import os

from src.utils.qt_compat import qt_exec
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox,
)

from src.carteleria.creador_png.panel_vitrina.archivo import (
    nombre_canonico, publicar_nuevo, slug_png,
)
from src.utils.letra import QSS_TITULO

PNG_LADO = 1024


class DialogoCargarVitrina(QDialog):
    def __init__(self, origen, destino_dir, producto="", icono_actual="", parent=None):
        super().__init__(parent)
        self.origen = origen
        self.destino_dir = destino_dir
        self.filename_guardado = None
        self._canon = nombre_canonico(producto, icono_actual)
        self._fijo = bool(icono_actual)
        self.setWindowTitle("Cargar PNG de vitrina")
        self.setMinimumSize(520, 560)
        self.resize(560, 620)
        self.setStyleSheet("background: #F8FAFC; font-family: 'Segoe UI', sans-serif;")
        self._armar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(12)

        titulo = QLabel("Cargar PNG")
        titulo.setStyleSheet(QSS_TITULO + " color: #1E293B; font-size: 20px;")
        lay.addWidget(titulo)

        aviso = QLabel(
            "Se guarda con el nombre de este producto. Si ya había uno, se pisa "
            "y el anterior queda en «Volver al anterior» por si no te gusta."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(
            "background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; "
            "border-radius: 10px; padding: 10px 12px; font-size: 12px; font-weight: 600;"
        )
        lay.addWidget(aviso)

        preview = QLabel()
        preview.setMinimumHeight(220)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setStyleSheet("background: #111827; border-radius: 12px;")
        pm = QPixmap(self.origen)
        if not pm.isNull():
            preview.setPixmap(pm.scaled(
                280, 280,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            preview.setText("No se pudo leer")
        lay.addWidget(preview)

        self.txt_nombre = QLineEdit(slug_png(os.path.splitext(self._canon)[0]))
        self.txt_nombre.setReadOnly(self._fijo)
        self.txt_nombre.setStyleSheet(
            "background: white; border: 2px solid #2563EB; border-radius: 8px; "
            "padding: 10px 12px; font-size: 14px; font-weight: 700; color: #0F172A;"
        )
        lay.addWidget(QLabel("Archivo (un PNG por producto):"))
        lay.addWidget(self.txt_nombre)
        lay.addStretch()

        botones = QHBoxLayout()
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Guardar PNG")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet(
            "QPushButton { background: #059669; color: white; border: none; "
            "border-radius: 8px; padding: 10px 22px; font-weight: bold; }"
            "QPushButton:hover { background: #047857; }"
        )
        ok.clicked.connect(self._guardar)
        botones.addWidget(cancel)
        botones.addStretch()
        botones.addWidget(ok)
        lay.addLayout(botones)

    def _guardar(self):
        nombre = os.path.splitext(self._canon)[0] if self._fijo else slug_png(self.txt_nombre.text())
        if not nombre:
            QMessageBox.warning(self, "Nombre", "Escribí un nombre para el PNG.")
            return
        dest = os.path.join(self.destino_dir, f"{nombre}.png")
        tmp = dest + ".part"
        try:
            self._escribir(tmp)
            publicar_nuevo(tmp, dest)
        except Exception as exc:
            try:
                if os.path.isfile(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{exc}")
            return
        self.filename_guardado = f"{nombre}.png"
        self.accept()

    def _escribir(self, dest):
        from PIL import Image

        img = Image.open(self.origen).convert("RGBA")
        w, h = img.size
        resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
        if max(w, h) > PNG_LADO:
            escala = PNG_LADO / max(w, h)
            img = img.resize((max(1, int(w * escala)), max(1, int(h * escala))), resample)
        canvas = Image.new("RGBA", (PNG_LADO, PNG_LADO), (0, 0, 0, 0))
        canvas.paste(img, ((PNG_LADO - img.width) // 2, (PNG_LADO - img.height) // 2), img)
        canvas.save(dest, "PNG", dpi=(150, 150))
        try:
            from src.carteleria.creador_png.fondo_transparente import quitar_fondo_negro
            quitar_fondo_negro(dest)
        except Exception:
            pass


def elegir_desde_pc(parent, destino_dir, producto="", icono_actual="") -> str | None:
    origen, _ = QFileDialog.getOpenFileName(
        parent, "Seleccionar PNG", "",
        "Imágenes (*.png *.jpg *.jpeg *.webp)",
    )
    if not origen:
        return None
    dlg = DialogoCargarVitrina(
        origen, destino_dir, producto=producto, icono_actual=icono_actual, parent=parent,
    )
    if not qt_exec(dlg):
        return None
    return dlg.filename_guardado
