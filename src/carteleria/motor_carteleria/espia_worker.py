from PyQt6.QtCore import QThread, pyqtSignal

class EspiaWorker(QThread):
    combo_triggered = pyqtSignal(str, float, float, float) # nombre, precio_original, precio_final, ahorro
    limpiar_solicitado = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, master_ip, path_local):
        super().__init__()
        self.master_ip = master_ip
        self.running = True

    def espia_log(self, msg):
        pass

    def run(self):
        import socket, json
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', 37021))
            sock.settimeout(2.0)
        except Exception as e:
            print(f"Error binding UDP port 37021: {e}")
            return
            
        while self.running:
            try:
                data_bytes, addr = sock.recvfrom(4096)
                
                data = json.loads(data_bytes.decode('utf-8'))
                
                # Filtrar por caja_id para soportar múltiples cajas en la misma red
                from src.config import config
                mi_caja_id = config.get("caja_id", 1)
                
                if data.get("type") == "COMBO_TRIGGERED":
                    # Si el paquete indica la caja, verificamos que sea para la nuestra
                    paquete_caja = data.get("caja_id")
                    if paquete_caja is not None and int(paquete_caja) != int(mi_caja_id):
                        continue # Pertenece a otra caja, ignoramos
                
                if data.get("limpiar"):
                    self.limpiar_solicitado.emit()
                elif data.get("type") == "COMBO_TRIGGERED":
                    combo = data.get("combo", "")
                    precio_original = float(data.get("precio_original", 0))
                    precio_final = float(data.get("precio_final", 0))
                    ahorro = float(data.get("ahorro", 0))
                    
                    self.combo_triggered.emit(combo, precio_original, precio_final, ahorro)
                elif data.get("type") == "PRECIOS_ACTUALIZADOS":
                    self.refresh_requested.emit()
            except socket.timeout:
                continue
            except Exception as e:
                continue
