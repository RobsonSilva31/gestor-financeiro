import re

def test_parser():
    # Test with simulated text containing percentages, active counts, and R$ values.
    # We include duplicate category entries representing typical allocation tables at the top/bottom.
    simulated_text = """
    AÇÕES
    0,58
    %
    Fundos Imobiliários
    4,40
    %
    AÇÕES 13 ATIVOS VALOR TOTAL: R$ 4.891,51 (0,58%)
    FIIS 12 ATIVOS VALOR TOTAL: R$ 4.751,54 (4,40%)
    ETFS INTERN. 1 ATIVOS VALOR TOTAL: R$ 1.329,66 (21,53%)
    STOCKS 10 ATIVOS VALOR TOTAL: R$ 4.646,28 (6,02%)
    TESOURO DIRETO 1 ATIVOS VALOR TOTAL: R$ 1.128,43 (21,05%)
    RENDA FIXA 1 ATIVOS VALOR TOTAL: R$ 5.324,18 (5,11%)
    """
    
    categories = {
        'Ações (B3)': [r'\baçõ[e|e]s\b', r'ações nacionais', r'bovespa', r'ações br'],
        'Fundos Imobiliários (FIIs)': [r'\bfii\b', r'fundos imobiliários', r'fundos imobiliario', r'\bfiis\b'],
        'Stock': [r'\bstock\b', r'ações internacionais', r'ações estrangeiras', r'\bstocks\b', r'ações eua'],
        'ETF': [r'\betf\b', r'\betfs\b', r'etfs intern', r'etf nacional', r'etf internacional'],
        'Tesouro Direto': [r'tesouro', r'tesouro direto', r'títulos públicos'],
        'CDB 100% CDI': [r'renda fixa', r'cdb', r'poupança', r'\blc\b', r'\blci\b', r'\blca\b', r'tesouro selic']
    }
    
    display_names = {
        'Ações (B3)': 'Ações',
        'Fundos Imobiliários (FIIs)': 'Fundos Imobiliários (FIIs)',
        'Stock': 'Stocks',
        'ETF': 'ETFs',
        'Tesouro Direto': 'Tesouro Direto',
        'CDB 100% CDI': 'CDB 100% CDI'
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

    def is_percentage_line(idx):
        if idx < 0 or idx >= len(lines):
            return False
        curr = lines[idx]
        # Se contiver R$, é uma linha de valor monetário real, mesmo que tenha percentual junto
        if 'R$' in curr:
            return False
        curr_lower = curr.lower()
        if '%' in curr:
            return True
        # Palavras que indicam percentual ou variação
        for word in ['rentabilidade', 'variação', 'variacao', 'rentab', 'yield', 'desempenho', 'carteira %']:
            if word in curr_lower:
                return True
        # Próxima linha é % ou indicador de percentual
        if idx + 1 < len(lines):
            nxt = lines[idx+1].strip()
            if nxt.startswith('%') or nxt.lower() in ['%', 'rentabilidade', 'variação', 'variacao']:
                return True
        # Linha anterior termina com % ou é indicador de percentual
        if idx - 1 >= 0:
            prv = lines[idx-1].strip()
            if prv.endswith('%') or prv.lower() in ['%', 'rentabilidade', 'variação', 'variacao']:
                return True
        return False

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
                
                # Extract asset count (e.g. 13 ATIVOS)
                for dist in range(0, 4):
                    for step in [dist, -dist] if dist > 0 else [0]:
                        j = i + step
                        if 0 <= j < len(lines):
                            search_line = lines[j]
                            if found_assets is None:
                                asset_match = re.search(r'\b(\d+)\s+ativos?\b', search_line.lower())
                                if asset_match:
                                    found_assets = int(asset_match.group(1))
                                    
                # Pass 1: Search for value containing 'R$' (outwards distance 0 to 3)
                for dist in range(0, 4):
                    for step in [dist, -dist] if dist > 0 else [0]:
                        j = i + step
                        if 0 <= j < len(lines):
                            if is_percentage_line(j):
                                continue
                            search_line = lines[j]
                            if 'R$' in search_line:
                                # We match numbers that are NOT immediately followed by a %
                                val_match = re.search(r'R\$\s*(\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b)', search_line)
                                if not val_match:
                                    val_match = re.search(r'(\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b)(?!\s*%)', search_line)
                                if val_match:
                                    val = parse_val(val_match.group(1))
                                    if val and val > 0:
                                        found_val = val
                                        break
                    if found_val is not None:
                        break
                        
                # Pass 2: Fallback (any currency-like value not followed by %)
                if found_val is None:
                    for dist in range(0, 4):
                        for step in [dist, -dist] if dist > 0 else [0]:
                            j = i + step
                            if 0 <= j < len(lines):
                                if is_percentage_line(j):
                                    continue
                                search_line = lines[j]
                                val_match = re.search(r'(\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b)(?!\s*%)', search_line)
                                if val_match:
                                    val = parse_val(val_match.group(1))
                                    if val and val > 0:
                                        found_val = val
                                        break
                        if found_val is not None:
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

