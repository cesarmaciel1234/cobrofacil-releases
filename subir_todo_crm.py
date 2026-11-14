"""Sube toda la base de datos (todas las tablas y clientes) a Render."""
import os
import sys
import time

from src.central_red_global.servidor.crm_salida.proceso import ruta_punpro
from src.central_red_global.servidor.crm_salida.vigilante import leer_credenciales
from src.central_red_global.servidor.crm_salida.motor import (
    entrar,
    leer_clientes,
    enviar,
    subir_base,
)


def main():
    creds = leer_credenciales()
    if not creds:
        print("ERROR: No se encontraron credenciales válidas en config.json")
        return 1

    url = creds["url"]
    usuario = creds.get("usuario")
    password = creds.get("password")
    clave = creds.get("clave")
    empresa = creds.get("empresa")
    sucursal_id = creds.get("sucursal_id") or "1"
    sucursal = creds.get("sucursal") or "Casa Central"
    db_path = ruta_punpro()

    print(f"=== INICIANDO SUBIDA TOTAL AL CRM ===")
    print(f"Destino:     {url}")
    print(f"Empresa:     {empresa}")
    print(f"Sucursal:    [{sucursal_id}] {sucursal}")
    print(f"Base local:  {db_path} ({os.path.getsize(db_path) / 1024 / 1024:.2f} MB)")
    print("=" * 37)

    opener = None
    empresa_id = creds.get("empresa_id")

    if usuario and password:
        print(f"Iniciando sesión en Render con usuario '{usuario}'...")
        opener, emp_login = entrar(url, usuario, password, timeout=60)
        if emp_login:
            empresa_id = emp_login
        print(f"✓ Sesión iniciada con éxito. Empresa ID: {empresa_id}")

    # 1. Enviar clientes y cartera
    print("\n[1/2] Sincronizando cartera de clientes...")
    clientes = leer_clientes(db_path)
    print(f"Leídos {len(clientes)} clientes de la base local.")
    res_cartera = enviar(
        url,
        clave,
        clientes,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        sucursal=sucursal,
        opener=opener,
        timeout=120,
    )
    print(f"✓ Cartera sincronizada: {res_cartera.get('mensaje', 'OK')} (Total: {len(clientes)})")

    # 2. Enviar todas las tablas de la base
    print("\n[2/2] Subiendo todas las tablas de la base de datos...")
    def reentrar():
        print("Renovando sesión...", flush=True)
        nuevo_opener, _ = entrar(url, usuario, password, timeout=60)
        return nuevo_opener

    inicio = time.time()
    res_base = subir_base(
        url,
        clave,
        db_path,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        sucursal=sucursal,
        opener=opener,
        timeout=120,
        reentrar=reentrar if usuario and password else None,
    )
    duracion = time.time() - inicio

    print("\n" + "=" * 37)
    print("=== RESULTADO DE LA SUBIDA TOTAL ===")
    print(f"Tablas subidas con éxito: {res_base.get('tablas')}")
    print(f"Total de filas subidas:   {res_base.get('filas')}")
    print(f"Tiempo total:             {duracion:.1f} segundos")
    if res_base.get("errores"):
        print(f"Errores encontrados ({len(res_base['errores'])}):")
        for err in res_base["errores"]:
            print(f"  - {err}")
    else:
        print("✓ ¡Toda la base de datos se subió perfectamente sin ningún error!")
    print("=" * 37)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
