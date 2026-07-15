from src.ui_global.cierre_diario_ui.cierre_main_ui import CierreGlobalUI

class Admin7Cierre(CierreGlobalUI):
    """
    Wrapper para mantener compatibilidad con el enrutador actual del Admin.
    Toda la lógica visual y de base de datos ahora vive en CierreGlobalUI y MotorCierre.
    """
    def __init__(self, parent_main=None):
        super().__init__(parent_main=parent_main)
