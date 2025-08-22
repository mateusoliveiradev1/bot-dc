# Guia de Instalação - Bot Discord Hawk Esports

## ⚠️ IMPORTANTE: Python não encontrado!

Para executar o bot, você precisa instalar o Python primeiro.

## 📋 Pré-requisitos

### 1. Instalar Python 3.10+

**Opção 1: Site oficial (Recomendado)**
1. Acesse: https://www.python.org/downloads/
2. Baixe a versão mais recente (3.10 ou superior)
3. **IMPORTANTE**: Durante a instalação, marque "Add Python to PATH"
4. Execute a instalação como administrador

**Opção 2: Microsoft Store**
1. Abra a Microsoft Store
2. Procure por "Python 3.11" ou "Python 3.12"
3. Instale a versão mais recente

### 2. Verificar instalação
Após instalar, abra um novo terminal e execute:
```bash
python --version
```
Deve mostrar algo como: `Python 3.11.x`

## 🚀 Instalação do Bot

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar o arquivo .env
1. Abra o arquivo `.env`
2. Preencha as chaves necessárias:
   - `DISCORD_TOKEN`: Token do seu bot Discord
   - `PUBG_API_KEY`: Chave da API do PUBG
   - Outros parâmetros conforme necessário

### 3. Executar o bot
```bash
python bot.py
```

## 🔧 Configuração Discord

### 1. Criar aplicação Discord
1. Acesse: https://discord.com/developers/applications
2. Clique em "New Application"
3. Dê um nome (ex: "Hawk Esports Bot")
4. Vá em "Bot" → "Add Bot"
5. Copie o token e cole no `.env`

### 2. Permissões necessárias
O bot precisa das seguintes permissões:
- ✅ Manage Roles
- ✅ Manage Channels
- ✅ Send Messages
- ✅ Use Slash Commands
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Attach Files
- ✅ Embed Links

### 3. Adicionar bot ao servidor
1. Vá em "OAuth2" → "URL Generator"
2. Marque "bot" e "applications.commands"
3. Selecione as permissões listadas acima
4. Copie a URL gerada e abra no navegador
5. Selecione seu servidor e autorize

## 🎮 PUBG API

1. Acesse: https://developer.pubg.com/
2. Crie uma conta
3. Gere uma API key
4. Cole a chave no arquivo `.env`

## ✅ Primeiros passos

1. Execute o bot: `python bot.py`
2. No Discord, use: `/setup_server`
3. Membros podem se registrar: `/register_pubg nome:SeuNick shard:steam`
4. Verifique rankings: `/leaderboard`

## 🆘 Problemas comuns

**"Python was not found"**
- Reinstale o Python marcando "Add to PATH"
- Reinicie o terminal após instalação

**"Module not found"**
- Execute: `pip install -r requirements.txt`

**"Invalid token"**
- Verifique se o token no `.env` está correto
- Regenere o token se necessário

**Bot não responde**
- Verifique se o bot tem permissões no servidor
- Confirme se as slash commands estão habilitadas

---

🎯 **Bot criado para o clã Hawk Esports**
📧 **Suporte**: Verifique os logs do bot para mais detalhes sobre erros