# Carga

## Qué hace la carpeta
Entra la mercadería del proveedor. Hay dos formas, separadas.

## Qué función, con el nombre real
* `PanelRecepcionRapida` (`recepcion.py`): escáner. Elige una ficha ya cargada y pasa los productos. No crea proveedor.
* `LineaBulto`: una línea bajo el escáner. Al elegir, limpia el remito y carga solo esa receta. Huevo manda el precio del cajón y parte maples; ese camino no se toca. En pollo, carne, cerdo y congelado la cantidad de cada corte es kilos por cajón × cajones. El costo por kilo es el precio del cajón dividido por los kilos que siguen en el remito. Borrar menudos o carcasa suma esa merma y sube el costo. El total sigue siendo cajones × precio. Al confirmar, el inventario recibe el stock antes que el libro de la fórmula. La pantalla no habla con la maestra: un hilo le pide al servidor que nutra, sin bajar el catálogo entero. El enlace y Pollo entero salen en el remito en gris: copian stock y costo, y no suman al total. La fórmula solo cuenta los cortes reales.
* La carga por peso (cajas × kilos × precio) sigue en `VistaProveedor`, pestaña interna de esa tarjeta. Sirve para media res, queso o cualquier mercadería.

## Cómo funciona, en el orden en que corre
1. La tarjeta Cargar pedido muestra dos subtarjetas: escáner y carga por peso. Ninguna muestra el histórico; ese alto lo usa la tabla de ítems.
2. El escáner confirma y emite `compra_guardada`.
3. La carga por peso arma cada línea como cajas × kilos × precio y llama a `MotorProveedor.save_proveedor`.
4. Sin tienda, esa compra queda en esta PC.

## Qué devuelve cuando falla
El escáner avisa y no deja el remito a medias. La carga por peso muestra el error y no vacía la grilla si no se guardó.

## Qué no debe cambiar una mejora futura
En el escáner no vuelve el botón de alta. El proveedor se elige de las fichas existentes.
