# Lanzador — pirámide servidor

```
lanzador/servidor/
  pulso.py            asegura autoarranque Windows, backoff exponencial y revive `--server --background`
  barra/
    badge.py          ONLINE / ESCLAVA / OFFLINE. Arranque asíncrono al clic o trae ventana al frente.
    interruptor.py    Win/Auto (Startup .lnk + Tarea Programada)
```

El hub (`vistas/hub_main.py`) monta badge + interruptor y dispara el watchdog (`_timer_servidor`) cada 10s en segundo plano.

- **Autoarranque en segundo plano:** `auto_start_store_server` permanece en `true` tanto en maestra como en esclava (no lo desactiva `auto_heal`). `windows.py` valida el destino real del `.lnk` y registra la tarea programada `CobroFacil_ServidorTienda` con reinicio ante fallo.
- **Watchdog asíncrono + Backoff:** `pulso.asegurar_servidor()` usa lock anti-reentrancia y backoff exponencial (10 s → 20 s → 40 s → 60 s) ante fallos seguidos de arranque, evitando congelar el Lanzador o spawnear en crash-loop.

**Esclava:** el hub no levanta MariaDB; el proceso `--server --background` mantiene el espejo vivo en segundo plano y los perfiles leen `db_host`.
