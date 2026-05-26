import os
import subprocess
import time
import sys

# Caminhos
project_dir = r"C:\Users\Robson Silva\.gemini\antigravity\scratch\finance-manager"
dist_exe = os.path.join(project_dir, "dist", "FinanSof.exe")

print("--- ETAPA 1: ENCERRANDO INSTÂNCIAS EM EXECUÇÃO ---")
try:
    # Tenta encerrar qualquer processo do FinanSof.exe aberto
    result = subprocess.run(["taskkill", "/F", "/IM", "FinanSof.exe"], capture_output=True, text=True)
    print("Taskkill stdout:", result.stdout.strip())
    print("Taskkill stderr:", result.stderr.strip())
except Exception as e:
    print("Nenhum processo FinanSof.exe rodando ou erro ao fechar:", e)

# Aguarda a liberação dos arquivos
time.sleep(2)

print("\n--- ETAPA 2: REMOVENDO EXECUTÁVEL ANTIGO ---")
if os.path.exists(dist_exe):
    try:
        os.remove(dist_exe)
        print(f"Removido com sucesso: {dist_exe}")
    except Exception as e:
        print(f"Erro ao remover executável antigo: {e}")
        print("Aguardando mais 3 segundos...")
        time.sleep(3)
        try:
            os.remove(dist_exe)
            print("Removido com sucesso na segunda tentativa.")
        except Exception as e2:
            print(f"Falha definitiva ao remover: {e2}")
            sys.exit(1)
else:
    print("Nenhum executável antigo encontrado em dist/. Perfeito.")

print("\n--- ETAPA 3: EXECUTANDO COMPILAÇÃO COM PYINSTALLER ---")
spec_path = os.path.join(project_dir, "FinanSof.spec")

# Utiliza a instalação estável do Python do usuário
python_exe = r"C:\Python314\python.exe"
if not os.path.exists(python_exe):
    python_exe = sys.executable

cmd = [python_exe, "-m", "PyInstaller", "--clean", spec_path]

print(f"Executando comando: {' '.join(cmd)}")
try:
    process = subprocess.Popen(cmd, cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    
    # Exibe a saída do compilador em tempo real
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            
    rc = process.poll()
    if rc == 0:
        print("\n--- COMPILAÇÃO CONCLUÍDA COM SUCESSO! ---")
        print(f"O executável foi gerado em: {dist_exe}")
    else:
        print(f"\n--- A COMPILAÇÃO FALHOU COM CÓDIGO {rc} ---")
        sys.exit(rc)
except Exception as e:
    print("Ocorreu uma exceção durante o build:", e)
    sys.exit(1)
