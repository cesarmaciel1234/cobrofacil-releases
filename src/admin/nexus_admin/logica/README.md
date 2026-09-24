# Lógica de Nexus

No pinta y no ejecuta SQL. Recibe la vista en el constructor y le habla por métodos.

`_get_initial_max_id` toma el último id conocido para no repetir eventos viejos al abrir.

`_connect_signals` une los paneles con este controlador. `_start_timers` prende el refresco y el destello.

`_connect_to_network` se engancha al motor UDP. `_on_udp_heartbeat` anota la hora del nodo en `active_terminals`, lo escribe en el log del panel izquierdo y lo registra en el panel central.

`_on_udp_message` marca el nodo activo. Si el tipo es `VENTA_NUEVA` y el método contiene EFECTIVO, guarda la hora en `last_cash_sales` para ese origen, registra el evento y sincroniza. Si el dato trae `fuera_de_maestra` y `request_id`, el monto queda en `_ventas_sin_maestra` y se suma a las métricas del turno hasta que ese id está en la maestra. La pantalla no vuelve a anunciar ese ticket cuando la cola sube. Si es `HARDWARE_SENSOR` con `evento` DRAWER_OPEN, llama `_evaluate_smart_drawer`. Si es `CIERRE_TURNO`, registra el cierre y sincroniza. Si es `ALERTA_SEGURIDAD`, registra el mensaje y, si dice CRITICO, arranca el destello.

`_evaluate_smart_drawer` lee el rol que viene después de `|` en el origen. Si no viene, asume CAJERO. Admin o jefe se anotan como INTERVENCION, texto de prueba, sin alerta crítica. Si no, mira cuántos segundos pasaron desde la última venta en efectivo de ese origen. Hasta 7 segundos se anota como apertura justificada. Después de eso registra `[CRITICO] CAJON FISICO ABIERTO SIN VENTA` y prende el destello.

`_on_connection_lost` marca el nodo inactivo y registra la pérdida. `_on_caja_selected` guarda `current_caja_filter`, se lo pasa a `panel_der.set_caja_filter` y sincroniza. Un clic repetido en el mismo filtro no vuelve a loguear.

`_force_z_close_from_panel` no abre el arqueo en esta PC. Pide el motor de red y manda la orden a la caja elegida, o a todas si el filtro es «todas».

`_sync_live_data` pide las métricas del turno al cerebro y las empuja a los paneles. `_registrar_evento_caja` escribe la bitácora. `_inyectar_ruido_red` es el efecto visual de la red, no un paquete real.

`_do_glitch_flash` corre el destello cuando hay una alerta crítica.
