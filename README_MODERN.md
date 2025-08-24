# 🦅 Hawk Bot - Versão Moderna

> Bot Discord refatorado com arquitetura moderna, injeção de dependências e sistemas otimizados

## 🚀 Novidades da Versão 2.0

### ✨ Arquitetura Moderna
- **Injeção de Dependências**: Sistema completo de DI com ciclo de vida gerenciado
- **Modularização**: Comandos organizados em Cogs separados
- **Cache Inteligente**: SmartCache com TTL adaptativo e estratégias otimizadas
- **Logging Estruturado**: Sistema de logs com sanitização de dados sensíveis
- **Configuração Tipada**: Validação completa com Pydantic

### 🔧 Melhorias de Performance
- **Cache Multi-Estratégia**: LRU, LFU, TTL e Adaptativo
- **Pool de Conexões**: Gerenciamento otimizado de conexões de banco
- **Monitoramento**: Métricas em tempo real e health checks
- **Garbage Collection**: Otimizações automáticas de memória

### 🛡️ Segurança e Confiabilidade
- **Sanitização de Dados**: Remoção automática de informações sensíveis dos logs
- **Rate Limiting**: Proteção contra spam e abuso
- **Validação de Entrada**: Validação rigorosa de todos os inputs
- **Graceful Shutdown**: Encerramento seguro com limpeza de recursos

## 📋 Pré-requisitos

- Python 3.9+
- PostgreSQL 12+ (recomendado) ou SQLite/JSON
- Redis (opcional, para cache distribuído)
- Dependências Python (ver `requirements.txt`)

## 🔧 Instalação

### 1. Clone o Repositório
```bash
git clone <repository-url>
cd bot-dc
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o Ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
nano .env
```

### 4. Configure o Banco de Dados

#### PostgreSQL (Recomendado)
```sql
-- Crie o banco e usuário
CREATE DATABASE hawkbot;
CREATE USER hawkbot_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE hawkbot TO hawkbot_user;
```

#### SQLite/JSON
O bot criará automaticamente os arquivos necessários.

### 5. Execute o Bot

#### Versão Moderna (Recomendada)
```bash
python -m src.core.modern_bot
```

#### Versão Legacy
```bash
python bot.py
```

## ⚙️ Configuração

### Arquivo .env

O arquivo `.env` contém todas as configurações do bot. Principais seções:

#### Discord
```env
DISCORD_BOT_TOKEN=seu_token_aqui
DISCORD_COMMAND_PREFIX=!
DISCORD_ENABLE_MESSAGE_CONTENT=true
```

#### Banco de Dados
```env
DATABASE_STORAGE_TYPE=postgresql
DATABASE_POSTGRESQL_HOST=localhost
DATABASE_POSTGRESQL_DATABASE=hawkbot
```

#### Cache
```env
CACHE_BACKEND=memory
CACHE_MEMORY_MAX_SIZE_MB=256
CACHE_MEMORY_STRATEGY=adaptive
```

#### APIs Externas
```env
API_PUBG_API_KEY=sua_chave_pubg
API_MEDAL_API_KEY=sua_chave_medal
```

#### Feature Flags
```env
FEATURE_RANKING_SYSTEM=true
FEATURE_MUSIC_SYSTEM=true
FEATURE_PUBG_INTEGRATION=true
```

### Configuração Avançada

Para configurações mais avançadas, edite diretamente os arquivos em `src/core/config.py`.

## 🏗️ Arquitetura

### Estrutura de Diretórios
```
src/
├── core/                    # Núcleo do sistema
│   ├── modern_bot.py       # Bot principal moderno
│   ├── config.py           # Sistema de configuração
│   ├── dependency_container.py  # Injeção de dependências
│   ├── smart_cache.py      # Cache inteligente
│   └── structured_logger.py # Logging estruturado
├── commands/               # Comandos organizados em Cogs
│   ├── pubg_commands.py    # Comandos PUBG
│   ├── music_commands.py   # Comandos de música
│   ├── season_commands.py  # Comandos de temporadas
│   └── admin_commands.py   # Comandos administrativos
├── systems/                # Sistemas de funcionalidades
├── storage/                # Camada de persistência
├── integrations/           # Integrações externas
└── web/                    # Dashboard web
```

### Fluxo de Inicialização

