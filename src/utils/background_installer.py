"""
background_installer.py
=======================
Instala las dependencias opcionales en segundo plano
mientras el cliente ya usa la app.

Uso en main_window.py:
    from src.utils.background_installer import BackgroundInstaller
    BackgroundInstaller.iniciar(parent_widget)
"""
import os
import sys
import subprocess
import threading
import logging
from PyQt5.QtWidgets import QWidget, QLabel, QProgressBar, QHBoxLayout
from PyQt5.QtCore    import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui     import QFont

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REQ_FULL     = os.path.join(BASE_DIR, "requirements_full.txt")
FLAG_FILE    = os.path.join(BASE_DIR, ".install_complete")   # existe = ya instalado todo
VENV_PIP     = os.path.join(BASE_DIR, ".venv", "Scripts", "pip.exe")


def _ya_instalado() -> bool:
    """Retorna True si ya se completó la instalación completa alguna vez."""
    return os.path.exists(FLAG_FILE)


def _marcar_completo():
    """Crea el flag para no volver a instalar."""
    try:
        with open(FLAG_FILE, "w") as f:
            f.write("ok")
    except:
        pass


def _paquetes_faltantes() -> list:
    """Lista los paquetes de requirements_full que no están instalados."""
    if not os.path.exists(REQ_FULL):
        return []
    faltantes = []
    try:
        r = subprocess.run(
            [VENV_PIP, "list", "--format=columns"],
            capture_output=True, text=True, timeout=10
        )
        instalados = {line.split()[0].lower()
                      for line in r.stdout.splitlines()[2:]
                      if line.strip()}
        with open(REQ_FULL) as f:
            for line in f:
                pkg = line.strip().split("==")[0].strip()
                if pkg and not pkg.startswith("#"):
                    if pkg.lower() not in instalados:
                        faltantes.append(pkg)
    except:
        pass
    return faltantes


# ── Señales ───────────────────────────────────────────────────────────────────
class _Signals(QObject):
    progreso   = pyqtSignal(int, str)   # pct, mensaje
    completado = pyqtSignal()
    ocultar    = pyqtSignal()


# ── Widget flotante discreto ──────────────────────────────────────────────────
class InstaladorWidget(QWidget):
    """
    Barra pequeña en la parte inferior de la pantalla.
    Se muestra mientras se instalan las dependencias opcionales.
    Se oculta sola cuando termina.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e293b;
                border-top: 2px solid #3b82f6;
            }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(12)

        self.lbl_icono = QLabel("⚙️")
        self.lbl_icono.setStyleSheet("font-size: 16px; background: transparent; border: none;")

        self.lbl = QLabel("Completando instalación en segundo plano...")
        self.lbl.setFont(QFont("Segoe UI", 10))
        self.lbl.setStyleSheet("color: #94a3b8; background: transparent; border: none;")

        self.bar = QProgressBar()
        self.bar.setFixedWidth(180)
        self.bar.setFixedHeight(8)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)

        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setFont(QFont("Segoe UI", 9))
        self.lbl_pct.setStyleSheet("color: #64748b; background: transparent; border: none;")
        self.lbl_pct.setFixedWidth(35)

        lay.addWidget(self.lbl_icono)
        lay.addWidget(self.lbl, 1)
        lay.addWidget(self.bar)
        lay.addWidget(self.lbl_pct)

    def actualizar(self, pct: int, msg: str):
        self.bar.setValue(pct)
        self.lbl_pct.setText(f"{pct}%")
        self.lbl.setText(msg)
        if pct >= 100:
            self.lbl_icono.setText("✅")
            self.lbl.setText("Sistema completo — todos los módulos listos")
            self.lbl.setStyleSheet("color: #10b981; background: transparent; border: none;")
            # Ocultar después de 4 segundos
            QTimer.singleShot(4000, self.hide)


# ── Instalador en background ──────────────────────────────────────────────────
class BackgroundInstaller:
    """
    Punto de entrada principal. Llamar una vez desde main_window.
    Si ya está todo instalado, no hace nada.
    """
    _signals  = None
    _widget   = None
    _iniciado = False

    @classmethod
    def iniciar(cls, parent_widget: QWidget) -> bool:
        """
        Inicia la instalación en background si es necesario.
        Retorna True si se inició, False si ya estaba todo instalado.
        """
        if cls._iniciado:
            return False
        if _ya_instalado():
            return False

        faltantes = _paquetes_faltantes()
        if not faltantes:
            _marcar_completo()
            return False

        cls._iniciado = True
        cls._signals  = _Signals()

        # Crear widget en la parte inferior
        cls._widget = InstaladorWidget(parent_widget)
        cls._widget.move(0, parent_widget.height() - 44)
        cls._widget.resize(parent_widget.width(), 44)
        cls._widget.show()
        cls._widget.raise_()

        # Conectar señales
        cls._signals.progreso.connect(cls._widget.actualizar)
        cls._signals.completado.connect(_marcar_completo)

        # Hilo de instalación
        t = threading.Thread(
            target=cls._instalar,
            args=(faltantes,),
            daemon=True
        )
        t.start()
        return True

    @classmethod
    def _instalar(cls, paquetes: list):
        total = len(paquetes)
        logging.info(f"[BG-INSTALL] Instalando {total} paquetes en background: {paquetes}")

        for idx, pkg in enumerate(paquetes):
            pct = int(10 + 85 * idx / total)
            cls._signals.progreso.emit(pct, f"Instalando {pkg}...")
            try:
                subprocess.run(
                    [VENV_PIP, "install", "--quiet", pkg],
                    capture_output=True, timeout=120
                )
                logging.info(f"[BG-INSTALL] ✓ {pkg}")
            except Exception as e:
                logging.warning(f"[BG-INSTALL] Error en {pkg}: {e}")

        cls._signals.progreso.emit(100, "Sistema completo")
        cls._signals.completado.emit()
        logging.info("[BG-INSTALL] Instalación completa finalizada")

    @classmethod
    def redimensionar(cls, width: int, height: int):
        """Llamar en resizeEvent del main_window para reubicar el widget."""
        if cls._widget and cls._widget.isVisible():
            cls._widget.move(0, height - 44)
            cls._widget.resize(width, 44)
