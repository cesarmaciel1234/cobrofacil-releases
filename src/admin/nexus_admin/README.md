# NEXUS GLOBAL DATABASE & CONTROL CENTER
## Arquitectura y Lógica Industrial

El módulo **Nexus Control Center** es una herramienta de supervisión global de alto nivel (High-Level Monitoring) diseñada para escenarios corporativos e industriales (ej. múltiples cajas, supervisores en oficinas, guardias de seguridad).

### 1. Rol y Función de NEXUS
- **Supervisión Pasiva / Activa:** Nexus permite a un supervisor o guardia monitorear en tiempo real (en vivo) el estado de 10 a 20+ terminales de cobro (cajas) sin necesidad de interactuar físicamente con ellas.
- **Topología de Red UDP:** Muestra qué nodos (PCs) están vivos y emitiendo latidos (Heartbeats) mediante la red LAN (UDP a través de 
etwork_engine.py).
- **Seguridad Perimetral:** Un guardia puede observar las ventas y el flujo de efectivo desde un cristal u oficina (junto a cámaras de seguridad) sin tener la capacidad de manipular los montos directamente.

### 2. Lógica Industrial de Cierre Z Remoto (Comando F4)
En entornos de alta seguridad empresarial, un supervisor no baja a la caja para realizar el arqueo ni ingresa los billetes al sistema. La responsabilidad del conteo físico recae en el cajero.
- **Acción:** El supervisor selecciona un nodo activo en Nexus y emite una orden de cierre (botón F4 / "ENVIAR ORDEN DE CIERRE").
- **Red:** Nexus emite un paquete UDP FORCE_Z_CUT dirigido a la IP de esa caja.
- **Ejecución Local:** La terminal del cajero intercepta la orden (en MainWindow._on_udp_message_received) e interrumpe al operador, forzando la apertura de la pestaña de **Control de Cierre (Arqueo)** en su pantalla. El cajero se ve obligado a realizar el corte Z en ese instante.

### 3. Sincronización de Métricas (Regla del Turno Activo)
**Regla de Oro de Nexus:** Las métricas centrales de "EFECTIVO ESPERADO" en Nexus *deben coincidir milimétricamente* con lo que la Caja Activa espera en su cajón físico en el instante actual.
- No se muestran los totales consolidados de "todo el día calendario" si han existido múltiples turnos previos.
- Nexus consulta exclusivamente a MotorCierre.obtener_datos_cierre_diario() para asegurar que se están midiendo los fondos desde la *última Apertura de Caja* (el turno en curso).

### 4. Directrices para futuras IAs y Desarrolladores
- **Cero Manipulación Local desde Nexus:** Si agregas funciones de cierre o arqueo a Nexus, **NUNCA** abras ventanas locales que alteren la caja de otro usuario. Usa siempre eventos distribuidos por UDP (engine.broadcast()).
- **Permisos de Guardia:** Los roles orientados a vigilancia no deben tener acceso a la base de datos histórica ni manipular métricas; la interfaz debe enfocarse en *Live Feeds* (Tarjetas de Métricas, Logs de Actividad, Status Online/Offline).
