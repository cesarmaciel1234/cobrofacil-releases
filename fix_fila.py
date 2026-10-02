import re
file_path = 'src/clientes_fiado/interfaz/cobro/hoja.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_fila = '''class _FilaNombre(QFrame):
    """Una fila del listado: el nombre arriba y el DNI abajo."""

    def __init__(self, hoja, indice, ficha):
        super().__init__()
        self._hoja = hoja
        self._indice = indice
        self.setMinimumHeight(62)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(14, 8, 14, 8)
        caja.setSpacing(0)
        nombre = QLabel(str(ficha.get("nombre") or ""))
        nombre.setStyleSheet(
            "color: #0F172A; font-size: 18px; font-weight: 800; background: transparent; border: none;"
        )
        caja.addWidget(nombre)
        dni = str(ficha.get("dni") or "").strip()
        linea = QLabel(f"DNI {dni}" if dni else "Sin DNI")
        linea.setStyleSheet(
            "color: #1E293B; font-size: 14px; font-weight: 700; background: transparent; border: none;"
        )
        caja.addWidget(linea)'''

new_fila = '''class _FilaNombre(QFrame):
    """Una fila del listado: el nombre arriba y el DNI abajo."""

    def __init__(self, hoja, indice, ficha):
        super().__init__()
        self._hoja = hoja
        self._indice = indice
        self.setMinimumHeight(76)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(16, 14, 16, 14)
        caja.setSpacing(4)
        nombre = QLabel(str(ficha.get("nombre") or ""))
        nombre.setStyleSheet(
            "color: #0F172A; font-size: 20px; font-weight: 900; background: transparent; border: none;"
        )
        caja.addWidget(nombre)
        dni = str(ficha.get("dni") or "").strip()
        linea = QLabel(f"DNI {dni}" if dni else "Sin DNI")
        linea.setStyleSheet(
            "color: #334155; font-size: 15px; font-weight: 700; background: transparent; border: none;"
        )
        caja.addWidget(linea)'''

if old_fila in text:
    text = text.replace(old_fila, new_fila)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Fixed _FilaNombre.')
else:
    print('old_fila not found.')
