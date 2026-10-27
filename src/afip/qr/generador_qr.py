import json
import base64
from datetime import datetime

def generar_url_qr_afip(cuit_clean, pto_venta, tipo_cmp, nro_comp, total, doc_tipo, doc_nro, cae_num):
    """
    Construye el JSON reglamentario de ARCA/AFIP y genera la URL con el payload en Base64
    para que la impresora térmica o visor genere el código QR legalmente válido.
    """
    payload = {
        "ver": 1,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "cuit": int(cuit_clean),
        "ptoVta": int(pto_venta),
        "tipoCmp": int(tipo_cmp),
        "nroCmp": int(nro_comp),
        "importe": float(total),
        "moneda": "PES",
        "ctz": 1.0,
        "tipoDocRec": int(doc_tipo),
        "nroDocRec": int(doc_nro),
        "tipoCodAut": "E",
        "codAut": int(cae_num)
    }

    payload_json = json.dumps(payload)
    payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
    return f"https://www.afip.gob.ar/fe/qr/?p={payload_b64}"
