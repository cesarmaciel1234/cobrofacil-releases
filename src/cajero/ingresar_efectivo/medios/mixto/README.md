# Lienzo de Pago Mixto

## Qué hace
Permite distribuir el cobro de una transacción entre múltiples medios: Efectivo, Tarjeta, Transferencia y QR.

## Funciones principales
- `arrancar(monto)`: Carga el total a liquidar y enfoca el campo de efectivo con selección lista.
- `_on_enter_campo(campo)`: Agiliza la carga con teclado: si el total está cubierto, confirma de inmediato; si falta cubrir, precompleta el siguiente campo con el saldo restante y le da foco.
- `_validar_cobertura()`: Verifica en tiempo real que la suma de los 4 medios iguale el total, habilitando el botón de confirmación en verde o mostrando la diferencia faltante en rojo.
- `tecla(k)`: Atiende `ENTER` para confirmar o `ESC` para volver al selector de medios.

## Cómo funciona
Devuelve un diccionario estructurado `{"Efectivo": e, "Tarjeta": t, "Transferencia": tr, "QR": q}` a través de la señal `listo`. El orquestador que lo invoque (por ejemplo, `PuenteF5Cobranza`) coordina la ejecución de los medios digitales en primer lugar y el asentamiento del efectivo y apertura del cajón al final.
