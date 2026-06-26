"""Tests de la capa qt_compat (PyQt6 por defecto en main)."""
from src.utils.qt_compat import qt_exec
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Forzar PyQt5 en CI/desarrollo salvo que se pruebe explícitamente Qt6
os.environ.setdefault("TPV_QT", "6")


class TestQtCompat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls._app = QApplication.instance() or QApplication([])

    def test_binding_info(self):
        from src.utils.qt_compat import binding_info, IS_QT6, QT_BINDING

        info = binding_info()
        self.assertIn("binding", info)
        if os.environ.get("TPV_QT", "6") == "6":
            self.assertTrue(IS_QT6)
            self.assertEqual(QT_BINDING, "PyQt6")
        else:
            self.assertFalse(IS_QT6)
            self.assertEqual(QT_BINDING, "PyQt5")

    def test_qt_exec_dialog(self):
        from PyQt6.QtWidgets import QDialog

        dlg = QDialog()
        dlg.setResult(0)
        self.assertEqual(qt_exec(dlg), 0)

    def test_screen_helpers(self):
        from src.utils.qt_compat import screen_count, screen_geometry_at

        self.assertGreaterEqual(screen_count(), 1)
        geo = screen_geometry_at(0)
        self.assertIsNotNone(geo)
        self.assertGreater(geo.width(), 0)

    def test_variant_float_animation(self):
        import time
        from src.utils.qt_compat import VariantFloatAnimation

        values = []
        anim = VariantFloatAnimation()
        anim.setStartValue(0.0)
        anim.setEndValue(10.0)
        anim.setDuration(100)
        anim.valueChanged.connect(values.append)
        anim.start()
        t0 = time.time()
        while time.time() - t0 < 0.5:
            self._app.processEvents()
            time.sleep(0.01)
        anim.stop()
        self.assertTrue(len(values) >= 1)


if __name__ == "__main__":
    unittest.main()
