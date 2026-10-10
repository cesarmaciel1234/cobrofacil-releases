# Plano: Centro de Cobranzas (F6) - Encarpetado Piramidal

## ¿Qué es esto?
Este es el "Centro de Cobranzas" o "F6", la pantalla a la que entra el cajero cuando el cliente viene a abonar (pagar) una deuda de fiado sin comprar productos nuevos.

## Arquitectura Piramidal (Frente y Fondo)

### Frente (UI Modular)
La interfaz visual se ha dividido en "lienzos" o componentes estáticos dentro de la carpeta `componentes_f6/` para no saturar el archivo principal (`panel.py`).
1. **`ui_buscador/`**: Contiene el buscador interactivo de clientes.
2. **`ui_estado/`**: Muestra la deuda actual del cliente, su nombre, y la caja para escribir el monto a abonar (o el botón para abrir el selector).
3. **`ui_selector/`**: Contiene los botones de los medios de pago digitales (Efectivo, Tarjeta, QR, Transferencia) y un `QStackedWidget` que embebe los lienzos interactivos nativos de cada medio (los mismos que usa Paso 6).

### Fondo (Motores Empresariales Globales)
A diferencia de versiones anteriores, F6 ya no tiene lógica dura embebida en su UI. `panel.py` actúa únicamente como orquestador y se conecta a los **Motores Empresariales** globales ubicados en `src/motores_empresariales/`:
1. **`MotorBusquedaClientes`**: Maneja la conexión a MariaDB/SQLite, busca el cliente, y emite `limite_aprobado` con los datos de deuda actualizados.
2. **`MotorCobranzaMedios`**: Recibe el intento de pago (Efectivo, QR, etc.). Tiene embebida la regla de autorización (el callback de PIN, por ejemplo, que levanta el `DialogoPIN` validado contra `CajeroActivo`). Si el PIN es correcto, este motor llama a `asentar()` en la base de datos y descuenta la deuda.

## Flujo de Datos (Cómo funciona)
1. El usuario abre F6. Aparece `PanelBuscadorClientes` (`ui_buscador`).
2. Al tipear y dar **Enter**, se emite `cliente_elegido`.
3. `panel.py` recibe el cliente y se lo pasa a `MotorBusquedaClientes.aprobar_credito()`.
4. El motor calcula y responde. La UI cambia al `PanelEstadoCredito` (`ui_estado`).
5. El cajero toca "Iniciar Pago". Se muestran los botones de medios (`ui_selector`).
6. El cajero selecciona (ej: Transferencia). Se abre el lienzo nativo de Transferencia.
7. Si el TPV no detecta nada, el cajero fuerza el cobro con **F9 MANUAL**.
8. El lienzo emite `listo`. `panel.py` se lo manda a `MotorCobranzaMedios.finalizar()`.
9. El motor global asienta el pago, descuenta el saldo en BD y emite éxito, cerrando el F6.
