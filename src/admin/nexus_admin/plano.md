# Plano — Nexus

Esta carpeta arranca el frente. El fondo SQL está en `src/cerebro_global/nexus_cerebro.py`.

## Frente

`nexus_admin_main.py` junta la pantalla. No escribe SQL.

`logica/nexus_controller.py` lleva UDP, sincronización y timers. Inyecta `theme_manager.theme_changed` en las vistas. Cada vista tiene `update_theme`.

`vistas/nexus_main_view.py` arma el layout de día y de noche.

`vistas/componentes/panel_izquierdo/` es el radar y la terminal. `panel_central/` es la matriz de tráfico y el cierre. `panel_derecho/` es la bitácora.

El cierre Z no se hace adentro de Nexus. El botón abre el cierre global. Una orden a otra caja sale por UDP. La caja la recibe y abre su propio arqueo. Nexus no abre una ventana local que cambie la caja de otro.

## Fondo

Las métricas, las ventas en vivo y los eventos se piden al cerebro. Prohibido `db_manager.execute_...` en las vistas y en el controlador.

El efectivo esperado de Nexus es el del turno abierto, el mismo que la caja espera en el cajón. No es la suma de todo el día si ya hubo otros turnos.

## Qué no cambiar

No cerrar el turno desde un botón propio de Nexus. No dar a un perfil de guardia la base histórica para que la modifique.
