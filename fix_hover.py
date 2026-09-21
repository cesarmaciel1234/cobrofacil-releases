import codecs

path = 'src/cajero/paso6_cobro/componentes_paso6_cobro/selector_metodo_pago.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

from_dark_hover = '''                    QFrame:hover {
                        background: #334155;
                        border-color: #3B82F6;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }'''
to_dark_hover = '''                    QFrame:hover {
                        background: #334155;
                        border-color: #475569;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }'''

from_light_hover = '''                    QFrame:hover {
                        background: #F8FAFC;
                        border-color: #3B82F6;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }'''
to_light_hover = '''                    QFrame:hover {
                        background: #F8FAFC;
                        border-color: #E2E8F0;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }'''

code = code.replace(from_dark_hover, to_dark_hover)
code = code.replace(from_light_hover, to_light_hover)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Hover fixed!")
