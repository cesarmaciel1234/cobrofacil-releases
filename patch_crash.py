import re

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(m):
    return '''                it_oferta = self._prom_tabla.item(r, 5)
                oferta_str = it_oferta.text().replace(',','').strip() if it_oferta else ""
                it_cant = self._prom_tabla.item(r, 6)
                cant_may_str = it_cant.text().replace(',','').strip() if it_cant else ""'''

content = re.sub(
    r'                oferta_str = self\._prom_tabla\.item\(r, 5\)\.text\(\)\.replace\(\',\',\s*\'\'\)\.strip\(\)\n                cant_may_str = self\._prom_tabla\.item\(r, 6\)\.text\(\)\.replace\(\',\',\s*\'\'\)\.strip\(\)',
    repl,
    content
)

def repl_save(m):
    return '''            row_data = [self._prom_tabla.item(r, c).text() if self._prom_tabla.item(r, c) else "" for c in range(11)]'''

content = re.sub(
    r'            row_data = \[self\._prom_tabla\.item\(r, c\)\.text\(\) if self\._prom_tabla\.item\(r, c\) else "" for c in range\(9\)\]',
    repl_save,
    content
)

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
