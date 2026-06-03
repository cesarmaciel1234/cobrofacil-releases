import hashlib
import sys

def generar_llave(hwid):
    import datetime
    mes_actual = datetime.datetime.now().strftime("%Y-%m")
    secreto = f"{hwid}-{mes_actual}-ELITE2026-X"
    return "PRO-" + hashlib.md5(secreto.encode()).hexdigest()[:8].upper()

def main():
    print("=============================================")
    print("💎 GENERADOR DE LICENCIAS - CAJAFACIL PRO 2026")
    print("=============================================\n")
    print("⚠️ Este programa genera un TOKEN MENSUAL. Deberá enviar uno nuevo cada mes.\n")
    
    while True:
        hwid = input("Ingrese el ID DE MÁQUINA del cliente (o 'salir'): ").strip().upper()
        if hwid == "SALIR":
            break
            
        if not hwid:
            continue
            
        llave = generar_llave(hwid)
        import datetime
        mes_actual = datetime.datetime.now().strftime("%Y-%m")
        print("\n---------------------------------------------")
        print(f"✔️ TOKEN MENSUAL ({mes_actual}) GENERADO: {llave}")
        print("---------------------------------------------\n")

if __name__ == "__main__":
    main()
