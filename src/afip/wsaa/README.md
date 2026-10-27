# Subcarpeta WSAA (Autenticación y Autorización AFIP/ARCA)

## Qué hace la carpeta
Gestiona la autenticación segura con el Web Service de Autenticación y Autorización (WSAA) de AFIP/ARCA en Argentina. Genera tickets de acceso criptográficos firmados con OpenSSL y los cachea en disco local para no demorar las transacciones del cajero.

## Qué función, con el nombre real
* `find_openssl()`: Localiza el ejecutable de OpenSSL en el sistema operativo (PATH o rutas habituales de Windows).
* `obtener_token_sign(cuit, cert_path, key_path, sandbox_mode)`: Retorna la tupla `(token, sign)` válida para operar en WSFE.

## Cómo funciona, en el orden en que corre
1. **Revisión de caché:** Verifica si existe `tempfile/arca_ta_{cuit}.json` y si `expires_at > time.time()`. Si está vigente, devuelve inmediatamente el `token` y `sign` almacenados sin hacer llamadas de red.
2. **Generación de TRA:** Si no hay caché válido, crea un XML `loginTicketRequest` con ventana de tiempo de generación y expiración (`gen_time` a -5 min, `exp_time` a +15 min).
3. **Firma digital CMS:** Ejecuta `openssl smime -sign -nodetach` con la clave privada (`clave.key`) y el certificado (`certificado.crt`) del negocio, produciendo un blob binario DER codificado en Base64.
4. **Llamada SOAP a LoginCms:** Envía el sobre SOAP a `https://wsaahomo.afip.gov.ar/ws/services/LoginCms` (Homologación) o `https://wsaa.afip.gov.ar/ws/services/LoginCms` (Producción).
5. **Parseo y guardado:** Extrae `<token>` y `<sign>`, los guarda en la caché temporal con 11.5 horas de vigencia y los retorna.

## Qué devuelve cuando falla
* Si falta OpenSSL: Lanza `FileNotFoundError`.
* Si la clave o el certificado son inválidos o no coinciden: Lanza `RuntimeError` detallando el fallo de firma.
* Si el servidor de AFIP rechaza la solicitud: Lanza `RuntimeError` con el código HTTP y el mensaje de error de AFIP.

## Qué no debe cambiar una mejora futura
* No quitar la caché en disco de 11.5 horas: AFIP bloquea CUITs que solicitan tokens repetitivos en menos de 10 minutos.
* No alterar los offsets de tiempo en TRA (`-5m` a `+15m`): evitan rechazos por desincronización de reloj con el servidor de AFIP.
