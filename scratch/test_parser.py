import re

def test_parser():
    simulated_text = """
    Patrimônio Consolidado
    Investidor10
    Minha Carteira
    Ações
    25%
    R$ 15.000,00
    Fundos Imobiliários
    R$ 25.300,50
    30%
    Stocks
    R$ 5.400,00
    ETF
    R$ 2.000,00
    Tesouro Direto
    R$ 10.000,00
    Criptoativos
    R$ 3.000,50
    Renda Fixa
    R$ 8.500,00
    """
    
    categories = {
        'Ações (B3)': [r'\baçõ[e|e]s\b', r'ações nacionais', r'bovespa', r'ações br'],
        'Fundos Imobiliários (FIIs)': [r'\bfii\b', r'fundos imobiliários', r'fundos imobiliario', r'\bfiis\b'],
        'Stock': [r'\bstock\b', r'ações internacionais', r'ações estrangeiras', r'\bstocks\b', r'ações eua'],
        'ETF': [r'\betf\b', r'\betfs\b', r'etf nacional', r'etf internacional'],
        'Tesouro Direto': [r'tesouro', r'tesouro direto', r'títulos públicos'],
        'Criptomoedas': [r'cripto', r'criptomoedas', r'bitcoin', r'criptoativos'],
        'CDB 100% CDI': [r'cdb', r'renda fixa', r'poupança', r'\blc\b', r'\blci\b', r'\blca\b', r'tesouro selic']
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
            if cat_name in result:
                continue
            matched = False
            for reg in regexes:
                if re.search(reg, line_lower):
                    matched = True
                    break
            if matched:
                # Search outwards from i (distance 0 to 5)
                found_val = None
                for dist in range(0, 6):
                    # Check j = i + dist, then j = i - dist
                    for step in [dist, -dist] if dist > 0 else [0]:
                        j = i + step
                        if 0 <= j < len(lines):
                            search_line = lines[j]
                            if 'R$' in search_line or re.search(r'\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b', search_line):
                                if '%' not in search_line:
                                    val = parse_val(search_line)
                                    if val and val > 0:
                                        found_val = val
                                        break
                    if found_val is not None:
                        break
                
                if found_val is not None:
                    result[cat_name] = found_val
                    
    print("Parsed results:")
    for k, v in result.items():
        print(f"  {k}: {v}")

test_parser()
