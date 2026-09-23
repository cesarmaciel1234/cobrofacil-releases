import sys
from PyQt6.QtWidgets import QApplication
from src.admin.nexus_admin.vistas.componentes.panel_central.nexus_panel_cen import NexusPanelCen

app = QApplication(sys.argv)
panel = NexusPanelCen()
panel.registrar_nodo_dinamico('cesar|cajero|caja1')
panel.registrar_nodo_dinamico('cesar|admin|caja1')
panel.show()
sys.exit(app.exec())
