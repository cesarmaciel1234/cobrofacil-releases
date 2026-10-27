from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit,
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.jefe.reportes.financiero.dinero import fmt_plata
from src.utils.letra import QSS_KPI, QSS_ROTULO, QSS_TITULO

from src.admin.mercadopago.historial.archivo import leer, omitir
from src.admin.mercadopago.historial.sincronizar import bajar_mes


class _BajadaMes(QThread):
    """Baja el mes y actualiza la copia portable fuera de la ventana."""

    listo = pyqtSignal(int, str, bool)

    def __init__(self, token):
        super().__init__()
        self.token = token

    def run(self):
        try:
            cuantos = bajar_mes(self.token)
        except Exception:
            cuantos = -1
        error_nodo = ""
        nodo_actualizado = False
        if cuantos >= 0:
            try:
                from src.admin.mercadopago.historial.nodo import sincronizar_nodo_configurado

                nodo_actualizado = sincronizar_nodo_configurado()
            except (OSError, ValueError, RuntimeError) as error:
                error_nodo = str(error)
        self.listo.emit(cuantos, error_nodo, nodo_actualizado)


class _SincronizacionNodo(QThread):
    listo = pyqtSignal(str, bool)

    def run(self):
        try:
            from src.admin.mercadopago.historial.nodo import sincronizar_nodo_configurado

            actualizado = sincronizar_nodo_configurado()
        except Exception as error:
            self.listo.emit(str(error), False)
        else:
            self.listo.emit("", actualizado)


