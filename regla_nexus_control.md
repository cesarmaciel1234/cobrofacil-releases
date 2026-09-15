# REGLA: ARQUITECTURA NEXUS CONTROL CENTER

## 1. Patrón Piramidal
El módulo Nexus Control Center (para Jefe y Admin) debe seguir una arquitectura piramidal estricta de 3 capas separadas en carpetas, conectadas al Motor Globalizado:

\\\
src/admin/nexus_admin/
+-- nexus_admin_main.py            (Punta de la pirámide: Entry point y unión MVC)
+-- logica/
¦   +-- nexus_controller.py        (Capa de Negocio: UDP, Sincronización, Timers)
+-- vistas/
    +-- nexus_main_view.py         (Capa Visual: Layout principal, Dark/Light Mode)
    +-- componentes/
        +-- nexus_panel_izq.py     (CyberRadar y Terminal SYS.OP)
        +-- nexus_panel_cen.py     (Matriz de Tráfico y Botón F12 Cierre Ejecutivo)
        +-- nexus_panel_der.py     (Bitácora de Eventos y Auditoría)

src/cerebro_global/
+-- nexus_cerebro.py               (Base de la pirámide: Motor SQL puro, sin UI)
\\\

## 2. Prohibido Código SQL en la Interfaz
Queda estrictamente prohibido usar \db_manager.execute_...\ dentro de las vistas (\
exus_panel_*\) o el controlador. Todas las métricas, ventas en vivo y eventos de seguridad deben ser solicitados al Motor Globalizado (\CerebroNexus\).

## 3. UI Ejecutiva y Tema Dinámico
Nexus no es un módulo estándar, es una herramienta ejecutiva premium.
- Todo componente visual debe tener un método \update_theme(theme)\.
- El controlador debe inyectar la señal \	heme_manager.theme_changed\ a todas las vistas hijas para adaptar la UI dinámicamente sin reiniciar (Modo Día / Modo Noche).
- El botón de Cierre Z (F12) **SIEMPRE** debe abrir el módulo global \CierrePremiumUI\, nunca intentar cerrar turnos de forma independiente.
