# Auditoría digital

Rama independiente. La nota de frente y fondo es `plano.md`.

Cada corte: `consultas/`, `libro_tickets/`, `libro_cobranzas/`, `libro_f9/`, `cruces/` con su `README.md`.

Pantalla: `admin/mercadopago/mercadopago_main.py`. Filtros: cruzados, ticket sin id de pago, id de pago sin ticket, y la cuenta del token activo en ese momento. `empleado.pedir` no arma en la ventana; `snapshot` sí arma si quien llama no es la pantalla. No cobra.
