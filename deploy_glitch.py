#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Deploy Automático para Glitch.com
Bot Hawk Esports - Deploy Gratuito 24/7
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def create_glitch_files():
    """Cria arquivos necessários para o Glitch"""
    
    # package.json para Glitch
    package_json = {
        "name": "hawk-esports-bot",
        "version": "1.0.0",
        "description": "Bot Discord Hawk Esports PUBG",
        "main": "app.py",
        "scripts": {
            "start": "python app.py"
        },
        "engines": {
            "python": "3.10.x"
        },
        "keywords": ["discord", "bot", "pubg", "esports"],
        "author": "Hawk Esports",
        "license": "MIT"
    }
    
    with open('package.json', 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    
    # .glitch-assets (necessário para Glitch)
    glitch_assets = {
        "assets": [],
        "metadata": {
            "title": "Hawk Esports Bot",
            "description": "Bot Discord para comunidade PUBG"
        }
    }
    
    with open('.glitch-assets', 'w', encoding='utf-8') as f:
        json.dump(glitch_assets, f, indent=2)
    
    # watch.json (configuração do Glitch)
    watch_json = {
        "install": {
            "include": ["^package\.json$", "^requirements\.txt$"]
        },
        "restart": {
            "exclude": ["^public/", "^dist/"],
            "include": ["\.py$", "\.json$"]
        },
        "throttle": 900000
    }
    
    with open('watch.json', 'w', encoding='utf-8') as f:
        json.dump(watch_json, f, indent=2)
    
    print("✅ Arquivos do Glitch criados com sucesso!")

def create_env_example():
    """Cria exemplo de .env para o usuário"""
    env_content = """# Configuração do Bot Discord
DISCORD_TOKEN=SEU_TOKEN_AQUI

# Configurações do Servidor
PORT=3000
WEB_PORT=3000

# Banco de Dados (JSON para Glitch)
DATABASE_TYPE=json

# Keep Alive
KEEP_ALIVE=true
"""
    
    with open('.env.glitch', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env.glitch criado!")
    print("📝 Configure seu DISCORD_TOKEN no arquivo .env.glitch")

def optimize_for_glitch():
    """Otimiza app.py para Glitch"""
    
    # Lê o app.py atual
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adiciona configurações específicas do Glitch
    glitch_config = """
# Configurações específicas para Glitch.com
if os.getenv('PROJECT_DOMAIN'):  # Detecta ambiente Glitch
    GLITCH = True
    WEB_PORT = int(os.getenv('PORT', 3000))
    print(f"🌐 Rodando no Glitch.com - Projeto: {os.getenv('PROJECT_DOMAIN')}")
else:
    GLITCH = False
"""
    
    # Insere após as importações
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('import') or line.startswith('from'):
            insert_index = i + 1
    
    lines.insert(insert_index + 1, glitch_config)
    
    # Salva o arquivo modificado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ app.py otimizado para Glitch!")

def main():
    """Função principal"""
    print("🚀 Preparando deploy para Glitch.com...")
    print("=" * 50)
    
    try:
        # Cria arquivos necessários
        create_glitch_files()
        create_env_example()
        optimize_for_glitch()
        
        print("\n" + "=" * 50)
        print("✅ PREPARAÇÃO CONCLUÍDA!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Acesse: https://glitch.com")
        print("2. Clique em 'New Project'")
        print("3. Selecione 'Import from GitHub'")
        print("4. Cole: https://github.com/mateusoliveiradev1/bot-dc.git")
        print("5. Configure .env com seu DISCORD_TOKEN")
        print("6. Seu bot estará online 24/7!")
        print("\n🎉 Bot pronto para deploy gratuito!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()