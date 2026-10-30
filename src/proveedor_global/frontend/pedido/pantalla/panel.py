from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame,
    QMessageBox, QTextEdit, QApplication, QDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.config import config
from src.motor_abastecimiento.exportador import generar_texto_whatsapp, mensaje_general
from src.motor_abastecimiento.hilo.hilo import HiloReposicion
from src.motor_inventario.piso.hilo import HiloGuardarPiso
from src.motor_inventario.planilla.orquestador import _cantidad, _motivo
from src.proveedor_global.backend.moneda import texto
from src.proveedor_global.frontend.pedido.vincular.dialogo import DialogoVincularProveedor


def _cuenta_pedido(items) -> int:
    """El bulto que esta vuelta no se compra no suma como artículo del pedido."""
    return sum(
        1 for it in items or []
        if not (it.get("es_formula") and float(it.get("cantidad_a_pedir") or 0) <= 0)
    )


def _del_modo(items, modo: str) -> list:
    """Autónomo es lo suelto. Bulto es la fórmula, con el stock adentro."""
    if modo == "bulto":
        return [it for it in items or [] if it.get("es_formula")]
    return [it for it in items or [] if not it.get("es_formula")]


def _filas_con_stock(items) -> list:
    """El corte queda debajo de la fórmula, con su stock, y no es una línea de compra."""
    salida = []
    for it in items or []:
        salida.append(it)
        for hijo in it.get("adentro") or []:
            salida.append({
                "codigo": hijo.get("codigo") or "",
                "nombre": hijo.get("nombre") or "",
                "stock_actual": hijo.get("stock_actual") or 0,
                "stock_minimo": "",
                "stock_maximo": "",
                "cantidad_a_pedir": 0,
                "motivo": "en_formula",
                "en_formula": True,
                "valor_unitario": 0,
                "presupuesto_linea": 0,
            })
    return salida


