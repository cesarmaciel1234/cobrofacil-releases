import codecs
import re

path = 'src/cajero/paso6_cobro/componentes_paso6_cobro/selector_metodo_pago.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# Fix dark hover
code = re.sub(r'QFrame:hover {\s*background: #334155;\s*border-color: #3B82F6;\s*margin-top: 0px;\s*margin-bottom: 4px;\s*}', 
              r'''QFrame:hover {
                    background: #334155;
                    border-color: #475569;
                    margin-top: 0px;
                    margin-bottom: 4px;
                }''', code)

# Fix light hover
code = re.sub(r'QFrame:hover {\s*background: #F8FAFC;\s*border-color: #3B82F6;\s*margin-top: 0px;\s*margin-bottom: 4px;\s*}', 
              r'''QFrame:hover {
                    background: #F8FAFC;
                    border-color: #E2E8F0;
                    margin-top: 0px;
                    margin-bottom: 4px;
                }''', code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("CSS fixed!")
