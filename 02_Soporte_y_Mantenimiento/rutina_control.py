import sys
import os
import time
import logging

# Configuración de rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

try:
    from src.base_de_datos.database import db_manager
    from src.hardware.printer import printer_manager
    from src.hardware.cash_drawer import drawer_manager
    from src.config import config
except ImportError:
    print("❌ Error: No se encontraron los módulos de src. Ejecuta desde la raíz del proyecto.")
    sys.exit(1)

def ejecutar_rutina():
    print("="*50)
    print("🚀 RUTINA DE CONTROL - Cobro Fácil POS")
    print("="*50)
    
    # 1. Verificar Base de Datos
    print("\n[1/4] Verificando Base de Datos...")
    try:
        res = db_manager.execute_query("SELECT COUNT(*) as total FROM productos")
        print(f"✅ DB Conectada. Productos en catálogo: {res[0]['total']}")
    except Exception as e:
        print(f"❌ Error en DB: {e}")

    # 2. Verificar Impresora
    print("\n[2/4] Verificando Impresora (COM3)...")
    ok, msg = printer_manager.verificar_estado()
    if ok:
        print(f"✅ Impresora lista: {msg}")
    else:
        print(f"⚠️ Aviso de Impresora: {msg}")

    # 3. Test de Apertura de Cajón (Pulso 200ms)
    print("\n[3/4] Probando apertura de cajón...")
    print("   (El cajón debería saltar ahora)")
    try:
        drawer_manager.abrir(autorizada=True)
        print("✅ Pulso de apertura enviado con éxito.")
    except Exception as e:
        print(f"❌ Error al abrir cajón: {e}")

    # 4. Simulación de Flujo de Venta (Lógica Paso 5 -> 6)
    print("\n[4/4] Validando integridad de flujo de venta...")
    try:
        test_item = [{"id": "000", "nombre": "TEST RUTINA", "precio": 10.0, "cant": 1, "subtotal": 10.0}]
        venta = {
            'total': 10.0, 'pago_con': 10.0, 'cambio': 0.0,
            'pago_efectivo': 10.0, 'pago_otro': 0.0,
            'usuario': 'SISTEMA_RUTINA', 'metodo_pago': 'Efectivo',
            'estado': 'TEST'
        }
        id_v = db_manager.guardar_venta_completa(venta, test_item)
        if id_v:
            print(f"✅ Flujo de venta validado (ID Venta Test: {id_v})")
            # Limpiar test (tabla correcta: detalles_ventas)
            db_manager.execute_non_query("DELETE FROM detalles_ventas WHERE id_venta = ?", (id_v,))
            db_manager.execute_non_query("DELETE FROM ventas WHERE id = ?", (id_v,))
        else:
            print("❌ Error: No se pudo registrar la venta de prueba.")
    except Exception as e:
        print(f"❌ Error en simulación de flujo: {e}")

    print("\n" + "="*50)
    print("🏁 RUTINA FINALIZADA")
    print("="*50)

if __name__ == "__main__":
    ejecutar_rutina()
