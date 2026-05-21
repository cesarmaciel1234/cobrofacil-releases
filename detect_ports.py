import serial.tools.list_ports

def check_ports():
    ports = list(serial.tools.list_ports.comports())
    print("--- PUERTOS COM DETECTADOS ---")
    found_port = None
    for p in ports:
        print(f"Port: {p.device} | Desc: {p.description}")
        if "USB" in p.description or "Serial" in p.description:
            found_port = p.device
    
    if found_port:
        print(f"Probable Port: {found_port}")
    else:
        print("No USB-Serial ports detected.")

if __name__ == "__main__":
    check_ports()
