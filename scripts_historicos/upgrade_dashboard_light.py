import codecs
import re

text = codecs.open('src/jefe/jefe0_dashboard.py', 'r', encoding='utf-8').read()

# Replace palette import and usage
text = text.replace('L = {', 'from src.jefe.theme_pro import THEME_PRO as L\n# L = {')

# Adjust Hero gradient to be an ultra-premium Light Mode gradient (Glass/Mesh style)
hero_replacement = '''QFrame#JefeHero {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0.00 #818CF8,
                    stop:0.45 #C084FC,
                    stop:0.80 #F472B6,
                    stop:1.00 #FB923C
                );
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }'''
text = re.sub(r'QFrame#JefeHero \{.*?\}', hero_replacement, text, flags=re.DOTALL)

# Tweak the shadows on JefeCard to be softer and more premium
text = text.replace('self._sh.setColor(QColor(r, g, b, 35))', 'self._sh.setColor(QColor(r, g, b, 25))')
text = text.replace('self._sh.setBlurRadius(20)', 'self._sh.setBlurRadius(30)')
text = text.replace('self._sh.setBlurRadius(28)', 'self._sh.setBlurRadius(40)')
text = text.replace('border-radius: 20px;', 'border-radius: 24px;')

# Upgrade the Brand text
text = text.replace("color:#6366F1;", "color: #C084FC;") # Make the 2026 match the purple gradient

# Update the overall theme
text = text.replace("font-family: 'Segoe UI', 'Outfit', sans-serif;", "font-family: 'Inter', 'Segoe UI', sans-serif;")

codecs.open('src/jefe/jefe0_dashboard.py', 'w', encoding='utf-8').write(text)
print('Dashboard updated to Ultra-Premium Light Mode!')
