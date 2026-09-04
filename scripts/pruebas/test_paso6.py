import sys
from PyQt6.QtWidgets import QApplication
from src.cajero.paso6_cobro.paso6_cobro import Paso6Cobro

if __name__ == "__main__":
    app = QApplication(sys.argv)
    total_simulado = 2500.00
    items_simulados = [{"nombre": "Asado", "cantidad": 1, "precio": 1500.00, "total": 1500.00}]
    ventana = Paso6Cobro(total_simulado, items_simulados)
    ventana.show()
    sys.exit(app.exec())
