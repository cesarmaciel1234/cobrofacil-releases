# Directo (kiosk)

Qué hace: el lanzador que usa Admin → Cartelería para la TV.

Qué función: `LanzadorDirectoTV` en `__init__.py`. Import público: `get_lanzador_directo()` desde `lanzador_directo.py`.

Cómo funciona: mezcla arranque, caché, motores, catálogo, paneles y estado. Orden: caché → HTTP :8765 → **una** Chrome → pulso en hilo. El Popen de Windows a veces se muere y deja la ventana: se mira el lock del perfil, no solo el PID.

Qué no debe cambiar: el singleton `_lanzador_directo` en `lanzador_directo.py` (la esclava lo patea al conectar).
