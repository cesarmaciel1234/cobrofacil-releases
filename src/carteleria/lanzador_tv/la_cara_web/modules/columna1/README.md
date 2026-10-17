# Columna 1 ranking

Qué hace: cuatro tarjetas con foto. Rota el panel cada 8 s sin vaciar la lista.

Qué función: `iniciarRotacionColumna1`, `ponerFoto`.

Cómo funciona: si la estructura es la misma, solo cambia nombre y PNG. `ponerFoto` precarga y recién ahí pone `src`. `revelarFoto` marca `.is-ready`.

Qué devuelve cuando falla: texto “Sin ventas todavía.”

Qué no debe cambiar: no borrar el DOM en cada giro. Foto vía `foto_tarjeta/`.
