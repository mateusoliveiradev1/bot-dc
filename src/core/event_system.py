"""Sistema de eventos e hooks para o Hawk Bot.

Este módulo fornece:
- Sistema de eventos assíncronos
- Hooks para interceptar e modificar comportamentos
- Event listeners com prioridades
- Sistema de middleware
- Eventos customizados
- Propagação e cancelamento de eventos
- Métricas de eventos
"""

import asyncio
import inspect
import logging
from typing import Any, Dict, List, Optional, Callable, Union, Type, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
import weakref
import traceback

try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None

class EventPriority(Enum):
    """Prioridades de eventos"""
    HIGHEST = 1000
    HIGH = 750
    NORMAL = 500
    LOW = 250
    LOWEST = 0

class EventPhase(Enum):
    """Fases de execução de eventos"""
    PRE = "pre"        # Antes do evento principal
    MAIN = "main"      # Evento principal
    POST = "post"      # Após o evento principal
    CLEANUP = "cleanup" # Limpeza após o evento

class HookType(Enum):
    """Tipos de hooks"""
    BEFORE = "before"    # Executado antes da função
    AFTER = "after"      # Executado após a função
    AROUND = "around"    # Envolve a função
    REPLACE = "replace"  # Substitui a função
    ERROR = "error"      # Executado em caso de erro

@dataclass
class EventData:
    """Dados de um evento"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    cancelled: bool = False
    propagation_stopped: bool = False
    phase: EventPhase = EventPhase.MAIN
    priority: EventPriority = EventPriority.NORMAL
    
    def cancel(self):
        """Cancela o evento"""
        self.cancelled = True
    
    def stop_propagation(self):
        """Para a propagação do evento"""
        self.propagation_stopped = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém dados do evento"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Define dados do evento"""
        self.data[key] = value
    
    def update(self, data: Dict[str, Any]):
        """Atualiza dados do evento"""
        self.data.update(data)

@dataclass
class EventListener:
    """Listener de evento"""
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    phase: EventPhase = EventPhase.MAIN
    once: bool = False
    condition: Optional[Callable] = None
    name: Optional[str] = None
    enabled: bool = True
    call_count: int = 0
    last_called: Optional[datetime] = None
    
    async def execute(self, event: EventData) -> Any:
        """Executa o listener"""
        if not self.enabled:
            return None
        
        # Verificar condição se existir
        if self.condition and not await self._check_condition(event):
            return None
        
        self.call_count += 1
        self.last_called = datetime.now()
        
        try:
            if inspect.iscoroutinefunction(self.callback):
                result = await self.callback(event)
            else:
                result = self.callback(event)
            
            # Remover listener se for "once"
            if self.once:
                self.enabled = False
            
            return result
            
        except Exception as e:
            logging.error(f"Erro ao executar listener {self.name}: {e}")
            raise
    
    async def _check_condition(self, event: EventData) -> bool:
        """Verifica condição do listener"""
        try:
            if inspect.iscoroutinefunction(self.condition):
                return await self.condition(event)
            else:
                return self.condition(event)
        except Exception:
            return False

@dataclass
class Hook:
    """Hook para interceptar funções"""
    callback: Callable
    hook_type: HookType
    priority: EventPriority = EventPriority.NORMAL
    condition: Optional[Callable] = None
    name: Optional[str] = None
    enabled: bool = True
    call_count: int = 0
    
    async def execute(self, *args, **kwargs) -> Any:
        """Executa o hook"""
        if not self.enabled:
            return None
        
        self.call_count += 1
        
        try:
            if inspect.iscoroutinefunction(self.callback):
                return await self.callback(*args, **kwargs)
            else:
                return self.callback(*args, **kwargs)
        except Exception as e:
            logging.error(f"Erro ao executar hook {self.name}: {e}")
            raise

