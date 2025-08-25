# 🦅 Hawk Bot - Bot Discord Profissional para Clã PUBG

## 📋 Descrição

Bot Discord completo e profissional desenvolvido especificamente para clãs de PUBG, oferecendo integração completa com a API oficial do PUBG, sistema de ranking automático, torneios, conquistas, música e muito mais.

## 🏗️ Arquitetura

O Hawk Bot foi completamente refatorado para seguir uma arquitetura modular e escalável:

- **Modular**: Cada funcionalidade é um módulo independente
- **Escalável**: Fácil adição de novas features
- **Testável**: Estrutura organizada para testes automatizados
- **Manutenível**: Código limpo e bem documentado

Veja a [documentação da arquitetura](docs/ARCHITECTURE.md) para mais detalhes.

## ✨ Principais Funcionalidades

## 🚀 Deploy no Render (Recomendado)

### Passo 1: Preparar Banco de Dados

**Opção A: PostgreSQL no Render**
1. Acesse [render.com](https://render.com) e faça login
2. Clique em "New" → "PostgreSQL"
3. Configure:
   - Name: `hawk-bot-db`
   - Database: `hawk_bot`
   - User: `hawk_user`
4. Anote as credenciais geradas

**Opção B: Supabase (Gratuito)**
1. Acesse [supabase.com](https://supabase.com)
2. Crie novo projeto
3. Vá em Settings → Database
4. Copie a Connection String

### Passo 2: Deploy do Bot

1. **Conectar Repositório**
   - No Render, clique em "New" → "Web Service"
   - Conecte seu repositório GitHub
   - Branch: `main`

2. **Configurações do Deploy**
   - Name: `hawk-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

3. **Configurar Variáveis de Ambiente** (veja seção abaixo)

### Passo 3: Configurar Discord Bot

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Crie nova aplicação
3. Vá em "Bot" → "Reset Token"
4. Copie o token e adicione nas variáveis de ambiente
5. Ative as "Privileged Gateway Intents"

## ⚙️ Variáveis de Ambiente

Configure estas variáveis no Render (Environment Variables):

### Obrigatórias

```env
# Discord Bot (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_do_bot_discord

# PostgreSQL Database (OBRIGATÓRIO)
DB_HOST=seu_host_do_banco
DB_NAME=seu_nome_do_banco  
DB_USER=seu_usuario_do_banco
DB_PASSWORD=sua_senha_do_banco
DB_PORT=5432

# Ou use DATABASE_URL (alternativa)
DATABASE_URL=postgresql://user:password@host:port/database
```

### Opcionais

```env
# PUBG API (para funcionalidades PUBG)
PUBG_API_KEY=sua_chave_da_api_pubg

# Configurações do Sistema
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO
STORAGE_TYPE=postgresql
CACHE_TYPE=memory

# Web Dashboard
WEB_PORT=8080
KEEP_ALIVE=true

# Configurações do Bot
COMMAND_PREFIX=!
MAX_RETRIES=3
```

### Como Configurar no Render

1. No painel do seu serviço no Render
2. Vá em "Environment"
3. Adicione cada variável:
   - Key: `DISCORD_TOKEN`
   - Value: `seu_token_aqui`
4. Clique em "Save Changes"
5. O serviço será reiniciado automaticamente

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

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- PostgreSQL (opcional, para produção)
- Git

### Método 1: Setup Rápido (Recomendado)

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/hawk-bot.git
cd hawk-bot
```

2. **Execute o setup automático:**
```bash
python scripts/setup/config_rapida.py
```

3. **Configure o banco de dados (opcional):**
```bash
python scripts/setup/supabase_auto_setup.py
```

4. **Inicie o bot:**
```bash
python main.py
```

### Método 2: Instalação Manual

1. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

2. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Execute o bot:**
```bash
python main.py
```

## 📁 Estrutura do Projeto

```
bot-dc/
├── src/                    # Código fonte principal
│   ├── core/              # Módulos essenciais
│   │   ├── bot.py         # Classe principal do bot
│   │   ├── config.py      # Configurações globais
│   │   └── storage.py     # Sistema de armazenamento
│   ├── features/          # Funcionalidades do bot
│   │   ├── music/         # Sistema de música
│   │   ├── pubg/          # Integração PUBG
│   │   ├── tournaments/   # Sistema de torneios
│   │   └── checkin/       # Sistema de check-in
│   ├── integrations/      # Integrações externas
│   │   └── medal/         # Integração Medal.tv
│   ├── utils/             # Utilitários
│   └── web/               # Interface web
├── config/                # Arquivos de configuração
├── data/                  # Dados JSON
├── database/              # Scripts SQL
├── docs/                  # Documentação
├── scripts/               # Scripts de setup e deploy
├── tests/                 # Testes automatizados
└── main.py               # Ponto de entrada
```

## 🚀 Funcionalidades Principais

## 👨‍💻 Desenvolvimento

Para contribuir com o desenvolvimento do Hawk Bot:

1. **Leia a documentação:**
   - [Guia de Arquitetura](docs/ARCHITECTURE.md)
   - [Guia de Desenvolvimento](docs/DEVELOPMENT_GUIDE.md)

2. **Configure o ambiente de desenvolvimento:**
```bash
# Clone e instale dependências
git clone https://github.com/seu-usuario/hawk-bot.git
cd hawk-bot
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
```

3. **Execute os testes:**
```bash
pytest
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Siga os padrões de código estabelecidos
4. Adicione testes para novas funcionalidades
5. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
6. Push para a branch (`git push origin feature/AmazingFeature`)
7. Abra um Pull Request