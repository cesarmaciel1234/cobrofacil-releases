# Dialogo editar cantidad

Piramide:

```
dialogo_editar_cantidad/
  __init__.py          exporta DialogoEditarCantidad
  dialogo.py           arma la ventana
  logica/              teclas y valor
  ui/                  estilos y widgets
```

- Enter confirma, Esc cancela.
- Rango 0.001–9999.999, 3 decimales (peso / unidades).
- Estilos propios en `ui/estilos.py` para que se vea en dia y noche (no depende de QSS blanco sobre blanco).
- Tamano: ~42% del terminal (minimo 820x480) para monitor grande.
