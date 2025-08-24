# -*- coding: utf-8 -*-
"""
Hawk Bot Moderno - Sistema Principal
Bot Discord refatorado com arquitetura moderna e injeção de dependências
"""

import asyncio
import logging
import signal
import sys
import time
from typing import Optional, Dict, Any
from pathlib import Path

import discord
from discord.ext import commands

import sys
sys.path.append('.')
from src.core.config import get_config
from .dependency_container import DependencyContainer, ServiceLifetime
from .smart_cache import SmartCache, get_cache
from .structured_logger import StructuredLogger, LogCategory

# Importar sistemas existentes que serão integrados
try:
    from ..storage.data_storage import DataStorage
    from ..storage.postgresql_storage import PostgreSQLStorage
    from ..systems.rank_system import RankSystem
    from ..systems.dual_ranking_system import DualRankingSystem
    from ..systems.season_system import SeasonSystem
    from ..systems.music_system import MusicSystem
    from ..systems.achievement_system import AchievementSystem
    from ..systems.notifications_system import NotificationsSystem
    from ..systems.minigames_system import MinigamesSystem
    from ..systems.task_scheduler import TaskScheduler
    from ..integrations.pubg_integration import PUBGIntegration
    from ..web.dashboard import WebDashboard
except ImportError as e:
    logging.warning(f"Alguns módulos não puderam ser importados: {e}")

