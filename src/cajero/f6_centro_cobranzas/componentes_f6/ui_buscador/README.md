# Buscador de Clientes (Paso 1)

Qué hace: Contiene la interfaz visual para buscar un cliente por DNI o Nombre. Muestra una caja de texto grande y un menú desplegable de sugerencias.
Qué función: PanelBuscadorClientes en panel_buscador.py
Cómo funciona: El cajero escribe, la caja emite texto_cambiado. El panel F6 busca cuentas con `consulta.buscar_cuentas` y llama a mostrar_sugerencias. Clic o Enter elige un cliente existente. No hay alta de cliente.
Qué no debe cambiar una mejora futura: F6 no crea clientes. El alta vive en crédito del paso 6.
