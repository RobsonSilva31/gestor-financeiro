# -*- coding: utf-8 -*-
import os
import sys
import urllib.request
import json
import zipfile
import shutil
import tempfile
from PySide6.QtCore import QUrl, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEnginePage, QWebEngineSettings

# Configurações Padrão
DEFAULT_OWNER = "RobsonSilva31"
DEFAULT_REPO = "gestor-financeiro"

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
            self.main_window.choose_custom_path()
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
            
            # Se a versão do instalador for mais nova, substitui a pasta local
            if bundle_version > local_version:
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
                        # Valida JSON básico
                        json.loads(data_str)
                        escaped_data = data_str.replace('\\', '\\\\').replace("'", "\\'")
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
            escaped_data = existing_data_str.replace('\\', '\\\\').replace("'", "\\'")
            self.browser.page().runJavaScript(f"window.loadDataFromPython('{escaped_data}');")

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
