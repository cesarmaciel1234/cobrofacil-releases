def traducir(paquete: dict) -> bytes:
    """
    Toma un paquete abstracto y lo traduce a bytes (ej. comandos ESC/POS).
    """
    buffer = bytearray()
    
    # Simulación de traducción
    lineas = paquete.get("lineas", [])
    for linea in lineas:
        buffer.extend(linea.encode('utf-8'))
        buffer.extend(b'\n')
    
    if paquete.get("abrir_cajon", False):
        buffer.extend(b'\x1b\x70\x00\x19\xff') # Comando ESC/POS para cajón
        
    if paquete.get("cortar_papel", False):
        buffer.extend(b'\x1d\x56\x00') # Comando ESC/POS para corte
        
    return bytes(buffer)
