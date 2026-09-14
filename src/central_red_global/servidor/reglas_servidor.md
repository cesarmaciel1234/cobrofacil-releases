# Pirámide del servidor de tienda

```
servidor/
  comando.py          cómo se lanza --server
  puerto.py           3306
  arranque/
    proceso.py        el lanzador despierta el proceso
    servicios.py      MariaDB + LAN + presencia
    bandeja.py        ventana (primera captura)
    headless.py       Linux sin pantalla
  autostart/
    os_boot.py        interruptor Win/Auto
    windows.py
    linux.py
  rol/
    motor.py          fachada MotorRed
    maestra.py        Convertir en MAESTRA
    esclava.py        Convertir en ESCLAVA (apaga MariaDB)
    apagar.py
```

Compat: `store_server.py` y `motor_red.py` solo reexportan.

El puesto vive en `config.json`. Maestra: despierta servidor. Esclava: no.

Cualquier perfil en PC esclava lee y graba en la maestra. SQLite local solo si `3306` no responde; al volver la tienda, se reengancha. Ver `src/base_de_datos/reglas.md`.
