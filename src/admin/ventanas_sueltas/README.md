# Ventanas sueltas (admin)

Qué hace: saca un módulo del hub a otra pantalla **sin otro proceso**.

Qué función: `se_puede`, `titulo`, `poner_en_otro_monitor`, `marcador`. `HojaSuelta` es la ventana.

Cómo funciona: el **+** de la tile saca el widget; solo cambia de padre. El stacked lo deja oculto: la hoja lo muestra. Máximo tres. Cerrar la hoja lo reinserta en el stack. El clic en el lanzador enfoca el PID que ya tiene el candado.
