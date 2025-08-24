# Guia de Desenvolvimento - Hawk Bot

## Configuração do Ambiente

### Pré-requisitos
- Python 3.8+
- PostgreSQL (opcional, para produção)
- Git

### Instalação

1. **Clone o repositório**
```bash
git clone <repository-url>
cd bot-dc
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. **Execute o bot**
```bash
python main.py
```

## Estrutura de Desenvolvimento

### Adicionando uma Nova Feature

1. **Crie o módulo da feature**
```bash
mkdir src/features/nova_feature
touch src/features/nova_feature/__init__.py
touch src/features/nova_feature/commands.py
```

2. **Implemente a funcionalidade**
```python
# src/features/nova_feature/commands.py
import discord
from discord.ext import commands

class NovaFeature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def novo_comando(self, ctx):
        await ctx.send("Nova funcionalidade!")
```

3. **Configure o __init__.py**
```python
# src/features/nova_feature/__init__.py
"""Nova feature do bot."""

from .commands import NovaFeature

__all__ = ['NovaFeature']
```

4. **Registre no bot principal**
```python
# No arquivo principal do bot
from src.features.nova_feature import NovaFeature

# Adicione o cog
bot.add_cog(NovaFeature(bot))
```

### Padrões de Código

#### Imports
- Use imports absolutos a partir de `src/`
- Organize imports por: stdlib, third-party, local
- Use `from . import` para imports relativos dentro do módulo

```python
# Correto
import asyncio
import logging

import discord
from discord.ext import commands

from src.core import DataStorage
from src.utils import embed_templates
from .helpers import helper_function
```

#### Estrutura de Classes
```python
class MinhaClasse:
    """Docstring descrevendo a classe."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = self._load_config()
    
    def _load_config(self):
        """Método privado para carregar configurações."""
        pass
    
    async def metodo_publico(self):
        """Método público assíncrono."""
        pass
```

#### Configurações
- Armazene configurações em `config/features/`
- Use JSON para configurações simples
- Use variáveis de ambiente para dados sensíveis

```python
# Carregando configuração
import json
from pathlib import Path

config_path = Path('config/features/minha_feature.json')
with open(config_path) as f:
    config = json.load(f)
```

### Testes

#### Estrutura de Testes
```python
# tests/unit/test_features/test_nova_feature.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.features.nova_feature import NovaFeature

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    return bot

@pytest.fixture
def nova_feature(mock_bot):
    return NovaFeature(mock_bot)

@pytest.mark.asyncio
async def test_novo_comando(nova_feature):
    ctx = AsyncMock()
    await nova_feature.novo_comando(ctx)
    ctx.send.assert_called_once_with("Nova funcionalidade!")
```

#### Executando Testes
```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/unit/test_features/

# Com cobertura
pytest --cov=src
```

### Banco de Dados

#### Usando DataStorage
```python
from src.core import DataStorage

# Inicializar storage
storage = DataStorage()

# Salvar dados
await storage.save_user_data(user_id, data)

# Carregar dados
data = await storage.load_user_data(user_id)
```

#### Migrações PostgreSQL
1. Crie o script SQL em `database/`
2. Execute via `scripts/setup/supabase_auto_setup.py`

### Logging

```python
import logging

logger = logging.getLogger(__name__)

class MinhaClasse:
    def metodo(self):
        logger.info("Informação importante")
        logger.warning("Aviso")
        logger.error("Erro ocorreu")
```

### Deploy

#### Desenvolvimento Local
```bash
python main.py
```

#### Produção (Render)
```bash
# Use os scripts de deploy
python scripts/deploy/render_deploy.py
```

## Boas Práticas

### Código
- Use type hints sempre que possível
- Docstrings para classes e métodos públicos
- Nomes descritivos para variáveis e funções
- Mantenha funções pequenas e focadas
- Use async/await para operações I/O

### Git
- Commits pequenos e focados
- Mensagens de commit descritivas
- Use branches para features
- Faça pull requests para revisão

### Performance
- Use cache quando apropriado
- Evite operações síncronas em handlers assíncronos
- Monitore uso de memória
- Use connection pooling para banco de dados

### Segurança
- Nunca commite tokens ou senhas
- Use variáveis de ambiente para dados sensíveis
- Valide inputs do usuário
- Use rate limiting quando necessário

## Troubleshooting

### Problemas Comuns

1. **Import Error**
   - Verifique se o `sys.path` inclui o diretório `src/`
   - Confirme que todos os `__init__.py` existem

2. **Database Connection**
   - Verifique as variáveis de ambiente
   - Confirme que o PostgreSQL está rodando

3. **Discord API Errors**
   - Verifique se o token está correto
   - Confirme as permissões do bot

### Debug
```python
# Ativar debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug específico do discord.py
logging.getLogger('discord').setLevel(logging.DEBUG)
```

## Recursos Úteis

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [PUBG API Documentation](https://documentation.pubg.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)