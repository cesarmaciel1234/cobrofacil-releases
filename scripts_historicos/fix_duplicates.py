import codecs

with codecs.open('src/jefe/contabilidad/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = """            # Espaciador
            spacer = QListWidgetItem("")
            spacer.setFlags(Qt.NoItemFlags)
            self.nav_list.addItem(spacer)
            
            self.add_nav_item("Promedios", 13)
            
            # Espaciador
            spacer = QListWidgetItem("")
            spacer.setFlags(Qt.NoItemFlags)
            self.nav_list.addItem(spacer)
            
            self.add_nav_item("Promedios", 13)"""

good_block = """            # Espaciador
            spacer = QListWidgetItem("")
            spacer.setFlags(Qt.NoItemFlags)
            self.nav_list.addItem(spacer)
            
            self.add_nav_item("Promedios", 13)"""

content = content.replace(bad_block, good_block)

with codecs.open('src/jefe/contabilidad/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing duplicates")
