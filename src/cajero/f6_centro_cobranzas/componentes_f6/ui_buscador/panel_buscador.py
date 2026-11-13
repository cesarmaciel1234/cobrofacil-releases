from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

class FilaSugerencia(QFrame):
    seleccionada = pyqtSignal(dict)

    def __init__(self, cliente, parent=None):
        super().__init__(parent)
        # Convert sqlite3.Row or similar to dict safely
        self.cliente = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
        self.setMinimumHeight(58)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            "QFrame { background: transparent; border-bottom: 1px solid #E2E8F0; border-radius: 0px; }"
            "QFrame:hover { background: #F1F5F9; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(2)
        
        nombre_str = str(self.cliente.get("nombre") or self.cliente.get("nombre_completo") or "")
        nombre = QLabel(nombre_str)
        nombre.setStyleSheet("color: #0F172A; font-size: 17px; font-weight: 800; background: transparent; border: none;")
        lay.addWidget(nombre)
        
        dni = str(self.cliente.get("dni") or "").strip()
        linea = QLabel(f"DNI: {dni}" if dni else "Sin DNI")
        linea.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        lay.addWidget(linea)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.seleccionada.emit(self.cliente)


class PanelBuscadorClientes(QWidget):
    texto_cambiado = pyqtSignal(str)
    cliente_elegido = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(10)

        # Encabezado
        self.lbl_subtitulo = QLabel("Cobranza de fiado y cuenta corriente. DNI o nombre.")
        self.lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("color: #64748B; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        lay.addWidget(self.lbl_subtitulo)

        # Contenedor de Búsqueda
        self.cont_busqueda = QFrame()
        self.cont_busqueda.setStyleSheet("background: transparent;")
        lay_busq = QVBoxLayout(self.cont_busqueda)
        lay_busq.setContentsMargins(0, 0, 0, 0)
        lay_busq.setSpacing(6)

        self.caja_busqueda = QLineEdit()
        self.caja_busqueda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja_busqueda.setFixedHeight(64)
        self.caja_busqueda.setPlaceholderText("Ej: Juan Perez o 34123456")
        self.caja_busqueda.setStyleSheet(
            "QLineEdit { background: #F8FAFC; color: #0F172A; border: 2.5px solid #CBD5E1; border-radius: 12px; padding: 6px 16px; font-size: 22px; font-weight: 800; }"
            "QLineEdit:focus { border: 2.5px solid #2563EB; background: #FFFFFF; }"
        )
        self.caja_busqueda.textChanged.connect(self.texto_cambiado.emit)
        self.caja_busqueda.returnPressed.connect(self.aceptar_actual)
        lay_busq.addWidget(self.caja_busqueda)
        
        self.lbl_sin_coincidencia = QLabel("No hay coincidencia con deuda o saldo a favor. F6 no crea clientes.")
        self.lbl_sin_coincidencia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_coincidencia.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 700; margin-top: 4px; background: transparent; border: none;")
        self.lbl_sin_coincidencia.hide()
        lay_busq.addWidget(self.lbl_sin_coincidencia)
        
        lay.addWidget(self.cont_busqueda)
        
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setMinimumHeight(40)
        self.lbl_error.setStyleSheet(
            "QLabel { background: #FEF2F2; color: #DC2626; border: 1.5px solid #F87171; border-radius: 8px; padding: 4px 12px; font-size: 14px; font-weight: 800; }"
        )
        self.lbl_error.hide()
        lay.addWidget(self.lbl_error)

        # Tarjeta informativa cuando no hay búsqueda activa (llena el espacio con guía útil)
        self.card_guia = QFrame()
        self.card_guia.setObjectName("CardGuiaF6")
        self.card_guia.setStyleSheet(
            "QFrame#CardGuiaF6 { background: #F8FAFC; border: 1.5px dashed #CBD5E1; border-radius: 14px; }"
        )
        lay_guia = QVBoxLayout(self.card_guia)
        lay_guia.setContentsMargins(22, 16, 22, 16)
        lay_guia.setSpacing(8)

        lbl_guia_tit = QLabel("💡 Búsqueda de cuentas y fiado")
        lbl_guia_tit.setStyleSheet("color: #1E3A8A; font-size: 14px; font-weight: 800; border: none; background: transparent;")
        lbl_guia_desc1 = QLabel("• Escribí al menos 3 caracteres del nombre, alias o DNI para buscar.")
        lbl_guia_desc1.setStyleSheet("color: #475569; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        lbl_guia_desc2 = QLabel("• Flechas ↑ ↓ para navegar entre resultados y Enter para abrir la ficha.")
        lbl_guia_desc2.setStyleSheet("color: #475569; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        lbl_guia_desc3 = QLabel("• En pantalla táctil podés tocar directamente la fila del cliente.")
        lbl_guia_desc3.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 600; border: none; background: transparent;")

        lay_guia.addWidget(lbl_guia_tit)
        lay_guia.addWidget(lbl_guia_desc1)
        lay_guia.addWidget(lbl_guia_desc2)
        lay_guia.addWidget(lbl_guia_desc3)
        lay.addWidget(self.card_guia)

        # Contenedor de Sugerencias
        self.lista_sugerencias = QFrame()
        self.lista_sugerencias.setObjectName("ListaSugerencias")
        self.lista_sugerencias.setStyleSheet(
            "QFrame#ListaSugerencias { background: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 12px; }"
        )
        
        self.lay_lista = QVBoxLayout(self.lista_sugerencias)
        self.lay_lista.setContentsMargins(0, 4, 0, 4)
        self.lay_lista.setSpacing(0)
        self.lista_sugerencias.hide()
        lay.addWidget(self.lista_sugerencias)

        lay.addStretch(1)

    def mostrar_sugerencias(self, clientes):
        while self.lay_lista.count():
            item = self.lay_lista.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._clientes_actuales = clientes[:5]
        self._indice_seleccionado = -1
        
        if not self._clientes_actuales:
            self.lista_sugerencias.hide()
            if self.caja_busqueda.text().strip():
                self.card_guia.hide()
                self.lbl_sin_coincidencia.show()
            else:
                self.lbl_sin_coincidencia.hide()
                self.card_guia.show()
            return
            
        self.lbl_sin_coincidencia.hide()
        self.card_guia.hide()
            
        for c in self._clientes_actuales:
            fila = FilaSugerencia(c)
            fila.seleccionada.connect(self.cliente_elegido.emit)
            self.lay_lista.addWidget(fila)
            
        self.lista_sugerencias.show()

    def limpiar(self):
        self.caja_busqueda.clear()
        self.mostrar_sugerencias([])
        self.card_guia.show()

    def focus_caja(self):
        self.caja_busqueda.setFocus()
        
    def navegar(self, direccion):
        if not hasattr(self, '_clientes_actuales') or not self._clientes_actuales:
            return
        if direccion == "arriba":
            self._indice_seleccionado -= 1
            if self._indice_seleccionado < 0:
                self._indice_seleccionado = len(self._clientes_actuales) - 1
        else:
            self._indice_seleccionado += 1
            if self._indice_seleccionado >= len(self._clientes_actuales):
                self._indice_seleccionado = 0
                
        for i in range(self.lay_lista.count()):
            item = self.lay_lista.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if i == self._indice_seleccionado:
                    w.setStyleSheet(
                        "QFrame { background: #E2E8F0; border-bottom: 2px solid #CBD5E1; border-radius: 0px; }"
                    )
                else:
                    w.setStyleSheet(
                        "QFrame { background: transparent; border-bottom: 2px solid #F1F5F9; border-radius: 0px; }"
                        "QFrame:hover { background: #E2E8F0; }"
                    )
                    
    def aceptar_actual(self):
        if not hasattr(self, '_clientes_actuales') or not self._clientes_actuales:
            return False
        if self._indice_seleccionado >= 0 and self._indice_seleccionado < len(self._clientes_actuales):
            c = self._clientes_actuales[self._indice_seleccionado]
        elif len(self._clientes_actuales) == 1:
            c = self._clientes_actuales[0]
        else:
            return False
        c_dict = dict(c) if hasattr(c, "keys") else (c if isinstance(c, dict) else {})
        self.cliente_elegido.emit(c_dict)
        return True
