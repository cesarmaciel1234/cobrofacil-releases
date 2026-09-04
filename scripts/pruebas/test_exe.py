import sys
from PyQt6.QtWidgets import QApplication
from src.navigation.screen_registry import build_screen_factories
from src.navigation.screen_indices import Screen

app = QApplication(sys.argv)
try:
    print("Loading factories...")
    f = build_screen_factories(None)
    print("Loading ETIQUETAS...")
    f[Screen.ETIQUETAS]()
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
