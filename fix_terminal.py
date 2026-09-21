import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# 1. Update the search text format
pattern_text = r"item = QListWidgetItem\(f.*?Stock:.*?r\['id'\].*?\)"
replacement_text = '''item = QListWidgetItem(f"{r['nombre']} - ")
                # Hacemos la fuente mas grande para enfoque total
                font = item.font()
                font.setPointSize(18)
                font.setBold(True)
                item.setFont(font)'''

if re.search(pattern_text, code, re.DOTALL):
    code = re.sub(pattern_text, replacement_text, code)

# 2. Update list_results styling and event filter
pattern_init = r'self\.list_results\.installEventFilter\(self\)'
replacement_init = '''self.list_results.installEventFilter(self)
        self.list_results.setStyleSheet("""
            QListWidget {
                border: 2px solid #3B82F6;
                border-radius: 8px;
                background-color: #F8FAFC;
                color: #0F172A;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E2E8F0;
            }
            QListWidget::item:selected {
                background-color: #3B82F6;
                color: white;
            }
        """)'''

if re.search(pattern_init, code):
    code = re.sub(pattern_init, replacement_init, code)


# 3. Add Key_Down and Key_Up support to txt_scan eventFilter
pattern_filter = r'(elif key == Qt\.Key_Escape:)'
replacement_filter = '''elif key == Qt.Key_Down:
                    if self.list_results.isVisible() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(0)
                        return True
                elif key == Qt.Key_Up:
                    if self.list_results.isVisible() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(self.list_results.count() - 1)
                        return True
                \g<1>'''

if re.search(pattern_filter, code):
    code = re.sub(pattern_filter, replacement_filter, code)

# 4. Make the popup window much bigger in _layout_list_results_popup
pattern_layout = r'metrics\["list_results_w"\],\s*metrics\["list_results_h"\],'
replacement_layout = '''int(metrics["list_results_w"] * 1.5),
            int(metrics["list_results_h"] * 2.0),'''

if re.search(pattern_layout, code):
    code = re.sub(pattern_layout, replacement_layout, code)
    
# Adjust the Y position of popup to account for bigger height
pattern_y = r'popup_y = self\.dashboard_frame\.y\(\) - metrics\["list_results_h"\] - scale_px\(8, metrics\["layout_scale"\]\)'
replacement_y = 'popup_y = self.dashboard_frame.y() - int(metrics["list_results_h"] * 2.0) - scale_px(8, metrics["layout_scale"])'

if re.search(pattern_y, code):
    code = re.sub(pattern_y, replacement_y, code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Applied bisturi fixes!")
