from src.utils.qt_compat import qt_exec
import sys
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt6.QtNetwork import QUdpSocket, QHostAddress

class HiloEscuchaDiagnostico(QThread):
    # Señal que envía el texto recibido y la IP de origen a la UI
    paquete_recibido = pyqtSignal(str, str)
    error_conexion = pyqtSignal(str)
    
    def run(self):
        self.socket = QUdpSocket()
        # Intentamos bindear con reutilización de puerto para evitar bloqueos locales
        exito = self.socket.bind(QHostAddress.AnyIPv4, 38000, QUdpSocket.ShareAddress | QUdpSocket.ReuseAddressHint)
        if not exito:
            self.error_conexion.emit("ERROR: No se pudo bindear el puerto 38000. ¿Ya está en uso por el Nexus?")
            return
            
        self.paquete_recibido.emit("SISTEMA", "Escuchando en puerto 38000 UDP de forma sólida...")
        
        while not self.isInterruptionRequested():
            if self.socket.hasPendingDatagrams():
                try:
                    datagrama, host, puerto = self.socket.readDatagram(self.socket.pendingDatagramSize())
                    texto = datagrama.decode('utf-8')
                    self.paquete_recibido.emit(host.toString(), texto)
                except Exception as e:
                    self.paquete_recibido.emit(host.toString(), f"Error decodificando bytes: {str(e)}")
            self.msleep(10) # Evita consumo excesivo de CPU (10ms es más responsivo que 100ms)

class VentanaDiagnosticoNexus(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.iniciar_hilo()
        
    def init_ui(self):
        self.setWindowTitle("Nexus Central - Consola de Diagnóstico de Red")
        self.resize(700, 500)
        self.setStyleSheet("background-color: #121212; color: #FFFFFF; font-family: 'Consolas', monospace;")
        
        layout = QVBoxLayout(self)
        
        # Indicadores de Estado de Hardware/Software
        self.lbl_estado_hilo = QLabel("ESTADO DEL HILO: INICIANDO...")
        self.lbl_estado_hilo.setStyleSheet("color: #FFB86C; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_estado_hilo)
        
        layout.addWidget(QLabel("Tráfico de Red Entrante (Puerto 38000):"))
        
        # Consola de datos crudos
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #1E1E1E; border: 1px solid #333; color: #50FA7B; font-size: 12px;")
        layout.addWidget(self.consola)
        
        # Botones
        btn_limpiar = QPushButton("Limpiar Consola")
        btn_limpiar.setStyleSheet("background-color: #44475A; padding: 10px; border-radius: 5px;")
        btn_limpiar.clicked.connect(self.consola.clear)
        layout.addWidget(btn_limpiar)

    def iniciar_hilo(self):
        self.hilo_escucha = HiloEscuchaDiagnostico()
        self.hilo_escucha.paquete_recibido.connect(self.log_paquete)
        self.hilo_escucha.error_conexion.connect(self.log_error)
        self.hilo_escucha.start()
        self.lbl_estado_hilo.setText("ESTADO DEL HILO: ESCUCHANDO (OK)")
        self.lbl_estado_hilo.setStyleSheet("color: #50FA7B; font-weight: bold; font-size: 14px;")

    def log_paquete(self, ip, texto):
        self.consola.append(f"[{ip}] -> {texto}")

    def log_error(self, err):
        self.lbl_estado_hilo.setText(f"ESTADO DEL HILO: ERROR DE BIND")
        self.lbl_estado_hilo.setStyleSheet("color: #FF5555; font-weight: bold; font-size: 14px;")
        self.consola.append(f"<span style='color: #FF5555;'>{err}</span>")

    def closeEvent(self, event):
        if hasattr(self, 'hilo_escucha'):
            self.hilo_escucha.requestInterruption()
            self.hilo_escucha.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.args if hasattr(sys, 'args') else sys.argv)
    ventana = VentanaDiagnosticoNexus()
    ventana.show()
    sys.exit(qt_exec(app))