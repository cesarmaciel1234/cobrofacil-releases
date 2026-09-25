# Hoja del mostrador

`hoja.py`, clase `HojaCuentaCobro`. Fiado y Cuenta corriente se piden en la hoja del cobro. El cartel no repite el monto de la venta y no trae Cancelar: Esc vuelve a los medios.

Fiado solo acepta números. El primer Enter, si el cupo alcanza, muestra arriba «Hola, …» con el nombre guardado, o «Sin datos» si admin todavía no cargó uno. Abajo quedan saldo y disponible, el campo se limpia y pide confirmar el DNI. El texto lo arma `MotorCartel`. Si un dato no carga, el otro sigue. El segundo Enter registra. Cuenta corriente, al escribir el nombre, abre el listado en el hueco de abajo: el nombre arriba y el DNI debajo. La fila marcada está en celeste. Las flechas la mueven. Enter toma esa fila. Si no hay nadie con ese nombre, crea el Express. Si el DNI ya está en un cliente del módulo, Fiado lo encuentra y no crea otro. Si el cupo no alcanza, suena la alarma y no pasa a confirmar. Si la repetición no coincide, suena el otro bip.

`fiado_express.py` y `cliente_express.py` quedan por el nombre viejo. El cobro ya no abre esas ventanas oscuras. El bip sigue en un hilo. La hoja no llama `entregar`. Al repetir bien, el paso 6 sigue con `finalizar` y el motor pide la orden ok.
