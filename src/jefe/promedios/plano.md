# Plano de Módulo Promedios

**Frente:** El usuario entra desde el Dashboard del Jefe a Costos y Promedios. Hay pestañas independientes para Carne (con submódulos Mocho, Pecho, Media Res), Cerdo y Pollo.
**Fondo:** Cada categoría tiene su propia carpeta, su propio archivo de Interfaz de Usuario (UI) y su propio Motor Lógico. Esto permite que el pollo pueda tener lógicas de despiece totalmente diferentes al cerdo o la carne sin causar conflictos en el código.

Al guardar un promedio, `motor_global_promedios._publicar_orden` deja los kilos, la merma, el costo y el código de cada corte en `formula_orden`. La última columna de Carne, Cerdo y Pollo es ese código. Las doce columnas de la cuenta no se mueven. La fórmula acepta esa receta y no arma otra. Un enlace de oferta resta el producto de ese código. El cajero no lee esa tabla: vende el producto.

Carne, Cerdo y Pollo cargan el bulto con el mismo método. El precio del bulto se divide por los kilos que quedan, sin la merma. El enlace copia el stock y el costo del original y no suma plata. La nota de cada uno está en su carpeta: `carne/README.md`, `cerdo/README.md`, `pollo/README.md`. La recepción que lo aplica está en `src/proveedor_global/frontend/formula/README.md`. Huevo no usa esa cuenta.

En Cerdo, Alta corte, Baja corte y Guardar nueva fórmula dejan el producto, el peso de cada corte y los kilos del bulto. Esa receta alimenta el precio. La nota está en `cerdo/README.md`.

La fórmula de stock vive en `formula/`. Huevo, en Costos y Promedios, calcula cada fórmula por separado: vender un cajón por esa fórmula, y por mayor si tiene precio. Una fila nueva entra sola. No se suman. Se arma en esta pantalla, por producto o por departamento. La fracción no lee su stock: el intermediario aplica la fórmula y dice los kilos o las cajas que quedan del base. Al vender, descuenta esa parte. El pedido de faltantes usa el stock del base. `guardar` reemplaza la fórmula en un solo cierre, para que una venta no la encuentre vacía. El envío del stock al inventario lo hace `src/proveedor_global/frontend/formula/motores/inventario.py`.
