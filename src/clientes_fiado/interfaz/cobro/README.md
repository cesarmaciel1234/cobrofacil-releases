# Hoja del mostrador

`hoja.py`, clase `HojaCuentaCobro`. Fiado y Cuenta corriente se piden en la hoja del cobro. El cartel no repite el monto de la venta y no trae Cancelar: Esc vuelve a los medios.

Fiado solo acepta números. El primer Enter, si el cupo alcanza, muestra arriba «Hola, …» con el nombre guardado, o «Sin datos» si admin todavía no cargó uno. Abajo quedan saldo y disponible, el campo se limpia y pide confirmar el DNI. El texto lo arma `MotorCartel`. Si un dato no carga, el otro sigue. El segundo Enter registra. Cuenta corriente, al escribir el nombre, abre el listado en el hueco de abajo: el nombre arriba y el DNI debajo. La fila marcada está en celeste. Las flechas la mueven. Enter toma esa fila. Si no hay nadie con ese nombre, crea el Express. Si el DNI ya está en un cliente del módulo, Fiado lo encuentra y no crea otro. Fiado y Cuenta corriente usan el mismo cupo. Si no alcanza, el aviso queda en tres líneas: límite superado en rojo, el crédito en verde y el exceso en rojo. Suena la alarma y el cartel del cobro pide el PIN de 4 dígitos de un admin. Elegir el nombre con un clic pide el mismo PIN. `pin_admin.py`, `quien_autoriza`, lo comprueba. Si coincide, pasa a confirmar y el cargo queda como excepción. Si no, el cartel sigue y la venta no se carga. Esc en ese momento cierra el PIN y deja el DNI. Si la repetición no coincide, suena el otro bip.

Desde Mixto, la misma hoja se abre por el resto, después de que el otro medio ya entró. El cupo se mira contra ese resto.

`medio.py`, `pedir_medio`, queda por el nombre. F6 ya no lo abre. El clic está en `src/cajero/ingresar_efectivo/fiado/cobro/`: pide el PIN y llama a los motores. El QR se dibuja en esa hoja. Mixto reparte el abono en dos medios y, si uno es QR, tarjeta o transferencia, corre ese motor. `medios/cerrar.py` `asentar` escribe la cuenta. Si algo falla, avisa y no tira. La venta del cajero sigue. El paso 6 no importa esta carpeta.

`fiado_express.py` y `cliente_express.py` quedan por el nombre viejo. El cobro ya no abre esas ventanas oscuras. El bip sigue en un hilo. La hoja no llama `entregar`. Al repetir bien, el paso 6 sigue con `finalizar` y el motor pide la orden ok.