1. **Carregamento da Configuração**: Validação e carregamento das configurações
2. **Registro de Serviços**: Registro no container de DI
3. **Inicialização de Serviços**: Inicialização ordenada por dependências
4. **Resolução de Dependências**: Injeção automática de dependências
5. **Carregamento de Comandos**: Carregamento dos Cogs
6. **Conexão Discord**: Estabelecimento da conexão
7. **Sincronização**: Sincronização de comandos slash
8. **Tarefas Automáticas**: Início das tarefas em background

## 🎮 Comandos Disponíveis

### PUBG
- `/pubg_registrar` - Registrar jogador PUBG
- `/pubg_status` - Verificar status do jogador
- `/leaderboard_geral` - Ranking geral do servidor
- `/leaderboard_duplo` - Ranking de duplas
- `/atividade_servidor` - Atividade do servidor

### Música
- `/tocar` - Tocar música
- `/pausar` - Pausar música atual
- `/pular` - Pular música
- `/fila` - Ver fila de reprodução
- `/volume` - Ajustar volume

### Temporadas e Conquistas
- `/badges_disponiveis` - Ver emblemas disponíveis
- `/temporada_atual` - Informações da temporada atual
- `/minhas_recompensas` - Ver suas recompensas
- `/conquistas_usuario` - Ver suas conquistas

### Administração
- `/setup_inicial` - Configuração inicial do servidor
- `/backup_dados` - Fazer backup dos dados
- `/status_bot` - Status detalhado do bot
- `/limpar_cache` - Limpar cache do sistema

## 📊 Monitoramento

### Health Checks
O bot inclui endpoints de health check para monitoramento:

```python
# Verificar saúde do bot
health = await bot.get_health_status()
print(health)
```

### Métricas
```python
# Obter métricas detalhadas
metrics = await bot.get_metrics()
print(metrics)
```

### Logs Estruturados
Todos os logs são estruturados e incluem:
- Timestamp preciso
- Categoria do log
- Contexto (guild_id, user_id, etc.)
- Dados sanitizados
- Stack traces (quando aplicável)

## 🔧 Desenvolvimento

### Adicionando Novos Comandos

1. Crie um novo Cog em `src/commands/`:
```python
from discord.ext import commands
from ..core.structured_logger import log_info, LogCategory

class MeuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="meu_comando")
    async def meu_comando(self, interaction: discord.Interaction):
        log_info("Comando executado", LogCategory.COMMAND)
        await interaction.response.send_message("Olá!")

async def setup(bot):
    await bot.add_cog(MeuCog(bot))
```

2. Registre o Cog em `src/commands/__init__.py`

### Adicionando Novos Serviços

1. Crie uma classe que herda de `IService`:
```python
from ..core.dependency_container import IService

class MeuServico(IService):
    async def initialize(self):
        # Inicialização do serviço
        pass
    
    async def cleanup(self):
        # Limpeza de recursos
        pass
```

2. Registre no container:
```python
self.container.register(MeuServico, lifetime=ServiceLifetime.SINGLETON)
```

### Usando o Cache
```python
from ..core.smart_cache import cached, get_cache

# Usando o decorador
@cached(ttl=3600, tags=["user_data"])
async def get_user_data(user_id: str):
    # Função custosa
    return data

# Usando diretamente
cache = get_cache()
await cache.set("key", "value", ttl=3600)
value = await cache.get("key")
```

## 🐛 Troubleshooting

### Problemas Comuns

#### Bot não inicia
1. Verifique o token do Discord
2. Confirme as configurações do banco de dados
3. Verifique os logs em `./logs/hawkbot_errors.log`

#### Comandos não aparecem
1. Verifique se o bot tem permissões adequadas
2. Execute `/sync` se disponível
3. Verifique os logs de sincronização

#### Performance baixa
1. Monitore o uso de memória
2. Verifique as configurações de cache
3. Analise os logs de performance

### Logs e Debug

#### Habilitar Debug
```env
DEBUG_ENABLE_DEBUG_MODE=true
LOGGING_LEVEL=DEBUG
```

#### Localização dos Logs
- Logs gerais: `./logs/hawkbot.log`
- Logs de erro: `./logs/hawkbot_errors.log`
- Logs estruturados: Formato JSON para análise

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- Equipe Discord.py
- Comunidade Python
- Contribuidores do projeto

---

**Hawk Bot v2.0** - Desenvolvido com ❤️ pela Hawk Team