# 🎬 TRAS ESCENA TÉCNICO: ARQUITECTURA CajaFacil Pro

Este documento describe la ingeniería "bajo el capó" que hace posible la estabilidad y seguridad del sistema.

---

## 🏗️ 1. GESTIÓN DE PERFILES DINÁMICOS (`CajeroActivo`)
El sistema no usa variables estáticas simples. La clase `CajeroActivo` en `paso5_terminal.py` funciona como un despacho de hardware:
*   **Mecanismo**: Al seleccionar Perfil 1 o 2, la clase conmuta la clave de configuración (`ticket_printer` vs `ticket_printer_2`).
*   **Efecto**: Todas las llamadas a `printer_manager` consultan esta clase en tiempo real, redirigiendo los tickets y los pulsos de apertura al puerto físico correspondiente sin reiniciar la app.

## ⚖️ 2. INTELIGENCIA DE ESCANEO Y BALANZAS
El terminal procesa cada entrada del teclado a través de un motor de reglas:
*   **Multiplicadores**: Usa un `split('*')`. Si detecta el asterisco, separa la cantidad de la búsqueda.
*   **Balanza (EAN-13)**: Si el código empieza con `2`, se activa el parseador de balanza. Extrae los dígitos 7 al 12 como "Importe" y calcula el peso inversamente basado en el precio unitario de la base de datos.
*   **Artículo Común**: Detecta el prefijo `+` y cortocircuita la búsqueda en DB, inyectando un objeto `QTableWidgetItem` temporal.

## 💳 3. FLUJO DE COBRO INTELIGENTE Y MODIFICADORES
El módulo `paso6_cobro.py` implementa una máquina de estados para la velocidad:
*   **Enter Inteligente**: Detecta el método de pago activo. Si es digital (Tarjeta/Transf), autocompleta el monto y ejecuta `finalizar(imprimir=False)`.
*   **Efectivo (Seguridad Antierror)**: El campo "Pago Con" inicia VACÍO para obligar al ingreso manual y evitar errores de vuelto.
*   **Transición Auto-Mixto**: La función `_validar_pago` detecta si el monto ingresado es insuficiente. Si es así, conmuta automáticamente al método **Mixto**, calcula la diferencia y posiciona el foco en `txt_otro` para completar el pago.
*   **Modificadores (F3/F4)**: Utilizan el componente `DialogoMontoRápido`. Estos ajustan la variable `self.total_final` antes del guardado.
*   **Solo Registrar (F2)**: Permite omitir la llamada a `printer_manager.imprimir_ticket_venta`, reduciendo la latencia de cierre a milisegundos.

## 🔒 4. PROTOCOLO DE SEGURIDAD ESC/POS (EL SENSOR)
Esta es la joya de la corona de la versión 2026:
*   **Comando Binario**: Se envía `\x10\x04\x01` (DLE EOT 1) directamente al puerto RAW de la impresora.
*   **Análisis de Bit**: El hardware responde con un byte. El sistema realiza una operación `status_byte & 8`. Si el Bit 3 está activo, el sensor reporta "Cajón Abierto".
*   **Bucle de Bloqueo**: Se ejecuta un `while` con `QApplication.processEvents()`. Esto permite que la interfaz siga "viva" (parpadeando) pero impide que el usuario haga clic en cobrar o limpie la pantalla hasta que el sensor reporte el cierre.

## 🚒 5. INTERVENCIÓN Y BURBUJA "RELOAD"
*   **Salto Administrativo**: F11 activa un `QDialog` de login. Al ser exitoso, se marca la variable global `_apertura_autorizada = True` para que el monitor de seguridad ignore ese evento específico.
*   **Monitor de Sirena**: El botón flotante usa un `QTimer` de 400ms que alterna hojas de estilo CSS (`setStyleSheet`) con degradados variables para crear el efecto de luz de emergencia.
*   **Diseño Simplificado y Seguro**: Se eliminó el botón flotante secundario (dorado de cajón) y se centralizó el flujo en una única burbuja parpadeante. Al hacer clic, se realiza un retorno limpio al terminal con sincronización en vivo, manteniendo el cajón físicamente cerrado y seguro para evitar exposiciones no deseadas de dinero en efectivo.
*   **Sincronización al Volver**: Al hacer clic en la burbuja, se ejecuta `refresh_terminal_data()`. Este método itera sobre la tabla de ventas, vuelve a consultar la DB por cada ID de producto y refresca los precios y ofertas, asegurando que los cambios del supervisor se apliquen al instante.

## 🏁 6. CIERRE CIEGO Y REINICIO (EXIT 888)
*   **Arqueo Ciego**: El sistema oculta los resultados de la consulta SQL (`SUM(total)`) hasta que el cajero guarda su declaración física en la tabla `cierres_caja`.
*   **Restauración del Sistema**: El archivo `main.py` contiene un bucle `while True` que monitorea el `exit_code`. Cuando el Cierre Z envía un `sys.exit(888)`, el script padre detecta este código especial y reinicia la instancia de la aplicación, volviendo al Login de forma limpia y segura.

---
*Documentación Técnica Confidencial - PunPro Systems 2026*
