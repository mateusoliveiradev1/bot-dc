"""Sistema de plugins dinâmicos para o Hawk Bot.

Este módulo fornece:
- Carregamento dinâmico de plugins
- Sistema de dependências entre plugins
- Hot reload de plugins
- Sandboxing e isolamento
- API para plugins
- Gerenciamento de lifecycle
- Sistema de permissões
- Marketplace de plugins
"""

import os
import sys
import importlib
import importlib.util
import inspect
import logging
import asyncio
import json
import hashlib
import zipfile
import tempfile
from typing import Any, Dict, List, Optional, Callable, Type, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
import weakref
import traceback
from concurrent.futures import ThreadPoolExecutor

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None
    commands = None

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

class PluginState(Enum):
    """Estados de um plugin"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"

class PluginType(Enum):
    """Tipos de plugins"""
    COMMAND = "command"        # Plugin de comandos
    EVENT = "event"            # Plugin de eventos
    SERVICE = "service"        # Plugin de serviço
    UTILITY = "utility"        # Plugin utilitário
    INTEGRATION = "integration" # Plugin de integração
    GAME = "game"              # Plugin de jogos
    MUSIC = "music"            # Plugin de música
    MODERATION = "moderation"  # Plugin de moderação
    FUN = "fun"                # Plugin de diversão
    CUSTOM = "custom"          # Plugin customizado

class PluginPermission(Enum):
    """Permissões de plugins"""
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    NETWORK_ACCESS = "network_access"
    DATABASE_ACCESS = "database_access"
    SYSTEM_COMMANDS = "system_commands"
    USER_DATA = "user_data"
    GUILD_MANAGEMENT = "guild_management"
    MESSAGE_MANAGEMENT = "message_management"
    ROLE_MANAGEMENT = "role_management"
    CHANNEL_MANAGEMENT = "channel_management"
    WEBHOOK_MANAGEMENT = "webhook_management"
    EXTERNAL_API = "external_api"
    DANGEROUS_OPERATIONS = "dangerous_operations"

@dataclass
class PluginMetadata:
    """Metadados de um plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType = PluginType.CUSTOM
    dependencies: List[str] = field(default_factory=list)
    permissions: List[PluginPermission] = field(default_factory=list)
    min_bot_version: Optional[str] = None
    max_bot_version: Optional[str] = None
    discord_py_version: Optional[str] = None
    python_version: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    api_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'plugin_type': self.plugin_type.value,
            'dependencies': self.dependencies,
            'permissions': [p.value for p in self.permissions],
            'min_bot_version': self.min_bot_version,
            'max_bot_version': self.max_bot_version,
            'discord_py_version': self.discord_py_version,
            'python_version': self.python_version,
            'homepage': self.homepage,
            'repository': self.repository,
            'license': self.license,
            'tags': self.tags,
            'config_schema': self.config_schema,
            'api_version': self.api_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Cria a partir de dicionário"""
        return cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            author=data['author'],
            plugin_type=PluginType(data.get('plugin_type', 'custom')),
            dependencies=data.get('dependencies', []),
            permissions=[PluginPermission(p) for p in data.get('permissions', [])],
            min_bot_version=data.get('min_bot_version'),
            max_bot_version=data.get('max_bot_version'),
            discord_py_version=data.get('discord_py_version'),
            python_version=data.get('python_version'),
            homepage=data.get('homepage'),
            repository=data.get('repository'),
            license=data.get('license'),
            tags=data.get('tags', []),
            config_schema=data.get('config_schema'),
            api_version=data.get('api_version', '1.0')
        )

class PluginAPI:
    """API disponível para plugins"""
    
    def __init__(self, plugin_manager, plugin_name: str):
        self.plugin_manager = plugin_manager
        self.plugin_name = plugin_name
        self.logger = logging.getLogger(f'plugin.{plugin_name}')
    
    # Logging
    def log_info(self, message: str):
        """Log de informação"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log de aviso"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log de erro"""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log de debug"""
        self.logger.debug(message)
    
    # Eventos
    async def emit_event(self, event_name: str, data: Optional[Dict[str, Any]] = None):
        """Emite um evento"""
        try:
            from .event_system import emit
            await emit(event_name, data, f'plugin.{self.plugin_name}')
        except ImportError:
            self.log_warning("Sistema de eventos não disponível")
    
    def add_event_listener(self, event_name: str, callback: Callable):
        """Adiciona listener de evento"""
        try:
            from .event_system import add_listener
            return add_listener(event_name, callback, name=f'{self.plugin_name}_{callback.__name__}')
        except ImportError:
            self.log_warning("Sistema de eventos não disponível")
            return None
    
    # Cache
    def cache_get(self, key: str, default: Any = None) -> Any:
        """Obtém valor do cache"""
        try:
            from .smart_cache_enhanced import get_cache
            cache = get_cache()
            return cache.get(f'plugin.{self.plugin_name}.{key}', default)
        except ImportError:
            return default
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Define valor no cache"""
        try:
            from .smart_cache_enhanced import get_cache
            cache = get_cache()
            cache.set(f'plugin.{self.plugin_name}.{key}', value, ttl)
        except ImportError:
            pass
    
    # Configuração
    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtém configuração do plugin"""
        return self.plugin_manager.get_plugin_config(self.plugin_name, key, default)
    
    def set_config(self, key: str, value: Any):
        """Define configuração do plugin"""
        self.plugin_manager.set_plugin_config(self.plugin_name, key, value)
    
    # Dados persistentes
    def get_data(self, key: str, default: Any = None) -> Any:
        """Obtém dados persistentes"""
        return self.plugin_manager.get_plugin_data(self.plugin_name, key, default)
    
    def set_data(self, key: str, value: Any):
        """Define dados persistentes"""
        self.plugin_manager.set_plugin_data(self.plugin_name, key, value)
    
    # Outros plugins
    def get_plugin(self, plugin_name: str) -> Optional['Plugin']:
        """Obtém referência a outro plugin"""
        return self.plugin_manager.get_plugin(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Verifica se plugin está carregado"""
        return self.plugin_manager.is_plugin_loaded(plugin_name)
    
    # Bot
    def get_bot(self):
        """Obtém referência ao bot"""
        return self.plugin_manager.bot
    
    # Métricas
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Registra métrica"""
        try:
            from .metrics import get_metrics_collector
            metrics = get_metrics_collector()
            full_name = f'plugin.{self.plugin_name}.{metric_name}'
            metrics.record_gauge(full_name, value, tags)
        except ImportError:
            pass
    
    def increment_counter(self, counter_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Incrementa contador"""
        try:
            from .metrics import get_metrics_collector
            metrics = get_metrics_collector()
            full_name = f'plugin.{self.plugin_name}.{counter_name}'
            metrics.increment_counter(full_name, value, tags)
        except ImportError:
            pass

class Plugin(ABC):
    """Classe base para plugins"""
    
    def __init__(self, api: PluginAPI):
        self.api = api
        self.metadata: Optional[PluginMetadata] = None
        self.state = PluginState.UNLOADED
        self.config: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def setup(self) -> bool:
        """Configuração inicial do plugin"""
        pass
    
    @abstractmethod
    async def teardown(self) -> bool:
        """Limpeza do plugin"""
        pass
    
    async def on_load(self):
        """Chamado quando o plugin é carregado"""
        pass
    
    async def on_unload(self):
        """Chamado quando o plugin é descarregado"""
        pass
    
    async def on_enable(self):
        """Chamado quando o plugin é habilitado"""
        pass
    
    async def on_disable(self):
        """Chamado quando o plugin é desabilitado"""
        pass
    
    async def on_config_change(self, key: str, old_value: Any, new_value: Any):
        """Chamado quando configuração muda"""
        pass
    
    def get_commands(self) -> List[commands.Command]:
        """Retorna comandos do plugin"""
        return []
    
    def get_cogs(self) -> List[commands.Cog]:
        """Retorna cogs do plugin"""
        return []
    
    def get_event_listeners(self) -> Dict[str, Callable]:
        """Retorna event listeners do plugin"""
        return {}
    
    def validate_permissions(self, required_permissions: List[PluginPermission]) -> bool:
        """Valida se o plugin tem as permissões necessárias"""
        if not self.metadata:
            return False
        
        plugin_permissions = set(self.metadata.permissions)
        required_permissions_set = set(required_permissions)
        
        return required_permissions_set.issubset(plugin_permissions)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtém status do plugin"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'state': self.state.value,
            'uptime': uptime,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'config_keys': list(self.config.keys()),
            'data_keys': list(self.data.keys())
        }

@dataclass
class PluginInfo:
    """Informações de um plugin carregado"""
    metadata: PluginMetadata
    plugin: Plugin
    module: Any
    file_path: str
    state: PluginState = PluginState.UNLOADED
    load_time: Optional[datetime] = None
    last_reload: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    dependencies_resolved: bool = False
    dependents: Set[str] = field(default_factory=set)
    file_hash: Optional[str] = None
    
    def update_hash(self):
        """Atualiza hash do arquivo"""
        try:
            with open(self.file_path, 'rb') as f:
                self.file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            self.file_hash = None
    
    def has_changed(self) -> bool:
        """Verifica se o arquivo mudou"""
        if not self.file_hash:
            return False
        
        try:
            with open(self.file_path, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()
                return current_hash != self.file_hash
        except Exception:
            return False

class PluginManager:
    """Gerenciador de plugins"""
    
    def __init__(self, bot=None, plugins_dir: str = "plugins"):
        self.bot = bot
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_data: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Criar diretório de plugins se não existir
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Diretórios especiais
        self.config_dir = self.plugins_dir / "configs"
        self.data_dir = self.plugins_dir / "data"
        self.temp_dir = self.plugins_dir / "temp"
        
        for dir_path in [self.config_dir, self.data_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Carregar configurações e dados
        self._load_plugin_configs()
        self._load_plugin_data()
        
        # Sistema de hot reload
        self.hot_reload_enabled = True
        self.file_watchers: Dict[str, float] = {}  # plugin_name -> last_modified
        
        # Marketplace
        self.marketplace_url = "https://hawkbot-plugins.example.com/api"
        self.installed_plugins_file = self.plugins_dir / "installed.json"
    
    def _load_plugin_configs(self):
        """Carrega configurações dos plugins"""
        for config_file in self.config_dir.glob("*.json"):
            plugin_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.plugin_configs[plugin_name] = json.load(f)
            except Exception as e:
                self.logger.error(f"Erro ao carregar config do plugin {plugin_name}: {e}")
    
    def _save_plugin_config(self, plugin_name: str):
        """Salva configuração de um plugin"""
        if plugin_name not in self.plugin_configs:
            return
        
        config_file = self.config_dir / f"{plugin_name}.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs[plugin_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar config do plugin {plugin_name}: {e}")
    
    def _load_plugin_data(self):
        """Carrega dados dos plugins"""
        for data_file in self.data_dir.glob("*.json"):
            plugin_name = data_file.stem
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.plugin_data[plugin_name] = json.load(f)
            except Exception as e:
                self.logger.error(f"Erro ao carregar dados do plugin {plugin_name}: {e}")
    
    def _save_plugin_data(self, plugin_name: str):
        """Salva dados de um plugin"""
        if plugin_name not in self.plugin_data:
            return
        
        data_file = self.data_dir / f"{plugin_name}.json"
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_data[plugin_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados do plugin {plugin_name}: {e}")
    
    def get_plugin_config(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """Obtém configuração de plugin"""
        return self.plugin_configs.get(plugin_name, {}).get(key, default)
    
    def set_plugin_config(self, plugin_name: str, key: str, value: Any):
        """Define configuração de plugin"""
        if plugin_name not in self.plugin_configs:
            self.plugin_configs[plugin_name] = {}
        
        old_value = self.plugin_configs[plugin_name].get(key)
        self.plugin_configs[plugin_name][key] = value
        self._save_plugin_config(plugin_name)
        
        # Notificar plugin sobre mudança
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name].plugin
            asyncio.create_task(plugin.on_config_change(key, old_value, value))
    
    def get_plugin_data(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """Obtém dados de plugin"""
        return self.plugin_data.get(plugin_name, {}).get(key, default)
    
    def set_plugin_data(self, plugin_name: str, key: str, value: Any):
        """Define dados de plugin"""
        if plugin_name not in self.plugin_data:
            self.plugin_data[plugin_name] = {}
        
        self.plugin_data[plugin_name][key] = value
        self._save_plugin_data(plugin_name)
    
    def discover_plugins(self) -> List[str]:
        """Descobre plugins disponíveis"""
        plugins = []
        
        # Buscar arquivos .py
        for plugin_file in self.plugins_dir.glob("*.py"):
            if not plugin_file.name.startswith('_'):
                plugins.append(plugin_file.stem)
        
        # Buscar diretórios com __init__.py
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                init_file = plugin_dir / "__init__.py"
                if init_file.exists():
                    plugins.append(plugin_dir.name)
        
        return plugins
    
    def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Carrega metadados de um plugin"""
        try:
            # Tentar carregar de plugin.json
            metadata_file = plugin_path.parent / f"{plugin_path.stem}.json"
            if plugin_path.is_dir():
                metadata_file = plugin_path / "plugin.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                    return PluginMetadata.from_dict(metadata_dict)
            
            # Tentar extrair do código
            if plugin_path.is_file():
                spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path)
            else:
                spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path / "__init__.py")
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Buscar metadados no módulo
                if hasattr(module, 'PLUGIN_METADATA'):
                    metadata_dict = module.PLUGIN_METADATA
                    return PluginMetadata.from_dict(metadata_dict)
                
                # Criar metadados básicos
                return PluginMetadata(
                    name=plugin_path.stem,
                    version="1.0.0",
                    description=getattr(module, '__doc__', 'Plugin sem descrição'),
                    author="Desconhecido"
                )
        
        except Exception as e:
            self.logger.error(f"Erro ao carregar metadados do plugin {plugin_path}: {e}")
            return None
    
    def _resolve_dependencies(self, plugin_name: str) -> bool:
        """Resolve dependências de um plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_name]
        dependencies = plugin_info.metadata.dependencies
        
        for dep in dependencies:
            if dep not in self.plugins:
                self.logger.error(f"Dependência '{dep}' não encontrada para plugin '{plugin_name}'")
                return False
            
            dep_info = self.plugins[dep]
            if dep_info.state not in [PluginState.LOADED, PluginState.RUNNING]:
                # Tentar carregar dependência
                if not await self.load_plugin(dep):
                    self.logger.error(f"Falha ao carregar dependência '{dep}' para plugin '{plugin_name}'")
                    return False
            
            # Adicionar como dependente
            dep_info.dependents.add(plugin_name)
        
        plugin_info.dependencies_resolved = True
        return True
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """Carrega um plugin"""
        try:
            # Verificar se já está carregado
            if plugin_name in self.plugins and self.plugins[plugin_name].state != PluginState.UNLOADED:
                self.logger.warning(f"Plugin '{plugin_name}' já está carregado")
                return True
            
            # Encontrar arquivo do plugin
            plugin_file = self.plugins_dir / f"{plugin_name}.py"
            plugin_dir = self.plugins_dir / plugin_name
            
            plugin_path = None
            if plugin_file.exists():
                plugin_path = plugin_file
            elif plugin_dir.exists() and (plugin_dir / "__init__.py").exists():
                plugin_path = plugin_dir
            else:
                self.logger.error(f"Plugin '{plugin_name}' não encontrado")
                return False
            
            # Carregar metadados
            metadata = self._load_plugin_metadata(plugin_path)
            if not metadata:
                self.logger.error(f"Falha ao carregar metadados do plugin '{plugin_name}'")
                return False
            
            # Carregar módulo
            if plugin_path.is_file():
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            else:
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path / "__init__.py")
            
            if not spec or not spec.loader:
                self.logger.error(f"Falha ao criar spec para plugin '{plugin_name}'")
                return False
            
            module = importlib.util.module_from_spec(spec)
            
            # Adicionar ao sys.modules temporariamente
            sys.modules[f"plugins.{plugin_name}"] = module
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                del sys.modules[f"plugins.{plugin_name}"]
                self.logger.error(f"Erro ao executar módulo do plugin '{plugin_name}': {e}")
                return False
            
            # Encontrar classe do plugin
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                del sys.modules[f"plugins.{plugin_name}"]
                self.logger.error(f"Classe Plugin não encontrada no plugin '{plugin_name}'")
                return False
            
            # Criar API e instância do plugin
            api = PluginAPI(self, plugin_name)
            plugin_instance = plugin_class(api)
            plugin_instance.metadata = metadata
            
            # Criar info do plugin
            plugin_info = PluginInfo(
                metadata=metadata,
                plugin=plugin_instance,
                module=module,
                file_path=str(plugin_path),
                state=PluginState.LOADING,
                load_time=datetime.now()
            )
            plugin_info.update_hash()
            
            self.plugins[plugin_name] = plugin_info
            
            # Resolver dependências
            if not self._resolve_dependencies(plugin_name):
                await self.unload_plugin(plugin_name)
                return False
            
            # Configurar plugin
            if not await plugin_instance.setup():
                await self.unload_plugin(plugin_name)
                return False
            
            # Carregar configuração e dados
            plugin_instance.config = self.plugin_configs.get(plugin_name, {})
            plugin_instance.data = self.plugin_data.get(plugin_name, {})
            
            # Chamar on_load
            await plugin_instance.on_load()
            
            # Registrar comandos e eventos se Discord estiver disponível
            if DISCORD_AVAILABLE and self.bot:
                # Registrar comandos
                for command in plugin_instance.get_commands():
                    self.bot.add_command(command)
                
                # Registrar cogs
                for cog in plugin_instance.get_cogs():
                    await self.bot.add_cog(cog)
                
                # Registrar event listeners
                for event_name, callback in plugin_instance.get_event_listeners().items():
                    self.bot.add_listener(callback, event_name)
            
            plugin_info.state = PluginState.LOADED
            plugin_instance.state = PluginState.LOADED
            plugin_instance.start_time = datetime.now()
            
            self.logger.info(f"Plugin '{plugin_name}' carregado com sucesso")
            
            # Emitir evento
            try:
                from .event_system import emit
                await emit('plugin_loaded', {
                    'plugin_name': plugin_name,
                    'metadata': metadata.to_dict()
                }, 'plugin_manager')
            except ImportError:
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar plugin '{plugin_name}': {e}")
            self.logger.error(traceback.format_exc())
            
            # Limpar em caso de erro
            if plugin_name in self.plugins:
                self.plugins[plugin_name].state = PluginState.ERROR
                self.plugins[plugin_name].last_error = str(e)
                self.plugins[plugin_name].error_count += 1
            
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Descarrega um plugin"""
        try:
            if plugin_name not in self.plugins:
                self.logger.warning(f"Plugin '{plugin_name}' não está carregado")
                return True
            
            plugin_info = self.plugins[plugin_name]
            plugin_instance = plugin_info.plugin
            
            # Verificar dependentes
            if plugin_info.dependents:
                self.logger.error(f"Não é possível descarregar plugin '{plugin_name}' - tem dependentes: {plugin_info.dependents}")
                return False
            
            plugin_info.state = PluginState.STOPPING
            plugin_instance.state = PluginState.STOPPING
            
            # Chamar on_unload
            await plugin_instance.on_unload()
            
            # Desregistrar do Discord se disponível
            if DISCORD_AVAILABLE and self.bot:
                # Remover comandos
                for command in plugin_instance.get_commands():
                    self.bot.remove_command(command.name)
                
                # Remover cogs
                for cog in plugin_instance.get_cogs():
                    await self.bot.remove_cog(cog.qualified_name)
                
                # Remover event listeners (mais complexo, precisaria de tracking)
            
            # Chamar teardown
            await plugin_instance.teardown()
            
            # Remover das dependências de outros plugins
            for dep_name in plugin_info.metadata.dependencies:
                if dep_name in self.plugins:
                    self.plugins[dep_name].dependents.discard(plugin_name)
            
            # Remover do sys.modules
            module_name = f"plugins.{plugin_name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Salvar dados e configurações
            self.plugin_configs[plugin_name] = plugin_instance.config
            self.plugin_data[plugin_name] = plugin_instance.data
            self._save_plugin_config(plugin_name)
            self._save_plugin_data(plugin_name)
            
            # Remover da lista
            del self.plugins[plugin_name]
            
            self.logger.info(f"Plugin '{plugin_name}' descarregado com sucesso")
            
            # Emitir evento
            try:
                from .event_system import emit
                await emit('plugin_unloaded', {
                    'plugin_name': plugin_name
                }, 'plugin_manager')
            except ImportError:
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao descarregar plugin '{plugin_name}': {e}")
            if plugin_name in self.plugins:
                self.plugins[plugin_name].state = PluginState.ERROR
                self.plugins[plugin_name].last_error = str(e)
                self.plugins[plugin_name].error_count += 1
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Recarrega um plugin"""
        if plugin_name in self.plugins:
            if not await self.unload_plugin(plugin_name):
                return False
        
        success = await self.load_plugin(plugin_name)
        
        if success and plugin_name in self.plugins:
            self.plugins[plugin_name].last_reload = datetime.now()
        
        return success
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Habilita um plugin"""
        if plugin_name not in self.plugins:
            return await self.load_plugin(plugin_name)
        
        plugin_info = self.plugins[plugin_name]
        if plugin_info.state == PluginState.DISABLED:
            await plugin_info.plugin.on_enable()
            plugin_info.state = PluginState.RUNNING
            plugin_info.plugin.state = PluginState.RUNNING
            return True
        
        return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Desabilita um plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_name]
        if plugin_info.state in [PluginState.LOADED, PluginState.RUNNING]:
            await plugin_info.plugin.on_disable()
            plugin_info.state = PluginState.DISABLED
            plugin_info.plugin.state = PluginState.DISABLED
            return True
        
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Obtém instância de um plugin"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].plugin
        return None
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Verifica se plugin está carregado"""
        return (plugin_name in self.plugins and 
                self.plugins[plugin_name].state in [PluginState.LOADED, PluginState.RUNNING])
    
    def get_loaded_plugins(self) -> List[str]:
        """Obtém lista de plugins carregados"""
        return [name for name, info in self.plugins.items() 
                if info.state in [PluginState.LOADED, PluginState.RUNNING]]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Obtém informações de um plugin"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtém informações de todos os plugins"""
        result = {}
        
        for name, info in self.plugins.items():
            result[name] = {
                'metadata': info.metadata.to_dict(),
                'state': info.state.value,
                'load_time': info.load_time.isoformat() if info.load_time else None,
                'last_reload': info.last_reload.isoformat() if info.last_reload else None,
                'error_count': info.error_count,
                'last_error': info.last_error,
                'dependencies_resolved': info.dependencies_resolved,
                'dependents': list(info.dependents),
                'file_path': info.file_path,
                'plugin_status': info.plugin.get_status()
            }
        
        return result
    
    async def check_for_updates(self):
        """Verifica atualizações de plugins (hot reload)"""
        if not self.hot_reload_enabled:
            return
        
        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.has_changed():
                self.logger.info(f"Arquivo do plugin '{plugin_name}' foi modificado, recarregando...")
                await self.reload_plugin(plugin_name)
    
    async def install_plugin_from_file(self, file_path: str) -> bool:
        """Instala plugin de um arquivo"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix == '.zip':
                # Extrair ZIP
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    extract_path = self.temp_dir / file_path.stem
                    zip_file.extractall(extract_path)
                    
                    # Procurar plugin.json ou __init__.py
                    plugin_json = extract_path / 'plugin.json'
                    init_py = extract_path / '__init__.py'
                    
                    if plugin_json.exists():
                        # Carregar metadados
                        with open(plugin_json, 'r', encoding='utf-8') as f:
                            metadata_dict = json.load(f)
                            metadata = PluginMetadata.from_dict(metadata_dict)
                        
                        # Mover para diretório de plugins
                        target_dir = self.plugins_dir / metadata.name
                        if target_dir.exists():
                            import shutil
                            shutil.rmtree(target_dir)
                        
                        import shutil
                        shutil.move(str(extract_path), str(target_dir))
                        
                        self.logger.info(f"Plugin '{metadata.name}' instalado com sucesso")
                        return True
            
            elif file_path.suffix == '.py':
                # Copiar arquivo Python
                import shutil
                target_file = self.plugins_dir / file_path.name
                shutil.copy2(file_path, target_file)
                
                self.logger.info(f"Plugin '{file_path.stem}' instalado com sucesso")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao instalar plugin: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """Desinstala um plugin"""
        try:
            # Descarregar primeiro
            if plugin_name in self.plugins:
                if not await self.unload_plugin(plugin_name):
                    return False
            
            # Remover arquivos
            plugin_file = self.plugins_dir / f"{plugin_name}.py"
            plugin_dir = self.plugins_dir / plugin_name
            
            import shutil
            
            if plugin_file.exists():
                plugin_file.unlink()
            
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            
            # Remover configurações e dados
            config_file = self.config_dir / f"{plugin_name}.json"
            data_file = self.data_dir / f"{plugin_name}.json"
            
            if config_file.exists():
                config_file.unlink()
            
            if data_file.exists():
                data_file.unlink()
            
            # Remover da memória
            self.plugin_configs.pop(plugin_name, None)
            self.plugin_data.pop(plugin_name, None)
            
            self.logger.info(f"Plugin '{plugin_name}' desinstalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao desinstalar plugin '{plugin_name}': {e}")
            return False
    
    async def load_all_plugins(self):
        """Carrega todos os plugins disponíveis"""
        plugins = self.discover_plugins()
        
        for plugin_name in plugins:
            try:
                await self.load_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"Erro ao carregar plugin '{plugin_name}': {e}")
    
    async def shutdown(self):
        """Descarrega todos os plugins"""
        plugin_names = list(self.plugins.keys())
        
        for plugin_name in plugin_names:
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"Erro ao descarregar plugin '{plugin_name}': {e}")
        
        self.executor.shutdown(wait=True)

# Instância global do gerenciador de plugins
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> Optional[PluginManager]:
    """Obtém a instância global do gerenciador de plugins"""
    return _plugin_manager

def initialize_plugin_manager(bot=None, plugins_dir: str = "plugins") -> PluginManager:
    """Inicializa o gerenciador de plugins"""
    global _plugin_manager
    _plugin_manager = PluginManager(bot, plugins_dir)
    return _plugin_manager

# Funções de conveniência
async def load_plugin(plugin_name: str) -> bool:
    """Carrega um plugin"""
    manager = get_plugin_manager()
    if manager:
        return await manager.load_plugin(plugin_name)
    return False

async def unload_plugin(plugin_name: str) -> bool:
    """Descarrega um plugin"""
    manager = get_plugin_manager()
    if manager:
        return await manager.unload_plugin(plugin_name)
    return False

async def reload_plugin(plugin_name: str) -> bool:
    """Recarrega um plugin"""
    manager = get_plugin_manager()
    if manager:
        return await manager.reload_plugin(plugin_name)
    return False

def get_plugin(plugin_name: str) -> Optional[Plugin]:
    """Obtém instância de um plugin"""
    manager = get_plugin_manager()
    if manager:
        return manager.get_plugin(plugin_name)
    return None

def is_plugin_loaded(plugin_name: str) -> bool:
    """Verifica se plugin está carregado"""
    manager = get_plugin_manager()
    if manager:
        return manager.is_plugin_loaded(plugin_name)
    return False

def get_loaded_plugins() -> List[str]:
    """Obtém lista de plugins carregados"""
    manager = get_plugin_manager()
    if manager:
        return manager.get_loaded_plugins()
    return []

def discover_plugins() -> List[str]:
    """Descobre plugins disponíveis"""
    manager = get_plugin_manager()
    if manager:
        return manager.discover_plugins()
    return []