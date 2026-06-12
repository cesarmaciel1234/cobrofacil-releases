import codecs
import re

text = codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'r', encoding='utf-8').read()

match = re.search(r'(# ── CONSTANTES Y PALETA .*?)(?=\nclass JefeContabilidad)', text, re.DOTALL)
if match:
    globals_code = match.group(1)
    
    with codecs.open('src/jefe/contabilidad/shared_globals.py', 'w', encoding='utf-8') as f:
        f.write('from src.utils.paths import get_base_path\nimport os\n')
        f.write('def get_jefe_db_path():\n    return os.path.join(get_base_path(), "db", "base_de_datos.db")\n')
        f.write('DB_PATH = get_jefe_db_path()\n\n')
        f.write(globals_code)
    
    text = text.replace(globals_code, 'from src.jefe.contabilidad.shared_globals import *\n')
    codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'w', encoding='utf-8').write(text)
    print('Created shared_globals.py')
else:
    print('Match not found')
