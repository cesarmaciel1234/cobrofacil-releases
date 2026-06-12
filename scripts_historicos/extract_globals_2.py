import codecs

text = codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'r', encoding='utf-8').read()

idx_start = text.find('PAL = {')
idx_end = text.find('from src.jefe.contabilidad.vista_resumen') # Where the mixins start

if idx_start != -1 and idx_end != -1:
    code = text[idx_start:idx_end]
    
    with codecs.open('src/jefe/contabilidad/shared_globals.py', 'w', encoding='utf-8') as f:
        f.write('from PyQt5.QtWidgets import *\nfrom PyQt5.QtCore import *\nfrom PyQt5.QtGui import *\nimport os\nfrom src.utils.paths import get_base_path\n')
        f.write(code)
    
    # Replace in jefe_contabilidad
    text = text.replace(code, 'from src.jefe.contabilidad.shared_globals import *\n')
    codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'w', encoding='utf-8').write(text)
    
    # Update all mixins
    import os as py_os
    import re
    for file in py_os.listdir('src/jefe/contabilidad'):
        if file.startswith('vista_') and file.endswith('.py'):
            t = codecs.open('src/jefe/contabilidad/'+file, 'r', encoding='utf-8').read()
            t = re.sub(r'from src\.jefe\.contabilidad\.styles import PAL.*?\n', 'from src.jefe.contabilidad.shared_globals import *\n', t)
            codecs.open('src/jefe/contabilidad/'+file, 'w', encoding='utf-8').write(t)
    print('Globals extracted successfully!')
else:
    print('Indexes not found', idx_start, idx_end)
