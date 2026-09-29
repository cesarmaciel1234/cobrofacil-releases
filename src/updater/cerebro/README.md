# Cerebro del actualizador

`engine.py` baja el ZIP del release y lo aplica. Al terminar, deja la `app_version` que vino dentro de ese ZIP.

No la reemplaza por la de GitHub. Si el número en el repositorio se adelanta al ejecutable, la caja no debe marcarse como actualizada con un programa viejo.

La caja solo descarga si el número remoto es mayor que el instalado, parte por parte (`v30.5` es mayor que `v4.0`). Un salto hacia atrás en el número no dispara la bajada.
