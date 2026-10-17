"""Galería grande de vitrina: rápida, pantalla completa, borrar, un PNG por producto."""

from __future__ import annotations

import os

from src.utils.qt_compat import qt_exec
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QGridLayout, QMessageBox,
)
from src.utils.letra import QSS_TITULO
from src.carteleria.creador_png.panel_vitrina.archivo import (
    borrar_png, hay_anterior, listar_pngs, restaurar_anterior,
)
from src.carteleria.creador_png.panel_vitrina.galeria.tarjetas import TarjetaPng


class DialogoGaleriaVitrina(QDialog):
    def __init__(self, icono_actual=None, parent=None, destino_dir="", producto=""):
        super().__init__(parent)
        self._producto = producto or ""
        self._icono_seleccionado = icono_actual
        self.target_dir = destino_dir
        self._cards = {}
        self._pendientes = []
        self.setWindowTitle("PNG del producto (foto de vitrina)")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(980, 680)
        self.setStyleSheet("background: #F8FAFC; font-family: 'Segoe UI', sans-serif;")
        self._armar()
        self._cargar_nombres()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.showMaximized)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            self._pantalla_completa()
            return
        super().keyPressEvent(event)

    def _armar(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 16, 20, 16)
        main.setSpacing(12)

        header = QHBoxLayout()
        tit = QLabel("PNG del producto (foto de vitrina)")
        tit.setStyleSheet(QSS_TITULO + " color: #1E293B; font-size: 20px;")
        header.addWidget(tit)
        header.addStretch()

        self.btn_full = QPushButton("Pantalla completa")
        self.btn_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_full.clicked.connect(self._pantalla_completa)
        btn_pc = QPushButton("➕ Cargar PNG desde PC")
        btn_pc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pc.setStyleSheet(
            "QPushButton { background: #059669; color: white; border: none; "
            "border-radius: 8px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #047857; }"
        )
        btn_pc.clicked.connect(self._importar)
        header.addWidget(self.btn_full)
        header.addWidget(btn_pc)
        main.addLayout(header)

        pista = QLabel(
            "Un PNG por producto: crear o cargar pisa el anterior. "
            "El anterior queda para «Volver al anterior». Casillero + ✕ para borrar. F11 pantalla completa."
        )
        pista.setWordWrap(True)
        pista.setStyleSheet(
            "background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; "
            "border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: 600;"
        )
        main.addWidget(pista)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre…")
        self.txt_buscar.setStyleSheet(
            "background: white; border: 1px solid #CBD5E1; border-radius: 8px; "
            "padding: 10px 14px; font-size: 13px;"
        )
        self.txt_buscar.textChanged.connect(self._filtrar)
        main.addWidget(self.txt_buscar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }")
        self.grid_widget = QWidget()
        self.grid_lay = QGridLayout(self.grid_widget)
        self.grid_lay.setContentsMargins(16, 16, 16, 16)
        self.grid_lay.setSpacing(12)
        self.scroll.setWidget(self.grid_widget)
        main.addWidget(self.scroll, 1)

        footer = QHBoxLayout()
        self.lbl_sel = QLabel(f"Elegido: {self._icono_seleccionado or 'ninguno'}")
        self.lbl_sel.setStyleSheet("font-weight: 700; color: #64748B;")
        footer.addWidget(self.lbl_sel)
        footer.addStretch()

        self.btn_anterior = QPushButton("Volver al anterior")
        self.btn_anterior.setEnabled(False)
        self.btn_anterior.clicked.connect(self._restaurar)
        btn_marcados = QPushButton("Eliminar marcados")
        btn_marcados.setStyleSheet(
            "QPushButton { background: #FEE2E2; color: #B91C1C; border: none; "
            "border-radius: 8px; padding: 10px 16px; font-weight: bold; }"
        )
        btn_marcados.clicked.connect(self._borrar_marcados)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("✔ Confirmar")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; padding: 10px 24px; font-weight: bold; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        ok.clicked.connect(self._confirmar)
        footer.addWidget(self.btn_anterior)
        footer.addWidget(btn_marcados)
        footer.addWidget(cancel)
        footer.addWidget(ok)
        main.addLayout(footer)

    def _pantalla_completa(self):
        if self.isFullScreen():
            self.showMaximized()
            self.btn_full.setText("Pantalla completa")
        else:
            self.showFullScreen()
            self.btn_full.setText("Salir de pantalla completa")

    def _cargar_nombres(self):
        for i in reversed(range(self.grid_lay.count())):
            w = self.grid_lay.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._cards.clear()
        self._pendientes = []
        files = listar_pngs(self.target_dir)
        if not files:
            lbl = QLabel("No hay PNG. Cargá una foto desde la PC o usá Creador PNG Pro.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #94A3B8; font-weight: bold; padding: 30px;")
            self.grid_lay.addWidget(lbl, 0, 0)
            self._actualizar_anterior()
            return
        cols = 6
        for i, (fname, fpath) in enumerate(files):
            card = TarjetaPng(fname, fpath)
            card.elegida.connect(self._elegir)
            card.borrar.connect(self._borrar_uno)
            self._cards[fname] = card
            self.grid_lay.addWidget(card, i // cols, i % cols)
            self._pendientes.append(card)
        if self._icono_seleccionado in self._cards:
            self._elegir(self._icono_seleccionado)
        QTimer.singleShot(0, self._pintar_lote)

    def _pintar_lote(self):
        lote = self._pendientes[:16]
        self._pendientes = self._pendientes[16:]
        for card in lote:
            try:
                card.pintar_thumb()
            except RuntimeError:
                pass
        if self._pendientes:
            QTimer.singleShot(0, self._pintar_lote)

    def _elegir(self, filename):
        self._icono_seleccionado = filename
        self.lbl_sel.setText(f"Elegido: {filename}")
        for fname, card in self._cards.items():
            try:
                card.set_elegida(fname == filename)
            except RuntimeError:
                pass
        self._actualizar_anterior()

    def _actualizar_anterior(self):
        name = self._icono_seleccionado or ""
        dest = os.path.join(self.target_dir, name) if name else ""
        self.btn_anterior.setEnabled(bool(dest and hay_anterior(dest)))

    def _filtrar(self, texto):
        t = texto.strip().lower()
        for fname, card in self._cards.items():
            card.setVisible(not t or t in fname.lower())

    def _importar(self):
        from src.carteleria.creador_png.panel_vitrina.galeria.cargar import elegir_desde_pc

        nombre = elegir_desde_pc(
            self, self.target_dir, producto=self._producto, icono_actual=self._icono_seleccionado or "",
        )
        if not nombre:
            return
        self._icono_seleccionado = nombre
        self._cargar_nombres()

    def _ruta(self, filename):
        return os.path.join(self.target_dir, filename)

    def _borrar_uno(self, filename):
        if QMessageBox.question(
            self, "Eliminar PNG",
            f"¿Borrar «{filename}» de la carpeta?\nLa TV deja de usarlo si un producto lo tenía.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        ok, msg = borrar_png(self._ruta(filename))
        if not ok:
            QMessageBox.warning(self, "No se pudo borrar", msg)
            return
        if self._icono_seleccionado == filename:
            self._icono_seleccionado = None
        self._cargar_nombres()

    def _borrar_marcados(self):
        marcados = [n for n, c in self._cards.items() if c.chk.isChecked()]
        if not marcados:
            QMessageBox.information(self, "Eliminar", "Marcá el casillero de los PNG que querés borrar.")
            return
        if QMessageBox.question(
            self, "Eliminar PNG",
            f"¿Borrar {len(marcados)} archivo(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        for name in marcados:
            borrar_png(self._ruta(name))
            if self._icono_seleccionado == name:
                self._icono_seleccionado = None
        self._cargar_nombres()

    def _restaurar(self):
        name = self._icono_seleccionado
        if not name:
            return
        dest = self._ruta(name)
        if not restaurar_anterior(dest):
            QMessageBox.information(self, "Anterior", "No hay un PNG anterior de este archivo.")
            return
        self._cargar_nombres()
        QMessageBox.information(self, "Anterior", "Volvió el PNG de antes. El que no te gustó quedó de respaldo.")

    def _confirmar(self):
        if not self._icono_seleccionado:
            QMessageBox.warning(self, "Aviso", "Elegí un PNG.")
            return
        self.accept()

    def get_selected_icon(self):
        return self._icono_seleccionado


def abrir_galeria(parent, destino_dir, icono_actual="", producto="") -> str | None:
    dlg = DialogoGaleriaVitrina(
        icono_actual=icono_actual, parent=parent, destino_dir=destino_dir, producto=producto,
    )
    if not qt_exec(dlg):
        return None
    return dlg.get_selected_icon()
