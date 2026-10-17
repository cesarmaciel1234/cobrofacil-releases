from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

# Cache de colores para evitar recrear el dict en cada instancia
_COLOR_CACHE = {
    "indigo": ("#E0E7FF", "#3730A3"),
    "blue": ("#DBEAFE", "#1E40AF"),
    "amber": ("#FEF3C7", "#92400E"),
    "emerald": ("#D1FAE5", "#065F46"),
    "rose": ("#FFE4E6", "#9F1239"),
    "violet": ("#EDE9FE", "#5B21B6"),
    "pink": ("#FCE7F3", "#9D174D"),
    "slate": ("#F1F5F9", "#334155"),
    "sky": ("#E0F2FE", "#075985")
}


class AdminCard(QFrame):
    clicked = pyqtSignal()
    desanclar = pyqtSignal()

    def __init__(self, title, icon, palette_name, sub, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clic: este monitor.  +: otra ventana (mismo proceso).")

        bg_soft, txt_dark = _COLOR_CACHE.get(palette_name, ("#F1F5F9", "#334155"))

        self.setStyleSheet(f"""
            AdminCard {{
                background-color: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-radius: 16px;
            }}
            AdminCard:hover {{
                background-color: #F8FAFC;
                border: 2px solid {txt_dark};
            }}
        """)
        self.setFixedSize(190, 160)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_icon = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setFixedSize(54, 54)
        lbl_icon.setStyleSheet(
            f"font-size: 26px; background-color: {bg_soft}; color: {txt_dark}; "
            "border-radius: 14px; border: none;"
        )
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_icon.addStretch()
        h_icon.addWidget(lbl_icon)
        h_icon.addStretch()

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-weight: 800; font-size: 15px; color: #0F172A; "
            "background: transparent; border: none;"
        )
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)

        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet(
            "font-weight: 700; font-size: 13px; color: #1E293B; "
            "background: transparent; border: none;"
        )
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)

        lay.addLayout(h_icon)
        lay.addSpacing(10)
        lay.addWidget(lbl_title)
        lay.addStretch()
        lay.addWidget(lbl_sub)

        self.btn_mas = QPushButton("+", self)
        self.btn_mas.setFixedSize(24, 24)
        self.btn_mas.move(190 - 24 - 8, 8)
        self.btn_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_mas.setToolTip("Abrir en otra ventana")
        self.btn_mas.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; "
            "border-radius: 12px; font-size: 16px; font-weight: 800; padding: 0; }"
            "QPushButton:hover { background: #2563EB; color: #FFFFFF; border-color: #2563EB; }"
        )
        self.btn_mas.clicked.connect(self.desanclar.emit)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.desanclar.emit()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            mods = event.modifiers()
            if mods & Qt.KeyboardModifier.ControlModifier:
                self.desanclar.emit()
            else:
                self.clicked.emit()
        super().mousePressEvent(event)
