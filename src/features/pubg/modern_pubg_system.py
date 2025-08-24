#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema PUBG Modernizado - Hawk Bot
Sistema completo e moderno para integração PUBG com async/await
Integra com todos os sistemas core modernos

Autor: Hawk Bot Development Team
Versão: 3.0.0 - Modernizado
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from collections import defaultdict, deque

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object

# Importar sistemas core modernos
try:
    from ...core.smart_cache import SmartCache, CacheStrategy
    from ...core.secure_logger import SecureLogger
    from ...core.typed_config import TypedConfig
    from ...core.metrics import MetricsCollector, increment_counter, record_gauge, record_timer
    from ...core.data_validator import DataValidator, validate_input
    from ...core.event_system import EventSystem, emit_event
    from ...core.rate_limiter import RateLimiter, rate_limit
except ImportError:
    # Fallback para compatibilidade
    SmartCache = None
    SecureLogger = None
    TypedConfig = None
    MetricsCollector = None
    DataValidator = None
    EventSystem = None
    RateLimiter = None

logger = logging.getLogger('HawkBot.ModernPUBG')

# ==================== ENUMS E CONSTANTES ====================

class PUBGShard(Enum):
    """Shards disponíveis na API PUBG"""
    STEAM = "steam"
    PSN = "psn"
    XBOX = "xbox"
    KAKAO = "kakao"
    STADIA = "stadia"

class GameMode(Enum):
    """Modos de jogo PUBG"""
    SOLO = "solo"
    SOLO_FPP = "solo-fpp"
    DUO = "duo"
    DUO_FPP = "duo-fpp"
    SQUAD = "squad"
    SQUAD_FPP = "squad-fpp"

class RankTier(Enum):
    """Tiers de ranking PUBG"""
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    DIAMOND = "Diamond"
    MASTER = "Master"
    GRANDMASTER = "Grandmaster"
    PREDATOR = "Predator"

