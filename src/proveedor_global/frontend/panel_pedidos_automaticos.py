import os
import urllib.parse
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QFrame, QMessageBox, QDialog, QLineEdit, QTextEdit,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from src.config import config
from src.motor_abastecimiento import MotorAbastecimiento
from src.motor_abastecimiento.exportador import generar_texto_whatsapp
from src.motor_abastecimiento.hilo.hilo import HiloReposicion
from src.motor_inventario.piso.hilo import HiloGuardarPiso
from src.motor_inventario.planilla.orquestador import _cantidad, _motivo
from src.contabilidad.shared_globals import PAL
from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta
from src.proveedor_global.backend.moneda import texto

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
        QMessageBox.information(
            self, "Proveedor creado",
            f"Quedó {resultado['codigo']}  {resultado['nombre']}.",
        )
        self.accept()


class DialogoVincularProveedor(QDialog):
    """Diálogo modal para asociar departamentos o productos a proveedores."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 Asignar Proveedor a Departamento o Producto")
        self.setFixedSize(480, 460)
        self.setStyleSheet(f"""
            QDialog {{ background: #FFFFFF; font-family: 'Segoe UI', sans-serif; }}
            QLabel {{ font-size: 12px; font-weight: 700; color: #1E293B; }}
            QLineEdit, QComboBox {{
                border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px;
                font-size: 13px; color: #0F172A; background: #F8FAFC;
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1.5px solid #2563EB; background: #FFFFFF; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        lay.addWidget(QLabel("Tipo de Criterio:"))
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Departamento", "Producto ID"])
        lay.addWidget(self.cb_tipo)

        lay.addWidget(QLabel("Valor (Ej: Nombre del Departamento o ID del Producto):"))
        self.txt_valor = QLineEdit()
        self.txt_valor.setPlaceholderText("Ej: LACTEOS, BEBIDAS, o 142")
        lay.addWidget(self.txt_valor)

        fila_prov = QHBoxLayout()
        fila_prov.addWidget(QLabel("Proveedor:"))
        fila_prov.addStretch()
        btn_alta = QPushButton("＋ Id")
        btn_alta.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_alta.setStyleSheet("background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; border-radius: 8px; padding: 6px 12px; font-weight: bold;")
        btn_alta.clicked.connect(self._alta)
        fila_prov.addWidget(btn_alta)
        lay.addLayout(fila_prov)
        self.cb_proveedor = QComboBox()
        lay.addWidget(self.cb_proveedor)
        self.cb_proveedor.currentIndexChanged.connect(self._al_elegir_ficha)

        lay.addWidget(QLabel("Teléfono WhatsApp (opcional, sale de la ficha):"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Ej: 5491122334455")
        lay.addWidget(self.txt_telefono)
        self._cargar_fichas()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_guardar = QPushButton("Guardar Vínculo")
        btn_guardar.setStyleSheet("background: #2563EB; color: white; border: none; border-radius: 8px; padding: 8px 18px; font-weight: bold;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)
        lay.addLayout(btn_box)

    def _cargar_fichas(self, seleccionar_id=None):
        self.cb_proveedor.blockSignals(True)
        self.cb_proveedor.clear()
        for ficha in FichaProveedor.listar():
            self.cb_proveedor.addItem(etiqueta(ficha), ficha)
            if seleccionar_id and ficha["id"] == seleccionar_id:
                self.cb_proveedor.setCurrentIndex(self.cb_proveedor.count() - 1)
        self.cb_proveedor.blockSignals(False)
        self._al_elegir_ficha()

    def _alta(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != QDialog.DialogCode.Accepted or not alta.ficha:
            return
        self._cargar_fichas(alta.ficha["id"])

    def _al_elegir_ficha(self):
        ficha = self.cb_proveedor.currentData()
        if isinstance(ficha, dict):
            self.txt_telefono.setText(ficha.get("telefono") or "")

    def _guardar(self):
        val = self.txt_valor.text().strip()
        ficha = self.cb_proveedor.currentData()
        if not val or not isinstance(ficha, dict):
            QMessageBox.warning(
                self, "Campos incompletos",
                "Elegí un proveedor con id. Si no hay, usá ＋ Id con la maestra conectada.",
            )
            return
        tipo = "departamento" if self.cb_tipo.currentIndex() == 0 else "producto_id"
        tel = self.txt_telefono.text().strip() or ficha.get("telefono") or ""
        ok = MotorAbastecimiento.vincular_proveedor(
            tipo, val, ficha["nombre"], tel, "", ficha["id"],
        )
        if not ok:
            QMessageBox.warning(self, "No se asignó", "La maestra no guardó el vínculo. La copia anterior queda.")
            return
        QMessageBox.information(
            self, "Vínculo guardado",
            f"Se asignó {etiqueta(ficha)} a {tipo} '{val}'.",
        )
        self.accept()


class PanelPedidosAutomaticos(QWidget):
    """
    Panel visual para visualizar y emitir órdenes de abastecimiento automáticas.
    Consulta el motor desacoplado src.motor_abastecimiento sin tocar inventario ni cajero.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._datos_resumen = {}
        self._build_ui()
        self.refrescar_datos()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # ── KPI BAR ──────────────────────────────────────────────────────────
        kpi_bar = QHBoxLayout()
        kpi_bar.setSpacing(14)

        self.kpi_faltantes = self._create_kpi_card("Artículos en Quiebre", "0", "#EF4444", "Alarma del inventario")
        self.kpi_proveedores = self._create_kpi_card("Proveedores con Pedido", "0", "#3B82F6", "Distribuidores a contactar")
        self.kpi_inversion = self._create_kpi_card("Inversión Estimada", texto(0), "#10B981", "Presupuesto sugerido")

        kpi_bar.addWidget(self.kpi_faltantes)
        kpi_bar.addWidget(self.kpi_proveedores)
        kpi_bar.addWidget(self.kpi_inversion)

        # Botones de Acción
        actions_col = QVBoxLayout()
        btn_refresh = QPushButton("🔄 Actualizar Faltantes")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFixedHeight(42)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #1E293B; border: 1.5px solid #CBD5E1;
                border-radius: 10px; padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }
        """)
        btn_refresh.clicked.connect(self.refrescar_datos)
        actions_col.addWidget(btn_refresh)

        btn_vincular = QPushButton("🔗 Asignar Proveedor")
        btn_vincular.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_vincular.setFixedHeight(42)
        btn_vincular.setStyleSheet("""
            QPushButton {
                background: #EEF2FF; color: #4338CA; border: 1.5px solid #C7D2FE;
                border-radius: 10px; padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #E0E7FF; border-color: #818CF8; }
        """)
        btn_vincular.clicked.connect(self._abrir_vinculador)
        actions_col.addWidget(btn_vincular)

        self._btn_guardar_piso = QPushButton("Guardar mínimo y máximo")
        self._btn_guardar_piso.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_guardar_piso.setFixedHeight(42)
        self._btn_guardar_piso.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #14532D; border: 1.5px solid #86EFAC;
                border-radius: 10px; padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #F0FDF4; }
            QPushButton:disabled { color: #94A3B8; border-color: #E2E8F0; }
        """)
        self._btn_guardar_piso.clicked.connect(self._guardar_piso)
        actions_col.addWidget(self._btn_guardar_piso)

        kpi_bar.addLayout(actions_col)
        root.addLayout(kpi_bar)

        # ── CUERPO PRINCIPAL ─────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(16)

        # Panel izquierdo: Selector de proveedor y tabla de productos
        left_box = QFrame()
        left_box.setObjectName("Card")
        left_box.setStyleSheet(f"""
            QFrame#Card {{
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
            }}
        """)
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(18, 18, 18, 18)
        left_lay.setSpacing(12)

        sel_lay = QHBoxLayout()
        lbl_sel = QLabel("Seleccionar Proveedor:")
        lbl_sel.setStyleSheet("font-weight: 800; font-size: 13px; color: #1E293B;")
        sel_lay.addWidget(lbl_sel)

        self.cb_proveedor = QComboBox()
        self.cb_proveedor.setFixedHeight(36)
        self.cb_proveedor.setStyleSheet("""
            QComboBox {
                background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px;
                padding: 0 12px; font-weight: 700; font-size: 13px; color: #0F172A;
            }
        """)
        self.cb_proveedor.currentIndexChanged.connect(self._on_proveedor_selected)
        sel_lay.addWidget(self.cb_proveedor, 1)
        left_lay.addLayout(sel_lay)

        # Tabla de artículos
        self.tbl_items = QTableWidget()
        self.tbl_items.setColumnCount(8)
        self.tbl_items.setHorizontalHeaderLabels([
            "Código", "Producto", "Stock Actual", "Mínimo", "Máximo", "A Pedir", "Costo Unit.", "Subtotal"
        ])
        self.tbl_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_items.cellChanged.connect(self._al_editar_celda)
        self.tbl_items.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF; border: 1px solid #F1F5F9; border-radius: 8px;
                gridline-color: #F8FAFC; font-size: 12px;
            }
            QHeaderView::section {
                background: #F8FAFC; color: #475569; font-weight: 800;
                padding: 8px; border: none; border-bottom: 2px solid #E2E8F0;
            }
        """)
        left_lay.addWidget(self.tbl_items)
        body.addWidget(left_box, 6)

        # Panel derecho: Vista previa de WhatsApp y botones de despacho
        right_box = QFrame()
        right_box.setObjectName("Card")
        right_box.setStyleSheet(f"""
            QFrame#Card {{
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
            }}
        """)
        right_lay = QVBoxLayout(right_box)
        right_lay.setContentsMargins(18, 18, 18, 18)
        right_lay.setSpacing(12)

        lbl_wa = QLabel("📱 Mensaje de WhatsApp Listo:")
        lbl_wa.setStyleSheet("font-weight: 800; font-size: 13px; color: #1E293B;")
        right_lay.addWidget(lbl_wa)

        self.txt_whatsapp = QTextEdit()
        self.txt_whatsapp.setReadOnly(True)
        self.txt_whatsapp.setStyleSheet("""
            QTextEdit {
                background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 10px;
                padding: 12px; font-family: 'Consolas', monospace; font-size: 12px; color: #14532D;
            }
        """)
        right_lay.addWidget(self.txt_whatsapp)

        btn_copiar = QPushButton("📋 Copiar para WhatsApp")
        btn_copiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copiar.setFixedHeight(44)
        btn_copiar.setStyleSheet("""
            QPushButton {
                background: #16A34A; color: #FFFFFF; border: none; border-radius: 10px;
                font-weight: 900; font-size: 13px;
            }
            QPushButton:hover { background: #15803D; }
        """)
        btn_copiar.clicked.connect(self._copiar_whatsapp)
        right_lay.addWidget(btn_copiar)

        body.addWidget(right_box, 4)
        root.addLayout(body)

    def _create_kpi_card(self, title, val, color, sub):
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(84)
        card.setStyleSheet(f"""
            QFrame#Card {{
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
                border-left: 5px solid {color};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 0.5px;")
        v_lbl = QLabel(val)
        v_lbl.setObjectName("Val")
        v_lbl.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color};")
        s_lbl = QLabel(sub)
        s_lbl.setStyleSheet("font-size: 10px; color: #94A3B8;")

        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        lay.addWidget(s_lbl)
        return card

    def _abrir_vinculador(self):
        diag = DialogoVincularProveedor(self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self.refrescar_datos()

    def refrescar_datos(self):
        """Pide el resumen en un hilo. La ventana no llama al inventario."""
        hilo = getattr(self, "_hilo_reposicion", None)
        if hilo is not None and hilo.isRunning():
            return
        self._hilo_reposicion = HiloReposicion(self)
        self._hilo_reposicion.listo.connect(self._pintar_resumen)
        self._hilo_reposicion.start()

    def _pintar_resumen(self, resumen):
        """Pinta lo que el hilo ya trajo. No vuelve a preguntar."""
        try:
            self._datos_resumen = resumen or {}
            articulos = self._datos_resumen.get("total_articulos_faltantes", 0)
            proveedores = self._datos_resumen.get("proveedores_involucrados", 0)
            inversion = self._datos_resumen.get("inversion_total_estimada", 0.0)

            self.kpi_faltantes.findChild(QLabel, "Val").setText(str(articulos))
            self.kpi_proveedores.findChild(QLabel, "Val").setText(str(proveedores))
            self.kpi_inversion.findChild(QLabel, "Val").setText(texto(inversion))

            # Llenar Combo de proveedores
            self.cb_proveedor.blockSignals(True)
            self.cb_proveedor.clear()
            pedidos = self._datos_resumen.get("pedidos", {})

            if not pedidos:
                self.cb_proveedor.addItem("Sin faltantes detectados")
                self.tbl_items.setRowCount(0)
                self.txt_whatsapp.setText("✅ El inventario no marca alarma de reposición.")
            else:
                for prov_nom, info in pedidos.items():
                    cant = info.get("total_items", 0)
                    codigo = info.get("codigo") or ""
                    etiqueta = f"{codigo} · {prov_nom}" if codigo else prov_nom
                    self.cb_proveedor.addItem(f"{etiqueta} ({cant} ítems)", prov_nom)

            self.cb_proveedor.blockSignals(False)
            self._on_proveedor_selected()

        except Exception as e:
            QMessageBox.warning(self, "Aviso de Motor", f"No se pudo consultar el motor de abastecimiento: {e}")

    def _on_proveedor_selected(self):
        prov_key = self.cb_proveedor.currentData()
        pedidos = self._datos_resumen.get("pedidos", {})
        if not prov_key or prov_key not in pedidos:
            self.tbl_items.setRowCount(0)
            if not pedidos:
                self.txt_whatsapp.setText("✅ El inventario no marca alarma de reposición.")
            return

        info_prov = pedidos[prov_key]
        items = info_prov.get("items", [])

        self.tbl_items.blockSignals(True)
        self.tbl_items.setRowCount(0)
        for r_idx, it in enumerate(items):
            self.tbl_items.insertRow(r_idx)
            bruto = float(it.get("cantidad_a_pedir") or 0)
            if it.get("motivo") == "sin_piso" or bruto <= 0:
                cant = "sin piso" if it.get("motivo") == "sin_piso" else "al piso"
            elif bruto.is_integer():
                cant = str(int(bruto))
            else:
                cant = f"{bruto:g}"
            costo = it.get('costo_unitario', 0.0)
            subt = it.get('costo_estimado_total', 0.0)

            c_item = QTableWidgetItem(str(it.get('codigo', '')))
            n_item = QTableWidgetItem(str(it.get('nombre', '')))
            s_item = QTableWidgetItem(str(it.get('stock_actual', 0)))
            m_item = QTableWidgetItem(str(it.get('stock_minimo', 0)))
            x_item = QTableWidgetItem(str(it.get('stock_maximo', 0)))
            p_item = QTableWidgetItem(str(cant))
            p_item.setForeground(QColor("#DC2626"))
            font_b = p_item.font()
            font_b.setBold(True)
            p_item.setFont(font_b)

            cu_item = QTableWidgetItem(texto(costo))
            sub_item = QTableWidgetItem(texto(subt))
            solo_leer = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            editar = solo_leer | Qt.ItemFlag.ItemIsEditable
            for fijo in (c_item, n_item, s_item, cu_item, sub_item):
                fijo.setFlags(solo_leer)
            for libre in (m_item, x_item, p_item):
                libre.setFlags(editar)

            self.tbl_items.setItem(r_idx, 0, c_item)
            self.tbl_items.setItem(r_idx, 1, n_item)
            self.tbl_items.setItem(r_idx, 2, s_item)
            self.tbl_items.setItem(r_idx, 3, m_item)
            self.tbl_items.setItem(r_idx, 4, x_item)
            self.tbl_items.setItem(r_idx, 5, p_item)
            self.tbl_items.setItem(r_idx, 6, cu_item)
            self.tbl_items.setItem(r_idx, 7, sub_item)

        self.tbl_items.blockSignals(False)
        self.txt_whatsapp.setText(info_prov.get("texto_whatsapp", ""))

    def _al_editar_celda(self, fila, columna):
        if columna in (3, 4):
            self._al_editar_piso(fila)
            return
        if columna != 5:
            return
        self._al_editar_cantidad(fila, columna)

    def _al_editar_piso(self, fila):
        """Mínimo y máximo rearman la cantidad y el WhatsApp. Todavía no se guardan."""
        item = self._item_de_fila(fila)
        if item is None:
            return
        try:
            minimo = self._numero_celda(fila, 3)
            maximo = self._numero_celda(fila, 4)
        except ValueError:
            self._restaurar_piso(fila, item)
            return
        if minimo < 0 or maximo < 0 or (maximo > 0 and maximo < minimo):
            self._restaurar_piso(fila, item)
            return
        item["stock_minimo"] = minimo
        item["stock_maximo"] = maximo
        cantidad = _cantidad(float(item.get("stock_actual") or 0), minimo, maximo)
        item["cantidad_a_pedir"] = cantidad
        item["motivo"] = _motivo(float(item.get("stock_actual") or 0), minimo, maximo, cantidad)
        self.tbl_items.blockSignals(True)
        celda = self.tbl_items.item(fila, 5)
        if celda is not None:
            celda.setText(str(int(cantidad) if float(cantidad).is_integer() else cantidad))
        self.tbl_items.blockSignals(False)
        self._publicar_cantidad(fila, item, cantidad)

    def _restaurar_piso(self, fila, item):
        self.tbl_items.blockSignals(True)
        minimo = self.tbl_items.item(fila, 3)
        maximo = self.tbl_items.item(fila, 4)
        if minimo is not None:
            minimo.setText(str(item.get("stock_minimo") or 0))
        if maximo is not None:
            maximo.setText(str(item.get("stock_maximo") or 0))
        self.tbl_items.blockSignals(False)

    def _numero_celda(self, fila, columna) -> float:
        celda = self.tbl_items.item(fila, columna)
        if celda is None:
            raise ValueError
        return float(str(celda.text()).strip().replace(",", "."))

    def _item_de_fila(self, fila):
        prov_key = self.cb_proveedor.currentData()
        info = (self._datos_resumen.get("pedidos") or {}).get(prov_key) or {}
        items = info.get("items") or []
        if fila < 0 or fila >= len(items):
            return None
        return items[fila]

    def _al_editar_cantidad(self, fila, columna):
        """La cantidad que escribe el operador reemplaza la del mensaje. No toca el stock."""
        if columna != 5:
            return
        prov_key = self.cb_proveedor.currentData()
        pedidos = self._datos_resumen.get("pedidos", {})
        info = pedidos.get(prov_key) or {}
        items = info.get("items") or []
        if fila < 0 or fila >= len(items):
            return
        celda = self.tbl_items.item(fila, 5)
        if celda is None:
            return
        try:
            cantidad = max(0.0, float(str(celda.text()).strip().replace(",", ".")))
        except ValueError:
            self.tbl_items.blockSignals(True)
            anterior = items[fila].get("cantidad_a_pedir") or 0
            celda.setText(str(int(anterior) if float(anterior).is_integer() else anterior))
            self.tbl_items.blockSignals(False)
            return
        item = items[fila]
        self._publicar_cantidad(fila, item, cantidad)

    def _publicar_cantidad(self, fila, item, cantidad):
        prov_key = self.cb_proveedor.currentData()
        info = (self._datos_resumen.get("pedidos") or {}).get(prov_key) or {}
        items = info.get("items") or []
        item["cantidad_a_pedir"] = cantidad
        item["costo_estimado_total"] = round(cantidad * float(item.get("costo_unitario") or 0), 2)
        info["costo_total_estimado"] = round(
            sum(float(it.get("costo_estimado_total") or 0) for it in items), 2
        )
        info["texto_whatsapp"] = generar_texto_whatsapp(
            info, config.get("business_name", "Mi Comercio")
        )
        self.txt_whatsapp.setText(info.get("texto_whatsapp") or "")
        self.tbl_items.blockSignals(True)
        sub = self.tbl_items.item(fila, 7)
        if sub is not None:
            sub.setText(texto(item["costo_estimado_total"]))
        self.tbl_items.blockSignals(False)
        inversion = sum(
            float(p.get("costo_total_estimado") or 0)
            for p in (self._datos_resumen.get("pedidos") or {}).values()
        )
        self._datos_resumen["inversion_total_estimada"] = round(inversion, 2)
        valor = self.kpi_inversion.findChild(QLabel, "Val")
        if valor is not None:
            valor.setText(texto(inversion))

    def _guardar_piso(self):
        """Manda piso y techo por el hilo. La ventana no escribe productos."""
        hilo = getattr(self, "_hilo_piso", None)
        if hilo is not None and hilo.isRunning():
            return
        filas = []
        for info in (self._datos_resumen.get("pedidos") or {}).values():
            for it in info.get("items") or []:
                filas.append({
                    "id": it.get("id"),
                    "minimo": it.get("stock_minimo") or 0,
                    "maximo": it.get("stock_maximo") or 0,
                })
        self._btn_guardar_piso.setEnabled(False)
        self._hilo_piso = HiloGuardarPiso(filas, self)
        self._hilo_piso.listo.connect(self._piso_guardado)
        self._hilo_piso.start()

    def _piso_guardado(self, ok, mensaje):
        self._btn_guardar_piso.setEnabled(True)
        if ok:
            QMessageBox.information(self, "Piso guardado", mensaje or "Listo.")
            return
        QMessageBox.warning(self, "No se guardó", mensaje or "El stock sigue igual.")

    def _copiar_whatsapp(self):
        txt = self.txt_whatsapp.toPlainText().strip()
        if not txt or txt.startswith("✅"):
            QMessageBox.information(self, "Sin pedido", "No hay ningún pedido activo para copiar.")
            return
        QApplication.clipboard().setText(txt)
        QMessageBox.information(self, "¡Copiado!", "El pedido ha sido copiado al portapapeles.\nYa podés pegarlo en WhatsApp Web o enviarlo.")
