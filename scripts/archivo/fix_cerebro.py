import codecs
import re

path = 'src/cerebro_global/nexus_cerebro.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

pattern = r'''    @staticmethod\s*def ejecutar_query\(q, p\):\s*from src\.base_de_datos\.database import db_manager\s*return db_manager\.execute_query\(q, p\)\s*@staticmethod\s*def ejecutar_escalar\(q, p\):\s*from src\.base_de_datos\.database import db_manager\s*return db_manager\.execute_scalar\(q, p\)'''

# The pattern appears twice at the end of the file.
# Let's just find the last occurrence and remove it, or replace the whole block if it appears twice sequentially.
code = re.sub(pattern + r'\s*' + pattern, pattern, code, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)
print("Duplicate functions removed")
