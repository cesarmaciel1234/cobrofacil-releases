from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from src.admin.nexus_admin.vistas.nexus_main_view import NexusMainView
from src.admin.nexus_admin.logica.nexus_controller import NexusController

class NexusExtremeControl(QWidget):
    request_dashboard = pyqtSignal()
    request_z_close = pyqtSignal(float, int)

    def __init__(self, parent_main=None):
        super().__init__(parent_main)
        self.setObjectName("NexusExtremeControl")

        self.view = NexusMainView(self)
        self.controller = NexusController(self.view)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view)

    def hideEvent(self, event):
        if hasattr(self.controller, 't_matrix'): self.controller.t_matrix.stop()
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'spectrum') and hasattr(self.view.panel_izq.spectrum, 'timer'):
            self.view.panel_izq.spectrum.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        if hasattr(self.controller, 't_matrix'): self.controller.t_matrix.start(3000)
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'spectrum') and hasattr(self.view.panel_izq.spectrum, 'timer'):
            self.view.panel_izq.spectrum.timer.start(100)

        try:
            from datetime import datetime
            from src.base_de_datos.database import db_manager
            hoy = datetime.now().strftime("%Y-%m-%d")
            max_id = db_manager.execute_scalar("SELECT MAX(id) FROM ventas WHERE DATE(fecha) = ?", (hoy,))
            self.controller.last_sale_id = max_id if max_id is not None else 0
        except Exception as e:
            print(f"Error actualizando last_sale_id en showEvent: {e}")

        super().showEvent(event)
