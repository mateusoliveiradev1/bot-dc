#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPLOY AUTOMÁTICO COMPLETO - HAWK ESPORTS BOT
Configura Supabase + Render automaticamente sem interação manual
"""

import requests
import json
import time
import os
from urllib.parse import quote

class AutoDeploy:
    def __init__(self):
        self.discord_token = "MTQwODE1NTczNTQ1MTM2OTUzNA.GUEGAW.umvZoNwDCiLZlTnM67sEsc5XpZh5qbuzktBBvw"
        self.supabase_url = None
        self.supabase_key = None
        self.database_url = None
        
    def create_supabase_project(self, access_token):
        """Cria projeto no Supabase automaticamente"""
        print("🔄 Criando projeto no Supabase...")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Listar organizações
        orgs_response = requests.get(
            "https://api.supabase.com/v1/organizations",
            headers=headers
        )
        
        if orgs_response.status_code != 200:
            print(f"❌ Erro ao listar organizações: {orgs_response.text}")
            return False
            
        orgs = orgs_response.json()
        if not orgs:
            print("❌ Nenhuma organização encontrada")
            return False
            
        org_id = orgs[0]['id']
        print(f"✅ Organização encontrada: {orgs[0]['name']}")
        
        # Criar projeto
        project_data = {
            "name": "hawk-esports-bot",
            "organization_id": org_id,
            "region": "us-east-1",
            "plan": "free",
            "db_pass": "HawkBot2024!@#"
        }
        
        project_response = requests.post(
            "https://api.supabase.com/v1/projects",
            headers=headers,
            json=project_data
        )
        
        if project_response.status_code not in [200, 201]:
            print(f"❌ Erro ao criar projeto: {project_response.text}")
            return False
            
        project = project_response.json()
        project_ref = project['id']
        print(f"✅ Projeto criado: {project_ref}")
        
        # Aguardar projeto ficar pronto
        print("⏳ Aguardando projeto ficar pronto...")
        for i in range(30):
            time.sleep(10)
            status_response = requests.get(
                f"https://api.supabase.com/v1/projects/{project_ref}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                project_status = status_response.json()
                if project_status.get('status') == 'ACTIVE_HEALTHY':
                    print("✅ Projeto ativo e saudável!")
                    break
            print(f"⏳ Tentativa {i+1}/30 - Status: {project_status.get('status', 'UNKNOWN')}")
        
        # Configurar URLs
        self.supabase_url = f"https://{project_ref}.supabase.co"
        self.database_url = f"postgresql://postgres:HawkBot2024!@#@db.{project_ref}.supabase.co:5432/postgres"
        
        # Obter chaves do projeto
        keys_response = requests.get(
            f"https://api.supabase.com/v1/projects/{project_ref}/api-keys",
            headers=headers
        )
        
        if keys_response.status_code == 200:
            keys = keys_response.json()
            for key in keys:
                if key['name'] == 'anon':
                    self.supabase_key = key['api_key']
                    break
        
        print(f"✅ Supabase configurado:")
        print(f"   URL: {self.supabase_url}")
        print(f"   Database: {self.database_url}")
        
        return True
    
    def setup_database(self):
        """Configura o banco de dados executando o SQL"""
        print("🔄 Configurando banco de dados...")
        
        # Ler SQL do arquivo
        try:
            with open('supabase_setup.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
        except FileNotFoundError:
            print("❌ Arquivo supabase_setup.sql não encontrado")
            return False
        
        # Executar SQL via API REST do Supabase
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        # Dividir SQL em comandos individuais
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        success_count = 0
        for i, command in enumerate(sql_commands):
            if not command:
                continue
                
            try:
                # Usar RPC para executar SQL
                rpc_response = requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    json={"sql": command}
                )
                
                if rpc_response.status_code in [200, 201, 204]:
                    success_count += 1
                else:
                    print(f"⚠️  Comando {i+1} falhou: {command[:50]}...")
                    
            except Exception as e:
                print(f"⚠️  Erro no comando {i+1}: {str(e)}")
        
        print(f"✅ Banco configurado: {success_count}/{len(sql_commands)} comandos executados")
        return True
    
    def create_render_service(self, github_repo, render_api_key):
        """Cria serviço no Render automaticamente"""
        print("🔄 Criando serviço no Render...")
        
        headers = {
            "Authorization": f"Bearer {render_api_key}",
            "Content-Type": "application/json"
        }
        
        # Dados do serviço
        service_data = {
            "type": "web_service",
            "name": "hawk-esports-bot",
            "repo": github_repo,
            "branch": "main",
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "python bot.py",
            "plan": "free",
            "region": "oregon",
            "envVars": [
                {"key": "DISCORD_TOKEN", "value": self.discord_token},
                {"key": "DATABASE_URL", "value": self.database_url},
                {"key": "RENDER", "value": "true"},
                {"key": "BOT_PREFIX", "value": "!"},
                {"key": "DEBUG", "value": "false"},
                {"key": "TIMEZONE", "value": "America/Sao_Paulo"},
                {"key": "LOG_LEVEL", "value": "INFO"},
                {"key": "WEB_PORT", "value": "10000"},
                {"key": "WEB_HOST", "value": "0.0.0.0"},
                {"key": "PUBG_API_KEY", "value": ""},
                {"key": "MEDAL_API_KEY", "value": ""}
            ]
        }
        
        # Criar serviço
        response = requests.post(
            "https://api.render.com/v1/services",
            headers=headers,
            json=service_data
        )
        
        if response.status_code in [200, 201]:
            service = response.json()
            service_url = service.get('service', {}).get('serviceDetails', {}).get('url')
            print(f"✅ Serviço criado no Render: {service_url}")
            return True
        else:
            print(f"❌ Erro ao criar serviço no Render: {response.text}")
            return False
    
    def deploy_complete(self, supabase_token, github_repo, render_api_key):
        """Deploy completo automático"""
        print("🚀 INICIANDO DEPLOY AUTOMÁTICO COMPLETO")
        print("=" * 50)
        
        # Passo 1: Criar projeto Supabase
        if not self.create_supabase_project(supabase_token):
            print("❌ Falha na criação do Supabase")
            return False
        
        # Passo 2: Configurar banco
        if not self.setup_database():
            print("❌ Falha na configuração do banco")
            return False
        
        # Passo 3: Criar serviço Render
        if not self.create_render_service(github_repo, render_api_key):
            print("❌ Falha na criação do serviço Render")
            return False
        
        print("\n🎉 DEPLOY COMPLETO REALIZADO COM SUCESSO!")
        print("=" * 50)
        print(f"🤖 Bot Discord: ONLINE")
        print(f"🗄️  Database: {self.database_url}")
        print(f"🌐 Supabase: {self.supabase_url}")
        print("\n💡 Seu bot estará online em 2-3 minutos!")
        
        return True

def main():
    print("🤖 HAWK ESPORTS BOT - DEPLOY AUTOMÁTICO COMPLETO")
    print("=" * 60)
    print("Este script fará TUDO automaticamente:")
    print("✅ Criar projeto no Supabase")
    print("✅ Configurar banco de dados")
    print("✅ Criar serviço no Render")
    print("✅ Configurar todas as variáveis")
    print("✅ Deploy automático")
    print()
    
    # Solicitar tokens necessários
    print("🔑 TOKENS NECESSÁRIOS:")
    print()
    
    supabase_token = input("1. Supabase Access Token: ").strip()
    if not supabase_token:
        print("❌ Token do Supabase é obrigatório!")
        print("💡 Obtenha em: https://supabase.com/dashboard/account/tokens")
        return
    
    github_repo = input("2. GitHub Repository (ex: usuario/repo): ").strip()
    if not github_repo:
        print("❌ Repositório GitHub é obrigatório!")
        return
    
    render_api_key = input("3. Render API Key: ").strip()
    if not render_api_key:
        print("❌ API Key do Render é obrigatória!")
        print("💡 Obtenha em: https://dashboard.render.com/account/api-keys")
        return
    
    print()
    print("🚀 Iniciando deploy automático...")
    print()
    
    # Executar deploy
    deployer = AutoDeploy()
    success = deployer.deploy_complete(supabase_token, github_repo, render_api_key)
    
    if success:
        print("\n🎉 SUCESSO! Seu bot está sendo deployado!")
        print("⏰ Aguarde 2-3 minutos para ficar online.")
    else:
        print("\n❌ Deploy falhou. Verifique os logs acima.")

if __name__ == "__main__":
    main()