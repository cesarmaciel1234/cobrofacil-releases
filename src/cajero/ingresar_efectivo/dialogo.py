"""Junta Cambio, Fiado y Otros. No cobra la venta."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout

from src.cajero.ingresar_efectivo.cambio.panel import PanelIngresoEfectivo
from src.cajero.ingresar_efectivo.fiado.paleta import PALETA
from src.cajero.ingresar_efectivo.fiado.panel import CentroCobranzasPanel
from src.cajero.ingresar_efectivo.opciones.boton import boton_opcion
from src.cajero.ingresar_efectivo.otros.panel import PanelOtrosIngresos
from src.cajero.ingresar_efectivo.pie.botones import fila_pie


class DialogoIngresoEfectivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""
        self.tipo_ingreso = "FIADO"
        self.cliente_id = None
        self.cliente_nombre = ""
        self.en_venta = False
        self.deuda_actual = 0.0
        self.resultado = None
        self._directo = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._armar()
        self._atajo_f9 = QShortcut(QKeySequence(Qt.Key.Key_F9), self)
        self._atajo_f9.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._atajo_f9.activated.connect(self._f9)

    def showEvent(self, event):
        from src.utils.fondo_gris import cubrir
        cubrir(self)
        self._ajustar_pagina()
        super().showEvent(event)

    def paintEvent(self, event):
        from src.utils.fondo_gris import pintar
        pintar(self)

    def _armar(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.paginas = QStackedWidget()
        exterior.addWidget(self.paginas)
        self.paginas.addWidget(self._pagina_opciones())
        self.paginas.addWidget(self._pagina_formulario())
        self.pagina_cobro = None
        self.paginas.addWidget(self._pagina_cobro())
        self._mostrar_opciones()

    def _ajustar_pagina(self):
        ancho = max(400, min(960, self.width() - 64))
        alto = max(400, min(700, self.height() - 40))
        self.paginas.setFixedSize(ancho, alto)

    def _pagina_opciones(self):
        hoja = QFrame()
        hoja.setObjectName("IngresoOpciones")
        hoja.setStyleSheet(
            "QFrame#IngresoOpciones { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 24px; }"
            "QLabel { background: transparent; border: none; color: #0F172A; }"
        )
        caja = QVBoxLayout(hoja)
        caja.setContentsMargins(56, 52, 56, 52)
        caja.setSpacing(12)
        marca = QLabel("CENTRO DE COBRANZAS")
        marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marca.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 900; letter-spacing: 2px;"
        )
        caja.addWidget(marca)
        titulo = QLabel("¿Qué ingreso vas a registrar?")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #0F172A; font-size: 25px; font-weight: 900;")
        caja.addWidget(titulo)
        subtitulo = QLabel("Elige una opción para continuar")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #64748B; font-size: 14px; font-weight: 500;")
        caja.addWidget(subtitulo)
        caja.addSpacing(8)
        fila = QHBoxLayout()
        fila.setSpacing(16)
        fila.setContentsMargins(0, 0, 0, 0)
        self.btn_cambio = boton_opcion(
            "🪙", "CAMBIO", "#D97706", "Registrar fondo fijo o cambio de caja"
        )
        self.btn_fiado = boton_opcion(
            "👥", "FIADO", PALETA["accent"], "Buscar un cliente y registrar un abono"
        )
        self.btn_otros = boton_opcion(
            "📦", "OTROS", "#6366F1", "Ingresar dinero con otro concepto"
        )
        opciones = (self.btn_cambio, self.btn_fiado, self.btn_otros)
        for opcion in opciones:
            opcion.establecer_opciones(opciones)
        self.btn_cambio.clicked.connect(lambda: self._set_modo("CAMBIO"))
        self.btn_fiado.clicked.connect(lambda: self._set_modo("FIADO"))
        self.btn_otros.clicked.connect(lambda: self._set_modo("OTROS"))
        fila.addWidget(self.btn_cambio, 1)
        fila.addWidget(self.btn_fiado, 1)
        fila.addWidget(self.btn_otros, 1)
        caja.addLayout(fila, 1)
        pie = QLabel("Selecciona una tarjeta para abrir el formulario")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pie.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600;")
        caja.addWidget(pie)
        return hoja

    def _pagina_formulario(self):
        hoja = QFrame()
        hoja.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 18px; }"
        )
        caja = QVBoxLayout(hoja)
        caja.setContentsMargins(20, 20, 20, 20)
        caja.setSpacing(10)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.panel_cambio = PanelIngresoEfectivo()
        self.panel_fiado = CentroCobranzasPanel()
        self.panel_otros = PanelOtrosIngresos()
        self.panel_cambio.txt_monto.returnPressed.connect(self._procesar)
        if hasattr(self.panel_fiado, 'txt_monto'):
            self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
        self.panel_otros.txt_monto.returnPressed.connect(self._procesar)
        self.panel_otros.txt_desc.returnPressed.connect(self._procesar)
        
        # Conectar senales del nuevo ecosistema
        if hasattr(self.panel_fiado, 'abono_registrado'):
            self.panel_fiado.abono_registrado.connect(self._on_abono_registrado)
        if hasattr(self.panel_fiado, 'cancelado'):
            self.panel_fiado.cancelado.connect(self.reject)
        self.stack.addWidget(self.panel_cambio)
        self.stack.addWidget(self.panel_fiado)
        self.stack.addWidget(self.panel_otros)
        caja.addWidget(self.stack)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        caja.addWidget(self.lbl_err)
        caja.addLayout(fila_pie(self._volver, self._procesar))
        return hoja

    def _pagina_cobro(self):
        from src.cajero.ingresar_efectivo.medios.pagina import PaginaCobroAbono

        self.pagina_cobro = PaginaCobroAbono(self)
        return self.pagina_cobro

    def volver_al_importe(self):
        self.paginas.setCurrentIndex(1)

    def cerrar_con_medio(self, resultado):
        self.resultado = resultado
        self.accept()

    def _mostrar_opciones(self):
        self.tipo_ingreso = ""
        self.paginas.setCurrentIndex(0)

    def _volver(self):
        if self._directo:
            self.reject()
            return
        self._mostrar_opciones()

    def abrir_para_cliente(self, cliente, monto_sugerido=None):
        """Deja el Centro de Cobranzas parado en esa ficha."""
        self._directo = True
        self._set_modo("FIADO")
        ficha = dict(cliente) if hasattr(cliente, "keys") else {}
        self.panel_fiado.seleccionar_cliente_directo(ficha, monto_sugerido)

    def _set_modo(self, modo):
        self.tipo_ingreso = modo
        self.paginas.setCurrentIndex(1)
        self.lbl_err.setText("")

        if modo == "CAMBIO":
            self.stack.setCurrentIndex(0)
            self.panel_cambio.reset()
        elif modo == "FIADO":
            self.stack.setCurrentIndex(1)
            if hasattr(self.panel_fiado, 'mostrar'):
                self.panel_fiado.mostrar()
        elif modo == "OTROS":
            self.stack.setCurrentIndex(2)
            self.panel_otros.reset()

    def _on_abono_registrado(self, resultado):
        self.resultado = resultado
        self.monto_ingresado = getattr(resultado, 'monto', 0.0)
        self.cliente_id = getattr(resultado, 'cliente_id', None)
        self.cliente_nombre = getattr(resultado, 'nombre', '')
        self.motivo = f"Abono Fiado: {self.cliente_nombre}"
        self.accept()

    def _procesar(self):
        try:
            if self.tipo_ingreso == "CAMBIO":
                ok, err = self.panel_cambio.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_cambio.monto()
                self.motivo = "Ingreso de Cambio / Fondo Fijo"
            elif self.tipo_ingreso == "FIADO":
                # El ecosistema Fiado se maneja a si mismo ahora.
                # Si presionan el boton inferior Confirmar, lo derivamos al panel fiado.
                if hasattr(self.panel_fiado, 'procesar_enter'):
                    self.panel_fiado.procesar_enter()
                return
                self.paginas.setCurrentIndex(2)
                return
            elif self.tipo_ingreso == "OTROS":
                ok, err = self.panel_otros.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_otros.monto()
                self.motivo = self.panel_otros.descripcion()
            self.accept()
        except Exception:
            self.lbl_err.setText("⚠️ Error interno al procesar el ingreso")

    def _quien_pin(self):
        if self._directo:
            from src.config import config
            return (config.current_user or {}).get("username") or ""
        from src.cajero.cajero_activo import CajeroActivo
        return CajeroActivo.nombre

    def _f9(self):
        if self.paginas.currentIndex() != 2:
            return
        try:
            self.pagina_cobro.tecla(Qt.Key.Key_F9)
        except Exception:
            pass

    def keyPressEvent(self, event):
        if self.paginas.currentIndex() == 2:
            if event.key() == Qt.Key.Key_F9:
                return
            if event.key() == Qt.Key.Key_Escape:
                self.pagina_cobro.escape()
                return
            if self.pagina_cobro.tecla(event.key()):
                return
            return
        if self.paginas.currentIndex() == 0:
            if event.key() == Qt.Key.Key_Escape:
                self.reject()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key.Key_Escape:
            self._volver()
        elif event.key() == Qt.Key.Key_Left:
            if self.tipo_ingreso == "FIADO":
                self._set_modo("CAMBIO")
            elif self.tipo_ingreso == "OTROS":
                self._set_modo("FIADO")
        elif event.key() == Qt.Key.Key_Right:
            if self.tipo_ingreso == "CAMBIO":
                self._set_modo("FIADO")
            elif self.tipo_ingreso == "FIADO":
                self._set_modo("OTROS")
        else:
            super().keyPressEvent(event)
