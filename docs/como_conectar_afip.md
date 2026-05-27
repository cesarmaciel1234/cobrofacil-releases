# 🇦🇷 Guía de Conexión a AFIP / ARCA (Web Services - Factura Electrónica)

Esta guía explica paso a paso cómo conectar este sistema de punto de venta (TPV) a los servidores oficiales de **ARCA (ex-AFIP)** para emitir Facturas Electrónicas reales en Argentina.

---

## 📋 Requisitos Previos en AFIP
Para operar con Facturación Electrónica necesitas contar con:
1. **Clave Fiscal** (Nivel de seguridad 3 o superior).
2. Estar adherido al **Monotributo** o ser **Responsable Inscripto**.
3. Habilitar un **Punto de Venta** específico para Factura Electrónica (Web Services) en el portal de AFIP:
   * Entra a la web de AFIP con tu CUIT y Clave Fiscal.
   * Ve al servicio **"Registro Único Tributario (RUT)"** o **"Autorización de Comprobantes"** -> **"ABM de Puntos de Venta"**.
   * Crea un nuevo Punto de Venta (ej: `Punto de Venta 0002`).
   * Selecciona el sistema de facturación: **"Factura Electrónica - Web Services (WSFE)"**.

---

## 🛠️ Paso 1: Generar la Clave Privada y el Pedido de Certificado (CSR)
Para que AFIP valide tu identidad, se requiere un certificado digital de seguridad. Se genera localmente con la herramienta **OpenSSL** (puedes instalarla en Windows o usar Git Bash):

1. **Generar la clave privada (`clave.key`):**
   ```bash
   openssl genrsa -out clave.key 2048
   ```

2. **Generar el archivo de solicitud de certificado (`pedido.csr`):**
   *Reemplaza `CUITxxxxxxxxxxx` por tu CUIT de 11 dígitos sin guiones y `MiNegocio` por tu nombre o razón social.*
   ```bash
   openssl req -new -key clave.key -subj "/C=AR/O=MiNegocio/CN=MiNegocio/serialNumber=CUITxxxxxxxxxxx" -out pedido.csr
   ```

---

## 🔑 Paso 2: Obtener el Certificado Digital (`certificado.crt`) en AFIP
1. Ingresa a la web oficial de [AFIP / ARCA](https://www.afip.gob.ar/).
2. Busca e ingresa al servicio **"Administración de Certificados Digitales"** (si no lo tienes en tu pantalla de inicio, actívalo desde el Administrador de Relaciones).
3. Agrega un nuevo alias para tu sistema (ej: `TPV_PunPro`).
4. Sube el archivo `pedido.csr` que generaste en el paso anterior.
5. AFIP procesará la solicitud al instante. Descarga el certificado generado por AFIP, que tendrá formato `.crt` o `.der`. Guárdalo como `certificado.crt`.

---

## 🔗 Paso 3: Asociar el Certificado al Web Service de Facturación (WSFE)
Debes indicarle a la AFIP que ese certificado digital está autorizado para emitir facturas:

1. En el menú de AFIP, ingresa al **"Administrador de Relaciones de Clave Fiscal"**.
2. Presiona **"Nueva Relación"** -> **"Buscar"**.
3. Selecciona el logo de **AFIP** -> **"Servicios Interactivos"** -> **"Facturación Electrónica - Web Services (WSFE)"** (o bien busca "WSFE").
4. En **"Representante"**, selecciona el alias digital que creaste en el Paso 2 (`TPV_PunPro`).
5. Confirma la operación.

---

## 💻 Paso 4: Configurar los Archivos en el TPV
Una vez que tengas tus dos archivos (`clave.key` y `certificado.crt`):

1. Crea una carpeta llamada `certificados` dentro del directorio del sistema `cobrofacil pro/`.
2. Guarda allí los archivos:
   * `c:\Users\cesar\OneDrive\Desktop\cobrofacil pro\certificados\clave.key`
   * `c:\Users\cesar\OneDrive\Desktop\cobrofacil pro\certificados\certificado.crt`
3. En el archivo `config.json` del TPV, agrega o actualiza estas directivas para activar la conexión:
   ```json
   {
     "factura_electronica_mode": true,
     "business_cuit": "30-00000000-7",
     "arca_punto_venta": 2,
     "arca_sandbox_mode": false,
     "cert_key_path": "certificados/clave.key",
     "cert_crt_path": "certificados/certificado.crt"
   }
   ```
   *(Usa `arca_sandbox_mode: true` si primero quieres realizar facturas de prueba en el servidor de homologación de AFIP).*

---

## 📦 Automatización en Python (Librerías Recomendadas)
El TPV utiliza la biblioteca estándar **PyAfipWs** o llamadas directas SOAP (`zeep`) en Python para automatizar el login de AFIP (WSAA) y la solicitud de CAE (WSFE).

Una vez configurado con tus credenciales reales, cada vez que cobres un pago digital (tarjetas, Mercado Pago o transferencias), el sistema se conectará a AFIP de forma invisible en menos de 1 segundo, obtendrá el código de CAE oficial y lo imprimirá automáticamente en el ticket térmico con su QR legal.
