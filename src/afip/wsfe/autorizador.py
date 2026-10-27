import re
from datetime import datetime
from src.config import config
from src.base_de_datos.database import db_manager
from src.logger import logger

def map_tasa_iva_id(tasa):
    """
    Mapea el porcentaje de IVA al ID correspondiente según la tabla oficial de AFIP:
    3: 0%, 4: 10.5%, 5: 21%, 6: 27%, 8: 5%, 9: 2.5%
    """
    t = round(float(tasa), 2)
    if t == 21.0: return 5
    elif t == 10.5: return 4
    elif t == 27.0: return 6
    elif t == 5.0: return 8
    elif t == 2.5: return 9
    elif t == 0.0: return 3
    else: return 5  # Por defecto 21%

def calcular_iva_desagregado(items, total):
    """
    Calcula el NETO e IVA total acumulado por tasa, alineado con printer.py y la normativa de AFIP.
    Retorna: (neto_total, iva_total, iva_por_tasa, base_por_tasa)
    """
    neto_total = 0.0
    iva_total = 0.0
    iva_por_tasa = {}
    base_por_tasa = {}

    factor_ajuste = 1.0
    if total > 0 and items:
        original_subtotal = sum(float(it.get('subtotal', 0.0)) for it in items)
        if original_subtotal > 0:
            factor_ajuste = total / original_subtotal

    for it in (items or []):
        p_id = it.get('id')
        tasa_iva = float(config.get("tax_percentage", 21.0))
        if p_id and str(p_id) != '000':
            try:
                res = db_manager.execute_query(
                    "SELECT d.iva FROM productos p JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE p.id = ? OR p.codigo = ?",
                    (p_id, p_id)
                )
                if res and res[0]['iva'] is not None:
                    tasa_iva = float(res[0]['iva'])
            except Exception:
                pass

        subt_item_ajustado = float(it.get('subtotal', 0.0)) * factor_ajuste
        neto_item = subt_item_ajustado / (1 + tasa_iva / 100)
        iva_item = subt_item_ajustado - neto_item

        neto_total += neto_item
        iva_total += iva_item
        iva_por_tasa[tasa_iva] = iva_por_tasa.get(tasa_iva, 0.0) + iva_item
        base_por_tasa[tasa_iva] = base_por_tasa.get(tasa_iva, 0.0) + neto_item

    return neto_total, iva_total, iva_por_tasa, base_por_tasa

def obtener_ultimo_autorizado(token, sign, cuit, pto_vta, cbte_tipo, sandbox_mode):
    """
    Consulta a AFIP (FECompUltimoAutorizado) el último comprobante autorizado para el punto de venta y tipo.
    """
    wsfe_url = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx" if sandbox_mode else "https://servicios1.afip.gov.ar/wsfev1/service.asmx"

    soap_req = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <FECompUltimoAutorizado xmlns="http://ar.gov.afip.dif.FEV1/">
      <Auth>
        <Token>{token}</Token>
        <Sign>{sign}</Sign>
        <Cuit>{cuit}</Cuit>
      </Auth>
      <PtoVta>{pto_vta}</PtoVta>
      <CbteTipo>{cbte_tipo}</CbteTipo>
    </FECompUltimoAutorizado>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://ar.gov.afip.dif.FEV1/FECompUltimoAutorizado"
    }

    import requests
    resp = requests.post(wsfe_url, data=soap_req, headers=headers, timeout=10, verify=False)
    if resp.status_code != 200:
        raise RuntimeError(f"WSFE ÚltimoAutorizado HTTP {resp.status_code}: {resp.text}")

    cbte_nro_match = re.search(r"<CbteNro>(\d+)</CbteNro>", resp.text)
    if cbte_nro_match:
        return int(cbte_nro_match.group(1))
    raise RuntimeError("No se pudo extraer CbteNro de la respuesta de AFIP.")

