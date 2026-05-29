import re

def test_parser():
    simulated_text = """
    AÇÕES 13 ATIVOS VALOR TOTAL: R$ 4.891,51
    FIIS 12 ATIVOS VALOR TOTAL: R$ 4.751,54
    ETFS INTERN. 1 ATIVOS VALOR TOTAL: R$ 1.329,66
    STOCKS 10 ATIVOS VALOR TOTAL: R$ 4.646,28
    TESOURO DIRETO 1 ATIVOS VALOR TOTAL: R$ 1.128,43
    RENDA FIXA 1 ATIVOS VALOR TOTAL: R$ 5.324,18
    """
    
    categories = {
        'Ações (B3)': [r'\baçõ[e|e]s\b', r'ações nacionais', r'bovespa', r'ações br'],
        'Fundos Imobiliários (FIIs)': [r'\bfii\b', r'fundos imobiliários', r'fundos imobiliario', r'\bfiis\b'],
        'Stock': [r'\bstock\b', r'ações internacionais', r'ações estrangeiras', r'\bstocks\b', r'ações eua'],
        'ETF': [r'\betf\b', r'\betfs\b', r'etfs intern', r'etf nacional', r'etf internacional'],
        'Tesouro Direto': [r'tesouro', r'tesouro direto', r'títulos públicos'],
        'Renda Fixa': [r'renda fixa', r'cdb', r'poupança', r'\blc\b', r'\blci\b', r'\blca\b', r'tesouro selic']
    }
    
    display_names = {
        'Ações (B3)': 'Ações',
        'Fundos Imobiliários (FIIs)': 'Fundos Imobiliários (FIIs)',
        'Stock': 'Stocks',
        'ETF': 'ETFs',
        'Tesouro Direto': 'Tesouro Direto',
        'Renda Fixa': 'Renda Fixa'
    }
    
    lines = [line.strip() for line in simulated_text.split('\n') if line.strip()]
    
    def parse_val(t):
        cleaned = re.sub(r'[^\d.,]', '', t).strip()
        if not cleaned:
            return None
        if ',' in cleaned and '.' in cleaned:
            if cleaned.index(',') > cleaned.index('.'):
                return float(cleaned.replace('.', '').replace(',', '.'))
            else:
                return float(cleaned.replace(',', ''))
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                return float(cleaned.replace(',', '.'))
            return float(cleaned.replace(',', ''))
        return float(cleaned)

    result = {}
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for cat_name, regexes in categories.items():
            matched = False
            for reg in regexes:
                if re.search(reg, line_lower):
                    matched = True
                    break
            if matched:
                found_val = None
                found_assets = None
                
                for dist in range(0, 6):
                    for step in [dist, -dist] if dist > 0 else [0]:
                        j = i + step
                        if 0 <= j < len(lines):
                            search_line = lines[j]
                            
                            # Try to find asset count (e.g. 13 ATIVOS)
                            if found_assets is None:
                                asset_match = re.search(r'\b(\d+)\s+ativos?\b', search_line.lower())
                                if asset_match:
                                    found_assets = int(asset_match.group(1))
                            
                            # Try to find BRL value by matching the currency substring specifically
                            if found_val is None:
                                val_match = re.search(r'(?:R\$\s*)?(\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b)', search_line)
                                if val_match:
                                    val = parse_val(val_match.group(1))
                                    if val and val > 0:
                                        found_val = val
                                    
                    if found_val is not None and found_assets is not None:
                        break
                
                if found_val is not None:
                    disp_name = display_names.get(cat_name, cat_name)
                    if found_assets is not None:
                        label = f"{disp_name} ({found_assets} ativo{'s' if found_assets > 1 else ''})"
                    else:
                        label = disp_name
                    result[label] = found_val
                    
    print("Parsed results:")
    for k, v in result.items():
        print(f"  {k}: {v}")

test_parser()
