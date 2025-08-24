# Arquitetura do Hawk Bot

## Visão Geral

O Hawk Bot foi refatorado para seguir uma arquitetura modular e escalável, organizando o código em módulos bem definidos e separando responsabilidades.

## Estrutura de Diretórios

```
bot-dc/
├── src/                    # Código fonte principal
│   ├── core/              # Sistemas fundamentais
│   │   ├── bot.py         # Configuração principal do bot
│   │   ├── config/        # Configurações e settings
│   │   ├── database/      # Modelos e conexões de banco
│   │   └── storage/       # Sistemas de armazenamento
│   ├── features/          # Funcionalidades do bot
│   │   ├── music/         # Sistema de música
│   │   ├── pubg/          # Integração PUBG
│   │   ├── tournaments/   # Sistema de torneios
│   │   ├── achievements/  # Sistema de conquistas
│   │   ├── notifications/ # Sistema de notificações
│   │   ├── moderation/    # Sistema de moderação
│   │   ├── minigames/     # Mini-jogos
│   │   └── checkin/       # Sistema de check-in
│   ├── integrations/      # Integrações externas
│   │   └── medal.py       # Integração Medal.tv
│   ├── utils/             # Utilitários compartilhados
│   │   ├── embed_templates.py
│   │   ├── emoji_system.py
│   │   ├── charts_system.py
│   │   ├── scheduler.py
│   │   └── keep_alive.py
│   └── web/               # Interface web
│       ├── app.py         # Aplicação Flask
│       ├── routes/        # Rotas web
│       ├── static/        # Arquivos estáticos
│       └── templates/     # Templates HTML
├── config/                # Arquivos de configuração
│   ├── deploy/           # Configurações de deploy
│   └── features/         # Configurações por feature
├── data/                 # Dados persistentes
├── database/             # Scripts SQL
├── scripts/              # Scripts utilitários
│   ├── deploy/          # Scripts de deploy
│   ├── setup/           # Scripts de configuração
│   └── maintenance/     # Scripts de manutenção
├── tests/               # Testes automatizados
│   ├── unit/           # Testes unitários
│   └── integration/    # Testes de integração
├── docs/               # Documentação
└── main.py            # Ponto de entrada
```

## Módulos Principais

### Core (`src/core/`)
Contém os sistemas fundamentais do bot:
- **bot.py**: Configuração principal e inicialização
- **config/**: Gerenciamento de configurações e variáveis de ambiente
- **database/**: Modelos de dados e conexões de banco
- **storage/**: Sistemas de armazenamento (JSON, PostgreSQL)

### Features (`src/features/`)
Funcionalidades específicas organizadas por domínio:
- **music/**: Sistema de música com player, canais e canais dinâmicos
- **pubg/**: API PUBG, sistema de ranks e roles
- **tournaments/**: Gerenciamento de torneios e temporadas
- **achievements/**: Sistema de conquistas e badges
- **notifications/**: Sistema de notificações
- **moderation/**: Comandos de moderação
- **minigames/**: Mini-jogos do servidor
- **checkin/**: Sistema completo de check-in

### Integrations (`src/integrations/`)
Integrações com serviços externos:
- **medal.py**: Integração com Medal.tv para clips

### Utils (`src/utils/`)
Utilitários compartilhados:
- **embed_templates.py**: Templates para embeds Discord
- **emoji_system.py**: Gerenciamento de emojis
- **charts_system.py**: Geração de gráficos
- **scheduler.py**: Agendamento de tarefas
- **keep_alive.py**: Manutenção da conexão

### Web (`src/web/`)
Interface web do bot:
- **app.py**: Aplicação Flask principal
- **routes/**: Definições de rotas
- **templates/**: Templates HTML
- **static/**: Arquivos CSS, JS, imagens

## Padrões de Desenvolvimento

### Imports
Todos os módulos seguem o padrão de imports relativos:
```python
from src.core import DataStorage, PostgresStorage
from src.features.pubg import api, ranks, roles
from src.utils import scheduler, embed_templates
```

### Configurações
Configurações são centralizadas em `src/core/config/` e organizadas por:
- **settings.py**: Configurações principais
- **env_loader.py**: Carregamento de variáveis de ambiente

### Testes
Testes são organizados espelhando a estrutura do código:
- `tests/unit/test_core/`: Testes dos módulos core
- `tests/unit/test_features/`: Testes das features
- `tests/integration/`: Testes de integração

## Benefícios da Nova Arquitetura

1. **Modularidade**: Cada funcionalidade é independente
2. **Escalabilidade**: Fácil adição de novas features
3. **Manutenibilidade**: Código organizado e fácil de encontrar
4. **Testabilidade**: Estrutura clara para testes
5. **Reutilização**: Utilitários compartilhados
6. **Separação de Responsabilidades**: Cada módulo tem uma função específica

## Próximos Passos

1. Migrar gradualmente funcionalidades para a nova estrutura
2. Implementar testes para todos os módulos
3. Criar documentação específica para cada feature
4. Estabelecer padrões de código e linting
5. Configurar CI/CD para a nova estrutura