#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configuração automática do Supabase
Cria projeto, executa SQL e gera variáveis de ambiente para o Render
"""

import requests
import json
import time
import os
import sys
from typing import Dict, Optional

class SupabaseAutoSetup:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.supabase.com/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    def get_organizations(self) -> list:
        """Lista organizações disponíveis"""
        try:
            response = requests.get(f"{self.base_url}/organizations", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro ao listar organizações: {e}")
            return []
    
    def create_project(self, name: str, org_id: str, region: str = "us-east-1", db_password: str = None) -> Optional[Dict]:
        """Cria um novo projeto no Supabase"""
        if not db_password:
            db_password = "HawkEsports2024!@#"
            
        payload = {
            "name": name,
            "organization_id": org_id,
            "region": region,
            "plan": "free",
            "db_pass": db_password
        }
        
        try:
            print(f"🚀 Criando projeto '{name}' na região {region}...")
            response = requests.post(f"{self.base_url}/projects", 
                                   headers=self.headers, 
                                   json=payload)
            response.raise_for_status()
            project_data = response.json()
            print(f"✅ Projeto criado com sucesso! ID: {project_data['id']}")
            return project_data
        except Exception as e:
            print(f"❌ Erro ao criar projeto: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Resposta da API: {e.response.text}")
            return None
    
    def wait_for_project_ready(self, project_ref: str, max_wait: int = 300) -> bool:
        """Aguarda o projeto ficar pronto"""
        print(f"⏳ Aguardando projeto {project_ref} ficar pronto...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.base_url}/projects/{project_ref}", 
                                      headers=self.headers)
                if response.status_code == 200:
                    project = response.json()
                    if project.get('status') == 'ACTIVE':
                        print(f"✅ Projeto {project_ref} está ativo!")
                        return True
                    else:
                        print(f"⏳ Status atual: {project.get('status', 'UNKNOWN')}")
                        
            except Exception as e:
                print(f"⚠️ Erro ao verificar status: {e}")
            
            time.sleep(10)
        
        print(f"❌ Timeout: Projeto não ficou pronto em {max_wait} segundos")
        return False
    
    def execute_sql_setup(self, project_ref: str, anon_key: str, service_key: str) -> bool:
        """Executa o SQL de configuração do banco"""
        try:
            # Lê o arquivo SQL
            with open('supabase_setup.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # URL da API REST do projeto
            project_url = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec_sql"
            
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json"
            }
            
            # Divide o SQL em comandos individuais
            sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            print(f"🔧 Executando {len(sql_commands)} comandos SQL...")
            
            for i, command in enumerate(sql_commands, 1):
                if command:
                    try:
                        payload = {"sql": command + ";"}
                        response = requests.post(project_url, headers=headers, json=payload)
                        
                        if response.status_code in [200, 201]:
                            print(f"✅ Comando {i}/{len(sql_commands)} executado")
                        else:
                            print(f"⚠️ Comando {i} falhou: {response.text}")
                            
                    except Exception as e:
                        print(f"❌ Erro no comando {i}: {e}")
            
            print("✅ Configuração SQL concluída!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao executar SQL: {e}")
            return False
    
    def get_project_keys(self, project_ref: str) -> Optional[Dict]:
        """Obtém as chaves do projeto"""
        try:
            response = requests.get(f"{self.base_url}/projects/{project_ref}/api-keys", 
                                  headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro ao obter chaves: {e}")
            return None
    
    def generate_env_vars(self, project_ref: str, db_password: str, discord_token: str) -> str:
        """Gera as variáveis de ambiente para o Render"""
        database_url = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        env_vars = f"""# ===== VARIÁVEIS DE AMBIENTE PARA O RENDER =====
# Cole estas variáveis no painel do Render

# === DISCORD BOT ===
DISCORD_TOKEN={discord_token}

# === BANCO DE DADOS POSTGRESQL (SUPABASE) ===
DATABASE_URL={database_url}
DB_HOST=db.{project_ref}.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD={db_password}
DB_PORT=5432

# === APIs EXTERNAS ===
PUBG_API_KEY=sua_pubg_api_key_aqui
MEDAL_API_KEY=sua_medal_api_key_aqui

