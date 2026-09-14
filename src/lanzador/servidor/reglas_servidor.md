# Lanzador — pirámide servidor

```
lanzador/servidor/
  pulso.py            al abrir el hub: despertar si es maestra
  barra/
    badge.py          ONLINE / ESCLAVA / OFFLINE
    interruptor.py    Win/Auto (respaldo corte / Linux)
```

El hub (`vistas/hub_main.py`) solo monta badge + interruptor. La lógica está acá.

**Esclava:** el hub no levanta MariaDB; los perfiles que abre leen `db_host`. Ver `src/base_de_datos/reglas.md`.
