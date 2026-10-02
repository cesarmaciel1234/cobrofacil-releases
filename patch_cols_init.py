import re
with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(m):
    return '''                it_ganancia = QTableWidgetItem("0.00")
                it_ganancia.setFlags(it_ganancia.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, 8, it_ganancia)

                it_v_may = QTableWidgetItem("0.00")
                it_v_may.setFlags(it_v_may.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, 9, it_v_may)

                it_g_may = QTableWidgetItem("0.00")
                it_g_may.setFlags(it_g_may.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, 10, it_g_may)'''

content = re.sub(
    r'                it_ganancia = QTableWidgetItem\("0\.00"\)\n                it_ganancia\.setFlags\(it_ganancia\.flags\(\) & ~Qt\.ItemFlag\.ItemIsEditable\)\n                self\._prom_tabla\.setItem\(i, 8, it_ganancia\)',
    repl,
    content
)

def repl2(m):
    return '''        it_ganancia = QTableWidgetItem("0.00")
        it_ganancia.setFlags(it_ganancia.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._prom_tabla.setItem(i, 8, it_ganancia)

        it_v_may = QTableWidgetItem("0.00")
        it_v_may.setFlags(it_v_may.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._prom_tabla.setItem(i, 9, it_v_may)

        it_g_may = QTableWidgetItem("0.00")
        it_g_may.setFlags(it_g_may.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._prom_tabla.setItem(i, 10, it_g_may)'''

content = re.sub(
    r'        it_ganancia = QTableWidgetItem\("0\.00"\)\n        it_ganancia\.setFlags\(it_ganancia\.flags\(\) & ~Qt\.ItemFlag\.ItemIsEditable\)\n        self\._prom_tabla\.setItem\(i, 8, it_ganancia\)',
    repl2,
    content
)

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