class Admin10MP(QWidget):
    request_dashboard = pyqtSignal()
    ultimo_pago_detectado = None

    def __init__(self):
        super().__init__()
        self.todos_los_pagos = []
        Admin10MP.vista = self
        self._marcas_archivos = None
        self._reloj_ticket = QTimer(self)
        self._reloj_ticket.timeout.connect(self._refrescar_si_cambio)
        self._reloj_nodo = QTimer(self)
        self._reloj_nodo.setSingleShot(True)
        self._reloj_nodo.timeout.connect(self._iniciar_sincronizacion_nodo)
        self._nodo_sync_pendiente = False
        self._sync_nodo_thread = None
        self._error_nodo = ""
        self.setup_ui()
        self.cargar_datos_locales(sincronizar_nodo=True)
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
        lbl_title = QLabel("Auditoría de cobros digitales")
        lbl_title.setStyleSheet(f"{QSS_TITULO} color: #FFFFFF; background: transparent;")
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
        self.lbl_estado = QLabel("DETENIDO")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;   padding: 5px 15px; border-radius: 10px;")
        hl.addWidget(self.lbl_estado)
        layout.addWidget(header)

        self.lbl_aviso_esclava = QLabel("")
        self.lbl_aviso_esclava.setWordWrap(True)
        self.lbl_aviso_esclava.setStyleSheet(
            "background: #FEF3C7; color: #92400E; font-size: 13px; font-weight: 700; "
            "padding: 10px 16px; border-bottom: 1px solid #F59E0B;"
        )
        self.lbl_aviso_esclava.hide()
        layout.addWidget(self.lbl_aviso_esclava)

        # --- BODY ---
        body = QVBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)

        kpi_lay = QGridLayout()
        kpi_lay.setSpacing(10)
        kpi_lay.setContentsMargins(0, 0, 0, 0)
        for col in range(4):
            kpi_lay.setColumnStretch(col, 1)

        def create_kpi_card(title, value, color_hex):
            card = QFrame()
            card.setFixedHeight(44)
            card.setStyleSheet(
                "QFrame { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; }"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 4, 12, 4)
            cl.setSpacing(0)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet(
                f"{QSS_ROTULO} color: #0F172A; background: transparent; border: none;"
            )

            lbl_value = QLabel(value)
            lbl_value.setWordWrap(False)
            lbl_value.setStyleSheet(
                f"{QSS_KPI} font-size: 16px; color: {color_hex}; "
                "background: transparent; border: none;"
            )

            lbl_nota = QLabel("")
            lbl_nota.setWordWrap(False)
            lbl_nota.setStyleSheet(
                "font-size: 10px; font-weight: 600; color: #1E293B; "
                "background: transparent; border: none;"
            )
            lbl_nota.hide()

            cl.addWidget(lbl_title)
            cl.addWidget(lbl_value)
            cl.addWidget(lbl_nota)
            card._nota = lbl_nota
            return card, lbl_value

        def hueco():
            f = QFrame()
            f.setFixedHeight(44)
            f.setStyleSheet(
                "QFrame { background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; }"
            )
            lay = QVBoxLayout(f)
            lay.setContentsMargins(12, 4, 12, 4)
            lay.setSpacing(0)
            t = QLabel("RESERVADO")
            t.setStyleSheet(
                f"{QSS_ROTULO} color: #1E293B; background: transparent; border: none;"
            )
            v = QLabel("—")
            v.setStyleSheet(
                f"{QSS_KPI} font-size: 16px; color: #CBD5E1; "
                "background: transparent; border: none;"
            )
            d = QLabel("Espacio para una tarjeta")
            d.setStyleSheet(
                "font-size: 10px; font-weight: 600; color: #1E293B; "
                "background: transparent; border: none;"
            )
            lay.addWidget(t)
            lay.addWidget(v)
            lay.addWidget(d)
            return f

        self.card_total_mes, self.lbl_kpi_total_mes = create_kpi_card("BRUTO MP", "$0,00", "#C2410C")
        self.card_neto_mes, self.lbl_kpi_neto_mes = create_kpi_card("NETO MP", "$0,00", "#047857")
        self.card_total, self.lbl_kpi_total = create_kpi_card("TICKETS DIGITALES", "$0,00", "#1D4ED8")
        self.card_count, self.lbl_kpi_count = create_kpi_card("FIRMADOS EN TICKET", "$0,00", "#047857")
        self.card_avg, self.lbl_kpi_avg = create_kpi_card("SIN FIRMAR / F9", "$0,00", "#B45309")
        self.card_suelto, self.lbl_kpi_suelto = create_kpi_card("MP SIN TICKET", "$0,00", "#B91C1C")
        self.card_cliente, self.lbl_kpi_cliente = create_kpi_card("CLIENTE", "$0,00", "#075985")
        self.card_cancelado, self.lbl_kpi_cancelado = create_kpi_card("CANCELADOS", "$0,00", "#DC2626")

        fila1 = (
            self.card_total_mes,
            self.card_neto_mes,
            self.card_total,
            self.card_count,
        )
        fila2 = (
            self.card_avg,
            self.card_suelto,
            self.card_cliente,
            self.card_cancelado,
        )
        for col, card in enumerate(fila1):
            kpi_lay.addWidget(card, 0, col)
        for col, card in enumerate(fila2):
            kpi_lay.addWidget(card, 1, col)

        body.addLayout(kpi_lay)
        body.addSpacing(15)

        # --- FILTROS DE BUSQUEDA ---
        filter_lay = QHBoxLayout()
        filter_lay.setSpacing(10)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar concepto, ID de pago, ticket de venta o COB-…")
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

        self._periodo = "Hoy"
        self._cruce = "Todos"
        self._cuenta_filtro = ""
        self._gen_vista = -1
        self._botones_periodo = {}
        _idle = (
            "QPushButton { background: #FFFFFF; color: #475569; border: 1px solid #E2E8F0; "
            "border-radius: 14px; padding: 6px 14px; font-weight: 600; }"
            "QPushButton:hover { background: #EEF2FF; color: #4338CA; }"
        )
        _activo = (
            "QPushButton { background: #0F172A; color: #FFFFFF; border: 1px solid #0F172A; "
            "border-radius: 14px; padding: 6px 14px; font-weight: 600; }"
        )
        self._estilo_periodo_idle = _idle
        self._estilo_periodo_activo = _activo
        for texto in ("Hoy", "Semana", "Mes", "Año", "Período"):
            b = QPushButton(texto)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(_activo if texto == "Hoy" else _idle)
            b.clicked.connect(lambda _c=False, t=texto: self._elegir_periodo(t))
            self._botones_periodo[texto] = b

        from PyQt6.QtCore import QDate
        estilo_fecha = """
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-width: 120px;
            }
        """
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-7))
        self.date_desde.setStyleSheet(estilo_fecha)
        self.date_desde.dateChanged.connect(self.aplicar_filtros)
        self.date_desde.hide()
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setStyleSheet(estilo_fecha)
        self.date_hasta.dateChanged.connect(self.aplicar_filtros)
        self.date_hasta.hide()

        self.btn_filtros = QPushButton("Filtros")
        self.btn_filtros.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_filtros.setStyleSheet(_idle)
        self.btn_filtros.clicked.connect(self._abrir_filtros)

        filter_lay.addWidget(self.txt_buscar, stretch=1)
        for texto in ("Hoy", "Semana", "Mes", "Año", "Período"):
            filter_lay.addWidget(self._botones_periodo[texto])
        filter_lay.addWidget(self.date_desde)
        filter_lay.addWidget(self.date_hasta)
        filter_lay.addWidget(self.btn_filtros)
        self.txt_buscar.setPlaceholderText("Buscar titular, concepto, ID de pago, ticket o COB-…")
        body.addLayout(filter_lay)
        self.lbl_reparto = QLabel("")
        self.lbl_reparto.setStyleSheet(
            "QLabel { color: #0F172A; font-size: 13px; font-weight: 700; padding: 2px 2px 0 2px; }"
        )
        self.lbl_reparto.hide()
        body.addWidget(self.lbl_reparto)
        body.addSpacing(10)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "ID de pago", "Cuenta / Token", "Concepto", "Monto", "Estado", "Ticket venta", "Ticket cobro",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                color: #0F172A;
                gridline-color: #E2E8F0;
                font-size: 13px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #F1F5F9;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #334155;
                font-size: 12px;
                font-weight: 700;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #CBD5E1;
            }
        """)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        body.addWidget(self.tabla)
        self.lbl_leyenda = QLabel(
            "Filtros: cruzados, ticket sin id, id sin ticket, y la cuenta del token que estaba activo.  ·  "
            "Sin id de pago no hay cuenta.  ·  Ticket venta = qué se vendió  ·  Ticket cobro = COB-…"
        )
        self.lbl_leyenda.setWordWrap(True)
        self.lbl_leyenda.setStyleSheet(
            "color: #64748B; font-size: 12px; padding: 8px 2px 0 2px; background: transparent;"
        )
        body.addWidget(self.lbl_leyenda)

        layout.addLayout(body)


    def iniciar_monitor(self):
        from src.services.mp_escucha import EscuchaMP
        # Esclava: intenta traer el token de la tienda antes de arrancar
        try:
            from src.central_red_global.sync_tienda.rol import es_esclava
            from src.central_red_global.sync_tienda.mp_token import traer

            if es_esclava():
                traer()
        except Exception:
            pass
        if not EscuchaMP.asegurar():
            self.lbl_estado.setText("SIN TOKEN")
            self._avisar_esclava_sin_token()
            return
        self.lbl_aviso_esclava.hide()
        hilo = EscuchaMP._hilo
        try:
            hilo.new_payment.disconnect(self._guardar_llegada)
        except TypeError:
            pass
        hilo.new_payment.connect(self._guardar_llegada)
        try:
            hilo.error_signal.disconnect(self._error_escucha)
        except TypeError:
            pass
        hilo.error_signal.connect(self._error_escucha)
        self.lbl_estado.setText("ESCUCHANDO")
        self.sincronizar_historico()

    def _avisar_esclava_sin_token(self):
        """Esclava sin token en tienda: la maestra aún no publicó o no hay MariaDB."""
        try:
            from src.config import config

            es_esclava = not bool(config.get("is_master", True))
        except Exception:
            es_esclava = False
        if not es_esclava:
            self.lbl_aviso_esclava.hide()
            return
        try:
            from src.central_red_global.sync_tienda.mp_token import traer

            if traer():
                self.lbl_aviso_esclava.hide()
                return
        except Exception:
            pass
        self.lbl_aviso_esclava.setText(
            "PC esclava · sin token en la tienda — El token MP lo publica la PC maestra "
            "(Configuración → Terminal TPV → Guardar). Se copia solo por MariaDB; "
            "no hace falta pegarlo acá. Ventas y stock ya van a la maestra."
        )
        self.lbl_aviso_esclava.show()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos_locales(sincronizar_nodo=False)
        self._programar_sincronizacion_nodo()
        self._marcas_archivos = self._marcas()
        self._reloj_ticket.start(1000)

    def hideEvent(self, event):
        self._reloj_ticket.stop()
        super().hideEvent(event)

    def sincronizar_historico(self):
        self._programar_sincronizacion_nodo()
        self.cargar_datos_locales(sincronizar_nodo=False)
        self._marcas_archivos = self._marcas()
        bajada = getattr(self, "_bajando", None)
        if bajada is not None and bajada.isRunning():
            return
        from src.services.mp_escucha import EscuchaMP
        token = EscuchaMP.token()
        if not token:
            estado_local = "COPIA LOCAL · NODO PENDIENTE" if self._error_nodo else "SOLO COPIA LOCAL"
            self.lbl_estado.setText(estado_local if self.todos_los_pagos else "SIN TOKEN")
            self.lbl_estado.setToolTip(
                (f"{self._error_nodo} " if self._error_nodo else "")
                + ("Historial disponible sin conexión. Actualizar en línea requiere el token de Mercado Pago."
                   if self.todos_los_pagos else "")
            )
            self._avisar_esclava_sin_token()
            return
        self.lbl_aviso_esclava.hide()
        self.lbl_estado.setToolTip("")
        self.lbl_estado.setText("ACTUALIZANDO")
        self._bajando = _BajadaMes(token)
        self._bajando.listo.connect(self._fin_bajada)
        self._bajando.start()

    def _fin_bajada(self, cuantos, error_nodo, nodo_actualizado):
        self.cargar_datos_locales()
        self._marcas_archivos = self._marcas()
        if cuantos < 0:
            self.lbl_estado.setText(
                "COPIA LOCAL · NODO PENDIENTE"
                if self._error_nodo and self.todos_los_pagos else
                "SIN RED · COPIA LOCAL" if self.todos_los_pagos else "SIN DATOS"
            )
            self.lbl_estado.setToolTip(
                (f"{self._error_nodo} " if self._error_nodo else "")
                + (
                    "No se pudo consultar Mercado Pago. Se muestran los pagos guardados en esta PC."
                    if self.todos_los_pagos else "No se pudo consultar Mercado Pago y no hay historial local."
                )
            )
            return
        self._error_nodo = error_nodo
        self.lbl_estado.setToolTip(error_nodo)
        if error_nodo:
            self.lbl_estado.setText("ACTUALIZADO · NODO PENDIENTE")
        elif nodo_actualizado:
            self.lbl_estado.setText("ACTUALIZADO · NODO OK")
        else:
            self.lbl_estado.setText("ESCUCHANDO")

    def _error_escucha(self, _texto):
        self.lbl_estado.setText(
            "SIN RED · COPIA LOCAL" if self.todos_los_pagos else "DETENIDO"
        )

    def _guardar_llegada(self, pago):
        from src.admin.mercadopago.historial.archivo import guardar
        if guardar([pago]):
            self._programar_sincronizacion_nodo()
        self.cargar_datos_locales()

    def _programar_sincronizacion_nodo(self):
        self._nodo_sync_pendiente = True
        self._reloj_nodo.start(300)

    def _iniciar_sincronizacion_nodo(self):
        hilo = self._sync_nodo_thread
        if hilo is not None and hilo.isRunning():
            self._nodo_sync_pendiente = True
            return
        self._nodo_sync_pendiente = False
        hilo = _SincronizacionNodo(self)
        hilo.listo.connect(self._fin_sincronizacion_nodo)
        self._sync_nodo_thread = hilo
        hilo.start()

    def _fin_sincronizacion_nodo(self, error, actualizado):
        if error:
            self._error_nodo = error
            self.lbl_estado.setText("PAGO LOCAL · NODO PENDIENTE")
            self.lbl_estado.setToolTip(error)
        elif actualizado:
            self._error_nodo = ""
            self.lbl_estado.setToolTip("")
        if self._nodo_sync_pendiente:
            self._reloj_nodo.start(0)

    def _marcas(self):
        import os
        from src.admin.mercadopago.historial.archivo import RUTA as csv_mp
        from src.cajero.paso6_cobro.vinculo_mp.libro import RUTA as vinculos
        from src.motor_auditoria_digital.libro_f9.libro import RUTA as f9
        from src.motor_auditoria_digital.libro_tickets.libro import RUTA as tickets_dig
        from src.motor_auditoria_digital.libro_cobranzas.libro import RUTA as cobranzas_dig

        marcas = []
        for ruta in (csv_mp, vinculos, f9, tickets_dig, cobranzas_dig):
            try:
                marcas.append(os.path.getmtime(ruta))
            except OSError:
                marcas.append(0)
        return tuple(marcas)

    def _refrescar_si_cambio(self):
        try:
            from src.motor_auditoria_digital.empleado import generacion

            gen = generacion()
        except Exception:
            gen = getattr(self, "_gen_vista", -1)
        if gen != getattr(self, "_gen_vista", -1):
            self._gen_vista = gen
            self.aplicar_filtros()
            return
        marcas = self._marcas()
        if marcas != self._marcas_archivos:
            self._marcas_archivos = marcas
            self.cargar_datos_locales()



    def cargar_datos_locales(self, sincronizar_nodo=False):
        if sincronizar_nodo:
            self._error_nodo = ""
            try:
                from src.admin.mercadopago.historial.nodo import sincronizar_nodo_configurado

                sincronizar_nodo_configurado()
            except (OSError, ValueError, RuntimeError) as error:
                self._error_nodo = str(error)
        barra = self.tabla.verticalScrollBar()
        puesto = barra.value()
        datos = leer()
        self.todos_los_pagos = datos["pagos"]
        self._forzar_cruce = True
        self.aplicar_filtros()
        barra.setValue(puesto)

    def aplicar_filtros(self):
        """
        Aplica período, texto y los dos filtros de negocio: firmados vs pendientes.
        """
        filtro_texto = self.txt_buscar.text().lower().strip()
        cruce = getattr(self, "_cruce", "Todos")
        cuenta_f = str(getattr(self, "_cuenta_filtro", "") or "")

        from src.motor_auditoria_digital.consultas.rango import filtro as rango_filtro

        d0, d1 = rango_filtro(
            getattr(self, "_periodo", "Hoy"),
            self.date_desde.date().toString("yyyy-MM-dd"),
            self.date_hasta.date().toString("yyyy-MM-dd"),
        )
        forzar = bool(getattr(self, "_forzar_cruce", False))
        self._forzar_cruce = False
        try:
            from src.motor_auditoria_digital.empleado import pedir as filas_auditoria

            crudo = filas_auditoria(d0, d1, forzar=forzar)
        except Exception:
            crudo = []
        if not crudo:
            from src.motor_auditoria_digital.consultas.rango import en_rango

            crudo = []
            for p in list(getattr(self, "todos_los_pagos", []) or []):
                if not en_rango(p.get("fecha") or "", d0, d1):
                    continue
                p.setdefault("ticket", "—")
                p.setdefault("estado", p.get("estado") or "")
                p.setdefault("monto_mp", p.get("monto") or 0)
                p.setdefault("neto", p.get("neto") or p.get("monto") or 0)
                crudo.append(p)

        cuentas_periodo = []
        for p in crudo:
            nombre_cuenta = str(p.get("cuenta") or "").strip()
            if nombre_cuenta and nombre_cuenta not in ("—", "-", "MP") and nombre_cuenta not in cuentas_periodo:
                cuentas_periodo.append(nombre_cuenta)
        self._cuentas_periodo = cuentas_periodo

        from src.admin.mercadopago.filtros.clase import entra_en_reparto, pasa

        filas = []
        para_reparto = []
        for p in crudo:
            op = p.get("op_type") or ""
            estado = str(p.get("estado") or "")
            fecha = str(p.get("fecha") or "")
            if op == "account_fund" or estado in ("CUENTA / DNI", "OMITIDO", "CARGA DE FONDOS"):
                continue
            if entra_en_reparto(p):
                para_reparto.append(p)
            if not pasa(p, cruce, cuenta_f):
                continue
            if filtro_texto:
                blob = " ".join([
                    fecha, str(p.get("id") or ""), str(p.get("cuenta") or ""),
                    str(p.get("nombre") or ""),
                    str(p.get("email") or ""), str(p.get("ticket") or ""),
                    str(p.get("ticket_venta") or ""), str(p.get("ticket_cobro") or ""),
                    f"{float(p.get('monto') or 0):.2f}", estado,
                ]).lower()
                if filtro_texto not in blob:
                    continue
            filas.append(p)

        try:
            from src.motor_auditoria_digital.cruces.totales import de_filas

            t = de_filas(filas)
        except Exception:
            t = {
                "bruto": 0.0, "neto": 0.0, "tickets": 0.0, "firmados": 0.0,
                "sin_firmar": 0.0, "cliente": 0.0, "n_sin_firmar": 0, "n_tickets": 0,
                "sin_ticket": 0.0, "n_sin_ticket": 0,
            }
        self.lbl_kpi_total_mes.setText(fmt_plata(t["bruto"]))
        self.lbl_kpi_neto_mes.setText(fmt_plata(t["neto"]))
        self.lbl_kpi_total.setText(fmt_plata(t["tickets"]))
        self.lbl_kpi_count.setText(fmt_plata(t["firmados"]))
        self.lbl_kpi_avg.setText(fmt_plata(t["sin_firmar"]))
        self.lbl_kpi_cliente.setText(fmt_plata(t.get("cliente", 0)))
        if hasattr(self, "lbl_kpi_cancelado"):
            self.lbl_kpi_cancelado.setText(fmt_plata(t.get("cancelados", 0)))
            n_canc = int(t.get("n_cancelados") or 0)
            if n_canc:
                self.card_cancelado._nota.setText(f"{n_canc} ticket{'s' if n_canc != 1 else ''} cancelado{'s' if n_canc != 1 else ''}")
                self.card_cancelado._nota.show()
            else:
                self.card_cancelado._nota.hide()
        sin_n = int(t.get("n_sin_firmar") or 0)
        tot_n = int(t.get("n_tickets") or 0)
        if tot_n:
            self.card_avg._nota.setText(f"{sin_n} / {tot_n}  ·  tickets no firmados")
            self.card_avg._nota.show()
        else:
            self.card_avg._nota.hide()
        self._pintar_reparto(para_reparto)
        self.lbl_kpi_suelto.setText(fmt_plata(t.get("sin_ticket") or 0))
        n_suelto = int(t.get("n_sin_ticket") or 0)
        if n_suelto:
            self.card_suelto._nota.setText(
                f"{n_suelto} cobro{'s' if n_suelto != 1 else ''} sin ticket para facturar"
            )
            self.card_suelto._nota.show()
        else:
            self.card_suelto._nota.hide()

        self.tabla.setRowCount(0)
        for p in filas:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            estado = str(p.get("estado") or "")
            fondo = QColor(self._fondo_estado(estado))
            cuenta = str(p.get("cuenta") or "—")
            fondo_cuenta, tinta_cuenta = self._tono_cuenta(cuenta)

            item_fecha = QTableWidgetItem(str(p.get("fecha") or ""))
            item_fecha.setForeground(QColor("#0F172A"))
            item_fecha.setBackground(fondo)
            self.tabla.setItem(row, 0, item_fecha)

            item_id = QTableWidgetItem(str(p.get("id") or "—") or "—")
            item_id.setForeground(QColor("#334155"))
            item_id.setBackground(fondo)
            self.tabla.setItem(row, 1, item_id)

            item_cuenta = QTableWidgetItem(cuenta)
            item_cuenta.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_cuenta.setForeground(QColor(tinta_cuenta))
            item_cuenta.setBackground(QColor(fondo_cuenta))
            self.tabla.setItem(row, 2, item_cuenta)

            item_nombre = QTableWidgetItem(str(p.get("nombre") or "—"))
            item_nombre.setForeground(QColor("#0F172A"))
            item_nombre.setBackground(fondo)
            self.tabla.setItem(row, 3, item_nombre)

            item_monto = QTableWidgetItem(f"${float(p.get('monto') or 0):.2f}")
            item_monto.setFont(QFont("Segoe UI", 12, QFont.Bold))
            if estado in ("CANCELADO", "CANCELADA"):
                item_monto.setForeground(QColor("#DC2626"))
            elif estado in ("F9 MANUAL", "SIN FIRMAR"):
                item_monto.setForeground(QColor("#B45309"))
            elif estado in ("SIN TICKET",):
                item_monto.setForeground(QColor("#DC2626"))
            elif estado in ("CUENTA / DNI", "CLIENTE", "COBRANZA"):
                item_monto.setForeground(QColor("#0369A1"))
            else:
                item_monto.setForeground(QColor("#059669"))
            item_monto.setBackground(fondo)
            self.tabla.setItem(row, 4, item_monto)

            item_estado = QTableWidgetItem(estado)
            item_estado.setFont(QFont("Segoe UI", 10, QFont.Bold))
            colores = {
                "APPROVED": "#059669",
                "FIRMADO": "#059669",
                "SIN TICKET": "#DC2626",
                "CANCELADO": "#DC2626",
                "CANCELADA": "#DC2626",
                "SIN FIRMAR": "#B45309",
                "F9 MANUAL": "#B45309",
                "COBRANZA": "#0369A1",
            }
            item_estado.setForeground(QColor(colores.get(estado, "#334155")))
            item_estado.setBackground(fondo)
            self.tabla.setItem(row, 5, item_estado)

            tv = str(p.get("ticket_venta") or "") or "—"
            tc = str(p.get("ticket_cobro") or "") or "—"
            item_tv = QTableWidgetItem(tv)
            item_tv.setForeground(QColor("#0F172A"))
            item_tv.setBackground(fondo)
            self.tabla.setItem(row, 6, item_tv)

            item_tc = QTableWidgetItem(tc)
            item_tc.setForeground(QColor("#0F172A"))
            item_tc.setBackground(fondo)
            self.tabla.setItem(row, 7, item_tc)

    def _abrir_filtros(self):
        from src.admin.mercadopago.filtros.panel import abrir
        from src.admin.mercadopago.historial.cuentas import listar_cuentas

        nombres = []
        try:
            nombres.extend(listar_cuentas())
        except Exception:
            pass
        for nombre in getattr(self, "_cuentas_periodo", []) or []:
            if nombre not in nombres:
                nombres.append(nombre)
        abrir(
            self,
            self.btn_filtros,
            getattr(self, "_cruce", "Todos"),
            str(getattr(self, "_cuenta_filtro", "") or ""),
            nombres,
            self._elegir_filtro,
            self._estilo_periodo_activo,
            self._estilo_periodo_idle,
        )

    def _elegir_filtro(self, cruce, cuenta):
        from src.admin.mercadopago.filtros.clase import texto_boton

        self._cruce = cruce or "Todos"
        self._cuenta_filtro = cuenta or ""
        panel = getattr(self, "_panel_filtros", None)
        if panel is not None:
            panel.hide()
        self.btn_filtros.setText(texto_boton(self._cruce, self._cuenta_filtro))
        self.btn_filtros.setStyleSheet(
            self._estilo_periodo_activo if self.btn_filtros.text() != "Filtros" else self._estilo_periodo_idle
        )
        self.aplicar_filtros()

    def _pintar_reparto(self, filas):
        from src.admin.mercadopago.filtros.clase import sumar_cuentas

        partes = [f"{nombre}   {fmt_plata(total)}" for nombre, total in sumar_cuentas(filas)]
        if not partes or not hasattr(self, "lbl_reparto"):
            if hasattr(self, "lbl_reparto"):
                self.lbl_reparto.hide()
            return
        self.lbl_reparto.setText("   ·   ".join(partes))
        self.lbl_reparto.show()

    @staticmethod
    def _fondo_estado(estado: str) -> str:
        clave = str(estado or "").upper()
        if clave in ("FIRMADO", "APPROVED"):
            return "#ECFDF5"
        if clave in ("SIN FIRMAR", "F9 MANUAL"):
            return "#FFFBEB"
        if clave in ("CANCELADO", "CANCELADA", "SIN TICKET"):
            return "#FEF2F2"
        if clave in ("COBRANZA", "CLIENTE", "CUENTA / DNI"):
            return "#F0F9FF"
        return "#FFFFFF"

    @staticmethod
    def _tono_cuenta(nombre: str) -> tuple[str, str]:
        clave = str(nombre or "").strip().lower()
        if not clave or clave in ("—", "-", "mp"):
            return "#F8FAFC", "#334155"
        paleta = (
            ("#E0E7FF", "#312E81"),
            ("#D1FAE5", "#065F46"),
            ("#FFEDD5", "#9A3412"),
            ("#FCE7F3", "#9D174D"),
            ("#E0F2FE", "#075985"),
            ("#EDE9FE", "#5B21B6"),
        )
        return paleta[sum(ord(c) for c in clave) % len(paleta)]

    def _elegir_periodo(self, texto):
        if texto == getattr(self, "_periodo", "") and texto != "Período":
            texto = "Todos"
        self._periodo = texto
        for t, b in self._botones_periodo.items():
            b.setStyleSheet(self._estilo_periodo_activo if t == texto else self._estilo_periodo_idle)
        es_periodo = texto == "Período"
        self.date_desde.setVisible(es_periodo)
        self.date_hasta.setVisible(es_periodo)
        self.aplicar_filtros()

    def mostrar_menu_contextual(self, pos):
        item = self.tabla.itemAt(pos)
        if not item: return

        row = self.tabla.row(item)
        id_item = self.tabla.item(row, 1)
        if not id_item: return
        id_pago = id_item.text()
        if not id_pago or id_pago in ("—", "F9 MANUAL"):
            return

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
        if omitir(id_pago):
            self._programar_sincronizacion_nodo()
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
