# Cartel

Llena el hueco de la confirmación. No cobra y no autoriza.

`motor.py`, clase `MotorCartel`, método `armar`. Junta dos submotores y siempre devuelve un diccionario.

`nombre.py`, `SubmotorNombre.leer`. Si el nombre guardado es de una persona, devuelve «Hola, …» con nombre y apellido. El apellido, si la ficha no lo tiene, se salta. Si admin todavía no cargó un nombre, o el nombre es `Express` más el DNI, devuelve `Sin datos`. Si la lectura falla, también `Sin datos`.

`saldos.py`, `SubmotorSaldos.leer`. Devuelve la deuda y el disponible. Si un número no carga, ese lado vuelve `None` y el otro sigue.

`armar` intenta releer la ficha por id. Si esa lectura falla, usa la ficha que ya tenía el cobro.
