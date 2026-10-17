# Cartelería

Rama: `src/carteleria`. Plano: `plano.md`.

Qué hace: Admin → Cartelería. Dashboard, PNG de vitrina, lanzar la TV kiosk.

Qué función: dashboard en `dashboard/`. Configuración en `configuracion/` (`Admin15Carteleria`). `admin15_carteleria.py` solo reexporta. La TV vive en `lanzador_tv/`.

Cómo funciona: Configuración abre con disco local. MariaDB va en hilo (`configuracion/motor/`). La cara en `lanzador_tv/la_cara_web/` pide `/api/state` sola.

Teclas de la TV (Chrome kiosk):
- **F5**: vuelve a pedir `/api/state`. No recarga Chrome.
- **F9**: cicla `data-wall` (4h → 3h → 2h → ofertas).
- **F10**: cambia de monitor (cierra esa ventana y abre una).
- **F11**: apaga la TV. Esc en el panel de Admin no.

Qué no debe cambiar: `src/cajero`, `qt_dpi`, puerto 8765, una sola Chrome.
