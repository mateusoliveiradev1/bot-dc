# 📋 Guia Completo de Deploy - Hawk Esports Bot

## 🎯 Opção Recomendada: Render + Supabase (100% Gratuito)

### Passo 1: Configurar Banco de Dados PostgreSQL no Supabase

1. **Criar conta no Supabase**
   - Acesse: https://supabase.com
   - Clique em "Start your project"
   - Faça login com sua conta GitHub

2. **Criar projeto PostgreSQL**
   - Clique em "New project"
   - Escolha sua organização
   - Nome do projeto: "hawk-esports-bot"
   - Senha do banco: anote uma senha forte
   - Região: escolha a mais próxima (São Paulo se disponível)
   - Clique em "Create new project"

3. **Obter credenciais do banco**
   - Aguarde a criação do projeto (2-3 minutos)
   - Vá em "Settings" → "Database"
   - Na seção "Connection info", anote:
     - Host (DB_HOST)
     - Database name (DB_NAME)
     - Username (DB_USER)
     - Password (DB_PASSWORD)
     - Port (DB_PORT - sempre 5432)

### Passo 2: Deploy no Render

1. **Criar conta no Render**
   - Acesse: https://render.com
   - Clique em "Get Started"
   - Faça login com sua conta GitHub

2. **Criar Web Service**
   - No dashboard, clique em "New" → "Web Service"
   - Conecte seu repositório GitHub
   - Escolha o repositório do bot
   - Configure:
     - Name: "hawk-esports-bot"
     - Environment: "Python 3"
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python bot.py`
     - Instance Type: "Free"

3. **Configurar variáveis de ambiente**
   - Na seção "Environment Variables", adicione:
   ```env
   DISCORD_TOKEN=SEU_TOKEN_DO_BOT_DISCORD
   DB_HOST=valor_do_host_supabase
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=sua_senha_do_supabase
   DB_PORT=5432
   TIMEZONE=America/Sao_Paulo
   LOG_LEVEL=INFO
   ```

4. **Fazer deploy**
   - Clique em "Create Web Service"
   - Aguarde o build e deploy (5-10 minutos)

### Passo 3: Preparar Repositório GitHub

1. **Criar repositório no GitHub**
   - Vá para https://github.com
   - Clique em "New repository"
   - Nome: `hawk-esports-bot` (ou outro nome)
   - Marque como "Public" (necessário para Render gratuito)

2. **Fazer upload dos arquivos**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Hawk Esports Bot"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/hawk-esports-bot.git
   git push -u origin main
   ```

### Passo 4: Verificar Funcionamento

1. **Verificar logs no Render**
   - No dashboard do Render, clique no seu serviço
   - Vá na aba "Logs"
   - Verifique se não há erros
   - Procure por mensagens como:
     - "🐘 Usando PostgreSQL como sistema de armazenamento"
     - "Bot Hawk Esports conectado como [NOME_DO_BOT]"

2. **Testar no Discord**
   - Convide o bot para seu servidor
   - Teste comandos básicos como `/ping`
   - Teste o sistema de check-in com `/checkin`

3. **Monitorar no Supabase**
   - No Supabase, vá em "Table Editor"
   - Verifique se as tabelas foram criadas automaticamente
   - Teste alguns comandos e veja os dados sendo inseridos

## 🔧 Alternativa: Heroku (Se disponível)

### Opção Heroku + PostgreSQL

1. **Criar conta no Heroku**
   - Acesse: https://heroku.com
   - Crie uma conta gratuita (se ainda disponível)

2. **Instalar Heroku CLI**
   ```bash
   # Windows
   winget install Heroku.CLI
   ```

3. **Deploy via CLI**
   ```bash
   heroku login
   heroku create hawk-esports-bot
   heroku addons:create heroku-postgresql:hobby-dev
   git push heroku main
   ```

4. **Configurar variáveis**
   ```bash
   heroku config:set DISCORD_TOKEN=seu_token
   heroku config:set TIMEZONE=America/Sao_Paulo
   ```

## 🚨 Troubleshooting

### Erro: "Bot não conecta"
- Verifique se o DISCORD_TOKEN está correto
- Confirme que o bot tem as permissões necessárias

### Erro: "Falha na conexão com banco"
- Verifique todas as credenciais do banco
- Confirme que o banco está ativo
- Teste a conexão manualmente

### Erro: "Módulo não encontrado"
- Verifique se requirements.txt está completo
- Force um redeploy

## 💡 Dicas Importantes

1. **Limites gratuitos Render:**
   - 750 horas por mês (suficiente para 24/7)
   - 512MB RAM
   - Hiberna após 15min de inatividade (reativa automaticamente)
   - Build time: 500 minutos/mês

2. **Limites gratuitos Supabase:**
   - 500MB de storage
   - 2GB de transferência/mês
   - Até 50MB de backup
   - 2 projetos simultâneos

3. **Evitar hibernação (Render):**
   - Use um serviço como UptimeRobot para fazer ping a cada 10min
   - Ou configure um cron job interno no bot

4. **Monitoramento:**
   - Configure alertas no Discord quando o bot ficar offline
   - Use o dashboard do Supabase para monitorar o banco
   - Verifique logs regularmente no Render

5. **Backup:**
   - O sistema faz backup automático dos dados
   - Dados JSON locais são migrados automaticamente
   - Supabase mantém backups automáticos por 7 dias

---

**✅ Após seguir este guia, seu bot estará rodando 24/7 gratuitamente!**