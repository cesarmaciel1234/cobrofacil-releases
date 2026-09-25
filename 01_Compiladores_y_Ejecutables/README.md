# Empaquetado del ejecutable

El release de GitHub (`.github/workflows/release.yml`) instala `requirements.txt` y después corre `empaquetar_pos.py`. Ese archivo es el que arma `CobroFacil_POS.exe`.

Si una pantalla nueva necesita una librería:

1. Agregarla en `requirements.txt` (y en `requirements-pyqt6.txt`).
2. Si trae archivos aparte (fuentes, plugins), sumar `--collect-all` en `empaquetar_pos.py`.
3. El próximo push a `main` la instala y la mete en el ejecutable.

Sin ese paso el cliente abre el módulo y el programa se cierra. Pasó con las etiquetas de góndola: faltaban `reportlab`, `barcode` y el plugin de impresión.

`empaquetar_pos.py` corta la compilación si falta `reportlab`, `barcode`, `qrcode`, `sqlalchemy` o `bcrypt`.