def solicitar_cae_wsfe(token, sign, cuit, pto_vta, cbte_tipo, cbte_nro, total, neto, iva_total, iva_por_tasa, base_por_tasa, doc_tipo, doc_nro, sandbox_mode):
    """
    Envía la solicitud de facturación electrónica a AFIP (FECAESolicitar).
    Retorna la tupla (cae, vencimiento_formateado).
    """
    wsfe_url = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx" if sandbox_mode else "https://servicios1.afip.gov.ar/wsfev1/service.asmx"
    cbte_fch = datetime.now().strftime("%Y%m%d")

    iva_xml = ""
    if iva_por_tasa:
        iva_xml = "<Iva>"
        for tasa, m_iva in iva_por_tasa.items():
            if m_iva <= 0: continue
            base_imp = base_por_tasa.get(tasa, 0.0)
            iva_xml += f"""
          <AlicIva>
            <Id>{map_tasa_iva_id(tasa)}</Id>
            <BaseImp>{base_imp:.2f}</BaseImp>
            <Importe>{m_iva:.2f}</Importe>
          </AlicIva>"""
        iva_xml += "</Iva>"

    soap_req = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <FECAESolicitar xmlns="http://ar.gov.afip.dif.FEV1/">
      <Auth>
        <Token>{token}</Token>
        <Sign>{sign}</Sign>
        <Cuit>{cuit}</Cuit>
      </Auth>
      <FeCAEReq>
        <FeCabReq>
          <CantReg>1</CantReg>
          <PreDoc>{pto_vta}</PreDoc>
          <CbteTipo>{cbte_tipo}</CbteTipo>
        </FeCabReq>
        <FeDetReq>
          <FECAEDetRequest>
            <Concepto>1</Concepto>
            <DocTipo>{doc_tipo}</DocTipo>
            <DocNro>{doc_nro}</DocNro>
            <CbteDesde>{cbte_nro}</CbteDesde>
            <CbteHasta>{cbte_nro}</CbteHasta>
            <CbteFch>{cbte_fch}</CbteFch>
            <ImpTotal>{total:.2f}</ImpTotal>
            <ImpTotConc>0.00</ImpTotConc>
            <ImpNeto>{neto:.2f}</ImpNeto>
            <ImpOpEx>0.00</ImpOpEx>
            <ImpTrib>0.00</ImpTrib>
            <ImpIVA>{iva_total:.2f}</ImpIVA>
            <FchServDesde/>
            <FchServHasta/>
            <FchVtoPago/>
            <MonId>PES</MonId>
            <MonCotiz>1</MonCotiz>
            {iva_xml}
          </FECAEDetRequest>
        </FeDetReq>
      </FeCAEReq>
    </FECAESolicitar>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://ar.gov.afip.dif.FEV1/FECAESolicitar"
    }

    import requests
    resp = requests.post(wsfe_url, data=soap_req, headers=headers, timeout=15, verify=False)
    if resp.status_code != 200:
        raise RuntimeError(f"WSFE FECAESolicitar HTTP {resp.status_code}: {resp.text}")

    res_text = resp.text

    resultado_match = re.search(r"<Resultado>([A-Z])</Resultado>", res_text)
    if not resultado_match:
        raise RuntimeError("Respuesta de AFIP no contiene elemento de Resultado.")

    resultado = resultado_match.group(1)
    if resultado != "A":
        obs_match = re.findall(r"<Msg>(.*?)</Msg>", res_text)
        err_msg = "; ".join(obs_match) if obs_match else "Rechazado por AFIP."
        msg_match = re.findall(r"<Mensaje>(.*?)</Mensaje>", res_text)
        if msg_match:
            err_msg += " | " + "; ".join(msg_match)
        raise RuntimeError(err_msg)

    cae_match = re.search(r"<CAE>(\d+)</CAE>", res_text)
    vto_match = re.search(r"<CAEFchVto>(\d+)</CAEFchVto>", res_text)

    if cae_match and vto_match:
        cae = cae_match.group(1)
        vto_raw = vto_match.group(1)
        vto_formatted = f"{vto_raw[6:8]}/{vto_raw[4:6]}/{vto_raw[0:4]}"
        return cae, vto_formatted

    raise RuntimeError("No se encontró el CAE o el Vencimiento en la respuesta aprobada.")
