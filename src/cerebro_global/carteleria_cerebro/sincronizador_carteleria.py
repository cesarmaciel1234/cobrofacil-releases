import math
import re
import threading
import time

from src.base_de_datos.database import db_manager
from src.logger import logger
from src.cerebro_global.servicios.cache_productos import cache_productos


def _limpiar_nombre(nombre):
    nombre = str(nombre or "")
    for tag in ["🔥 [OFERTA] ", "🔥 [OFERTA]", "[OFERTA] ", "[OFERTA]", "📦 [MAYOREO] ", "📦 [MAYOREO]", "🌟 "]:
        nombre = nombre.replace(tag, "")
    nombre = re.sub(r'^(?:oferta\s+de|oferta)\s+', '', nombre, flags=re.IGNORECASE).strip()
    return nombre


class SincronizadorCarteleria:
    """
    Cerebro independiente que carga los datos de 'productos' (Inventario),
    los formatea limpiamente (Kilos/Unidades/Colores), y los guarda en 'carteleria_global'
    para que la Grilla de Precios los consuma sin saturar el sistema.
    """
    def __init__(self, intervalo_segundos=30):
        self.intervalo = intervalo_segundos
        self.running = False
        self._thread = None
        self._fail_streak = 0

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Sincronizador de Cartelería INICIADO.")

    def stop(self):
        self.running = False

    def _run_loop(self):
        self.sincronizar_ahora()

        while self.running:
            time.sleep(self.intervalo)
            self.sincronizar_ahora()

    def sincronizar_ahora(self):
        try:
            filas = [
                p for p in cache_productos.obtener_todos()
                if float(p.get('precio') or 0) > 0
            ]
            if not filas:
                return

            nuevos_datos = []

            for fila in filas:
                if isinstance(fila, dict):
                    departamento = str(fila.get('categoria', ''))
                    nombre_producto = _limpiar_nombre(fila.get('nombre', ''))
                    precio_normal = float(fila.get('precio') or 0)
                    precio_oferta = float(fila.get('precio_oferta') or 0)
                    cant_oferta = float(fila.get('cant_oferta') or 0)
                    tipo_unidad = str(fila.get('tipo_unidad_oferta') or "").strip().lower()
                    prod_unidad = str(fila.get('unidad') or "").strip().lower()
                else:
                    departamento = str(fila[0])
                    nombre_producto = _limpiar_nombre(fila[1])
                    precio_normal = float(fila[2] or 0)
                    precio_oferta = float(fila[3] or 0)
                    cant_oferta = float(fila[4] or 0)
                    tipo_unidad = str(fila[5] or "").strip().lower()
                    prod_unidad = str(fila[6] or "").strip().lower()

                regla_texto = ""
                if cant_oferta > 0:
                    cant_display = cant_oferta
                    if cant_display >= 1:
                        frac = cant_display - math.floor(cant_display)
                        if frac >= 0.8:
                            cant_display = float(math.ceil(cant_display))

                    is_kilo = (
                        'kilo' in prod_unidad or prod_unidad == 'kg'
                        or 'kilo' in tipo_unidad or tipo_unidad == 'kg'
                        or cant_oferta != int(cant_oferta)
                    )
                    if is_kilo:
                        if cant_display < 1:
                            t_un_str = f"{int(round(cant_display * 1000))} gs"
                        elif cant_display == 1:
                            t_un_str = "1 Kilo"
                        else:
                            t_un_str = f"{cant_display:g} Kilos"
                    else:
                        if cant_display == 1:
                            t_un_str = "1 Unidad"
                        else:
                            t_un_str = f"{int(cant_display)} Unidades"

                    regla_texto = (
                        f"<span style='color: #00A859;'>Llevando</span> "
                        f"<span style='color: #DC2626;'>{t_un_str}</span>"
                    )

                nuevos_datos.append((
                    departamento,
                    nombre_producto,
                    precio_normal,
                    precio_oferta,
                    regla_texto
                ))

            # Una sola transacción: no dejar la tabla vacía si falla el INSERT
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM carteleria_global")
                insert_sql = db_manager._normalize_query(
                    """
                    INSERT INTO carteleria_global
                    (departamento, nombre_producto, precio_normal, precio_oferta, regla_texto)
                    VALUES (?, ?, ?, ?, ?)
                    """
                )
                cursor.executemany(insert_sql, nuevos_datos)
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            self._fail_streak = 0

        except Exception as e:
            self._fail_streak += 1
            # Evitar spamear traceback completo en caídas de red / maestra offline
            if self._fail_streak <= 1 or self._fail_streak % 10 == 0:
                logger.warning(
                    f"SincronizadorCarteleria: sin sync ({self._fail_streak}x): {e}"
                )


# Instancia global (Singleton)
sincronizador_carteleria = SincronizadorCarteleria(intervalo_segundos=30)
