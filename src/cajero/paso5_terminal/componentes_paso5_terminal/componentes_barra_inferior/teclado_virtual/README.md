# Teclado Virtual Paso 5

Teclado en pantalla del paso 5. Se abre solo al tocar un cuadro, y solo si Windows ve una pantalla táctil. Escribir con el teclado físico o el escáner no lo abre. El botón TECLADO lo abre igual.

## Architecture
The logic has been split into several modules to enforce separation of concerns and a pyramidal structure:

- `virtual_keyboard_paso5.py`: The main entry point. Defines the `VirtualKeyboardPaso5` widget. It brings together UI and logic components.
- `keyboard_ui.py`: Handles everything related to building the layout of the UI (the drag bar, titles, close button, keys container, styles).
- `keyboard_logic.py`: Handles all the behavior (key presses, shift toggling, layout switching, and sending `QKeyEvent`s to focused widgets).
- `keys_layout.py`: Defines the visual arrangement of keys for the different modes (`abc` and `123`).
- `constants.py`: Holds mappings like the `KEY_MAP` which translates strings into `Qt.Key` objects.

## Modifying the Keyboard
- **Change layout or add a key:** Update the `abc` or `123` list in `keys_layout.py`.
- **Change visual styles:** Update the `apply_theme` or `build_keys` methods inside `keyboard_ui.py`.
- **Add custom behavior for a key:** Modify `handle_key_press` in `keyboard_logic.py` and map the corresponding logic.
- **Add new symbols:** Make sure the corresponding key code is mapped in `constants.py`.

## Usage
Simply import the `VirtualKeyboardPaso5` class and use it normally in `paso5_terminal.py` or anywhere else.

```python
from src.cajero.paso5_terminal.componentes_paso5_terminal.componentes_barra_inferior.teclado_virtual.virtual_keyboard_paso5 import VirtualKeyboardPaso5

# Instantiation
keyboard = VirtualKeyboardPaso5(parent_widget)
keyboard.show()
```
