import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Evitar que QTimer o la UI colapse sin app
app = QApplication(sys.argv)

from src.network.network_engine import init_network_engine

print(">>> Iniciando Test de NetworkEngine (Modo: admin)")
try:
    engine = init_network_engine("admin")
    print("[OK] NetworkEngine instanciado.")
    
    def on_heartbeat(origen):
        print(f"[EVENTO] Heartbeat recibido de: {origen}")
        
    engine.heartbeat_received.connect(on_heartbeat)
    print("[OK] Señales conectadas.")
    
    print(">>> Esperando 4 segundos para escuchar la red (y enviando nuestro propio heartbeat)...")
    QTimer.singleShot(4000, app.quit)
    app.exec_()
    print(">>> Test finalizado correctamente sin crasheos.")
except Exception as e:
    import traceback
    print(f"[ERROR FATAL] {e}")
    traceback.print_exc()
