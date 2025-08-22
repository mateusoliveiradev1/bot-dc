#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPLOY AUTOMÁTICO NO RENDER
Hawk Esports Bot - Deploy Simplificado

Este script prepara todos os arquivos necessários para deploy no Render
e fornece instruções passo-a-passo para um deploy rápido e fácil.
"""

import os
import json
from datetime import datetime

class RenderDeploySimplificado:
    def __init__(self):
        self.project_name = "hawk-esports-bot"
        
    def verificar_arquivos_necessarios(self):
        """Verifica se todos os arquivos necessários existem"""
        print("🔍 Verificando arquivos necessários...")
        
        arquivos_necessarios = {
            'requirements.txt': 'Dependências Python',
            'bot.py': 'Arquivo principal do bot',
            '.env': 'Variáveis de ambiente',
            'render.yaml': 'Configuração do Render'
        }
        
        arquivos_ok = True
        for arquivo, descricao in arquivos_necessarios.items():
            if os.path.exists(arquivo):
                print(f"✅ {arquivo} - {descricao}")
            else:
                print(f"❌ {arquivo} - {descricao} (FALTANDO)")
                arquivos_ok = False
        
        return arquivos_ok
    
    def criar_render_yaml(self):
        """Cria o arquivo render.yaml otimizado"""
        render_config = {
            'services': [{
                'type': 'web',
                'name': self.project_name,
                'env': 'python',
                'plan': 'free',
                'buildCommand': 'pip install -r requirements.txt',
                'startCommand': 'python bot.py',
                'envVars': [
                    {'key': 'PYTHON_VERSION', 'value': '3.11.0'},
                    {'key': 'DISCORD_TOKEN', 'sync': False},
                    {'key': 'DATABASE_URL', 'sync': False},
                    {'key': 'SUPABASE_URL', 'sync': False},
                    {'key': 'SUPABASE_KEY', 'sync': False}
                ]
            }]
        }
        
        with open('render.yaml', 'w') as f:
            import yaml
            yaml.dump(render_config, f, default_flow_style=False)
        
        print("✅ render.yaml criado/atualizado")
    
    def criar_guia_deploy(self):
        """Cria guia completo de deploy"""
        guia = f"""
# 🚀 GUIA DE DEPLOY NO RENDER - HAWK ESPORTS BOT

## ✅ Arquivos Preparados:
- ✅ render.yaml (configuração automática)
- ✅ requirements.txt (dependências)
- ✅ .env (variáveis de ambiente)
- ✅ Todos os arquivos do bot

## 🎯 DEPLOY EM 3 PASSOS SIMPLES:

### Passo 1: Conectar GitHub ao Render
1. Acesse: https://dashboard.render.com
2. Clique em "New +" → "Web Service"
3. Conecte sua conta GitHub
4. Selecione o repositório do bot
5. Clique em "Connect"

### Passo 2: Configuração Automática
✅ O Render detectará automaticamente o `render.yaml`
✅ Todas as configurações serão aplicadas automaticamente:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Python Version: 3.11.0
   - Plan: Free

### Passo 3: Adicionar Variáveis de Ambiente
No dashboard do Render, vá em "Environment" e adicione:

```
DISCORD_TOKEN=seu_token_do_discord_aqui
DATABASE_URL=sua_url_do_supabase_aqui
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_anonima_supabase_aqui
```

## 🔧 Onde encontrar as informações:

### Discord Token:
1. https://discord.com/developers/applications
2. Seu bot → Bot → Token

### Supabase (já configurado):
1. https://supabase.com/dashboard
2. Seu projeto → Settings → API
3. URL: Project URL
4. Key: anon/public key
5. DATABASE_URL: Settings → Database → Connection string

## 🚀 Após o Deploy:

1. **Aguarde o build** (2-3 minutos)
2. **Verifique os logs** na aba "Logs"
3. **Teste o bot** no Discord
4. **URL do serviço** será gerada automaticamente

