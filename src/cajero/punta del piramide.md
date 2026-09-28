# Punta del Pirámide - Actualización de Cobro y Cierre

**Componentes Modificados:** paso6_cobro.py, pantalla_mp.py, point_service.py, cierre.py.

## Cambios Implementados (Producción Masiva)

1. **Pantalla MP (Aprobado/Rechazado) Blindada:**
   - Se instanció correctamente PantallaMP desde el inicio para evitar crasheos silenciosos (AttributeError).
   - Se aplicó aislamiento estricto (	ry...except) alrededor de las llamadas a mostrar_aprobado y mostrar_rechazado. Si la interfaz visual falla, el sistema ignora el error y llama a self.accept() o super().reject(), asegurando que la transacción comercial en la base de datos nunca se congele.

2. **Diferenciación de Cobro Autónomo vs Manual:**
   - Se agregó la variable de estado _es_autonomo.
   - Cuando el cobro se finaliza de forma automática (Point Service o Polling/Webhook de MP), se pinta la pantalla verde con la leyenda "Cobro Autónomo".
   - Cuando el cajero fuerza el cobro manual (Efectivo, o saltando validación con TPV apagado/rojo), la pantalla verde se pinta pero **se oculta** el texto "Cobro Autónomo".

3. **Prevención de Ventas Fantasma (Bug Crítico Solucionado):**
   - En _cerrar_como_eligio(), si PointService.procesar_pago_mercadopago_point() devuelve False (porque el cliente canceló en el dispositivo o hubo error de red), el sistema ahora ejecuta un pass. Antes llamaba erróneamente a inalizar(False), lo que desencadenaba el guardado de la venta en base de datos.
   - El cajero ahora puede reintentar el cobro libremente sin corromper la base de datos.

4. **Experiencia de Cancelación Mejorada:**
   - La tecla ESC y el botón táctil Salir ahora están sincronizados. Si el usuario está en un medio de pago, retroceden a la botonera principal.
   - Al abortar totalmente la venta desde Paso6Cobro (usando "Salir" desde el menú principal), se intercepta el cierre y se pinta una pantalla gigante roja ("⛔ Cobro Cancelado" / "Venta Abortada") por 2 segundos antes de volver al ticket. Esto brinda claridad absoluta al cajero.

5. **Backup en Cierre Z (Offline-safe):**
   - Se enganchó una rutina de compresión (comprimir_backups_del_dia()) en cerrar_caja() cuando 	ipo_cierre es CIERRE_Z.
   - Opera en un 	hreading.Thread secundario para no congelar la pantalla.
   - Cuenta con tolerancias para archivos bloqueados (lock de SQLite), priorizando que el cajero finalice su turno al instante.

- Se optimizo la resiliencia en Modo Esclava: la busqueda de la Maestra por red y la impresion de tickets ahora corren en hilos asincronos. Esto elimina los bloqueos de 2 a 5 segundos en la pantalla del cajero (Cobro y escaneo) cuando la conexion Wi-Fi o LAN a la Maestra se corta.
- Se soluciono el error (AttributeError: get) de la tabla de Historial de Caja (F3) cuando el nodo esta offline en SQLite.
- Se distribuyo proporcionalmente el ancho de las 5 columnas del Historial de Caja (Folio, Arts, Hora, Total, Redondeo) para ocupar mejor las pantallas grandes.

- [Bugfix] Corrupcion de Token MP: Se arreglo el fallo donde el cajero guardaba un token valido y funcionaba, pero al rato fallaba (Error 403). La sincronizacion automatica entre Maestra y Esclava (tienda.py) estaba leyendo mal el objeto SQLite y pisaba el token bueno con el texto de memoria <sqlite3.Row object...>. Ya quedo documentado y parchado.

- [Mejora] Interfaz Terminal (Paso 5): Se remarcaron los bordes de los contenedores principales (Panel de Totales, Tabla, Barra Inferior) a 2px solid #94A3B8 para mayor definicion visual estructural, sobreescribiendo el estilo difuminado global.
- [Blindaje] Cobro Autonomo (Paso 6): Se envolvio la impresion de tickets en try-catch y se movio el envio a la terminal Point a un hilo secundario asincrono (QEventLoop). Esto evita que el cajero se congele ante timeouts de internet de hasta 10 segundos, asegurando fluidez e interrupcion manual segura via F9.

- [Mejora] Historial de Caja (Paso 8): Se agrego la columna 'Cliente' en la tabla principal de tickets (UI: lista_tickets.py) y se modifico el controlador SQL (logica: historial_controller.py) para extraer el campo literal cliente_nombre. Esto permite visibilidad instantanea de las cuentas corrientes sin seleccionar el ticket.
