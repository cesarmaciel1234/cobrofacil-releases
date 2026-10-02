import re

with open('src/cerebro_global/proveedor/motor_proveedor.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('    def get_proveedores_unicos', '    def get_proveedores_unicos_OLD')
content = content.replace('    def load_proveedores', '    def load_proveedores_OLD')

