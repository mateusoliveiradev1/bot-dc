# -*- coding: utf-8 -*-
"""
Sistema de Cache Inteligente Aprimorado - Hawk Bot
Cache com TTL dinâmico, predição de acesso, compressão automática e otimizações avançadas
"""

import asyncio
import logging
import time
import weakref
import zlib
import json
from typing import Any, Dict, Optional, Set, Callable, Union, TypeVar, Generic, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger('HawkBot.SmartCacheEnhanced')

T = TypeVar('T')

class CacheStrategy(Enum):
    """Estratégias de cache disponíveis"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptativo baseado em padrões de uso
    PREDICTIVE = "predictive"  # Preditivo com machine learning básico
    HYBRID = "hybrid"  # Híbrido combinando múltiplas estratégias

class CachePriority(Enum):
    """Prioridades de cache"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    PERSISTENT = 5  # Nunca remove automaticamente

class CompressionType(Enum):
    """Tipos de compressão disponíveis"""
    NONE = "none"
    ZLIB = "zlib"
    AUTO = "auto"  # Decide automaticamente baseado no tamanho

@dataclass
class AccessPattern:
    """Padrão de acesso para análise preditiva"""
    timestamps: deque = field(default_factory=lambda: deque(maxlen=50))
    intervals: deque = field(default_factory=lambda: deque(maxlen=20))
    access_count: int = 0
    last_prediction: Optional[float] = None
    prediction_accuracy: float = 0.0
    
    def add_access(self, timestamp: float):
        """Adiciona um novo acesso ao padrão"""
        if self.timestamps:
            interval = timestamp - self.timestamps[-1]
            self.intervals.append(interval)
        
        self.timestamps.append(timestamp)
        self.access_count += 1
    
    def predict_next_access(self) -> Optional[float]:
        """Prediz o próximo acesso baseado no padrão"""
        if len(self.intervals) < 3:
            return None
        
        # Usar média ponderada dos intervalos recentes
        recent_intervals = list(self.intervals)[-10:]
        weights = [i + 1 for i in range(len(recent_intervals))]
        
        weighted_avg = sum(interval * weight for interval, weight in zip(recent_intervals, weights)) / sum(weights)
        
        # Adicionar variabilidade baseada no desvio padrão
        if len(recent_intervals) > 1:
            std_dev = statistics.stdev(recent_intervals)
            # Ajustar predição com base na variabilidade
            weighted_avg += std_dev * 0.1
        
        self.last_prediction = time.time() + weighted_avg
        return self.last_prediction
    
    def update_prediction_accuracy(self, actual_access_time: float):
        """Atualiza a precisão da predição"""
        if self.last_prediction is None:
            return
        
        error = abs(actual_access_time - self.last_prediction)
        # Calcular precisão como 1 - erro_normalizado
        max_error = 3600  # 1 hora como erro máximo
        accuracy = max(0, 1 - (error / max_error))
        
        # Média móvel da precisão
        self.prediction_accuracy = (self.prediction_accuracy * 0.8) + (accuracy * 0.2)

@dataclass
class EnhancedCacheEntry(Generic[T]):
    """Entrada do cache aprimorada com metadados avançados"""
    value: T
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    priority: CachePriority = CachePriority.NORMAL
    size_bytes: int = 0
    compressed_size: int = 0
    tags: Set[str] = field(default_factory=set)
    compression_type: CompressionType = CompressionType.NONE
    access_pattern: AccessPattern = field(default_factory=AccessPattern)
    heat_score: float = 0.0  # Score de "calor" baseado em acessos recentes
    predicted_next_access: Optional[float] = None
    
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
    
    @property
    def compression_ratio(self) -> float:
        """Taxa de compressão"""
        if self.size_bytes == 0:
            return 1.0
        return self.compressed_size / self.size_bytes
    
    def access(self):
        """Registra um acesso à entrada"""
        now = time.time()
        self.last_accessed = now
        self.access_count += 1
        
        # Atualizar padrão de acesso
        self.access_pattern.add_access(now)
        
        # Atualizar score de calor (decai com o tempo)
        time_factor = max(0.1, 1.0 - (self.time_since_access / 3600))  # Decai em 1 hora
        self.heat_score = (self.heat_score * 0.9) + (time_factor * 0.1)
        
        # Atualizar predição
        self.predicted_next_access = self.access_pattern.predict_next_access()
    
    def calculate_eviction_score(self) -> float:
        """Calcula score para decisão de eviction (maior = mais provável de ser removido)"""
        # Fatores: idade, frequência, prioridade, calor, predição
        age_factor = min(self.age / 3600, 10)  # Normalizar por hora, máximo 10
        freq_factor = 1.0 / (self.access_count + 1)
        priority_factor = (6 - self.priority.value) / 5  # Inverter prioridade
        heat_factor = 1.0 - self.heat_score
        
        # Fator de predição: se prevemos acesso em breve, reduzir score
        prediction_factor = 1.0
        if self.predicted_next_access:
            time_to_next = self.predicted_next_access - time.time()
            if time_to_next > 0 and time_to_next < 3600:  # Próxima hora
                prediction_factor = time_to_next / 3600
        
        # Combinar fatores com pesos
        score = (age_factor * 0.25 + freq_factor * 0.25 + priority_factor * 0.2 + 
                heat_factor * 0.2 + prediction_factor * 0.1)
        
        return score

