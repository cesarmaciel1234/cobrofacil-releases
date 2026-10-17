# Configuración (Admin)

Qué hace: Admin → Cartelería → Configuración. Datos del negocio, 5 temas, zócalo.

Qué función: `CarteleriaConfigPanel` en `panel.py`. Entrada pública `Admin15Carteleria` en `pantalla.py`. Temas en `temas.py`. MariaDB en `motor/`.

Cómo funciona: abre con `config.json` (no espera red). Un hilo pide `carteleria_config`. Guardar pisa memoria TV y disco al toque; REPLACE de MariaDB corre en `HiloGuardar`. El botón dice Guardando; no hay `QMessageBox` de éxito que congele. Elegir un renglón de la lista no guarda.

Qué no debe cambiar: no SELECT/REPLACE ni `gethostbyname` en el hilo de la UI. `admin15_carteleria.py` solo reexporta para `main_window`.
