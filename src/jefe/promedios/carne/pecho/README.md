# Módulo carne/pecho
Contiene la vista y el motor matemático exclusivo para carne/pecho.
Al cargar la interfaz, solo se precargan los cortes y kilos por defecto. El resto de la tabla se inicializa en 0 o vacío para evitar cálculos fantasma.
Al editar cualquier celda de la tabla, su motor interno recalcula las 12 columnas en orden:
Corte | Kilos | Costo$/kg | Precio Venta | % Ganancia | P. Mayoreo | Desde kg | % Mayoreo | V. Total | V. Mayoreo | Ganancia | G. Mayoreo
