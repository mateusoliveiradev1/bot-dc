# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.0.0] - 2024-01-XX - Refatoração Completa

### 🏗️ Arquitetura
- **BREAKING CHANGE**: Refatoração completa da estrutura do projeto
- Nova arquitetura modular e escalável
- Separação clara entre core, features, integrations e utils
- Estrutura de pastas reorganizada para melhor manutenibilidade

### ✨ Adicionado
- Documentação completa da arquitetura (`docs/ARCHITECTURE.md`)
- Guia de desenvolvimento (`docs/DEVELOPMENT_GUIDE.md`)
- Estrutura de testes organizada (`tests/`)
- Scripts de setup e manutenção organizados (`scripts/`)
- Configurações centralizadas (`config/`)
- Dados JSON organizados (`data/`)

### 🔄 Modificado
- **BREAKING CHANGE**: Todos os imports foram atualizados para a nova estrutura
- Módulos reorganizados em:
  - `src/core/`: Bot principal, configurações, storage
  - `src/features/`: Funcionalidades específicas (music, pubg, tournaments, etc.)
  - `src/integrations/`: Integrações externas (medal, etc.)
  - `src/utils/`: Utilitários compartilhados
  - `src/web/`: Interface web
- README.md atualizado com nova estrutura
- Scripts de deploy movidos para `scripts/deploy/`
- Scripts de setup movidos para `scripts/setup/`

### 📁 Estrutura de Arquivos Movidos

#### Core Systems
- `bot.py` → `src/core/bot.py`
- `config.py` → `src/core/config.py`
- `data_storage.py` → `src/core/storage.py`
- `database.py` → `src/core/database.py`

#### Features
- `music_system.py` → `src/features/music/player.py`
- `channels_system.py` → `src/features/music/channels.py`
- `dynamic_channels.py` → `src/features/music/dynamic_channels.py`
- `pubg_system.py` → `src/features/pubg/api.py`
- `dual_ranking_system.py` → `src/features/pubg/dual_ranking.py`
- `tournament_system.py` → `src/features/tournaments/manager.py`
- `season_system.py` → `src/features/tournaments/seasons.py`
- `checkin_system.py` → `src/features/checkin/system.py`
- `notification_system.py` → `src/features/notifications/system.py`
- `minigames_system.py` → `src/features/minigames/system.py`
- `badge_system.py` → `src/features/badges/system.py`

#### Integrations
- `medal_integration.py` → `src/integrations/medal.py`

#### Utils
- `embed_templates.py` → `src/utils/embed_templates.py`
- `emoji_system.py` → `src/utils/emoji_system.py`
- `charts_system.py` → `src/utils/charts_system.py`
- `scheduler.py` → `src/utils/scheduler.py`
- `keep_alive.py` → `src/utils/keep_alive.py`

#### Web
- `web_interface.py` → `src/web/app.py`
- `routes.py` → `src/web/routes/main.py`

#### Configuration
- `*_config.json` → `config/features/*.json`

#### Data
- `*_data.json` → `data/*.json`

#### Tests
- `test_*.py` → `tests/unit/` ou `tests/integration/`

#### Scripts
- `config_rapida.py` → `scripts/setup/config_rapida.py`
- `generate_env_vars.py` → `scripts/setup/generate_env_vars.py`
- `supabase_auto_setup.py` → `scripts/setup/supabase_auto_setup.py`
- `corrigir_database_url.py` → `scripts/maintenance/corrigir_database_url.py`

#### Database
- `supabase_setup.sql` → `database/supabase_setup.sql`

### 🔧 Melhorias
- Melhor organização do código
- Imports mais limpos e consistentes
- Estrutura preparada para crescimento
- Facilita testes e manutenção
- Documentação abrangente

### ⚠️ Breaking Changes

Esta versão introduz mudanças significativas na estrutura do projeto. Se você tem um fork ou contribuições pendentes:

1. **Imports**: Todos os imports precisam ser atualizados
2. **Estrutura**: Arquivos foram movidos para nova organização
3. **Configurações**: Caminhos de configuração podem ter mudado

### 🚀 Migração

Para migrar de versões anteriores:

1. Faça backup de suas configurações personalizadas
2. Clone a nova versão
3. Reconfigure usando `scripts/setup/config_rapida.py`
4. Atualize qualquer código personalizado para usar os novos imports

---

## [1.x.x] - Versões Anteriores

Versões anteriores à refatoração completa. Consulte o histórico do Git para detalhes específicos.