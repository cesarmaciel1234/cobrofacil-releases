"""Splash de arranque — versión ligera para monitores modestos (sin QPainter 3D ni sombras)."""
from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QLabel, QFrame, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QFont


class CobroFacilSplash(QSplashScreen):
    """Carga inicial minimalista: fondo sólido, texto nítido, barra plana."""

    def __init__(self):
        from src.utils.qt_dpi import scale_px, layout_scale, center_on_primary_screen

        self._ls = layout_scale()
        w = scale_px(460, self._ls)
        h = scale_px(240, self._ls)

        pixmap = QPixmap(w, h)
        pixmap.fill(QColor("#1E293B"))
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self.setFixedSize(w, h)
        self.current_status_text = "Iniciando..."

        root = QVBoxLayout(self)
        m = scale_px(24, self._ls)
        root.setContentsMargins(m, m, m, m)
        root.setSpacing(scale_px(12, self._ls))

        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 2px solid #334155;
                border-radius: 12px;
            }
            QLabel { background: transparent; border: none; color: #F8FAFC; }
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(scale_px(20, self._ls), scale_px(18, self._ls),
                               scale_px(20, self._ls), scale_px(18, self._ls))
        lay.setSpacing(scale_px(10, self._ls))

        title_fs = max(18, scale_px(22, self._ls))
        sub_fs = max(9, scale_px(10, self._ls))
        status_fs = max(10, scale_px(11, self._ls))

        self.lbl_title = QLabel("CAJAFACIL PRO")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        f = QFont("Segoe UI")
        f.setPixelSize(title_fs)
        f.setBold(True)
        self.lbl_title.setFont(f)
        self.lbl_title.setStyleSheet("color: #F8FAFC; letter-spacing: 2px;")
        lay.addWidget(self.lbl_title)

        self.lbl_sub = QLabel("Sistema de facturación POS")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        f2 = QFont("Segoe UI")
        f2.setPixelSize(sub_fs)
        f2.setBold(True)
        self.lbl_sub.setFont(f2)
        self.lbl_sub.setStyleSheet("color: #94A3B8;")
        lay.addWidget(self.lbl_sub)

        lay.addSpacing(scale_px(8, self._ls))

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(max(6, scale_px(8, self._ls)))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        lay.addWidget(self.progress_bar)

        self.lbl_status = QLabel(self.current_status_text)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        f3 = QFont("Segoe UI")
        f3.setPixelSize(status_fs)
        f3.setBold(True)
        self.lbl_status.setFont(f3)
        self.lbl_status.setStyleSheet("color: #CBD5E1;")
        lay.addWidget(self.lbl_status)

        root.addWidget(panel)
        try:
            center_on_primary_screen(self)
        except Exception:
            pass

    def update_status(self, text, progress_val=None):
        self.current_status_text = text
        self.lbl_status.setText(text)
        if progress_val is not None:
            self.progress_bar.setValue(progress_val)
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.processEvents()