class PanelPedidosAutomaticos(QWidget):
    """
    Panel visual para visualizar y emitir órdenes de abastecimiento automáticas.
    Consulta el motor desacoplado src.motor_abastecimiento sin tocar inventario ni cajero.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._datos_resumen = {}
        self._modo = "autonomo"
        self._build_ui()
        self.refrescar_datos()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        modos = QHBoxLayout()
        modos.setSpacing(10)
        self._btn_autonomo = QPushButton("Pedidos autónomos")
        self._btn_bulto = QPushButton("Pedido bulto")
        for btn, modo in ((self._btn_autonomo, "autonomo"), (self._btn_bulto, "bulto")):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda _, m=modo: self._elegir_modo(m))
            modos.addWidget(btn)
        modos.addStretch()
        root.addLayout(modos)
        self._pintar_modos()

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
        left_lay.addWidget(self._fila_reparto())

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
        s_lbl.setObjectName("Sub")
        s_lbl.setStyleSheet("font-size: 10px; color: #94A3B8;")

        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        lay.addWidget(s_lbl)
        return card

    def _abrir_vinculador(self):
        diag = DialogoVincularProveedor(self)
        if diag.exec() == QDialog.DialogCode.Accepted:
            self.refrescar_datos()

    def _elegir_modo(self, modo: str):
        self._modo = modo
        self._pintar_modos()
        self._on_proveedor_selected()

    def _pintar_modos(self):
        activo = """
            QPushButton {
                background: #1D4ED8; color: white; border: none;
                border-radius: 10px; padding: 0 18px; font-weight: 700; font-size: 13px;
            }
        """
        quieto = """
            QPushButton {
                background: #FFFFFF; color: #1E293B; border: 1.5px solid #CBD5E1;
                border-radius: 10px; padding: 0 18px; font-weight: 700; font-size: 13px;
            }
            QPushButton:hover { background: #F8FAFC; }
        """
        self._btn_autonomo.setStyleSheet(activo if self._modo == "autonomo" else quieto)
        self._btn_bulto.setStyleSheet(activo if self._modo == "bulto" else quieto)

    def _mensaje_modo(self, pedidos) -> str:
        filtrados = {}
        for nombre, info in (pedidos or {}).items():
            items = _del_modo(info.get("items"), self._modo)
            if not items:
                continue
            copia = dict(info)
            copia["items"] = items
            filtrados[nombre] = copia
        if not filtrados:
            return "Esta vuelta no hay un bulto para pedir." if self._modo == "bulto" else "✅ El inventario no marca alarma de reposición."
        return mensaje_general(filtrados, config.get("business_name", "Mi Comercio"))

    def refrescar_datos(self):
        """Pide el resumen en un hilo. La ventana no llama al inventario."""
        hilo = getattr(self, "_hilo_reposicion", None)
        if hilo is not None and hilo.isRunning():
            self._refrescar_al_terminar = True
            return
        self._refrescar_al_terminar = False
        self._hilo_reposicion = HiloReposicion(self)
        self._hilo_reposicion.listo.connect(self._pintar_resumen)
        self._hilo_reposicion.start()

    def _pintar_resumen(self, resumen):
        """Pinta lo que el hilo ya trajo. No vuelve a preguntar."""
        if getattr(self, "_refrescar_al_terminar", False):
            self._refrescar_al_terminar = False
            self.refrescar_datos()
            return
        if not isinstance(resumen, dict) or "pedidos" not in resumen:
            return
        try:
            self._datos_resumen = resumen or {}
            self._aplicar_stock()
            articulos = self._datos_resumen.get("total_articulos_faltantes", 0)

            # Llenar Combo de proveedores
            self.cb_proveedor.blockSignals(True)
            self.cb_proveedor.clear()
            pedidos = self._datos_resumen.get("pedidos", {})

            if not pedidos:
                self.cb_proveedor.addItem("Sin faltantes detectados")
                self.tbl_items.setRowCount(0)
                self.txt_whatsapp.setText("✅ El inventario no marca alarma de reposición.")
            else:
                self.cb_proveedor.addItem(f"Todos ({articulos})", "__todos__")
                for prov_nom, info in pedidos.items():
                    cant = info.get("total_items", 0)
                    codigo = info.get("codigo") or ""
                    if str(codigo).upper() == "EN CASA":
                        codigo = ""
                    etiqueta = f"{codigo} · {prov_nom}" if codigo else prov_nom
                    detalle = f"{cant} ítems" if cant else "sin faltantes"
                    self.cb_proveedor.addItem(f"{etiqueta} ({detalle})", prov_nom)
                self.cb_proveedor.setCurrentIndex(0)

            self.cb_proveedor.blockSignals(False)
            self._on_proveedor_selected()

        except Exception as e:
            QMessageBox.warning(self, "Aviso de Motor", f"No se pudo consultar el motor de abastecimiento: {e}")

    def _fila_reparto(self):
        self._caja_reparto = QWidget()
        fila = QHBoxLayout(self._caja_reparto)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(6)
        rotulo = QLabel("Reparto")
        rotulo.setStyleSheet("font-weight: 800; font-size: 13px; color: #1E293B;")
        fila.addWidget(rotulo)
        self._dias_prov = []
        for dia in ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"):
            boton = QPushButton(dia)
            boton.setCheckable(True)
            boton.setFixedHeight(32)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(self._al_marcar_reparto)
            self._dias_prov.append(boton)
            fila.addWidget(boton)
        fila.addStretch(1)
        self._caja_reparto.setVisible(False)
        return self._caja_reparto

    def _aplicar_stock(self):
        from src.proveedor_global.frontend.pedido.sugerir import preparar

        pedidos = self._datos_resumen.get("pedidos") or {}
        preparar(pedidos)
        articulos = 0
        for info in pedidos.values():
            articulos += sum(
                1 for it in info.get("items") or []
                if not (it.get("es_formula") and float(it.get("cantidad_a_pedir") or 0) <= 0)
            )
        self._datos_resumen["total_articulos_faltantes"] = articulos

    def _mostrar_reparto(self, nombre):
        visible = bool(nombre) and nombre != "__todos__"
        self._caja_reparto.setVisible(visible)
        if not visible:
            return
        from src.proveedor_global.frontend.pedido.reparto import dias

        puestos = set(dias(nombre))
        for i, boton in enumerate(self._dias_prov):
            boton.blockSignals(True)
            boton.setChecked(i in puestos)
            boton.blockSignals(False)
            if i in puestos:
                boton.setStyleSheet(
                    "QPushButton { background: #1D4ED8; color: white; border: none; border-radius: 8px; "
                    "font-weight: 700; padding: 0 8px; }"
                )
            else:
                boton.setStyleSheet(
                    "QPushButton { background: white; color: #1E293B; border: 1px solid #CBD5E1; "
                    "border-radius: 8px; font-weight: 700; padding: 0 8px; }"
                )

    def _al_marcar_reparto(self):
        nombre = self.cb_proveedor.currentData()
        if not nombre or nombre == "__todos__":
            return
        from src.proveedor_global.frontend.pedido.reparto import guardar
        from src.proveedor_global.frontend.pedido.sugerir import aplicar_grupo

        guardar(nombre, [i for i, boton in enumerate(self._dias_prov) if boton.isChecked()])
        info = (self._datos_resumen.get("pedidos") or {}).get(nombre)
        if info:
            aplicar_grupo(nombre, info)
        self._on_proveedor_selected()

    def _on_proveedor_selected(self):
        prov_key = self.cb_proveedor.currentData()
        self._mostrar_reparto(prov_key)
        pedidos = self._datos_resumen.get("pedidos", {})
        if prov_key == "__todos__":
            items = []
            for info in pedidos.values():
                items.extend(_del_modo(info.get("items"), self._modo))
            info_prov = {
                "items": items,
                "texto_whatsapp": self._mensaje_modo(pedidos),
            }
        elif not prov_key or prov_key not in pedidos:
            self.tbl_items.setRowCount(0)
            if not pedidos:
                self.txt_whatsapp.setText("✅ El inventario no marca alarma de reposición.")
            self._pintar_kpis()
            return
        else:
            info_prov = dict(pedidos[prov_key])
            items = _del_modo(info_prov.get("items"), self._modo)
            info_prov["items"] = items
            info_prov["texto_whatsapp"] = generar_texto_whatsapp(
                info_prov, config.get("business_name", "Mi Comercio")
            )

        self.tbl_items.blockSignals(True)
        self.tbl_items.setRowCount(0)
        self._filas = _filas_con_stock(items)
        for r_idx, it in enumerate(self._filas):
            self.tbl_items.insertRow(r_idx)
            bruto = float(it.get("cantidad_a_pedir") or 0)
            if it.get("rango"):
                cant = str(it.get("rango"))
            elif it.get("en_formula") or it.get("motivo") == "en_formula":
                cant = "en fórmula"
            elif it.get("motivo") == "stock" and bruto <= 0:
                cant = "corto" if "cero" in str(it.get("porque") or "").lower() else "sin movimiento"
            elif it.get("motivo") == "sin_piso" or bruto <= 0:
                cant = "sin piso" if it.get("motivo") == "sin_piso" else "al piso"
            elif bruto.is_integer():
                cant = str(int(bruto))
            else:
                cant = f"{bruto:g}"
            costo = it.get("valor_unitario", it.get("costo_unitario", 0.0))
            subt = it.get("presupuesto_linea", it.get("costo_estimado_total", 0.0))

            c_item = QTableWidgetItem(str(it.get('codigo', '')))
            n_item = QTableWidgetItem(str(it.get('nombre', '')))
            s_item = QTableWidgetItem(str(it.get('stock_actual', 0)))
            m_item = QTableWidgetItem(str(it.get('stock_minimo', 0)))
            x_item = QTableWidgetItem(str(it.get('stock_maximo', 0)))
            p_item = QTableWidgetItem(str(cant))
            if it.get("en_formula"):
                gris = QColor("#94A3B8")
                for celda in (n_item, s_item, p_item):
                    celda.setForeground(gris)
            else:
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
                libre.setFlags(solo_leer if it.get("en_formula") else editar)

            self.tbl_items.setItem(r_idx, 0, c_item)
            self.tbl_items.setItem(r_idx, 1, n_item)
            self.tbl_items.setItem(r_idx, 2, s_item)
            self.tbl_items.setItem(r_idx, 3, m_item)
            self.tbl_items.setItem(r_idx, 4, x_item)
            self.tbl_items.setItem(r_idx, 5, p_item)
            self.tbl_items.setItem(r_idx, 6, cu_item)
            self.tbl_items.setItem(r_idx, 7, sub_item)

        self.tbl_items.blockSignals(False)
        texto_wa = info_prov.get("texto_whatsapp") or ""
        if not items and self._modo == "bulto":
            texto_wa = "Esta vuelta no hay un bulto para pedir."
        elif not items and prov_key != "__todos__":
            texto_wa = f"{prov_key} no tiene productos bajo el mínimo."
        self.txt_whatsapp.setText(texto_wa)
        self._pintar_kpis()

    def _monto_items(self, items) -> float:
        return round(
            sum(float(it.get("presupuesto_linea", it.get("costo_estimado_total")) or 0) for it in items),
            2,
        )

    def _pintar_kpis(self):
        """Las tres tarjetas siguen el proveedor elegido en el filtro."""
        pedidos = self._datos_resumen.get("pedidos") or {}
        prov_key = self.cb_proveedor.currentData()
        if prov_key and prov_key != "__todos__" and prov_key in pedidos:
            info = pedidos[prov_key]
            items = _del_modo(info.get("items"), getattr(self, "_modo", "autonomo"))
            articulos = _cuenta_pedido(items)
            proveedores = 1
            inversion = self._monto_items(items)
            pie = str(prov_key)
        else:
            items = []
            for info in pedidos.values():
                items.extend(_del_modo(info.get("items"), getattr(self, "_modo", "autonomo")))
            articulos = _cuenta_pedido(items)
            proveedores = sum(
                1 for p in pedidos.values()
                if str(p.get("proveedor") or "").strip().upper() != "SIN PROVEEDOR ASIGNADO"
            )
            inversion = self._monto_items(items)
            pie = ""
        self._poner_kpi(self.kpi_faltantes, str(articulos), pie or "Alarma del inventario")
        self._poner_kpi(self.kpi_proveedores, str(proveedores), pie or "Distribuidores a contactar")
        self._poner_kpi(self.kpi_inversion, texto(inversion), pie or "Presupuesto sugerido")

    def _poner_kpi(self, card, valor, pie):
        numero = card.findChild(QLabel, "Val")
        if numero is not None:
            numero.setText(valor)
        sub = card.findChild(QLabel, "Sub")
        if sub is not None:
            sub.setText(pie)

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

    def _items_visibles(self):
        prov_key = self.cb_proveedor.currentData()
        pedidos = self._datos_resumen.get("pedidos") or {}
        if prov_key == "__todos__":
            items = []
            for info in pedidos.values():
                items.extend(info.get("items") or [])
            return items
        return (pedidos.get(prov_key) or {}).get("items") or []

    def _item_de_fila(self, fila):
        filas = getattr(self, "_filas", None) or self._items_visibles()
        if fila < 0 or fila >= len(filas):
            return None
        item = filas[fila]
        if item.get("en_formula"):
            return None
        return item

    def _al_editar_cantidad(self, fila, columna):
        """La cantidad que escribe el operador reemplaza la del mensaje. No toca el stock."""
        if columna != 5:
            return
        item = self._item_de_fila(fila)
        if item is None:
            return
        celda = self.tbl_items.item(fila, 5)
        if celda is None:
            return
        try:
            cantidad = max(0.0, float(str(celda.text()).strip().replace(",", ".")))
        except ValueError:
            self.tbl_items.blockSignals(True)
            anterior = item.get("cantidad_a_pedir") or 0
            celda.setText(str(int(anterior) if float(anterior).is_integer() else anterior))
            self.tbl_items.blockSignals(False)
            return
        self._publicar_cantidad(fila, item, cantidad)

    def _publicar_cantidad(self, fila, item, cantidad):
        info = {}
        for grupo in (self._datos_resumen.get("pedidos") or {}).values():
            if item in (grupo.get("items") or []):
                info = grupo
                break
        items = info.get("items") or []
        item["cantidad_a_pedir"] = cantidad
        costo = float(item.get("costo_unitario") or 0)
        precio = float(item.get("precio_unitario") or 0)
        base = costo if costo > 0 else precio
        item["valor_unitario"] = base
        item["costo_estimado_total"] = round(cantidad * costo, 2)
        item["presupuesto_linea"] = round(cantidad * base, 2)
        if info:
            info["costo_total_estimado"] = round(
                sum(float(it.get("costo_estimado_total") or 0) for it in items), 2
            )
            info["presupuesto_estimado"] = round(
                sum(float(it.get("presupuesto_linea") or 0) for it in items), 2
            )
            info["texto_whatsapp"] = generar_texto_whatsapp(
                info, config.get("business_name", "Mi Comercio")
            )
        if self.cb_proveedor.currentData() == "__todos__":
            self.txt_whatsapp.setText(
                mensaje_general(
                    self._datos_resumen.get("pedidos") or {},
                    config.get("business_name", "Mi Comercio"),
                )
            )
        else:
            self.txt_whatsapp.setText(info.get("texto_whatsapp") or "")
        self.tbl_items.blockSignals(True)
        sub = self.tbl_items.item(fila, 7)
        if sub is not None:
            sub.setText(texto(item["presupuesto_linea"]))
        self.tbl_items.blockSignals(False)
        self._pintar_kpis()

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
