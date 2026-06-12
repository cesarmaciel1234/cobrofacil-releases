import sys
import time
from PyQt5.QtWidgets import QApplication

def test_jefe_reportes():
    print("Iniciando prueba de rendimiento de JefeReportes...")
    app = QApplication(sys.argv)
    
    # Measure import time
    t0 = time.time()
    from src.jefe.jefe_reportes import JefeReportes
    t1 = time.time()
    print(f"Tiempo de importación: {(t1 - t0)*1000:.2f} ms")
    
    # Measure instantiation time
    t2 = time.time()
    modulo = JefeReportes()
    t3 = time.time()
    print(f"Tiempo de instanciación (setup_ui): {(t3 - t2)*1000:.2f} ms")
    
    # Let data loader thread run for a bit
    print("Esperando 2 segundos para que el hilo cargue datos...")
    start_wait = time.time()
    while time.time() - start_wait < 2.0:
        app.processEvents()
        
    print("Carga finalizada sin crashear.")

if __name__ == '__main__':
    test_jefe_reportes()
