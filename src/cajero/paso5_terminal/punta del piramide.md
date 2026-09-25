# Punta de la pirámide — terminal

La pantalla de venta. Esta carpeta la abre. El cobro está en `paso6_cobro`.

```
paso5_terminal/
  punta del piramide.md
  paso5_terminal.py        junta la pantalla
  componentes_paso5_terminal/
    cabecera_superior/     Estado, Caja, título y fecha
    centro_de_notificaciones/
    componente_tabla_de_productos/   ticket y marco naranja
    panel_de_totales/      buscador, total y resumen
    barra_de_herramientas_inferior/
    apariencia/            azul Francia, rosa y el marco del cobro
```

F10 sale de pantalla completa. El candado se aprieta con el botón.

## Fondo

`paso5_terminal.py`, clase `Paso5Terminal`. Termina en la línea 2427. Tiene 81 métodos. La lógica de carrito, stock, caja y cierre remoto está en `logica/terminal_controller.py`, no en un `state_manager.py`.

`_precalentar_cobro` importa el cobro después de pintar. `parse_float_safe` vive una sola vez en este archivo.

## Qué no cambiar

No partir la clase. No subir los imports internos al tope. No crear `plano.md` al lado de esta punta.

`hideEvent` está definido dos veces. Corre el que esconde el teclado virtual. El datagrama `HIDE` al puerto 45680 no corre, y en el repo nadie lo escucha. No juntes los dos métodos. No borres el del teclado.

`seleccionar_item_busqueda` deja la cantidad en `1.0` si el multiplicador no es un número. `_evaluar_combos` salta un combo roto y sigue la venta. El bip usa `AUDIO_ENABLED` y un hilo con `winsound`. El `if __name__ == "__main__":` del final ya cubre el arranque manual. No se borra ni se vuelve a envolver.

## Producción

Los relojes están en `Paso5Terminal.__init__`: reloj 1 s, búsqueda de un solo tiro, foco del escáner 150 ms, stock 5 min si `stock_alerta_activa`, autocierre 1 min si `cierre_auto_activo`. Si el cajero toca el ticket, la lista o el asistente, el cursor vuelve al buscador a los 2 s. Si deja de escribir en el asistente, también. Un escaneo cierra el asistente y la lista, y carga el producto. F12 hace lo mismo antes de abrir el cobro. El cobro no se toca: es el paso 6.

F7 es `_leer_bascula`. El puerto se lee fuera de la pantalla. Si no lee, deja `0.750*` o `1.250*` en el escáner. El puerto se cierra en el hilo de la lectura. `focusChanged` se engancha una sola vez.

El candado, el retiro, el ingreso, el historial y el cierre no desenfocan la venta. La pantalla queda plana.

El teclado en pantalla no se abre al escribir ni cuando el escáner toma el foco. Se abre si la pantalla es táctil y el cuadro se tocó (`MouseFocusReason`). `teclado_virtual_modo` en `nunca` lo apaga. El botón TECLADO lo abre a mano.

Un código numérico no busca por nombre hasta Enter. `obtener_combos` se recuerda 15 s. Un combo aplicado manda UDP al puerto 37021 y cierra ese socket. El detalle de la caja está en `src/cajero/README.md`, sección Producción.

El total que pasa al cobro lo calcula `finalizar_venta`: suma la columna de subtotales con `parse_float_safe` y la cierra `redondear_dinero`. No usa el texto del total grande. `redondear_items_carrito` deja precio y subtotal en dos centavos. `actualizar_totales` usa la misma suma para lo que se ve en la venta. `fmt_moneda_sin_centavos` pinta con dos decimales y separador argentino. El nombre viejo se queda. El redondeo de la venta está en `paso6_cobro/punta del piramide.md`, sección Redondeo.