class ModernHawkBot(commands.Bot):
    """Bot Discord moderno com arquitetura refatorada"""
    
    def __init__(self):
        # Carregar configuração
        self.config = get_config()
        
        # Configurar intents do Discord
        intents = discord.Intents.default()
        intents.message_content = self.config.discord.enable_message_content
        intents.members = self.config.discord.enable_guild_members
        intents.voice_states = self.config.discord.enable_voice_states
        
        # Inicializar bot base
        super().__init__(
            command_prefix=self.config.discord.command_prefix,
            intents=intents,
            case_insensitive=self.config.discord.case_insensitive,
            help_command=None  # Usar comando de ajuda customizado
        )
        
        # Container de dependências
        self.container = DependencyContainer()
        
        # Estado do bot
        self._startup_time: Optional[float] = None
        self._ready = False
        self._shutdown_requested = False
        
        # Sistemas principais (serão injetados)
        self.storage: Optional[DataStorage] = None
        self.cache: Optional[SmartCache] = None
        self.logger: Optional[StructuredLogger] = None
        
        # Sistemas de funcionalidades
        self.rank_system: Optional[RankSystem] = None
        self.dual_ranking_system: Optional[DualRankingSystem] = None
        self.season_system: Optional[SeasonSystem] = None
        self.music_system: Optional[MusicSystem] = None
        self.achievement_system: Optional[AchievementSystem] = None
        self.notifications_system: Optional[NotificationsSystem] = None
        self.minigames_system: Optional[MinigamesSystem] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        
        # Integrações
        self.pubg_integration: Optional[PUBGIntegration] = None
        self.web_dashboard: Optional[WebDashboard] = None
        
        # Logger será inicializado após a resolução de dependências
        print("ModernHawkBot inicializado")
    
    async def setup_hook(self):
        """Configuração inicial do bot (chamado automaticamente)"""
        try:
            self._startup_time = time.time()
            
            # Registrar serviços no container
            await self._register_services()
            
            # Inicializar todos os serviços
            await self.container.initialize_all()
            
            # Resolver dependências principais
            await self._resolve_dependencies()
            
            # Carregar comandos (Cogs)
            await self._load_commands()
            
            # Configurar handlers de sinal
            self._setup_signal_handlers()
            
            startup_time = (time.time() - self._startup_time) * 1000
            if self.logger:
                self.logger.log_info(f"Setup do bot concluído em {startup_time:.2f}ms", LogCategory.SYSTEM)
            else:
                print(f"Setup do bot concluído em {startup_time:.2f}ms")
            
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Erro durante setup do bot: {e}", LogCategory.SYSTEM, exc_info=True)
            else:
                print(f"Erro durante setup do bot: {e}")
            raise
    
    async def _register_services(self):
        """Registra todos os serviços no container de dependências"""
        print("Registrando serviços...")
        
        # Serviços principais
        self.container.register(StructuredLogger, lifetime=ServiceLifetime.SINGLETON)
        self.container.register(SmartCache, lifetime=ServiceLifetime.SINGLETON)
        
        # Sistema de storage
        if self.config.database.storage_type.value == "postgresql":
            self.container.register(PostgreSQLStorage, DataStorage, lifetime=ServiceLifetime.SINGLETON)
        else:
            self.container.register(DataStorage, lifetime=ServiceLifetime.SINGLETON)
        
        # Sistemas de funcionalidades (apenas se habilitados)
        feature_flags = self.config.get_feature_flags()
        
        if feature_flags.get('ranking_system', True):
            self.container.register(RankSystem, lifetime=ServiceLifetime.SINGLETON)
            self.container.register(DualRankingSystem, lifetime=ServiceLifetime.SINGLETON)
        
        if feature_flags.get('seasons', True):
            self.container.register(SeasonSystem, lifetime=ServiceLifetime.SINGLETON)
        
        if feature_flags.get('music_system', True):
            self.container.register(MusicSystem, lifetime=ServiceLifetime.SINGLETON)
        
        if feature_flags.get('achievements', True):
            self.container.register(AchievementSystem, lifetime=ServiceLifetime.SINGLETON)
        
        self.container.register(NotificationsSystem, lifetime=ServiceLifetime.SINGLETON)
        self.container.register(MinigamesSystem, lifetime=ServiceLifetime.SINGLETON)
        self.container.register(TaskScheduler, lifetime=ServiceLifetime.SINGLETON)
        
        # Integrações
        if feature_flags.get('pubg_integration', True) and self.config.api.pubg_api_key:
            self.container.register(PUBGIntegration, lifetime=ServiceLifetime.SINGLETON)
        
        # Web Dashboard
        if self.config.performance.enable_metrics:
            self.container.register(WebDashboard, lifetime=ServiceLifetime.SINGLETON)
        
        print(f"Registrados {len(self.container._services)} serviços")
    
    async def _resolve_dependencies(self):
        """Resolve as dependências principais do bot"""
        print("Resolvendo dependências...")
        
        # Resolver serviços principais
        self.logger = await self.container.resolve(StructuredLogger)
        self.cache = await self.container.resolve(SmartCache)
        self.storage = await self.container.resolve(DataStorage)
        
        # Resolver sistemas opcionais
        feature_flags = self.config.get_feature_flags()
        
        try:
            if feature_flags.get('ranking_system', True):
                self.rank_system = await self.container.resolve(RankSystem)
                self.dual_ranking_system = await self.container.resolve(DualRankingSystem)
        except Exception as e:
            print(f"Sistema de ranking não disponível: {e}")
        
        try:
            if feature_flags.get('seasons', True):
                self.season_system = await self.container.resolve(SeasonSystem)
        except Exception as e:
            print(f"Sistema de temporadas não disponível: {e}")
        
        try:
            if feature_flags.get('music_system', True):
                self.music_system = await self.container.resolve(MusicSystem)
        except Exception as e:
            print(f"Sistema de música não disponível: {e}")
        
        try:
            if feature_flags.get('achievements', True):
                self.achievement_system = await self.container.resolve(AchievementSystem)
        except Exception as e:
            print(f"Sistema de conquistas não disponível: {e}")
        
        try:
            self.notifications_system = await self.container.resolve(NotificationsSystem)
            self.minigames_system = await self.container.resolve(MinigamesSystem)
            self.task_scheduler = await self.container.resolve(TaskScheduler)
        except Exception as e:
            print(f"Alguns sistemas auxiliares não disponíveis: {e}")
        
        try:
            if feature_flags.get('pubg_integration', True):
                self.pubg_integration = await self.container.resolve(PUBGIntegration)
        except Exception as e:
            print(f"Integração PUBG não disponível: {e}")
        
        try:
            if self.config.performance.enable_metrics:
                self.web_dashboard = await self.container.resolve(WebDashboard)
        except Exception as e:
            print(f"Web Dashboard não disponível: {e}")
        
        print("Dependências resolvidas com sucesso")
    
    async def _load_commands(self):
        """Carrega todos os comandos (Cogs)"""
        print("Carregando comandos...")
        
        cogs_to_load = [
            'src.commands.pubg_commands',
            'src.commands.music_commands', 
            'src.commands.season_commands',
            'src.commands.admin_commands'
        ]
        
        loaded_cogs = 0
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                loaded_cogs += 1
                print(f"Cog carregado: {cog}")
            except Exception as e:
                print(f"Erro ao carregar cog {cog}: {e}")
        
        print(f"Carregados {loaded_cogs}/{len(cogs_to_load)} cogs")
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        if sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            
            def signal_handler(signum, frame):
                print(f"Sinal recebido: {signum}")
                self._shutdown_requested = True
                asyncio.create_task(self.close())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
    
    async def on_ready(self):
        """Evento chamado quando o bot está pronto"""
        if self._ready:
            return  # Evitar múltiplas execuções
        
        self._ready = True
        startup_time = (time.time() - self._startup_time) * 1000 if self._startup_time else 0
        
        if self.logger:
            self.logger.log_info(f"Bot conectado como {self.user} (ID: {self.user.id})", LogCategory.DISCORD)
            self.logger.log_info(f"Conectado a {len(self.guilds)} servidores", LogCategory.DISCORD)
            self.logger.log_info(f"Tempo total de inicialização: {startup_time:.2f}ms", LogCategory.SYSTEM)
        else:
            print(f"Bot conectado como {self.user} (ID: {self.user.id})")
            print(f"Conectado a {len(self.guilds)} servidores")
            print(f"Tempo total de inicialização: {startup_time:.2f}ms")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            if self.logger:
                self.logger.log_info(f"Sincronizados {len(synced)} comandos slash", LogCategory.DISCORD)
            else:
                print(f"Sincronizados {len(synced)} comandos slash")
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Erro ao sincronizar comandos slash: {e}", LogCategory.DISCORD, exc_info=True)
            else:
                print(f"Erro ao sincronizar comandos slash: {e}")
        
        # Iniciar tarefas automáticas
        if self.task_scheduler:
            await self.task_scheduler.start_all_tasks()
        
        # Definir status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servidores | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_guild_join(self, guild: discord.Guild):
        """Evento chamado quando o bot entra em um servidor"""
        if self.logger:
            self.logger.log_info(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})", LogCategory.DISCORD,
                    guild_id=str(guild.id), member_count=guild.member_count)
        else:
            print(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
        
        # Atualizar status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servidores | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Evento chamado quando o bot sai de um servidor"""
        if self.logger:
            self.logger.log_info(f"Bot removido do servidor: {guild.name} (ID: {guild.id})", LogCategory.DISCORD,
                    guild_id=str(guild.id))
        else:
            print(f"Bot removido do servidor: {guild.name} (ID: {guild.id})")
        
        # Atualizar status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servidores | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_error(self, event: str, *args, **kwargs):
        """Handler global de erros"""
        if self.logger:
            self.logger.log_error(f"Erro no evento {event}", LogCategory.ERROR, 
                     exc_info=True, event=event, args=args, kwargs=kwargs)
        else:
            print(f"Erro no evento {event}")
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handler de erros de comandos"""
        if self.logger:
            self.logger.log_error(f"Erro no comando {ctx.command}: {error}", LogCategory.ERROR,
                     exc_info=True, command=str(ctx.command), user_id=str(ctx.author.id),
                     guild_id=str(ctx.guild.id) if ctx.guild else None)
        else:
            print(f"Erro no comando {ctx.command}: {error}")
    
    async def close(self):
        """Fecha o bot e limpa recursos"""
        if self._shutdown_requested:
            return  # Evitar múltiplas execuções
        
        self._shutdown_requested = True
        if self.logger:
            self.logger.log_info("Iniciando shutdown do bot...", LogCategory.SYSTEM)
        else:
            print("Iniciando shutdown do bot...")
        
        try:
            # Parar tarefas automáticas
            if self.task_scheduler:
                await self.task_scheduler.stop_all_tasks()
            
            # Limpar recursos dos serviços
            await self.container.cleanup()
            
            # Fechar conexão do Discord
            await super().close()
            
            if self.logger:
                self.logger.log_info("Shutdown concluído com sucesso", LogCategory.SYSTEM)
            else:
                print("Shutdown concluído com sucesso")
            
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Erro durante shutdown: {e}", LogCategory.SYSTEM, exc_info=True)
            else:
                print(f"Erro durante shutdown: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Obtém status de saúde do bot"""
        health = {
            'bot_status': 'healthy' if self._ready else 'starting',
            'uptime_seconds': time.time() - self._startup_time if self._startup_time else 0,
            'guilds_count': len(self.guilds),
            'users_count': len(self.users),
            'latency_ms': round(self.latency * 1000, 2),
            'memory_usage': {},
            'services': {}
        }
        
        # Status dos serviços
        try:
            container_health = await self.container.check_health()
            health['services'] = container_health
        except Exception as e:
            health['services'] = {'error': str(e)}
        
        # Estatísticas do cache
        if self.cache:
            health['cache'] = self.cache.get_stats()
        
        return health
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas detalhadas do bot"""
        metrics = {
            'timestamp': time.time(),
            'bot': {
                'uptime_seconds': time.time() - self._startup_time if self._startup_time else 0,
                'guilds': len(self.guilds),
                'users': len(self.users),
                'latency_ms': round(self.latency * 1000, 2),
                'ready': self._ready
            },
            'services': {},
            'cache': {},
            'performance': {}
        }
        
        # Métricas dos serviços
        try:
            metrics['services'] = self.container.get_service_stats()
        except Exception as e:
            metrics['services'] = {'error': str(e)}
        
        # Métricas do cache
        if self.cache:
            metrics['cache'] = self.cache.get_stats()
        
        return metrics

# Função principal para executar o bot
async def run_bot():
    """Executa o bot moderno"""
    bot = None
    try:
        print("Iniciando Hawk Bot Moderno...")
        
        # Criar e executar bot
        bot = ModernHawkBot()
        
        # Obter token da configuração
        token = get_config().discord.bot_token.get_secret_value()
        
        # Executar bot
        await bot.start(token)
        
    except KeyboardInterrupt:
        print("Interrupção do usuário detectada")
    except Exception as e:
        print(f"Erro fatal: {e}")
        raise
    finally:
        if bot:
            await bot.close()
        
        # Logger será limpo automaticamente pelo container

def main():
    """Ponto de entrada principal"""
    try:
        # Configurar loop de eventos para Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Executar bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        print("\nBot interrompido pelo usuário")
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()