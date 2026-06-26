from src.utils.qt_compat import qt_exec
import sys
import os
import random
from datetime import datetime

# Asegurar que el directorio raíz esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from src.admin.admin7_nexus import NexusExtremeControl
from src.base_de_datos.database import db_manager

def simulate_activity():
    try:
        for _ in range(3): # Generar 3 eventos por ciclo para hiper-actividad
            caja_id = random.randint(1, 17) # Hasta la caja 17
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 80% probabilidad de Venta, 20% probabilidad de problema (Cancelación o Intervención)
            if random.random() < 0.8:
                metodos = ["Efectivo", "Efectivo", "Efectivo", "Tarjeta", "Transferencia"]
                metodo = random.choice(metodos)
                total = round(random.uniform(500.0, 15000.0), 2)
                
                # Insertar VENTA real
                query = "INSERT INTO ventas (caja_id, total, metodo_pago, usuario, estado, fecha) VALUES (?, ?, ?, ?, ?, ?)"
                db_manager.execute_non_query(query, (caja_id, total, metodo, "SYS.SIM", "completada", ahora))
            else:
                # Insertar EVENTO de seguridad
                eventos = [
                    ("CANCELACION", "Cancelación de Ticket #SIM", "SYS.SIM"),
                    ("INTERVENCION", "Intervención de Supervisor", "SYS.ADMIN"),
                    ("ALERTA_SEGURIDAD", "Cajón de dinero abierto sin venta", "SYS.SIM")
                ]
                tipo, obs, usr = random.choice(eventos)
                query = "INSERT INTO movimientos_caja (caja_id, tipo, monto, observaciones, usuario, fecha) VALUES (?, ?, ?, ?, ?, ?)"
                db_manager.execute_non_query(query, (caja_id, tipo, 0.0, obs, usr, ahora))
    except Exception as e:
        import traceback
        with open("error_sim.log", "w") as f:
            f.write(traceback.format_exc())
        print(f"Error en simulate_activity: {e}")

def main():
    import os
    os.environ["QT_ACCESSIBILITY"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    
    app = QApplication(sys.argv)
    
    # Crear y mostrar solo el widget de Nexus
    window = NexusExtremeControl()
    window.setWindowTitle("TEST: Nexus Center Standalone - SIMULANDO 5 CAJAS A FULL")
    window.resize(1000, 700)
    window.show()
    
    # Iniciar Simulador a TODA MÁQUINA (Hiper velocidad)
    global timer_sim
    timer_sim = QTimer()
    timer_sim.timeout.connect(simulate_activity)
    timer_sim.start(50) # Un ciclo de 3 eventos cada 50 ms (60 eventos por segundo!)
    
sys.exit(qt_exec(app))

if __name__ == '__main__':
    main()