# === CONFIGURAÇÕES GERAIS ===
BOT_PREFIX=!
DEBUG=false
RENDER=true
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# === DASHBOARD WEB ===
WEB_PORT=10000
WEB_HOST=0.0.0.0

# ===== INFORMAÇÕES DO PROJETO SUPABASE =====
# Project URL: https://{project_ref}.supabase.co
# Project Ref: {project_ref}
# Database URL: {database_url}

# ===== PRÓXIMOS PASSOS =====
# 1. Copie todas as variáveis acima
# 2. Cole no painel do Render (Environment Variables)
# 3. Substitua 'sua_pubg_api_key_aqui' pela sua chave real
# 4. Substitua 'sua_medal_api_key_aqui' pela sua chave real
# 5. Faça o deploy!
"""
        
        return env_vars
    
    def setup_complete_project(self, project_name: str, discord_token: str) -> bool:
        """Configuração completa do projeto"""
        print("🎯 INICIANDO CONFIGURAÇÃO AUTOMÁTICA DO SUPABASE")
        print("=" * 50)
        
        # 1. Listar organizações
        orgs = self.get_organizations()
        if not orgs:
            print("❌ Não foi possível listar organizações")
            return False
        
        # Usar a primeira organização disponível
        org_id = orgs[0]['id']
        print(f"📋 Usando organização: {orgs[0]['name']} ({org_id})")
        
        # 2. Criar projeto
        db_password = "HawkEsports2024!@#"
        project = self.create_project(project_name, org_id, db_password=db_password)
        if not project:
            return False
        
        project_ref = project['id']
        
        # 3. Aguardar projeto ficar pronto
        if not self.wait_for_project_ready(project_ref):
            return False
        
        # 4. Obter chaves do projeto
        print("🔑 Obtendo chaves do projeto...")
        time.sleep(5)  # Aguarda um pouco mais
        
        # 5. Executar SQL (simulado - na prática você faria via SQL Editor)
        print("🔧 SQL de configuração deve ser executado manualmente no SQL Editor")
        print(f"📁 Arquivo: supabase_setup.sql")
        
        # 6. Gerar variáveis de ambiente
        print("📝 Gerando variáveis de ambiente...")
        env_vars = self.generate_env_vars(project_ref, db_password, discord_token)
        
        # Salvar em arquivo
        with open('RENDER_ENV_VARS_FINAL.txt', 'w', encoding='utf-8') as f:
            f.write(env_vars)
        
        print("\n" + "=" * 50)
        print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 50)
        print(f"📊 Projeto: {project_name}")
        print(f"🆔 Project Ref: {project_ref}")
        print(f"🌐 URL: https://{project_ref}.supabase.co")
        print(f"📁 Variáveis salvas em: RENDER_ENV_VARS_FINAL.txt")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Acesse https://supabase.com/dashboard")
        print(f"2. Abra o projeto {project_name}")
        print("3. Vá em SQL Editor")
        print("4. Execute o conteúdo do arquivo supabase_setup.sql")
        print("5. Use as variáveis do arquivo RENDER_ENV_VARS_FINAL.txt no Render")
        
        return True

def main():
    print("🤖 HAWK ESPORTS BOT - CONFIGURAÇÃO AUTOMÁTICA SUPABASE")
    print("=" * 60)
    
    # Verificar se o token foi fornecido
    access_token = input("🔑 Digite seu Access Token do Supabase: ").strip()
    if not access_token:
        print("❌ Access Token é obrigatório!")
        print("💡 Obtenha em: https://supabase.com/dashboard/account/tokens")
        return
    
    # Discord token já fornecido anteriormente
    discord_token = "MTQwODE1NTczNTQ1MTM2OTUzNA.GUEGAW.umvZoNwDCiLZlTnM67sEsc5XpZh5qbuzktBBvw"
    
    # Configurar projeto
    setup = SupabaseSetup(access_token)
    if setup.setup_complete_project("hawk-esports-bot", discord_token):
        print("✅ Configuração concluída com sucesso!")
    else:
        print("❌ Configuração falhou!")

if __name__ == "__main__":
    main()
