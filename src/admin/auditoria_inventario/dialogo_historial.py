"""Diálogo de Historial y Auditoría Global de Ajustes de Stock.

Permite auditar el comportamiento del negocio, inspeccionar modificaciones manuales
de stock, filtrar por producto, código, usuario responsable y tipo de diferencia,
con soporte de pantalla completa (maximizar al lado de la X) y exportación a Excel.
"""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QFileDialog, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QBrush, QFont

from src.utils.theme_manager import theme_manager
from src.utils.letra import (
    fuente_id, fuente_nombre, fuente_numero,
    vestir_id, vestir_nombre, vestir_numero,
    QSS_KPI, QSS_TITULO
)


class DialogoHistorialAuditoria(QDialog):
    def __init__(
        self,
        parent=None,
        producto_id: Optional[int | str] = None,
        codigo: Optional[str] = None,
        nombre_producto: Optional[str] = None,
        conector=None
    ):
        super().__init__(parent)
        self.producto_id_filtro = producto_id
        self.codigo_filtro = codigo
        self.nombre_producto_filtro = nombre_producto
        self.conector = conector

        self.todos_los_registros: List[Dict] = []
        self.registros_filtrados: List[Dict] = []

        # Habilitar botones de Maximizar (Pantalla Completa) y Minimizar al lado de la X
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.setWindowTitle("Historial de Ajustes — Auditoría de Stock")
        self.resize(1120, 680)
        self.setMinimumSize(850, 500)

        self._setup_ui()
        self._cargar_datos_iniciales()
        self._aplicar_tema()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # --- 1. ENCABEZADO CON TÍTULO Y BOTÓN PANTALLA COMPLETA ---
        header_layout = QHBoxLayout()

        tit_box = QVBoxLayout()
        tit_box.setSpacing(3)
        self.lbl_titulo = QLabel("📋 HISTORIAL DE AJUSTES Y AUDITORÍA DE STOCK")
        self.lbl_titulo.setStyleSheet(QSS_TITULO)
        self.lbl_subtitulo = QLabel(
            "Trazabilidad de modificaciones de stock: cuándo, quién y por qué se ajustó cada producto."
        )
        self.lbl_subtitulo.setStyleSheet("font-size: 12px; font-weight: 600; opacity: 0.75;")
        tit_box.addWidget(self.lbl_titulo)
        tit_box.addWidget(self.lbl_subtitulo)
        header_layout.addLayout(tit_box)

        header_layout.addStretch()

        # Botón de pantalla completa manual integrado
        self.btn_fullscreen = QPushButton("🗖 PANTALLA COMPLETA")
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fullscreen.setStyleSheet(
            "font-size: 12px; font-weight: 900; padding: 8px 16px; border-radius: 6px; "
            "background: #0284C7; color: white; border: none;"
        )
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        header_layout.addWidget(self.btn_fullscreen)

        # Botón Exportar
        self.btn_exportar = QPushButton("📥 EXPORTAR (CSV / Excel)")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet(
            "font-size: 12px; font-weight: 900; padding: 8px 16px; border-radius: 6px; "
            "background: #059669; color: white; border: none;"
        )
        self.btn_exportar.clicked.connect(self._exportar_csv)
        header_layout.addWidget(self.btn_exportar)

        main_layout.addLayout(header_layout)

        # --- 2. TARJETAS KPI DE RESUMEN EN VIVO ---
        kpis_layout = QHBoxLayout()
        kpis_layout.setSpacing(12)

        self.card_total, self.val_total = self._crear_kpi_card("📊 REGISTROS", "0", "#3B82F6")
        self.card_prods, self.val_prods = self._crear_kpi_card("📦 PRODUCTOS", "0", "#8B5CF6")
        self.card_falt, self.val_falt = self._crear_kpi_card("🔻 FALTANTE NETO", "0.000", "#EF4444")
        self.card_sobr, self.val_sobr = self._crear_kpi_card("🔺 SOBRANTE NETO", "0.000", "#10B981")

        kpis_layout.addWidget(self.card_total)
        kpis_layout.addWidget(self.card_prods)
        kpis_layout.addWidget(self.card_falt)
        kpis_layout.addWidget(self.card_sobr)
        main_layout.addLayout(kpis_layout)

        # --- 3. BARRA DE FILTROS MULTIDIMENSIONAL ---
        filtro_frame = QFrame()
        filtro_frame.setObjectName("FiltroFrame")
        filtro_frame.setStyleSheet(
            "QFrame#FiltroFrame { background: rgba(15, 23, 42, 0.04); "
            "border: 1px solid rgba(15, 23, 42, 0.12); border-radius: 10px; padding: 8px; }"
        )
        filtro_lay = QHBoxLayout(filtro_frame)
        filtro_lay.setContentsMargins(10, 8, 10, 8)
        filtro_lay.setSpacing(10)

        # Buscador texto libre
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por producto, ID, código, usuario o motivo...")
        self.txt_buscar.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px 12px; border-radius: 6px;")
        self.txt_buscar.textChanged.connect(self._aplicar_filtros)
        filtro_lay.addWidget(self.txt_buscar, 3)

        # Filtro Producto
        self.cmb_producto = QComboBox()
        self.cmb_producto.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px 10px; border-radius: 6px;")
        self.cmb_producto.currentIndexChanged.connect(self._aplicar_filtros)
        filtro_lay.addWidget(self.cmb_producto, 2)

        # Filtro Usuario
        self.cmb_usuario = QComboBox()
        self.cmb_usuario.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px 10px; border-radius: 6px;")
        self.cmb_usuario.currentIndexChanged.connect(self._aplicar_filtros)
        filtro_lay.addWidget(self.cmb_usuario, 1)

        # Filtro Diferencia
        self.cmb_dif = QComboBox()
        self.cmb_dif.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px 10px; border-radius: 6px;")
        self.cmb_dif.addItem("Todos los ajustes", "todos")
        self.cmb_dif.addItem("🔴 Solo Faltantes (-)", "faltantes")
        self.cmb_dif.addItem("🟢 Solo Sobrantes (+)", "sobrantes")
        self.cmb_dif.addItem("⚪ Sin diferencia (0)", "ceros")
        self.cmb_dif.currentIndexChanged.connect(self._aplicar_filtros)
        filtro_lay.addWidget(self.cmb_dif, 1)

        # Botón Limpiar Filtros
        self.btn_limpiar = QPushButton("LIMPIAR")
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.setStyleSheet(
            "font-size: 11px; font-weight: bold; padding: 7px 12px; border-radius: 6px; "
            "background: transparent; color: #64748B; border: 1px solid #94A3B8;"
        )
        self.btn_limpiar.clicked.connect(self._limpiar_filtros)
        filtro_lay.addWidget(self.btn_limpiar)

        main_layout.addWidget(filtro_frame)

        # --- 4. TABLA DE AJUSTES ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "FECHA Y HORA", "ID", "CÓDIGO", "PRODUCTO",
            "USUARIO", "STOCK ANT.", "STOCK NUEVO", "DIFERENCIA", "MOTIVO"
        ])
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setDefaultSectionSize(34)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.tabla, 1)

        # --- 5. BARRA INFERIOR ---
        bottom_layout = QHBoxLayout()
        self.lbl_estado_filas = QLabel("Cargando historial...")
        self.lbl_estado_filas.setStyleSheet("font-size: 12px; font-weight: bold; opacity: 0.8;")
        bottom_layout.addWidget(self.lbl_estado_filas)

        bottom_layout.addStretch()

        self.btn_cerrar = QPushButton("CERRAR")
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.setStyleSheet(
            "background: #475569; color: white; font-weight: bold; font-size: 13px; "
            "padding: 10px 24px; border-radius: 8px; border: none;"
        )
        self.btn_cerrar.clicked.connect(self.accept)
        bottom_layout.addWidget(self.btn_cerrar)

        main_layout.addLayout(bottom_layout)

    def _crear_kpi_card(self, titulo: str, valor_ini: str, color_acento: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("KpiCard")
        card.setStyleSheet(
            f"QFrame#KpiCard {{ background: rgba(15, 23, 42, 0.03); "
            f"border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 8px; padding: 6px 12px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 11px; font-weight: 800; opacity: 0.7;")

        lbl_val = QLabel(valor_ini)
        lbl_val.setStyleSheet(QSS_KPI + f" color: {color_acento}; font-size: 18px;")

        lay.addWidget(lbl_tit)
        lay.addWidget(lbl_val)
        return card, lbl_val

    def _toggle_fullscreen(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_fullscreen.setText("🗖 PANTALLA COMPLETA")
        else:
            self.showMaximized()
            self.btn_fullscreen.setText("🗗 RESTAURAR")

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMaximized():
                self.btn_fullscreen.setText("🗗 RESTAURAR")
            else:
                self.btn_fullscreen.setText("🗖 PANTALLA COMPLETA")
        super().changeEvent(event)

    def _aplicar_tema(self):
        is_dark = theme_manager.is_dark()
        bg = "#0B1329" if is_dark else "#F8FAFC"
        fg = "#F8FAFC" if is_dark else "#0F172A"
        card_bg = "#1E293B" if is_dark else "#FFFFFF"
        border_col = "#334155" if is_dark else "#E2E8F0"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {fg}; font-family: 'Segoe UI'; }}
            QLabel {{ color: {fg}; }}
            QLineEdit, QComboBox {{ background: {card_bg}; color: {fg}; border: 1px solid {border_col}; }}
            QTableWidget {{ background: {card_bg}; color: {fg}; border: 1px solid {border_col}; gridline-color: {border_col}; }}
            QHeaderView::section {{ background: {'#0F172A' if is_dark else '#F1F5F9'}; color: {fg}; font-weight: bold; border: 1px solid {border_col}; padding: 6px; }}
            QFrame#KpiCard {{ background: {card_bg}; border: 1px solid {border_col}; }}
        """)

    def _cargar_datos_iniciales(self):
        try:
            if not self.conector:
                from src.cerebro_global.auditoria.motor_conector_auditoria import obtener_conector_auditoria
                self.conector = obtener_conector_auditoria()

            # Obtenemos el historial completo del local (hasta 1000 registros para auditoría exhaustiva)
            self.todos_los_registros = self.conector.obtener_historial_ajustes(limite=1000) or []
        except Exception as e:
            self.todos_los_registros = []
            from src.logger import logger
            logger.exception("Error cargando historial de auditoría: %s", e)

        self._poblar_filtros_desplegables()
        self._aplicar_filtros()

    def _poblar_filtros_desplegables(self):
        self.cmb_producto.blockSignals(True)
        self.cmb_usuario.blockSignals(True)

        self.cmb_producto.clear()
        self.cmb_usuario.clear()

        # Recopilar productos únicos
        prods_dict = {}
        usuarios_set = set()

        for r in self.todos_los_registros:
            p_id = str(r.get("producto_id") or "")
            nombre = str(r.get("nombre_producto") or f"ID {p_id}").strip()
            if p_id:
                prods_dict[p_id] = nombre
            user = str(r.get("responsable") or "").strip()
            if user:
                usuarios_set.add(user)

        self.cmb_producto.addItem(f"Todos los productos ({len(prods_dict)})", "")
        # Ordenar productos alfabéticamente
        for pid, nom in sorted(prods_dict.items(), key=lambda x: x[1].upper()):
            self.cmb_producto.addItem(f"{nom} [ID {pid}]", pid)

        self.cmb_usuario.addItem(f"Todos los usuarios ({len(usuarios_set)})", "")
        for u in sorted(usuarios_set):
            self.cmb_usuario.addItem(f"Usuario: {u}", u)

        # Si se abrió desde un producto específico, preseleccionarlo en el combo
        if self.producto_id_filtro is not None:
            pid_target = str(self.producto_id_filtro)
            for idx in range(self.cmb_producto.count()):
                if self.cmb_producto.itemData(idx) == pid_target:
                    self.cmb_producto.setCurrentIndex(idx)
                    break

        self.cmb_producto.blockSignals(False)
        self.cmb_usuario.blockSignals(False)

    def _aplicar_filtros(self):
        txt = self.txt_buscar.text().strip().lower()
        prod_id_sel = str(self.cmb_producto.currentData() or "")
        user_sel = str(self.cmb_usuario.currentData() or "")
        tipo_dif = self.cmb_dif.currentData() or "todos"

        filtrados = []
        for r in self.todos_los_registros:
            # 1. Filtro por producto
            r_pid = str(r.get("producto_id") or "")
            if prod_id_sel and r_pid != prod_id_sel:
                continue

            # 2. Filtro por usuario
            r_user = str(r.get("responsable") or "")
            if user_sel and r_user != user_sel:
                continue

            # 3. Filtro por diferencia
            try:
                dif = float(r.get("diferencia") or 0.0)
            except (TypeError, ValueError):
                dif = 0.0

            if tipo_dif == "faltantes" and dif >= -0.0001:
                continue
            if tipo_dif == "sobrantes" and dif <= 0.0001:
                continue
            if tipo_dif == "ceros" and abs(dif) > 0.0001:
                continue

            # 4. Filtro por texto libre
            if txt:
                nom = str(r.get("nombre_producto") or "").lower()
                cod = str(r.get("codigo") or "").lower()
                mot = str(r.get("motivo") or "").lower()
                user = r_user.lower()
                if not (txt in nom or txt in cod or txt in r_pid.lower() or txt in user or txt in mot):
                    continue

            filtrados.append(r)

        self.registros_filtrados = filtrados
        self._renderizar_tabla()
        self._actualizar_kpis()

    def _renderizar_tabla(self):
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)

        is_dark = theme_manager.is_dark()

        for i, r in enumerate(self.registros_filtrados):
            self.tabla.insertRow(i)

            fecha = str(r.get("fecha") or "")
            p_id = str(r.get("producto_id") or "")
            codigo = str(r.get("codigo") or "")
            nombre = str(r.get("nombre_producto") or f"ID {p_id}")
            usuario = str(r.get("responsable") or "")

            try:
                stock_ant = float(r.get("stock_sistema") or 0.0)
            except (TypeError, ValueError):
                stock_ant = 0.0

            try:
                stock_nue = float(r.get("stock_fisico") or 0.0)
            except (TypeError, ValueError):
                stock_nue = 0.0

            try:
                dif = float(r.get("diferencia") or 0.0)
            except (TypeError, ValueError):
                dif = 0.0

            motivo = str(r.get("motivo") or "")

            # 0. Fecha
            it_fecha = QTableWidgetItem(fecha)
            vestir_id(it_fecha)
            it_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 0, it_fecha)

            # 1. ID
            it_id = QTableWidgetItem(p_id)
            vestir_id(it_id)
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 1, it_id)

            # 2. Código
            it_cod = QTableWidgetItem(codigo)
            vestir_id(it_cod)
            it_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 2, it_cod)

            # 3. Nombre
            it_nom = QTableWidgetItem(nombre)
            vestir_nombre(it_nom)
            self.tabla.setItem(i, 3, it_nom)

            # 4. Usuario
            it_user = QTableWidgetItem(usuario)
            vestir_nombre(it_user)
            it_user.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 4, it_user)

            # 5. Stock Anterior
            it_ant = QTableWidgetItem(f"{stock_ant:.3f}")
            vestir_numero(it_ant)
            it_ant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 5, it_ant)

            # 6. Stock Nuevo
            it_nue = QTableWidgetItem(f"{stock_nue:.3f}")
            vestir_numero(it_nue)
            it_nue.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 6, it_nue)

            # 7. Diferencia con color inteligente
            dif_signo = f"+{dif:.3f}" if dif > 0 else f"{dif:.3f}"
            it_dif = QTableWidgetItem(dif_signo)
            vestir_numero(it_dif)
            it_dif.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if dif < -0.0001:
                # Faltante: Rojo
                it_dif.setForeground(QBrush(QColor("#EF4444" if is_dark else "#DC2626")))
                it_dif.setBackground(QBrush(QColor(239, 68, 68, 25 if is_dark else 35)))
            elif dif > 0.0001:
                # Sobrante: Verde
                it_dif.setForeground(QBrush(QColor("#10B981" if is_dark else "#16A34A")))
                it_dif.setBackground(QBrush(QColor(16, 185, 129, 25 if is_dark else 35)))
            else:
                # Cero
                it_dif.setForeground(QBrush(QColor("#94A3B8")))

            self.tabla.setItem(i, 7, it_dif)

            # 8. Motivo
            it_mot = QTableWidgetItem(motivo)
            vestir_nombre(it_mot)
            self.tabla.setItem(i, 8, it_mot)

        self.tabla.blockSignals(False)

        total_mostrados = len(self.registros_filtrados)
        total_bd = len(self.todos_los_registros)
        self.lbl_estado_filas.setText(
            f"Mostrando {total_mostrados} de {total_bd} ajustes registrados en la base de datos."
        )

    def _actualizar_kpis(self):
        total_movs = len(self.registros_filtrados)
        prods_unicos = set()
        faltante_acum = 0.0
        sobrante_acum = 0.0

        for r in self.registros_filtrados:
            pid = r.get("producto_id")
            if pid:
                prods_unicos.add(pid)
            try:
                dif = float(r.get("diferencia") or 0.0)
            except (TypeError, ValueError):
                dif = 0.0

            if dif < 0:
                faltante_acum += dif
            elif dif > 0:
                sobrante_acum += dif

        self.val_total.setText(str(total_movs))
        self.val_prods.setText(str(len(prods_unicos)))
        self.val_falt.setText(f"{faltante_acum:.3f}")
        self.val_sobr.setText(f"+{sobrante_acum:.3f}" if sobrante_acum > 0 else "0.000")

    def _limpiar_filtros(self):
        self.txt_buscar.clear()
        self.cmb_producto.setCurrentIndex(0)
        self.cmb_usuario.setCurrentIndex(0)
        self.cmb_dif.setCurrentIndex(0)

    def _exportar_csv(self):
        if not self.registros_filtrados:
            QMessageBox.information(self, "Exportar", "No hay datos filtrados para exportar.")
            return

        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        sug_nombre = f"historial_auditoria_stock_{fecha_str}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Historial de Auditoría (CSV / Excel)",
            sug_nombre,
            "Archivos CSV (*.csv);;Todos los archivos (*.*)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Fecha y Hora", "ID / PLU", "Código", "Producto",
                    "Usuario Responsable", "Stock Anterior", "Stock Nuevo", "Diferencia", "Motivo"
                ])
                for r in self.registros_filtrados:
                    writer.writerow([
                        r.get("fecha", ""),
                        r.get("producto_id", ""),
                        r.get("codigo", ""),
                        r.get("nombre_producto", ""),
                        r.get("responsable", ""),
                        f"{float(r.get('stock_sistema') or 0):.3f}",
                        f"{float(r.get('stock_fisico') or 0):.3f}",
                        f"{float(r.get('diferencia') or 0):.3f}",
                        r.get("motivo", "")
                    ])
            QMessageBox.information(
                self,
                "Exportación Exitosa",
                f"✅ Se exportaron con éxito {len(self.registros_filtrados)} registros a:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el archivo: {e}")
