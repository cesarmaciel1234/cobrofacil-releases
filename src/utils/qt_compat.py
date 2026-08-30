"""
Capa de compatibilidad Qt — Cobro Fácil POS.

Rama feature/pyqt6: PyQt6 por defecto.
Migración: exportar TPV_QT=6 e instalar requirements-pyqt6.txt.

Uso recomendado en código nuevo o al tocar bootstrap:
    from src.utils.qt_compat import qt_exec, screen_geometry_at, VariantFloatAnimation
"""

from __future__ import annotations

import os
import sys

from PyQt6 import QtCore, QtGui, QtWidgets  # noqa: F401

QT_VERSION = 6
Qt = QtCore.Qt
IS_QT6 = True
QT_BINDING = "PyQt6"


def _patch_qt_enums() -> None:
    """Re-exporta enums anidados en Qt (PyQt5 API) para código legacy del cajero."""
    if not IS_QT6:
        return
    for group_name in dir(Qt):
        if group_name.startswith("_"):
            continue
        group = getattr(Qt, group_name)
        members = getattr(group, "__members__", None)
        if members is None:
            continue
        for member_name, member_val in members.items():
            if not hasattr(Qt, member_name):
                setattr(Qt, member_name, member_val)


def _patch_class_enums(cls) -> None:
    """Re-exporta enums anidados en widgets (QHeaderView.Fixed, QMessageBox.Yes…)."""
    if not IS_QT6:
        return
    for group_name in dir(cls):
        if group_name.startswith("_"):
            continue
        try:
            group = getattr(cls, group_name)
        except AttributeError:
            continue
        members = getattr(group, "__members__", None)
        if members is None:
            continue
        for member_name, member_val in members.items():
            if not hasattr(cls, member_name):
                setattr(cls, member_name, member_val)


_WIDGET_ENUM_CLASSES = (
    "QAbstractItemView",
    "QAbstractScrollArea",
    "QComboBox",
    "QDialog",
    "QFileDialog",
    "QFrame",
    "QHeaderView",
    "QInputDialog",
    "QLineEdit",
    "QMessageBox",
    "QSizePolicy",
    "QTableWidget",
    "QStyle",
    "QApplication",
    "QGraphicsEffect",
    "QAbstractSpinBox",
    "QSpinBox",
    "QDoubleSpinBox",
)

_CORE_ENUM_CLASSES = (
    "QEvent",
    "QEasingCurve",
    "QIODevice",
    "QTimer",
    "QThread",
)

_GUI_ENUM_CLASSES = (
    "QPainter",
    "QKeySequence",
    "QPalette",
    "QFont",
    "QCursor",
    "QTextCursor",
    "QTextOption",
)


def _patch_widget_enums() -> None:
    if not IS_QT6:
        return
    for name in _WIDGET_ENUM_CLASSES:
        cls = getattr(QtWidgets, name, None)
        if cls is not None:
            _patch_class_enums(cls)
            
    for name in _CORE_ENUM_CLASSES:
        cls = getattr(QtCore, name, None)
        if cls is not None:
            _patch_class_enums(cls)
            
    for name in _GUI_ENUM_CLASSES:
        cls = getattr(QtGui, name, None)
        if cls is not None:
            _patch_class_enums(cls)


_patch_qt_enums()
_patch_widget_enums()

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
    if hasattr(QtWidgets.QApplication, "setHighDpiScaleFactorRoundingPolicy"):
        try:
            policy = Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        except AttributeError:
            policy = Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(policy)


def set_share_opengl_contexts() -> None:
    """Requerido por QtWebEngine antes de QApplication."""
    try:
        attr = Qt.ApplicationAttribute.AA_ShareOpenGLContexts
        if attr is not None:
            QtCore.QCoreApplication.setAttribute(attr, True)
    except Exception:
        pass


def prepare_frozen_qt_paths() -> None:
    """DLL de QtWebEngine en el .exe: PATH y QtWebEngineProcess junto a _internal."""
    if not getattr(sys, "frozen", False):
        return
    roots = []
    meipass = getattr(sys, "_MEIPASS", "") or ""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    if meipass:
        roots.append(meipass)
    roots.extend([
        os.path.join(exe_dir, "_internal"),
        exe_dir,
    ])
    extra = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        extra.append(root)
        for sub in (
            os.path.join("PyQt6", "Qt6", "bin"),
            os.path.join("PyQt6", "Qt6", "plugins"),
            "PyQt6",
        ):
            path = os.path.join(root, sub)
            if os.path.isdir(path):
                extra.append(path)
    if extra:
        os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])
    for root in roots:
        plugin = os.path.join(root, "PyQt6", "Qt6", "plugins")
        if os.path.isdir(plugin):
            os.environ["QT_PLUGIN_PATH"] = plugin
            break
    for root in roots:
        for rel in (
            os.path.join("PyQt6", "Qt6", "bin", "QtWebEngineProcess.exe"),
            "QtWebEngineProcess.exe",
        ):
            proc = os.path.join(root, rel)
            if os.path.isfile(proc):
                os.environ["QTWEBENGINEPROCESS_PATH"] = proc
                return


def queued_connection():
    try:
        return Qt.ConnectionType.QueuedConnection
    except AttributeError:
        return Qt.QueuedConnection


def invoke_method(obj, method_name: str, *args) -> bool:
    """Invoca un @pyqtSlot en el hilo del QObject (seguro desde threads)."""
    conn = queued_connection()
    if args:
        return QtCore.QMetaObject.invokeMethod(
            obj,
            method_name,
            conn,
            *[QtCore.Q_ARG(type(a), a) for a in args],
        )
    return QtCore.QMetaObject.invokeMethod(obj, method_name, conn)


def create_webengine_page(parent, callback):
    """Crea una QWebEnginePage que intercepta console.log de forma segura."""
    try:
        from PyQt6.QtWebEngineCore import QWebEnginePage
    except ImportError:
        return None

    class HookedPage(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, message, line, source):
            callback(level, message, line, source)
    
    return HookedPage(parent)

def webengine_page_transparent(page) -> None:
    """Fondo transparente del canvas WebEngine."""
    try:
        from PyQt6.QtGui import QColor
        page.setBackgroundColor(QColor(0, 0, 0, 0))
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
    if app is None:
        try:
            app = QtWidgets.QApplication.instance() or QtGui.QGuiApplication.instance()
        except AttributeError:
            app = None

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


def easing_sine_curve():
    """QEasingCurve.SineCurve compatible PyQt5/PyQt6."""
    try:
        return QEasingCurve.Type.SineCurve
    except AttributeError:
        return QEasingCurve.SineCurve


class VariantFloatAnimation(QObject):
    """
    Animación de float para PyQt6 (usa QPropertyAnimation).
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
