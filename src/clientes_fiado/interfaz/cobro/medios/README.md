# Medios del abono

Cobran un pago que no es venta. No importan el paso 6. El paso 6 no los importa.

`puerta.py`, `cobrar(medio, monto, partes)`, despacha. Las claves son Efectivo, Transferencia, Tarjeta, QR y Mixto.

Efectivo, transferencia, tarjeta y QR tienen `cobrar(monto)`. Mixto tiene `cobrar(monto, partes)`: admite solo dos de esos cuatro y la suma tiene que cubrir el abono. `hoja.py` pide esos dos importes. Devuelven `ResultadoMedio`: `ok`, `medio`, `entra_caja`, `detalle`, `monto_caja`. Si el monto no es mayor a cero, `ok` es falso. `monto_caja` es la parte en efectivo. Transferencia, tarjeta y QR dejan `monto_caja` en cero.

F6 no usa la ventanita de `medio.py` para cobrar. El clic está en `src/cajero/ingresar_efectivo/fiado/cobro/`: pide el PIN y llama a los motores del QR, de la tarjeta y de la transferencia. El QR se dibuja en esa hoja. `cerrar.py` `asentar` escribe la cuenta después. Si algo falla, devuelve aviso y no tira. El ingreso de caja lo hace la pantalla que cobró, solo por `monto_caja`. El paso 6 no importa esta carpeta. Si el abono falla, la venta del cajero sigue.

Tras un abono ok, `cerrar.avisar` publica el mismo mensajero que un cobro normal: `✅ COBRO EXITOSO — nombre · pago · saldo`. F6 refresca la franja; admin muestra ese texto y también refresca la terminal si está cargada.
