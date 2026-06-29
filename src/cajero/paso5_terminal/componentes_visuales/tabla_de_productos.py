from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTableWidget, QHeaderView, QAbstractItemView

class TablaDeProductos(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalTablaContainer")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        
        # --- TABLA CENTRAL ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "DESCRIPCION PRODUCTO", "PRECIO", "CANT", "DES. TOTAL", "TOTAL"])
        self.tabla.setObjectName("TerminalTabla")
        self.tabla.setAlternatingRowColors(True)
        # Bloquear columnas numéricas para evitar que Qt las exprima
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed) 
        # Solo la descripción se estira dinámicamente
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        
        # Anchos iniciales (referencia 1920×1080)
        self.tabla.setColumnWidth(0, 110)  # ID / Barcode
        self.tabla.setColumnWidth(2, 160)  # PRECIO
        self.tabla.setColumnWidth(3, 85)   # CANT
        self.tabla.setColumnWidth(4, 150)  # DES. TOTAL
        self.tabla.setColumnWidth(5, 170)  # TOTAL
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout_principal.addWidget(self.tabla)
        
    def get_tabla(self):
        """Devuelve el widget de tabla para poder conectarle eventos o el NavRowBorderOverlay desde afuera."""
        return self.tabla
