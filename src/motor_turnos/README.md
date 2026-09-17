# Motor de Turnos (Shift Engine)

Este motor administra el ciclo de vida de los cajeros en el sistema.

## Reglas de Negocio
1. **Unicidad de Turno Diario**: Si un cajero inicia sesión varias veces en el mismo día sin haber hecho su "Cierre Z", no se crea un turno nuevo, el sistema reanuda el turno abierto.
2. **Rol "Jefe" o Administrador**: El Jefe no es un cajero. Cuando un admin se logea en una caja, genera una "Intervención de Supervisor". Los cobros realizados por el Jefe se auditan en una bolsa independiente para no cuadrar la caja del cajero.
3. **Corte Automático (00hs)**: Si un turno queda abierto a la medianoche, el sistema lo cierra automáticamente.
