# Buscador de Clientes (Paso 1)

Qué hace: Contiene la interfaz visual para buscar un cliente por DNI o Nombre. Muestra una caja de texto grande y un menú desplegable de sugerencias.
Qué función: PanelBuscadorClientes en panel_buscador.py
Cómo funciona: El cajero escribe, la caja emite 	exto_cambiado. El motor local escucha, busca en la BD y llama a mostrar_sugerencias(lista). Si el cajero hace clic en un resultado o da Enter, emite cliente_elegido.
Qué no debe cambiar una mejora futura: Debe mantenerse 100% visual (frontend). Las consultas a la base de datos se hacen desde el motor, no desde aquí.
