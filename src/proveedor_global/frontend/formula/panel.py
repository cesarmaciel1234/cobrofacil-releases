"""Tarjetas de la fórmula. Cada categoría abre la lista que la compone."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from src.motor_descuentos.compartido import TarjetaModulo
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


def _listas():
    from src.jefe.promedios.carne.motor_carne import MotorCarne
    from src.jefe.promedios.cerdo.motor_cerdo import MotorCerdo
    from src.jefe.promedios.pollo.motor_pollo import MotorPollo

    return {
        "media_res": ("Media res", "Kilos", MotorCarne.get_cortes("Media Res")),
        "mocho": ("Mocho", "Kilos", MotorCarne.get_cortes("Mocho")),
        "pecho": ("Pecho", "Kilos", MotorCarne.get_cortes("Pecho")),
        "cerdo": ("Cerdo", "Kilos", MotorCerdo.get_cortes()),
        "pollo": ("Pollo", "Kilos", MotorPollo.get_cortes()),
        "huevo": ("Huevo", "Huevos", [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6),
        ]),
        "congelado": ("Congelado", "Kilos", [
            ("Pollo congelado kg", 0),
            ("Milanesa kg", 0),
            ("Nuggets kg", 0),
            ("Hamburguesa kg", 0),
            ("Papas congeladas kg", 0),
            ("Vegetales mix kg", 0),
        ]),
    }


def _kilos_jefe(codigo, filas):
    """Si el jefe ya dejó kilos, la lista muestra esos. Si no, la receta de fábrica."""
    tipo = {
        "media_res": "Media res",
        "mocho": "Mocho",
        "pecho": "Pecho",
        "pollo": "Pollo",
        "cerdo": "Cerdo",
        "congelado": "Congelado",
    }.get(codigo, "")
    if not tipo:
        return filas
    try:
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.frontend.formula.motores.orden import cortes
        pares = cortes(db_manager, tipo)
    except Exception:
        return filas
    return pares or filas


class PanelFormula(QWidget):
    cambio = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nivel = "raiz"
        self._origen = ""
        self.setStyleSheet("background: #F1F5F9;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._pila = QVBoxLayout()
        lay.addLayout(self._pila)
        self._paginas = {
            "raiz": self._grilla((
                ("carne", "🥩", "Carne", "Media res, mocho y pecho."),
                ("cerdo", "🐖", "Cerdo", "Los cortes que la componen."),
                ("pollo", "🍗", "Pollo", "Los cortes que la componen."),
                ("huevo", "🥚", "Huevo", "El cajón partido en maples."),
                ("congelado", "❄️", "Congelado", "Lo que entra congelado."),
                ("predictiva", "📈", "Compra predictiva", "Stock, reparto y feriados."),
            ), self._abrir_categoria),
            "carne": self._grilla((
                ("media_res", "🥩", "Media res", "Los cortes de la media res."),
                ("mocho", "🥩", "Mocho", "Los cortes del mocho."),
                ("pecho", "🥩", "Pecho", "Los cortes del pecho."),
            ), self._abrir_lista),
            "lista": self._tabla(),
            "huevo": self._pagina_huevo(),
            "predictiva": self._pagina_predictiva(),
        }
        for pagina in self._paginas.values():
            pagina.hide()
            self._pila.addWidget(pagina)
        self.inicio()

    def inicio(self):
        self._nivel = "raiz"
        self._origen = ""
        self._mostrar("raiz")
        self.cambio.emit("Fórmula", "Carne, cerdo, pollo, huevo, congelado y compra predictiva", "← Módulos")

    def retroceder(self) -> bool:
        if self._nivel == "lista" and self._origen == "carne":
            self._nivel = "carne"
            self._mostrar("carne")
            self.cambio.emit("Carne", "Media res, mocho o pecho", "← Fórmula")
            return True
        if self._nivel != "raiz":
            self.inicio()
            return True
        return False

    def _abrir_categoria(self, codigo):
        if codigo == "predictiva":
            self._nivel = "predictiva"
            self._origen = ""
            self._paginas["predictiva"].refrescar()
            self._mostrar("predictiva")
            self.cambio.emit("Compra predictiva", "Historial de stock", "← Fórmula")
            return
        if codigo == "carne":
            self._nivel = "carne"
            self._origen = "carne"
            self._mostrar("carne")
            self.cambio.emit("Carne", "Media res, mocho o pecho", "← Fórmula")
            return
        self._origen = ""
        self._abrir_lista(codigo)

    def _abrir_lista(self, codigo):
        if codigo == "huevo":
            self._pintar_huevo()
            self._nivel = "lista"
            self._origen = ""
            self._mostrar("huevo")
            self.cambio.emit("Huevo", "Del promedio, de 1 cajón y si se vende 1", "← Fórmula")
            return
        listas = _listas()
        titulo, columna, filas = listas.get(codigo, (codigo, "Kilos", []))
        filas = _kilos_jefe(codigo, filas)
        self._carne_viva = codigo in ("media_res", "mocho", "pecho", "pollo", "cerdo", "congelado")
        self._formula_carne = {
            "media_res": "Media res", "mocho": "Mocho", "pecho": "Pecho",
            "pollo": "Pollo", "cerdo": "Cerdo", "congelado": "Congelado",
        }.get(codigo, "")
        self._tabla_widget.setRowCount(len(filas))
        if self._carne_viva:
            self._tabla_widget.setColumnCount(6)
            self._tabla_widget.setHorizontalHeaderLabels(
                ["Código", "Mercadería", "Stock", "Vendido", "De este código", "Resta a"]
            )
            self._pintando = True
            try:
                for i, (nombre, cantidad) in enumerate(filas):
                    self._poner_corte(self._tabla_widget, i, nombre, cantidad)
            finally:
                self._pintando = False
            texto_lista = (
                "Arriba, Este es el producto dice el código y el nombre. "
                "Abajo, Enlazar y Quitar son solo de la oferta. "
                "El original lo trae el jefe en Promedios y no se borra."
            )
            if codigo == "pollo":
                texto_lista += " En Stock se puede cambiar el original a mano. La suma y el pedido siguen ese número."
                self._tabla_widget.setEditTriggers(
                    QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
                )
            else:
                self._tabla_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self._nota_lista.setText(texto_lista)
            if hasattr(self, "_nombre_original"):
                self._nombre_original.setText("")
            self._barra_pieza.show()
            self._nota_kilos.show()
            self._nota_carne.show()
            self._nota_carne_pedido.show()
            if codigo in ("media_res", "mocho", "pecho"):
                self._nota_carne.setText("Leyendo el stock compartido…")
            else:
                self._nota_carne.setText("Leyendo la orden del jefe…")
            self._nota_carne_pedido.setText("")
        else:
            self._tabla_widget.setColumnCount(2)
            self._tabla_widget.setHorizontalHeaderLabels(["Mercadería", columna])
            for i, (nombre, cantidad) in enumerate(filas):
                item_nombre = vestir_nombre(QTableWidgetItem(str(nombre)))
                item_cant = vestir_numero(QTableWidgetItem(f"{cantidad:g}"))
                item_cant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._tabla_widget.setItem(i, 0, item_nombre)
                self._tabla_widget.setItem(i, 1, item_cant)
            self._nota_lista.setText("Esta es la lista que arma la fórmula. El stock de cada una sale del producto base.")
            self._barra_pieza.hide()
            if hasattr(self, "_nota_carne"):
                self._nota_carne.hide()
                self._nota_carne_pedido.hide()
            if hasattr(self, "_nota_kilos"):
                self._nota_kilos.hide()
        cabecera = self._tabla_widget.horizontalHeader()
        if self._carne_viva:
            cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            for col in range(2, self._tabla_widget.columnCount()):
                cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
                self._tabla_widget.setColumnWidth(col, 110)
        else:
            cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for col in range(1, self._tabla_widget.columnCount()):
                cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
                self._tabla_widget.setColumnWidth(col, 110)
        self._cerrar_suma()
        self._pintar_kilos()
        self._nivel = "lista"
        if codigo in ("media_res", "mocho", "pecho"):
            self._origen = "carne"
            volver = "← Carne"
        else:
            volver = "← Fórmula"
        self._mostrar("lista")
        self.cambio.emit(titulo, "Lo que compone esta fórmula", volver)

    def _mostrar(self, cual):
        for clave, pagina in self._paginas.items():
            pagina.setVisible(clave == cual)
        if cual == "huevo":
            self._parar_carne()
            self._seguir_stock()
        elif cual == "lista" and getattr(self, "_carne_viva", False):
            self._parar_stock()
            self._seguir_carne()
        else:
            self._parar_stock()
            self._parar_carne()

    def _grilla(self, tarjetas, al_click):
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
            card.clicked.connect(lambda c=cod: al_click(c))
            grid.addWidget(card, i // 3, i % 3)
        grid.setRowStretch(2, 1)
        scroll.setWidget(wrap)
        lay.addWidget(scroll)
        return page

    def _pagina_predictiva(self):
        from src.proveedor_global.frontend.predictiva.panel import PanelPredictiva
        return PanelPredictiva(self)

    def _tabla(self):
        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 20, 28, 20)
        nota = QLabel("Esta es la lista que arma la fórmula. El stock de cada una sale del producto base.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color: #475569; font-size: 13px; background: transparent;")
        self._nota_lista = nota
        lay.addWidget(nota)
        self._barra_pieza = self._barra_codigos()
        self._barra_pieza.hide()
        lay.addWidget(self._barra_pieza)
        tabla = QTableWidget(0, 2)
        tabla.setHorizontalHeaderLabels(["Mercadería", "Kilos"])
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.itemChanged.connect(self._al_editar_stock)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.setColumnWidth(1, 120)
        tabla.setStyleSheet(
            "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; }"
            "QHeaderView::section { background: #F8FAFC; color: #0F172A; font-weight: 700; border: none; padding: 8px; }"
        )
        self._tabla_widget = tabla
        lay.addWidget(tabla, 1)
        self._nota_kilos = QLabel("")
        self._nota_kilos.setWordWrap(True)
        self._nota_kilos.setStyleSheet(
            "color: #475569; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._nota_kilos.hide()
        lay.addWidget(self._nota_kilos)
        self._nota_carne = QLabel("")
        self._nota_carne.setWordWrap(True)
        self._nota_carne.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: 700; background: transparent;"
        )
        self._nota_carne_pedido = QLabel("")
        self._nota_carne_pedido.setWordWrap(True)
        self._nota_carne_pedido.setStyleSheet(
            "color: #1D4ED8; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._nota_carne.hide()
        self._nota_carne_pedido.hide()
        lay.addWidget(self._nota_carne)
        lay.addWidget(self._nota_carne_pedido)
        return page

    def _pagina_huevo(self):
        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 16, 28, 16)
        lay.setSpacing(8)
        self._nota_huevo = QLabel("")
        self._nota_huevo.setWordWrap(True)
        self._nota_huevo.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: 700; background: transparent;"
        )
        lay.addWidget(self._nota_huevo)
        self._nota_venta = QLabel("")
        self._nota_venta.setWordWrap(True)
        self._nota_venta.setStyleSheet(
            "color: #1D4ED8; font-size: 14px; font-weight: 700; background: transparent;"
        )
        lay.addWidget(self._nota_venta)
        lay.addWidget(self._titulo_tabla("Cortes del promedio"))
        self._tbl_cortes = self._tabla_vacia(["Mercadería", "Huevos"])
        lay.addWidget(self._tbl_cortes, 1)
        lay.addWidget(self._titulo_tabla("De 1 cajón · 12 maples · 360 huevos"))
        self._tbl_cajon = self._tabla_vacia(["Fracción", "Huevos", "Maples", "Salen", "Stock", "Costo"])
        lay.addWidget(self._tbl_cajon, 1)
        self._periodo_mov = "Hoy"
        self._chips_mov = {}
        chips = QHBoxLayout()
        chips.setSpacing(6)
        from src.proveedor_global.frontend.formula.motores.movimientos import PERIODOS
        for nombre in PERIODOS:
            btn = QPushButton(nombre)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, n=nombre: self._elegir_periodo_mov(n))
            self._chips_mov[nombre] = btn
            chips.addWidget(btn)
        chips.addStretch()
        lay.addLayout(chips)
        self._pintar_chips_mov()
        self._tbl_venta = self._tabla_vacia(
            ["Fracción", "Vendido", "Reajuste", "Maples", "Huevos", "Queda"]
        )
        lay.addWidget(self._tbl_venta, 1)
        return page

    def _titulo_tabla(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: 800; background: transparent;")
        return lbl

    def _tabla_vacia(self, columnas):
        tabla = QTableWidget(0, len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        cabecera = tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cabecera.setMinimumSectionSize(84)
        cabecera.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col in range(1, len(columnas)):
            cabecera.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setStyleSheet(
            "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; }"
            "QHeaderView::section { background: #F8FAFC; color: #0F172A; font-weight: 700; border: none; padding: 8px; }"
        )
        return tabla

    def _poner(self, tabla, filas):
        tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for c, valor in enumerate(fila):
                item = QTableWidgetItem(str(valor))
                if c == 0:
                    vestir_nombre(item)
                else:
                    vestir_numero(item)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(i, c, item)

    def _pintar_huevo(self):
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.frontend.formula.motores.lectura import leer
        from src.proveedor_global.frontend.formula.motores import carga

        vivos = []
        try:
            vivos = leer(db_manager, "Huevo")
        except Exception:
            vivos = []
        cortes = vivos or _listas()["huevo"][2]
        rendimiento = []
        cajon = {"hallado": False, "nombre": "Cajón de huevo", "stock": 1.0}
        try:
            rendimiento = carga.de_un_cajon(cortes)
            cajon = carga.stock_cajon(db_manager)
        except Exception:
            rendimiento = []
        porciones = []
        try:
            porciones = carga.stock_porciones(rendimiento, cajon.get("stock") or 0)
        except Exception:
            porciones = []
        try:
            carga.publicar_formula(db_manager, rendimiento, cajon.get("nombre") or "Cajón de huevo")
        except Exception:
            pass
        resultado = {}
        if cajon.get("hallado"):
            try:
                from src.proveedor_global.frontend.formula.motores.inventario import enviar
                resultado = enviar(db_manager, cajon.get("id"), rendimiento) or {}
            except Exception:
                resultado = {}
        if resultado.get("ok"):
            try:
                porciones = carga.stock_porciones(rendimiento, resultado.get("stock") or 0)
            except Exception:
                pass
        compra = {}
        try:
            from src.proveedor_global.frontend.formula.motores.costo import de_reposicion
            compra = de_reposicion(db_manager, rendimiento) or {}
        except Exception:
            compra = {}
        por_compra = {linea["nombre"]: linea for linea in compra.get("lineas") or []}
        escritos = int(resultado.get("enviados") or 0)
        stock_visto = resultado.get("stock") if resultado.get("ok") else (cajon.get("stock") or 0)
        from src.proveedor_global.frontend.formula.motores.diferencia import etiquetar, texto_queda, texto_vendido
        from src.proveedor_global.frontend.formula.motores.carga import unidades
        from src.proveedor_global.frontend.formula.motores.costo import _parte
        from src.proveedor_global.frontend.formula.motores.verdad import leer as leer_verdad
        from src.proveedor_global.backend.moneda import texto as plata
        dato = leer_verdad(db_manager, "Huevo")
        cajones = float(dato.get("cajones") or 0)
        nombres = {
            int(fila["unidad"]): fila["nombre"]
            for fila in etiquetar(db_manager, [(n, h) for n, h in cortes])
        }
        self._poner(self._tbl_cortes, [
            (nombres.get(int(round(float(h))), n), f"{h:g}" if not isinstance(h, str) else h)
            for n, h in cortes
        ])
        filas_cajon = []
        for p in porciones:
            unidad = int(round(float(p["huevos"])))
            filas_cajon.append((
                nombres.get(unidad, p["nombre"]),
                f"{p['huevos']:g}",
                p.get("maples") or "",
                f"{p['salen']:g}",
                str(unidades(cajones, p["huevos"])),
                plata(_parte(dato.get("costo"), p["salen"])),
            ))
        self._poner(self._tbl_cajon, filas_cajon)
        self._rendimiento_huevo = rendimiento
        self._cajones_huevo = cajones
        self._costo_cajon_texto = plata(dato.get("costo") or 0)
        self._nota_huevo.setText(texto_queda(cajones, self._costo_cajon_texto))
        self._nota_venta.setText(texto_vendido([], getattr(self, "_periodo_mov", "Hoy")))
        self._pintar_cuadro_vacio()
        self._pedir_stock()

    def _pintar_chips_mov(self):
        activo = (
            "QPushButton { background: #2563EB; color: white; border: none; border-radius: 8px; "
            "padding: 0 10px; font-weight: 700; font-size: 12px; }"
        )
        quieto = (
            "QPushButton { background: white; color: #334155; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 0 10px; font-weight: 700; font-size: 12px; }"
        )
        for nombre, btn in self._chips_mov.items():
            btn.setStyleSheet(activo if nombre == self._periodo_mov else quieto)

    def _elegir_periodo_mov(self, nombre):
        self._periodo_mov = nombre
        self._pintar_chips_mov()
        self._pedir_stock()

    def _seguir_stock(self):
        if getattr(self, "_reloj_stock", None) is None:
            self._reloj_stock = QTimer(self)
            self._reloj_stock.setInterval(8000)
            self._reloj_stock.timeout.connect(self._pedir_stock)
        if not self._reloj_stock.isActive():
            self._reloj_stock.start()

    def _parar_stock(self):
        reloj = getattr(self, "_reloj_stock", None)
        if reloj is not None and reloj.isActive():
            reloj.stop()

    def _seguir_carne(self):
        if getattr(self, "_reloj_carne", None) is None:
            self._reloj_carne = QTimer(self)
            self._reloj_carne.setInterval(8000)
            self._reloj_carne.timeout.connect(self._pedir_carne)
        if not self._reloj_carne.isActive():
            self._reloj_carne.start()
        self._pedir_carne()

    def _parar_carne(self):
        reloj = getattr(self, "_reloj_carne", None)
        if reloj is not None and reloj.isActive():
            reloj.stop()

    def _pedir_carne(self):
        if not getattr(self, "_carne_viva", False):
            return
        hilo = getattr(self, "_hilo_carne", None)
        if hilo is not None and hilo.isRunning():
            self._carne_pendiente = True
            return
        from src.proveedor_global.frontend.formula.motores.hilo import HiloCarne

        self._hilo_carne = HiloCarne(getattr(self, "_formula_carne", "Mocho"), self)
        self._hilo_carne.listo.connect(self._aplicar_carne)
        self._hilo_carne.finished.connect(self._al_terminar_carne)
        self._carne_pendiente = False
        self._hilo_carne.start()

    def _al_terminar_carne(self):
        if getattr(self, "_carne_pendiente", False):
            self._carne_pendiente = False
            self._pedir_carne()

    def _barra_codigos(self):
        caja = QWidget()
        caja.setStyleSheet("background: transparent;")
        columna = QVBoxLayout(caja)
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(8)
        self._codigo_pieza = self._casillero("Código del producto")
        self._codigo_enlace = self._casillero("Código a enlazar")
        self._codigo_pieza.returnPressed.connect(self._marcar_producto)
        self._codigo_enlace.returnPressed.connect(self._sumar_codigo)
        base = self._boton_pieza("Este es el producto")
        sumar = self._boton_pieza("Enlazar")
        quitar = self._boton_pieza("Quitar")
        base.clicked.connect(self._marcar_producto)
        sumar.clicked.connect(self._sumar_codigo)
        quitar.clicked.connect(self._quitar_codigo)
        self._nombre_original = QLabel("")
        self._nombre_original.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: 700; background: transparent;"
        )
        self._aviso_pieza = QLabel("")
        self._aviso_pieza.setWordWrap(True)
        self._aviso_pieza.setStyleSheet("color: #B91C1C; font-size: 13px; background: transparent;")
        arriba = QHBoxLayout()
        arriba.setSpacing(8)
        arriba.addWidget(self._rotulo("Código del producto"))
        arriba.addWidget(self._codigo_pieza)
        arriba.addWidget(base)
        arriba.addWidget(self._nombre_original, 1)
        abajo = QHBoxLayout()
        abajo.setSpacing(8)
        abajo.addWidget(self._rotulo("Código a enlazar"))
        abajo.addWidget(self._codigo_enlace)
        abajo.addWidget(sumar)
        abajo.addWidget(quitar)
        abajo.addWidget(self._aviso_pieza, 1)
        columna.addLayout(arriba)
        columna.addLayout(abajo)
        return caja

    def _casillero(self, pista: str) -> QLineEdit:
        caja = QLineEdit()
        caja.setPlaceholderText(pista)
        caja.setFixedWidth(180)
        caja.setFixedHeight(36)
        caja.setStyleSheet(
            "QLineEdit { background: white; border: 1px solid #CBD5E1; border-radius: 8px; "
            "padding: 0 10px; font-size: 14px; color: #0F172A; }"
        )
        return caja

    def _rotulo(self, texto: str) -> QLabel:
        rotulo = QLabel(texto)
        rotulo.setStyleSheet("color: #334155; font-size: 13px; font-weight: 700; background: transparent;")
        return rotulo

    def _boton_pieza(self, texto: str) -> QPushButton:
        boton = QPushButton(texto)
        boton.setFixedHeight(36)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setStyleSheet(
            "QPushButton { background: white; color: #0F172A; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 0 12px; font-size: 13px; font-weight: 700; }"
            "QPushButton:hover { background: #F8FAFC; }"
        )
        return boton

    def _poner_corte(self, tabla, fila, nombre, kilos, codigo="", stock=None, vendido=None, propio=None):
        codigo_item = vestir_id(QTableWidgetItem(str(codigo or "—")))
        codigo_item.setData(Qt.ItemDataRole.UserRole, "corte")
        codigo_item.setData(Qt.ItemDataRole.UserRole + 1, str(nombre or ""))
        nombre_item = vestir_nombre(QTableWidgetItem(str(nombre or "")))
        try:
            codigo_item.setData(Qt.ItemDataRole.UserRole + 3, float(kilos or 0))
        except (TypeError, ValueError):
            codigo_item.setData(Qt.ItemDataRole.UserRole + 3, 0.0)
        tabla.setItem(fila, 0, codigo_item)
        tabla.setItem(fila, 1, nombre_item)
        self._poner_numero(
            tabla, fila, 2, "—" if stock is None else self._aprox(stock),
            editable=self._formula_carne == "Pollo" and stock is not None,
        )
        self._poner_numero(tabla, fila, 3, "0" if vendido is None else self._aprox(vendido))
        de_este = vendido if propio is None else propio
        self._poner_numero(tabla, fila, 4, "—" if de_este is None else self._aprox(de_este))
        resta = vestir_nombre(QTableWidgetItem("Su stock"))
        tabla.setItem(fila, 5, resta)

    def _poner_anexo(self, tabla, fila, corte, anexo, stock=None):
        codigo_item = vestir_id(QTableWidgetItem(str(anexo.get("codigo") or "—")))
        codigo_item.setData(Qt.ItemDataRole.UserRole, "anexo")
        codigo_item.setData(Qt.ItemDataRole.UserRole + 1, str(corte or ""))
        codigo_item.setData(Qt.ItemDataRole.UserRole + 2, str(anexo.get("id") or ""))
        codigo_item.setBackground(QColor("#F8FAFC"))
        nombre_item = vestir_nombre(QTableWidgetItem(str(anexo.get("nombre") or "")))
        nombre_item.setBackground(QColor("#F8FAFC"))
        tabla.setItem(fila, 0, codigo_item)
        tabla.setItem(fila, 1, nombre_item)
        self._poner_numero(
            tabla, fila, 2, "—" if stock is None else self._aprox(stock), "#94A3B8",
        )
        self._poner_numero(tabla, fila, 3, self._aprox(anexo.get("vendido")))
        self._poner_numero(tabla, fila, 4, self._aprox(anexo.get("vendido")))
        resta = vestir_nombre(QTableWidgetItem(str(corte or "")))
        resta.setBackground(QColor("#F8FAFC"))
        tabla.setItem(fila, 5, resta)
        for col in range(2, 5):
            celda = tabla.item(fila, col)
            if celda is not None:
                celda.setBackground(QColor("#F8FAFC"))

    def _corte_elegido(self) -> str:
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None:
            return ""
        fila = tabla.currentRow()
        if fila >= 0:
            marca = tabla.item(fila, 0)
            if marca is not None and marca.text().strip().upper() != "TOTAL":
                corte = str(marca.data(Qt.ItemDataRole.UserRole + 1) or "")
                if corte:
                    return corte
        codigo = self._codigo_pieza.text().strip() if hasattr(self, "_codigo_pieza") else ""
        if not codigo:
            return ""
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
                continue
            if marca.text().strip() == codigo:
                return str(marca.data(Qt.ItemDataRole.UserRole + 1) or "")
        return ""

    def _volver_a(self, corte: str) -> None:
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None or not corte:
            return
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
                continue
            if str(marca.data(Qt.ItemDataRole.UserRole + 1) or "") == corte:
                tabla.setCurrentCell(i, 1)
                return

    def _aviso(self, texto: str, ok: bool) -> None:
        color = "#047857" if ok else "#B91C1C"
        self._aviso_pieza.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent;")
        self._aviso_pieza.setText(texto)

    def _producto_de(self, codigo: str) -> dict:
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.pieza import _producto
            return _producto(db_manager, codigo) or {}
        except Exception:
            return {}

    def _marcar_producto(self):
        codigo = self._codigo_pieza.text().strip() if hasattr(self, "_codigo_pieza") else ""
        if not codigo:
            self._nombre_original.setText("Escribí el código del producto.")
            return
        prod = self._producto_de(codigo)
        if not prod:
            self._nombre_original.setText(f"No hay un producto con el código {codigo}.")
            return
        nombre = str(prod.get("nombre") or "").strip()
        self._nombre_original.setText(f"{codigo} es {nombre}")
        corte = self._cortes_por_codigo().get(codigo, "")
        if not corte:
            buscado = nombre.upper()
            tabla = getattr(self, "_tabla_widget", None)
            if tabla is not None:
                for i in range(tabla.rowCount()):
                    marca = tabla.item(i, 0)
                    if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
                        continue
                    if str(marca.data(Qt.ItemDataRole.UserRole + 1) or "").upper() == buscado:
                        corte = str(marca.data(Qt.ItemDataRole.UserRole + 1) or "")
                        break
        if not corte:
            self._nombre_original.setText(
                f"{codigo} es {nombre}. No está en esta receta. Lo carga el jefe en Promedios."
            )
            return
        self._volver_a(corte)

    def _sumar_codigo(self):
        codigo = self._codigo_enlace.text().strip() if hasattr(self, "_codigo_enlace") else ""
        if not codigo:
            self._aviso("Escribí el código a enlazar.", False)
            return
        if codigo in self._cortes_por_codigo():
            self._aviso("Ese es el producto original. Solo se enlaza una oferta.", False)
            return
        corte = self._cortes_por_codigo().get(self._codigo_pieza.text().strip(), "")
        if not corte:
            corte = self._corte_elegido()
        if not corte:
            self._aviso("Primero apretá Este es el producto.", False)
            return
        ya = self._fila_de_anexo(codigo)
        if ya >= 0:
            self._recalcar_codigo(codigo)
            self._aviso(f"{codigo} ya está enlazado a {corte}.", True)
            return
        prod = self._producto_de(codigo)
        if not prod:
            self._aviso(f"No hay un producto con el código {codigo}.", False)
            return
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.pieza import sumar
            aviso = sumar(db_manager, self._formula_carne, corte, codigo)
        except Exception:
            aviso = "No se pudo enlazar."
        if aviso:
            self._aviso(aviso, False)
            return
        self._fila_enlace(corte, codigo)
        self._recalcar_codigo(codigo)
        self._codigo_enlace.clear()
        self._aviso(f"{codigo} enlazado a {corte}.", True)
        self._pedir_carne()

    def _cortes_por_codigo(self) -> dict:
        tabla = getattr(self, "_tabla_widget", None)
        salida = {}
        if tabla is None:
            return salida
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
                continue
            cod = marca.text().strip()
            nombre = str(marca.data(Qt.ItemDataRole.UserRole + 1) or "")
            if cod and cod != "—" and nombre:
                salida[cod] = nombre
        return salida

    def _oferta_automatica(self, propio: str, enlace: str):
        """Si un código ya es un corte, el otro es la oferta. No hace falta elegir la fila."""
        cortes = self._cortes_por_codigo()
        if propio in cortes and enlace in cortes and propio != enlace:
            return "", "", self._codigo_enlace
        if enlace in cortes and propio and propio not in cortes:
            return cortes[enlace], propio, self._codigo_pieza
        if propio in cortes and enlace and enlace not in cortes:
            return cortes[propio], enlace, self._codigo_enlace
        corte = self._corte_elegido()
        codigo_corte = ""
        for cod, nombre in cortes.items():
            if nombre == corte:
                codigo_corte = cod
                break
        if enlace and enlace == codigo_corte and propio and propio != enlace:
            return corte, propio, self._codigo_pieza
        return corte, enlace, self._codigo_enlace

    def _usar_codigo(self, es_base: bool) -> None:
        propio = self._codigo_pieza.text().strip() if hasattr(self, "_codigo_pieza") else ""
        enlace = self._codigo_enlace.text().strip() if hasattr(self, "_codigo_enlace") else ""
        if es_base:
            corte = self._corte_elegido()
            codigo = propio
            caja = self._codigo_pieza
        else:
            corte, codigo, caja = self._oferta_automatica(propio, enlace)
            if propio in self._cortes_por_codigo() and enlace in self._cortes_por_codigo() and propio != enlace:
                self._aviso_pieza.setStyleSheet("color: #B91C1C; font-size: 13px; background: transparent;")
                self._aviso_pieza.setText("Los dos códigos ya son cortes. El segundo tiene que ser la oferta.")
                return
        if not corte:
            self._aviso_pieza.setStyleSheet("color: #B91C1C; font-size: 13px; background: transparent;")
            self._aviso_pieza.setText("Escribí el código del producto, el de Pata Muslo, o elegí la fila.")
            return
        if not codigo:
            self._aviso_pieza.setText(
                "Escribí el código del producto." if es_base else "Escribí el código a enlazar."
            )
            return
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.pieza import es_el_producto, sumar
            aviso = es_el_producto(db_manager, self._formula_carne, corte, codigo) if es_base else sumar(
                db_manager, self._formula_carne, corte, codigo
            )
        except Exception:
            aviso = "No se pudo guardar el código."
        if aviso:
            self._aviso_pieza.setStyleSheet("color: #B91C1C; font-size: 13px; background: transparent;")
            self._aviso_pieza.setText(aviso)
            return
        self._aviso_pieza.setStyleSheet("color: #047857; font-size: 13px; background: transparent;")
        if es_base:
            self._aviso_pieza.setText(f"{codigo} quedó como stock de {corte}.")
        else:
            self._aviso_pieza.setText(
                f"{codigo} quedó enlazado a {corte}. Otra oferta: escribí el próximo código y sumá de nuevo."
            )
            self._fila_enlace(corte, codigo)
        caja.clear()
        self._pedir_carne()

    def _fila_enlace(self, corte: str, codigo: str) -> None:
        """Muestra la oferta enseguida, debajo del corte, sin esperar el hilo."""
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None:
            return
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.pieza import _producto
            prod = _producto(db_manager, codigo) or {}
        except Exception:
            prod = {}
        destino = -1
        stock = None
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
                continue
            if str(marca.data(Qt.ItemDataRole.UserRole + 1) or "") != corte:
                continue
            destino = i + 1
            celda = tabla.item(i, 2)
            if celda is not None and celda.text().strip() not in ("", "—"):
                try:
                    stock = float(celda.text().replace(",", "."))
                except ValueError:
                    stock = None
            break
        if destino < 0:
            return
        while destino < tabla.rowCount():
            marca = tabla.item(destino, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "anexo":
                break
            if marca.text().strip() == str(prod.get("codigo") or codigo):
                return
            destino += 1
        tabla.insertRow(destino)
        self._poner_anexo(tabla, destino, corte, {
            "id": prod.get("id") or "",
            "codigo": prod.get("codigo") or codigo,
            "nombre": prod.get("nombre") or codigo,
            "vendido": 0,
        }, stock)
        self._cerrar_suma()

    def _fila_de_anexo(self, codigo: str) -> int:
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None or not codigo:
            return -1
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "anexo":
                continue
            if marca.text().strip() == codigo:
                return i
        return -1

    def _recalcar_codigo(self, codigo: str) -> None:
        self._marca_codigo = str(codigo or "").strip()
        self._pintar_marca()

    def _pintar_marca(self) -> None:
        codigo = str(getattr(self, "_marca_codigo", "") or "").strip()
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None or not codigo:
            return
        for i in range(tabla.rowCount()):
            marca = tabla.item(i, 0)
            if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "anexo":
                continue
            color = "#FEF3C7" if marca.text().strip() == codigo else "#F8FAFC"
            if marca.text().strip() == codigo:
                tabla.setCurrentCell(i, 0)
            for col in range(tabla.columnCount()):
                celda = tabla.item(i, col)
                if celda is not None:
                    celda.setBackground(QColor(color))

    def _quitar_codigo(self):
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None:
            return
        codigo = self._codigo_enlace.text().strip() if hasattr(self, "_codigo_enlace") else ""
        if not codigo:
            self._aviso("Escribí el código a enlazar.", False)
            return
        if codigo in self._cortes_por_codigo():
            self._aviso("El producto original no se borra. Lo cambia el jefe en Promedios.", False)
            return
        fila = self._fila_de_anexo(codigo)
        if fila < 0:
            self._aviso(f"{codigo} no existe.", False)
            return
        marca = tabla.item(fila, 0)
        corte = str(marca.data(Qt.ItemDataRole.UserRole + 1) or "") if marca is not None else ""
        ident = str(marca.data(Qt.ItemDataRole.UserRole + 2) or "") if marca is not None else ""
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.pieza import quitar
            ok = quitar(db_manager, ident, codigo)
        except Exception:
            ok = False
        if not ok:
            self._aviso("No se pudo quitar.", False)
            return
        tabla.removeRow(fila)
        self._cerrar_suma()
        self._codigo_enlace.clear()
        if getattr(self, "_marca_codigo", "") == codigo:
            self._marca_codigo = ""
        self._aviso(f"{codigo} of. {corte} quitado", True)
        self._pedir_carne()

    def _al_editar_stock(self, item):
        if getattr(self, "_pintando", False) or item is None or item.column() != 2:
            return
        if getattr(self, "_formula_carne", "") != "Pollo":
            return
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None:
            return
        marca = tabla.item(item.row(), 0)
        if marca is None or marca.data(Qt.ItemDataRole.UserRole) != "corte":
            return
        texto = item.text().replace(",", ".").replace("—", "").strip()
        try:
            numero = float(texto)
        except (TypeError, ValueError):
            self._aviso("El stock tiene que ser un número.", False)
            self._pedir_carne()
            return
        codigo = marca.text().strip()
        ofertas = []
        for i in range(item.row() + 1, tabla.rowCount()):
            otra = tabla.item(i, 0)
            if otra is None or otra.data(Qt.ItemDataRole.UserRole) != "anexo":
                break
            ofertas.append(str(otra.data(Qt.ItemDataRole.UserRole + 2) or ""))
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.inventario import fijar
            ok = fijar(db_manager, codigo, numero, ofertas)
        except Exception:
            ok = False
        if not ok:
            self._aviso("No se pudo guardar el stock.", False)
            self._pedir_carne()
            return
        self._aviso(f"{codigo} quedó en {self._aprox(numero)} kg.", True)
        self._pedir_carne()

    def _aplicar_carne(self, dato):
        if not isinstance(dato, dict) or not getattr(self, "_carne_viva", False):
            return
        if hasattr(self, "_nota_carne"):
            self._nota_carne.setText("Info se extrae de promedio jefe.")
            self._nota_carne_pedido.setText("")
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None or tabla.columnCount() < 6:
            return
        elegido = self._corte_elegido()
        self._pintando = True
        try:
            self._pintar_cortes(tabla, dato, elegido)
        finally:
            self._pintando = False

    def _pintar_cortes(self, tabla, dato, elegido):
        tabla.setRowCount(0)
        for corte in dato.get("cortes") or []:
            fila = tabla.rowCount()
            tabla.insertRow(fila)
            self._poner_corte(
                tabla, fila, corte.get("nombre") or "", corte.get("kilos") or 0,
                corte.get("codigo") or "", corte.get("stock"), corte.get("vendido"),
                corte.get("propio"),
            )
            for anexo in corte.get("anexos") or []:
                fila = tabla.rowCount()
                tabla.insertRow(fila)
                self._poner_anexo(
                    tabla, fila, corte.get("nombre") or "", anexo, corte.get("stock"),
                )
        self._cerrar_suma()
        self._volver_a(elegido)
        self._pintar_marca()
        self._pintar_kilos()

    def _pintar_kilos(self) -> None:
        """La receta larga no se muestra. La info sale del promedio del jefe."""
        nota = getattr(self, "_nota_kilos", None)
        if nota is not None:
            nota.setText("")

    def _cerrar_suma(self):
        """La última fila suma el stock y lo vendido del original. El enlace no entra."""
        tabla = getattr(self, "_tabla_widget", None)
        if tabla is None or tabla.rowCount() < 1 or tabla.columnCount() < 2:
            return
        ultima = tabla.rowCount() - 1
        titulo = tabla.item(ultima, 0)
        if titulo is None or titulo.text().strip().upper() != "TOTAL":
            tabla.insertRow(tabla.rowCount())
            ultima = tabla.rowCount() - 1
            nombre = vestir_nombre(QTableWidgetItem("Total"))
            tabla.setItem(ultima, 0, nombre)
        columnas = (2, 3) if tabla.columnCount() >= 6 else range(1, tabla.columnCount())
        for col in columnas:
            total = 0.0
            hay = False
            for i in range(ultima):
                marca = tabla.item(i, 0)
                if marca is not None and marca.data(Qt.ItemDataRole.UserRole) == "anexo":
                    continue
                celda = tabla.item(i, col)
                if celda is None:
                    continue
                texto = celda.text().replace(",", ".").replace("—", "").strip()
                if not texto:
                    continue
                try:
                    total += float(texto)
                    hay = True
                except ValueError:
                    continue
            self._poner_numero(tabla, ultima, col, self._aprox(total) if hay else "0")
        for col in range(tabla.columnCount()):
            celda = tabla.item(ultima, col)
            if celda is not None:
                celda.setBackground(QColor("#F8FAFC"))

    def _poner_numero(self, tabla, fila, col, texto, color: str = "", editable: bool = False):
        item = vestir_numero(QTableWidgetItem(str(texto)))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if editable:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        else:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if color:
            item.setForeground(QColor(color))
        tabla.setItem(fila, col, item)

    def _pedir_stock(self):
        if not hasattr(self, "_tbl_venta"):
            return
        hilo = getattr(self, "_hilo_stock", None)
        if hilo is not None and hilo.isRunning():
            self._stock_pendiente = True
            return
        from src.proveedor_global.frontend.formula.motores.hilo import HiloFormula

        cortes = [
            {"nombre": item.get("nombre"), "huevos": item.get("huevos")}
            for item in (getattr(self, "_rendimiento_huevo", None) or [])
            if isinstance(item, dict)
        ]
        self._hilo_stock = HiloFormula(getattr(self, "_periodo_mov", "Hoy"), cortes, self)
        self._hilo_stock.listo.connect(self._aplicar_stock)
        self._hilo_stock.finished.connect(self._al_terminar_stock)
        self._stock_pendiente = False
        self._hilo_stock.start()

    def _al_terminar_stock(self):
        if getattr(self, "_stock_pendiente", False):
            self._stock_pendiente = False
            self._pedir_stock()

    def _aplicar_stock(self, dato):
        if not isinstance(dato, dict) or not hasattr(self, "_tbl_venta"):
            return
        self._cajones_huevo = float(dato.get("cajones") or 0)
        self._poner(self._tbl_venta, [
            (
                linea.get("nombre") or "",
                self._aprox(linea.get("vendido")),
                self._aprox(linea.get("reajuste")),
                linea.get("maples") or "",
                f"{float(linea.get('huevos') or 0):g}",
                self._aprox(linea.get("queda")),
            )
            for linea in dato.get("filas") or []
        ])
        self._marcar_stock(dato.get("filas") or [])
        self._igualar_nombres(dato.get("filas") or [])
        from src.proveedor_global.frontend.formula.motores.diferencia import texto_queda, texto_vendido
        costo = getattr(self, "_costo_cajon_texto", "")
        self._nota_huevo.setText(texto_queda(self._cajones_huevo, costo))
        if hasattr(self, "_nota_venta"):
            self._nota_venta.setText(texto_vendido(dato.get("filas") or [], getattr(self, "_periodo_mov", "Hoy")))

    def _igualar_nombres(self, filas):
        for fila in filas:
            try:
                unidad = str(int(fila.get("unidad") or 0))
            except (TypeError, ValueError):
                continue
            nombre = fila.get("nombre") or ""
            if not nombre or unidad == "0":
                continue
            self._renombrar_fila(getattr(self, "_tbl_cortes", None), 1, unidad, nombre)
            self._renombrar_fila(getattr(self, "_tbl_cajon", None), 1, unidad, nombre)

    def _renombrar_fila(self, tabla, col_huevos, unidad, nombre):
        if tabla is None:
            return
        for i in range(tabla.rowCount()):
            celda = tabla.item(i, col_huevos)
            if celda is None or not self._misma_unidad(celda.text(), unidad):
                continue
            titulo = tabla.item(i, 0)
            if titulo is not None:
                titulo.setText(nombre)
            return

    def _misma_unidad(self, texto, unidad) -> bool:
        try:
            return int(round(float(str(texto).replace(",", ".")))) == int(unidad)
        except (TypeError, ValueError):
            return False

    def _marcar_stock(self, filas):
        tabla = getattr(self, "_tbl_cajon", None)
        if tabla is None:
            return
        for i, linea in enumerate(filas):
            if i >= tabla.rowCount():
                break
            item = tabla.item(i, 4)
            if item is not None:
                item.setText(self._aprox(linea.get("queda")))

    def _pintar_cuadro_vacio(self):
        if hasattr(self, "_tbl_venta"):
            self._tbl_venta.setRowCount(0)

    def _aprox(self, numero) -> str:
        try:
            numero = float(numero or 0)
        except (TypeError, ValueError):
            return "0"
        if abs(numero - round(numero)) < 1e-4:
            return str(int(round(numero)))
        return f"{numero:.2f}"
