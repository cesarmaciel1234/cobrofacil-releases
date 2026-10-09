"""
prueba_contabilidad.py - Script de prueba para aprendizaje contable
TPV Pro 2026 · Cobro Fácil POS

Este script permite probar el flujo completo:
1. Crear venta con IVA 21%
2. Ver asiento contable generado automáticamente
3. Ver comprobante fiscal
4. Liquidar IVA del período

Uso: python src/contabilidad/prueba_contabilidad.py
"""

import sys
import os
from datetime import date

# Agregar ruta al proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def prueba_completa():
    """Prueba completa del flujo contable"""
    print("=" * 60)
    print("PRUEBA DE CONTABILIDAD - APRENDIZAJE")
    print("=" * 60)
    
    try:
        from src.contabilidad.database import Database
        from src.utils.paths import get_base_path
        
        # Ruta de la base de datos
        db_path = os.path.join(get_base_path(), "data", "contabilidad_jefe.db")
        
        print(f"\nBase de datos: {db_path}")
        print(f"Existe: {'Si' if os.path.exists(db_path) else 'No'}")
        
        # Inicializar base de datos
        print("\nInicializando Database...")
        db = Database(db_path)
        
        # Verificar modo enterprise
        print(f"Modo Enterprise: {'ACTIVO' if db.is_enterprise_mode() else 'NO ACTIVO'}")
        
        if not db.is_enterprise_mode():
            print("\nEl modo enterprise no esta activado.")
            print("   Esto puede ser porque faltan dependencias o hay un error de importacion.")
            print("   El sistema funcionara en modo legacy (sin asientos contables).")
            return
        
        # Cargar plan de cuentas por defecto
        print("\nCargando plan de cuentas por defecto...")
        db.cargar_plan_cuentas_defecto()
        print("   Plan de cuentas cargado")
        
        # Mostrar algunas cuentas
        print("\nEjemplo de cuentas del plan:")
        cuentas = db.get_plan_cuentas(tipo="activo")
        for cuenta in cuentas[:5]:
            print(f"   • {cuenta['codigo']}: {cuenta['nombre']}")
        
        # Crear una venta de prueba
        print("\nCreando venta de prueba...")
        from datetime import datetime
        
        venta_fecha = date.today()
        venta_monto = 100.0  # $100
        metodo_pago = "Efectivo"
        iva_tasa = 21.0
        
        print(f"   Fecha: {venta_fecha}")
        print(f"   Monto total: ${venta_monto}")
        print(f"   Metodo: {metodo_pago}")
        print(f"   IVA: {iva_tasa}%")
        
        # Calcular desglose IVA
        monto_gravado = venta_monto / (1 + iva_tasa / 100)
        monto_iva = venta_monto - monto_gravado
        
        print(f"\n   Desglose IVA:")
        print(f"      Monto gravado (neto): ${monto_gravado:.2f}")
        print(f"      IVA ({iva_tasa}%): ${monto_iva:.2f}")
        print(f"      Total: ${venta_monto:.2f}")
        
        # Generar asiento contable
        print("\nGenerando asiento contable...")
        from src.contabilidad.motor_asientos import MotorAsientos
        
        motor = MotorAsientos(db_path)
        exito, mensaje, asiento_id = motor.generar_asiento_venta(
            fecha=venta_fecha,
            monto_total=venta_monto,
            metodo_pago=metodo_pago,
            iva_tasa=iva_tasa,
            costo_mercaderia=0.0,
            referencia="PRUEBA-001"
        )
        
        if exito:
            print(f"   {mensaje}")
            print(f"   ID de asiento: {asiento_id}")
        else:
            print(f"   Error: {mensaje}")
            return
        
        # Ver el asiento en el mayor
        print("\nAsiento en el Mayor General:")
        mayor = motor.obtener_mayor_general(desde=venta_fecha, hasta=venta_fecha)
        
        for fila in mayor:
            tipo_cuenta = fila.get('cuenta_nombre', '')
            debe = fila.get('debe', 0)
            haber = fila.get('haber', 0)
            
            if debe > 0:
                print(f"   DEBE: {tipo_cuenta} - ${debe:.2f}")
            if haber > 0:
                print(f"   HABER: {tipo_cuenta} - ${haber:.2f}")
        
        # Generar comprobante fiscal
        print("\nGenerando comprobante fiscal...")
        from src.contabilidad.integracion_iva import IntegradorIVA
        
        integrador = IntegradorIVA(db_path)
        exito, mensaje, comp_id = integrador.generar_comprobante_fiscal_venta(
            num_venta=1,
            items=[{"id": "001", "subtotal": venta_monto}],
            total=venta_monto,
            metodo_pago=metodo_pago
        )
        
        if exito:
            print(f"   {mensaje}")
            print(f"   ID de comprobante: {comp_id}")
        else:
            print(f"   {mensaje}")
        
        # Ver balance general
        print("\nBalance General actual:")
        balance = db.get_balance_general(venta_fecha)
        
        print(f"   Total Activos: ${balance.get('total_activos', 0):,.2f}")
        print(f"   Total Pasivos: ${balance.get('total_pasivos', 0):,.2f}")
        print(f"   Total Patrimonio: ${balance.get('total_patrimonio', 0):,.2f}")
        print(f"   Cuadra: {'Si' if balance.get('cuadra', False) else 'No'}")
        
        # Ver estado de resultados
        print("\nEstado de Resultados (mes actual):")
        desde = date.today().replace(day=1)
        hasta = date.today()
        
        er = db.get_estado_resultados(desde, hasta)
        
        print(f"   Total Ingresos: ${er.get('total_ingresos', 0):,.2f}")
        print(f"   Total Gastos: ${er.get('total_gastos', 0):,.2f}")
        print(f"   Resultado Neto: ${er.get('resultado_neto', 0):,.2f}")
        
        print("\n" + "=" * 60)
        print("PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nSiguientes pasos para aprender:")
        print("   1. Ir a TPV -> Vender un producto del Almacen (IVA 21%)")
        print("   2. Ir a Jefe -> Contabilidad -> Impuestos")
        print("   3. Ver el asiento contable generado automaticamente")
        print("   4. Liquidar IVA del mes")
        print("   5. Ver el desglose por alicuota")
        print("\nDocumentacion:")
        print("   • COMPATIBILIDAD_IVA.md - Integracion IVA TPV <-> Contabilidad")
        print("   • README_ENTERPRISE.md - Modulos enterprise")
        
    except Exception as e:
        print(f"\nError en la prueba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    prueba_completa()
