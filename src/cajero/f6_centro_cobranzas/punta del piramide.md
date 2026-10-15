# Punta — F6 centro de cobranzas

Paso 5, tecla **F6**. Cobranza pura: sin carrito, sin venta. El cajero la aprieta y cobra al cliente. No es F2. No es F5. No es **CRÉDITO**. El botón **COBRANZA** del paso 6 usa el mismo motor, pero ahí el cliente está comprando.

Tabla: `src/cajero/README.md` y `paso6_cobro/decisiones.md`.

```
f6_centro_cobranzas/
  punta del piramide.md
  dialogo.py                 DialogoCentroCobranzas
  panel.py                   buscador → ficha → medios
  consulta.py                buscar_cuentas
  consulta_historial/        hilo de lectura
  paleta.py
  componentes_f6/
    ui_buscador/
    ui_estado/
    ui_selector/
```

## Frente

Buscador por DNI o nombre (tope 5). Ficha: hola, deuda o a favor, o al día. PAGAR / ABONAR aunque no haya deuda: el excedente queda a favor, sin cartel. Paso 1 monto a la cuenta. Paso 2 medio. Efectivo pregunta los billetes; si falta no cobra.

Admin Abonar abre el mismo diálogo con `perfil=Admin`, va directo al monto y al medio, PIN apagado. El cobro se asienta una sola vez.

No pinta alta de cliente. Las flechas no saltan a F2.

## Fondo

1. `consulta.buscar_cuentas` — tabla `clientes`. No crea filas.
2. Hilo `consulta_historial/hilo.py` pregunta a `src/clientes_fiado/oficina/consulta_historial`. Si se cae, PAGAR sigue.
3. QR / tarjeta / transferencia: el lienzo espera el importe y, si llega, llama `finalizar` solo. **F9** asocia (otro monto) o cierra a mano. **Enter no asocia**: espera el exacto.
4. Mixto: solo dos medios. Point / tarjeta primero, después transferencia, después QR. Esc vacía el lienzo. Recién después `MotorCobranzaMedios.finalizar` → `asentar` una vez (`COB-{id}`). No es el mixto del paso 6 (ahí puede ir un resto a cliente).
5. Admin Abonar abre esta misma hoja (`perfil=Admin`). No vuelve a asentar.

Qué no romper: paso 6, F2, F5. No unir F6 con el cobro de la venta ni con el botón COBRANZA del paso 6.
