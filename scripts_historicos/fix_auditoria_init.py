import codecs
text = codecs.open('src/jefe/reportes/vista_auditoria.py', 'r', encoding='utf-8').read()
text = text.replace('self.cargar_datos("Semana Actual")', '')
codecs.open('src/jefe/reportes/vista_auditoria.py', 'w', encoding='utf-8').write(text)
