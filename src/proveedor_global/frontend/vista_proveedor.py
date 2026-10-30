from src.utils.qt_compat import qt_exec
import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Utilidades visuales importadas desde el módulo del Jefe
from src.contabilidad.shared_globals import (
    section_title, date_field, input_field, build_table,
    btn_primary, btn_ghost, PAL
)

from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta, nombre_de_eleccion
from src.proveedor_global.backend.motor_proveedor import MotorProveedor
from src.proveedor_global.frontend.pedido.panel import (
    DialogoAltaProveedor, PanelPedidosAutomaticos,
)
from src.proveedor_global.backend.moneda import leer, texto
from src.proveedor_global.frontend.carga.recepcion import PanelRecepcionRapida, plata
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


def _dia(fecha) -> str:
    texto = str(fecha or "").strip()
    base = texto[:10]
    partes = base.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return base or texto


def _fecha_de(fecha):
    base = str(fecha or "").strip()[:10]
    try:
        return datetime.date.fromisoformat(base)
    except ValueError:
        return None


def _rango_historial(periodo, hoy=None):
    hoy = hoy or datetime.date.today()
    if periodo == "Hoy":
        return hoy, hoy
    if periodo == "Ayer":
        ayer = hoy - datetime.timedelta(days=1)
        return ayer, ayer
    if periodo == "Semana":
        inicio = hoy - datetime.timedelta(days=hoy.weekday())
        return inicio, inicio + datetime.timedelta(days=6)
    if periodo == "Semana pasada":
        inicio = hoy - datetime.timedelta(days=hoy.weekday() + 7)
        return inicio, inicio + datetime.timedelta(days=6)
    if periodo == "Mes":
        return hoy.replace(day=1), hoy
    if periodo == "Mes pasado":
        primero = hoy.replace(day=1) - datetime.timedelta(days=1)
        return primero.replace(day=1), primero
    if periodo == "Año":
        return hoy.replace(month=1, day=1), hoy
    return None, None


