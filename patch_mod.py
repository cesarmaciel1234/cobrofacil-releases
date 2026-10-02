with open('modularizacion.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_rule = '''
## Aislamiento de Perfiles (Motores de Transporte)

1. **Sin cruce directo de datos:** Ningún perfil (Jefe, Cajero, Admin) debe leer la memoria o el estado en vivo de otro perfil directamente.
2. **Motores de transporte:** Si un módulo genera información que otro necesita (ej. *Promedios* genera precios para el *Cajero*), deben comunicarse enviando los datos a un "Motor de Transporte" (ej. el Motor de Base de Datos, Motor Mayoreo, etc.).
3. **Resiliencia:** Si el motor de un perfil colapsa o entra en error, los demás perfiles deben seguir operando con normalidad leyendo la última verdad consolidada desde el motor de transporte. Nunca acoplar las interfaces.
'''

if 'Aislamiento de Perfiles' not in content:
    content += new_rule
    with open('modularizacion.md', 'w', encoding='utf-8') as f:
        f.write(content)
