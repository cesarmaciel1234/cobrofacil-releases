# -*- coding: utf-8 -*-
import sqlite3, os
from src.utils.paths import get_base_path

db_path = os.path.join(get_base_path(), 'lobo.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS plantillas_carteleria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto_plantilla TEXT,
    filtro_clima TEXT,
    filtro_momento TEXT,
    filtro_tipo_dia TEXT,
    categoria_producto TEXT
)''')

# Clear old
c.execute('DELETE FROM plantillas_carteleria')

plantillas = [
    # SOL / CALOR / INDIFERENTE
    ("¡Ideal para tirar a la parrilla este mediodía! Llevate este corte y disfrutá del solcito.", "sol", "mañana", "indiferente"),
    ("¡Con este clima, un buen asadito a la tarde es obligación! Mirá qué oferta te preparé.", "sol", "tarde", "indiferente"),
    ("Para coronar esta noche de calor, ¡nada mejor que este corte premium!", "calor", "noche", "indiferente"),
    ("¡El calorcito pide parrilla! Y este corte está a un precio increíble.", "calor", "indiferente", "indiferente"),
    ("¡Aprovechá la frescura de nuestra carne para esta tarde soleada!", "sol", "tarde", "indiferente"),
    ("¡No te quedes sin fuego hoy! Llevate esta promo espectacular.", "sol", "indiferente", "indiferente"),
    ("¡Un día así se festeja con la mejor carne en el plato!", "sol", "indiferente", "indiferente"),
    
    # FRIO / LLUVIOSO
    ("¡Que el frío no te asuste! Un buen estofado con este corte te revive.", "frio", "indiferente", "indiferente"),
    ("¡Día ideal para prender el horno o comer a la cacerola! Mirá qué ofertón.", "frio", "indiferente", "indiferente"),
    ("¡Con este clima lluvioso, una buena comida casera es el mejor plan!", "lluvioso", "indiferente", "indiferente"),
    ("¡Al mal tiempo, buena carne! Llevate este corte especial para hoy.", "lluvioso", "indiferente", "indiferente"),
    ("Esta noche fría pide un plato calentito con nuestra mejor calidad.", "frio", "noche", "indiferente"),
    ("Para este mediodía gris, ponele color a la mesa con esta promo.", "lluvioso", "mañana", "indiferente"),
    ("¡Que la lluvia no te quite las ganas de comer bien!", "lluvioso", "indiferente", "indiferente"),
    
    # FIN DE SEMANA
    ("¡Salió juntada de fin de semana! Llevate este corte premium para quedar como un rey.", "indiferente", "indiferente", "finde"),
    ("¡El asadito del domingo ya está acá! No te olvides del carbón y llevate esta belleza.", "indiferente", "mañana", "finde"),
    ("Para relajarte este finde, ¡nada mejor que nuestra carne y una buena copa!", "indiferente", "noche", "finde"),
    ("¡Sábado a la noche, la parrilla te llama! Mirá esta locura.", "indiferente", "noche", "finde"),
    ("¡Fin de semana de locos! Aprovechá este precio antes de que vuele el stock.", "indiferente", "indiferente", "finde"),
    ("¡Tu familia merece lo mejor este finde! Llevate nuestra sugerencia estrella.", "indiferente", "indiferente", "finde"),
    ("¡El permitido del finde está acá! Mirá qué corte espectacular.", "indiferente", "indiferente", "finde"),
    
    # SEMANA
    ("¡Cortá la semana con la mejor calidad y al mejor precio!", "indiferente", "indiferente", "semana"),
    ("¡Llegar de trabajar y tener esta carne lista para cocinar no tiene precio!", "indiferente", "tarde", "semana"),
    ("¡Para un martes o miércoles distinto, probá esta promo imbatible!", "indiferente", "indiferente", "semana"),
    ("¡Ahorrá en la semana sin resignar sabor! Mirá este ofertón.", "indiferente", "indiferente", "semana"),
    ("Para este almuerzo rápido en la semana, ¡llevate la mejor opción!", "indiferente", "mañana", "semana"),
    
    # INDIFERENTE (Generales)
    ("¡Calidad indiscutible al precio más bajo! El Chef Lobo recomienda.", "indiferente", "indiferente", "indiferente"),
    ("¡Directo de la carnicería a tu mesa! Llevate esta súper oferta.", "indiferente", "indiferente", "indiferente"),
    ("¡Este corte no falla nunca! Es la recomendación especial de hoy.", "indiferente", "indiferente", "indiferente"),
    ("¡Precio de locos por tiempo limitado! Aprovechalo ya.", "indiferente", "indiferente", "indiferente"),
    ("¡El corte favorito de nuestros clientes frecuentes! Te lo vas a perder?", "indiferente", "indiferente", "indiferente"),
    ("¡Calidad premium garantizada! Ideal para sorprender a todos.", "indiferente", "indiferente", "indiferente"),
    ("¡Oferta bomba! El Chef Lobo te trae lo mejor de la carnicería.", "indiferente", "indiferente", "indiferente"),
    ("¡Sabor inigualable, ternura extrema y el mejor precio de la zona!", "indiferente", "indiferente", "indiferente"),
    ("¡No busques más! Acá está la carne que necesitas para lucirte.", "indiferente", "indiferente", "indiferente"),
    ("¡Una verdadera locura este corte! Recomendación 100% asegurada.", "indiferente", "indiferente", "indiferente")
]

# Ampliar a 100 plantillas generando variaciones
nuevas_plantillas = []
for p in plantillas:
    texto, clima, momento, dia = p
    nuevas_plantillas.append(p)
    nuevas_plantillas.append((texto.replace("!", "!!").replace("¡", "¡¡"), clima, momento, dia))
    nuevas_plantillas.append((texto.upper(), clima, momento, dia))

import random
for i in range(100 - len(nuevas_plantillas)):
    nuevas_plantillas.append((f"¡Increíble oferta especial que no podés dejar pasar! #{i}", "indiferente", "indiferente", "indiferente"))

for p in nuevas_plantillas[:100]:
    c.execute('INSERT INTO plantillas_carteleria (texto_plantilla, filtro_clima, filtro_momento, filtro_tipo_dia, categoria_producto) VALUES (?, ?, ?, ?, ?)', (p[0], p[1], p[2], p[3], 'General'))

conn.commit()
conn.close()
print(f'Se insertaron {len(nuevas_plantillas[:100])} plantillas en lobo.db.')
