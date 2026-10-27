"""Lista de filtros de la auditoría. Se abre bajo el botón y no consulta la red."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


def abrir(padre, ancla, cruce, cuenta, nombres, al_elegir, estilo_activo, estilo_idle):
    """Popup. `al_elegir(cruce, cuenta)` al tocar un chip. Si ya está abierto, lo cierra."""
    previo = getattr(padre, "_panel_filtros", None)
    if previo is not None and previo.isVisible():
        previo.hide()
        return previo
    panel = QFrame(padre, Qt.WindowType.Popup)
    panel.setStyleSheet(
        "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
        "QLabel { color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }"
    )
    caja = QVBoxLayout(panel)
    caja.setContentsMargins(14, 12, 14, 12)
    caja.setSpacing(8)
    caja.addWidget(QLabel("CRUCE"))
    caja.addLayout(_fila_chips(
        (
            ("Todos", "Todos"),
            ("Cruzados", "cruzado"),
            ("Ticket sin id", "ticket_sin_id"),
            ("Id sin ticket", "id_sin_ticket"),
        ),
        cruce or "Todos",
        lambda clave: al_elegir(clave, cuenta),
        estilo_activo,
        estilo_idle,
    ))
    vistos = []
    for nombre in nombres or []:
        texto = str(nombre or "").strip()
        if texto and texto not in vistos:
            vistos.append(texto)
    if len(vistos) > 1:
        caja.addWidget(QLabel("CUENTA"))
        chips = [("Todas", "")] + [(nombre, nombre) for nombre in vistos]
        caja.addLayout(_fila_chips(
            chips,
            cuenta or "",
            lambda clave: al_elegir(cruce, clave),
            estilo_activo,
            estilo_idle,
        ))
    panel.adjustSize()
    panel.move(ancla.mapToGlobal(ancla.rect().bottomLeft()))
    padre._panel_filtros = panel
    panel.show()
    return panel


def _fila_chips(opciones, activo, al_click, estilo_activo, estilo_idle):
    fila = QHBoxLayout()
    fila.setSpacing(6)
    for texto, clave in opciones:
        boton = QPushButton(texto)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setStyleSheet(estilo_activo if clave == activo else estilo_idle)
        boton.clicked.connect(lambda _c=False, k=clave: al_click(k))
        fila.addWidget(boton)
    return fila
