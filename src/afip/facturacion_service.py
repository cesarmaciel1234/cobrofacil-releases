import os
import random
from datetime import datetime, timedelta
from src.config import config
from src.logger import logger

from src.afip.wsaa import obtener_token_sign, find_openssl
from src.afip.wsfe import (
    obtener_ultimo_autorizado,
    solicitar_cae_wsfe,
    calcular_iva_desagregado,
    map_tasa_iva_id
)
from src.afip.qr import generar_url_qr_afip

class FacturacionService:
    """
    Servicio de Facturación Electrónica Industrial para ARCA (ex-AFIP) en Argentina.
    Orquesta la autenticación con WSAA, consulta de correlativo y CAE mediante WSFEv1,
    y generación de QR reglamentario.
    Si los certificados no están configurados o falla la conexión, realiza una simulación determinística
    robusta para garantizar que la venta nunca se bloquee en el mostrador.
    """

    @staticmethod
    def _find_openssl():
        return find_openssl()

    @staticmethod
    def _map_tasa_iva_id(tasa):
        return map_tasa_iva_id(tasa)

    @staticmethod
    def _calcular_iva_desagregado(items, total):
        return calcular_iva_desagregado(items, total)

    @staticmethod
    def _obtener_token_sign(cuit, cert_path, key_path, sandbox_mode):
        return obtener_token_sign(cuit, cert_path, key_path, sandbox_mode)

    @staticmethod
    def _obtener_ultimo_autorizado(token, sign, cuit, pto_vta, cbte_tipo, sandbox_mode):
        return obtener_ultimo_autorizado(token, sign, cuit, pto_vta, cbte_tipo, sandbox_mode)

    @staticmethod
    def _solicitar_cae_wsfe(token, sign, cuit, pto_vta, cbte_tipo, cbte_nro, total, neto, iva_total, iva_por_tasa, base_por_tasa, doc_tipo, doc_nro, sandbox_mode):
        return solicitar_cae_wsfe(token, sign, cuit, pto_vta, cbte_tipo, cbte_nro, total, neto, iva_total, iva_por_tasa, base_por_tasa, doc_tipo, doc_nro, sandbox_mode)

    @staticmethod
    def procesar_factura_electronica(venta_data):
        """
        Determina si la venta requiere Facturación Electrónica,
        solicita el CAE a ARCA de manera real o simula en caso de error/offline.
        """
        if not config.get("factura_electronica_mode", False):
            return None

        metodo = str(venta_data.get('metodo_pago', 'Efectivo')).upper()
        if metodo == "EFECTIVO":
            logger.info("Venta en Efectivo. Omitiendo Facturación Electrónica.")
            return None

        cuit_emisor = config.get("business_cuit", "30-00000000-7")
        cuit_clean = "".join([c for c in cuit_emisor if c.isdigit()])
        if not cuit_clean:
            cuit_clean = "30000000007"

        pto_venta = int(config.get("arca_punto_venta", 1))
        sandbox_mode = config.get("arca_sandbox_mode", False)

        cert_path = config.get("cert_crt_path", "certificados/certificado.crt")
        key_path = config.get("cert_key_path", "certificados/clave.key")

        # 6 = Factura B, 11 = Factura C (Monotributo usa 11, RI usa 6. Por defecto usaremos B=6)
        tipo_cmp = 6

        # Datos de la venta
        nro_comp = int(venta_data.get('id', 0))
        total = float(venta_data.get('total', 0.0))
        items = venta_data.get('items', [])

        # Mapeo de cliente (Consumidor Final por defecto)
        doc_tipo = 99
        doc_nro = 0

        # Calcular IVA desagregado
        neto, iva_total, iva_por_tasa, base_por_tasa = calcular_iva_desagregado(items, total)

        cae_num = None
        cae_vence = None
        origen_factura = "REAL"

        # Si las claves existen, intentar conexión real con AFIP
        if os.path.exists(cert_path) and os.path.exists(key_path):
            try:
                logger.info(f"Conectando a AFIP/ARCA para solicitar CAE real del comprobante #{nro_comp}...")
                token, sign = obtener_token_sign(cuit_clean, cert_path, key_path, sandbox_mode)

                # Consultar último comprobante para asegurar correlatividad exacta
                ultimo_autorizado = obtener_ultimo_autorizado(token, sign, cuit_clean, pto_venta, tipo_cmp, sandbox_mode)
                proximo_nro = ultimo_autorizado + 1
                logger.info(f"Correlativo AFIP/ARCA: Último autorizado: {ultimo_autorizado}. Próximo a autorizar: {proximo_nro}.")

                cae_num, cae_vence = solicitar_cae_wsfe(
                    token, sign, cuit_clean, pto_venta, tipo_cmp, proximo_nro,
                    total, neto, iva_total, iva_por_tasa, base_por_tasa,
                    doc_tipo, doc_nro, sandbox_mode
                )
                logger.info(f"CAE Real obtenido con éxito: {cae_num}. Vence: {cae_vence}.")

            except Exception as e:
                logger.error(f"Fallo al conectar con el servidor AFIP ({e}). Entrando en modo offline/simulado.")
                cae_num = None

        if not cae_num:
            # Fallback a simulación industrial determinística
            origen_factura = "SIMULADA"
            random.seed(nro_comp + int(total * 100))
            cae_num = "".join([str(random.randint(0, 9)) for _ in range(14)])
            cae_vence = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
            logger.info(f"Factura generada en modo offline/simulado. CAE determinístico asignado: {cae_num}.")

        # Generar URL oficial de QR
        qr_url = generar_url_qr_afip(cuit_clean, pto_venta, tipo_cmp, nro_comp, total, doc_tipo, doc_nro, cae_num)

        return {
            "cae": cae_num,
            "vencimiento": cae_vence,
            "qr_url": qr_url,
            "tipo_comprobante": "FACTURA_B",
            "pto_venta": pto_venta,
            "origen": origen_factura
        }
