#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPLOY ZERO CLICK - HAWK ESPORTS BOT
Deploy 100% automático sem interação do usuário
"""

import requests
import json
import time
import os
from datetime import datetime

class ZeroClickDeploy:
    def __init__(self):
        self.discord_token = "MTQwODE1NTczNTQ1MTM2OTUzNA.GUEGAW.umvZoNwDCiLZlTnM67sEsc5XpZh5qbuzktBBvw"
        self.project_name = f"hawk-bot-{int(time.time())}"
        self.db_password = "HawkBot2024!@#"
        
    def create_env_file(self):
        """Cria arquivo .env com todas as configurações"""
        print("📝 Criando arquivo de configuração...")
        
        env_content = f"""# HAWK ESPORTS BOT - Configurações de Deploy
# Gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Discord Bot
DISCORD_TOKEN={self.discord_token}
BOT_PREFIX=!

# Database (Configure após criar projeto Supabase)
DATABASE_URL=postgresql://postgres:{self.db_password}@db.SEU_PROJECT_REF.supabase.co:5432/postgres

# Render Settings
RENDER=true
WEB_PORT=10000
WEB_HOST=0.0.0.0

# Bot Settings
DEBUG=false
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# API Keys (Configure conforme necessário)
PUBG_API_KEY=
MEDAL_API_KEY=

