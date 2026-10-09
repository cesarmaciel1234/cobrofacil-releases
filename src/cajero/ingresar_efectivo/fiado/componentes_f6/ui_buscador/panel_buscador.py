from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

class FilaSugerencia(QFrame):
    seleccionada = pyqtSignal(dict)

    def __init__(self, cliente, parent=None):
        super().__init__(parent)
        # Convert sqlite3.Row or similar to dict safely
        self.cliente = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
        self.setMinimumHeight(80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(
            "QFrame { background: transparent; border-bottom: 2px solid #F1F5F9; border-radius: 0px; }"
            "QFrame:hover { background: #E2E8F0; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(2)
        
        nombre_str = str(self.cliente.get("nombre") or self.cliente.get("nombre_completo") or "")
        nombre = QLabel(nombre_str)
        nombre.setStyleSheet("color: #0F172A; font-size: 22px; font-weight: 900; background: transparent; border: none;")
        lay.addWidget(nombre)
        
        dni = str(self.cliente.get("dni") or "").strip()
        linea = QLabel(f"DNI: {dni}" if dni else "Sin DNI")
        linea.setStyleSheet("color: #475569; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        lay.addWidget(linea)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.seleccionada.emit(self.cliente)


class PanelBuscadorClientes(QWidget):
    texto_cambiado = pyqtSignal(str)
    cliente_elegido = pyqtSignal(dict)
    creacion_solicitada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(15)

        # Encabezado Flat Premium
        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #0F172A; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel("Pida el DNI o el nombre del cliente.")
        self.lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("color: #64748B; font-size: 18px; font-weight: 700; margin-bottom: 10px;")
        lay.addWidget(self.lbl_subtitulo)

        # Contenedor de Búsqueda Flat
        self.cont_busqueda = QFrame()
        self.cont_busqueda.setStyleSheet("background: transparent;")
        lay_busq = QVBoxLayout(self.cont_busqueda)
        lay_busq.setContentsMargins(0,0,0,0)

        self.caja_busqueda = QLineEdit()
        self.caja_busqueda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja_busqueda.setMinimumHeight(76)
        self.caja_busqueda.setPlaceholderText("Ej: Juan Perez o 34123456")
        self.caja_busqueda.setStyleSheet(
            "QLineEdit { background: #F8FAFC; color: #0F172A; border: 3px solid #CBD5E1; border-radius: 12px; padding: 10px 20px; font-size: 28px; font-weight: 900; }"
            "QLineEdit:focus { border: 3px solid #2563EB; background: #FFFFFF; }"
        )
        self.caja_busqueda.textChanged.connect(self.texto_cambiado.emit)
        lay_busq.addWidget(self.caja_busqueda)
        lay.addWidget(self.cont_busqueda)

        # Contenedor de Sugerencias Flat
        self.lista_sugerencias = QFrame()
        self.lista_sugerencias.setObjectName("ListaSugerencias")
        self.lista_sugerencias.setStyleSheet(
            "QFrame#ListaSugerencias { background: #FFFFFF; border: 3px solid #E2E8F0; border-radius: 12px; }"
        )
        
        self.lay_lista = QVBoxLayout(self.lista_sugerencias)
        self.lay_lista.setContentsMargins(0, 5, 0, 5)
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
            return
            
        for c in self._clientes_actuales:
            fila = FilaSugerencia(c)
            fila.seleccionada.connect(self.cliente_elegido.emit)
            self.lay_lista.addWidget(fila)
            
        self.lista_sugerencias.show()

    def limpiar(self):
        self.caja_busqueda.clear()
        self.mostrar_sugerencias([])

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
        texto = self.caja_busqueda.text().strip()
        if not hasattr(self, '_clientes_actuales') or not self._clientes_actuales:
            if texto:
                self.creacion_solicitada.emit(texto)
                return True
            return False
        
        indice = 0 if self._indice_seleccionado < 0 else self._indice_seleccionado
        if indice < len(self._clientes_actuales):
            self.cliente_elegido.emit(self._clientes_actuales[indice])
            return True
            
        return False
