with open('CobroFacil_POS.spec', 'r', encoding='utf-8') as f:
    content = f.read()

new_imports = '''        'src.cajero.paso6_cobro.vinculo_mp.libro',
        'src.jefe.promedios.promedios_main',
        'src.jefe.promedios.carne.ui_carne',
        'src.jefe.promedios.carne.motor_carne',
        'src.jefe.promedios.cerdo.ui_cerdo',
        'src.jefe.promedios.cerdo.motor_cerdo',
        'src.jefe.promedios.pollo.ui_pollo',
        'src.jefe.promedios.pollo.motor_pollo',
        'src.jefe.promedios.motor_global_promedios',
        'src.creador_pdf_global.motor_pdf_promedios',
        'src.motor_descuentos.mayoreo.motor',
'''

content = content.replace("'src.cajero.paso6_cobro.vinculo_mp.libro',", new_imports)

with open('CobroFacil_POS.spec', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated spec file')
