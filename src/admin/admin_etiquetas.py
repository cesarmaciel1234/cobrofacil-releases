# ==============================================================================
# CajaFacil Pro - REDIRECCIONAMIENTO DE SEGURIDAD
# ==============================================================================
# Este archivo legacy ha sido unificado y modularizado para evitar duplicidad.
# Todo el código de producción y lógica de impresión reside en:
# src/admin/etiquetas/admin_etiquetas.py
# ==============================================================================

from src.admin.etiquetas.admin_etiquetas import AdminEtiquetas

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AdminEtiquetas()
    window.show()
    sys.exit(app.exec_())