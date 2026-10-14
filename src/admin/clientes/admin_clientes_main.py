from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QMessageBox, QDialog,
                             QFormLayout, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

from src.admin.clientes.componentes.metric_card import MetricCard
from src.admin.clientes.componentes.dialogo_nuevo_cliente import DialogoNuevoCliente
from src.admin.clientes.componentes.dialogo_recalculo_fiado import DialogoRecalculoFiado
from src.admin.clientes.componentes.dialogo_editar_cliente import DialogoEditarCliente
from src.admin.clientes.componentes.dialogo_historial_cliente import DialogoHistorialCliente
from src.admin.clientes.componentes.dialogo_cobros import DialogoCobros
from src.admin.clientes.componentes.dialogo_cuadre import DialogoCuadre

class AdminClientes(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.db = db_manager
        self.initUI()

    def initUI(self):
        self.setStyleSheet(f"background: {_CLI['bg']};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)

        # Header
        header_lay = QHBoxLayout()

        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {_CLI['text']}; font-weight: 800; border-radius: 10px;
                padding: 10px 20px; border: 1px solid {_CLI['border']}; font-size: 12px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {_CLI['accent_light']}; color: {_CLI['accent']}; border-color: #BFDBFE; }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)

        header_lay.addWidget(btn_back)
        header_lay.addSpacing(15)

        lbl_titulo = QLabel("💎 CARTERA DE CLIENTES Y CRÉDITO")
        lbl_titulo.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {_CLI['text']}; letter-spacing: 0.5px; border: none;"
        )

        self.btn_nuevo = QPushButton("+ NUEVO CLIENTE")
        self.btn_nuevo.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background: {_CLI['accent']};
                color: white; padding: 12px 24px; font-weight: 900; border-radius: 10px; font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{ background: {_CLI['accent_hover']}; }}
        """)
        self.btn_nuevo.clicked.connect(self.nuevo_cliente)

        header_lay.addWidget(lbl_titulo)
        header_lay.addSpacing(12)

        from src.central_red_global.motor_red import MotorRed
        motor_red = MotorRed()
        st = motor_red.obtener_estado_red()
        if st.get("is_master", True):
            badge_txt = "🖥️ BD Maestra (Servidor)"
            badge_css = "background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; font-size: 11px; font-weight: bold; border-radius: 8px; padding: 5px 12px;"
        else:
            host_ip = st.get("db_host", "LAN")
            badge_txt = f"⚡ Sincronizado en Tiempo Real con Maestra ({host_ip})"
            badge_css = "background: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; font-size: 11px; font-weight: bold; border-radius: 8px; padding: 5px 12px;"

        self.lbl_red_status = QLabel(badge_txt)
        self.lbl_red_status.setStyleSheet(badge_css)
        header_lay.addWidget(self.lbl_red_status)

        self.btn_planilla = QPushButton("PLANILLA DE COBROS")
        self.btn_planilla.setCursor(Qt.PointingHandCursor)
        self.btn_planilla.setStyleSheet(f"""
            QPushButton {{
                background: white; color: #047857; font-weight: 900; border-radius: 10px;
                padding: 12px 18px; border: 1px solid #A7F3D0; font-size: 13px;
            }}
            QPushButton:hover {{ background: #ECFDF5; }}
        """)
        self.btn_planilla.clicked.connect(self._abrir_cobros)

        self.btn_auditoria = QPushButton("AUDITORÍA")
        self.btn_auditoria.setCursor(Qt.PointingHandCursor)
        self.btn_auditoria.setToolTip("Quién creó o cambió cada cliente, en qué PC y cuándo")
        self.btn_auditoria.setStyleSheet("""
            QPushButton {
                background: white; color: #1E40AF; font-weight: 900; border-radius: 10px;
                padding: 12px 18px; border: 1px solid #BFDBFE; font-size: 13px;
            }
            QPushButton:hover { background: #EFF6FF; }
        """)
        self.btn_auditoria.clicked.connect(self._abrir_auditoria)

        header_lay.addStretch()
        header_lay.addWidget(self.btn_auditoria)
        header_lay.addSpacing(10)
        header_lay.addWidget(self.btn_planilla)
        header_lay.addSpacing(10)
        header_lay.addWidget(self.btn_nuevo)
        lay.addLayout(header_lay)

        # Tarjetas 3D
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)
        self.card_deuda = MetricCard("Deuda Total en la Calle", "💸", "#EF4444")
        self.card_activos = MetricCard("Deudores Activos", "👥", "#3B82F6")
        self.card_mayor = MetricCard("Mayor Deuda", "🏆", "#F59E0B")
        self.card_cobros = MetricCard("Cobros", "💵", "#059669")
        cards_lay.addWidget(self.card_deuda)
        cards_lay.addWidget(self.card_activos)
        cards_lay.addWidget(self.card_mayor)
        cards_lay.addWidget(self.card_cobros)
        lay.addLayout(cards_lay)

        self.aviso_cuadre = QFrame()
        self.aviso_cuadre.setStyleSheet(
            "background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 12px;"
        )
        aviso_lay = QHBoxLayout(self.aviso_cuadre)
        aviso_lay.setContentsMargins(16, 10, 16, 10)
        self.lbl_cuadre = QLabel("")
        self.lbl_cuadre.setStyleSheet(
            "color: #92400E; font-weight: 800; font-size: 13px; background: transparent; border: none;"
        )
        self.btn_cuadre = QPushButton("CUADRAR")
        self.btn_cuadre.setCursor(Qt.PointingHandCursor)
        self.btn_cuadre.setStyleSheet(
            "background: #B45309; color: white; font-weight: 900; border: none; "
            "border-radius: 8px; padding: 8px 14px;"
        )
        self.btn_cuadre.clicked.connect(self._abrir_cuadre)
        aviso_lay.addWidget(self.lbl_cuadre)
        aviso_lay.addStretch()
        aviso_lay.addWidget(self.btn_cuadre)
        self.aviso_cuadre.hide()
        lay.addWidget(self.aviso_cuadre)

        # Tabla
        panel_tabla = QFrame()
        panel_tabla.setStyleSheet(
            f"background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px;"
        )
        pt_lay = QVBoxLayout(panel_tabla)
        pt_lay.setContentsMargins(20, 20, 20, 20)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre o DNI...")
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px 16px; border: 1px solid {_CLI['border']}; border-radius: 10px;
                font-size: 14px; background: {_CLI['row_alt']}; color: {_CLI['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {_CLI['accent']}; background: white;
            }}
        """)
        self.txt_buscar.textChanged.connect(self.cargar_clientes)
        pt_lay.addWidget(self.txt_buscar)

        from PyQt6.QtWidgets import QButtonGroup
        self._filtro = "todos"
        self._chips = {}
        chips_lay = QHBoxLayout()
        chips_lay.setSpacing(8)
        chips_lay.setContentsMargins(0, 6, 0, 2)
        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for clave, color in (("todos", "#334155"), ("deuda", "#DC2626"), ("al_dia", "#059669"),
                             ("favor", "#2563EB"), ("express", "#D97706")):
            chip = QPushButton()
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet(f"""
                QPushButton {{
                    background: white; color: {color}; border: 1px solid {_CLI['border']};
                    border-radius: 16px; padding: 7px 16px; font-weight: 800; font-size: 12px;
                }}
                QPushButton:hover {{ border-color: {color}; }}
                QPushButton:checked {{ background: {color}; color: white; border-color: {color}; }}
            """)
            chip.clicked.connect(lambda _=False, c=clave: self._elegir_filtro(c))
            grupo.addButton(chip)
            chips_lay.addWidget(chip)
            self._chips[clave] = chip
        self._chips["todos"].setChecked(True)
        chips_lay.addStretch()
        pt_lay.addLayout(chips_lay)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "DNI", "Tipo", "Límite", "Deuda", "Disponible",
            "Días", "Recálculo", "Acciones",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self.tabla.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(8, 135)
        self.tabla.setColumnWidth(9, 240)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(54)
        self.tabla.horizontalHeader().setMinimumHeight(46)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 13px; gridline-color: transparent;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']};
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 14px 10px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 11px;
                border-bottom: 2px solid {_CLI['accent']};
            }}
            QTableWidget::item {{ padding: 14px 10px; }}
            QTableWidget::item:selected {{ background: {_CLI['accent_light']}; color: #1E40AF; }}
        """)
        self.tabla.setToolTip("Clic en una fila para ver el historial del cliente")
        self.tabla.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tabla.cellClicked.connect(self._on_fila_cliente_clic)
        pt_lay.addWidget(self.tabla)
        lay.addWidget(panel_tabla)

        self.cargar_clientes()

    @staticmethod
    def _categoria(ficha):
        deuda = float(ficha.get("deuda_actual") or 0)
        if deuda > 0.009:
            return "deuda"
        if deuda < -0.009:
            return "favor"
        return "al_dia"

    def _elegir_filtro(self, clave):
        self._filtro = clave
        self.cargar_clientes()

    def _pintar_chips(self, fichas):
        cuentas = {"todos": len(fichas), "deuda": 0, "al_dia": 0, "favor": 0, "express": 0}
        for f in fichas:
            cuentas[self._categoria(f)] += 1
            if (f.get("tipo_cliente") or "").lower() == "express":
                cuentas["express"] += 1
        textos = {
            "todos": "Todos", "deuda": "🔴 Con deuda", "al_dia": "🟢 Al día",
            "favor": "🔵 Saldo a favor", "express": "⚡ Express",
        }
        for clave, chip in self._chips.items():
            chip.setText(f"{textos[clave]} ({cuentas[clave]})")

    def _pasa_filtro(self, ficha):
        if self._filtro == "todos":
            return True
        if self._filtro == "express":
            return (ficha.get("tipo_cliente") or "").lower() == "express"
        return self._categoria(ficha) == self._filtro

    @staticmethod
    def _dias_txt(n):
        return f"{n} día" if abs(n) == 1 else f"{n} días"

    def cargar_clientes(self):
        from src.clientes_fiado.cerebro.cerebro import cerebro
        from src.clientes_fiado.oficina.huella.consulta import huella_texto

        self.tabla.setRowCount(0)
        busqueda = self.txt_buscar.text().strip()
        clientes = cerebro.buscar(busqueda)
        todas = [dict(c) for c in clientes]
        if hasattr(self, "_chips"):
            self._pintar_chips(todas)
        fichas = [f for f in todas if self._pasa_filtro(f)] if hasattr(self, "_chips") else todas
        fechas_cargo = cerebro.ultimos_cargos(
            [
                ficha["id"]
                for ficha in fichas
                if float(ficha.get("deuda_actual") or 0) > 0
            ]
        )

        total_deuda = 0
        deudores = 0
        max_deuda = 0
        for f in todas:
            d = float(f.get("deuda_actual") or 0)
            if d > 0:
                total_deuda += d
                deudores += 1
                max_deuda = max(max_deuda, d)

        if fichas:
            for i, c in enumerate(fichas):
                deuda = float(c.get('deuda_actual') or 0)
                limite = float(c.get('limite_credito') or 0)
                disponible = cerebro.credito_disponible(c)
                dni = (c.get('dni') or '').strip()
                tipo = (c.get('tipo_cliente') or 'regular').lower()
                tipo_txt = "⚡ Express" if tipo == 'express' else "Regular"
                if tipo == 'express' and limite <= 0:
                    limite = FIADO_EXPRESS_LIMITE_DEFAULT
                try:
                    plazo = int(c.get('plazo_dias') or 0)
                except (TypeError, ValueError):
                    plazo = 0

                self.tabla.insertRow(i)
                self.tabla.setRowHeight(i, 58)
                it_id = QTableWidgetItem(str(c['id']))
                it_id.setData(Qt.ItemDataRole.UserRole, int(c['id']))
                self.tabla.setItem(i, 0, it_id)
                nombre_raw = str(c['nombre'] or '')
                nombre_vis = nombre_raw.title() if (nombre_raw.islower() or nombre_raw.isupper()) else nombre_raw
                it_nombre = QTableWidgetItem(nombre_vis)
                it_nombre.setToolTip(huella_texto(c))
                self.tabla.setItem(i, 1, it_nombre)
                self.tabla.setItem(i, 2, QTableWidgetItem(dni or "—"))
                it_tipo = QTableWidgetItem(tipo_txt)
                if tipo == 'express':
                    it_tipo.setForeground(QColor("#059669"))
                    it_tipo.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 3, it_tipo)
                self.tabla.setItem(i, 4, QTableWidgetItem(f"${limite:,.2f}"))

                if deuda > 0.009:
                    it_deuda = QTableWidgetItem(f"${deuda:,.2f}")
                    it_deuda.setForeground(QColor("#EF4444"))
                    it_deuda.setFont(QFont("Arial", 10, QFont.Bold))
                elif deuda < -0.009:
                    it_deuda = QTableWidgetItem(f"+${abs(deuda):,.2f} a favor")
                    it_deuda.setForeground(QColor("#2563EB"))
                    it_deuda.setFont(QFont("Arial", 10, QFont.Bold))
                else:
                    it_deuda = QTableWidgetItem("$0.00")
                    it_deuda.setForeground(QColor("#64748B"))
                self.tabla.setItem(i, 5, it_deuda)

                it_disp = QTableWidgetItem(f"${disponible:,.2f}")
                if disponible <= 0:
                    it_disp.setForeground(QColor("#DC2626"))
                elif disponible < limite * 0.2:
                    it_disp.setForeground(QColor("#F59E0B"))
                self.tabla.setItem(i, 6, it_disp)

                # Días: sin plazo = días corridos desde el último cargo.
                # Con plazo = cuenta regresiva; después del día 0 sigue en -1, -2… (vencido).
                if deuda > 0.009:
                    dias_corridos = 0
                    ultima_compra = fechas_cargo.get(c["id"])
                    if ultima_compra:
                        try:
                            dt = datetime.strptime(str(ultima_compra).split('.')[0], "%Y-%m-%d %H:%M:%S")
                            dias_corridos = (datetime.now() - dt).days
                        except Exception:
                            pass
                    if plazo > 0:
                        restan = plazo - dias_corridos
                        if restan > 0:
                            it_dias = QTableWidgetItem(f"⏳ {self._dias_txt(restan)}")
                            it_dias.setForeground(QColor("#D97706" if restan <= 3 else "#0F766E"))
                        elif restan == 0:
                            it_dias = QTableWidgetItem("⚠ Vence hoy")
                            it_dias.setForeground(QColor("#D97706"))
                        else:
                            it_dias = QTableWidgetItem(f"🔴 {self._dias_txt(restan)}")
                            it_dias.setForeground(QColor("#DC2626"))
                        it_dias.setFont(QFont("Arial", 10, QFont.Bold))
                        it_dias.setToolTip(f"Plazo {plazo} días · {self._dias_txt(dias_corridos)} desde el último cargo")
                    else:
                        it_dias = QTableWidgetItem(self._dias_txt(dias_corridos))
                        if dias_corridos > 30:
                            it_dias.setForeground(QColor("#DC2626"))
                            it_dias.setFont(QFont("Arial", 10, QFont.Bold))
                        it_dias.setToolTip("Sin plazo: días corridos desde el último cargo")
                elif deuda < -0.009:
                    it_dias = QTableWidgetItem("A favor")
                    it_dias.setForeground(QColor("#2563EB"))
                else:
                    it_dias = QTableWidgetItem("Al día")
                    it_dias.setForeground(QColor("#059669"))
                self.tabla.setItem(i, 7, it_dias)

                btn_sim = QPushButton("🔄 Recalcular")
                btn_sim.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_sim.setFixedHeight(32)
                btn_sim.setToolTip("Simula precios de hoy y un % de financiación. No cambia la deuda.")
                btn_sim.setStyleSheet(
                    "background-color: #F8FAFC; color: #2563EB; border: 1px solid #CBD5E1; "
                    "font-weight: bold; border-radius: 6px; padding: 4px 10px; font-size: 12px;"
                )
                btn_sim.clicked.connect(
                    lambda ch, cid=c['id'], cnom=c['nombre']: self._abrir_recalculo(cid, cnom)
                )
                self.tabla.setCellWidget(i, 8, btn_sim)

                acc_w = QWidget()
                acc_lay = QHBoxLayout(acc_w)
                acc_lay.setContentsMargins(4, 2, 4, 2)
                acc_lay.setSpacing(6)

                btn_abonar = QPushButton("Abonar")
                btn_abonar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_abonar.setFixedHeight(32)
                btn_abonar.setMinimumWidth(68)
                btn_abonar.setToolTip(
                    "Cobra aunque no haya deuda: el excedente queda saldo a favor."
                )
                btn_abonar.setStyleSheet(
                    "background-color: #3B82F6; color: white; border-radius: 6px; "
                    "padding: 4px 10px; font-size: 12px; font-weight: bold; border: none;"
                )
                btn_abonar.clicked.connect(
                    lambda ch, cid=c['id'], cnom=c['nombre'], cdeu=deuda: self.abonar_deuda_admin(cid, cnom, cdeu)
                )
                acc_lay.addWidget(btn_abonar)

                btn_limite = QPushButton("Límite")
                btn_limite.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_limite.setFixedHeight(32)
                btn_limite.setMinimumWidth(62)
                btn_limite.setToolTip("Ampliar cupo de fiado (Express o habitual)")
                btn_limite.setStyleSheet(
                    "background-color: #10B981; color: white; border-radius: 6px; "
                    "padding: 4px 8px; font-size: 12px; font-weight: bold; border: none;"
                )
                btn_limite.clicked.connect(
                    lambda ch, cid=c['id'], cnom=c['nombre'], lim=limite: self.editar_limite_credito(cid, cnom, lim)
                )
                acc_lay.addWidget(btn_limite)

                btn_editar = QPushButton("✏️ Editar")
                btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_editar.setFixedHeight(32)
                btn_editar.setMinimumWidth(68)
                btn_editar.setToolTip("Editar nombre, DNI, teléfono, dirección y perfil")
                btn_editar.setStyleSheet(
                    "background-color: #F59E0B; color: white; border-radius: 6px; "
                    "padding: 4px 8px; font-size: 12px; font-weight: bold; border: none;"
                )
                btn_editar.clicked.connect(
                    lambda ch, cid=c['id']: self._abrir_editar_cliente(cid)
                )
                acc_lay.addWidget(btn_editar)

                self.tabla.setCellWidget(i, 9, acc_w)

        self.card_deuda.set_valor(total_deuda, True)
        self.card_activos.set_valor(deudores)
        self.card_mayor.set_valor(max_deuda, True)
        self.card_cobros.set_valor(cerebro.total_cobros(), True)
        self._pintar_cuadre()

    def _pintar_cuadre(self):
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            huecos = cerebro.ventas_sin_cargo()
        except Exception:
            huecos = []
        if not huecos:
            self.aviso_cuadre.hide()
            return
        total = sum(float(fila.get("total") or 0) for fila in huecos)
        self.lbl_cuadre.setText(
            f"{len(huecos)} ventas a crédito sin cargo en la cuenta  ·  ${total:,.2f}"
        )
        self.aviso_cuadre.show()

    def _abrir_cuadre(self):
        if qt_exec(DialogoCuadre(self)):
            self.cargar_clientes()

    def _abrir_cobros(self):
        qt_exec(DialogoCobros(self))

    def _abrir_auditoria(self):
        from src.admin.clientes.componentes.dialogo_auditoria_clientes import DialogoAuditoriaClientes

        qt_exec(DialogoAuditoriaClientes(self))

    def _on_fila_cliente_clic(self, row, col):
        """Abre historial al clic en datos del cliente (no en botones de acción)."""
        if col >= 8:
            return
        item = self.tabla.item(row, 0)
        if not item:
            return
        cliente_id = item.data(Qt.ItemDataRole.UserRole)
        if cliente_id is None:
            try:
                cliente_id = int(item.text())
            except (TypeError, ValueError):
                return
        self._abrir_historial_cliente(int(cliente_id))

    def _abrir_historial_cliente(self, cliente_id):
        dlg = DialogoHistorialCliente(cliente_id, self)
        qt_exec(dlg)
        self.cargar_clientes()

    def _abrir_editar_cliente(self, cliente_id):
        dlg = DialogoEditarCliente(cliente_id, self)
        if qt_exec(dlg):
            self.cargar_clientes()

    def _abrir_recalculo(self, cliente_id, nombre):
        dlg = DialogoRecalculoFiado(cliente_id, nombre, self)
        qt_exec(dlg)

    def nuevo_cliente(self):
        dlg = DialogoNuevoCliente(self)
        if qt_exec(dlg):
            data = dlg.get_data()
            nombre = (data.get('nombre') or '').strip()
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
                return
            dni = data.get('dni')

            # Verificar si existe cliente por DNI o Nombre
            from src.clientes_fiado.cerebro.cerebro import cerebro

            existente_dni = cerebro.buscar_por_dni(dni) if dni else None
            existente_nombre = cerebro.buscar_por_nombre(nombre)
            existente = existente_dni or existente_nombre

            if existente:
                resp = QMessageBox.question(
                    self,
                    "Cliente Existente",
                    f"Ya existe un cliente registrado como '{existente['nombre']}'.\n\n"
                    f"¿Desea actualizar los datos de este cliente existente en lugar de duplicarlo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if resp == QMessageBox.StandardButton.Yes:
                    cerebro.actualizar_existente(
                        existente["id"],
                        nombre,
                        data["telefono"],
                        data["limite_credito"],
                        dni or existente.get("dni"),
                    )
                    self.cargar_clientes()
                    return
                else:
                    return

            cerebro.alta_regular(nombre, data["telefono"], data["limite_credito"], dni)
            self.cargar_clientes()

    def editar_limite_credito(self, cliente_id, nombre, limite_actual):
        from PyQt6.QtWidgets import QInputDialog
        nuevo, ok = QInputDialog.getDouble(
            self,
            "Límite de crédito",
            f"Cliente: {nombre}\nLímite actual: ${limite_actual:,.2f}\n\nNuevo límite ($):",
            limite_actual,
            0,
            99_999_999,
            2,
        )
        if ok and nuevo >= 0:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            cerebro.fijar_limite(cliente_id, nuevo)
            QMessageBox.information(self, "Listo", f"Límite actualizado a ${nuevo:,.2f}")
            self.cargar_clientes()

    def abonar_deuda_admin(self, cliente_id, nombre, deuda_actual):
        from src.utils.qt_compat import qt_exec
        from src.cajero.f6_centro_cobranzas import DialogoCentroCobranzas
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cliente = cerebro.obtener(cliente_id) or {
            "id": cliente_id,
            "nombre": nombre,
            "deuda_actual": deuda_actual,
        }
        dlg = DialogoCentroCobranzas(parent=self, perfil="Admin")
        dlg.abrir_para_cliente(cliente)
        if not (qt_exec(dlg) and dlg.monto_ingresado > 0 and dlg.cliente_id):
            return
        resultado = getattr(dlg, "resultado", None)
        if resultado is None or not getattr(resultado, "ok", False):
            return
        saldo = float(getattr(resultado, "saldo", 0) or 0)
        if saldo < -0.009:
            extra = f"Saldo a favor ${abs(saldo):,.2f}"
        else:
            extra = f"Saldo ${saldo:,.2f}"
        QMessageBox.information(
            self,
            "Cobro",
            f"Cobro asentado · {getattr(resultado, 'nombre', None) or nombre}\n"
            f"Pago ${float(getattr(resultado, 'monto', 0) or 0):,.2f} · {extra}",
        )
        try:
            win = self.window()
            pantallas = getattr(win, "screens", None) or []
            ventas = pantallas[1] if len(pantallas) > 1 else None
            if ventas is not None and hasattr(ventas, "_refrescar_notificaciones"):
                ventas._refrescar_notificaciones()
        except Exception:
            pass
        self.cargar_clientes()
