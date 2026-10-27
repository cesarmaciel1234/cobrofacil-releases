# Plano del Módulo: Facturación Electrónica AFIP / ARCA (`src/afip`)

Este módulo es la rama oficial de integración fiscal con la Agencia de Recaudación y Control Aduanero (ARCA, ex-AFIP) de la República Argentina. Permite la emisión de Facturas Electrónicas (B y C), consulta de correlatividad y generación del código QR legal para tickets térmicos.

---

## 🖥️ Frente (Lo que ve el usuario)

1. **Pantalla de Configuración Fiscal (Admin):**
   * **Acceso:** Desde el menú lateral del Administrador -> Botón **Configuración** -> Categoría **Facturación** / Diálogo `dialogo_facturacion.py`.
   * **Qué pinta:**
     * Switch de activación general de Facturación Electrónica (ARCA WSFE).
     * Campo para ingresar el CUIT emisor del comercio.
     * Selector de Punto de Venta (número entero habilitado en AFIP, ej: 2).
     * Checkbox de Modo Homologación (Sandbox / Pruebas) vs Modo Producción.
     * Selectores de archivo para cargar la clave privada (`clave.key`) y el certificado digital (`certificado.crt`).
     * Selector de métodos de pago que disparan factura obligatoria (Tarjeta, Transferencia, QR, Débito, Crédito).
   * **Qué no pinta:**
     * No expone contraseñas ni el contenido crudo de la clave privada.
     * No solicita credenciales en el mostrador del cajero.

2. **Cajero (Punto de Venta al Cobrar):**
   * **Acceso:** Al presionar **F12 / Cobrar** en el módulo de ventas.
   * **Qué pinta:**
     * Si la venta es con un método digital (o fiscal forzado), emite el ticket térmico incorporando:
       * Encabezado con datos fiscales (CUIT emisor, Razón Social, Condición de IVA).
       * Leyenda oficial: `FACTURA B` o `FACTURA C`, Punto de Venta y Número consecutivo.
       * Código de Autorización Electrónico: `CAE: XXXXXXXXXXXXXX`.
       * Fecha de vencimiento: `Vto. CAE: DD/MM/AAAA`.
       * **Código QR impreso** oficial de ARCA/AFIP escaneable con cualquier smartphone.
   * **Qué no pinta:**
     * Si la venta es en efectivo y no se forzó comprobante fiscal, no llama a AFIP ni imprime el bloque de CAE para agilizar la cola.

---

## ⚙️ Fondo (Lo que corre internamente)

### Arquitectura en Pirámide
```
src/afip/
  plano.md                  <-- Este documento (Frente y Fondo)
  como_conectar_afip.md     <-- Guía paso a paso para dar de alta certificados en ARCA/AFIP
  facturacion_service.py    <-- Orquestador y fachada de compatibilidad
  wsaa/
    README.md               <-- Documentación de autenticación y tokens
    autenticador.py         <-- LoginCms, OpenSSL y caché de 11.5 horas
  wsfe/
    README.md               <-- Documentación de comprobantes y CAE
    autorizador.py          <-- FECompUltimoAutorizado y FECAESolicitar
  qr/
    README.md               <-- Documentación del formato oficial de QR
    generador_qr.py         <-- Payload JSON oficial y URL Base64
```

### Flujo de Ejecución y Orden de Llamadas
1. **Disparo:** El cajero finaliza una venta (`src/hardware/printer.py` -> `imprimir_ticket_venta`).
2. **Evaluación de condiciones:** Se verifica si `factura_electronica_mode == True` y si el método de pago no es Efectivo simple.
3. **Orquestación:** Se invoca a `FacturacionService.procesar_factura_electronica(venta_data)`.
4. **Cálculo de alícuotas:** `src.afip.wsfe.autorizador.calcular_iva_desagregado()` desglosa el Neto e IVA por cada tasa (21%, 10.5%, etc.) según la tabla de `departamentos` o configuración.
5. **Autenticación WSAA:** `src.afip.wsaa.autenticador.obtener_token_sign()` busca la caché local (`arca_ta_{cuit}.json`). Si expiró, invoca OpenSSL para firmar el CMS y obtiene un nuevo `Token` y `Sign` desde AFIP.
6. **Consulta de correlativo:** `src.afip.wsfe.autorizador.obtener_ultimo_autorizado()` consulta `FECompUltimoAutorizado` y suma +1.
7. **Autorización CAE:** `src.afip.wsfe.autorizador.solicitar_cae_wsfe()` envía `FECAESolicitar` con el desglose impositivo y obtiene el CAE de 14 dígitos y su vencimiento.
8. **Generación QR:** `src.afip.qr.generador_qr.generar_url_qr_afip()` arma el JSON reglamentario en Base64 con el enlace oficial de AFIP.
9. **Retorno al Hardware:** Se devuelve el diccionario con `cae`, `vencimiento`, `qr_url` y `pto_venta` a `printer.py` para el renderizado e impresión física.

### Fallback y Tolerancia a Fallos
* Si el servidor de AFIP no responde, se corta internet o faltan los certificados `.crt/.key`, el orquestador captura el error, registra un log informativo y genera un comprobante con numeración de contingencia determinística sin bloquear la venta ni congelar la pantalla del cajero.

---

## 🚫 Qué NO hay que romper en futuras mejoras
1. **La numeración consecutiva:** No se debe enviar un número de comprobante sin haber consultado previamente el último autorizado por AFIP, de lo contrario AFIP bloqueará la autorización.
2. **La caché de autenticación WSAA:** AFIP banea transitoriamente los CUITs que solicitan tickets de acceso continuos. El archivo de caché temporal debe conservarse.
3. **El fallback offline:** La llamada a AFIP nunca debe detener el hilo principal de la interfaz ni evitar que el cajón de dinero abra o que el ticket se emita.