class APIStatus(Enum):
    """Status da API PUBG"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RATE_LIMITED = "rate_limited"

# ==================== MODELOS DE DADOS ====================

if PYDANTIC_AVAILABLE:
    class PUBGPlayerModel(BaseModel):
        """Modelo de dados do jogador PUBG"""
        id: str = Field(..., description="ID único do jogador")
        name: str = Field(..., min_length=1, max_length=50, description="Nome do jogador")
        shard: PUBGShard = Field(..., description="Shard do jogador")
        created_at: Optional[datetime] = Field(None, description="Data de criação")
        
        @validator('name')
        def validate_name(cls, v):
            if not v or len(v.strip()) == 0:
                raise ValueError('Nome do jogador não pode estar vazio')
            return v.strip()
    
    class PUBGStatsModel(BaseModel):
        """Modelo de estatísticas PUBG"""
        player_id: str = Field(..., description="ID do jogador")
        season_id: str = Field(..., description="ID da temporada")
        game_mode: GameMode = Field(..., description="Modo de jogo")
        
        # Estatísticas básicas
        matches_played: int = Field(0, ge=0, description="Partidas jogadas")
        wins: int = Field(0, ge=0, description="Vitórias")
        kills: int = Field(0, ge=0, description="Eliminações")
        deaths: int = Field(0, ge=0, description="Mortes")
        assists: int = Field(0, ge=0, description="Assistências")
        
        # Estatísticas calculadas
        kd_ratio: float = Field(0.0, ge=0.0, description="Razão K/D")
        win_rate: float = Field(0.0, ge=0.0, le=100.0, description="Taxa de vitória")
        avg_damage: float = Field(0.0, ge=0.0, description="Dano médio")
        
        # Ranking
        current_tier: Optional[RankTier] = Field(None, description="Tier atual")
        current_rank_points: int = Field(0, ge=0, description="Pontos de rank")
        
        # Metadados
        last_updated: datetime = Field(default_factory=datetime.now, description="Última atualização")
        data_quality: str = Field("good", description="Qualidade dos dados")
        
        @validator('kd_ratio', pre=True)
        def calculate_kd(cls, v, values):
            if 'deaths' in values and values['deaths'] > 0:
                return round(values.get('kills', 0) / values['deaths'], 2)
            return values.get('kills', 0)
        
        @validator('win_rate', pre=True)
        def calculate_win_rate(cls, v, values):
            if 'matches_played' in values and values['matches_played'] > 0:
                return round((values.get('wins', 0) / values['matches_played']) * 100, 2)
            return 0.0
    
    class PUBGSeasonModel(BaseModel):
        """Modelo de temporada PUBG"""
        id: str = Field(..., description="ID da temporada")
        is_current: bool = Field(False, description="Se é a temporada atual")
        is_off_season: bool = Field(False, description="Se é off-season")
else:
    # Fallback classes sem Pydantic
    @dataclass
    class PUBGPlayerModel:
        id: str
        name: str
        shard: str
        created_at: Optional[datetime] = None
    
    @dataclass
    class PUBGStatsModel:
        player_id: str
        season_id: str
        game_mode: str
        matches_played: int = 0
        wins: int = 0
        kills: int = 0
        deaths: int = 0
        assists: int = 0
        kd_ratio: float = 0.0
        win_rate: float = 0.0
        avg_damage: float = 0.0
        current_tier: Optional[str] = None
        current_rank_points: int = 0
        last_updated: datetime = field(default_factory=datetime.now)
        data_quality: str = "good"
    
    @dataclass
    class PUBGSeasonModel:
        id: str
        is_current: bool = False
        is_off_season: bool = False

# ==================== SISTEMA PUBG MODERNIZADO ====================

class ModernPUBGSystem:
    """Sistema PUBG modernizado com async/await e integração completa"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get('pubg_api_key') or os.getenv('PUBG_API_KEY')
        self.base_url = "https://api.pubg.com"
        
        # Inicializar sistemas core
        self._init_core_systems()
        
        # Configurações da API
        self.rate_limits = {
            'requests_per_minute': 10,
            'burst_limit': 3,
            'cooldown_seconds': 60
        }
        
        # Status da API
        self.api_status = APIStatus.HEALTHY
        self.last_health_check = datetime.now()
        
        # Métricas internas
        self.metrics = {
            'requests_made': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'rate_limits_hit': 0
        }
        
        # Sessão HTTP reutilizável
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("PUBG API key não configurada. Funcionalidades limitadas.")
        else:
            logger.info("Sistema PUBG modernizado inicializado com sucesso")
    
    def _init_core_systems(self):
        """Inicializa os sistemas core modernos"""
        try:
            # Cache inteligente
            if SmartCache:
                self.cache = SmartCache(
                    default_ttl=900,  # 15 minutos
                    max_size=1000,
                    strategy=CacheStrategy.LRU
                )
            else:
                self.cache = {}
            
            # Logger seguro
            if SecureLogger:
                self.secure_logger = SecureLogger('ModernPUBG')
            else:
                self.secure_logger = logger
            
            # Rate limiter
            if RateLimiter:
                self.rate_limiter = RateLimiter(
                    max_requests=self.rate_limits['requests_per_minute'],
                    time_window=60,
                    burst_limit=self.rate_limits['burst_limit']
                )
            else:
                self.rate_limiter = None
            
            # Validador de dados
            if DataValidator:
                self.validator = DataValidator()
            else:
                self.validator = None
            
            # Sistema de eventos
            if EventSystem:
                self.event_system = EventSystem()
            else:
                self.event_system = None
                
        except Exception as e:
            logger.warning(f"Erro ao inicializar sistemas core: {e}")
            # Usar fallbacks
            self.cache = {}
            self.secure_logger = logger
            self.rate_limiter = None
            self.validator = None
            self.event_system = None
    
    async def __aenter__(self):
        """Context manager para sessão HTTP"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup da sessão HTTP"""
        await self.close()
    
    async def _ensure_session(self):
        """Garante que a sessão HTTP está ativa"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Accept': 'application/vnd.api+json',
                    'User-Agent': 'HawkBot-ModernPUBG/3.0.0'
                }
            )
    
    async def close(self):
        """Fecha a sessão HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _generate_cache_key(self, *args) -> str:
        """Gera chave única para cache"""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @rate_limit(max_calls=10, time_window=60)
    async def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Faz requisição à API PUBG com rate limiting e retry"""
        if not self.api_key:
            logger.error("API key não configurada")
            return None
        
        await self._ensure_session()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Aplicar rate limiting manual se necessário
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        try:
            # Registrar métrica
            if MetricsCollector:
                increment_counter('pubg_api_requests_total')
            
            self.metrics['requests_made'] += 1
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Emitir evento de sucesso
                    if self.event_system:
                        await emit_event('pubg_api_success', {
                            'endpoint': endpoint,
                            'status': response.status
                        })
                    
                    return data
                
                elif response.status == 429:
                    # Rate limit hit
                    self.metrics['rate_limits_hit'] += 1
                    self.api_status = APIStatus.RATE_LIMITED
                    
                    if MetricsCollector:
                        increment_counter('pubg_api_rate_limits_total')
                    
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit atingido. Aguardando {retry_after}s")
                    
                    await asyncio.sleep(retry_after)
                    return None
                
                elif response.status == 404:
                    logger.warning(f"Recurso não encontrado: {endpoint}")
                    return None
                
                else:
                    self.metrics['errors'] += 1
                    error_text = await response.text()
                    logger.error(f"Erro na API PUBG: {response.status} - {error_text}")
                    
                    if MetricsCollector:
                        increment_counter('pubg_api_errors_total', labels={'status': str(response.status)})
                    
                    return None
        
        except asyncio.TimeoutError:
            self.metrics['errors'] += 1
            logger.error(f"Timeout na requisição para {endpoint}")
            return None
        
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Erro na requisição: {e}")
            
            # Emitir evento de erro
            if self.event_system:
                await emit_event('pubg_api_error', {
                    'endpoint': endpoint,
                    'error': str(e)
                })
            
            return None
    
    async def get_player_by_name(self, player_name: str, shard: Union[str, PUBGShard] = PUBGShard.STEAM) -> Optional[PUBGPlayerModel]:
        """Busca jogador por nome"""
        if isinstance(shard, str):
            try:
                shard = PUBGShard(shard.lower())
            except ValueError:
                logger.error(f"Shard inválido: {shard}")
                return None
        
        # Verificar cache
        cache_key = self._generate_cache_key("player", player_name, shard.value)
        
        if SmartCache and hasattr(self.cache, 'get'):
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                self.metrics['cache_hits'] += 1
                return PUBGPlayerModel(**cached_data) if PYDANTIC_AVAILABLE else cached_data
        
        self.metrics['cache_misses'] += 1
        
        # Buscar na API
        endpoint = f"shards/{shard.value}/players"
        params = {'filter[playerNames]': player_name}
        
        data = await self._make_api_request(endpoint, params)
        if not data or 'data' not in data or not data['data']:
            return None
        
        player_data = data['data'][0]
        player_info = {
            'id': player_data['id'],
            'name': player_data['attributes']['name'],
            'shard': shard.value,
            'created_at': datetime.fromisoformat(player_data['attributes']['createdAt'].replace('Z', '+00:00'))
        }
        
        # Salvar no cache
        if SmartCache and hasattr(self.cache, 'set'):
            await self.cache.set(cache_key, player_info, ttl=1800)  # 30 minutos
        
        return PUBGPlayerModel(**player_info) if PYDANTIC_AVAILABLE else player_info
    
    async def get_player_stats(self, player_id: str, season_id: str, shard: Union[str, PUBGShard] = PUBGShard.STEAM) -> Optional[Dict[str, PUBGStatsModel]]:
        """Busca estatísticas do jogador por temporada"""
        if isinstance(shard, str):
            try:
                shard = PUBGShard(shard.lower())
            except ValueError:
                logger.error(f"Shard inválido: {shard}")
                return None
        
        # Verificar cache
        cache_key = self._generate_cache_key("stats", player_id, season_id, shard.value)
        
        if SmartCache and hasattr(self.cache, 'get'):
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                self.metrics['cache_hits'] += 1
                return cached_data
        
        self.metrics['cache_misses'] += 1
        
        # Buscar na API
        endpoint = f"shards/{shard.value}/players/{player_id}/seasons/{season_id}"
        
        with record_timer('pubg_api_request_duration') if MetricsCollector else nullcontext():
            data = await self._make_api_request(endpoint)
        
        if not data or 'data' not in data:
            return None
        
        # Processar estatísticas por modo de jogo
        stats_data = data['data']['attributes']['gameModeStats']
        processed_stats = {}
        
        for mode, stats in stats_data.items():
            try:
                game_mode = GameMode(mode)
            except ValueError:
                continue  # Modo não suportado
            
            # Calcular estatísticas derivadas
            matches = stats.get('roundsPlayed', 0)
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            wins = stats.get('wins', 0)
            
            kd_ratio = round(kills / deaths, 2) if deaths > 0 else kills
            win_rate = round((wins / matches) * 100, 2) if matches > 0 else 0.0
            
            stat_model_data = {
                'player_id': player_id,
                'season_id': season_id,
                'game_mode': game_mode.value,
                'matches_played': matches,
                'wins': wins,
                'kills': kills,
                'deaths': deaths,
                'assists': stats.get('assists', 0),
                'kd_ratio': kd_ratio,
                'win_rate': win_rate,
                'avg_damage': round(stats.get('damageDealt', 0) / matches, 2) if matches > 0 else 0.0,
                'current_rank_points': stats.get('rankPoints', 0),
                'last_updated': datetime.now(),
                'data_quality': 'good' if matches >= 10 else 'limited'
            }
            
            if PYDANTIC_AVAILABLE:
                processed_stats[mode] = PUBGStatsModel(**stat_model_data)
            else:
                processed_stats[mode] = stat_model_data
        
        # Salvar no cache
        if SmartCache and hasattr(self.cache, 'set'):
            await self.cache.set(cache_key, processed_stats, ttl=900)  # 15 minutos
        
        return processed_stats
    
    async def get_current_season(self, shard: Union[str, PUBGShard] = PUBGShard.STEAM) -> Optional[PUBGSeasonModel]:
        """Busca a temporada atual"""
        if isinstance(shard, str):
            try:
                shard = PUBGShard(shard.lower())
            except ValueError:
                logger.error(f"Shard inválido: {shard}")
                return None
        
        # Verificar cache
        cache_key = self._generate_cache_key("current_season", shard.value)
        
        if SmartCache and hasattr(self.cache, 'get'):
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                self.metrics['cache_hits'] += 1
                return PUBGSeasonModel(**cached_data) if PYDANTIC_AVAILABLE else cached_data
        
        self.metrics['cache_misses'] += 1
        
        # Buscar na API
        endpoint = f"shards/{shard.value}/seasons"
        data = await self._make_api_request(endpoint)
        
        if not data or 'data' not in data:
            return None
        
        # Encontrar temporada atual
        current_season = None
        for season in data['data']:
            if season['attributes']['isCurrentSeason']:
                current_season = {
                    'id': season['id'],
                    'is_current': True,
                    'is_off_season': season['attributes']['isOffseason']
                }
                break
        
        if not current_season:
            return None
        
        # Salvar no cache por mais tempo (temporadas mudam raramente)
        if SmartCache and hasattr(self.cache, 'set'):
            await self.cache.set(cache_key, current_season, ttl=3600)  # 1 hora
        
        return PUBGSeasonModel(**current_season) if PYDANTIC_AVAILABLE else current_season
    
    async def get_player_complete_profile(self, player_name: str, shard: Union[str, PUBGShard] = PUBGShard.STEAM) -> Optional[Dict[str, Any]]:
        """Busca perfil completo do jogador (dados + estatísticas)"""
        try:
            # Buscar dados do jogador
            player = await self.get_player_by_name(player_name, shard)
            if not player:
                return None
            
            # Buscar temporada atual
            current_season = await self.get_current_season(shard)
            if not current_season:
                logger.warning(f"Não foi possível obter temporada atual para {shard}")
                return None
            
            # Buscar estatísticas
            player_id = player.id if hasattr(player, 'id') else player['id']
            season_id = current_season.id if hasattr(current_season, 'id') else current_season['id']
            
            stats = await self.get_player_stats(player_id, season_id, shard)
            
            # Compilar perfil completo
            profile = {
                'player': player.dict() if hasattr(player, 'dict') else player,
                'season': current_season.dict() if hasattr(current_season, 'dict') else current_season,
                'stats': {}
            }
            
            if stats:
                for mode, stat_data in stats.items():
                    profile['stats'][mode] = stat_data.dict() if hasattr(stat_data, 'dict') else stat_data
            
            # Emitir evento de perfil completo
            if self.event_system:
                await emit_event('pubg_profile_loaded', {
                    'player_name': player_name,
                    'shard': shard.value if hasattr(shard, 'value') else shard,
                    'stats_count': len(profile['stats'])
                })
            
            return profile
            
        except Exception as e:
            logger.error(f"Erro ao buscar perfil completo de {player_name}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde da API PUBG"""
        try:
            # Fazer uma requisição simples para testar
            endpoint = "shards/steam/seasons"
            start_time = datetime.now()
            
            data = await self._make_api_request(endpoint)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if data:
                self.api_status = APIStatus.HEALTHY
                status = {
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'last_check': datetime.now().isoformat(),
                    'metrics': self.metrics.copy()
                }
            else:
                self.api_status = APIStatus.DEGRADED
                status = {
                    'status': 'degraded',
                    'response_time_ms': round(response_time * 1000, 2),
                    'last_check': datetime.now().isoformat(),
                    'metrics': self.metrics.copy()
                }
            
            self.last_health_check = datetime.now()
            
            # Registrar métricas de saúde
            if MetricsCollector:
                record_gauge('pubg_api_response_time_ms', response_time * 1000)
                record_gauge('pubg_api_health_score', 1.0 if data else 0.5)
            
            return status
            
        except Exception as e:
            self.api_status = APIStatus.DOWN
            logger.error(f"Health check falhou: {e}")
            
            return {
                'status': 'down',
                'error': str(e),
                'last_check': datetime.now().isoformat(),
                'metrics': self.metrics.copy()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do sistema PUBG"""
        return {
            'api_status': self.api_status.value,
            'last_health_check': self.last_health_check.isoformat(),
            'internal_metrics': self.metrics.copy(),
            'cache_info': {
                'size': len(self.cache) if isinstance(self.cache, dict) else 'unknown',
                'hit_rate': round(
                    (self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'])) * 100, 2
                ) if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0.0
            }
        }

# ==================== FUNÇÕES DE CONVENIÊNCIA ====================

# Instância global
_pubg_system: Optional[ModernPUBGSystem] = None

def get_pubg_system(config: Optional[Dict[str, Any]] = None) -> ModernPUBGSystem:
    """Retorna a instância global do sistema PUBG"""
    global _pubg_system
    if _pubg_system is None:
        _pubg_system = ModernPUBGSystem(config)
    return _pubg_system

async def get_player_stats_quick(player_name: str, shard: str = "steam") -> Optional[Dict[str, Any]]:
    """Função rápida para buscar estatísticas de jogador"""
    pubg = get_pubg_system()
    async with pubg:
        return await pubg.get_player_complete_profile(player_name, shard)

async def check_pubg_api_health() -> Dict[str, Any]:
    """Função rápida para verificar saúde da API"""
    pubg = get_pubg_system()
    async with pubg:
        return await pubg.health_check()

# ==================== CONTEXT MANAGER HELPER ====================

from contextlib import nullcontext

if __name__ == "__main__":
    # Exemplo de uso
    async def main():
        async with ModernPUBGSystem() as pubg:
            # Verificar saúde
            health = await pubg.health_check()
            print(f"API Status: {health['status']}")
            
            # Buscar jogador
            player = await pubg.get_player_by_name("exemplo_jogador")
            if player:
                print(f"Jogador encontrado: {player.name if hasattr(player, 'name') else player['name']}")
            
            # Métricas
            metrics = pubg.get_metrics()
            print(f"Métricas: {metrics}")
    
    # asyncio.run(main())
    pass