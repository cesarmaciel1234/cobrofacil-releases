# Plano — ventanas sueltas de admin

La rama arranca acá. Un solo proceso `--role admin`. Hasta tres módulos en otros monitores.

```
admin/ventanas_sueltas/
  plano.md
  gestor.py     puede / título / monitor / marcador
  hoja.py       QMainWindow del módulo desanclado
```

## Frente

En el hub: clic abre el módulo en esta ventana. El **+** de la tile (también Ctrl+clic o clic derecho) lo manda a otro monitor. Cerrar la hoja o «Traer al hub» lo devuelve. El lanzador, si Admin ya corre, **trae esa instancia**; no abre otro proceso.

## Fondo

`MainWindow._desanclar_modulo` saca el widget del `QStackedWidget` (queda oculto) y `HojaSuelta` lo vuelve a mostrar. Mismo PID, mismo candado `perfil_admin.lock`. No hay `QProcess`. Cajero (1) y la TV (21) no se desanclan. Auditoría (25) sí se puede desanclar.

## Qué no cambiar

- No un segundo `--role admin`.
- No matar el candado para “abrir otro”.
- No desanclar el terminal de ventas.
