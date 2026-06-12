import codecs
import re

text = codecs.open('src/main_window.py', 'r', encoding='utf-8').read()

# 1. Add the import
text = text.replace('from src.jefe.jefe0_dashboard import Jefe0Dashboard', 'from src.jefe.jefe0_dashboard import Jefe0Dashboard\nfrom src.carteleria.carteleria_main import CarteleriaMain')

# 2. Add it to _setup_ui
setup_replacement = '''self.jefe_dashboard = Jefe0Dashboard()
        self.jefe_dashboard.request_screen.connect(self._mostrar_pantalla_jefe)
        self.jefe_dashboard.request_tab.connect(self._navegar_tab_jefe)
        self.jefe_dashboard.request_logout.connect(self._do_logout)
        self.stack.addWidget(self.jefe_dashboard)

        self.carteleria = CarteleriaMain()
        self.carteleria.request_logout.connect(self._do_logout)
        self.stack.addWidget(self.carteleria)'''
text = text.replace('''self.jefe_dashboard = Jefe0Dashboard()
        self.jefe_dashboard.request_screen.connect(self._mostrar_pantalla_jefe)
        self.jefe_dashboard.request_tab.connect(self._navegar_tab_jefe)
        self.jefe_dashboard.request_logout.connect(self._do_logout)
        self.stack.addWidget(self.jefe_dashboard)''', setup_replacement)

# 3. Add the routing logic in _mostrar_perfil
mostrar_replacement = '''elif rol == 'jefe':
            self._current_profile = 'jefe'
            self._nav_bar.setVisible(False)
            self._nav_jefe.setVisible(False)
            self.jefe_dashboard.cargar_datos()
            self.stack.setCurrentWidget(self.jefe_dashboard)
            
        elif rol == 'carteleria':
            self._current_profile = 'carteleria'
            self._nav_bar.setVisible(False)
            self._nav_jefe.setVisible(False)
            if hasattr(self, 'top_bar_v3'):
                self.top_bar_v3.setVisible(False)
            self.carteleria.cargar_datos()
            self.stack.setCurrentWidget(self.carteleria)'''
text = text.replace('''elif rol == 'jefe':
            self._current_profile = 'jefe'
            self._nav_bar.setVisible(False)
            self._nav_jefe.setVisible(False)
            self.jefe_dashboard.cargar_datos()
            self.stack.setCurrentWidget(self.jefe_dashboard)''', mostrar_replacement)

codecs.open('src/main_window.py', 'w', encoding='utf-8').write(text)
print('main_window.py updated successfully!')