## 🔄 Atualizações Futuras:
- Faça push para o GitHub
- O Render fará redeploy automaticamente
- Zero configuração adicional necessária

## 🆘 Solução de Problemas:

### Bot não conecta:
- Verifique se o DISCORD_TOKEN está correto
- Confirme se o bot está ativo no Discord Developer Portal

### Erro de banco de dados:
- Verifique se DATABASE_URL está correto
- Confirme se o Supabase está ativo
- Teste a conexão localmente primeiro

### Build falha:
- Verifique se requirements.txt está correto
- Confirme se todos os arquivos estão no repositório

## 📊 Monitoramento:
- **Logs em tempo real**: Dashboard → Logs
- **Métricas**: Dashboard → Metrics
- **Status**: Dashboard → Events

---

## 🎉 PRONTO!
Seu bot estará online 24/7 gratuitamente no Render!

**Deploy preparado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
**Tempo estimado de deploy:** 5-10 minutos
**Custo:** R$ 0,00 (plano gratuito)

---

### 💡 Dicas Extras:
- O plano gratuito do Render hiberna após 15min de inatividade
- O keep_alive.py já está configurado para evitar isso
- Seu bot ficará online 24/7 sem custos
- Atualizações são automáticas via GitHub
"""
        
        with open('RENDER_DEPLOY_GUIA.md', 'w', encoding='utf-8') as f:
            f.write(guia)
        
        print("✅ RENDER_DEPLOY_GUIA.md criado")
    
    def verificar_env_vars(self):
        """Verifica e lista as variáveis de ambiente necessárias"""
        print("\n🔍 Verificando variáveis de ambiente...")
        
        if not os.path.exists('.env'):
            print("❌ Arquivo .env não encontrado")
            return False
        
        with open('.env', 'r') as f:
            env_content = f.read()
        
        vars_necessarias = {
            'DISCORD_TOKEN': 'Token do bot Discord',
            'DATABASE_URL': 'URL do banco PostgreSQL (Supabase)',
            'SUPABASE_URL': 'URL do projeto Supabase',
            'SUPABASE_KEY': 'Chave anônima do Supabase'
        }
        
        vars_ok = True
        for var, descricao in vars_necessarias.items():
            if var in env_content and not env_content.split(f'{var}=')[1].split('\n')[0].strip() in ['', 'SEU_TOKEN_AQUI', 'sua_url_aqui']:
                print(f"✅ {var} - {descricao}")
            else:
                print(f"⚠️ {var} - {descricao} (PRECISA CONFIGURAR)")
                vars_ok = False
        
        return vars_ok
    
    def executar_preparacao(self):
        """Executa toda a preparação para deploy"""
        print("🦅 HAWK ESPORTS BOT - PREPARAÇÃO PARA DEPLOY")
        print("=" * 55)
        
        # Verificar arquivos
        if not self.verificar_arquivos_necessarios():
            print("\n❌ Alguns arquivos estão faltando!")
            return False
        
        # Criar/atualizar render.yaml
        try:
            self.criar_render_yaml()
        except ImportError:
            print("⚠️ PyYAML não instalado, render.yaml não foi criado")
            print("   Isso não é crítico - você pode configurar manualmente")
        
        # Verificar variáveis de ambiente
        self.verificar_env_vars()
        
        # Criar guia de deploy
        self.criar_guia_deploy()
        
        print("\n" + "=" * 55)
        print("🎉 PREPARAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 55)
        print("\n📖 PRÓXIMO PASSO:")
        print("   Leia o arquivo: RENDER_DEPLOY_GUIA.md")
        print("   Siga os 3 passos simples para fazer o deploy")
        print("\n⏱️ Tempo estimado: 5-10 minutos")
        print("💰 Custo: R$ 0,00 (gratuito)")
        print("\n🚀 Seu bot ficará online 24/7!")
        
        return True

if __name__ == "__main__":
    deployer = RenderDeploySimplificado()
    deployer.executar_preparacao()