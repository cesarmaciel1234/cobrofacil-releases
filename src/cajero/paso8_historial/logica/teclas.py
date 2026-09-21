from PyQt6.QtCore import Qt


def aplicar_tecla(dialogo, event) -> bool:
    if event.key() == Qt.Key.Key_Escape:
        dialogo.accept()
        return True
    return False
