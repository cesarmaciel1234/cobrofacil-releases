# Subcarpeta WSFE (Facturación Electrónica WSFEv1)

## Qué hace la carpeta
Interactúa con el Web Service de Facturación Electrónica versión 1 (WSFEv1) de AFIP/ARCA. Permite consultar la correlatividad de comprobantes del punto de venta y solicitar la autorización fiscal (CAE) con desglose multi-alícuota de IVA.

## Qué función, con el nombre real
* `map_tasa_iva_id(tasa)`: Convierte el porcentaje de IVA (21, 10.5, etc.) al ID reglamentario de AFIP (5, 4, etc.).
* `calcular_iva_desagregado(items, total)`: Calcula el Neto Gravado y el IVA correspondiente por cada tasa de los productos del ticket. Retorna `(neto_total, iva_total, iva_por_tasa, base_por_tasa)`.
* `obtener_ultimo_autorizado(token, sign, cuit, pto_vta, cbte_tipo, sandbox_mode)`: Llama a `FECompUltimoAutorizado` y retorna el entero con el último número aprobado.
* `solicitar_cae_wsfe(...)`: Envía el sobre SOAP `FECAESolicitar` con el detalle del comprobante y retorna `(cae, vencimiento_formateado)`.

## Cómo funciona, en el orden en que corre
1. **Desglose impositivo:** `calcular_iva_desagregado()` recorre los productos consultando su alícuota en la base de datos o configuración global, ajustando por descuentos o recargos.
2. **Correlatividad:** Antes de emitir, se consulta a AFIP cuál fue el último número autorizado mediante `obtener_ultimo_autorizado()`. Se suma +1 para garantizar que no haya saltos de factura ni duplicaciones.
3. **Solicitud de CAE:** Se arma el XML `FECAESolicitar` con importes netos, IVA por tasa, concepto de productos y moneda local. Se envía vía SOAP con el Token y Sign del WSAA.
4. **Verificación de respuesta:**
   * Si el `<Resultado>` es `A` (Aprobado), extrae el `<CAE>` (14 dígitos) y la fecha de vencimiento `<CAEFchVto>`, formateándola a `DD/MM/AAAA`.
   * Si el resultado es `R` (Rechazado), extrae los mensajes de observación del servidor de AFIP y levanta una excepción explicativa.

## Qué devuelve cuando falla
* Lanza `RuntimeError` con el motivo exacto devuelto por AFIP (por ejemplo: *"Fecha de comprobante fuera de rango"*, *"CUIT inválido"*, *"Punto de venta no habilitado"*).

## Qué no debe cambiar una mejora futura
* No enviar números de comprobante arbitrarios sin consultar `FECompUltimoAutorizado`: AFIP rechaza tajantemente cualquier comprobante que no sea estrictamente consecutivo.
* Mantener el redondeo a 2 decimales en las bases imponibles y cuotas de IVA.
