
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

**Deploy preparado em:** 22/08/2025 às 18:27:18
**Tempo estimado de deploy:** 5-10 minutos
**Custo:** R$ 0,00 (plano gratuito)

---

### 💡 Dicas Extras:
- O plano gratuito do Render hiberna após 15min de inatividade
- O keep_alive.py já está configurado para evitar isso
- Seu bot ficará online 24/7 sem custos
- Atualizações são automáticas via GitHub
