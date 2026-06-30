from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

class PanelArqueo(QFrame):
    enter_pressed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelArq")
        
        self.esperado = 0.0
        
        # Sombra de elevación para el panel derecho
        # Se elimina QGraphicsDropShadowEffect para mejorar rendimiento.
        
        pa_lay = QVBoxLayout(self)
        pa_lay.setContentsMargins(30, 30, 30, 30)
        pa_lay.setSpacing(20)
        
        lbl_esp_tit = QLabel("EFECTIVO ESPERADO")
        lbl_esp_tit.setObjectName("PanelArqTitEsp")
        lbl_esp_tit.setAlignment(Qt.AlignCenter)
        pa_lay.addWidget(lbl_esp_tit)
        
        self.lbl_esp = QLabel("••••••")
        self.lbl_esp.setAlignment(Qt.AlignCenter)
        self.lbl_esp.setObjectName("PanelArqValEsp")
        pa_lay.addWidget(self.lbl_esp)
        
        pa_lay.addSpacing(10)
        lbl_fisico_tit = QLabel("INGRESA EL FÍSICO CONTADO ($)")
        lbl_fisico_tit.setObjectName("PanelArqTitFis")
        lbl_fisico_tit.setAlignment(Qt.AlignCenter)
        pa_lay.addWidget(lbl_fisico_tit)
        
        self.txt_fisico = QLineEdit("0.00")
        self.txt_fisico.setAlignment(Qt.AlignCenter)
        self.txt_fisico.setObjectName("PanelArqValFis")
        self.txt_fisico.textChanged.connect(self._update_diff)
        pa_lay.addWidget(self.txt_fisico)
        
        self.frame_dif = QFrame()
        self.frame_dif.setFixedHeight(90)
        self.frame_dif.setObjectName("FrameDif")
        fd_lay = QHBoxLayout(self.frame_dif)
        
        lbl_dif_tit = QLabel("DIFERENCIA:")
        lbl_dif_tit.setObjectName("FrameDifTit")
        fd_lay.addWidget(lbl_dif_tit)
        
        self.lbl_dif = QLabel("--")
        self.lbl_dif.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_dif.setObjectName("FrameDifVal")
        fd_lay.addWidget(self.lbl_dif)
        pa_lay.addWidget(self.frame_dif)
        
        self._sos_timer = QTimer(self)
        self._sos_timer.timeout.connect(self._blink_sos)
        
    def get_fisico_y_dif(self):
        try:
            from src.utils.parser import parse_float_regional
            fisico = parse_float_regional(self.txt_fisico.text())
            dif = fisico - self.esperado
            return fisico, dif
        except:
            return 0.0, -self.esperado

    def _update_diff(self):
        try:
            from src.utils.parser import parse_float_regional
            fisico = parse_float_regional(self.txt_fisico.text())
            dif = fisico - self.esperado
            if dif >= 0:
                self.lbl_dif.setText(f"+$ {dif:,.2f} (Sobrante)")
                self.frame_dif.setProperty("estado", "sobrante")
                if self._sos_timer.isActive():
                    self._sos_timer.stop()
            else:
                self.lbl_dif.setText(f"-$ {abs(dif):,.2f} (Faltante)")
                self.frame_dif.setProperty("estado", "faltante")
                if not self._sos_timer.isActive():
                    self._sos_timer.start(400)
                
            self.frame_dif.style().unpolish(self.frame_dif)
            self.frame_dif.style().polish(self.frame_dif)
            self.lbl_dif.style().unpolish(self.lbl_dif)
            self.lbl_dif.style().polish(self.lbl_dif)
        except: pass

    def _blink_sos(self):
        # Blink handled by state "sos" vs "faltante"
        if self._sos_timer.remainingTime() % 800 < 400:
            self.frame_dif.setProperty("estado", "sos")
        else:
            self.frame_dif.setProperty("estado", "faltante")
        self.frame_dif.style().unpolish(self.frame_dif)
        self.frame_dif.style().polish(self.frame_dif)

    def focus_fisico(self):
        self.txt_fisico.setFocus()
        
    def has_focus_fisico(self):
        return self.txt_fisico.hasFocus()

    def _finalizar(self):
        self.parent()._finalizar()

    def set_esperado(self, valor):
        self.esperado = valor
        self.lbl_esp.setText(f"$ {valor:,.2f}")
        self.lbl_esp.setProperty("modo", "revelado")
        self.lbl_esp.style().unpolish(self.lbl_esp)
        self.lbl_esp.style().polish(self.lbl_esp)
        self._update_diff()
