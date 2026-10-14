# Consulta historial (F6)

Ecosistema del cajero. No importa diálogos de admin.

`hilo.py`, clase `HiloMovimientosCajero`. Al elegir ficha, el panel pide las últimas líneas (cargos, abonos, BORRADO, CANCELADO). Pregunta al mismo transporte que admin: `oficina/consulta_historial`.

Si este hilo se rompe, F6 sigue cobrando. No crea clientes. No borra deuda: solo lee.
