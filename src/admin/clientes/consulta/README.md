# Consulta de historial (admin)

Ecosistema de la cartera. No usa el hilo de F6.

`hilo.py`, clase `HiloMovimientosAdmin`. Corre fuera de la interfaz. Pregunta a `src/clientes_fiado/oficina/consulta_historial`. Si el hilo falla, el diálogo muestra aviso y sigue: el ticket y borrar van por otros caminos.

El diálogo `dialogo_historial_cliente.py` pinta lo que llega. No llama `cerebro.movimientos` en el hilo de la ventana.