class VistaProveedor(QWidget):
    """
    Vista unificada de Proveedores (Romaneo y Compras Rǭpidas).
    """
    request_dashboard = pyqtSignal()
    def __init__(self, parent=None, perfil="admin", db_jefe=None):
        super().__init__(parent)
        self.perfil = perfil.lower()
        self._db_jefe = db_jefe
        try:
            from src.motor_inventario.planilla.orquestador import MotorPlanilla

            MotorPlanilla.arrancar()
        except Exception:
            pass

        # Layout principal
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setStyleSheet("background: #F1F5F9;")
        self.lay_container = lay

        nav = QFrame()
        nav.setFixedHeight(72)
        nav.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        n_lay = QHBoxLayout(nav)
        n_lay.setContentsMargins(24, 0, 24, 0)
        self._btn_volver = QPushButton("← Panel admin")
        self._btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_volver.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; border-radius: 10px; "
            "padding: 10px 18px; font-weight: 700; } QPushButton:hover { background: #1D4ED8; }"
        )
        self._btn_volver.clicked.connect(self._volver)
        n_lay.addWidget(self._btn_volver)
        n_lay.addSpacing(16)
        col_t = QVBoxLayout()
        col_t.setSpacing(0)
        self._titulo = QLabel("Proveedores")
        self._titulo.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A; background: transparent; border: none;")
        self._sub = QLabel("Pedido, carga, fichas y pago")
        self._sub.setStyleSheet("font-size: 12px; color: #64748B; background: transparent; border: none;")
        col_t.addWidget(self._titulo)
        col_t.addWidget(self._sub)
        n_lay.addLayout(col_t)
        n_lay.addStretch()
        lay.addWidget(nav)

        self._build_ui()
        QTimer.singleShot(0, self.cargar_datos)

    def _cargar_proveedor(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != QDialog.DialogCode.Accepted:
            return
        fichas = getattr(self, "_fichas", None)
        if fichas is not None:
            fichas._compras = MotorProveedor.load_proveedores(self.perfil, self._db_jefe) or []
            fichas._pintar()

    def _hub(self, tarjetas):
        from src.motor_descuentos.compartido import TarjetaModulo

        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")
        wrap = QWidget()
        wrap.setStyleSheet("background: #F1F5F9;")
        grid = QGridLayout(wrap)
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setSpacing(18)
        for i, (cod, ico, tit, sub) in enumerate(tarjetas):
            card = TarjetaModulo(cod, ico, tit, sub)
            card.clicked.connect(lambda c=cod: self._ir(c))
            grid.addWidget(card, i // 3, i % 3)
        grid.setRowStretch(2, 1)
        scroll.setWidget(wrap)
        lay.addWidget(scroll)
        return page

    def _pagina_fichas(self):
        from src.proveedor_global.frontend.fichas.panel import DialogoProveedoresActivos

        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 12, 16, 12)
        barra = QHBoxLayout()
        barra.addStretch()
        btn = QPushButton("Cargar proveedor")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; border-radius: 8px; "
            "padding: 0 16px; font-weight: 700; } QPushButton:hover { background: #1D4ED8; }"
        )
        btn.clicked.connect(self._cargar_proveedor)
        barra.addWidget(btn)
        lay.addLayout(barra)
        self._fichas = DialogoProveedoresActivos(page, embebido=True)
        lay.addWidget(self._fichas, 1)
        return page

    def _volver(self):
        actual = self.stack.currentIndex() if hasattr(self, "stack") else 0
        if actual in (3, 4):
            self._ir("carga")
            return
        if hasattr(self, "_formula") and actual == self.stack.indexOf(self._formula):
            if self._formula.retroceder():
                return
            self._ir("hub")
            return
        if actual == 0:
            self.request_dashboard.emit()
            return
        self._ir("hub")

    def _ir(self, codigo):
        textos = {
            "hub": ("Proveedores", "Pedido, carga, fichas, pago, historial y fórmula", "← Panel admin"),
            "pedido": ("Realizar pedido", "Faltantes y mensaje para el proveedor", "← Módulos"),
            "carga": ("Cargar pedido", "Escáner o carga por peso", "← Módulos"),
            "escaner": ("Recepción por escáner", "Elegí el proveedor y pasá la mercadería", "← Cargar pedido"),
            "peso": ("Carga por peso", "Cajas × kilos × precio", "← Cargar pedido"),
            "fichas": ("Proveedores", "Fichas y productos asociados", "← Módulos"),
            "pago": ("Pago centralizado", "Pendientes, historial y forma de pago", "← Módulos"),
            "historial": ("Historial", "Compras, contado y fiado", "← Módulos"),
            "formula": ("Fórmula", "Carne, cerdo, pollo, huevo y congelado", "← Módulos"),
        }
        titulo, sub, volver = textos.get(codigo, textos["hub"])
        self._titulo.setText(titulo)
        self._sub.setText(sub)
        self._btn_volver.setText(volver)
        if self.perfil == "contabilidad" and codigo == "hub":
            self._btn_volver.hide()
        else:
            self._btn_volver.show()
        paginas = {
            "hub": 0, "pedido": 1, "carga": 2, "escaner": 3, "peso": 4,
            "fichas": 5, "pago": 6, "historial": 7, "formula": 8,
        }
        self.stack.setCurrentIndex(paginas.get(codigo, 0))
        if codigo == "pedido":
            self.panel_pedidos.refrescar_datos()
        elif codigo == "escaner":
            self.cargar_datos()
            self.panel_recepcion.recargar_proveedores()
            self.panel_recepcion.enfocar_escaner()
        elif codigo == "peso":
            self._cargar_combo_proveedores()
            self.cargar_datos()
        elif codigo == "fichas" and getattr(self, "_fichas", None) is not None:
            self._fichas._compras = MotorProveedor.load_proveedores(self.perfil, self._db_jefe) or []
            self._fichas._pintar()
        elif codigo == "formula":
            self._formula.inicio()
        elif codigo == "pago":
            self._pago_centralizado(en_pagina=True)
        elif codigo == "historial":
            self.cargar_datos()

    def _deudas_abiertas(self):
        filas = MotorProveedor.load_proveedores(self.perfil, self._db_jefe) or []
        abiertas = []
        for fila in filas:
            try:
                restante = float(fila.get("restante") or 0)
            except (TypeError, ValueError):
                restante = 0.0
            if restante <= 0:
                continue
            casa = fila.get("origen") == "casa"
            rid = f"casa:{fila['id']}" if casa else fila["id"]
            abiertas.append({
                "id": rid,
                "casa": casa,
                "proveedor": fila.get("proveedor") or "",
                "fecha": _dia(fila.get("fecha")),
                "restante": restante,
                "condicion": fila.get("condicion") or "Fiado",
            })
        return abiertas

    def _pago_centralizado(self, en_pagina=False):
        if en_pagina and getattr(self, "_pago_listo", False):
            self._pintar_pago()
            return
        if en_pagina:
            dlg = self._pagina_pago
            dlg.setStyleSheet("background: #F8FAFC;")
            self._pago_listo = True
        else:
            dlg = QDialog(self)
            dlg.setWindowTitle("Pago centralizado")
            dlg.setMinimumSize(760, 480)
            dlg.resize(820, 540)
            dlg.setStyleSheet("QDialog { background: #F8FAFC; }")
        caja = QVBoxLayout(dlg)
        caja.setContentsMargins(24, 20, 24, 18)
        caja.setSpacing(12)

        titulo = QLabel("Fiados abiertos")
        titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E293B; background: transparent;")
        caja.addWidget(titulo)
        resumen = QLabel("")
        resumen.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569;")
        caja.addWidget(resumen)

        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["Proveedor", "Fecha", "Restante", "Condición"])
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.verticalHeader().setVisible(False)
        tabla.setStyleSheet(
            "QTableWidget { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
            "QHeaderView::section { background: #F8FAFC; color: #64748B; font-weight: 700; border: none; padding: 8px; }"
        )
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        caja.addWidget(tabla, stretch=1)

        hechos_titulo = QLabel("Historial de pagos")
        hechos_titulo.setStyleSheet("font-size: 16px; font-weight: 800; color: #1E293B; background: transparent;")
        caja.addWidget(hechos_titulo)
        hechos = QTableWidget(0, 5)
        hechos.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Monto", "Medio", "Nota"])
        hechos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hechos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        hechos.verticalHeader().setVisible(False)
        hechos.setStyleSheet(tabla.styleSheet())
        hechos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hechos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        caja.addWidget(hechos, stretch=1)

        deudas = []

        def _pintar():
            deudas.clear()
            deudas.extend(self._deudas_abiertas())
            tabla.setRowCount(0)
            total = 0.0
            for fila in deudas:
                total += fila["restante"]
                r = tabla.rowCount()
                tabla.insertRow(r)
                celdas = [
                    QTableWidgetItem(str(fila["proveedor"])),
                    QTableWidgetItem(fila["fecha"]),
                    QTableWidgetItem(texto(fila["restante"])),
                    QTableWidgetItem(fila["condicion"]),
                ]
                vestir_nombre(celdas[0])
                vestir_numero(celdas[2])
                for c, it in enumerate(celdas):
                    tabla.setItem(r, c, it)
            if deudas:
                resumen.setText(f"{len(deudas)} cuentas  ·  {texto(total)}")
            else:
                resumen.setText("No hay fiados pendientes.")
            from src.proveedor_global.backend.cuenta import listar_pagos

            try:
                pagos = listar_pagos()
            except Exception:
                pagos = []
            hechos.setRowCount(0)
            for pago in pagos:
                r = hechos.rowCount()
                hechos.insertRow(r)
                celdas = [
                    QTableWidgetItem(_dia(pago.get("fecha"))),
                    QTableWidgetItem(str(pago.get("proveedor") or "")),
                    QTableWidgetItem(texto(pago.get("monto"))),
                    QTableWidgetItem(str(pago.get("medio") or "")),
                    QTableWidgetItem(str(pago.get("nota") or "")),
                ]
                vestir_numero(celdas[0])
                vestir_nombre(celdas[1])
                vestir_numero(celdas[2])
                vestir_nombre(celdas[3])
                vestir_nombre(celdas[4])
                for c, it in enumerate(celdas):
                    hechos.setItem(r, c, it)
            if pagos:
                hechos_titulo.setText(f"Historial de pagos  ·  {len(pagos)}")
            else:
                hechos_titulo.setText("Historial de pagos")

        def _elegidas():
            return [deudas[idx.row()] for idx in tabla.selectionModel().selectedRows() if idx.row() < len(deudas)]

        def _pagar():
            from src.proveedor_global.frontend.pago.dialogo import pedir_pago

            elegidas = _elegidas()
            if not elegidas:
                QMessageBox.information(dlg, "Pago", "Elegí una o varias cuentas.")
                return
            bloqueadas = [
                d for d in elegidas
                if getattr(self, "_solo_lectura", False) and not d["casa"]
            ]
            if bloqueadas and len(bloqueadas) == len(elegidas):
                QMessageBox.warning(
                    dlg, "Sin conexión",
                    "Esas cuentas son del negocio. El pago espera la conexión con la tienda.",
                )
                return
            elegidas = [d for d in elegidas if d not in bloqueadas]
            total = sum(d["restante"] for d in elegidas)
            proveedor = elegidas[0]["proveedor"] if len(elegidas) == 1 else f"{len(elegidas)} cuentas"
            dato = pedir_pago(dlg, total, proveedor, varios=len(elegidas))
            if not dato:
                return
            fallos = []
            for deuda in elegidas:
                monto = dato["monto"] if len(elegidas) == 1 else deuda["restante"]
                try:
                    MotorProveedor.pagar_proveedor(
                        deuda["id"], monto, self.perfil, self._db_jefe,
                        medio=dato["medio"], fecha=dato["fecha"], nota=dato["nota"],
                    )
                except Exception as exc:
                    fallos.append(f"{deuda['proveedor']}: {exc}")
            self.cargar_datos()
            _pintar()
            if fallos:
                QMessageBox.warning(dlg, "Pago incompleto", "\n".join(fallos))
            elif len(elegidas) == 1:
                QMessageBox.information(dlg, "Listo", f"Pago de {texto(dato['monto'])} registrado.")

        pie = QHBoxLayout()
        pie.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(36)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 0 16px; font-weight: 700; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_cerrar.clicked.connect(dlg.reject if not en_pagina else lambda: self._ir("hub"))
        btn_ok = QPushButton("Pagar elegidas")
        btn_ok.setFixedHeight(36)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            "QPushButton { background: #059669; color: white; border: none; "
            "border-radius: 8px; padding: 0 16px; font-weight: 700; }"
            "QPushButton:hover { background: #047857; }"
        )
        btn_ok.clicked.connect(_pagar)
        pie.addWidget(btn_cerrar)
        pie.addWidget(btn_ok)
        caja.addLayout(pie)
        self._pintar_pago = _pintar
        _pintar()
        if not en_pagina:
            qt_exec(dlg)

    def _build_ui(self):
        lay = self.lay_container

        self.stack = QStackedWidget()
        self.stack.addWidget(self._hub((
            ("pedido", "📦", "Realizar pedido", "Faltantes y el mensaje para el proveedor."),
            ("carga", "📥", "Cargar pedido", "Escáner o cajas × kilos × precio."),
            ("fichas", "🚚", "Proveedores", "Fichas y productos asociados."),
            ("pago", "💳", "Pago centralizado", "Pendientes, historial y forma de pago."),
            ("historial", "📋", "Historial", "Compras a proveedores, contado y fiado."),
            ("formula", "🧮", "Fórmula", "Carne, cerdo, pollo, huevo y congelado."),
        )))

        self.panel_pedidos = PanelPedidosAutomaticos(self)
        self.stack.addWidget(self.panel_pedidos)
        self.stack.addWidget(self._hub((
            ("escaner", "⚡", "Recepción por escáner", "Elegí el proveedor y pasá la mercadería."),
            ("peso", "⚖️", "Carga por peso", "Una media res, un queso o lo que sea: cajas × kilos × precio."),
        )))

        # Pestaña 2: Recepción Rápida por Escáner
        self.panel_recepcion = PanelRecepcionRapida(self, perfil=self.perfil)
        self.panel_recepcion.compra_guardada.connect(self.cargar_datos)
        self.stack.addWidget(self.panel_recepcion)

        # Pestaña 3: Carga de Compras / Romaneo Tradicional
        self.widget_carga = QWidget()
        lay_carga = QVBoxLayout(self.widget_carga)
        lay_carga.setContentsMargins(16, 16, 16, 8)
        lay_carga.setSpacing(16)

        self._lbl_estado_red = QLabel("")
        self._lbl_estado_red.setWordWrap(True)
        self._lbl_estado_red.setStyleSheet(
            f"QLabel {{ background: {PAL['surface']}; color: {PAL['text']}; "
            f"border: 1px solid {PAL['border']}; border-radius: 8px; padding: 9px 12px; "
            "font-weight: 700; }}"
        )
        self._lbl_estado_red.hide()
        lay_carga.addWidget(self._lbl_estado_red)

        main_h = QHBoxLayout()
        main_h.setSpacing(20)

        left_panel = QFrame()
        self._panel_carga = left_panel
        left_panel.setObjectName("Card")
        left_panel.setStyleSheet(f"""
            QFrame#Card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['surface']}, stop:1 #F8FAFC);
                border: 1px solid {PAL['border']};
                border-radius: 16px;
            }}
        """)
        fl = QGridLayout(left_panel)
        fl.setContentsMargins(25, 25, 25, 25); fl.setSpacing(15)

        title_lbl = QLabel("🧾 DATOS DEL REMITO")
        title_lbl.setStyleSheet(f"QLabel {{ color: {PAL['primary']}; font-weight: 900; font-size: 14px; letter-spacing: 1px; }}")
        fl.addWidget(title_lbl, 0, 0, 1, 4)

        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_fecha, 1, 0)
        self._prov_date = date_field(); fl.addWidget(self._prov_date, 1, 1)

        lbl_prov = QLabel("Proveedor:")
        lbl_prov.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_prov, 1, 2)

        self._prov_nombre = QComboBox()
        self._prov_nombre.setEditable(True)
        self._prov_nombre.setPlaceholderText("Ej: Frigorífico Rioplatense")
        self._prov_nombre.setStyleSheet(f"QComboBox {{ background: white; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-size: 13px; }}")
        caja_prov = QHBoxLayout()
        caja_prov.setSpacing(8)
        caja_prov.addWidget(self._prov_nombre, 1)
        self._btn_alta_prov = QPushButton("＋ Id")
        self._btn_alta_prov.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_alta_prov.setFixedWidth(64)
        self._btn_alta_prov.setStyleSheet(
            "QPushButton { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; "
            "border-radius: 6px; padding: 8px; font-weight: 700; }"
        )
        self._btn_alta_prov.clicked.connect(self._alta_proveedor)
        caja_prov.addWidget(self._btn_alta_prov)
        fl.addLayout(caja_prov, 1, 3)
        self._cargar_combo_proveedores()

        lbl_tropa = QLabel("Tropa/Lote:")
        lbl_tropa.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_tropa, 2, 0)
        self._prov_tropa = input_field("Nro Tropa"); fl.addWidget(self._prov_tropa, 2, 1)

        lbl_merc = QLabel("Mercadería:")
        lbl_merc.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_merc, 2, 2)
        self._prov_type = QComboBox()
        self._prov_type.setEditable(True)
        self._prov_type.addItems([
            "Media res", "Queso", "Fiambre", "Pollo", "Cerdo", "Achuras",
            "Carne_Media Res", "Carne_Mocho", "Carne_Pecho",
        ])
        self._prov_type.setCurrentText("")
        self._prov_type.lineEdit().setPlaceholderText("Media res, queso, lo que sea")
        self._prov_type.setStyleSheet(f"QComboBox {{ background: white; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-size: 13px; }}")
        fl.addWidget(self._prov_type, 2, 3)

        lbl_cajas = QLabel("Cajas:")
        lbl_cajas.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_cajas, 3, 0)
        self._prov_cajas = input_field("1")
        self._prov_cajas.setText("1")
        self._prov_cajas.setStyleSheet(f"QLineEdit {{ background: white; border: 1px solid {PAL['border']}; padding: 10px; border-radius: 8px; color: {PAL['text']}; font-size: 14px; }}")
        fl.addWidget(self._prov_cajas, 3, 1)

        lbl_kilos = QLabel("Kilos c/u:")
        lbl_kilos.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_kilos, 3, 2)
        self._romaneo_input = input_field("Ej: 80 o 4.5 y Enter")
        self._romaneo_input.setStyleSheet(f"QLineEdit {{ background: #ECFDF5; border: 2px solid #10B981; padding: 12px; border-radius: 8px; color: #065F46; font-size: 16px; }}")
        self._romaneo_input.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._romaneo_input, 3, 3)

        lbl_precio = QLabel("Precio / kg:")
        lbl_precio.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_precio, 4, 0)
        self._prov_precio = input_field("Precio del kilo")
        self._prov_precio.setStyleSheet(f"QLineEdit {{ background: #FEF3C7; border: 2px solid #F59E0B; padding: 10px; border-radius: 8px; color: #92400E; font-size: 14px; }}")
        self._prov_precio.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._prov_precio, 4, 1)

        self._lbl_carga = QLabel("La línea es cajas × kilos × precio. Enter agrega.")
        self._lbl_carga.setStyleSheet("QLabel { color: #475569; font-size: 12px; }")
        fl.addWidget(self._lbl_carga, 4, 2, 1, 2)

        self._romaneo_table = build_table(["Nro", "Mercadería", "Cajas", "Kilos", "Precio/kg", "Subtotal", "X"])
        self._romaneo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._romaneo_table.setMinimumHeight(180)
        fl.setRowStretch(5, 1)
        self._romaneo_table.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {PAL['border']}; border-radius: 8px; font-size: 13px; }}")
        fl.addWidget(self._romaneo_table, 5, 0, 1, 4)

        main_h.addWidget(left_panel, stretch=6)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        totals_card = QFrame()
        totals_card.setStyleSheet(f"""
            QFrame {{ background: #0F172A; border-radius: 16px; border: 2px solid #1E293B; }}
            QLabel {{ color: white; background: transparent; }}
        """)
        t_lay = QVBoxLayout(totals_card)
        t_lay.setContentsMargins(20, 20, 20, 20)

        lbl_t1 = QLabel("RESUMEN DE COMPRA")
        lbl_t1.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t1)

        self._lbl_romaneo_totals = QLabel(f"0 items - {texto(0)}")
        self._lbl_romaneo_totals.setStyleSheet("QLabel { color: #38BDF8; font-weight: 900; font-size: 22px; }")
        t_lay.addWidget(self._lbl_romaneo_totals)

        t_lay.addSpacing(15)
        lbl_t2 = QLabel("MONTO TOTAL")
        lbl_t2.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t2)

        self._prov_amount = QLineEdit("0.00")
        self._prov_amount.setReadOnly(True)
        self._prov_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._prov_amount.setStyleSheet("QLineEdit { background: transparent; border: none; color: #10B981; font-weight: 900; font-size: 36px; }")
        t_lay.addWidget(self._prov_amount)

        right_panel.addWidget(totals_card)

        action_card = QFrame()
        self._panel_acciones = action_card
        action_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 16px; }}")
        a_lay = QVBoxLayout(action_card)
        a_lay.setContentsMargins(20, 20, 20, 20)

        lbl_pago = QLabel("💳 CONDICIÓN DE PAGO:")
        lbl_pago.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        a_lay.addWidget(lbl_pago)
        self._prov_payment = QComboBox()
        self._prov_payment.addItems(["A Pagar (Deuda en Cta. Cte.)", "Contado (Pago Inmediato)"])
        self._prov_payment.setStyleSheet(f"QComboBox {{ background: {PAL.get('surface2', '#E2E8F0')}; border: 1px solid {PAL['border']}; padding: 12px; border-radius: 8px; color: {PAL['text']}; font-weight: 800; font-size: 13px; }}")
        a_lay.addWidget(self._prov_payment)

        a_lay.addSpacing(15)
        btn_add = QPushButton("✅ PROCESAR COMPRA")
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                color: white; border-radius: 16px; padding: 15px; font-weight: 900; font-size: 16px;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._save_proveedor)
        a_lay.addWidget(btn_add)

        right_panel.addWidget(action_card)
        right_panel.addStretch()

        main_h.addLayout(right_panel, stretch=4)
        lay_carga.addLayout(main_h, 1)

        self.stack.addWidget(self.widget_carga)
        self.stack.addWidget(self._pagina_fichas())
        self._pagina_pago = QWidget()
        self._pago_listo = False
        self.stack.addWidget(self._pagina_pago)

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: #F8FAFC;")
        h_box = QVBoxLayout(self.history_container)
        h_box.setContentsMargins(24, 16, 24, 16)
        h_box.setSpacing(12)
        self._periodo_hist = "Todo"
        self._filas_hist = []
        self._chips_hist = {}

        chips = QHBoxLayout()
        chips.setSpacing(8)
        for nombre in ("Hoy", "Ayer", "Semana", "Semana pasada", "Mes", "Mes pasado", "Año", "Todo"):
            btn = QPushButton(nombre)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, n=nombre: self._elegir_periodo_hist(n))
            self._chips_hist[nombre] = btn
            chips.addWidget(btn)
        chips.addStretch()
        h_box.addLayout(chips)
        self._pintar_chips_hist()

        filtros = QHBoxLayout()
        filtros.setSpacing(10)
        self._cb_hist_prov = QComboBox()
        self._cb_hist_prov.setMinimumWidth(240)
        self._cb_hist_prov.setFixedHeight(36)
        self._cb_hist_prov.addItem("Todos los proveedores", "")
        self._cb_hist_estado = QComboBox()
        self._cb_hist_estado.setMinimumWidth(160)
        self._cb_hist_estado.setFixedHeight(36)
        self._cb_hist_estado.addItem("Todos los estados", "")
        self._cb_hist_estado.addItem("Fiado", "Fiado")
        self._cb_hist_estado.addItem("Pagado", "Pagado")
        self._cb_hist_estado.addItem("Anulado", "Anulado")
        estilo_combo = (
            "QComboBox { background: white; border: 1px solid #CBD5E1; border-radius: 8px; "
            "padding: 0 10px; color: #0F172A; font-size: 13px; }"
        )
        self._cb_hist_prov.setStyleSheet(estilo_combo)
        self._cb_hist_estado.setStyleSheet(estilo_combo)
        self._cb_hist_prov.currentIndexChanged.connect(lambda _i: self._pintar_historial())
        self._cb_hist_estado.currentIndexChanged.connect(lambda _i: self._pintar_historial())
        filtros.addWidget(self._cb_hist_prov)
        filtros.addWidget(self._cb_hist_estado)
        filtros.addStretch()
        h_box.addLayout(filtros)

        totales = QHBoxLayout()
        totales.setSpacing(12)
        self._lbl_hist_cuenta = QLabel("0 compras")
        self._lbl_hist_cuenta.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; background: transparent;")
        totales.addWidget(self._lbl_hist_cuenta)
        totales.addStretch()
        self._val_hist_pagado = self._tarjeta_total(totales, "Pagado", "#059669")
        self._val_hist_restante = self._tarjeta_total(totales, "Restante", "#DC2626")
        self._val_hist_monto = self._tarjeta_total(totales, "Monto", "#0F172A")
        h_box.addLayout(totales)

        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Fecha", "Estado", "Acción"])
        self._tbl_prov.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tbl_prov.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        h_box.addWidget(self._tbl_prov, 1)
        self.stack.addWidget(self.history_container)

        from src.proveedor_global.frontend.formula.panel import PanelFormula
        self._formula = PanelFormula(self)
        self._formula.cambio.connect(self._titulo_formula)
        self.stack.addWidget(self._formula)

        lay.addWidget(self.stack, 1)
        self._ir("hub")

    def _titulo_formula(self, titulo, sub, volver):
        self._titulo.setText(titulo)
        self._sub.setText(sub)
        self._btn_volver.setText(volver)

    def _add_romaneo_item(self):
        merc = self._prov_type.currentText().strip()
        cajas_txt = self._prov_cajas.text().strip().replace(",", ".") or "1"
        kilos_txt = self._romaneo_input.text().strip().replace(",", ".")
        precio_txt = self._prov_precio.text().strip().replace(",", ".")
        if not merc:
            QMessageBox.warning(self, "Falta la mercadería", "Escribí qué entra: media res, queso u otra cosa.")
            self._prov_type.setFocus()
            return
        if not kilos_txt:
            self._romaneo_input.setFocus()
            return
        if not precio_txt:
            self._prov_precio.setFocus()
            return

        try:
            cajas = float(cajas_txt)
            kilos = float(kilos_txt)
            precio = float(precio_txt)
            if cajas <= 0 or kilos <= 0 or precio < 0:
                raise ValueError
            subtotal = cajas * kilos * precio

            row = self._romaneo_table.rowCount()
            self._romaneo_table.insertRow(row)

            def _celda(valor):
                it = QTableWidgetItem(valor)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return it

            self._romaneo_table.setItem(row, 0, _celda(f"#{row + 1}"))
            self._romaneo_table.setItem(row, 1, _celda(merc))
            self._romaneo_table.setItem(row, 2, _celda(f"{cajas:g}"))
            self._romaneo_table.setItem(row, 3, _celda(f"{kilos:.2f}"))
            self._romaneo_table.setItem(row, 4, _celda(texto(precio)))
            self._romaneo_table.setItem(row, 5, _celda(texto(subtotal)))

            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 4px; font-weight: 700; }")
            btn_del.clicked.connect(lambda _, r=row: self._remove_romaneo_item(r))

            widget = QWidget()
            l = QHBoxLayout(widget)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(btn_del)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setCellWidget(row, 6, widget)

            self._prov_cajas.setText("1")
            self._romaneo_input.clear()
            self._romaneo_input.setFocus()
            self._romaneo_table.scrollToBottom()
            self._update_prov_calc()
        except ValueError:
            QMessageBox.warning(self, "Error", "Cajas, kilos y precio tienen que ser números.")

    def _remove_romaneo_item(self, row):
        self._romaneo_table.removeRow(row)
        for i in range(self._romaneo_table.rowCount()):
            self._romaneo_table.item(i, 0).setText(f"#{i+1}")
            widget = self._romaneo_table.cellWidget(i, 6)
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    try: btn.clicked.disconnect()
                    except: pass
                    btn.clicked.connect(lambda _, r=i: self._remove_romaneo_item(r))
        self._update_prov_calc()

    def _update_prov_calc(self):
        monto_total = 0.0
        items_count = self._romaneo_table.rowCount()
        for i in range(items_count):
            monto_total += leer(self._romaneo_table.item(i, 5).text())

        self._lbl_romaneo_totals.setText(f"{items_count} items - {texto(monto_total)}")
        self._prov_amount.setText(f"{monto_total:.2f}")

    def cargar_datos(self):
        """Carga el historial de compras utilizando el motor."""
        tienda_online = MotorProveedor.tienda_disponible()
        _db, modo = MotorProveedor._get_read_db(self.perfil, self._db_jefe)
        self._solo_lectura = not tienda_online
        self._panel_carga.setEnabled(True)
        self._panel_acciones.setEnabled(True)
        if self._solo_lectura and modo == "copia":
            self._lbl_estado_red.setText(
                "Sin la tienda, la compra queda en esta PC. "
                "Pagar una cuenta del negocio espera la conexión."
            )
            self._lbl_estado_red.show()
        elif self._solo_lectura and modo == "sin_copia":
            self._lbl_estado_red.setText(
                "Sin conexión y sin copia del nodo disponible. No se muestra un historial local incompleto; "
                "conecte la tienda o el nodo."
            )
            self._lbl_estado_red.show()
        elif self._solo_lectura:
            self._lbl_estado_red.setText(
                "Consulta de solo lectura. Compras y pagos requieren conexión con la tienda."
            )
            self._lbl_estado_red.show()
        else:
            self._lbl_estado_red.hide()

        self._filas_hist = list(MotorProveedor.load_proveedores(self.perfil, self._db_jefe) or [])
        self._cargar_combo_hist()
        self._pintar_historial()

    def _tarjeta_total(self, lay, titulo, color):
        caja = QFrame()
        caja.setFixedHeight(64)
        caja.setMinimumWidth(160)
        caja.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
            "QLabel { background: transparent; border: none; }"
        )
        col = QVBoxLayout(caja)
        col.setContentsMargins(14, 8, 14, 8)
        col.setSpacing(0)
        nombre = QLabel(titulo)
        nombre.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        valor = QLabel(texto(0))
        valor.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {color};")
        col.addWidget(nombre)
        col.addWidget(valor)
        lay.addWidget(caja)
        return valor

    def _pintar_chips_hist(self):
        activo = (
            "QPushButton { background: #2563EB; color: white; border: none; border-radius: 8px; "
            "padding: 0 12px; font-weight: 700; font-size: 12px; }"
        )
        quieto = (
            "QPushButton { background: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 0 12px; font-weight: 700; font-size: 12px; }"
            "QPushButton:hover { background: #F8FAFC; }"
        )
        for nombre, btn in self._chips_hist.items():
            btn.setStyleSheet(activo if nombre == self._periodo_hist else quieto)

    def _elegir_periodo_hist(self, nombre):
        self._periodo_hist = nombre
        self._pintar_chips_hist()
        self._pintar_historial()

    def _cargar_combo_hist(self):
        actual = self._cb_hist_prov.currentData()
        nombres = sorted(
            {str(fila.get("proveedor") or "").strip() for fila in self._filas_hist if str(fila.get("proveedor") or "").strip()},
            key=str.upper,
        )
        self._cb_hist_prov.blockSignals(True)
        self._cb_hist_prov.clear()
        self._cb_hist_prov.addItem("Todos los proveedores", "")
        for nombre in nombres:
            self._cb_hist_prov.addItem(nombre, nombre)
        idx = self._cb_hist_prov.findData(actual if actual is not None else "")
        self._cb_hist_prov.setCurrentIndex(idx if idx >= 0 else 0)
        self._cb_hist_prov.blockSignals(False)

    def _fila_en_filtro(self, fila):
        desde, hasta = _rango_historial(self._periodo_hist)
        if desde is not None:
            dia = _fecha_de(fila.get("fecha"))
            if dia is None or dia < desde or dia > hasta:
                return False
        proveedor = self._cb_hist_prov.currentData() or ""
        if proveedor and str(fila.get("proveedor") or "").strip() != proveedor:
            return False
        estado = self._cb_hist_estado.currentData() or ""
        condicion = fila.get("condicion") or ""
        if estado == "Fiado" and condicion != "Fiado":
            return False
        if estado == "Pagado" and condicion not in ("Pagado", "Contado"):
            return False
        if estado == "Anulado" and condicion != "Anulado":
            return False
        return True

    def _pintar_historial(self):
        if not hasattr(self, "_tbl_prov"):
            return
        visibles = [fila for fila in self._filas_hist if self._fila_en_filtro(fila)]
        pagado = sum(float(fila.get("pagado") or 0) for fila in visibles)
        restante = sum(float(fila.get("restante") or 0) for fila in visibles)
        monto = sum(float(fila.get("monto") or 0) for fila in visibles)
        self._lbl_hist_cuenta.setText(f"{len(visibles)} compras")
        self._val_hist_pagado.setText(texto(pagado))
        self._val_hist_restante.setText(texto(restante))
        self._val_hist_monto.setText(texto(monto))

        self._tbl_prov.setRowCount(0)
        for r in visibles:
            row = self._tbl_prov.rowCount()
            self._tbl_prov.insertRow(row)

            condicion = r.get("condicion") or "Pagado"
            if condicion == "Fiado":
                estado_txt = "⏳ Fiado"
            elif condicion == "Anulado":
                estado_txt = "Anulada"
            else:
                estado_txt = f"✅ {condicion}"
            vals = [
                str(r["id"]),
                r["proveedor"],
                plata(r["monto"]),
                plata(r["pagado"]),
                plata(r["restante"]),
                _dia(r["fecha"]),
                estado_txt,
            ]

            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    vestir_id(it)
                elif c == 1:
                    vestir_nombre(it)
                elif c in (2, 3, 4):
                    vestir_numero(it)
                if c == 6 and "Fiado" in v:
                    it.setForeground(QColor(PAL["danger"]))
                elif c == 6 and v == "Anulada":
                    it.setForeground(QColor("#64748B"))
                elif c == 6 and ("Contado" in v or "Pagado" in v):
                    it.setForeground(QColor("#10B981"))
                self._tbl_prov.setItem(row, c, it)

            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            btn_ver = btn_ghost("👁️ Ver Remito")
            btn_ver.setFixedHeight(30)
            casa = r.get("origen") == "casa"
            rid = f"casa:{r['id']}" if casa else r["id"]
            btn_ver.clicked.connect(
                lambda _, rid=rid, d=r["desc_full"], rem=r["restante"], casa=casa, cond=condicion: self._show_remito_detail(rid, d, rem, casa, cond)
            )
            l.addWidget(btn_ver)
            if condicion != "Anulado" and (casa or not getattr(self, "_solo_lectura", False)):
                btn_anular = btn_ghost("Anular")
                btn_anular.setFixedHeight(30)
                btn_anular.setStyleSheet(
                    "QPushButton { background: #FFFFFF; color: #B91C1C; border: 1px solid #FECACA; "
                    "border-radius: 8px; padding: 0 10px; font-weight: 700; }"
                    "QPushButton:hover { background: #FEF2F2; }"
                )
                btn_anular.clicked.connect(lambda _, rid=rid: self._anular_compra(rid))
                l.addWidget(btn_anular)
            self._tbl_prov.setCellWidget(row, 7, w)

    def _anular_compra(self, debt_id) -> bool:
        if getattr(self, "_solo_lectura", False) and not str(debt_id).startswith("casa:"):
            QMessageBox.warning(
                self, "Sin conexión",
                "Esa factura es del negocio. La anulación espera la conexión con la tienda.",
            )
            return False
        aviso = QMessageBox(self)
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle("Anular carga")
        aviso.setText(
            "La factura queda en el historial como anulada y el stock vuelve al estado anterior.\n"
            "El registro no se borra."
        )
        aviso.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        aviso.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if aviso.exec() != QMessageBox.StandardButton.Ok:
            return False
        try:
            from src.proveedor_global.backend.cuenta import anular
            mensaje = anular(debt_id)
        except Exception as exc:
            QMessageBox.warning(self, "Anular carga", str(exc))
            return False
        QMessageBox.information(self, "Anulada", mensaje)
        self.cargar_datos()
        return True

    def _show_remito_detail(self, debt_id, desc, restante, casa=False, condicion=""):
        dlg = QDialog(self)
        dlg.setWindowTitle("📄 Detalle de Remito")
        dlg.setMinimumWidth(400)
        dlg.setStyleSheet(f"QDialog {{ background: {PAL['bg']}; }} QLabel {{ color: {PAL['text']}; font-size: 14px; }}")

        lay = QVBoxLayout(dlg)
        lbl_desc = QLabel(desc.replace("\n", "<br>"))
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)
        lay.addSpacing(20)

        if condicion != "Anulado" and restante > 0 and (casa or not getattr(self, "_solo_lectura", False)):
            btn_pagar = btn_primary(f"💳 Pagar Deuda (Falta {texto(restante)})")
            btn_pagar.clicked.connect(lambda: [dlg.accept(), self._pagar_proveedor(debt_id, restante)])
            lay.addWidget(btn_pagar)
        if condicion != "Anulado" and (casa or not getattr(self, "_solo_lectura", False)):
            btn_anular = btn_ghost("Anular carga")
            btn_anular.clicked.connect(lambda: self._anular_compra(debt_id) and dlg.accept())
            lay.addWidget(btn_anular)

        btn_cerrar = btn_ghost("Cerrar")
        btn_cerrar.clicked.connect(dlg.reject)
        lay.addWidget(btn_cerrar)
        qt_exec(dlg)

    def _pagar_proveedor(self, debt_id, restante):
        if getattr(self, "_solo_lectura", False) and not str(debt_id).startswith("casa:"):
            QMessageBox.warning(
                self, "Sin conexión", "La consulta está disponible, pero los pagos requieren conexión con la tienda."
            )
            return
        if restante <= 0:
            QMessageBox.information(self, "Aviso", "Esta cuenta ya está saldada.")
            return
        from src.proveedor_global.frontend.pago.dialogo import pedir_pago

        dato = pedir_pago(self, restante)
        if not dato:
            return
        try:
            MotorProveedor.pagar_proveedor(
                debt_id, dato["monto"], self.perfil, self._db_jefe,
                medio=dato["medio"], fecha=dato["fecha"], nota=dato["nota"],
            )
            QMessageBox.information(self, "Éxito", f"Pago de {texto(dato['monto'])} registrado.")
            self.cargar_datos()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo registrar el pago: {e}")

    def _cargar_combo_proveedores(self, conservar=True):
        texto = self._prov_nombre.currentText() if conservar else ""
        self._prov_nombre.blockSignals(True)
        self._prov_nombre.clear()
        self._prov_nombre.addItem("Sin Proveedor (Proveedor General)", {"nombre": "Proveedor General", "codigo": "P00000"})
        vistos = {"PROVEEDOR GENERAL"}
        for ficha in FichaProveedor.listar():
            self._prov_nombre.addItem(etiqueta(ficha), ficha)
            vistos.add(ficha["nombre"].strip().upper())
        for nombre in MotorProveedor.get_proveedores_unicos(self.perfil, self._db_jefe) or []:
            limpio = str(nombre or "").strip()
            if limpio and limpio.upper() not in vistos:
                self._prov_nombre.addItem(limpio)
                vistos.add(limpio.upper())
        if texto:
            self._prov_nombre.setCurrentText(texto)
        self._prov_nombre.blockSignals(False)

    def _alta_proveedor(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != QDialog.DialogCode.Accepted or not alta.ficha:
            return
        self._cargar_combo_proveedores(conservar=False)
        marca = etiqueta(alta.ficha)
        idx = self._prov_nombre.findText(marca)
        if idx >= 0:
            self._prov_nombre.setCurrentIndex(idx)

    def _save_proveedor(self):
        amount_text = self._prov_amount.text()
        if not amount_text or self._romaneo_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Debe cargar ítems y un monto total.")
            return

        try:
            amount = float(amount_text)
            date = self._prov_date.date().toString("yyyy-MM-dd")
            prov_name = nombre_de_eleccion(
                self._prov_nombre.currentText(), self._prov_nombre.currentData()
            )
            tropa = self._prov_tropa.text() or "-"

            grupos = {}
            for i in range(self._romaneo_table.rowCount()):
                nro = self._romaneo_table.item(i, 0).text()
                merc = self._romaneo_table.item(i, 1).text()
                cajas = float(self._romaneo_table.item(i, 2).text().replace(",", "."))
                kilos = float(self._romaneo_table.item(i, 3).text().replace(",", "."))
                precio = leer(self._romaneo_table.item(i, 4).text())
                key = (merc, precio)
                if key not in grupos:
                    grupos[key] = []
                grupos[key].append((nro, kilos, cajas))

            payment = self._prov_payment.currentText()

            success, msg = MotorProveedor.save_proveedor(
                date, prov_name, tropa, grupos, payment, amount, self.perfil, self._db_jefe
            )

            if success:
                QMessageBox.information(self, "Exito", "Compra registrada correctamente.")
                self._romaneo_table.setRowCount(0)
                self._prov_precio.clear()
                self._prov_amount.clear()
                self._romaneo_input.clear()
                self._prov_tropa.clear()
                self._cargar_combo_proveedores(conservar=False)
                if hasattr(self, '_prov_nombre'):
                    self._prov_nombre.setCurrentText("")
                self._update_prov_calc()
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", f"Error guardando proveedor: {msg}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error procesando la compra: {e}")

