# -*- coding: utf-8 -*-
import os
import json
import subprocess
import sys

project_dir = os.path.dirname(os.path.abspath(__file__))
version_path = os.path.join(project_dir, "version.json")
dist_version_path = os.path.join(project_dir, "dist_web", "version.json")

print("==================================================")
print("     INICIANDO DEPLOY AUTOMÁTICO DE ATUALIZAÇÃO   ")
print("==================================================")

# 1. Incrementar versão
if os.path.exists(version_path):
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        version = data.get("version", 1) + 1
    except Exception:
        version = 2
else:
    version = 2

data = {"version": version}
with open(version_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
with open(dist_version_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"[1/3] Versão incrementada com sucesso para: {version}")

# 2. Rodar compilação local (build_and_deploy.py)
print("[2/3] Executando PyInstaller para rebuild do executável...")
build_script = os.path.join(project_dir, "build_and_deploy.py")

python_exe = r"C:\Python314\python.exe"
if not os.path.exists(python_exe):
    python_exe = sys.executable

try:
    result = subprocess.run([python_exe, build_script], capture_output=False)
    if result.returncode != 0:
        print("Erro: A compilação do executável falhou!")
        sys.exit(1)
except Exception as e:
    print(f"Erro ao executar script de compilação: {e}")
    sys.exit(1)

# 3. Enviar ao GitHub
print("[3/3] Enviando atualizações para o GitHub...")
try:
    # Adicionar arquivos ao Git
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
    
    # Criar o Commit
    commit_msg = f"Auto-update para versao {version}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_dir, check=True)
    
    # Enviar para a nuvem
    print("Enviando (git push)...")
    subprocess.run(["git", "push"], cwd=project_dir, check=True)
    print("\n>>> SUCESSO! A atualização foi publicada no GitHub.")
    print(f">>> Outros computadores com o mesmo app receberão a versão {version} ao abrir o app!")
except Exception as e:
    print(f"\nErro ao sincronizar com o GitHub: {e}")
    print("Dica: Certifique-se de que este diretório já está vinculado a um repositório git:")
    print(f"  git remote add origin https://github.com/RobsonSilva31/gestor-financeiro.git")
    sys.exit(1)
