from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.admin.mercadopago.historial.archivo import leer, omitir
from src.admin.mercadopago.historial.sincronizar import bajar_mes

class Admin10MP(QWidget):
    request_dashboard = pyqtSignal()
    ultimo_pago_detectado = None

    def __init__(self):
        super().__init__()
        self.poller = None
        self.pagos_hoy = []
        self.todos_los_pagos = []
        Admin10MP.vista = self
        self.setup_ui()
        self.cargar_datos_locales()
        self.iniciar_monitor()

    def setup_ui(self):
        self.setStyleSheet(" font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(" background-color: #1e293b; color: white;")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet("background: white;  font-weight: bold; border-radius: 5px; padding: 8px 15px;")
        btn_volver.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_volver)

        hl.addSpacing(20)
        lbl_title = QLabel("Monitor de Mercado Pago (Tiempo Real)")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        hl.addWidget(lbl_title)
        hl.addStretch()
        self.btn_aviso = QPushButton("")
        self.btn_aviso.setCheckable(True)
        self.btn_aviso.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aviso.setStyleSheet(
            "background: white; color: #1e293b; font-weight: bold; border-radius: 8px; padding: 8px 14px;"
        )
        self.btn_aviso.clicked.connect(self._alternar_aviso)
        self._pintar_aviso()
        hl.addWidget(self.btn_aviso)
        hl.addSpacing(12)
        self.btn_sync = QPushButton("Actualizar")
        self.btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync.setStyleSheet(
            "background: white; color: #1e293b; font-weight: bold; border-radius: 8px; padding: 8px 14px;"
        )
        self.btn_sync.clicked.connect(self.sincronizar_historico)
        hl.addWidget(self.btn_sync)
        hl.addSpacing(12)

        # Estado
        self.lbl_estado = QLabel("🔴 DETENIDO")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;   padding: 5px 15px; border-radius: 10px;")
        hl.addWidget(self.lbl_estado)
        layout.addWidget(header)

        # --- BODY ---
        body = QVBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)

        # KPI Dashboard Cards
        kpi_lay = QHBoxLayout()
        kpi_lay.setSpacing(15)

        def create_kpi_card(title, value, color_hex):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 15px;
                }}
            """)

            cl = QVBoxLayout(card)
            cl.setSpacing(5)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-size: 11px; font-weight: 900;  letter-spacing: 1px;")

            lbl_value = QLabel(value)
            lbl_value.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color_hex}; font-family: 'Segoe UI Black';")

            cl.addWidget(lbl_title)
            cl.addWidget(lbl_value)
            return card, lbl_value

        self.card_total_mes, self.lbl_kpi_total_mes = create_kpi_card("📅 ACUMULADO BRUTO MES", "$0.00", "#ea580c")
        self.card_neto_mes, self.lbl_kpi_neto_mes = create_kpi_card("💵 ACUMULADO NETO MES", "$0.00", "#10b981")
        self.card_total, self.lbl_kpi_total = create_kpi_card("💰 RECAUDADO HOY", "$0.00", "#3b82f6")
        self.card_count, self.lbl_kpi_count = create_kpi_card("✅ TRANSACCIONES HOY", "0", "#0284c7")
        self.card_avg, self.lbl_kpi_avg = create_kpi_card("📈 TICKET PROMEDIO", "$0.00", "#f59e0b")

        kpi_lay.addWidget(self.card_total_mes)
        kpi_lay.addWidget(self.card_neto_mes)
        kpi_lay.addWidget(self.card_total)
        kpi_lay.addWidget(self.card_count)
        kpi_lay.addWidget(self.card_avg)

        body.addLayout(kpi_lay)
        body.addSpacing(15)

        # --- FILTROS DE BUSQUEDA ---
        filter_lay = QHBoxLayout()
        filter_lay.setSpacing(10)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por Cliente, ID de Pago o Fecha...")
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00B1EA;
            }
        """)
        self.txt_buscar.textChanged.connect(self.aplicar_filtros)

        from PyQt6.QtWidgets import QComboBox
        self.cmb_fecha = QComboBox()
        self.cmb_fecha.addItems(["Todos los registros", "Solo Hoy", "Este Mes", "Día Específico..."])
        self.cmb_fecha.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        self.cmb_fecha.currentIndexChanged.connect(self.on_combo_fecha_changed)

        from PyQt6.QtCore import QDate
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-width: 120px;
            }
        """)
        self.date_picker.dateChanged.connect(self.aplicar_filtros)
        self.date_picker.hide()

        self.chk_cargas = QCheckBox("Cargas Propias")
        self.chk_cargas.setChecked(False)
        self.chk_cargas.setStyleSheet("""
            QCheckBox {
                font-size: 13px;

                font-weight: bold;
            }
        """)
        self.chk_cargas.stateChanged.connect(self.aplicar_filtros)

        self.chk_omitidos = QCheckBox("Omitidos")
        self.chk_omitidos.setChecked(False)
        self.chk_omitidos.setStyleSheet("""
            QCheckBox {
                font-size: 13px;

                font-weight: bold;
            }
        """)
        self.chk_omitidos.stateChanged.connect(self.aplicar_filtros)

        filter_lay.addWidget(self.txt_buscar, stretch=1)
        filter_lay.addWidget(self.cmb_fecha)
        filter_lay.addWidget(self.date_picker)
        filter_lay.addWidget(self.chk_cargas)
        filter_lay.addWidget(self.chk_omitidos)
        body.addLayout(filter_lay)
        body.addSpacing(10)

        # Tabla de Pagos
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "ID de Pago", "Cliente", "Monto", "Estado", "Ticket"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("background: white; alternate- font-size: 14px;")
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        body.addWidget(self.tabla)

        layout.addLayout(body)


    def iniciar_monitor(self):
        from src.services.mp_escucha import EscuchaMP
        if not EscuchaMP.asegurar():
            self.lbl_estado.setText("SIN TOKEN")
            return
        hilo = EscuchaMP._hilo
        try:
            hilo.new_payment.disconnect(self._guardar_llegada)
        except TypeError:
            pass
        hilo.new_payment.connect(self._guardar_llegada)
        self.lbl_estado.setText("ESCUCHANDO")
        self.sincronizar_historico()

    def sincronizar_historico(self):
        from src.services.mp_escucha import EscuchaMP
        try:
            bajar_mes(EscuchaMP.token())
        except Exception as error:
            print("Error en sincronizacion MP:", error)
        self.cargar_datos_locales()

    def _guardar_llegada(self, pago):
        from src.admin.mercadopago.historial.archivo import guardar
        guardar([pago])
        self.cargar_datos_locales()

    def cargar_datos_locales(self):
        datos = leer()
        self.todos_los_pagos = datos["pagos"]
        self.lbl_kpi_total_mes.setText(f"${datos['total_mes']:,.2f}")
        self.lbl_kpi_neto_mes.setText(f"${datos['neto_mes']:,.2f}")
        self.lbl_kpi_total.setText(f"${datos['total_hoy']:,.2f}")
        self.lbl_kpi_count.setText(str(datos["cant_hoy"]))
        cant = datos["cant_hoy"]
        prom = (datos["total_hoy"] / cant) if cant else 0
        self.lbl_kpi_avg.setText(f"${prom:,.2f}")
        self.aplicar_filtros()

    def aplicar_filtros(self):
        """
        Aplica los filtros de texto, fecha, cargas propias y omitidos a la lista de pagos.
        """
        filtro_texto = self.txt_buscar.text().lower().strip()
        filtro_fecha = self.cmb_fecha.currentText()

        now = datetime.now()
        mes_str = now.strftime("%Y-%m")
        hoy_str = now.strftime("%Y-%m-%d")

        show_cargas = self.chk_cargas.isChecked()
        show_omitidos = self.chk_omitidos.isChecked()

        pagos_filtrados = []
        for p in getattr(self, "todos_los_pagos", []):
            # Filtro por Cargas Propias
            if p["op_type"] == "account_fund" and not show_cargas:
                continue

            # Filtro por Omitidos
            if p["estado"] == "OMITIDO" and not show_omitidos:
                continue

            # Filtro por Fecha
            if filtro_fecha == "Solo Hoy" and not p["fecha"].startswith(hoy_str):
                continue
            if filtro_fecha == "Este Mes" and not p["fecha"].startswith(mes_str):
                continue
            if filtro_fecha == "Día Específico...":
                fecha_sel = self.date_picker.date().toString("yyyy-MM-dd")
                if not p["fecha"].startswith(fecha_sel):
                    continue

            # Filtro por Texto
            if filtro_texto:
                match = (
                    filtro_texto in p["fecha"].lower() or
                    filtro_texto in p["id"].lower() or
                    filtro_texto in p["nombre"].lower() or
                    filtro_texto in p["email"].lower() or
                    filtro_texto in f"${p['monto']:.2f}"
                )
                if not match:
                    continue

            pagos_filtrados.append(p)

        from src.cajero.paso6_cobro.vinculo_mp.libro import asociado

        self.tabla.setRowCount(0)
        for p in pagos_filtrados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(p["fecha"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(p["id"]))

            # Nombre de Cliente o Carga
            nombre_display = p["nombre"]
            if p["op_type"] == "account_fund":
                nombre_display = "Carga de Fondos (Autotransferencia)"
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre_display))

            item_monto = QTableWidgetItem(f"${p['monto']:.2f}")
            item_monto.setForeground(QColor("#059669"))
            item_monto.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.tabla.setItem(row, 3, item_monto)

            if p["op_type"] == "account_fund":
                item_estado = QTableWidgetItem("CARGA DE FONDOS")
                item_estado.setForeground(QColor("#8B5CF6")) # Violeta
            else:
                item_estado = QTableWidgetItem(p["estado"].upper())
                if p["estado"].upper() == "APPROVED":
                    item_estado.setForeground(QColor("#059669"))
                elif p["estado"].upper() == "OMITIDO":
                    item_estado.setForeground(QColor("#94A3B8"))
            self.tabla.setItem(row, 4, item_estado)
            vinculo = asociado(p["id"]) or {}
            self.tabla.setItem(row, 5, QTableWidgetItem(str(vinculo.get("ticket") or "—")))

    def on_combo_fecha_changed(self, index):
        if self.cmb_fecha.currentText() == "Día Específico...":
            self.date_picker.show()
        else:
            self.date_picker.hide()
        self.aplicar_filtros()

    def mostrar_menu_contextual(self, pos):
        item = self.tabla.itemAt(pos)
        if not item: return

        row = self.tabla.row(item)
        id_item = self.tabla.item(row, 1)
        if not id_item: return
        id_pago = id_item.text()

        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)

        pago_actual = None
        for p in self.todos_los_pagos:
            if p["id"] == id_pago:
                pago_actual = p
                break

        if pago_actual:
            es_omitido = (pago_actual.get("estado") == "OMITIDO")

            action_omitir = QAction("🚫 Omitir de Reportes / Ocultar" if not es_omitido else "🔄 Restaurar en Reportes", self)
            action_omitir.triggered.connect(lambda: self.toggle_omitir_pago(id_pago))
            menu.addAction(action_omitir)

            qt_exec(menu, self.tabla.mapToGlobal(pos))


    def toggle_omitir_pago(self, id_pago):
        omitir(id_pago)
        self.cargar_datos_locales()

    def _alternar_aviso(self):
        from src.services.mp_escucha import EscuchaMP
        EscuchaMP.fijar_sonido(self.btn_aviso.isChecked())
        self._pintar_aviso()

    def _pintar_aviso(self):
        from src.services.mp_escucha import EscuchaMP
        activo = EscuchaMP.con_sonido()
        self.btn_aviso.setChecked(activo)
        self.btn_aviso.setText("Con sonido" if activo else "Cajero silencioso")