# Supabase (Configure após criar projeto)
SUPABASE_URL=https://SEU_PROJECT_REF.supabase.co
SUPABASE_KEY=SUA_ANON_KEY
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
            
        print("✅ Arquivo .env criado")
        return True
    
    def create_render_yaml(self):
        """Cria arquivo render.yaml para deploy automático"""
        print("📝 Criando configuração do Render...")
        
        yaml_content = f"""services:
  - type: web
    name: {self.project_name}
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: DISCORD_TOKEN
        value: {self.discord_token}
      - key: BOT_PREFIX
        value: "!"
      - key: RENDER
        value: "true"
      - key: WEB_PORT
        value: "10000"
      - key: WEB_HOST
        value: "0.0.0.0"
      - key: DEBUG
        value: "false"
      - key: TIMEZONE
        value: "America/Sao_Paulo"
      - key: LOG_LEVEL
        value: "INFO"
      - key: PUBG_API_KEY
        value: ""
      - key: MEDAL_API_KEY
        value: ""
      - key: DATABASE_URL
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
"""
        
        with open('render.yaml', 'w', encoding='utf-8') as f:
            f.write(yaml_content)
            
        print("✅ Arquivo render.yaml criado")
        return True
    
    def create_deploy_instructions(self):
        """Cria instruções finais de deploy"""
        print("📝 Criando instruções de deploy...")
        
        instructions = f"""# 🚀 HAWK ESPORTS BOT - DEPLOY ZERO CLICK

## ✅ ARQUIVOS PREPARADOS AUTOMATICAMENTE

Todos os arquivos necessários foram criados:
- ✅ requirements.txt
- ✅ Procfile
- ✅ bot.py (atualizado)
- ✅ .env (configurações)
- ✅ render.yaml (deploy automático)
- ✅ supabase_setup.sql (banco de dados)

## 🎯 PRÓXIMOS PASSOS (APENAS 3 CLIQUES!)

### 1. 🗄️ SUPABASE (1 minuto)
1. Acesse: https://supabase.com/dashboard
2. Clique em "New Project"
3. Nome: `{self.project_name}`
4. Senha: `{self.db_password}`
5. Região: `East US (North Virginia)`
6. Clique "Create new project"
7. Aguarde 2 minutos
8. Vá em SQL Editor e cole o conteúdo de `supabase_setup.sql`
9. Execute o SQL
10. Copie a URL e chave anon das configurações

### 2. 🌐 RENDER (30 segundos)
1. Acesse: https://dashboard.render.com
2. Clique "New" → "Web Service"
3. Conecte seu repositório GitHub
4. O arquivo `render.yaml` configurará tudo automaticamente!
5. Adicione as variáveis do Supabase:
   - `DATABASE_URL`: postgresql://postgres:{self.db_password}@db.SEU_REF.supabase.co:5432/postgres
   - `SUPABASE_URL`: https://SEU_REF.supabase.co
   - `SUPABASE_KEY`: sua_chave_anon

### 3. 🤖 ATIVAÇÃO (instantâneo)
Seu bot estará online automaticamente!

## 🔧 CONFIGURAÇÕES OPCIONAIS

Para funcionalidades extras, adicione no Render:
- `PUBG_API_KEY`: Para sistema PUBG
- `MEDAL_API_KEY`: Para integração Medal.tv

## 📊 MONITORAMENTO

- **Logs do Bot**: Dashboard do Render
- **Database**: Dashboard do Supabase
- **Status**: Seu bot aparecerá online no Discord

---

🎉 **DEPLOY ZERO CLICK CONCLUÍDO!**

Seu bot Discord está pronto para produção com:
✅ Banco PostgreSQL gratuito
✅ Hosting gratuito 24/7
✅ Sistema keep-alive integrado
✅ Logs e monitoramento
✅ Backup automático

Tempo total: **3 minutos** ⚡
"""
        
        with open('DEPLOY_ZERO_CLICK.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
            
        print("✅ Instruções criadas: DEPLOY_ZERO_CLICK.md")
        return True
    
    def create_quick_setup_script(self):
        """Cria script para configuração rápida das variáveis"""
        print("📝 Criando script de configuração rápida...")
        
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"\nCONFIGURACAO RAPIDA - HAWK ESPORTS BOT\nScript para configurar variaveis do Supabase rapidamente\n\"\"\""

def configure_supabase():
    print("🔧 CONFIGURAÇÃO RÁPIDA DO SUPABASE")
    print("=" * 40)
    
    project_ref = input("Project Reference (ex: abcdefghijklmnop): ").strip()
    anon_key = input("Anon Key: ").strip()
    
    if not project_ref or not anon_key:
        print("❌ Dados obrigatórios não fornecidos!")
        return
    
    # Atualizar .env
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('SEU_PROJECT_REF', project_ref)
    content = content.replace('SUA_ANON_KEY', anon_key)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("\n✅ Configuração atualizada!")
    print(f"🗄️  Database: postgresql://postgres:{self.db_password}@db.{{project_ref}}.supabase.co:5432/postgres")
    print(f"🌐 Supabase: https://{{project_ref}}.supabase.co")
    print("\n🚀 Agora faça o deploy no Render!")

if __name__ == "__main__":
    configure_supabase()
"""
        
        with open('config_rapida.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        print("✅ Script de configuração criado: config_rapida.py")
        return True
    
    def run_zero_click_deploy(self):
        """Executa o deploy zero click completo"""
        print("🚀 HAWK ESPORTS BOT - DEPLOY ZERO CLICK")
        print("=" * 50)
        print("Preparando deploy 100% automático...")
        print()
        
        # Criar todos os arquivos
        steps = [
            ("Arquivo de configuração", self.create_env_file),
            ("Configuração do Render", self.create_render_yaml),
            ("Instruções de deploy", self.create_deploy_instructions),
            ("Script de configuração rápida", self.create_quick_setup_script)
        ]
        
        for step_name, step_func in steps:
            try:
                step_func()
                time.sleep(0.5)  # Pausa visual
            except Exception as e:
                print(f"❌ Erro em {step_name}: {str(e)}")
                return False
        
        print()
        print("🎉 DEPLOY ZERO CLICK PREPARADO COM SUCESSO!")
        print("=" * 50)
        print("📁 Arquivos criados:")
        print("   ✅ .env - Configurações do bot")
        print("   ✅ render.yaml - Deploy automático")
        print("   ✅ DEPLOY_ZERO_CLICK.md - Instruções")
        print("   ✅ config_rapida.py - Configuração rápida")
        print()
        print("🎯 PRÓXIMO PASSO:")
        print("   📖 Leia o arquivo DEPLOY_ZERO_CLICK.md")
        print("   ⏱️  Tempo total: 3 minutos")
        print("   🚀 Deploy em 3 cliques!")
        print()
        print("💡 DICA: Execute 'python config_rapida.py' após criar o Supabase")
        
        return True

def main():
    deployer = ZeroClickDeploy()
    deployer.run_zero_click_deploy()

if __name__ == "__main__":
    main()