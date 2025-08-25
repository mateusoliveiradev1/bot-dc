#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Deploy Automático para Replit
Bot Hawk Esports - Deploy Gratuito Sem CLI
"""

import os
import json
import webbrowser
import time

def create_replit_config():
    """Cria configuração para Replit"""
    
    # .replit file
    replit_config = """run = "python app.py"
modules = ["python-3.10"]

[nix]
channel = "stable-22_11"

[env]
PYTHON_LD_LIBRARY_PATH = "/home/runner/$REPL_SLUG/.pythonlibs/lib"

[gitHubImport]
requiredFiles = [".replit", "replit.nix"]

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"

[deployment]
run = ["sh", "-c", "python app.py"]
deploymentTarget = "cloudrun"
"""
    
    with open('.replit', 'w', encoding='utf-8') as f:
        f.write(replit_config)
    
    # replit.nix
    nix_config = """{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.replitPackages.prybar-python310
    pkgs.replitPackages.stderred
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      # Needed for pandas / numpy
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      # Needed for pygame
      pkgs.glib
      # Needed for matplotlib
      pkgs.xorg.libX11
    ];
    PYTHONHOME = "${pkgs.python310Full}";
    PYTHONBIN = "${pkgs.python310Full}/bin/python3.10";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python310}/bin/prybar-python310";
  };
}
"""
    
    with open('replit.nix', 'w', encoding='utf-8') as f:
        f.write(nix_config)
    
    # pyproject.toml
    pyproject = """[tool.poetry]
name = "hawk-esports-bot"
version = "1.0.0"
description = "Bot Discord Hawk Esports PUBG"
author = "Hawk Esports"

[tool.poetry.dependencies]
python = "^3.10"
discord-py = "^2.3.2"
aiohttp = "^3.8.5"
requests = "^2.31.0"
python-dotenv = "^1.0.0"
coloredlogs = "^15.0.1"
aiofiles = "^23.2.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    
    with open('pyproject.toml', 'w', encoding='utf-8') as f:
        f.write(pyproject)
    
    print("✅ Arquivos do Replit criados com sucesso!")

def create_secrets_template():
    """Cria template para secrets"""
    secrets_info = """# CONFIGURAÇÃO DE SECRETS NO REPLIT

## Como configurar:
1. No Replit, vá em "Secrets" (ícone de cadeado)
2. Adicione as seguintes variáveis:

DISCORD_TOKEN = seu_token_aqui
PORT = 8000
WEB_PORT = 8000
KEEP_ALIVE = true

## Importante:
- NUNCA coloque o token no código
- Use apenas a aba Secrets do Replit
- O bot ficará online 24/7 automaticamente
"""
    
    with open('REPLIT_SECRETS.md', 'w', encoding='utf-8') as f:
        f.write(secrets_info)
    
    print("✅ Guia de secrets criado!")

def optimize_app_for_replit():
    """Otimiza app.py para Replit"""
    
    # Lê o app.py atual
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adiciona configurações específicas do Replit
    replit_config = """
# Configurações específicas para Replit
if os.getenv('REPL_ID'):  # Detecta ambiente Replit
    REPLIT = True
    WEB_PORT = int(os.getenv('PORT', 8000))
    print(f"🌐 Rodando no Replit - ID: {os.getenv('REPL_ID')}")
    
    # Keep alive automático no Replit
    from threading import Thread
    import time
    
    def keep_alive():
        while True:
            time.sleep(300)  # 5 minutos
            print("💓 Keep alive - Bot ativo")
    
    Thread(target=keep_alive, daemon=True).start()
else:
    REPLIT = False
"""
    
    # Insere após as importações
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('import') or line.startswith('from'):
            insert_index = i + 1
    
    lines.insert(insert_index + 1, replit_config)
    
    # Salva o arquivo modificado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ app.py otimizado para Replit!")

def open_replit_import():
    """Abre Replit para import automático"""
    github_url = "https://github.com/mateusoliveiradev1/bot-dc"
    replit_import_url = f"https://replit.com/new/github/{github_url.replace('https://github.com/', '')}"
    
    print(f"🌐 Abrindo Replit: {replit_import_url}")
    webbrowser.open(replit_import_url)
    
    return replit_import_url

def main():
    """Função principal"""
    print("🚀 Deploy Automático para Replit")
    print("=" * 50)
    
    try:
        # Cria arquivos necessários
        create_replit_config()
        create_secrets_template()
        optimize_app_for_replit()
        
        # Commit das alterações
        print("\n📦 Preparando arquivos...")
        os.system('git add .')
        os.system('git commit -m "🚀 REPLIT: Configuração completa para deploy"')
        os.system('git push origin main')
        
        # Abre Replit
        replit_url = open_replit_import()
        
        print("\n" + "=" * 50)
        print("✅ PREPARAÇÃO CONCLUÍDA!")
        print("\n📋 PRÓXIMOS PASSOS NO REPLIT:")
        print("1. ✅ Replit já abriu automaticamente")
        print("2. 🔑 Clique em 'Secrets' (cadeado)")
        print("3. ➕ Adicione: DISCORD_TOKEN = seu_token")
        print("4. ▶️ Clique em 'Run' (botão verde)")
        print("5. 🎉 Bot online 24/7!")
        
        print("\n🌟 VANTAGENS DO REPLIT:")
        print("✅ 100% Gratuito")
        print("✅ Sempre Online")
        print("✅ Editor Completo")
        print("✅ Terminal Integrado")
        print("✅ Sem CLI necessário")
        
        print(f"\n🔗 Link direto: {replit_url}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()