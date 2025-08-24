# -*- coding: utf-8 -*-
"""
Sistema de Cache Inteligente - Hawk Bot
Cache com TTL dinâmico, limpeza automática e otimizações de performance
"""

import asyncio
import logging
import time
import weakref
from typing import Any, Dict, Optional, Set, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor

import sys
sys.path.append('.')
from src.core.config import get_config
from .dependency_container import IService

logger = logging.getLogger('HawkBot.SmartCache')

T = TypeVar('T')

class CacheStrategy(Enum):
    """Estratégias de cache disponíveis"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptativo baseado em padrões de uso

class CachePriority(Enum):
    """Prioridades de cache"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class CacheEntry(Generic[T]):
    """Entrada do cache com metadados"""
    value: T
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    priority: CachePriority = CachePriority.NORMAL
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    @property
    def age(self) -> float:
        """Idade da entrada em segundos"""
        return time.time() - self.created_at
    
    @property
    def time_since_access(self) -> float:
        """Tempo desde o último acesso"""
        return time.time() - self.last_accessed
    
    def access(self):
        """Registra um acesso à entrada"""
        self.last_accessed = time.time()
        self.access_count += 1

class CacheStats:
    """Estatísticas do cache"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expired_removals = 0
        self.memory_cleanups = 0
        self.total_size_bytes = 0
        self.peak_size_bytes = 0
        self.start_time = time.time()
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acertos do cache"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def uptime(self) -> float:
        """Tempo de funcionamento em segundos"""
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte estatísticas para dicionário"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate,
            'evictions': self.evictions,
            'expired_removals': self.expired_removals,
            'memory_cleanups': self.memory_cleanups,
            'total_size_bytes': self.total_size_bytes,
            'peak_size_bytes': self.peak_size_bytes,
            'uptime_seconds': self.uptime
        }

class SmartCache(IService):
    """Cache inteligente com TTL dinâmico e otimizações"""
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: float = 3600,
                 strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
                 max_memory_mb: int = 100,
                 cleanup_interval: float = 300):
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        
        # Storage principal
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        
        # Índices para otimização
        self._access_order: Dict[str, float] = {}  # Para LRU
        self._frequency: Dict[str, int] = defaultdict(int)  # Para LFU
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Índice por tags
        
        # Estatísticas e monitoramento
        self.stats = CacheStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="SmartCache")
        
        # Configurações adaptativas
        self._access_patterns: Dict[str, list] = defaultdict(list)
        self._adaptive_ttls: Dict[str, float] = {}
        
        logger.info(f"SmartCache inicializado: max_size={max_size}, strategy={strategy.value}")
    
    async def initialize(self):
        """Inicializa o serviço de cache"""
        config = get_config()
        
        # Atualizar configurações do config
        self.max_size = config.cache.memory_cache_size
        self.default_ttl = config.cache.default_ttl
        self.max_memory_bytes = config.cache.max_memory_usage * 1024 * 1024
        self.cleanup_interval = config.cache.cleanup_interval
        
        # Iniciar tarefa de limpeza
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("SmartCache inicializado com sucesso")
    
    async def cleanup(self):
        """Limpa recursos do cache"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._executor.shutdown(wait=True)
        await self.clear()
        
        logger.info("SmartCache finalizado")
    
    def _calculate_size(self, value: Any) -> int:
        """Calcula o tamanho aproximado de um valor"""
        try:
            return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            # Fallback para estimativa baseada no tipo
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return sys.getsizeof(value)
            elif isinstance(value, (list, tuple, dict)):
                return sys.getsizeof(value) + sum(sys.getsizeof(item) for item in value)
            else:
                return sys.getsizeof(value)
    
    def _generate_key(self, key: Union[str, tuple]) -> str:
        """Gera uma chave de cache consistente"""
        if isinstance(key, str):
            return key
        
        # Para chaves compostas, criar hash
        key_str = str(key)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _calculate_adaptive_ttl(self, key: str) -> float:
        """Calcula TTL adaptativo baseado em padrões de acesso"""
        if key not in self._access_patterns:
            return self.default_ttl
        
        patterns = self._access_patterns[key]
        if len(patterns) < 2:
            return self.default_ttl
        
        # Calcular intervalo médio entre acessos
        intervals = [patterns[i] - patterns[i-1] for i in range(1, len(patterns))]
        avg_interval = sum(intervals) / len(intervals)
        
        # TTL adaptativo: 2x o intervalo médio, com limites
        adaptive_ttl = min(max(avg_interval * 2, 60), self.default_ttl * 2)
        
        self._adaptive_ttls[key] = adaptive_ttl
        return adaptive_ttl
    
    async def get(self, key: Union[str, tuple], default: Any = None) -> Any:
        """Obtém um valor do cache"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key not in self._cache:
                self.stats.misses += 1
                return default
            
            entry = self._cache[cache_key]
            
            # Verificar expiração
            if entry.is_expired:
                await self._remove_entry(cache_key)
                self.stats.misses += 1
                self.stats.expired_removals += 1
                return default
            
            # Registrar acesso
            entry.access()
            self._access_order[cache_key] = time.time()
            self._frequency[cache_key] += 1
            
            # Registrar padrão de acesso para TTL adaptativo
            if self.strategy == CacheStrategy.ADAPTIVE:
                self._access_patterns[cache_key].append(time.time())
                # Manter apenas os últimos 10 acessos
                if len(self._access_patterns[cache_key]) > 10:
                    self._access_patterns[cache_key] = self._access_patterns[cache_key][-10:]
            
            self.stats.hits += 1
            return entry.value
    
    async def set(self, 
                  key: Union[str, tuple], 
                  value: Any, 
                  ttl: Optional[float] = None,
                  priority: CachePriority = CachePriority.NORMAL,
                  tags: Optional[Set[str]] = None) -> bool:
        """Define um valor no cache"""
        cache_key = self._generate_key(key)
        
        # Calcular TTL
        if ttl is None:
            if self.strategy == CacheStrategy.ADAPTIVE:
                ttl = self._calculate_adaptive_ttl(cache_key)
            else:
                ttl = self.default_ttl
        
        # Calcular tamanho
        size_bytes = self._calculate_size(value)
        
        async with self._lock:
            # Verificar limites de memória
            if self.stats.total_size_bytes + size_bytes > self.max_memory_bytes:
                await self._cleanup_memory()
                
                # Se ainda não couber, rejeitar
                if self.stats.total_size_bytes + size_bytes > self.max_memory_bytes:
                    logger.warning(f"Cache cheio, não foi possível armazenar chave: {cache_key}")
                    return False
            
            # Remover entrada existente se houver
            if cache_key in self._cache:
                await self._remove_entry(cache_key)
            
            # Verificar limite de entradas
            if len(self._cache) >= self.max_size:
                await self._evict_entries(1)
            
            # Criar nova entrada
            now = time.time()
            entry = CacheEntry(
                value=value,
                created_at=now,
                last_accessed=now,
                ttl=ttl,
                priority=priority,
                size_bytes=size_bytes,
                tags=tags or set()
            )
            
            # Armazenar
            self._cache[cache_key] = entry
            self._access_order[cache_key] = now
            self._frequency[cache_key] = 1
            
            # Atualizar índices de tags
            for tag in entry.tags:
                self._tags_index[tag].add(cache_key)
            
            # Atualizar estatísticas
            self.stats.total_size_bytes += size_bytes
            if self.stats.total_size_bytes > self.stats.peak_size_bytes:
                self.stats.peak_size_bytes = self.stats.total_size_bytes
            
            return True
    
    async def delete(self, key: Union[str, tuple]) -> bool:
        """Remove uma entrada do cache"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key in self._cache:
                await self._remove_entry(cache_key)
                return True
            return False
    
    async def clear(self, tags: Optional[Set[str]] = None):
        """Limpa o cache (opcionalmente por tags)"""
        async with self._lock:
            if tags is None:
                # Limpar tudo
                self._cache.clear()
                self._access_order.clear()
                self._frequency.clear()
                self._tags_index.clear()
                self._access_patterns.clear()
                self._adaptive_ttls.clear()
                self.stats.total_size_bytes = 0
            else:
                # Limpar por tags
                keys_to_remove = set()
                for tag in tags:
                    if tag in self._tags_index:
                        keys_to_remove.update(self._tags_index[tag])
                
                for cache_key in keys_to_remove:
                    await self._remove_entry(cache_key)
    
    async def _remove_entry(self, cache_key: str):
        """Remove uma entrada específica"""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        
        # Atualizar estatísticas
        self.stats.total_size_bytes -= entry.size_bytes
        
        # Remover dos índices
        self._cache.pop(cache_key, None)
        self._access_order.pop(cache_key, None)
        self._frequency.pop(cache_key, None)
        
        # Remover das tags
        for tag in entry.tags:
            if tag in self._tags_index:
                self._tags_index[tag].discard(cache_key)
                if not self._tags_index[tag]:
                    del self._tags_index[tag]
    
    async def _evict_entries(self, count: int):
        """Remove entradas baseado na estratégia"""
        if not self._cache:
            return
        
        keys_to_remove = []
        
        if self.strategy == CacheStrategy.LRU:
            # Remover menos recentemente usados
            sorted_keys = sorted(self._access_order.items(), key=lambda x: x[1])
            keys_to_remove = [key for key, _ in sorted_keys[:count]]
        
        elif self.strategy == CacheStrategy.LFU:
            # Remover menos frequentemente usados
            sorted_keys = sorted(self._frequency.items(), key=lambda x: x[1])
            keys_to_remove = [key for key, _ in sorted_keys[:count]]
        
        elif self.strategy == CacheStrategy.TTL:
            # Remover por TTL (mais antigos primeiro)
            entries_with_keys = [(key, entry) for key, entry in self._cache.items()]
            sorted_entries = sorted(entries_with_keys, key=lambda x: x[1].created_at)
            keys_to_remove = [key for key, _ in sorted_entries[:count]]
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Estratégia adaptativa: combinar idade, frequência e prioridade
            scored_entries = []
            for key, entry in self._cache.items():
                # Score baseado em: idade (peso 0.3), frequência (peso 0.4), prioridade (peso 0.3)
                age_score = entry.age / 3600  # Normalizar por hora
                freq_score = 1.0 / (self._frequency.get(key, 1) + 1)
                priority_score = (5 - entry.priority.value) / 4  # Inverter prioridade
                
                total_score = (age_score * 0.3) + (freq_score * 0.4) + (priority_score * 0.3)
                scored_entries.append((key, total_score))
            
            sorted_entries = sorted(scored_entries, key=lambda x: x[1], reverse=True)
            keys_to_remove = [key for key, _ in sorted_entries[:count]]
        
        # Remover as entradas selecionadas
        for key in keys_to_remove:
            await self._remove_entry(key)
            self.stats.evictions += 1
    
    async def _cleanup_memory(self):
        """Limpeza de memória quando necessário"""
        # Primeiro, remover entradas expiradas
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self._remove_entry(key)
            self.stats.expired_removals += 1
        
        # Se ainda precisar de espaço, usar estratégia de eviction
        if self.stats.total_size_bytes > self.max_memory_bytes * 0.8:  # 80% do limite
            entries_to_remove = max(1, len(self._cache) // 10)  # Remover 10%
            await self._evict_entries(entries_to_remove)
            self.stats.memory_cleanups += 1
    
    async def _cleanup_loop(self):
        """Loop de limpeza automática"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                async with self._lock:
                    # Remover entradas expiradas
                    expired_keys = []
                    for key, entry in self._cache.items():
                        if entry.is_expired:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        await self._remove_entry(key)
                        self.stats.expired_removals += 1
                    
                    # Verificar uso de memória
                    if self.stats.total_size_bytes > self.max_memory_bytes * 0.9:
                        await self._cleanup_memory()
                
                if expired_keys:
                    logger.debug(f"Limpeza automática: {len(expired_keys)} entradas expiradas removidas")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro na limpeza automática do cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache"""
        stats = self.stats.to_dict()
        stats.update({
            'current_entries': len(self._cache),
            'max_size': self.max_size,
            'strategy': self.strategy.value,
            'memory_usage_mb': self.stats.total_size_bytes / (1024 * 1024),
            'memory_limit_mb': self.max_memory_bytes / (1024 * 1024)
        })
        return stats
    
    async def get_entry_info(self, key: Union[str, tuple]) -> Optional[Dict[str, Any]]:
        """Obtém informações sobre uma entrada específica"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key not in self._cache:
                return None
            
            entry = self._cache[cache_key]
            return {
                'key': cache_key,
                'created_at': entry.created_at,
                'last_accessed': entry.last_accessed,
                'access_count': entry.access_count,
                'ttl': entry.ttl,
                'age': entry.age,
                'time_since_access': entry.time_since_access,
                'is_expired': entry.is_expired,
                'priority': entry.priority.name,
                'size_bytes': entry.size_bytes,
                'tags': list(entry.tags)
            }

# Cache global para uso em toda a aplicação
_global_cache: Optional[SmartCache] = None

def get_cache() -> SmartCache:
    """Obtém a instância global do cache"""
    global _global_cache
    if _global_cache is None:
        config = get_config()
        _global_cache = SmartCache(
            max_size=config.cache.memory_cache_size,
            default_ttl=config.cache.default_ttl,
            max_memory_mb=config.cache.max_memory_usage,
            cleanup_interval=config.cache.cleanup_interval
        )
    return _global_cache

# Decorador para cache automático
def cached(ttl: Optional[float] = None, 
          key_prefix: str = "",
          tags: Optional[Set[str]] = None,
          priority: CachePriority = CachePriority.NORMAL):
    """Decorador para cache automático de funções"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Gerar chave baseada na função e argumentos
            func_name = f"{func.__module__}.{func.__qualname__}"
            cache_key = f"{key_prefix}{func_name}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Tentar obter do cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Executar função e armazenar resultado
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl=ttl, priority=priority, tags=tags)
            return result
        
        def sync_wrapper(*args, **kwargs):
            # Para funções síncronas, usar versão assíncrona em loop
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator