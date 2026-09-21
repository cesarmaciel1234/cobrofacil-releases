from PyQt6.QtCore import Qt


def aplicar_tecla(dialogo, event) -> bool:
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        dialogo.accept()
        return True
    if event.key() == Qt.Key.Key_Escape:
        dialogo.reject()
        return True
    return False
