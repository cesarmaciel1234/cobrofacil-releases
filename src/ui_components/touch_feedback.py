import time
from PyQt6.QtWidgets import QPushButton, QTableWidget
from PyQt6.QtCore import QObject, QEvent, QTimer, Qt

class TouchFeedbackManager(QObject):
    """
    Gestor global de feedback visual estilo táctil.
    Opera de forma independiente del backend.
    """
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self._active_buttons = {}
        
        # Interceptar eventos a nivel de aplicación (Global)
        if parent_app:
            parent_app.installEventFilter(self)
            
            # Inyectar el destello/iluminación suave para las filas de las tablas
            # Estilo 'glow' elegante para las tablas
            glow_css = """
            QTableWidget::item:selected {
                background-color: rgba(37, 99, 235, 0.25) !important; /* Azul translúcido */
                border: 1px solid #60a5fa !important;
                color: #0f172a !important;
                font-weight: bold;
            }
            """
            current_style = parent_app.styleSheet()
            parent_app.setStyleSheet(current_style + glow_css)

    def eventFilter(self, obj, event):
        # Capturar clics de ratón
        if event.type() == QEvent.MouseButtonPress:
            if isinstance(obj, QPushButton):
                self.trigger_button_feedback(obj)
        elif event.type() == QEvent.MouseButtonRelease:
            if isinstance(obj, QPushButton):
                self.release_button_feedback(obj)
                
        # Capturar pulsaciones de teclado (Enter/Espacio en botón con foco)
        elif event.type() == QEvent.KeyPress:
            if isinstance(obj, QPushButton) and event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Space):
                self.trigger_button_feedback(obj)
        elif event.type() == QEvent.KeyRelease:
            if isinstance(obj, QPushButton) and event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Space):
                self.release_button_feedback(obj)
                
        # Capturar atajos de teclado globales (ej. F1, F4 ligados a botones)
        elif event.type() == QEvent.Shortcut:
            if isinstance(obj, QPushButton):
                self.trigger_button_feedback(obj)
                # Liberación automática para atajos (no hay evento de soltar atajo confiable)
                QTimer.singleShot(150, lambda: self.release_button_feedback(obj))
                
        return False # Nunca consumir el evento, dejar que el botón original funcione

    def trigger_button_feedback(self, btn):
        if btn in self._active_buttons:
            return
            
        original_style = btn.styleSheet()
        self._active_buttons[btn] = {
            'original_style': original_style,
            'press_time': time.time(),
            'released': False
        }
        
        # Efecto visual táctil: Color azul vibrante + sombra interna simulada + encogimiento
        press_style = original_style + """
            QPushButton {
                background-color: #2563eb !important; 
                color: white !important;
                border: 2px inset #1e40af !important;
                padding-top: 2px !important;
                padding-left: 2px !important;
            }
        """
        btn.setStyleSheet(press_style)

    def release_button_feedback(self, btn):
        if btn in self._active_buttons:
            state = self._active_buttons[btn]
            state['released'] = True
            
            elapsed_ms = (time.time() - state['press_time']) * 1000
            
            # Si soltó el botón antes de los 150ms, forzar el retraso de la animación
            # Si lo soltó después de 150ms, revertir inmediatamente
            if elapsed_ms >= 150:
                self.revert_button_feedback(btn)
            else:
                QTimer.singleShot(int(150 - elapsed_ms), lambda: self.revert_button_feedback(btn))

    def revert_button_feedback(self, btn):
        try:
            if btn in self._active_buttons:
                # Asegurarse de que realmente fue soltado antes de revertir
                if self._active_buttons[btn]['released']:
                    state = self._active_buttons.pop(btn)
                    btn.setStyleSheet(state['original_style'])
        except RuntimeError:
            # Ocurre si el botón de C++ fue destruido (por ejemplo al cambiar dinámicamente de layout)
            pass
