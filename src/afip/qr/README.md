# Subcarpeta QR (Código QR Fiscal ARCA/AFIP)

## Qué hace la carpeta
Genera el payload estructurado y la URL oficial reglamentaria exigida por AFIP/ARCA (Resolución General 4892/2020) para la impresión de comprobantes electrónicos con código QR.

## Qué función, con el nombre real
* `generar_url_qr_afip(cuit_clean, pto_venta, tipo_cmp, nro_comp, total, doc_tipo, doc_nro, cae_num)`: Ensambla el diccionario con las claves exigidas por la AFIP, lo serializa a JSON y lo codifica en Base64. Retorna el enlace `https://www.afip.gob.ar/fe/qr/?p={payload_b64}`.

## Cómo funciona, en el orden en que corre
1. Recibe los datos de cabecera y el CAE otorgado por el WSFE.
2. Formatea la fecha actual en `YYYY-MM-DD`.
3. Establece el tipo de autorización en `E` (CAE electrónico).
4. Codifica el texto JSON a bytes UTF-8 y luego a Base64 estándar.
5. Concatena la URL oficial del portal de verificación ciudadana de AFIP.

## Qué devuelve cuando falla
* Si faltan argumentos o los tipos no son convertibles a numéricos/cadenas, levanta `ValueError` o `TypeError`.

## Qué no debe cambiar una mejora futura
* El formato de los campos del JSON está normado por ley: no cambiar nombres de claves (`ptoVta`, `tipoCmp`, `nroCmp`, `codAut`, etc.) ni la URL base de AFIP.
