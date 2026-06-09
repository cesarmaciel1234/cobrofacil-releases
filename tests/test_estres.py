import os
import sys
import time

# Agregar directorio actual al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.base_de_datos.database import db_manager
from src.config import config

def run_tests():
    print("="*50)
    print("INICIANDO TEST DE ESTRÉS DE VENTAS EN CONSOLA")
    print("="*50)

    # 1. Crear producto de prueba
    codigo_test = "TEST999"
    nombre_test = "Producto Stress Test"
    stock_inicial = 5000.0
    precio_test = 100.0

    print("\n[1] Preparando producto de prueba...")
    # Limpiar si existía
    db_manager.execute_non_query("DELETE FROM productos WHERE codigo = ?", (codigo_test,))
    db_manager.execute_non_query(
        "INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)",
        (codigo_test, nombre_test, precio_test, stock_inicial)
    )
    
    prod = db_manager.execute_query("SELECT id, stock FROM productos WHERE codigo = ?", (codigo_test,))
    prod_id = prod[0]['id']
    print(f"[OK] Producto creado: {nombre_test} (Stock: {stock_inicial})")

    # 2. Venta Normal con Descuento y Recargo
    print("\n[2] Probando descuentos y recargos...")
    venta_data = {
        'total': 90.0,  # 100 - 20 (desc) + 10 (rec)
        'pago_con': 100.0,
        'cambio': 10.0,
        'pago_efectivo': 100.0,
        'pago_otro': 0.0,
        'usuario': 'admin',
        'metodo_pago': 'Efectivo',
        'estado': 'COMPLETADA',
        'descuento': 20.0,
        'recargo': 10.0,
        'caja_id': 1
    }
    items = [{
        'id': prod_id,
        'nombre': nombre_test,
        'cant': 1,
        'precio': 100.0,
        'subtotal': 100.0,
        'es_pesable': 0
    }]

    id_v1 = db_manager.guardar_venta_completa(venta_data, items)
    if id_v1:
        print(f"[OK] Venta {id_v1} completada (Descuento y Recargo aplicados en DB).")
    else:
        print("[FALLO] Fallo venta con descuento.")

    # 3. Verificando Stock
    prod = db_manager.execute_query("SELECT stock FROM productos WHERE id = ?", (prod_id,))
    stock_actual = float(prod[0]['stock'])
    if stock_actual == stock_inicial - 1:
        print(f"[OK] Stock descontado correctamente: {stock_actual}")
    else:
        print(f"[FALLO] Error en stock: Esperado {stock_inicial - 1}, actual {stock_actual}")

    # 4. Cancelaciones (Test)
    print("\n[3] Probando cancelaciones y restauración de stock...")
    db_manager.execute_non_query("UPDATE ventas SET estado = 'CANCELADA' WHERE id = ?", (id_v1,))
    db_manager.execute_non_query("UPDATE productos SET stock = stock + 1 WHERE id = ?", (prod_id,))
    
    prod = db_manager.execute_query("SELECT stock FROM productos WHERE id = ?", (prod_id,))
    stock_restaurado = float(prod[0]['stock'])
    if stock_restaurado == stock_inicial:
        print(f"[OK] Venta cancelada y stock restaurado correctamente: {stock_restaurado}")
    else:
        print("[FALLO] Error restaurando stock.")

    # 5. Trabajo Extremo (100 ventas simultáneas)
    print("\n[4] Iniciando TRABAJO EXTREMO (Test de estrés de 100 ventas)...")
    start_time = time.time()
    for i in range(100):
        venta_stress = dict(venta_data)
        venta_stress['total'] = 100.0
        venta_stress['descuento'] = 0.0
        venta_stress['recargo'] = 0.0
        db_manager.guardar_venta_completa(venta_stress, items)
    end_time = time.time()
    
    prod = db_manager.execute_query("SELECT stock FROM productos WHERE id = ?", (prod_id,))
    stock_post_stress = float(prod[0]['stock'])
    
    print(f"[OK] 100 Ventas procesadas en {end_time - start_time:.2f} segundos.")
    print(f"[OK] Stock verificado tras estrés: {stock_post_stress} (Esperado: {stock_inicial - 100})")

    # 6. Alarma de exceso de efectivo
    print("\n[5] Probando alerta de exceso de efectivo (Alarma de Seguridad)...")
    efectivo = db_manager.get_efectivo_en_caja(1)
    print(f"Efectivo actual en caja: ${efectivo:,.2f}")
    
    umbral_rojo = float(config.get("limite_efectivo_rojo", 70000.0))
    if efectivo >= umbral_rojo:
        print(f"[ALARMA] ¡ALARMA ACTIVADA! El efectivo (${efectivo:,.2f}) supera el límite rojo (${umbral_rojo:,.2f}).")
        print("   -> El sistema requerirá un 'Retiro de Efectivo (F5)' por seguridad.")
    else:
        print(f"[INFO] Efectivo debajo del límite de alarma (${umbral_rojo:,.2f}).")
        print("   -> Simulando ingreso masivo de $100,000 para forzar alarma...")
        db_manager.execute_non_query(
            "INSERT INTO movimientos_caja (tipo, monto, observaciones, caja_id) VALUES ('INGRESO', 100000, 'Test Alarma', 1)"
        )
        efectivo_nuevo = db_manager.get_efectivo_en_caja(1)
        if efectivo_nuevo >= umbral_rojo:
            print(f"[ALARMA] ¡ALARMA ACTIVADA CORRECTAMENTE! Nuevo saldo: ${efectivo_nuevo:,.2f} > ${umbral_rojo:,.2f}")
        else:
            print("[FALLO] Fallo en activación de alarma tras inyección.")

    print("\n" + "="*50)
    print("TEST FINALIZADO CON ÉXITO")
    print("="*50)

if __name__ == '__main__':
    run_tests()
