"""
Capa de compatibilidad Qt — Cobro Fácil POS.

Producción actual: PyQt5 (por defecto).
Migración: exportar TPV_QT=6 e instalar requirements-pyqt6.txt.

Uso recomendado en código nuevo o al tocar bootstrap:
    from src.utils.qt_compat import qt_exec, screen_geometry_at, VariantFloatAnimation
"""

from __future__ import annotations

import os
import sys

_QT_PREF = os.environ.get("TPV_QT", "5").strip()


def _load_qt():
    if _QT_PREF == "6":
        try:
            from PyQt6 import QtCore, QtGui, QtWidgets  # noqa: F401
            return 6, QtCore, QtGui, QtWidgets
        except ImportError as exc:
            raise ImportError(
                "TPV_QT=6 pero PyQt6 no está instalado. "
                "Ejecuta: pip install -r requirements-pyqt6.txt"
            ) from exc
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: F401
        return 5, QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise ImportError(
            "PyQt5 no está instalado. Ejecuta: pip install -r requirements.txt"
        ) from exc


QT_VERSION, QtCore, QtGui, QtWidgets = _load_qt()
Qt = QtCore.Qt

IS_QT6 = QT_VERSION >= 6
QT_BINDING = "PyQt6" if IS_QT6 else "PyQt5"

# Re-export frecuentes (import único en módulos que migren)
QApplication = QtWidgets.QApplication
QCoreApplication = QtCore.QCoreApplication
pyqtSignal = QtCore.pyqtSignal
pyqtSlot = QtCore.pyqtSlot
QPropertyAnimation = QtCore.QPropertyAnimation
QEasingCurve = QtCore.QEasingCurve
QObject = QtCore.QObject


def qt_exec(obj, *args, **kwargs):
    """QDialog/QMenu/QApplication.exec compatible PyQt5 y PyQt6."""
    runner = getattr(obj, "exec", None) or getattr(obj, "exec_", None)
    if runner is None:
        raise TypeError(f"{type(obj).__name__} no tiene exec/exec_")
    return runner(*args, **kwargs)


def configure_qt_application_attributes() -> None:
    """Atributos de app antes del primer QApplication()."""
    if IS_QT6:
        if hasattr(QtWidgets.QApplication, "setHighDpiScaleFactorRoundingPolicy"):
            try:
                policy = Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            except AttributeError:
                policy = Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(policy)
        return

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def set_share_opengl_contexts() -> None:
    """Requerido por QtWebEngine antes de QApplication."""
    try:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    except Exception:
        pass


def screen_count(app=None) -> int:
    app = app or QApplication.instance()
    if app is None:
        return 1
    screens = app.screens()
    return len(screens) if screens else 1


def screen_geometry_at(index: int = 0, app=None):
    """Geometría usable de un monitor (reemplaza QApplication.desktop())."""
    from PyQt5.QtWidgets import QApplication as _QApp5
    from PyQt5.QtGui import QGuiApplication as _QGui5

    if IS_QT6:
        from PyQt6.QtWidgets import QApplication as QApp6
        from PyQt6.QtGui import QGuiApplication as QGui6

        app = app or QApp6.instance() or QGui6.instance()
    else:
        app = app or _QApp5.instance() or _QGui5.instance()

    if app is None:
        return None
    screens = app.screens()
    if not screens:
        return None
    idx = max(0, min(index, len(screens) - 1))
    return screens[idx].availableGeometry()


def _easing_linear():
    try:
        return QEasingCurve.Type.Linear  # PyQt6
    except AttributeError:
        return QEasingCurve.Linear  # PyQt5


class VariantFloatAnimation(QObject):
    """
  Animación de float compatible PyQt5/QPyQt6.
  En PyQt5 usa QVariantAnimation; en PyQt6 usa QPropertyAnimation.
  API compatible: setStartValue, setEndValue, setDuration, valueChanged,
  finished, setEasingCurve, setLoopCount, start, stop.
    """

    valueChanged = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 250
        self._easing = _easing_linear()
        self._loop_count = 1
        self._start = 0.0
        self._end = 1.0
        self._anim = None
        self._qt5_anim = None

    def setStartValue(self, value):
        self._start = float(value)

    def setEndValue(self, value):
        self._end = float(value)

    def setDuration(self, ms: int):
        self._duration = int(ms)

    def setEasingCurve(self, curve):
        self._easing = curve

    def setLoopCount(self, count: int):
        self._loop_count = int(count)

    def start(self):
        self.stop()
        if not IS_QT6:
            from PyQt5.QtCore import QVariantAnimation

            self._qt5_anim = QVariantAnimation(self)
            self._qt5_anim.setStartValue(self._start)
            self._qt5_anim.setEndValue(self._end)
            self._qt5_anim.setDuration(self._duration)
            self._qt5_anim.setEasingCurve(self._easing)
            self._qt5_anim.setLoopCount(self._loop_count)
            self._qt5_anim.valueChanged.connect(self.valueChanged.emit)
            self._qt5_anim.finished.connect(self.finished.emit)
            self._qt5_anim.start()
            return

        holder = _FloatHolder(self._start, self.valueChanged.emit, parent=self)
        self._holder = holder
        self._anim = QPropertyAnimation(holder, b"value")
        self._anim.setStartValue(self._start)
        self._anim.setEndValue(self._end)
        self._anim.setDuration(self._duration)
        self._anim.setEasingCurve(self._easing)
        self._anim.setLoopCount(self._loop_count)
        self._anim.finished.connect(self.finished.emit)
        self._anim.start()

    def stop(self):
        if self._qt5_anim is not None:
            self._qt5_anim.stop()
            self._qt5_anim = None
        if self._anim is not None:
            self._anim.stop()
            self._anim = None


class _FloatHolder(QObject):
    """Helper interno para QPropertyAnimation de floats en Qt6."""

    def __init__(self, value: float, on_change, parent=None):
        super().__init__(parent)
        self._value = float(value)
        self._on_change = on_change

    def getValue(self) -> float:
        return self._value

    def setValue(self, value: float) -> None:
        self._value = float(value)
        self._on_change(self._value)

    value = QtCore.pyqtProperty(float, getValue, setValue)


def binding_info() -> dict:
    return {
        "binding": QT_BINDING,
        "qt_version": QT_VERSION,
        "is_qt6": IS_QT6,
        "python": sys.version.split()[0],
    }
