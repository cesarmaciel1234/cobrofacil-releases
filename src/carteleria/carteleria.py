from src.utils.qt_compat import qt_exec
import sys
import os

# Asegurar que la raíz del proyecto esté en el path para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from PyQt6.QtWidgets import QApplication
from src.carteleria.main_board import CarteleriaMain

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarteleriaMain()
    window.setWindowTitle("Cartelería Autónoma - Apple Style Modular")
    window.showFullScreen()
    sys.exit(qt_exec(app))