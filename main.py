# -*- coding: utf-8 -*-
import os
import sys
import urllib.request
import json
import zipfile
import shutil
import tempfile
from PySide6.QtCore import QUrl, Slot, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEnginePage, QWebEngineSettings

import builtins
_original_print = builtins.print
def flushed_print(*args, **kwargs):
    _original_print(*args, **kwargs)
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
builtins.print = flushed_print

# Configurações Padrão
DEFAULT_OWNER = "RobsonSilva31"
DEFAULT_REPO = "gestor-financeiro"

# Redirecionar stdout/stderr para arquivo de log persistente
persist_dir = os.path.join(os.path.expanduser('~'), '.finance_manager_app')
os.makedirs(persist_dir, exist_ok=True)
log_path = os.path.join(persist_dir, 'app.log')
try:
    log_file = open(log_path, 'a', encoding='utf-8')
    sys.stdout = log_file
    sys.stderr = log_file
    print("\n=== INICIANDO APLICATIVO (LOG REDIRECTED) ===")
except Exception as e:
    pass

def check_for_updates(persist_dir, persist_web, owner, repo):
    version_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/version.json"
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    
    local_version_path = os.path.join(persist_dir, 'version.json')
    local_version = 1
    
    if os.path.exists(local_version_path):
        try:
            with open(local_version_path, 'r', encoding='utf-8') as f:
                local_version = json.load(f).get('version', 1)
        except Exception:
            pass
            
    print(f"[Auto-Updater] Versão local atual: {local_version}")
    print(f"[Auto-Updater] Verificando atualizações em: {owner}/{repo}")
    
    try:
        # Busca a versão remota no GitHub com timeout curto de 4 segundos
        req = urllib.request.Request(
            version_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            remote_data = json.loads(response.read().decode('utf-8'))
            remote_version = remote_data.get('version', 1)
            print(f"[Auto-Updater] Versão remota no GitHub: {remote_version}")
            
            if remote_version > local_version:
                print("[Auto-Updater] Nova versão encontrada! Iniciando download da atualização...")
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, 'update.zip')
                    
                    # Faz o download do arquivo ZIP
                    download_req = urllib.request.Request(
                        zip_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(download_req, timeout=20) as dl_response:
                        with open(zip_path, 'wb') as out_file:
                            out_file.write(dl_response.read())
                    
                    # Extrai o ZIP
                    extract_dir = os.path.join(temp_dir, 'extracted')
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # Procura a pasta dist_web extraída dentro do zip
                    extracted_web_src = None
                    for root, dirs, files in os.walk(extract_dir):
                        if 'dist_web' in dirs:
                            extracted_web_src = os.path.join(root, 'dist_web')
                            break
                    
                    if extracted_web_src and os.path.exists(extracted_web_src):
                        # Limpa pasta dist_web local para evitar lixo
                        if os.path.exists(persist_web):
                            shutil.rmtree(persist_web)
                        os.makedirs(persist_web, exist_ok=True)
                        
                        # Copia novos arquivos para a pasta estável
                        for root, dirs, files in os.walk(extracted_web_src):
                            rel_path = os.path.relpath(root, extracted_web_src)
                            dest_path = os.path.join(persist_web, rel_path) if rel_path != '.' else persist_web
                            os.makedirs(dest_path, exist_ok=True)
                            
                            for file in files:
                                shutil.copy2(os.path.join(root, file), os.path.join(dest_path, file))
                        
                        # Salva o novo arquivo de versão local
                        with open(local_version_path, 'w', encoding='utf-8') as f:
                            json.dump({'version': remote_version}, f)
                        print(f"[Auto-Updater] Atualizado com sucesso para a versão {remote_version}!")
                        return True
    except Exception as e:
        print(f"[Auto-Updater] Sem internet ou falha ao buscar atualizações: {e}")
    return False

class DialogConsolePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[Dialog JS] {message} (Line: {lineNumber}, Source: {sourceID})")

class Investidor10SyncDialog(QDialog):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sincronizar com Investidor10")
        self.resize(1100, 800)
        self.setMinimumSize(900, 650)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1017;
                color: #fff;
            }
            QLabel {
                color: #e2e8f0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        top_bar = QHBoxLayout()
        
        info_label = QLabel(
            "<b>Como Importar seus Investimentos:</b><br>"
            "1. Faça login na sua conta do Investidor10 abaixo.<br>"
            "2. Acesse sua <b>Carteira</b> (a página onde o gráfico de distribuição de ativos é exibido).<br>"
            "3. Quando os valores de patrimônio aparecerem na tela, clique em <b>'Importar Carteira'</b>."
        )
        info_label.setStyleSheet("font-size: 13px; line-height: 1.4; color: #a0aec0;")
        top_bar.addWidget(info_label, stretch=1)
        
        self.btn_import = QPushButton("Importar Carteira")
        self.btn_import.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #0d1017;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2cef87;
            }
            QPushButton:pressed {
                background-color: #059669;
            }
        """)
        self.btn_import.clicked.connect(self.import_data)
        top_bar.addWidget(self.btn_import, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        layout.addLayout(top_bar)
        
        # Fallback para Login do Google
        fallback_layout = QHBoxLayout()
        fallback_layout.setContentsMargins(0, 0, 0, 5)
        fallback_layout.setSpacing(10)
        
        fallback_info = QLabel(
            "<b>Usa Login do Google?</b> Se o Google bloquear o login no navegador interno, "
            "clique ao lado para abrir no seu navegador padrão, copie a página da Carteira (Ctrl+A e Ctrl+C) "
            "e clique em 'Importar do Clipboard'."
        )
        fallback_info.setWordWrap(True)
        fallback_info.setStyleSheet("font-size: 12px; color: #fbbf24; line-height: 1.3;")
        fallback_layout.addWidget(fallback_info, stretch=1)
        
        btn_open_browser = QPushButton("1. Abrir Navegador")
        btn_open_browser.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #fff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #60a5fa;
            }
        """)
        btn_open_browser.clicked.connect(self.open_default_browser)
        fallback_layout.addWidget(btn_open_browser)
        
        btn_import_clipboard = QPushButton("2. Importar do Clipboard")
        btn_import_clipboard.setStyleSheet("""
            QPushButton {
                background-color: #d97706;
                color: #fff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f59e0b;
            }
        """)
        btn_import_clipboard.clicked.connect(self.import_from_clipboard)
        fallback_layout.addWidget(btn_import_clipboard)
        
        layout.addLayout(fallback_layout)
        
        self.browser = QWebEngineView(self)
        self.page_obj = DialogConsolePage(profile, self.browser)
        self.browser.setPage(self.page_obj)
        
        self.page_obj.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.browser.loadFinished.connect(self.on_load_finished)
        
        self.browser.setUrl(QUrl("https://investidor10.com.br/login/"))
        layout.addWidget(self.browser)
        
        self.imported_data = None

    def open_default_browser(self):
        QDesktopServices.openUrl(QUrl("https://investidor10.com.br/carteiras/"))

    def import_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text or not clipboard_text.strip():
            QMessageBox.warning(
                self,
                "Área de Transferência Vazia",
                "Não encontramos nenhum texto na sua Área de Transferência.\n\n"
                "Instruções:\n"
                "1. Acesse o Investidor10 no seu navegador padrão e faça login.\n"
                "2. Vá para a página da sua Carteira.\n"
                "3. Selecione tudo com Ctrl+A e copie com Ctrl+C.\n"
                "4. Volte aqui e clique em '2. Importar do Clipboard' novamente."
            )
            return
            
        import re
        categories = {
            'Ações (B3)': [r'\baçõ[e|e]s\b', r'ações nacionais', r'bovespa', r'ações br'],
            'Fundos Imobiliários (FIIs)': [r'\bfii\b', r'fundos imobiliários', r'fundos imobiliario', r'\bfiis\b'],
            'Stock': [r'\bstock\b', r'ações internacionais', r'ações estrangeiras', r'\bstocks\b', r'ações eua'],
            'ETF': [r'\betf\b', r'\betfs\b', r'etfs intern', r'etf nacional', r'etf internacional'],
            'Tesouro Direto': [r'tesouro', r'tesouro direto', r'títulos públicos'],
            'Criptomoedas': [r'cripto', r'criptomoedas', r'bitcoin', r'criptoativos'],
            'CDB 100% CDI': [r'renda fixa', r'cdb', r'poupança', r'\blc\b', r'\blci\b', r'\blca\b', r'tesouro selic']
        }
        
        display_names = {
            'Ações (B3)': 'Ações',
            'Fundos Imobiliários (FIIs)': 'Fundos Imobiliários (FIIs)',
            'Stock': 'Stocks',
            'ETF': 'ETFs',
            'Tesouro Direto': 'Tesouro Direto',
            'Criptomoedas': 'Criptomoedas',
            'CDB 100% CDI': 'CDB 100% CDI'
        }
        
        lines = [line.strip() for line in clipboard_text.split('\n') if line.strip()]
        
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
                                
                                # Tenta encontrar o número de ativos (ex: 13 ativos)
                                if found_assets is None:
                                    asset_match = re.search(r'\b(\d+)\s+ativos?\b', search_line.lower())
                                    if asset_match:
                                        found_assets = int(asset_match.group(1))
                                
                                # Tenta encontrar o valor monetário R$ na linha
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
                        
        self.process_scraped_data(result)

    def import_data(self):
        self.btn_import.setEnabled(False)
        self.btn_import.setText("Verificando...")
        
        js_script = """
        (function() {
            const data = {};
            const categories = {
                'Ações (B3)': [/ações/i, /ações nacionais/i, /bovespa/i, /ações br/i],
                'Fundos Imobiliários (FIIs)': [/fii/i, /fundos imobiliários/i, /fundos imobiliario/i, /fiis/i],
                'Stock': [/stock/i, /ações internacionais/i, /ações estrangeiras/i, /stocks/i, /ações eua/i],
                'ETF': [/etf/i, /etfs/i, /etf nacional/i, /etf internacional/i],
                'Tesouro Direto': [/tesouro/i, /tesouro direto/i, /títulos públicos/i],
                'Criptomoedas': [/cripto/i, /criptomoedas/i, /bitcoin/i, /criptoativos/i],
                'CDB 100% CDI': [/cdb/i, /renda fixa/i, /poupança/i, /lc/i, /lci/i, /lca/i, /poupança/i, /tesouro selic/i]
            };

            function parseValue(text) {
                if (!text) return null;
                const cleaned = text.replace(/[^\\d.,]/g, '').trim();
                if (!cleaned) return null;
                if (cleaned.includes(',') && cleaned.includes('.')) {
                    if (cleaned.indexOf(',') > cleaned.indexOf('.')) {
                        return parseFloat(cleaned.replace(/\\./g, '').replace(',', '.'));
                    } else {
                        return parseFloat(cleaned.replace(/,/g, ''));
                    }
                }
                if (cleaned.includes(',')) {
                    const parts = cleaned.split(',');
                    if (parts.length === 2 && parts[1].length <= 2) {
                        return parseFloat(cleaned.replace(',', '.'));
                    }
                    return parseFloat(cleaned.replace(/,/g, ''));
                }
                return parseFloat(cleaned);
            }

            // Método 1: Extrair das instâncias do Chart.js
            let foundInCharts = false;
            try {
                const canvases = document.querySelectorAll('canvas');
                canvases.forEach(canvas => {
                    for (let prop in canvas) {
                        if (prop.toLowerCase().includes('chart') && canvas[prop] && canvas[prop].config) {
                            const chart = canvas[prop];
                            const labels = chart.data.labels;
                            const datasets = chart.data.datasets;
                            if (labels && datasets && datasets.length > 0) {
                                const dataset = datasets[0];
                                const values = dataset.data;
                                if (labels.length === values.length) {
                                    labels.forEach((label, idx) => {
                                        const val = parseFloat(values[idx]);
                                        if (!isNaN(val) && val > 0) {
                                            for (const [key, regexes] of Object.entries(categories)) {
                                                for (const regex of regexes) {
                                                    if (regex.test(label)) {
                                                        data[key] = val;
                                                        foundInCharts = true;
                                                    }
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                        }
                    }
                });
            } catch (e) {
                console.error(e);
            }

            // Método 2: Analisar todas as tabelas e linhas do DOM
            const rows = document.querySelectorAll('tr, div.item, div.row, li, div.card, div.patrimonio-item');
            rows.forEach(row => {
                const text = (row.innerText || '').trim();
                if (text.length > 0 && text.length < 300) {
                    for (const [key, regexes] of Object.entries(categories)) {
                        if (data[key] !== undefined) continue;
                        for (const regex of regexes) {
                            if (regex.test(text)) {
                                const cells = row.querySelectorAll('td, span, div, p');
                                for (let cell of cells) {
                                    const cellText = (cell.innerText || '').trim();
                                    if (cellText.includes('R$')) {
                                        const val = parseValue(cellText);
                                        if (val !== null && val > 0 && !cellText.includes('%')) {
                                            data[key] = val;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            });

            // Método 3: Tentar encontrar divs que contêm o nome da categoria seguido de um valor monetário
            const elements = document.querySelectorAll('div, span, p');
            elements.forEach(el => {
                const text = (el.innerText || '').trim();
                if (text.length > 0 && text.length < 150) {
                    for (const [key, regexes] of Object.entries(categories)) {
                        if (data[key] !== undefined) continue;
                        for (const regex of regexes) {
                            if (regex.test(text)) {
                                const matches = text.match(/(?:R\\$|R\\$\\s*)\\s*([0-9.,]+)/i);
                                if (matches) {
                                    const val = parseValue(matches[0]);
                                    if (val !== null && val > 0) {
                                        data[key] = val;
                                    }
                                }
                            }
                        }
                    }
                }
            });

            return data;
        })()
        """
        self.browser.page().runJavaScript(js_script, self.process_scraped_data)

    def process_scraped_data(self, result):
        self.btn_import.setEnabled(True)
        self.btn_import.setText("Importar Carteira")
        
        if not result or len(result) == 0:
            QMessageBox.warning(
                self,
                "Importação Falhou",
                "Nenhum valor de investimento foi detectado na página atual.\n\n"
                "Instruções:\n"
                "1. Faça login na sua conta do Investidor10.\n"
                "2. Vá para a página da sua Carteira (Dashboard de Evolução/Patrimônio).\n"
                "3. Aguarde o carregamento completo do gráfico e tabelas antes de tentar importar."
            )
            return
            
        msg = "<h3><b>Valores identificados no Investidor10:</b></h3><br>"
        self.imported_data = {}
        has_values = False
        
        for key, val in result.items():
            if val and val > 0:
                val_formatted = f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                msg += f"• <b>{key}:</b> {val_formatted}<br>"
                self.imported_data[key] = val
                has_values = True
                
        if not has_values:
            QMessageBox.warning(
                self,
                "Nenhum valor encontrado",
                "Não foram encontrados investimentos com valores acima de R$ 0,00 na página atual."
            )
            return
            
        msg += "<br><b>Deseja atualizar sua aba de Investimentos com esses valores?</b>"
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Importação")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        msg_box.button(QMessageBox.StandardButton.Yes).setText("Sim, Atualizar")
        msg_box.button(QMessageBox.StandardButton.No).setText("Cancelar")
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.accept()

    def on_load_finished(self, ok):
        print(f"[Dialog] Carregamento concluído: {ok}. URL atual: {self.browser.url().toString()}")