class EnhancedCacheStats:
    """Estatísticas avançadas do cache"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expired_removals = 0
        self.memory_cleanups = 0
        self.compressions = 0
        self.decompressions = 0
        self.prediction_hits = 0
        self.prediction_misses = 0
        self.total_size_bytes = 0
        self.compressed_size_bytes = 0
        self.peak_size_bytes = 0
        self.start_time = time.time()
        
        # Métricas por período
        self.hourly_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self.daily_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acertos do cache"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def compression_ratio(self) -> float:
        """Taxa de compressão geral"""
        if self.total_size_bytes == 0:
            return 1.0
        return self.compressed_size_bytes / self.total_size_bytes
    
    @property
    def prediction_accuracy(self) -> float:
        """Precisão das predições"""
        total = self.prediction_hits + self.prediction_misses
        return self.prediction_hits / total if total > 0 else 0.0
    
    @property
    def uptime(self) -> float:
        """Tempo de funcionamento em segundos"""
        return time.time() - self.start_time
    
    def record_access(self, hit: bool):
        """Registra um acesso para estatísticas por período"""
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d-%H')
        day_key = now.strftime('%Y-%m-%d')
        
        if hit:
            self.hits += 1
            self.hourly_stats[hour_key]['hits'] += 1
            self.daily_stats[day_key]['hits'] += 1
        else:
            self.misses += 1
            self.hourly_stats[hour_key]['misses'] += 1
            self.daily_stats[day_key]['misses'] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte estatísticas para dicionário"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate,
            'evictions': self.evictions,
            'expired_removals': self.expired_removals,
            'memory_cleanups': self.memory_cleanups,
            'compressions': self.compressions,
            'decompressions': self.decompressions,
            'prediction_hits': self.prediction_hits,
            'prediction_misses': self.prediction_misses,
            'prediction_accuracy': self.prediction_accuracy,
            'total_size_bytes': self.total_size_bytes,
            'compressed_size_bytes': self.compressed_size_bytes,
            'compression_ratio': self.compression_ratio,
            'peak_size_bytes': self.peak_size_bytes,
            'uptime_seconds': self.uptime
        }

class SmartCacheEnhanced:
    """Cache inteligente aprimorado com recursos avançados"""
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: float = 3600,
                 strategy: CacheStrategy = CacheStrategy.HYBRID,
                 max_memory_mb: int = 100,
                 cleanup_interval: float = 300,
                 enable_compression: bool = True,
                 compression_threshold: int = 1024,
                 enable_prediction: bool = True):
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.enable_prediction = enable_prediction
        
        # Storage principal
        self._cache: Dict[str, EnhancedCacheEntry] = {}
        self._lock = asyncio.Lock()
        
        # Índices para otimização
        self._access_order: Dict[str, float] = {}  # Para LRU
        self._frequency: Dict[str, int] = defaultdict(int)  # Para LFU
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Índice por tags
        self._heat_index: Dict[str, float] = {}  # Índice de calor
        
        # Estatísticas e monitoramento
        self.stats = EnhancedCacheStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._prediction_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="SmartCacheEnhanced")
        
        # Configurações adaptativas
        self._adaptive_ttls: Dict[str, float] = {}
        self._global_access_pattern = AccessPattern()
        
        logger.info(f"SmartCacheEnhanced inicializado: max_size={max_size}, strategy={strategy.value}")
    
    async def initialize(self):
        """Inicializa o cache aprimorado"""
        # Iniciar tarefas de background
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        if self.enable_prediction:
            self._prediction_task = asyncio.create_task(self._prediction_loop())
        
        logger.info("SmartCacheEnhanced inicializado com sucesso")
    
    async def cleanup(self):
        """Limpa recursos do cache"""
        tasks_to_cancel = [self._cleanup_task, self._prediction_task]
        
        for task in tasks_to_cancel:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._executor.shutdown(wait=True)
        await self.clear()
        
        logger.info("SmartCacheEnhanced finalizado")
    
    def _compress_value(self, value: Any) -> Tuple[Any, CompressionType, int, int]:
        """Comprime um valor se necessário"""
        if not self.enable_compression:
            size = self._calculate_size(value)
            return value, CompressionType.NONE, size, size
        
        # Serializar valor
        try:
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            original_size = len(serialized)
            
            # Decidir se comprimir
            if original_size < self.compression_threshold:
                return value, CompressionType.NONE, original_size, original_size
            
            # Comprimir
            compressed = zlib.compress(serialized, level=6)
            compressed_size = len(compressed)
            
            # Só usar compressão se houver ganho significativo
            if compressed_size < original_size * 0.9:  # Pelo menos 10% de redução
                self.stats.compressions += 1
                return compressed, CompressionType.ZLIB, original_size, compressed_size
            else:
                return value, CompressionType.NONE, original_size, original_size
                
        except Exception as e:
            logger.warning(f"Erro na compressão: {e}")
            size = self._calculate_size(value)
            return value, CompressionType.NONE, size, size
    
    def _decompress_value(self, compressed_value: Any, compression_type: CompressionType) -> Any:
        """Descomprime um valor"""
        if compression_type == CompressionType.NONE:
            return compressed_value
        
        try:
            if compression_type == CompressionType.ZLIB:
                decompressed = zlib.decompress(compressed_value)
                value = pickle.loads(decompressed)
                self.stats.decompressions += 1
                return value
        except Exception as e:
            logger.error(f"Erro na descompressão: {e}")
            raise
        
        return compressed_value
    
    def _calculate_size(self, value: Any) -> int:
        """Calcula o tamanho aproximado de um valor"""
        try:
            return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            return sys.getsizeof(value)
    
    def _generate_key(self, key: Union[str, tuple]) -> str:
        """Gera uma chave de cache consistente"""
        if isinstance(key, str):
            return key
        
        key_str = str(key)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _calculate_adaptive_ttl(self, key: str) -> float:
        """Calcula TTL adaptativo baseado em padrões de acesso"""
        if key in self._cache:
            entry = self._cache[key]
            pattern = entry.access_pattern
            
            if len(pattern.intervals) >= 3:
                # Usar padrão específico da entrada
                recent_intervals = list(pattern.intervals)[-5:]
                avg_interval = statistics.mean(recent_intervals)
                
                # TTL = 1.5x o intervalo médio, com limites
                adaptive_ttl = min(max(avg_interval * 1.5, 300), self.default_ttl * 3)
                
                # Ajustar baseado na precisão das predições
                if pattern.prediction_accuracy > 0.7:
                    adaptive_ttl *= 1.2  # Aumentar TTL se predições são boas
                
                self._adaptive_ttls[key] = adaptive_ttl
                return adaptive_ttl
        
        # Usar padrão global se não houver dados específicos
        if len(self._global_access_pattern.intervals) >= 3:
            global_avg = statistics.mean(list(self._global_access_pattern.intervals)[-10:])
            return min(max(global_avg * 2, 600), self.default_ttl * 2)
        
        return self.default_ttl
    
    async def get(self, key: Union[str, tuple], default: Any = None) -> Any:
        """Obtém um valor do cache"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key not in self._cache:
                self.stats.record_access(False)
                return default
            
            entry = self._cache[cache_key]
            
            # Verificar expiração
            if entry.is_expired:
                await self._remove_entry(cache_key)
                self.stats.record_access(False)
                self.stats.expired_removals += 1
                return default
            
            # Registrar acesso
            entry.access()
            self._access_order[cache_key] = time.time()
            self._frequency[cache_key] += 1
            self._heat_index[cache_key] = entry.heat_score
            
            # Atualizar padrão global
            self._global_access_pattern.add_access(time.time())
            
            self.stats.record_access(True)
            
            # Descomprimir se necessário
            return self._decompress_value(entry.value, entry.compression_type)
    
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
            if self.strategy in [CacheStrategy.ADAPTIVE, CacheStrategy.HYBRID]:
                ttl = self._calculate_adaptive_ttl(cache_key)
            else:
                ttl = self.default_ttl
        
        # Comprimir valor
        compressed_value, compression_type, original_size, compressed_size = self._compress_value(value)
        
        async with self._lock:
            # Verificar limites de memória
            if self.stats.compressed_size_bytes + compressed_size > self.max_memory_bytes:
                await self._cleanup_memory()
                
                if self.stats.compressed_size_bytes + compressed_size > self.max_memory_bytes:
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
            entry = EnhancedCacheEntry(
                value=compressed_value,
                created_at=now,
                last_accessed=now,
                ttl=ttl,
                priority=priority,
                size_bytes=original_size,
                compressed_size=compressed_size,
                tags=tags or set(),
                compression_type=compression_type
            )
            
            # Armazenar
            self._cache[cache_key] = entry
            self._access_order[cache_key] = now
            self._frequency[cache_key] = 1
            self._heat_index[cache_key] = 0.0
            
            # Atualizar índices de tags
            for tag in entry.tags:
                self._tags_index[tag].add(cache_key)
            
            # Atualizar estatísticas
            self.stats.total_size_bytes += original_size
            self.stats.compressed_size_bytes += compressed_size
            
            if self.stats.total_size_bytes > self.stats.peak_size_bytes:
                self.stats.peak_size_bytes = self.stats.total_size_bytes
            
            return True
    
    async def _evict_entries(self, count: int):
        """Remove entradas baseado na estratégia aprimorada"""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.HYBRID:
            # Estratégia híbrida: usar scores de eviction
            scored_entries = []
            for key, entry in self._cache.items():
                if entry.priority == CachePriority.PERSISTENT:
                    continue  # Nunca remover entradas persistentes
                
                score = entry.calculate_eviction_score()
                scored_entries.append((key, score))
            
            # Ordenar por score (maior primeiro)
            scored_entries.sort(key=lambda x: x[1], reverse=True)
            keys_to_remove = [key for key, _ in scored_entries[:count]]
        
        else:
            # Usar estratégias tradicionais
            keys_to_remove = await self._traditional_eviction(count)
        
        # Remover as entradas selecionadas
        for key in keys_to_remove:
            await self._remove_entry(key)
            self.stats.evictions += 1
    
    async def _traditional_eviction(self, count: int) -> List[str]:
        """Eviction usando estratégias tradicionais"""
        keys_to_remove = []
        
        if self.strategy == CacheStrategy.LRU:
            sorted_keys = sorted(self._access_order.items(), key=lambda x: x[1])
            keys_to_remove = [key for key, _ in sorted_keys[:count]]
        
        elif self.strategy == CacheStrategy.LFU:
            sorted_keys = sorted(self._frequency.items(), key=lambda x: x[1])
            keys_to_remove = [key for key, _ in sorted_keys[:count]]
        
        elif self.strategy == CacheStrategy.TTL:
            entries_with_keys = [(key, entry) for key, entry in self._cache.items()]
            sorted_entries = sorted(entries_with_keys, key=lambda x: x[1].created_at)
            keys_to_remove = [key for key, _ in sorted_entries[:count]]
        
        return keys_to_remove
    
    async def _remove_entry(self, cache_key: str):
        """Remove uma entrada específica"""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        
        # Atualizar estatísticas
        self.stats.total_size_bytes -= entry.size_bytes
        self.stats.compressed_size_bytes -= entry.compressed_size
        
        # Remover dos índices
        self._cache.pop(cache_key, None)
        self._access_order.pop(cache_key, None)
        self._frequency.pop(cache_key, None)
        self._heat_index.pop(cache_key, None)
        
        # Remover das tags
        for tag in entry.tags:
            if tag in self._tags_index:
                self._tags_index[tag].discard(cache_key)
                if not self._tags_index[tag]:
                    del self._tags_index[tag]
    
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
        
        # Se ainda precisar de espaço, usar eviction
        if self.stats.compressed_size_bytes > self.max_memory_bytes * 0.8:
            entries_to_remove = max(1, len(self._cache) // 10)
            await self._evict_entries(entries_to_remove)
            self.stats.memory_cleanups += 1
    
    async def _cleanup_loop(self):
        """Loop de limpeza automática aprimorado"""
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
                    if self.stats.compressed_size_bytes > self.max_memory_bytes * 0.9:
                        await self._cleanup_memory()
                    
                    # Atualizar scores de calor
                    for key, entry in self._cache.items():
                        # Decair score de calor com o tempo
                        decay_factor = 0.95  # 5% de decay por ciclo
                        entry.heat_score *= decay_factor
                        self._heat_index[key] = entry.heat_score
                
                if expired_keys:
                    logger.debug(f"Limpeza automática: {len(expired_keys)} entradas expiradas removidas")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro na limpeza automática do cache: {e}")
    
    async def _prediction_loop(self):
        """Loop de predição de acessos"""
        while True:
            try:
                await asyncio.sleep(60)  # Executar a cada minuto
                
                async with self._lock:
                    current_time = time.time()
                    
                    for key, entry in self._cache.items():
                        # Atualizar predição de próximo acesso
                        predicted = entry.access_pattern.predict_next_access()
                        if predicted:
                            entry.predicted_next_access = predicted
                            
                            # Se predição indica acesso em breve, aumentar TTL
                            if predicted - current_time < entry.ttl * 0.1:  # 10% do TTL restante
                                if entry.ttl and entry.ttl < self.default_ttl * 2:
                                    entry.ttl *= 1.2  # Aumentar TTL em 20%
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de predição: {e}")
    
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
                self._heat_index.clear()
                self._adaptive_ttls.clear()
                self.stats.total_size_bytes = 0
                self.stats.compressed_size_bytes = 0
            else:
                # Limpar por tags
                keys_to_remove = set()
                for tag in tags:
                    if tag in self._tags_index:
                        keys_to_remove.update(self._tags_index[tag])
                
                for cache_key in keys_to_remove:
                    await self._remove_entry(cache_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas avançadas do cache"""
        stats = self.stats.to_dict()
        stats.update({
            'current_entries': len(self._cache),
            'max_size': self.max_size,
            'strategy': self.strategy.value,
            'memory_usage_mb': self.stats.total_size_bytes / (1024 * 1024),
            'compressed_memory_mb': self.stats.compressed_size_bytes / (1024 * 1024),
            'memory_limit_mb': self.max_memory_bytes / (1024 * 1024),
            'compression_enabled': self.enable_compression,
            'prediction_enabled': self.enable_prediction,
            'avg_heat_score': statistics.mean(self._heat_index.values()) if self._heat_index else 0.0
        })
        return stats
    
    async def get_top_entries(self, limit: int = 10, sort_by: str = 'heat') -> List[Dict[str, Any]]:
        """Obtém as top entradas do cache"""
        async with self._lock:
            entries_info = []
            
            for key, entry in self._cache.items():
                info = {
                    'key': key,
                    'heat_score': entry.heat_score,
                    'access_count': entry.access_count,
                    'age': entry.age,
                    'size_bytes': entry.size_bytes,
                    'compressed_size': entry.compressed_size,
                    'compression_ratio': entry.compression_ratio,
                    'priority': entry.priority.name,
                    'predicted_next_access': entry.predicted_next_access
                }
                entries_info.append(info)
            
            # Ordenar baseado no critério
            if sort_by == 'heat':
                entries_info.sort(key=lambda x: x['heat_score'], reverse=True)
            elif sort_by == 'access_count':
                entries_info.sort(key=lambda x: x['access_count'], reverse=True)
            elif sort_by == 'size':
                entries_info.sort(key=lambda x: x['size_bytes'], reverse=True)
            
            return entries_info[:limit]

# Cache global aprimorado
_global_enhanced_cache: Optional[SmartCacheEnhanced] = None

def get_enhanced_cache() -> SmartCacheEnhanced:
    """Obtém a instância global do cache aprimorado"""
    global _global_enhanced_cache
    if _global_enhanced_cache is None:
        _global_enhanced_cache = SmartCacheEnhanced(
            max_size=2000,
            default_ttl=3600,
            strategy=CacheStrategy.HYBRID,
            max_memory_mb=200,
            cleanup_interval=300,
            enable_compression=True,
            compression_threshold=1024,
            enable_prediction=True
        )
    return _global_enhanced_cache

# Decorador aprimorado para cache automático
def enhanced_cached(ttl: Optional[float] = None, 
                   key_prefix: str = "",
                   tags: Optional[Set[str]] = None,
                   priority: CachePriority = CachePriority.NORMAL,
                   enable_compression: bool = True):
    """Decorador aprimorado para cache automático de funções"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            cache = get_enhanced_cache()
            
            # Gerar chave baseada na função e argumentos
            func_name = f"{func.__module__}.{func.__qualname__}"
            args_hash = hash((args, tuple(sorted(kwargs.items()))))
            cache_key = f"{key_prefix}{func_name}:{args_hash}"
            
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
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator