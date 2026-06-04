import sys

def main():
    path = r'src/admin/admin14_ventas_digitales.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject load_bank_dataframe
    helper_code = '''
def load_bank_dataframe(path: str):
    import pandas as pd
    try:
        if path.lower().endswith(('.xls', '.xlsx')):
            try:
                df = pd.read_excel(path, header=None)
            except Exception:
                try:
                    df = pd.read_html(path, decimal=',', thousands='.')[0]
                except Exception:
                    df = pd.read_csv(path, header=None, encoding='utf-8-sig', on_bad_lines='skip')
        else:
            df = pd.read_csv(path, header=None, encoding='utf-8-sig', on_bad_lines='skip', sep=None, engine='python')
            
        header_idx = 0
        max_kw = 0
        kws = {'fecha', 'date', 'importe', 'monto', 'amount', 'descripcion', 'concepto', 'detalle', 'estado', 'referencia', 'operacion'}
        
        for i, row in df.head(30).iterrows():
            rstr = ' '.join([str(x).lower() for x in row.values])
            m = sum(1 for k in kws if k in rstr)
            if m > max_kw and m >= 2:
                max_kw = m
                header_idx = i
                
        if max_kw >= 2:
            df.columns = [str(c).strip().lower() for c in df.iloc[header_idx].values]
            df = df.iloc[header_idx+1:].reset_index(drop=True)
        else:
            df.columns = [str(c).strip().lower() for c in df.iloc[0].values]
            df = df.iloc[1:].reset_index(drop=True)
            
        return df
    except Exception as e:
        print(f"Error load_bank_dataframe {path}: {e}")
        import pandas as pd
        return pd.DataFrame()

'''
    content = content.replace('# -----------------------------------------------------------------------------\n# Parser Mercado Pago CSV oficial', helper_code + '# -----------------------------------------------------------------------------\n# Parser Mercado Pago CSV oficial')

    # 2. Replace parsers logic
    mp_old = '''    import pandas as pd
    filas = []
    try:
        if path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="skip")
    except Exception as e:
        print(f"Error parsing MP {path}: {e}")
        return []
        
    df.columns = [str(c).strip().lower() for c in df.columns]'''
    
    mp_new = '''    import pandas as pd
    filas = []
    df = load_bank_dataframe(path)
    if df.empty: return []'''
    content = content.replace(mp_old, mp_new)

    bp_old = '''    import pandas as pd
    filas = []
    try:
        if path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="skip")
    except Exception as e:
        print(f"Error parsing BP {path}: {e}")
        return []
        
    df.columns = [str(c).strip().lower() for c in df.columns]'''
    content = content.replace(bp_old, mp_new)

    # 3. Replace setup_ui filters
    ui_old = '''        self.cmb_mes = QComboBox()
        self.cmb_mes.setStyleSheet(
            "padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px;"
            "background:white; font-size:13px; min-width:150px;")
        self.cmb_mes.currentIndexChanged.connect(self.aplicar_filtros)'''
        
    ui_new = '''        self.dt_desde = QDateEdit()
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDate(QDate.currentDate().addDays(-30))
        self.dt_desde.setStyleSheet("padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px; background:white; font-size:13px;")
        self.dt_desde.dateChanged.connect(self.aplicar_filtros)

        self.dt_hasta = QDateEdit()
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDate(QDate.currentDate())
        self.dt_hasta.setStyleSheet("padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px; background:white; font-size:13px;")
        self.dt_hasta.dateChanged.connect(self.aplicar_filtros)'''
    content = content.replace(ui_old, ui_new)
    
    ui_fl_old = '''        fl.addWidget(QLabel("Mes:")); fl.addWidget(self.cmb_mes)'''
    ui_fl_new = '''        fl.addWidget(QLabel("Desde:")); fl.addWidget(self.dt_desde)
        fl.addWidget(QLabel("Hasta:")); fl.addWidget(self.dt_hasta)'''
    content = content.replace(ui_fl_old, ui_fl_new)
    
    # 4. Replace recargar_datos
    rd_old = '''        # Actualizar combo de meses
        meses = sorted({m["fecha"][:7] for m in self.todos_los_movs if len(m["fecha"]) >= 7}, reverse=True)
        self.cmb_mes.blockSignals(True)
        self.cmb_mes.clear()
        self.cmb_mes.addItem("Todos los meses")
        for mes in meses:
            self.cmb_mes.addItem(mes)
        if meses:
            self.cmb_mes.setCurrentIndex(1)  # Mes más reciente por defecto
        self.cmb_mes.blockSignals(False)'''
    content = content.replace(rd_old, "")
    
    # 5. Replace aplicar_filtros
    af_old = '''    def aplicar_filtros(self):
        texto   = self.txt_buscar.text().lower().strip()
        mes_sel = self.cmb_mes.currentText()
        fuente_sel = self.cmb_fuente.currentText()

        filtrados = []
        for m in self.todos_los_movs:
            if mes_sel != "Todos los meses" and not m["fecha"].startswith(mes_sel):
                continue'''
                
    af_new = '''    def aplicar_filtros(self):
        texto   = self.txt_buscar.text().lower().strip()
        fuente_sel = self.cmb_fuente.currentText()
        
        fd = self.dt_desde.date().toString("yyyy-MM-dd")
        fh = self.dt_hasta.date().toString("yyyy-MM-dd") + " 23:59:59"

        filtrados = []
        for m in self.todos_los_movs:
            if not (fd <= m["fecha"] <= fh):
                continue'''
    content = content.replace(af_old, af_new)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("PATCH APPLIED SUCCESSFULLY")

if __name__ == '__main__':
    main()
