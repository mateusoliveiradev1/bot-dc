# 🦅 Hawk Esports Discord Bot

Um bot Discord completo para comunidades de esports com sistema de check-in, torneios, rankings e muito mais!

## 🚀 Deploy Gratuito

### Opção 1: Railway (Recomendado)

1. **Criar conta no Railway**
   - Acesse [railway.app](https://railway.app)
   - Faça login com GitHub

2. **Configurar banco de dados PostgreSQL**
   - No Railway, clique em "New Project"
   - Selecione "Provision PostgreSQL"
   - Anote as credenciais do banco

3. **Deploy do bot**
   - Clique em "New Project" → "Deploy from GitHub repo"
   - Conecte seu repositório
   - Configure as variáveis de ambiente (veja abaixo)

### Opção 2: Render + Supabase

1. **Banco de dados no Supabase**
   - Acesse [supabase.com](https://supabase.com)
   - Crie um novo projeto
   - Anote as credenciais de conexão

2. **Deploy no Render**
   - Acesse [render.com](https://render.com)
   - Conecte seu repositório GitHub
   - Configure como "Web Service"

## ⚙️ Variáveis de Ambiente

Configure estas variáveis no seu provedor de deploy:

```env
# Discord Bot
DISCORD_TOKEN=seu_token_do_bot_discord

# PostgreSQL Database
DB_HOST=seu_host_do_banco
DB_NAME=seu_nome_do_banco
DB_USER=seu_usuario_do_banco
DB_PASSWORD=sua_senha_do_banco
DB_PORT=5432

# PUBG API (opcional)
PUBG_API_KEY=sua_chave_da_api_pubg

# Configurações
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO
```

## 🛠️ Desenvolvimento Local

1. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar ambiente**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. **Executar o bot**
   ```bash
   python bot.py
   ```

## 🚀 Funcionalidades Principais