import os
import json
import time
import random
import subprocess
import tempfile
import base64
import re
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from src.logger import logger

def find_openssl():
    """Localiza el binario openssl en el sistema operativo."""
    import shutil
    openssl_path = shutil.which("openssl")
    if openssl_path:
        return openssl_path

    common_paths = [
        r"C:\Program Files\Git\usr\bin\openssl.exe",
        r"C:\Program Files (x86)\Git\usr\bin\openssl.exe",
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
        r"C:\Git\usr\bin\openssl.exe"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

def obtener_token_sign(cuit, cert_path, key_path, sandbox_mode):
    """
    Obtiene el Token y Sign del servicio WSAA de AFIP/ARCA usando OpenSSL para firmar el TRA.
    Mantiene caché de 11.5 horas en tempfile para optimizar tiempos de cobro.
    """
    cache_file = os.path.join(tempfile.gettempdir(), f"arca_ta_{cuit}.json")

    # 1. Validar cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
            if cache.get("expires_at", 0) > time.time():
                return cache["token"], cache["sign"]
        except Exception:
            pass

    # 2. Generar XML de TRA (Ticket de Requerimiento de Acceso)
    now = datetime.now()
    gen_dt = now - timedelta(minutes=5)
    exp_dt = now + timedelta(minutes=15)
    gen_time = gen_dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")
    exp_time = exp_dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")
    unique_id = random.randint(1000, 99999)

    tra_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>{unique_id}</uniqueId>
    <generationTime>{gen_time}</generationTime>
    <expirationTime>{exp_time}</expirationTime>
  </header>
  <service>wsfe</service>
</loginTicketRequest>"""

    tra_path = os.path.join(tempfile.gettempdir(), f"tra_{cuit}.xml")
    cms_path = os.path.join(tempfile.gettempdir(), f"tra_{cuit}.cms")

    try:
        with open(tra_path, "w", encoding="utf-8") as f:
            f.write(tra_xml)

        openssl_bin = find_openssl()
        if not openssl_bin:
            raise FileNotFoundError("OpenSSL no está en el PATH ni en ubicaciones comunes de Windows.")

        cmd = [
            openssl_bin, "smime", "-sign",
            "-signer", cert_path,
            "-inkey", key_path,
            "-outform", "DER",
            "-nodetach",
            "-in", tra_path,
            "-out", cms_path
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        with open(cms_path, "rb") as f:
            cms_data = f.read()
        cms_b64 = base64.b64encode(cms_data).decode("utf-8")

    except Exception as e:
        logger.error(f"Error al firmar el TRA usando OpenSSL: {e}")
        raise RuntimeError(f"Firma de TRA falló. Verifique OpenSSL y las rutas de certificados (.crt y .key): {e}")
    finally:
        for p in [tra_path, cms_path]:
            try: os.remove(p)
            except: pass

    # 3. Request a WSAA SOAP
    wsaa_url = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" if sandbox_mode else "https://wsaa.afip.gov.ar/ws/services/LoginCms"

    soap_req = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <loginCms xmlns="http://wsaa.view.xfire.sofia.usro.afip.gov">
      <in0>{cms_b64}</in0>
    </loginCms>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": ""
    }

    import requests
    resp = requests.post(wsaa_url, data=soap_req, headers=headers, timeout=15, verify=False)
    if resp.status_code != 200:
        raise RuntimeError(f"Error WSAA HTTP {resp.status_code}: {resp.text}")

    match = re.search(r"<loginCmsReturn>(.*?)</loginCmsReturn>", resp.text, re.DOTALL)
    if not match:
        raise RuntimeError("Respuesta del servidor WSAA de AFIP no tiene el tag loginCmsReturn.")

    ta_xml = match.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&").replace("&apos;", "'")

    try:
        ta_root = ET.fromstring(ta_xml)
        token = ta_root.find(".//token").text
        sign = ta_root.find(".//sign").text

        cache_data = {
            "token": token,
            "sign": sign,
            "expires_at": time.time() + 11.5 * 3600
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        return token, sign
    except Exception as e:
        raise RuntimeError(f"Error parseando XML del Ticket de Acceso: {e}")
