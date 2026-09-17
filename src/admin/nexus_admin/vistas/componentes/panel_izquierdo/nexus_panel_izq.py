from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class NexusPanelIzq(QWidget):
    def __init__(self):
        super().__init__()
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(10)

        self.lbl_title = QLabel("💻 TERMINAL SYS.OP")
        self.lbl_title.setStyleSheet("font-family: Consolas; font-size: 12px; font-weight: bold; color: #F59E0B;")
        self.lay.addWidget(self.lbl_title)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 11))
        self.terminal_output.setStyleSheet('''
            QTextEdit {
                background-color: #FFFFFF; color: #000000; 
                border: 1px solid #000000; border-radius: 0px; padding: 4px;
                font-family: Consolas; font-size: 11px;
            }
        ''')
        self.lay.addWidget(self.terminal_output, 1)

        self.lbl_topo = QLabel("📡 TOPOLOGIA DE RED // LOGS DE TRAFICO UDP")
        self.lbl_topo.setStyleSheet("font-family: Consolas; font-size: 11px; font-weight: bold; color: #38BDF8; margin-top: 10px;")
        self.lay.addWidget(self.lbl_topo)

        self.txt_topo = QTextEdit()
        self.txt_topo.setReadOnly(True)
        self.txt_topo.setFont(QFont("Consolas", 9))
        self.txt_topo.setFixedHeight(120)
        self.txt_topo.setStyleSheet('''
            QTextEdit {
                background-color: #0F172A; color: #38BDF8; 
                border: 1px solid #1E293B; border-radius: 6px; padding: 5px;
            }
        ''')
        self.lay.addWidget(self.txt_topo)

        self._boot_sequence()

    def _boot_sequence(self):
        self.terminal_output.append("[SYSTEM] INICIANDO ENTORNO SEGURO...")
        self.terminal_output.append("[SYSTEM] CONECTANDO A MOTOR NEXUS_GLOBAL_CEREBRO...")
        self.terminal_output.append("[SYSTEM] ESTADO: ONLINE\n")
        self.txt_topo.append("--- INICIANDO RASTREO UDP ---")

    def update_theme(self, theme):
        # Terminal siempre estilo blanco minimalista para vigilancia
        self.terminal_output.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #000000; border-radius: 0px; padding: 4px; font-family: Consolas; font-size: 11px; }")
        self.txt_topo.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #000000; border-radius: 0px; padding: 4px; font-family: Consolas; font-size: 10px; }")


    def add_log(self, text):
        self.terminal_output.append(f"> {text}")
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()

    def add_structured_log(self, titulo, accion, descripcion, color_titulo="#000000", color_accion="#000000"):
        self.terminal_output.append("")
        titulo_html = f'<b style="font-size: 12px;">=== {titulo.upper()} ===</b>'
        self.terminal_output.insertHtml(titulo_html + "<br>")
        self.terminal_output.append("-" * (len(titulo) + 10))
        self.terminal_output.append(f"• {accion}")
        self.terminal_output.append(f"  {descripcion}")
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()

    def inject_ai_log(self, category, origin, message, time_str):
        clean_org = origin.split('|')[-1].upper() if '|' in str(origin) else f"CAJA {origin}"
        
        if category == "VENTA_EFECTIVO": tipo = "VENTA EFECTIVO"; color = None
        elif category == "VENTA_DIGITAL": tipo = "VENTA DIGITAL"; color = None
        elif category == "APERTURA_SOFTWARE": tipo = "APERTURA CAJON (SOFTWARE)"; color = None
        elif category == "APERTURA_HARDWARE_OK": tipo = "APERTURA CAJON (VALIDADO)"; color = None
        elif category == "ALARMA_CRITICA": tipo = "ALERTA CRITICA"; color = "#FF0000"
        elif category == "INTERVENCION": tipo = "INTERVENCION ADMIN"; color = "#FF6600"
        else: tipo = category; color = None

        if color:
            log_html = f'<span style="color: {color}; font-weight: bold;">[{time_str}] [{clean_org}] {tipo}:</span> {message}'
            self.terminal_output.append(log_html)
        else:
            log_text = f"[{time_str}] [{clean_org}] {tipo}: {message}"
            self.terminal_output.append(log_text)
        
        self.terminal_output.append("") # Pequeña separación
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()

    def _trim_terminal(self):
        if self.terminal_output.document().lineCount() > 150:
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
    def log_udp(self, text):
        self.txt_topo.append(f"~ {text}")
        if self.txt_topo.document().lineCount() > 50:
            cursor = self.txt_topo.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
