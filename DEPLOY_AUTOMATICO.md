# 🚀 Deploy Automático - Render + Supabase

## 📋 **Plano de Deploy**

✅ **Eu faço (Automático):**
- Configurar projeto no Supabase
- Criar tabelas do banco de dados
- Gerar connection string
- Preparar todas as variáveis de ambiente

🔧 **Você faz (Passo-a-passo):**
- Seguir o guia do Render
- Colar as variáveis que eu fornecer
- Testar o funcionamento

---

## 🎯 **PARTE 1: Configuração Automática do Supabase**

### 📝 **Informações Necessárias:**

Para configurar automaticamente, preciso que você me forneça:

1. **Token do Discord Bot** (já deve ter)
2. **API Key do PUBG** (se usar)
3. **Token do Medal.tv** (se usar)
4. **Nome do projeto** (ex: "hawk-esports-bot")

### 🔄 **Processo Automático:**

1. **Criar projeto no Supabase**
2. **Executar SQL para criar tabelas:**
   ```sql
   -- Tabela de usuários
   CREATE TABLE users (
       user_id BIGINT PRIMARY KEY,
       username TEXT,
       display_name TEXT,
       avatar_url TEXT,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW(),
       data JSONB DEFAULT '{}'
   );

   -- Tabela de configurações do bot
   CREATE TABLE bot_settings (
       key TEXT PRIMARY KEY,
       value JSONB,
       updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Tabela de sessões
   CREATE TABLE sessions (
       session_id TEXT PRIMARY KEY,
       user_id BIGINT,
       data JSONB DEFAULT '{}',
       expires_at TIMESTAMP,
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- Índices para performance
   CREATE INDEX idx_users_username ON users(username);
   CREATE INDEX idx_sessions_user_id ON sessions(user_id);
   CREATE INDEX idx_sessions_expires ON sessions(expires_at);
   ```

3. **Configurar políticas de segurança (RLS)**
4. **Gerar connection string segura**

---

## 🔧 **PARTE 2: Seu Passo-a-Passo no Render**

### **Passo 1: Preparar Repositório GitHub**

```bash
# 1. Inicializar Git (se ainda não fez)
git init

# 2. Adicionar todos os arquivos
git add .

# 3. Fazer commit inicial
git commit -m "Deploy inicial do Hawk Esports Bot"

# 4. Conectar ao GitHub (substitua pelo seu repositório)
git remote add origin https://github.com/SEU_USUARIO/hawk-esports-bot.git

# 5. Enviar para GitHub
git push -u origin main
```

### **Passo 2: Criar Serviço no Render**

1. **Acesse:** https://render.com
2. **Faça login** com GitHub
3. **Clique em "New +"** → **"Web Service"**
4. **Conecte seu repositório** GitHub
5. **Configure:**
   - **Name:** `hawk-esports-bot`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** `Free`

### **Passo 3: Configurar Variáveis de Ambiente**

**Na seção "Environment Variables" do Render, adicione:**

```env
# ⚠️ EU VOU FORNECER ESTES VALORES APÓS CONFIGURAR O SUPABASE
DISCORD_TOKEN=seu_token_aqui
DATABASE_URL=postgresql://...
POSTGRES_HOST=...
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_PORT=5432

# Opcionais (se usar)
PUBG_API_KEY=sua_api_key_pubg
MEDAL_TOKEN=seu_token_medal

# Configurações do bot
BOT_PREFIX=!
DEBUG=false
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# Para evitar hibernação
RENDER=true
```

### **Passo 4: Deploy**

1. **Clique em "Create Web Service"**
2. **Aguarde o build** (5-10 minutos)
3. **Verifique os logs** para erros
4. **Bot deve ficar online** no Discord

---

## 🔍 **PARTE 3: Verificação e Testes**

### **Comandos para Testar:**

```
# No Discord, teste:
!ping              # Verifica se bot responde
!help              # Lista comandos disponíveis
!status            # Status do sistema
!db_test           # Testa conexão com banco
```

### **Verificar Logs:**

1. **No Render:** Aba "Logs"
2. **Procurar por:**
   - ✅ `Bot conectado como: NomeDoBot`
   - ✅ `PostgreSQL conectado com sucesso`
   - ✅ `Keep-alive iniciado`
   - ❌ Erros de conexão

---

## 🆘 **Troubleshooting**

### **Problemas Comuns:**

**1. Bot não conecta:**
- Verificar `DISCORD_TOKEN`
- Token deve ter permissões de bot

**2. Erro de banco:**
- Verificar connection string
- Supabase deve estar ativo

**3. Bot hiberna:**
- Verificar `RENDER=true`
- Keep-alive deve estar funcionando

**4. Comandos não funcionam:**
- Verificar permissões do bot no servidor
- Bot deve ter permissão de "Send Messages"

---

## 📞 **Próximos Passos**

1. **Me forneça as informações necessárias**
2. **Eu configuro o Supabase automaticamente**
3. **Você segue o passo-a-passo do Render**
4. **Testamos juntos o funcionamento**

**Pronto para começar? Me envie:**
- Token do Discord Bot
- API Keys (se tiver)
- Nome desejado para o projeto

🚀 **Vamos fazer seu bot ficar online em menos de 30 minutos!**