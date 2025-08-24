# 🚀 Guia de Deploy no Render - Hawk Esports Bot

## 📋 Pré-requisitos

- Conta no [Render](https://render.com)
- Repositório GitHub com o código do bot
- Token do Discord Bot
- (Opcional) PUBG API Key para funcionalidades completas

## 🔧 Configuração no Render

### 1. Criar Novo Web Service

1. Acesse o dashboard do Render
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure as seguintes opções:

```
Name: hawk-esports-bot
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python main.py
```

### 2. Variáveis de Ambiente Obrigatórias

Configure estas variáveis na seção "Environment":

```bash
# Discord Configuration (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_do_discord_aqui

# Bot Configuration
BOT_PREFIX=!
DEBUG=false
RENDER=true
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# Web Dashboard
WEB_PORT=10000
WEB_HOST=0.0.0.0

# Storage
STORAGE_TYPE=json

# Features
ENABLE_MUSIC=true
```

### 3. Variáveis Opcionais (Para Funcionalidades Completas)

```bash
# PUBG API (Opcional - para ranking real)
PUBG_API_KEY=sua_pubg_api_key_aqui

# Medal API (Opcional - para clips)
MEDAL_API_KEY=sua_medal_api_key_aqui

# Database (Opcional - para produção avançada)
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🎯 Funcionalidades Disponíveis

### ✅ Funcionando Sem APIs Externas
- ✅ Sistema de registro de jogadores
- ✅ Sistema de conquistas
- ✅ Mini-games (Quiz, Adivinhação, etc.)
- ✅ Sistema de música
- ✅ Dashboard web moderno
- ✅ Sistema de moderação
- ✅ Canais dinâmicos
- ✅ Sistema de lembretes
- ✅ Gráficos e estatísticas

### 🔑 Requer PUBG API Key
- 🔑 Ranking PUBG real
- 🔑 Atualização automática de stats
- 🔑 Sistema de roles baseado em rank

### 🎬 Requer Medal API Key
- 🎬 Sistema de clips automático
- 🎬 Integração com Medal.tv

## 🚀 Deploy

1. **Push do código**: Certifique-se que todo código está no GitHub
2. **Configurar variáveis**: Adicione pelo menos `DISCORD_TOKEN`
3. **Deploy**: O Render fará deploy automaticamente
4. **Verificar logs**: Monitore os logs para garantir inicialização correta

## 📊 Monitoramento

### Logs Importantes
```
✅ Bot conectado como: [Nome do Bot]
✅ Dashboard iniciado em: http://0.0.0.0:10000
✅ Sistemas carregados: [Lista de sistemas]
```

### URLs de Acesso
- **Bot Discord**: Funcionará automaticamente nos servidores
- **Dashboard Web**: `https://seu-app.onrender.com`

## 🔧 Comandos Principais do Bot

### Registro e Perfil
- `/registrar` - Registrar no sistema
- `/perfil` - Ver perfil completo
- `/conquistas` - Ver conquistas

### Rankings
- `/ranking_pubg` - Ranking PUBG (requer API)
- `/ranking_jogos` - Ranking mini-games
- `/leaderboard` - Leaderboard geral

### Mini-Games
- `/quiz` - Jogo de quiz
- `/adivinhar` - Jogo de adivinhação
- `/coinflip` - Cara ou coroa

### Música
- `/play` - Tocar música
- `/queue` - Ver fila
- `/skip` - Pular música

### Administração
- `/force_rank_update` - Forçar atualização de rank
- `/tournament_create` - Criar torneio

## 🛠️ Troubleshooting

### Bot não conecta
- ✅ Verificar se `DISCORD_TOKEN` está correto
- ✅ Verificar logs do Render
- ✅ Verificar se o bot tem permissões no servidor

### Dashboard não carrega
- ✅ Verificar se `WEB_PORT=10000` está configurado
- ✅ Verificar se `WEB_HOST=0.0.0.0` está configurado
- ✅ Acessar via URL do Render

### Ranking PUBG não funciona
- ✅ Configurar `PUBG_API_KEY`
- ✅ Verificar se a API key é válida
- ✅ Usar comandos básicos enquanto isso

## 📈 Próximos Passos

1. **Deploy Básico**: Configure apenas `DISCORD_TOKEN` para começar
2. **Teste Funcionalidades**: Use comandos básicos para testar
3. **APIs Externas**: Adicione PUBG_API_KEY quando disponível
4. **Monitoramento**: Configure alertas no Render
5. **Backup**: Configure backup automático dos dados

## 🎉 Status Atual

- ✅ **Código**: 100% funcional e testado
- ✅ **Sintaxe**: Todos erros corrigidos
- ✅ **Sistemas**: Todos sistemas modernizados funcionando
- ✅ **Dashboard**: Interface web moderna operacional
- ✅ **Deploy Ready**: Pronto para produção no Render

---

**🚀 O bot está 100% pronto para deploy no Render!**

Apenas configure o `DISCORD_TOKEN` e faça o deploy. Todas as funcionalidades básicas funcionarão imediatamente, e você pode adicionar APIs externas posteriormente para funcionalidades avançadas.