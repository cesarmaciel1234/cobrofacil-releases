"""Snapshot JSON de la cara. Si fallar armar, se deja el último bueno."""

import logging

logger = logging.getLogger("LanzadorDirectoTV")

ESTADO_MINIMO = {"config": {"data_status": "offline"}, "precios": []}
MAX_PRECIOS_TV = 96


def precios_para_tv(rows, perfil="max"):
    """La cara no traga 4000 filas: ofertas primero, tope para el ticker."""
    avisos = []
    ofertas = []
    resto = []
    for p in rows or []:
        if p.get("es_publicidad"):
            avisos.append(p)
            continue
        ofe = p.get("precio_oferta") or 0
        pre = p.get("precio") or 0
        if ofe > 0 and ofe < pre:
            ofertas.append(p)
        else:
            resto.append(p)
    return (avisos + ofertas + resto)[:MAX_PRECIOS_TV]


class EstadoMixin:
    def _publicar_estado(self):
        previo = self._state_cache
        try:
            from src.carteleria.lanzador_tv.perfil_pc import perfil_activo
            from src.carteleria.lanzador_tv.cerebro_lanzador_tv import _leer_config_carteleria

            cfg_tv = _leer_config_carteleria(solo_memoria=True)
            perf = perfil_activo()
            business_name = cfg_tv["business_name"]
            try:
                from src.central_red_global.sync_tienda.aviso_tv import leer_sello

                datos_gen = leer_sello()
            except Exception:
                datos_gen = ""
            paneles = self._paneles or {}
            self._state_cache = {
                "datos_gen": datos_gen,
                "config": {
                    "business_name": business_name,
                    "phone": cfg_tv["phone"],
                    "carteleria_theme": cfg_tv["carteleria_theme"],
                    "carteleria_perf": perf,
                    "mensaje_zocalo": cfg_tv["mensaje_zocalo"] or self._generar_mensaje_banderin(business_name),
                    "data_status": self._sync_status,
                },
                "precios": precios_para_tv(self.rows_precios, perf),
                "sos": self.sos_data,
                "top10": self.top10_data,
                "hero": paneles.get("hero"),
                "destacados": paneles.get("destacados") or [],
                "rotacion": paneles.get("rotacion") or [],
                "combos": paneles.get("combos") or [],
                "columna3": paneles.get("columna3") or [],
                "ia": paneles.get("ia") or [],
                "climaData": self._generar_datos_clima(),
            }
        except Exception as e:
            logger.warning("Publicar estado: %s", e)
            if not isinstance(previo, dict) or not previo.get("precios"):
                self._state_cache = dict(ESTADO_MINIMO)
                self._state_cache["precios"] = list(self.rows_precios or [])

    def get_web_state(self):
        st = self._state_cache
        if not isinstance(st, dict):
            return dict(ESTADO_MINIMO)
        if "precios" not in st:
            out = dict(st)
            out["precios"] = list(self.rows_precios or [])
        else:
            out = st
        try:
            from src.carteleria.lanzador_tv.cerebro_lanzador_tv import _leer_config_carteleria

            vivo = _leer_config_carteleria(solo_memoria=True)
            cfg = dict(out.get("config") or {})
            tema = vivo.get("carteleria_theme")
            if tema and cfg.get("carteleria_theme") != tema:
                out = dict(out)
                cfg["carteleria_theme"] = tema
                out["config"] = cfg
        except Exception:
            pass
        return out

    def _generar_datos_clima(self):
        try:
            import datetime

            icono = self._clima_icon or "sol"
            temperatura = self._clima or "22°C"
            hora_actual = datetime.datetime.now().hour
            clima = str(self._clima or "").lower()
            if 18 <= hora_actual or hora_actual < 6:
                mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
                producto_recomendado = "BOLSA DE MENUDENCIOS" if "lluvia" in clima else "POLLO ENTERO"
            else:
                if "nublado" in clima:
                    mensaje = "Día nublado, ideal para compras en abrigo"
                    producto_recomendado = "POLLO ENTERO"
                elif "lluvia" in clima:
                    mensaje = "Día de lluvia, perfecto para productos de olla"
                    producto_recomendado = "BOLSA DE MENUDENCIOS"
                else:
                    mensaje = "Día soleado, perfecto para la parrilla"
                    producto_recomendado = "POLLO ENTERO"
            precio = 4900
            for prod in self.rows_precios or []:
                if producto_recomendado.lower() in (prod.get("nombre") or "").lower():
                    precio = prod.get("precio", 4900)
                    break
            return {
                "icono": icono,
                "temperatura": temperatura,
                "mensaje": mensaje,
                "producto_recomendado": producto_recomendado,
                "precio": precio,
            }
        except Exception:
            return {
                "icono": "sol",
                "temperatura": "22°C",
                "mensaje": "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR",
                "producto_recomendado": "POLLO ENTERO",
                "precio": 4900,
            }

    def _generar_mensaje_banderin(self, business_name):
        try:
            mensajes_base = [
                f"Bienvenido a {business_name} • Los mejores precios • Calidad garantizada",
                f"Calidad garantizada en {business_name} • Precios competitivos • Atención personalizada",
                f"{business_name} • Frescura garantizada • Productos de primera calidad",
            ]
            clima = str(self._clima or "").lower()
            if "nublado" in clima:
                mensajes_base.append("Día ideal para compras en abrigo • Calidez en cada producto")
            elif "sol" in clima:
                mensajes_base.append("Día perfecto para la parrilla • Disfruta el buen clima")
            ofertas = [
                p for p in (self.rows_precios or [])
                if (p.get("precio_oferta") or 0) > 0 and (p.get("precio_oferta") or 0) < (p.get("precio") or 0)
            ]
            if ofertas:
                mensajes_base.append(f"• {len(ofertas)} ofertas activas hoy • Aprovechá las promociones")
            return " • ".join(mensajes_base)
        except Exception:
            return f"Bienvenido a {business_name or 'la tienda'}"
