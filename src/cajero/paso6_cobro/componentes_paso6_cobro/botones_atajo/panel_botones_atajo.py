from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

class PanelBotonesAtajo(QWidget):
    """
    Panel invisible que agrupa los atajos de teclado adicionales del cobro (ej. F9, F10).
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.hide() # No tiene UI visible
        
        self.atajo_f9 = QShortcut(QKeySequence(Qt.Key.Key_F9), main_window)
        self.atajo_f9.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
