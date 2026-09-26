import math
import os
import datetime
import json

class MotorPromedios:
    @staticmethod
    def calcular_media_res(kilos_totales: float, precio_kg: float, suma_kilos_cortes: float):
        """
        Calcula la merma, los kilos útiles y el costo real por kg de la media res.
        """
        merma_auto = kilos_totales - suma_kilos_cortes
        kilos_utiles = kilos_totales - merma_auto
        total_compra = kilos_totales * precio_kg
        costo_real_kg = total_compra / kilos_utiles if kilos_utiles > 0 else 0.0
        return merma_auto, kilos_utiles, costo_real_kg

    @staticmethod
    def recalcular_fila(columna_editada: int, nuevo_valor: float, costo_real_kg: float):
        """
        Calcula el nuevo porcentaje de ganancia o el nuevo precio de venta, dependiendo de qué columna se editó.
        Retorna (nuevo_pct, nuevo_precio_venta).
        Si columna_editada == 3 (% Ganancia), recalcula Precio Venta.
        Si columna_editada == 4 (Precio Venta), recalcula % Ganancia.
        """
        pct = 0.0
        precio_venta = 0.0

        if columna_editada == 3: # % Ganancia
            pct = nuevo_valor
            if costo_real_kg > 0:
                precio_venta = costo_real_kg * (1 + pct / 100.0)

        elif columna_editada == 4: # Precio Venta
            precio_venta = nuevo_valor
            if costo_real_kg > 0:
                pct = ((precio_venta / costo_real_kg) - 1) * 100.0

        return pct, precio_venta

    @staticmethod
    def exportar_a_inventario(db, tipo_promedio: str, estado_promedios: dict):
        """
        Exporta precio/costo y mayoreo al inventario vía MotorMayoreo.
        Ya no usa precio_oferta_promedio (retirado).
        """
        from src.motor_descuentos.mayoreo.motor import MotorMayoreo

        estado = estado_promedios.get(tipo_promedio)
        if not estado:
            return 0

        motor = MotorMayoreo(db=db)
        actualizados = 0
        filas = estado.get("filas", [])
        for row_data in filas:
            if len(row_data) < 9:
                continue
            corte = str(row_data[0]).strip()
            if not corte:
                continue

            costo_str = str(row_data[2]).replace(",", "").strip()
            precio_base_str = str(row_data[4]).replace(",", "").strip()
            mayoreo_str = str(row_data[5]).replace(",", "").strip()
            cant_str = str(row_data[6]).replace(",", "").strip()

            precio = 0.0
            precio_mayoreo = 0.0
            cant_mayoreo = 0.0
            costo = 0.0
            try:
                if precio_base_str:
                    precio = float(precio_base_str)
            except Exception:
                pass
            try:
                if mayoreo_str:
                    precio_mayoreo = float(mayoreo_str)
            except Exception:
                pass
            try:
                if cant_str:
                    cant_mayoreo = float(cant_str)
            except Exception:
                pass
            try:
                if costo_str:
                    costo = float(costo_str)
            except Exception:
                pass

            if motor.aplicar_desde_promedios(
                corte, precio, costo, cant_mayoreo, precio_mayoreo,
                categoria=tipo_promedio,
            ):
                actualizados += 1

        return actualizados

    @staticmethod
    def sincronizar_inventario(db, tipo_promedio: str, estado_promedios: dict):
        """
        Trae precio y mayoreo desde inventario hacia la tabla de promedios.
        """
        from src.motor_descuentos.mayoreo.motor import MotorMayoreo

        estado = estado_promedios.get(tipo_promedio)
        if not estado:
            return 0

        motor = MotorMayoreo(db=db)
        actualizados = 0
        filas = estado.get("filas", [])
        for r_idx, row_data in enumerate(filas):
            if len(row_data) < 9:
                continue
            corte = str(row_data[0]).strip()
            if not corte:
                continue
            cfg = motor.obtener_por_nombre(corte)
            if cfg.get("precio", 0) > 0:
                filas[r_idx][4] = f"{cfg['precio']:,.2f}"
                actualizados += 1
            if cfg.get("precio_mayoreo", 0) > 0:
                filas[r_idx][5] = f"{cfg['precio_mayoreo']:,.2f}"
            if cfg.get("cant_mayoreo", 0) > 0:
                filas[r_idx][6] = f"{cfg['cant_mayoreo']:g}"

        return actualizados

    @staticmethod
    def guardar_historial(db, tipo_carne: str, estado_promedio: dict, prov: str, fecha_str: str):
        """
        Guarda el historial en la base de datos SQL.
        """
        import json
        try:
            kilos = float(estado_promedio.get("kilos") or 0)
            precio = float(estado_promedio.get("precio") or 0)
            if kilos == 0 or precio == 0:
                return False

            datos_json = json.dumps(estado_promedio.get("filas", []))

            db.execute_non_query(
                "INSERT INTO historial_promedios (tipo_carne, fecha_guardado, proveedor, kilos_base, precio_kg_base, datos_json) VALUES (?, ?, ?, ?, ?, ?)",
                (tipo_carne, fecha_str, prov, kilos, precio, datos_json)
            )
            return True
        except Exception as e:
            print("Error al guardar historial:", e)
            return False

    @staticmethod
    def obtener_historial(db, tipo_carne: str):
        """
        Lee el historial de la BD.
        """
        import json

        try:
            # Create table if not exists just in case (hot patch)
            db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS historial_promedios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_carne TEXT, fecha_guardado TEXT, proveedor TEXT, kilos_base REAL, precio_kg_base REAL, datos_json TEXT
                )
            """)

            historial = db.execute_query(
                "SELECT id, fecha_guardado as fecha, proveedor, kilos_base as kilos, precio_kg_base as precio, datos_json FROM historial_promedios WHERE tipo_carne = ? ORDER BY id DESC LIMIT 50",
                (tipo_carne,)
            )

            resultados = []
            if historial:
                for row in historial:
                    try:
                        row['filas'] = json.loads(row['datos_json'])
                        resultados.append(row)
                    except: pass
            return resultados
        except Exception as e:
            print("Error al cargar historial:", e)
            return []
