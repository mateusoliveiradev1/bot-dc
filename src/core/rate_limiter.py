"""Sistema de rate limiting avançado para o Hawk Bot.

Este módulo fornece:
- Rate limiting por usuário, servidor e global
- Diferentes algoritmos de rate limiting
- Whitelist e blacklist
- Rate limiting adaptativo
- Métricas de rate limiting
- Integração com sistema de punições
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import json
from pathlib import Path

try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None

class RateLimitAlgorithm(Enum):
    """Algoritmos de rate limiting disponíveis"""
    TOKEN_BUCKET = "token_bucket"      # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window algorithm
    FIXED_WINDOW = "fixed_window"      # Fixed window algorithm
    LEAKY_BUCKET = "leaky_bucket"      # Leaky bucket algorithm
    ADAPTIVE = "adaptive"              # Adaptive rate limiting

class RateLimitScope(Enum):
    """Escopo do rate limiting"""
    USER = "user"          # Por usuário
    GUILD = "guild"        # Por servidor
    CHANNEL = "channel"    # Por canal
    GLOBAL = "global"      # Global
    COMMAND = "command"    # Por comando específico

class RateLimitAction(Enum):
    """Ações quando rate limit é atingido"""
    IGNORE = "ignore"              # Ignorar comando
    WARNING = "warning"            # Enviar aviso
    TIMEOUT = "timeout"            # Timeout temporário
    KICK = "kick"                  # Expulsar do servidor
    BAN = "ban"                    # Banir do servidor
    CUSTOM = "custom"              # Ação customizada

@dataclass
class RateLimitConfig:
    """Configuração de rate limiting"""
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    max_requests: int = 10
    time_window: int = 60  # segundos
    burst_limit: Optional[int] = None  # Para token bucket
    refill_rate: Optional[float] = None  # Para token bucket
    scope: RateLimitScope = RateLimitScope.USER
    action: RateLimitAction = RateLimitAction.IGNORE
    whitelist: List[int] = field(default_factory=list)
    blacklist: List[int] = field(default_factory=list)
    enabled: bool = True
    custom_message: Optional[str] = None
    punishment_duration: int = 300  # segundos para timeout
    escalation_enabled: bool = False
    escalation_multiplier: float = 2.0

@dataclass
class RateLimitEntry:
    """Entrada de rate limiting"""
    identifier: str
    requests: deque = field(default_factory=deque)
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.time)
    violations: int = 0
    last_violation: Optional[datetime] = None
    punishment_until: Optional[datetime] = None
    total_requests: int = 0
    blocked_requests: int = 0

class TokenBucket:
    """Implementação do algoritmo Token Bucket"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Tenta consumir tokens do bucket"""
        now = time.time()
        
        # Adicionar tokens baseado no tempo decorrido
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        # Verificar se há tokens suficientes
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Retorna o tempo de espera para obter tokens suficientes"""
        if self.tokens >= tokens:
            return 0.0
        
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate

class SlidingWindow:
    """Implementação do algoritmo Sliding Window"""
    
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
    
    def is_allowed(self) -> bool:
        """Verifica se uma nova requisição é permitida"""
        now = time.time()
        
        # Remove requisições antigas
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        # Verifica se pode adicionar nova requisição
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def get_reset_time(self) -> float:
        """Retorna quando a janela será resetada"""
        if not self.requests:
            return 0.0
        
        return self.requests[0] + self.window_size - time.time()

class FixedWindow:
    """Implementação do algoritmo Fixed Window"""
    
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size
        self.current_window = 0
        self.request_count = 0
    
    def is_allowed(self) -> bool:
        """Verifica se uma nova requisição é permitida"""
        now = time.time()
        current_window = int(now // self.window_size)
        
        # Nova janela
        if current_window != self.current_window:
            self.current_window = current_window
            self.request_count = 0
        
        # Verifica se pode adicionar nova requisição
        if self.request_count < self.max_requests:
            self.request_count += 1
            return True
        
        return False
    
    def get_reset_time(self) -> float:
        """Retorna quando a janela será resetada"""
        now = time.time()
        next_window = (int(now // self.window_size) + 1) * self.window_size
        return next_window - now

class AdaptiveRateLimiter:
    """Rate limiter adaptativo que ajusta limites baseado no comportamento"""
    
    def __init__(self, base_limit: int, window_size: int):
        self.base_limit = base_limit
        self.window_size = window_size
        self.current_limit = base_limit
        self.violation_count = 0
        self.last_adjustment = time.time()
        self.requests = deque()
    
    def is_allowed(self) -> bool:
        """Verifica se uma nova requisição é permitida"""
        now = time.time()
        
        # Remove requisições antigas
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        # Ajustar limite se necessário
        self._adjust_limit()
        
        # Verifica se pode adicionar nova requisição
        if len(self.requests) < self.current_limit:
            self.requests.append(now)
            return True
        
        # Registrar violação
        self.violation_count += 1
        return False
    
    def _adjust_limit(self):
        """Ajusta o limite baseado no comportamento recente"""
        now = time.time()
        
        # Ajustar a cada 5 minutos
        if now - self.last_adjustment < 300:
            return
        
        self.last_adjustment = now
        
        # Se há muitas violações, diminuir limite
        if self.violation_count > 5:
            self.current_limit = max(1, int(self.current_limit * 0.8))
            self.violation_count = 0
        # Se não há violações, aumentar limite gradualmente
        elif self.violation_count == 0 and self.current_limit < self.base_limit:
            self.current_limit = min(self.base_limit, int(self.current_limit * 1.1))

class RateLimiter:
    """Sistema principal de rate limiting"""
    
    def __init__(self):
        self.configs: Dict[str, RateLimitConfig] = {}
        self.entries: Dict[str, Dict[str, RateLimitEntry]] = defaultdict(dict)
        self.algorithms: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Métricas
        self.total_requests = 0
        self.blocked_requests = 0
        self.violations_by_user = defaultdict(int)
        
        # Carregar configurações padrão
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Carrega configurações padrão de rate limiting"""
        # Rate limiting global
        self.add_rate_limit(
            "global",
            RateLimitConfig(
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                max_requests=100,
                time_window=60,
                burst_limit=20,
                refill_rate=2.0,
                scope=RateLimitScope.GLOBAL,
                action=RateLimitAction.IGNORE
            )
        )
        
        # Rate limiting por usuário
        self.add_rate_limit(
            "user_commands",
            RateLimitConfig(
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                max_requests=10,
                time_window=60,
                scope=RateLimitScope.USER,
                action=RateLimitAction.WARNING,
                escalation_enabled=True
            )
        )
        
        # Rate limiting por servidor
        self.add_rate_limit(
            "guild_commands",
            RateLimitConfig(
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                max_requests=50,
                time_window=60,
                scope=RateLimitScope.GUILD,
                action=RateLimitAction.IGNORE
            )
        )
        
        # Rate limiting adaptativo para spam
        self.add_rate_limit(
            "anti_spam",
            RateLimitConfig(
                algorithm=RateLimitAlgorithm.ADAPTIVE,
                max_requests=5,
                time_window=10,
                scope=RateLimitScope.USER,
                action=RateLimitAction.TIMEOUT,
                punishment_duration=300,
                escalation_enabled=True,
                escalation_multiplier=2.0
            )
        )
    
    def add_rate_limit(self, name: str, config: RateLimitConfig):
        """Adiciona uma nova configuração de rate limiting"""
        self.configs[name] = config
        self.logger.info(f"Rate limit '{name}' configurado: {config.max_requests}/{config.time_window}s")
    
    def remove_rate_limit(self, name: str):
        """Remove uma configuração de rate limiting"""
        if name in self.configs:
            del self.configs[name]
            if name in self.entries:
                del self.entries[name]
            if name in self.algorithms:
                del self.algorithms[name]
    
    def _get_identifier(self, config: RateLimitConfig, user_id: Optional[int] = None,
                       guild_id: Optional[int] = None, channel_id: Optional[int] = None,
                       command: Optional[str] = None) -> str:
        """Gera identificador baseado no escopo"""
        if config.scope == RateLimitScope.USER and user_id:
            return f"user_{user_id}"
        elif config.scope == RateLimitScope.GUILD and guild_id:
            return f"guild_{guild_id}"
        elif config.scope == RateLimitScope.CHANNEL and channel_id:
            return f"channel_{channel_id}"
        elif config.scope == RateLimitScope.COMMAND and command:
            return f"command_{command}_{user_id or 'global'}"
        else:
            return "global"
    
    def _get_or_create_algorithm(self, name: str, identifier: str, config: RateLimitConfig) -> Any:
        """Obtém ou cria instância do algoritmo"""
        if identifier not in self.algorithms[name]:
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                capacity = config.burst_limit or config.max_requests
                refill_rate = config.refill_rate or (config.max_requests / config.time_window)
                self.algorithms[name][identifier] = TokenBucket(capacity, refill_rate)
            
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                self.algorithms[name][identifier] = SlidingWindow(config.max_requests, config.time_window)
            
            elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                self.algorithms[name][identifier] = FixedWindow(config.max_requests, config.time_window)
            
            elif config.algorithm == RateLimitAlgorithm.ADAPTIVE:
                self.algorithms[name][identifier] = AdaptiveRateLimiter(config.max_requests, config.time_window)
        
        return self.algorithms[name][identifier]
    
    def _is_whitelisted(self, config: RateLimitConfig, user_id: Optional[int] = None,
                       guild_id: Optional[int] = None) -> bool:
        """Verifica se está na whitelist"""
        if user_id and user_id in config.whitelist:
            return True
        if guild_id and guild_id in config.whitelist:
            return True
        return False
    
    def _is_blacklisted(self, config: RateLimitConfig, user_id: Optional[int] = None,
                       guild_id: Optional[int] = None) -> bool:
        """Verifica se está na blacklist"""
        if user_id and user_id in config.blacklist:
            return True
        if guild_id and guild_id in config.blacklist:
            return True
        return False
    
    async def check_rate_limit(self, name: str, user_id: Optional[int] = None,
                             guild_id: Optional[int] = None, channel_id: Optional[int] = None,
                             command: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Verifica se uma ação é permitida pelo rate limiting"""
        if name not in self.configs:
            return True, None
        
        config = self.configs[name]
        
        # Verificar se está desabilitado
        if not config.enabled:
            return True, None
        
        # Verificar whitelist
        if self._is_whitelisted(config, user_id, guild_id):
            return True, None
        
        # Verificar blacklist
        if self._is_blacklisted(config, user_id, guild_id):
            return False, "Usuário/servidor está na blacklist"
        
        identifier = self._get_identifier(config, user_id, guild_id, channel_id, command)
        
        # Obter ou criar entrada
        if identifier not in self.entries[name]:
            self.entries[name][identifier] = RateLimitEntry(identifier=identifier)
        
        entry = self.entries[name][identifier]
        
        # Verificar se está em punição
        if entry.punishment_until and datetime.now() < entry.punishment_until:
            return False, f"Em punição até {entry.punishment_until.strftime('%H:%M:%S')}"
        
        # Limpar punição expirada
        if entry.punishment_until and datetime.now() >= entry.punishment_until:
            entry.punishment_until = None
        
        # Incrementar contador de requisições
        entry.total_requests += 1
        self.total_requests += 1
        
        # Verificar rate limit usando algoritmo apropriado
        algorithm = self._get_or_create_algorithm(name, identifier, config)
        
        allowed = False
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            allowed = algorithm.consume()
        elif config.algorithm in [RateLimitAlgorithm.SLIDING_WINDOW, 
                                 RateLimitAlgorithm.FIXED_WINDOW,
                                 RateLimitAlgorithm.ADAPTIVE]:
            allowed = algorithm.is_allowed()
        
        if not allowed:
            # Rate limit atingido
            entry.blocked_requests += 1
            entry.violations += 1
            entry.last_violation = datetime.now()
            self.blocked_requests += 1
            
            if user_id:
                self.violations_by_user[user_id] += 1
            
            # Aplicar ação
            await self._apply_rate_limit_action(config, entry, user_id, guild_id, channel_id)
            
            return False, self._get_rate_limit_message(config, algorithm)
        
        return True, None
    
    async def _apply_rate_limit_action(self, config: RateLimitConfig, entry: RateLimitEntry,
                                     user_id: Optional[int] = None, guild_id: Optional[int] = None,
                                     channel_id: Optional[int] = None):
        """Aplica ação quando rate limit é atingido"""
        if config.action == RateLimitAction.IGNORE:
            return
        
        # Calcular duração da punição (com escalação se habilitada)
        duration = config.punishment_duration
        if config.escalation_enabled and entry.violations > 1:
            duration = int(duration * (config.escalation_multiplier ** (entry.violations - 1)))
        
        if config.action == RateLimitAction.TIMEOUT:
            entry.punishment_until = datetime.now() + timedelta(seconds=duration)
            self.logger.warning(f"Usuário {user_id} em timeout por {duration}s (violação #{entry.violations})")
        
        elif config.action == RateLimitAction.WARNING:
            self.logger.warning(f"Rate limit warning para usuário {user_id} (violação #{entry.violations})")
        
        # Outras ações podem ser implementadas aqui (kick, ban, etc.)
    
    def _get_rate_limit_message(self, config: RateLimitConfig, algorithm: Any) -> str:
        """Gera mensagem de rate limit"""
        if config.custom_message:
            return config.custom_message
        
        if hasattr(algorithm, 'get_reset_time'):
            reset_time = algorithm.get_reset_time()
            if reset_time > 0:
                return f"Rate limit atingido. Tente novamente em {reset_time:.1f} segundos."
        elif hasattr(algorithm, 'get_wait_time'):
            wait_time = algorithm.get_wait_time()
            if wait_time > 0:
                return f"Rate limit atingido. Tente novamente em {wait_time:.1f} segundos."
        
        return "Rate limit atingido. Tente novamente mais tarde."
    
    async def reset_rate_limit(self, name: str, identifier: Optional[str] = None):
        """Reseta rate limit para um identificador específico ou todos"""
        if name not in self.entries:
            return
        
        if identifier:
            if identifier in self.entries[name]:
                del self.entries[name][identifier]
            if name in self.algorithms and identifier in self.algorithms[name]:
                del self.algorithms[name][identifier]
        else:
            # Resetar todos
            self.entries[name].clear()
            if name in self.algorithms:
                self.algorithms[name].clear()
    
    async def clear_punishment(self, name: str, user_id: int):
        """Remove punição de um usuário"""
        if name not in self.configs:
            return
        
        config = self.configs[name]
        identifier = self._get_identifier(config, user_id=user_id)
        
        if name in self.entries and identifier in self.entries[name]:
            entry = self.entries[name][identifier]
            entry.punishment_until = None
            entry.violations = 0
            self.logger.info(f"Punição removida para usuário {user_id} no rate limit '{name}'")
    
    def get_rate_limit_info(self, name: str, identifier: Optional[str] = None) -> Dict[str, Any]:
        """Obtém informações sobre rate limiting"""
        if name not in self.configs:
            return {}
        
        config = self.configs[name]
        info = {
            'name': name,
            'config': {
                'algorithm': config.algorithm.value,
                'max_requests': config.max_requests,
                'time_window': config.time_window,
                'scope': config.scope.value,
                'action': config.action.value,
                'enabled': config.enabled
            },
            'entries': {}
        }
        
        if name in self.entries:
            if identifier:
                if identifier in self.entries[name]:
                    entry = self.entries[name][identifier]
                    info['entries'][identifier] = {
                        'total_requests': entry.total_requests,
                        'blocked_requests': entry.blocked_requests,
                        'violations': entry.violations,
                        'last_violation': entry.last_violation.isoformat() if entry.last_violation else None,
                        'punishment_until': entry.punishment_until.isoformat() if entry.punishment_until else None
                    }
            else:
                for ident, entry in self.entries[name].items():
                    info['entries'][ident] = {
                        'total_requests': entry.total_requests,
                        'blocked_requests': entry.blocked_requests,
                        'violations': entry.violations,
                        'last_violation': entry.last_violation.isoformat() if entry.last_violation else None,
                        'punishment_until': entry.punishment_until.isoformat() if entry.punishment_until else None
                    }
        
        return info
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas globais de rate limiting"""
        active_punishments = 0
        total_violations = 0
        
        for name, entries in self.entries.items():
            for entry in entries.values():
                total_violations += entry.violations
                if entry.punishment_until and datetime.now() < entry.punishment_until:
                    active_punishments += 1
        
        return {
            'total_requests': self.total_requests,
            'blocked_requests': self.blocked_requests,
            'block_rate': (self.blocked_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            'total_violations': total_violations,
            'active_punishments': active_punishments,
            'configured_limits': len(self.configs),
            'top_violators': dict(sorted(self.violations_by_user.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    async def _cleanup_loop(self):
        """Loop de limpeza para remover entradas antigas"""
        while self._running:
            try:
                now = datetime.now()
                
                for name, entries in list(self.entries.items()):
                    for identifier, entry in list(entries.items()):
                        # Remover entradas antigas (sem atividade por 1 hora)
                        if (entry.last_violation is None or 
                            (now - entry.last_violation).total_seconds() > 3600):
                            
                            # Manter apenas se há punição ativa
                            if not (entry.punishment_until and now < entry.punishment_until):
                                del entries[identifier]
                                if name in self.algorithms and identifier in self.algorithms[name]:
                                    del self.algorithms[name][identifier]
                
                await asyncio.sleep(300)  # Limpeza a cada 5 minutos
                
            except Exception as e:
                self.logger.error(f"Erro no loop de limpeza do rate limiter: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Inicia o sistema de rate limiting"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Sistema de rate limiting iniciado")
    
    async def stop(self):
        """Para o sistema de rate limiting"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Sistema de rate limiting parado")

# Instância global do rate limiter
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Obtém a instância global do rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

# Funções de conveniência
async def check_rate_limit(name: str, user_id: Optional[int] = None,
                         guild_id: Optional[int] = None, channel_id: Optional[int] = None,
                         command: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Verifica rate limit"""
    return await get_rate_limiter().check_rate_limit(name, user_id, guild_id, channel_id, command)

def add_rate_limit(name: str, config: RateLimitConfig):
    """Adiciona configuração de rate limit"""
    get_rate_limiter().add_rate_limit(name, config)

async def reset_rate_limit(name: str, identifier: Optional[str] = None):
    """Reseta rate limit"""
    await get_rate_limiter().reset_rate_limit(name, identifier)

async def clear_punishment(name: str, user_id: int):
    """Remove punição"""
    await get_rate_limiter().clear_punishment(name, user_id)

def get_rate_limit_stats() -> Dict[str, Any]:
    """Obtém estatísticas de rate limiting"""
    return get_rate_limiter().get_global_stats()

async def start_rate_limiter():
    """Inicia o sistema de rate limiting"""
    await get_rate_limiter().start()

async def stop_rate_limiter():
    """Para o sistema de rate limiting"""
    await get_rate_limiter().stop()

# Decorador para rate limiting automático
def rate_limit(name: str, max_requests: int = 10, time_window: int = 60,
              scope: RateLimitScope = RateLimitScope.USER,
              action: RateLimitAction = RateLimitAction.IGNORE):
    """Decorador para aplicar rate limiting a comandos"""
    def decorator(func):
        # Registrar rate limit se não existir
        limiter = get_rate_limiter()
        if name not in limiter.configs:
            config = RateLimitConfig(
                max_requests=max_requests,
                time_window=time_window,
                scope=scope,
                action=action
            )
            limiter.add_rate_limit(name, config)
        
        async def wrapper(*args, **kwargs):
            # Extrair IDs do contexto (assumindo comando Discord)
            user_id = None
            guild_id = None
            channel_id = None
            
            if DISCORD_AVAILABLE and args:
                ctx = args[0] if hasattr(args[0], 'author') else None
                if ctx:
                    user_id = ctx.author.id if hasattr(ctx, 'author') else None
                    guild_id = ctx.guild.id if hasattr(ctx, 'guild') and ctx.guild else None
                    channel_id = ctx.channel.id if hasattr(ctx, 'channel') else None
            
            # Verificar rate limit
            allowed, message = await check_rate_limit(
                name, user_id, guild_id, channel_id, func.__name__
            )
            
            if not allowed:
                if message and DISCORD_AVAILABLE and hasattr(args[0], 'send'):
                    await args[0].send(f"⚠️ {message}")
                return
            
            # Executar função original
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator