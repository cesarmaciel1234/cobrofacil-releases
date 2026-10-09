from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QSizePolicy, QStackedWidget
from PyQt6.QtCore import Qt

class PanelBotonesAccion(QWidget):
    """
    Panel derecho con las acciones de cobro (F1, F2, F3, F4, F5, F11, F12).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        fila_acciones = QHBoxLayout(self)
        fila_acciones.setSpacing(5)
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        
        def columna_fija():
            caja = QFrame()
            caja.setObjectName("ColumnaAccion")
            caja.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            lay = QVBoxLayout(caja)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(5)
            return caja, lay

        self.col_imprime, lay_imprime = columna_fija()
        self.col_registra, lay_registra = columna_fija()
        self.col_ajuste, lay_ajuste = columna_fija()
        
        for col in (self.col_imprime, self.col_registra, self.col_ajuste):
            fila_acciones.addWidget(col, 1)

        def create_action_btn(fn_key, subtitle, style="default"):
            btn = QPushButton(f"{fn_key}\n{subtitle}")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setProperty("action_type", style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn
            
        self.btn_f1 = create_action_btn("F1", "imprime", style="primary")
        lay_imprime.addWidget(self.btn_f1, 1)
        
        self.btn_f2 = create_action_btn("F2", "sin ticket", style="default")
        self.pila_f2 = QStackedWidget()
        self.pila_f2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_f2.setMinimumHeight(78)
        self.btn_ultimo_mixto = create_action_btn("F12", "último monto", style="default")
        self.pila_f2.addWidget(self.btn_f2)
        self.pila_f2.addWidget(self.btn_ultimo_mixto)
        lay_registra.addWidget(self.pila_f2, 1)
        
        self.btn_descuento = create_action_btn("F3", "redondeo", style="default")
        lay_ajuste.addWidget(self.btn_descuento, 1)

        self.btn_recargo = create_action_btn("F4", "recargo", style="default")
        lay_imprime.addWidget(self.btn_recargo, 1)
        
        self.pila_point = QStackedWidget()
        self.pila_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_point.setMinimumHeight(78)
        self.btn_f11 = create_action_btn("F11", "Point MP", style="default")
        self.pila_point.addWidget(self.btn_f11)
        self.pila_point.addWidget(QWidget())
        lay_registra.addWidget(self.pila_point, 1)
        
        self.btn_f5 = create_action_btn("F5", "pagar cuenta", style="default")
        self.pila_extra = QStackedWidget()
        self.pila_extra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_extra.setMinimumHeight(78)
        self.btn_f12 = create_action_btn("F12", "Verif QR", style="default")
        self.btn_ultimo = create_action_btn("F12", "último monto", style="default")
        self.pila_extra.addWidget(self.btn_f12)
        self.pila_extra.addWidget(self.btn_ultimo)
        self.pila_extra.addWidget(QWidget())
        self.pila_extra.addWidget(self.btn_f5)
        lay_ajuste.addWidget(self.pila_extra, 1)
