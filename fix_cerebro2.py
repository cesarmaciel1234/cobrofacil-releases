import codecs

path = 'src/cerebro_global/nexus_cerebro.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

dup = '''    @staticmethod
    def ejecutar_query(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, p)

    @staticmethod
    def ejecutar_escalar(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_scalar(q, p)

    @staticmethod
    def ejecutar_query(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, p)

    @staticmethod
    def ejecutar_escalar(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_scalar(q, p)'''

single = '''    @staticmethod
    def ejecutar_query(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, p)

    @staticmethod
    def ejecutar_escalar(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_scalar(q, p)'''

if dup in code:
    code = code.replace(dup, single)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed duplicate functions")
else:
    print("Duplicates not found")
