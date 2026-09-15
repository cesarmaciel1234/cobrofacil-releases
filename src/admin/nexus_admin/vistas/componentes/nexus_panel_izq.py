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
        self.terminal_output.setFont(QFont("Consolas", 10))
        self.terminal_output.setStyleSheet('''
            QTextEdit {
                background-color: #0B1120; color: #10B981; 
                border: 1px solid #1E293B; border-radius: 6px; padding: 5px;
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
        self.terminal_output.append("[SYSTEM] ESTADO: ONLINE")
        self.txt_topo.append("--- INICIANDO RASTREO UDP ---")

    def update_theme(self, theme):
        if theme == "dark":
            self.terminal_output.setStyleSheet("QTextEdit { background-color: #0B1120; color: #10B981; border: 1px solid #1E293B; border-radius: 6px; padding: 5px; }")
            self.txt_topo.setStyleSheet("QTextEdit { background-color: #0F172A; color: #38BDF8; border: 1px solid #1E293B; border-radius: 6px; padding: 5px; }")
        else:
            self.terminal_output.setStyleSheet("QTextEdit { background-color: #F8FAFC; color: #065F46; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px; }")
            self.txt_topo.setStyleSheet("QTextEdit { background-color: #F1F5F9; color: #0369A1; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px; }")

    def add_log(self, text):
        self.terminal_output.append(f"> {text}")
        if self.terminal_output.document().lineCount() > 100:
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
