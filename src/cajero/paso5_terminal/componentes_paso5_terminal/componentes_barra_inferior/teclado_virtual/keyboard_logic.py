from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from .constants import KEY_MAP
from .keyboard_ui import build_keys

def handle_key_press(keyboard, key_text):
    focused = QApplication.focusWidget()
    if not focused:
        return

    if key_text == "⚡ SHIFT":
        keyboard.shift_active = not keyboard.shift_active
        for orig_char, btn in keyboard.letter_buttons.items():
            btn.setText(orig_char.upper() if keyboard.shift_active else orig_char.lower())
        return

    elif key_text == "?123":
        keyboard.set_layout_mode("123")
        return

    elif key_text == "ABC":
        keyboard.set_layout_mode("abc")
        return

    modifiers = Qt.KeyboardModifier.ShiftModifier if keyboard.shift_active else Qt.KeyboardModifier.NoModifier

    if key_text == "⌫":
        send_key_event(focused, Qt.Key.Key_Backspace, "", modifiers)
    elif key_text == "ESPACIO":
        send_key_event(focused, Qt.Key.Key_Space, " ", modifiers)
    elif key_text == "ENTER":
        send_key_event(focused, Qt.Key.Key_Return, "\n", modifiers)
        keyboard.hide()
        return
    else:
        char_to_send = key_text
        if keyboard.layout_mode == "abc" and not keyboard.shift_active and len(char_to_send) == 1:
            char_to_send = char_to_send.lower()

        key_code = KEY_MAP.get(char_to_send.lower() if len(char_to_send) == 1 else char_to_send, Qt.Key.Key_unknown)
        send_key_event(focused, key_code, char_to_send, modifiers)

def send_key_event(target, key_code, text, modifiers):
    event_press = QKeyEvent(QEvent.Type.KeyPress, key_code, modifiers, text)
    QApplication.sendEvent(target, event_press)

    event_release = QKeyEvent(QEvent.Type.KeyRelease, key_code, modifiers, text)
    QApplication.sendEvent(target, event_release)