class ConsolePage(QWebEnginePage):
    def __init__(self, profile, main_window):
        super().__init__(profile, main_window)
        self.main_window = main_window

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Escuta comunicações vindas da interface Web por meio do console.log
        if message.startswith("SAVE_DATA:"):
            data_json = message[len("SAVE_DATA:"):]
            self.main_window.save_data_from_js(data_json)
        elif message.startswith("CHOOSE_PATH:"):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.main_window.choose_custom_path)
        elif message.startswith("SYNC_INVESTIDOR10:"):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.main_window.open_investidor10_sync)
        elif message.startswith("UPDATE_INVESTIDOR10:"):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.main_window.auto_update_investidor10)
        else:
            print(f"JS Console: {message} (Line: {lineNumber}, Source: {sourceID})")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinanSof - Gestor Financeiro Pessoal")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 768)
        
        # 1. Configurar diretórios de persistência locais
        if getattr(sys, 'frozen', False):
            # Se executado a partir do executável compilado (.exe)
            self.base_path = sys._MEIPASS
            self.persist_dir = os.path.join(os.path.expanduser('~'), '.finance_manager_app')
            self.persist_web = os.path.join(self.persist_dir, 'dist_web')
            src_web = os.path.join(self.base_path, 'dist_web')
            
            # Carrega versão local vs embutida no instalador
            bundle_version = 1
            bundle_version_path = os.path.join(src_web, 'version.json')
            if os.path.exists(bundle_version_path):
                try:
                    with open(bundle_version_path, 'r', encoding='utf-8') as f:
                        bundle_version = json.load(f).get('version', 1)
                except Exception:
                    pass
            
            local_version_path = os.path.join(self.persist_dir, 'version.json')
            local_version = 0
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r', encoding='utf-8') as f:
                        local_version = json.load(f).get('version', 1)
                except Exception:
                    pass
            
            # Se a versão do instalador for mais nova ou igual, substitui a pasta local
            if bundle_version >= local_version:
                print(f"[Core] Atualizando pasta estática (Embutida {bundle_version} > Local {local_version})")
                try:
                    if os.path.exists(self.persist_web):
                        shutil.rmtree(self.persist_web)
                    os.makedirs(self.persist_web, exist_ok=True)
                    
                    for root, dirs, files in os.walk(src_web):
                        rel_path = os.path.relpath(root, src_web)
                        dest_path = os.path.join(self.persist_web, rel_path) if rel_path != '.' else self.persist_web
                        os.makedirs(dest_path, exist_ok=True)
                        
                        for file in files:
                            shutil.copy2(os.path.join(root, file), os.path.join(dest_path, file))
                            
                    with open(local_version_path, 'w', encoding='utf-8') as f:
                        json.dump({'version': bundle_version}, f)
                except Exception as e:
                    print(f"[Core] Erro ao copiar arquivos estáticos: {e}")
            
            # Carrega configurações para ver se há repositório customizado
            self.load_config()
            
            # Procura atualizações remotas
            check_for_updates(self.persist_dir, self.persist_web, self.github_owner, self.github_repo)
            
            self.entry_path = os.path.join(self.persist_web, 'index.html')
        else:
            # Em modo de desenvolvimento
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.entry_path = os.path.join(self.base_path, 'dist_web', 'index.html')
            self.persist_dir = os.path.join(self.base_path, '.dev_storage')
            self.persist_web = os.path.join(self.base_path, 'dist_web')
            self.load_config()

        profile_path = os.path.join(self.persist_dir, 'profile')
        cache_path = os.path.join(self.persist_dir, 'cache')
        os.makedirs(profile_path, exist_ok=True)
        os.makedirs(cache_path, exist_ok=True)
        
        # 2. Configurar o perfil do navegador Chromium embutido
        self.profile = QWebEngineProfile("FinanceManagerProfile", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(cache_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        self.profile.clearHttpCache()
        self.profile.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 3. Criar visualizador web
        self.browser = QWebEngineView()
        self.page = ConsolePage(self.profile, self)
        self.browser.setPage(self.page)
        
        # Injeta ícone da janela
        icon_path = os.path.join(self.base_path, 'logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        if not os.path.exists(self.entry_path):
            print(f"Erro: Arquivo '{self.entry_path}' não encontrado.")
            sys.exit(1)
            
        # Conecta sinal de carga completa para injetar os dados salvos
        self.browser.loadFinished.connect(self.on_load_finished)
        
        # Carrega o HTML
        self.browser.setUrl(QUrl.fromLocalFile(self.entry_path))
        self.setCentralWidget(self.browser)

    # Carregar configurações globais (caminho do banco de dados e repositório)
    def load_config(self):
        config_path = os.path.join(self.persist_dir, 'config.json')
        self.data_filepath = os.path.join(self.persist_dir, 'dados_financeiros.json')
        self.github_owner = DEFAULT_OWNER
        self.github_repo = DEFAULT_REPO
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.data_filepath = cfg.get('data_filepath', self.data_filepath)
                    self.github_owner = cfg.get('github_owner', self.github_owner)
                    self.github_repo = cfg.get('github_repo', self.github_repo)
            except Exception as e:
                print(f"[Config] Erro ao ler arquivo de config: {e}")

    # Salva configurações globais
    def save_config(self):
        config_path = os.path.join(self.persist_dir, 'config.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'data_filepath': self.data_filepath,
                    'github_owner': self.github_owner,
                    'github_repo': self.github_repo
                }, f, indent=2)
        except Exception as e:
            print(f"[Config] Erro ao salvar arquivo de config: {e}")

    # Quando a página web carrega, alimenta o javascript com as informações locais
    def on_load_finished(self, ok):
        if ok:
            print(f"[Core] Webview carregada com sucesso. Injetando dados de {self.data_filepath}")
            
            # Envia o caminho de dados para a interface
            escaped_path = self.data_filepath.replace('\\', '\\\\')
            self.browser.page().runJavaScript(f"window.updateDatabasePathFromPython('{escaped_path}');")
            
            # Lê e injeta os lançamentos salvos
            if os.path.exists(self.data_filepath):
                try:
                    with open(self.data_filepath, 'r', encoding='utf-8') as f:
                        data_str = f.read().strip()
                    if data_str:
                        # Valida e minifica o JSON para evitar erros com quebras de linha em strings do JS
                        minified_data = json.dumps(json.loads(data_str), ensure_ascii=False)
                        escaped_data = minified_data.replace('\\', '\\\\').replace("'", "\\'")
                        self.browser.page().runJavaScript(f"window.loadDataFromPython('{escaped_data}');")
                except Exception as e:
                    print(f"[Core] Erro ao ler banco de dados e passar pro JS: {e}")


    # Salva dados financeiros recebidos do JS
    def save_data_from_js(self, data_json):
        try:
            # Valida JSON antes de gravar
            parsed = json.loads(data_json)
            
            # Garante que o diretório de destino exista
            os.makedirs(os.path.dirname(self.data_filepath), exist_ok=True)
            
            # Grava no arquivo
            with open(self.data_filepath, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
                
            # Se as configurações mudaram (ex: github settings)
            if 'settings' in parsed:
                settings = parsed['settings']
                owner = settings.get('githubOwner', self.github_owner)
                repo = settings.get('githubRepo', self.github_repo)
                if owner != self.github_owner or repo != self.github_repo:
                    self.github_owner = owner
                    self.github_repo = repo
                    self.save_config()
                    
            print(f"[Core] Lançamentos salvos com sucesso em: {self.data_filepath}")
        except Exception as e:
            print(f"[Core] Falha ao salvar lançamentos em arquivo: {e}")

    # Abre a caixa de diálogo para escolher um novo caminho do arquivo dados_financeiros.json
    def choose_custom_path(self):
        default_dir = os.path.dirname(self.data_filepath)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Selecionar Local do Banco de Dados (.json)",
            os.path.join(default_dir, "dados_financeiros.json"),
            "Arquivo de Dados JSON (*.json);;Todos os Arquivos (*)"
        )
        
        if file_path:
            clean_path = os.path.normpath(file_path)
            print(f"[Core] Usuário escolheu novo caminho: {clean_path}")
            
            # 1. Carrega dados do arquivo escolhido se ele já existir e for válido
            existing_data_str = ""
            if os.path.exists(clean_path):
                try:
                    with open(clean_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            json.loads(content) # validação
                            existing_data_str = content
                            print("[Core] Arquivo existente detectado e validado. Carregando dados dele.")
                except Exception as e:
                    print(f"[Core] Arquivo existente no caminho escolhido é inválido ou vazio: {e}")
            
            # 2. Se o arquivo não existia, mas temos dados no caminho antigo, copia os dados atuais para lá
            if not existing_data_str and os.path.exists(self.data_filepath):
                try:
                    shutil.copy2(self.data_filepath, clean_path)
                    with open(clean_path, 'r', encoding='utf-8') as f:
                        existing_data_str = f.read()
                    print("[Core] Dados locais copiados com sucesso para o novo caminho de sincronização.")
                except Exception as e:
                    print(f"[Core] Erro ao copiar banco antigo para o novo caminho: {e}")
            
            # 3. Se ainda não há dados, grava um JSON básico inicial
            if not existing_data_str:
                existing_data_str = "{}"
                try:
                    with open(clean_path, 'w', encoding='utf-8') as f:
                        f.write(existing_data_str)
                except Exception as e:
                    print(f"[Core] Erro ao inicializar novo arquivo JSON: {e}")
                    return
            
            # Atualiza o caminho ativo
            self.data_filepath = clean_path
            self.save_config()
            
            # Notifica o JS do novo caminho ativo
            escaped_path = clean_path.replace('\\', '\\\\')
            self.browser.page().runJavaScript(f"window.updateDatabasePathFromPython('{escaped_path}');")
            
            # Envia as informações do novo arquivo para serem renderizadas na tela
            try:
                minified_data = json.dumps(json.loads(existing_data_str), ensure_ascii=False)
            except Exception:
                minified_data = "{}"
            escaped_data = minified_data.replace('\\', '\\\\').replace("'", "\\'")
            self.browser.page().runJavaScript(f"window.loadDataFromPython('{escaped_data}');")

    # Abre a janela de sincronização com o Investidor10
    def open_investidor10_sync(self):
        print("[Core] Abrindo janela de sincronização do Investidor10...")
        dialog = Investidor10SyncDialog(self.profile, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.imported_data:
            import_json = json.dumps(dialog.imported_data)
            escaped_import = import_json.replace('\\', '\\\\').replace("'", "\\'")
            print(f"[Core] Importando dados de investimentos para o frontend: {import_json}")
            self.browser.page().runJavaScript(f"window.importInvestmentsFromPython('{escaped_import}');")

    # Atualiza a carteira em segundo plano sem abrir janela
    def auto_update_investidor10(self):
        print("[Core] Iniciando atualização automática em segundo plano do Investidor10...")
        
        self.bg_browser = QWebEngineView(self)
        self.bg_page = QWebEnginePage(self.profile, self.bg_browser)
        self.bg_browser.setPage(self.bg_page)
        
        self.bg_page.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.bg_page.settings().setAttribute(QWebEngineSettings.AutoLoadImages, False)
        
        self.bg_browser.loadFinished.connect(self.on_bg_load_finished)
        self.bg_browser.setUrl(QUrl("https://investidor10.com.br/carteiras/"))

    def on_bg_load_finished(self, ok):
        if not ok:
            print("[Core] Falha ao carregar carteira em segundo plano.")
            self.browser.page().runJavaScript("showNotification('Erro de Conexão', 'Não foi possível acessar o Investidor10.', 'danger');")
            self.bg_browser.deleteLater()
            self.bg_browser = None
            return
            
        url = self.bg_browser.url().toString()
        print(f"[Core] Página em segundo plano carregada. URL: {url}")
        
        if "login" in url:
            print("[Core] Sessão expirada no Investidor10. Redirecionando usuário para login...")
            self.browser.page().runJavaScript("showNotification('Sessão Expirada', 'Por favor, conecte novamente ao Investidor10.', 'warning');")
            self.open_investidor10_sync()
            self.bg_browser.deleteLater()
            self.bg_browser = None
            return
            
        js_script = """
        (function() {
            const data = {};
            const categories = {
                'Ações (B3)': [/ações/i, /ações nacionais/i, /bovespa/i, /ações br/i],
                'Fundos Imobiliários (FIIs)': [/fii/i, /fundos imobiliários/i, /fundos imobiliario/i, /fiis/i],
                'Stock': [/stock/i, /ações internacionais/i, /ações estrangeiras/i, /stocks/i, /ações eua/i],
                'ETF': [/etf/i, /etfs/i, /etf nacional/i, /etf internacional/i],
                'Tesouro Direto': [/tesouro/i, /tesouro direto/i, /títulos públicos/i],
                'Criptomoedas': [/cripto/i, /criptomoedas/i, /bitcoin/i, /criptoativos/i],
                'CDB 100% CDI': [/cdb/i, /renda fixa/i, /poupança/i, /lc/i, /lci/i, /lca/i, /poupança/i, /tesouro selic/i]
            };

            function parseValue(text) {
                if (!text) return null;
                const cleaned = text.replace(/[^\\d.,]/g, '').trim();
                if (!cleaned) return null;
                if (cleaned.includes(',') && cleaned.includes('.')) {
                    if (cleaned.indexOf(',') > cleaned.indexOf('.')) {
                        return parseFloat(cleaned.replace(/\\./g, '').replace(',', '.'));
                    } else {
                        return parseFloat(cleaned.replace(/,/g, ''));
                    }
                }
                if (cleaned.includes(',')) {
                    const parts = cleaned.split(',');
                    if (parts.length === 2 && parts[1].length <= 2) {
                        return parseFloat(cleaned.replace(',', '.'));
                    }
                    return parseFloat(cleaned.replace(/,/g, ''));
                }
                return parseFloat(cleaned);
            }

            // Método 1: Chart.js
            try {
                const canvases = document.querySelectorAll('canvas');
                canvases.forEach(canvas => {
                    for (let prop in canvas) {
                        if (prop.toLowerCase().includes('chart') && canvas[prop] && canvas[prop].config) {
                            const chart = canvas[prop];
                            const labels = chart.data.labels;
                            const datasets = chart.data.datasets;
                            if (labels && datasets && datasets.length > 0) {
                                const dataset = datasets[0];
                                const values = dataset.data;
                                if (labels.length === values.length) {
                                    labels.forEach((label, idx) => {
                                        const val = parseFloat(values[idx]);
                                        if (!isNaN(val) && val > 0) {
                                            for (const [key, regexes] of Object.entries(categories)) {
                                                for (const regex of regexes) {
                                                    if (regex.test(label)) {
                                                        data[key] = val;
                                                    }
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                        }
                    }
                });
            } catch (e) {}

            // Método 2: DOM
            const rows = document.querySelectorAll('tr, div.item, div.row, li, div.card, div.patrimonio-item');
            rows.forEach(row => {
                const text = (row.innerText || '').trim();
                if (text.length > 0 && text.length < 300) {
                    for (const [key, regexes] of Object.entries(categories)) {
                        if (data[key] !== undefined) continue;
                        for (const regex of regexes) {
                            if (regex.test(text)) {
                                const cells = row.querySelectorAll('td, span, div, p');
                                for (let cell of cells) {
                                    const cellText = (cell.innerText || '').trim();
                                    if (cellText.includes('R$')) {
                                        const val = parseValue(cellText);
                                        if (val !== null && val > 0 && !cellText.includes('%')) {
                                            data[key] = val;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            });

            return data;
        })()
        """
        self.bg_browser.page().runJavaScript(js_script, self.process_bg_scraped_data)

    def process_bg_scraped_data(self, result):
        if not result or len(result) == 0:
            print("[Core] Nenhum dado raspado em segundo plano.")
            self.browser.page().runJavaScript("showNotification('Atualização Falhou', 'Não encontramos dados na sua carteira. Abra a conexão manual.', 'warning');")
        else:
            import_json = json.dumps(result)
            escaped_import = import_json.replace('\\', '\\\\').replace("'", "\\'")
            print(f"[Core] Atualização automática: Importando dados de investimentos para o frontend: {import_json}")
            self.browser.page().runJavaScript(f"window.importInvestmentsFromPython('{escaped_import}');")
            
        self.bg_browser.deleteLater()
        self.bg_browser = None

if __name__ == '__main__':
    # Evita que o Windows agrupe o app com o ícone genérico do Python na barra de tarefas
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RobsonSilva31.FinanSof.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
