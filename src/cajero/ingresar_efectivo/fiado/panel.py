"""Fiado: busca al cliente y toma el abono."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QAbstractItemView, QFrame, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

from src.cajero.ingresar_efectivo.fiado.paleta import PALETA
from src.cajero.ingresar_efectivo.fiado.consulta import parse_consulta_cobranza, buscar_deudores

_EXEC = PALETA


class CentroCobranzasPanel(QWidget):
    """Panel F6 → FIADO: buscador centrado, foco siempre en cliente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cliente: dict | None = None
        self._deuda_actual = 0.0
        self.setStyleSheet("background: transparent; border: none;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row_center = QHBoxLayout()
        row_center.addStretch(1)
        self.card = QFrame()
        self.card.setObjectName("CobranzaCard")
        self.card.setStyleSheet(
            "QFrame#CobranzaCard { background: transparent; border: none; border-radius: 0px; }"
        )

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(22, 18, 22, 12)
        lay.setSpacing(8)

        tit = QLabel("CENTRO DE COBRANZAS")
        tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tit.setStyleSheet(
            f"color: {_EXEC['navy']}; font-size: 14px; font-weight: 900; "
            "letter-spacing: 2px; border: none; background: transparent;"
        )
        sub = QLabel("Busque por DNI · nombre · dirección · teléfono")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet(
            f"color: {_EXEC['text_soft']}; font-size: 11px; font-weight: 500; "
            "border: none; background: transparent;"
        )
        lay.addWidget(tit)
        lay.addWidget(sub)

        self.lbl_modo = QLabel("Mostrando: todos los deudores")
        self.lbl_modo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_modo.setStyleSheet(
            "font-size: 11px; color: #3B82F6; font-weight: 700; "
            "border: none; background: transparent; padding-top: 2px;"
        )
        lay.addWidget(self.lbl_modo)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("DNI, nombre, dirección o teléfono…")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                font-size: 16px; font-weight: 700; color: {_EXEC['text']};
                padding: 14px 16px;
                border: 2px solid {_EXEC['border']};
                border-radius: 10px;
                background: {_EXEC['bg']};
            }}
            QLineEdit:focus {{
                border: 2px solid #3B82F6;
                background: white;
            }}
        """)
        self.txt_buscar.textChanged.connect(self._on_buscar_cambio)
        self.txt_buscar.returnPressed.connect(self._on_enter_buscar)
        lay.addWidget(self.txt_buscar)

        self.zona_lista = QFrame()
        self.zona_lista.setObjectName("ZonaListaCobranza")
        self.zona_lista.setStyleSheet(
            f"QFrame#ZonaListaCobranza {{ background: {_EXEC['bg']}; border: 1px solid {_EXEC['border']};"
            " border-radius: 10px; }}"
        )
        zona_lay = QVBoxLayout(self.zona_lista)
        zona_lay.setContentsMargins(6, 6, 6, 6)
        zona_lay.setSpacing(4)
        self.lbl_lista = QLabel("")
        self.lbl_lista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_lista.setStyleSheet(
            f"font-size: 12px; color: {_EXEC['text_muted']}; font-weight: 700; "
            "border: none; background: transparent; padding: 2px;"
        )
        zona_lay.addWidget(self.lbl_lista)
        self.lista = QListWidget()
        self.lista.setMinimumHeight(120)
        self.lista.setMaximumHeight(160)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lista.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lista.setUniformItemSizes(False)
        self.lista.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background: transparent;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 8px;
                color: {_EXEC['text']};
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background: {_EXEC['row_sel']};
                color: {_EXEC['navy']};
                font-weight: 700;
            }}
            QListWidget::item:hover {{
                background: #F1F5F9;
            }}
        """)
        self.lista.itemClicked.connect(self._on_item_seleccionado)
        self.lista.itemDoubleClicked.connect(lambda _: self.focus_monto())
        zona_lay.addWidget(self.lista)
        lay.addWidget(self.zona_lista)

        self.ficha = QFrame()
        self.ficha.setObjectName("FichaClienteCobranza")
        self.ficha.setStyleSheet(
            "QFrame#FichaClienteCobranza { background: #EFF6FF; border: 1px solid #BFDBFE;"
            " border-radius: 12px; }"
            "QLabel { background: transparent; border: none; }"
        )
        ficha_lay = QVBoxLayout(self.ficha)
        ficha_lay.setContentsMargins(14, 12, 14, 12)
        ficha_lay.setSpacing(4)
        self.lbl_cliente = QLabel("Seleccione un cliente")
        self.lbl_cliente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cliente.setWordWrap(True)
        self.lbl_cliente.setStyleSheet(
            f"font-size: 16px; color: {_EXEC['navy']}; font-weight: 800;"
        )
        ficha_lay.addWidget(self.lbl_cliente)
        self.lbl_info = QLabel("")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet(
            f"font-size: 12px; color: {_EXEC['text_soft']}; font-weight: 600;"
        )
        ficha_lay.addWidget(self.lbl_info)
        self.lbl_deuda = QLabel("")
        self.lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda.setStyleSheet(
            f"font-size: 18px; color: {_EXEC['deuda']}; font-weight: 900;"
        )
        ficha_lay.addWidget(self.lbl_deuda)
        self.ficha.hide()
        lay.addWidget(self.ficha)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {_EXEC['border']}; border: none;")
        lay.addWidget(sep)

        lbl_m = QLabel("MONTO A ABONAR")
        lbl_m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_m.setStyleSheet(
            f"font-size: 10px; color: {_EXEC['text_muted']}; font-weight: 800; "
            "letter-spacing: 1.5px; border: none; background: transparent;"
        )
        lay.addWidget(lbl_m)

        self.txt_monto = QLineEdit()
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setMinimumHeight(64)
        self.txt_monto.setStyleSheet(f"""
            QLineEdit {{
                font-size: 34px; font-weight: 900; color: {_EXEC['navy']};
                border: 2px solid {_EXEC['border']};
                border-radius: 12px;
                padding: 10px;
                background: white;
            }}
            QLineEdit:focus {{
                border: 2px solid #3B82F6;
            }}
        """)
        lay.addWidget(self.txt_monto)

        row_center.addWidget(self.card, stretch=0)
        row_center.addStretch(1)
        outer.addLayout(row_center)

        btn_lay = QHBoxLayout()
        btn_lay.addStretch(1)
        self.btn_imprimir = QPushButton("🖨 IMPRIMIR SALDO")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.setStyleSheet(f"""
            QPushButton {{
                background: {_EXEC['navy']}; color: white; font-weight: 800; font-size: 11px;
                border-radius: 8px; padding: 10px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {_EXEC['accent']}; color: {_EXEC['navy']}; }}
        """)
        self.btn_imprimir.setVisible(False)
        self.btn_imprimir.clicked.connect(self._imprimir_estado_deuda)
        btn_lay.addWidget(self.btn_imprimir)
        btn_lay.addStretch(1)
        outer.addLayout(btn_lay)

        self._timer_buscar = QTimer(self)
        self._timer_buscar.setSingleShot(True)
        self._timer_buscar.setInterval(280)
        self._timer_buscar.timeout.connect(self._ejecutar_busqueda)

    def cargar_clientes_abono(self):
        self.reset()

    def reset(self):
        self._limpiar_seleccion()
        self.txt_buscar.clear()
        self.lista.clear()
        self.zona_lista.show()
        self.lbl_lista.setText("")
        self.lbl_modo.setText("Escriba para buscar un cliente...")
        self._ejecutar_busqueda()
        QTimer.singleShot(120, self.focus_busqueda)

    def focus_busqueda(self):
        self.txt_buscar.setFocus()
        self.txt_buscar.selectAll()

    def focus_monto(self):
        if self.txt_monto is not None:
            self.txt_monto.setFocus()
            self.txt_monto.selectAll()

    def _limpiar_seleccion(self):
        self._cliente = None
        self._deuda_actual = 0.0
        self.lbl_cliente.setText("Seleccione un cliente")
        self.lbl_info.clear()
        self.lbl_deuda.clear()
        self.txt_monto.clear()
        self.ficha.hide()
        self.btn_imprimir.setVisible(False)

    def _on_enter_buscar(self):
        if self.lista.count() == 1 and not self._cliente:
            self.lista.setCurrentRow(0)
            self._on_item_seleccionado(self.lista.item(0))
            self.focus_monto()
        else:
            self._ejecutar_busqueda()

    def _on_buscar_cambio(self, _text: str):
        self._timer_buscar.start()

    def _ejecutar_busqueda(self):
        consulta = self.txt_buscar.text().strip()
        self.lista.clear()
        self._limpiar_seleccion()
        self.zona_lista.show()

        if not consulta:
            self.lbl_modo.setText("Escriba para buscar un cliente...")
            self.lbl_lista.setText("")
            return

        p = parse_consulta_cobranza(consulta)
        self.lbl_modo.setText(f"Mostrando: {p['etiqueta']}")
        resultados = buscar_deudores(consulta)
        if not resultados:
            self.lbl_lista.setText("Sin resultados — pruebe otro criterio")
            return

        for r in resultados:
            dni = (r.get("dni") or "").strip()
            tel = (r.get("telefono") or "").strip()
            deuda = float(r.get("deuda_actual") or 0)
            ult = r.get("ultimo_cargo")
            ult_txt = f" · {str(ult).split('.')[0][:10]}" if ult else ""
            extra = " · ".join(p for p in (f"DNI {dni}" if dni else "", f"Tel {tel}" if tel else "") if p)
            if extra:
                texto = f"{r['nombre']}\n{extra} · Deuda ${deuda:,.2f}{ult_txt}"
            else:
                texto = f"{r['nombre']}\nDeuda ${deuda:,.2f}{ult_txt}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            if (r.get("tipo_cliente") or "") == "express":
                item.setForeground(QColor(_EXEC["accent"]))
                f = item.font()
                f.setWeight(QFont.Weight.Bold)
                item.setFont(f)
            self.lista.addItem(item)

        self.lbl_lista.setText(f"{len(resultados)} deudor(es) — seleccione uno")
        if len(resultados) == 1:
            self.lista.setCurrentRow(0)
            self._on_item_seleccionado(self.lista.item(0))

    def _on_item_seleccionado(self, item: QListWidgetItem | None):
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        self._cliente = data
        self._deuda_actual = float(data.get("deuda_actual") or 0)
        dni = (data.get("dni") or "").strip()
        tel = (data.get("telefono") or "").strip()
        direc = (data.get("direccion") or "").strip()
        nombre = data.get("nombre", "")
        info_parts = []
        if dni:
            info_parts.append(f"DNI {dni}")
        if tel:
            info_parts.append(f"Tel {tel}")
        if direc:
            info_parts.append(direc)
        self.lbl_cliente.setText(nombre)
        self.lbl_info.setText(" · ".join(info_parts))
        self.lbl_deuda.setText(f"Deuda: ${self._deuda_actual:,.2f}")
        self.txt_monto.setText(f"{self._deuda_actual:.2f}")
        self.zona_lista.hide()
        self.ficha.show()
        self.btn_imprimir.setVisible(True)

    def _imprimir_estado_deuda(self):
        if not self._cliente:
            return
        from src.hardware.printer import printer_manager
        anterior = float(self._deuda_actual or 0)
        credito = min(self.monto(), anterior)
        if credito < 0:
            credito = 0.0
        printer_manager.imprimir_saldo_fiado(
            self._cliente.get("nombre", ""),
            anterior,
            credito,
            anterior - credito,
        )
        self.txt_buscar.setFocus()

    def cliente_actual(self):
        return self._cliente

    def deuda_actual(self) -> float:
        return self._deuda_actual

    def monto(self) -> float:
        if self.txt_monto is None:
            return 0.0
        return float(self.txt_monto.text().strip() or 0)

    def validar(self) -> tuple[bool, str]:
        if not self._cliente:
            return False, "⚠️ Seleccione un cliente de la lista"
        monto = self.monto()
        if monto <= 0:
            return False, "⚠️ Ingresa un abono mayor a 0"
        if monto > self._deuda_actual + 0.01:
            return False, "⚠️ El abono no puede superar la deuda"
        return True, ""
