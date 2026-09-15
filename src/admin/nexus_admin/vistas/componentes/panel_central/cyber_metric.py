from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class CyberMetric(QFrame):
    def __init__(self, title, icon):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background: rgba(15, 23, 42, 0.6); border: 1px solid #1E293B; border-radius: 8px;")
        lay = QVBoxLayout(self)
        
        lbl_t = QLabel(f"{icon} {title}")
        lbl_t.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.val_label = QLabel("$ 0")
        self.val_label.setStyleSheet("color: #F8FAFC; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay.addWidget(lbl_t)
        lay.addWidget(self.val_label)

