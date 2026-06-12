import sys
import os

# Asegurar que la raíz del proyecto esté en el path para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from PyQt5.QtWidgets import QApplication
from src.vistas.carteleria_app.main_board import CarteleriaMain

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarteleriaMain()
    window.setWindowTitle("Cartelería Autónoma - Apple Style Modular")
    window.showMaximized()
    sys.exit(app.exec_())
