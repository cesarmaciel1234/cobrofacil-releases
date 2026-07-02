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
        header = self.tabla.horizontalHeader()
        
        # 1. Definir un tamaño mínimo global para que las celdas nunca se aplasten
        header.setMinimumSectionSize(100)
        
        # 2. Las columnas numéricas se ajustan a su contenido para nunca mostrar '...'
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # PRECIO
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # CANT
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # DES. TOTAL
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # TOTAL
        
        # 3. La descripción estira para ocupar todo el espacio sobrante en pantallas 14" a 24"
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout_principal.addWidget(self.tabla)
        
    def get_tabla(self):
        """Devuelve el widget de tabla para poder conectarle eventos o el NavRowBorderOverlay desde afuera."""
        return self.tabla
