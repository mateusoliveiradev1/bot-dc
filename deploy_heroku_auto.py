#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Deploy Automático para Heroku
Bot Hawk Esports - Deploy Gratuito Confiável
"""

import os
import subprocess
import sys
import time

def check_heroku_cli():
    """Verifica se Heroku CLI está instalado"""
    try:
        result = subprocess.run(['heroku', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Heroku CLI encontrado: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def install_heroku_cli():
    """Instala Heroku CLI automaticamente"""
    print("📦 Instalando Heroku CLI...")
    
    # Download e instalação automática
    install_cmd = [
        'powershell', '-Command',
        'Invoke-WebRequest -Uri "https://cli-assets.heroku.com/heroku-x64.exe" -OutFile "heroku-installer.exe"; Start-Process "heroku-installer.exe" -ArgumentList "/S" -Wait; Remove-Item "heroku-installer.exe"'
    ]
    
    try:
        subprocess.run(install_cmd, check=True)
        print("✅ Heroku CLI instalado com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar Heroku CLI")
        return False

def heroku_login():
    """Faz login no Heroku"""
    print("🔐 Fazendo login no Heroku...")
    try:
        subprocess.run(['heroku', 'auth:login'], check=True)
        print("✅ Login realizado com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro no login do Heroku")
        return False

def create_heroku_app():
    """Cria app no Heroku"""
    app_name = "hawk-esports-bot-" + str(int(time.time()))
    print(f"🚀 Criando app: {app_name}")
    
    try:
        result = subprocess.run(['heroku', 'create', app_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ App criado: {app_name}")
            return app_name
        else:
            print(f"❌ Erro ao criar app: {result.stderr}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        return None

def set_config_vars(app_name):
    """Configura variáveis de ambiente"""
    print("⚙️ Configurando variáveis de ambiente...")
    
    # Pede o token do Discord
    token = input("🔑 Digite seu DISCORD_TOKEN: ").strip()
    
    if not token:
        print("❌ Token não pode estar vazio!")
        return False
    
    try:
        # Configura as variáveis
        configs = [
            ['heroku', 'config:set', f'DISCORD_TOKEN={token}', '-a', app_name],
            ['heroku', 'config:set', 'PORT=8000', '-a', app_name],
            ['heroku', 'config:set', 'WEB_PORT=8000', '-a', app_name],
            ['heroku', 'config:set', 'KEEP_ALIVE=true', '-a', app_name]
        ]
        
        for config in configs:
            subprocess.run(config, check=True)
        
        print("✅ Variáveis configuradas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao configurar variáveis")
        return False

def deploy_to_heroku(app_name):
    """Faz deploy para Heroku"""
    print("🚀 Fazendo deploy...")
    
    try:
        # Adiciona remote do Heroku
        subprocess.run(['heroku', 'git:remote', '-a', app_name], check=True)
        
        # Faz push para Heroku
        subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
        
        print("✅ Deploy realizado com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro no deploy")
        return False

def scale_dynos(app_name):
    """Ativa os dynos"""
    print("⚡ Ativando dynos...")
    
    try:
        subprocess.run(['heroku', 'ps:scale', 'worker=1', '-a', app_name], check=True)
        print("✅ Dynos ativados!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao ativar dynos")
        return False

def main():
    """Função principal"""
    print("🚀 Deploy Automático para Heroku")
    print("=" * 50)
    
    # Verifica Heroku CLI
    if not check_heroku_cli():
        print("📦 Heroku CLI não encontrado. Instalando...")
        if not install_heroku_cli():
            print("❌ Falha na instalação. Instale manualmente: https://devcenter.heroku.com/articles/heroku-cli")
            return
        
        # Aguarda instalação
        print("⏳ Aguardando instalação...")
        time.sleep(10)
    
    # Login
    if not heroku_login():
        return
    
    # Cria app
    app_name = create_heroku_app()
    if not app_name:
        return
    
    # Configura variáveis
    if not set_config_vars(app_name):
        return
    
    # Deploy
    if not deploy_to_heroku(app_name):
        return
    
    # Ativa dynos
    if not scale_dynos(app_name):
        return
    
    print("\n" + "=" * 50)
    print("🎉 DEPLOY CONCLUÍDO COM SUCESSO!")
    print(f"📱 Seu bot está rodando em: https://{app_name}.herokuapp.com")
    print(f"📊 Dashboard: https://dashboard.heroku.com/apps/{app_name}")
    print("\n✅ Bot online 24/7 gratuitamente!")

if __name__ == "__main__":
    main()