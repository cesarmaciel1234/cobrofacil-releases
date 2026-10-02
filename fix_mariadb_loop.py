import sys

with open('src/services/mariadb_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = "def start_server(self):"
replacement1 = "def start_server(self, _repair_attempt=0):"

target2 = "return self.start_server()"
replacement2 = '''if _repair_attempt > 2:
                                logger.error("No se pudo reparar la base de datos de manera automatica.")
                                return False
                            return self.start_server(_repair_attempt + 1)'''

if target1 in content and target2 in content:
    content = content.replace(target1, replacement1)
    content = content.replace(target2, replacement2)
    with open('src/services/mariadb_controller.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed mariadb_controller!")
else:
    print("Targets not found.")