class EventSystem:
    """Sistema principal de eventos"""
    
    def __init__(self):
        self.listeners: Dict[str, List[EventListener]] = defaultdict(list)
        self.hooks: Dict[str, Dict[HookType, List[Hook]]] = defaultdict(lambda: defaultdict(list))
        self.middleware: List[Callable] = []
        self.event_history: deque = deque(maxlen=1000)
        self.logger = logging.getLogger(__name__)
        
        # Métricas
        self.event_count = defaultdict(int)
        self.listener_count = defaultdict(int)
        self.hook_count = defaultdict(int)
        self.error_count = defaultdict(int)
        
        # Weak references para cleanup automático
        self._weak_refs: List[weakref.ref] = []
        
        # Eventos padrão do sistema
        self._register_system_events()
    
    def _register_system_events(self):
        """Registra eventos padrão do sistema"""
        system_events = [
            'bot_ready',
            'bot_shutdown',
            'command_executed',
            'command_error',
            'user_joined',
            'user_left',
            'message_received',
            'message_deleted',
            'message_edited',
            'reaction_added',
            'reaction_removed',
            'voice_state_changed',
            'member_banned',
            'member_unbanned',
            'guild_joined',
            'guild_left',
            'error_occurred',
            'cache_hit',
            'cache_miss',
            'rate_limit_hit',
            'backup_created',
            'config_changed'
        ]
        
        for event_name in system_events:
            self.listeners[event_name] = []
    
    def on(self, event_name: str, priority: EventPriority = EventPriority.NORMAL,
           phase: EventPhase = EventPhase.MAIN, once: bool = False,
           condition: Optional[Callable] = None, name: Optional[str] = None):
        """Decorador para registrar event listener"""
        def decorator(callback: Callable):
            self.add_listener(event_name, callback, priority, phase, once, condition, name)
            return callback
        return decorator
    
    def add_listener(self, event_name: str, callback: Callable,
                    priority: EventPriority = EventPriority.NORMAL,
                    phase: EventPhase = EventPhase.MAIN,
                    once: bool = False,
                    condition: Optional[Callable] = None,
                    name: Optional[str] = None) -> EventListener:
        """Adiciona um event listener"""
        listener = EventListener(
            callback=callback,
            priority=priority,
            phase=phase,
            once=once,
            condition=condition,
            name=name or f"{callback.__name__}_{len(self.listeners[event_name])}"
        )
        
        self.listeners[event_name].append(listener)
        
        # Ordenar por prioridade (maior primeiro)
        self.listeners[event_name].sort(key=lambda x: x.priority.value, reverse=True)
        
        self.listener_count[event_name] += 1
        self.logger.debug(f"Listener '{listener.name}' adicionado para evento '{event_name}'")
        
        return listener
    
    def remove_listener(self, event_name: str, listener: Union[EventListener, str]):
        """Remove um event listener"""
        if event_name not in self.listeners:
            return False
        
        listeners = self.listeners[event_name]
        
        if isinstance(listener, str):
            # Remover por nome
            for i, l in enumerate(listeners):
                if l.name == listener:
                    del listeners[i]
                    self.listener_count[event_name] -= 1
                    return True
        else:
            # Remover por referência
            if listener in listeners:
                listeners.remove(listener)
                self.listener_count[event_name] -= 1
                return True
        
        return False
    
    def add_hook(self, function_name: str, hook_type: HookType, callback: Callable,
                priority: EventPriority = EventPriority.NORMAL,
                condition: Optional[Callable] = None,
                name: Optional[str] = None) -> Hook:
        """Adiciona um hook"""
        hook = Hook(
            callback=callback,
            hook_type=hook_type,
            priority=priority,
            condition=condition,
            name=name or f"{callback.__name__}_{len(self.hooks[function_name][hook_type])}"
        )
        
        self.hooks[function_name][hook_type].append(hook)
        
        # Ordenar por prioridade
        self.hooks[function_name][hook_type].sort(key=lambda x: x.priority.value, reverse=True)
        
        self.hook_count[function_name] += 1
        self.logger.debug(f"Hook '{hook.name}' adicionado para função '{function_name}'")
        
        return hook
    
    def add_middleware(self, middleware: Callable):
        """Adiciona middleware para processar todos os eventos"""
        self.middleware.append(middleware)
        self.logger.debug(f"Middleware '{middleware.__name__}' adicionado")
    
    async def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None,
                  source: Optional[str] = None, phase: EventPhase = EventPhase.MAIN,
                  priority: EventPriority = EventPriority.NORMAL) -> EventData:
        """Emite um evento"""
        event = EventData(
            name=event_name,
            data=data or {},
            source=source,
            phase=phase,
            priority=priority
        )
        
        self.event_count[event_name] += 1
        self.event_history.append(event)
        
        try:
            # Processar middleware
            for middleware in self.middleware:
                try:
                    if inspect.iscoroutinefunction(middleware):
                        await middleware(event)
                    else:
                        middleware(event)
                    
                    if event.cancelled or event.propagation_stopped:
                        break
                except Exception as e:
                    self.logger.error(f"Erro no middleware: {e}")
                    self.error_count[event_name] += 1
            
            # Executar listeners se o evento não foi cancelado
            if not event.cancelled:
                await self._execute_listeners(event_name, event)
            
            return event
            
        except Exception as e:
            self.logger.error(f"Erro ao emitir evento '{event_name}': {e}")
            self.error_count[event_name] += 1
            raise
    
    async def _execute_listeners(self, event_name: str, event: EventData):
        """Executa listeners para um evento"""
        if event_name not in self.listeners:
            return
        
        # Filtrar listeners por fase
        phase_listeners = [l for l in self.listeners[event_name] 
                          if l.phase == event.phase and l.enabled]
        
        # Executar listeners em ordem de prioridade
        for listener in phase_listeners:
            if event.propagation_stopped:
                break
            
            try:
                await listener.execute(event)
            except Exception as e:
                self.logger.error(f"Erro ao executar listener '{listener.name}': {e}")
                self.error_count[event_name] += 1
                
                # Emitir evento de erro
                error_event = EventData(
                    name='listener_error',
                    data={
                        'original_event': event_name,
                        'listener_name': listener.name,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                )
                
                # Evitar recursão infinita
                if event_name != 'listener_error':
                    await self.emit('listener_error', error_event.data)
        
        # Remover listeners "once" que foram desabilitados
        self.listeners[event_name] = [l for l in self.listeners[event_name] if l.enabled]
    
    async def emit_phases(self, event_name: str, data: Optional[Dict[str, Any]] = None,
                         source: Optional[str] = None) -> List[EventData]:
        """Emite evento em todas as fases"""
        events = []
        
        for phase in EventPhase:
            event = await self.emit(event_name, data, source, phase)
            events.append(event)
            
            # Parar se o evento foi cancelado
            if event.cancelled:
                break
        
        return events
    
    async def apply_hooks(self, function_name: str, hook_type: HookType,
                         *args, **kwargs) -> Any:
        """Aplica hooks a uma função"""
        if function_name not in self.hooks or hook_type not in self.hooks[function_name]:
            return None
        
        hooks = self.hooks[function_name][hook_type]
        results = []
        
        for hook in hooks:
            if not hook.enabled:
                continue
            
            try:
                result = await hook.execute(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Erro ao executar hook '{hook.name}': {e}")
                self.error_count[function_name] += 1
        
        return results
    
    def create_event_emitter(self, source: str):
        """Cria um emissor de eventos com fonte específica"""
        class EventEmitter:
            def __init__(self, event_system: EventSystem, source: str):
                self.event_system = event_system
                self.source = source
            
            async def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None,
                          phase: EventPhase = EventPhase.MAIN,
                          priority: EventPriority = EventPriority.NORMAL) -> EventData:
                return await self.event_system.emit(event_name, data, self.source, phase, priority)
            
            async def emit_phases(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> List[EventData]:
                return await self.event_system.emit_phases(event_name, data, self.source)
        
        return EventEmitter(self, source)
    
    def get_listeners(self, event_name: str) -> List[EventListener]:
        """Obtém listeners de um evento"""
        return self.listeners.get(event_name, [])
    
    def get_hooks(self, function_name: str) -> Dict[HookType, List[Hook]]:
        """Obtém hooks de uma função"""
        return self.hooks.get(function_name, {})
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de eventos"""
        total_events = sum(self.event_count.values())
        total_errors = sum(self.error_count.values())
        
        return {
            'total_events': total_events,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_events * 100) if total_events > 0 else 0,
            'events_by_name': dict(self.event_count),
            'errors_by_name': dict(self.error_count),
            'listeners_by_event': dict(self.listener_count),
            'hooks_by_function': dict(self.hook_count),
            'registered_events': list(self.listeners.keys()),
            'middleware_count': len(self.middleware),
            'recent_events': [{
                'name': e.name,
                'timestamp': e.timestamp.isoformat(),
                'source': e.source,
                'cancelled': e.cancelled
            } for e in list(self.event_history)[-10:]]
        }
    
    def clear_listeners(self, event_name: Optional[str] = None):
        """Remove listeners"""
        if event_name:
            if event_name in self.listeners:
                self.listeners[event_name].clear()
                self.listener_count[event_name] = 0
        else:
            self.listeners.clear()
            self.listener_count.clear()
    
    def clear_hooks(self, function_name: Optional[str] = None):
        """Remove hooks"""
        if function_name:
            if function_name in self.hooks:
                self.hooks[function_name].clear()
                self.hook_count[function_name] = 0
        else:
            self.hooks.clear()
            self.hook_count.clear()
    
    def reset_stats(self):
        """Reseta estatísticas"""
        self.event_count.clear()
        self.error_count.clear()
        self.event_history.clear()

# Instância global do sistema de eventos
_event_system: Optional[EventSystem] = None

def get_event_system() -> EventSystem:
    """Obtém a instância global do sistema de eventos"""
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
    return _event_system

# Funções de conveniência
def on(event_name: str, priority: EventPriority = EventPriority.NORMAL,
       phase: EventPhase = EventPhase.MAIN, once: bool = False,
       condition: Optional[Callable] = None, name: Optional[str] = None):
    """Decorador para registrar event listener"""
    return get_event_system().on(event_name, priority, phase, once, condition, name)

def add_listener(event_name: str, callback: Callable,
                priority: EventPriority = EventPriority.NORMAL,
                phase: EventPhase = EventPhase.MAIN,
                once: bool = False,
                condition: Optional[Callable] = None,
                name: Optional[str] = None) -> EventListener:
    """Adiciona event listener"""
    return get_event_system().add_listener(event_name, callback, priority, phase, once, condition, name)

def add_hook(function_name: str, hook_type: HookType, callback: Callable,
            priority: EventPriority = EventPriority.NORMAL,
            condition: Optional[Callable] = None,
            name: Optional[str] = None) -> Hook:
    """Adiciona hook"""
    return get_event_system().add_hook(function_name, hook_type, callback, priority, condition, name)

async def emit(event_name: str, data: Optional[Dict[str, Any]] = None,
              source: Optional[str] = None, phase: EventPhase = EventPhase.MAIN,
              priority: EventPriority = EventPriority.NORMAL) -> EventData:
    """Emite evento"""
    return await get_event_system().emit(event_name, data, source, phase, priority)

async def emit_phases(event_name: str, data: Optional[Dict[str, Any]] = None,
                     source: Optional[str] = None) -> List[EventData]:
    """Emite evento em todas as fases"""
    return await get_event_system().emit_phases(event_name, data, source)

def add_middleware(middleware: Callable):
    """Adiciona middleware"""
    get_event_system().add_middleware(middleware)

def get_event_stats() -> Dict[str, Any]:
    """Obtém estatísticas de eventos"""
    return get_event_system().get_event_stats()

# Decoradores úteis
def hookable(function_name: Optional[str] = None):
    """Decorador para tornar uma função hookable"""
    def decorator(func):
        fname = function_name or func.__name__
        
        async def wrapper(*args, **kwargs):
            event_system = get_event_system()
            
            # Executar hooks BEFORE
            await event_system.apply_hooks(fname, HookType.BEFORE, *args, **kwargs)
            
            try:
                # Executar função original
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Executar hooks AFTER
                await event_system.apply_hooks(fname, HookType.AFTER, result, *args, **kwargs)
                
                return result
                
            except Exception as e:
                # Executar hooks ERROR
                await event_system.apply_hooks(fname, HookType.ERROR, e, *args, **kwargs)
                raise
        
        return wrapper
    return decorator

def event_emitter(source: str):
    """Decorador para criar emissor de eventos automático"""
    def decorator(cls):
        emitter = get_event_system().create_event_emitter(source)
        cls._event_emitter = emitter
        cls.emit_event = emitter.emit
        cls.emit_event_phases = emitter.emit_phases
        return cls
    return decorator

# Middleware úteis
async def logging_middleware(event: EventData):
    """Middleware para logging de eventos"""
    logger = logging.getLogger('events')
    logger.debug(f"Evento '{event.name}' emitido por '{event.source}' com dados: {event.data}")

async def metrics_middleware(event: EventData):
    """Middleware para métricas de eventos"""
    try:
        from .metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics.increment_counter(f'events.{event.name}.count')
        metrics.record_gauge(f'events.{event.name}.last_timestamp', event.timestamp.timestamp())
    except ImportError:
        pass

async def validation_middleware(event: EventData):
    """Middleware para validação de eventos"""
    try:
        from .data_validator import get_data_validator
        validator = get_data_validator()
        
        # Validar dados do evento se houver schema
        schema_name = f'event_{event.name}'
        valid, validated_data, errors = validator.validate_data(event.data, schema_name)
        
        if not valid and errors:
            logging.warning(f"Dados inválidos no evento '{event.name}': {errors}")
            # Não cancelar o evento, apenas logar
    except ImportError:
        pass

# Registrar middleware padrão
def _register_default_middleware():
    """Registra middleware padrão"""
    event_system = get_event_system()
    event_system.add_middleware(logging_middleware)
    event_system.add_middleware(metrics_middleware)
    event_system.add_middleware(validation_middleware)

# Inicializar middleware padrão
_register_default_middleware()

# Eventos Discord integrados
if DISCORD_AVAILABLE:
    class DiscordEventIntegration:
        """Integração com eventos do Discord.py"""
        
        def __init__(self, bot):
            self.bot = bot
            self.event_system = get_event_system()
            self._setup_discord_events()
        
        def _setup_discord_events(self):
            """Configura eventos do Discord"""
            
            @self.bot.event
            async def on_ready():
                await self.event_system.emit('bot_ready', {
                    'bot_user': self.bot.user.id if self.bot.user else None,
                    'guild_count': len(self.bot.guilds),
                    'user_count': sum(g.member_count for g in self.bot.guilds)
                }, 'discord')
            
            @self.bot.event
            async def on_message(message):
                await self.event_system.emit('message_received', {
                    'message_id': message.id,
                    'author_id': message.author.id,
                    'guild_id': message.guild.id if message.guild else None,
                    'channel_id': message.channel.id,
                    'content': message.content,
                    'is_bot': message.author.bot
                }, 'discord')
            
            @self.bot.event
            async def on_member_join(member):
                await self.event_system.emit('user_joined', {
                    'user_id': member.id,
                    'guild_id': member.guild.id,
                    'username': member.name,
                    'joined_at': member.joined_at.isoformat() if member.joined_at else None
                }, 'discord')
            
            @self.bot.event
            async def on_member_remove(member):
                await self.event_system.emit('user_left', {
                    'user_id': member.id,
                    'guild_id': member.guild.id,
                    'username': member.name
                }, 'discord')
            
            @self.bot.event
            async def on_command_completion(ctx):
                await self.event_system.emit('command_executed', {
                    'command_name': ctx.command.name if ctx.command else 'unknown',
                    'user_id': ctx.author.id,
                    'guild_id': ctx.guild.id if ctx.guild else None,
                    'channel_id': ctx.channel.id,
                    'success': True
                }, 'discord')
            
            @self.bot.event
            async def on_command_error(ctx, error):
                await self.event_system.emit('command_error', {
                    'command_name': ctx.command.name if ctx.command else 'unknown',
                    'user_id': ctx.author.id,
                    'guild_id': ctx.guild.id if ctx.guild else None,
                    'channel_id': ctx.channel.id,
                    'error': str(error),
                    'error_type': type(error).__name__
                }, 'discord')
    
    def setup_discord_integration(bot):
        """Configura integração com Discord"""
        return DiscordEventIntegration(bot)
else:
    def setup_discord_integration(bot):
        """Fallback quando Discord não está disponível"""
        logging.warning("Discord.py não disponível, integração de eventos desabilitada")
        return None