# Cartelería (Digital Signage)


### Optimizaciones de Carga (Skeleton Loader)
- En lanzador_tv/la_cara_web/index.html se agregaron contenedores Skeleton (marcadores visuales en CSS) a cada panel principal. 
- Evita el efecto de "pantalla blanca" en ejecutables congelados. Al recibir datos por JS, .innerHTML sobrescribe los skeletons limpiamente.

### Mapeo de Teclas TV (pp.js & TeclasTv)
- **F5**: Forzar location.reload() (Refresh visual total).
- **F9**: Conmutador local de Vistas/Grilla (cicla el layout CSS data-wall de 4h a 1h, 2h, 3h mostrando dinámicamente de 1 a 4 paneles centrales y ocultando el resto, manteniendo zócalo y carrusel intactos).
- **F10**: Interruptor de Mover Monitor (API /api/control?action=monitor en JS, o Selector en Kiosk Python).
- **F11 / Esc**: Detener servidor TV y regresar al Dashboard de Cartelería.
