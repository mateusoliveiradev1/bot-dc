#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Integração PUBG API Otimizado
Responsável por buscar estatísticas e dados dos jogadores via API oficial
Com cache avançado, rate limiting e tratamento de erros robusto

Autor: Desenvolvedor Sênior
Versão: 2.0.0 - Otimizado para API gratuita
"""

import aiohttp
import asyncio
import logging
import os
import time
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from collections import defaultdict, deque

logger = logging.getLogger('HawkBot.PUBGAPI')

class PUBGIntegration:
    """Classe otimizada para integração com a API oficial do PUBG"""
    
    def __init__(self):
        self.api_key = os.getenv('API_PUBG_API_KEY')
        self.base_url = "https://api.pubg.com"
        
        # Sistema de cache avançado
        self.cache = {}  # Cache principal
        self.cache_stats = defaultdict(int)  # Estatísticas do cache
        self.cache_duration = {
            'player': 15 * 60,      # 15 minutos para dados de jogador
            'season': 60 * 60,      # 1 hora para temporadas
            'stats': 30 * 60,       # 30 minutos para estatísticas
            'matches': 2 * 60 * 60, # 2 horas para partidas (não mudam)
        }
        
        # Sistema de rate limiting (API gratuita: 10 req/min)
        self.rate_limit = {
            'max_requests': 8,      # Margem de segurança
            'time_window': 60,      # 1 minuto
            'requests': deque(),    # Histórico de requisições
            'blocked_until': 0      # Timestamp até quando está bloqueado
        }
        
        # Mapeamento de shards válidos
        self.valid_shards = {
            'steam': 'steam',
            'psn': 'psn', 
            'xbox': 'xbox',
            'kakao': 'kakao'
        }
        
        # Mapeamento de modos de jogo
        self.game_modes = {
            'solo': ['solo', 'solo-fpp'],
            'duo': ['duo', 'duo-fpp'],
            'squad': ['squad', 'squad-fpp']
        }
        
        # Configurações de retry
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1,        # Delay base em segundos
            'max_delay': 30,        # Delay máximo
            'backoff_factor': 2     # Fator de backoff exponencial
        }
        
        if not self.api_key:
            logger.error("API_PUBG_API_KEY não encontrada nas variáveis de ambiente!")
        else:
            logger.info("PUBG API otimizada inicializada com sucesso")
            logger.info(f"Rate limit: {self.rate_limit['max_requests']} req/{self.rate_limit['time_window']}s")
    
    def _generate_cache_key(self, *args) -> str:
        """Gera uma chave única para o cache"""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str, cache_type: str) -> bool:
        """Verifica se o cache ainda é válido"""
        if cache_key not in self.cache:
            return False
        
        cache_entry = self.cache[cache_key]
        duration = self.cache_duration.get(cache_type, 30 * 60)
        
        return (time.time() - cache_entry['timestamp']) < duration
    
    def _get_from_cache(self, cache_key: str, cache_type: str) -> Optional[Any]:
        """Recupera dados do cache se válidos"""
        if self._is_cache_valid(cache_key, cache_type):
            self.cache_stats['hits'] += 1
            logger.debug(f"Cache hit para {cache_key[:8]}...")
            return self.cache[cache_key]['data']
        
        self.cache_stats['misses'] += 1
        return None
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """Salva dados no cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        self.cache_stats['saves'] += 1
        
        # Limpeza automática do cache (manter apenas 1000 entradas)
        if len(self.cache) > 1000:
            oldest_keys = sorted(self.cache.keys(), 
                               key=lambda k: self.cache[k]['timestamp'])[:100]
            for key in oldest_keys:
                del self.cache[key]
    
    async def _wait_for_rate_limit(self) -> None:
        """Aguarda se necessário para respeitar o rate limit"""
        current_time = time.time()
        
        # Se estamos bloqueados, aguarda
        if current_time < self.rate_limit['blocked_until']:
            wait_time = self.rate_limit['blocked_until'] - current_time
            logger.warning(f"Rate limit ativo. Aguardando {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            return
        
        # Remove requisições antigas da janela de tempo
        window_start = current_time - self.rate_limit['time_window']
        while (self.rate_limit['requests'] and 
               self.rate_limit['requests'][0] < window_start):
            self.rate_limit['requests'].popleft()
        
        # Se atingiu o limite, aguarda
        if len(self.rate_limit['requests']) >= self.rate_limit['max_requests']:
            wait_time = (self.rate_limit['requests'][0] + 
                        self.rate_limit['time_window'] - current_time)
            if wait_time > 0:
                logger.warning(f"Rate limit atingido. Aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
    
    async def _make_request_with_retry(self, url: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Faz requisição com retry automático e tratamento de erros"""
        await self._wait_for_rate_limit()
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                # Registra a requisição para rate limiting
                self.rate_limit['requests'].append(time.time())
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limit exceeded
                            retry_after = int(response.headers.get('Retry-After', 60))
                            self.rate_limit['blocked_until'] = time.time() + retry_after
                            logger.warning(f"Rate limit da API excedido. Bloqueado por {retry_after}s")
                            if attempt < self.retry_config['max_retries'] - 1:
                                await asyncio.sleep(retry_after)
                                continue
                        elif response.status == 404:
                            logger.warning(f"Recurso não encontrado: {url}")
                            return None
                        elif response.status >= 500:
                            logger.warning(f"Erro do servidor ({response.status}). Tentativa {attempt + 1}")
                            if attempt < self.retry_config['max_retries'] - 1:
                                delay = min(self.retry_config['base_delay'] * 
                                          (self.retry_config['backoff_factor'] ** attempt),
                                          self.retry_config['max_delay'])
                                await asyncio.sleep(delay)
                                continue
                        else:
                            logger.error(f"Erro na API: {response.status} - {await response.text()}")
                            return None
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout na requisição. Tentativa {attempt + 1}")
                if attempt < self.retry_config['max_retries'] - 1:
                    await asyncio.sleep(self.retry_config['base_delay'] * (attempt + 1))
                    continue
            except Exception as e:
                logger.error(f"Erro na requisição: {e}. Tentativa {attempt + 1}")
                if attempt < self.retry_config['max_retries'] - 1:
                    await asyncio.sleep(self.retry_config['base_delay'] * (attempt + 1))
                    continue
        
        logger.error(f"Falha após {self.retry_config['max_retries']} tentativas")
        return None
    
    async def get_player_stats(self, player_name: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca estatísticas completas de um jogador com cache otimizado"""
        try:
            if not self.api_key:
                logger.error("API key não configurada")
                return None
            
            # Validar shard
            if shard not in self.valid_shards:
                logger.error(f"Shard inválido: {shard}")
                return None
            
            # Verificar cache primeiro
            cache_key = self._generate_cache_key("player_stats", player_name, shard)
            cached_data = self._get_from_cache(cache_key, 'stats')
            if cached_data:
                logger.info(f"Dados do cache para {player_name}")
                return cached_data
            
            # Buscar dados do jogador
            player_data = await self._get_player_by_name(player_name, shard)
            if not player_data:
                return None
            
            player_id = player_data['id']
            
            # Buscar estatísticas da temporada
            season_stats = await self._get_season_stats(player_id, shard)
            if not season_stats:
                logger.warning(f"Não foi possível obter estatísticas da temporada para {player_name}")
                season_stats = {}
            
            # Buscar partidas recentes (limitado para economizar API calls)
            recent_matches = await self._get_recent_matches(player_id, shard, limit=5)
            
            # Compilar dados completos
            complete_stats = {
                'player_info': {
                    'id': player_id,
                    'name': player_data['attributes']['name'],
                    'shard': shard
                }
            }
        except Exception as e:
            logger.error(f"Erro ao buscar dados de fallback: {e}")
            return {}
    
    async def get_essential_player_data(self, player_name: str, shard: str = 'steam') -> Dict[str, Any]:
        """Busca apenas dados essenciais do jogador para economizar API calls"""
        try:
            # Verificar cache primeiro
            cache_key = self._generate_cache_key("essential_data", player_name, shard)
            cached_data = self._get_from_cache(cache_key, 'player')
            if cached_data:
                return cached_data
            
            # Buscar apenas dados básicos do jogador
            player_data = await self._get_player_by_name(player_name, shard)
            if not player_data:
                return self._get_fallback_data('player_stats', player_name)
            
            # Buscar apenas estatísticas da temporada (sem partidas recentes)
            season_stats = await self._get_season_stats(player_data['id'], shard)
            
            essential_data = {
                'player_info': {
                    'name': player_data.get('name', player_name),
                    'id': player_data.get('id'),
                    'shard': shard
                },
                'season_stats': season_stats or {},
                'last_updated': datetime.now().isoformat(),
                'data_type': 'essential'
            }
            
            # Cache por mais tempo para dados essenciais
            self._save_to_cache(cache_key, essential_data)
            
            return essential_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados essenciais de {player_name}: {e}")
            return self._get_fallback_data('player_stats', player_name)
    
    async def get_batch_player_stats(self, player_names: List[str], shard: str = 'steam', max_concurrent: int = 3) -> Dict[str, Dict[str, Any]]:
        """Busca estatísticas de múltiplos jogadores de forma otimizada"""
        results = {}
        
        # Dividir em lotes para respeitar rate limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_single_player(name: str) -> tuple:
            async with semaphore:
                try:
                    stats = await self.get_essential_player_data(name, shard)
                    return name, stats
                except Exception as e:
                    logger.error(f"Erro ao buscar {name}: {e}")
                    return name, self._get_fallback_data('player_stats', name)
        
        # Executar consultas em paralelo (limitado)
        tasks = [get_single_player(name) for name in player_names]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, tuple):
                name, stats = result
                results[name] = stats
            else:
                logger.error(f"Erro na consulta em lote: {result}")
        
        return results
    
    async def get_quick_rank_data(self, player_name: str, shard: str = 'steam') -> Dict[str, Any]:
        """Busca apenas dados necessários para ranking (otimizado)"""
        try:
            # Verificar cache específico para ranking
            cache_key = self._generate_cache_key("rank_data", player_name, shard)
            cached_data = self._get_from_cache(cache_key, 'stats')
            if cached_data:
                return cached_data
            
            # Buscar dados essenciais
            essential_data = await self.get_essential_player_data(player_name, shard)
            
            if essential_data.get('fallback_mode'):
                return essential_data
            
            # Extrair apenas dados relevantes para ranking
            season_stats = essential_data.get('season_stats', {})
            
            rank_data = {
                'player_name': player_name,
                'total_kills': 0,
                'total_deaths': 0,
                'total_wins': 0,
                'total_matches': 0,
                'kd_ratio': 0.0,
                'win_rate': 0.0,
                'rank_score': 0
            }
            
            # Somar estatísticas de todos os modos
            for mode_stats in season_stats.values():
                if isinstance(mode_stats, dict):
                    rank_data['total_kills'] += mode_stats.get('kills', 0)
                    rank_data['total_deaths'] += mode_stats.get('deaths', 0)
                    rank_data['total_wins'] += mode_stats.get('wins', 0)
                    rank_data['total_matches'] += mode_stats.get('roundsPlayed', 0)
            
            # Calcular métricas
            if rank_data['total_deaths'] > 0:
                rank_data['kd_ratio'] = rank_data['total_kills'] / rank_data['total_deaths']
            
            if rank_data['total_matches'] > 0:
                rank_data['win_rate'] = (rank_data['total_wins'] / rank_data['total_matches']) * 100
            
            # Calcular score de ranking
            rank_data['rank_score'] = self.calculate_rank({
                'kd_ratio': rank_data['kd_ratio'],
                'matches_played': rank_data['total_matches'],
                'win_rate': rank_data['win_rate']
            })
            
            rank_data['last_updated'] = datetime.now().isoformat()
            
            # Cache por tempo menor (dados de ranking mudam mais)
            self._save_to_cache(cache_key, rank_data)
            
            return rank_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de ranking de {player_name}: {e}")
            return {
                'player_name': player_name,
                'total_kills': 0,
                'total_deaths': 0,
                'total_wins': 0,
                'total_matches': 0,
                'kd_ratio': 0.0,
                'win_rate': 0.0,
                'rank_score': 0,
                'fallback_mode': True,
                'error': str(e)
            }
    
    def optimize_api_usage(self) -> Dict[str, Any]:
        """Retorna sugestões para otimizar o uso da API"""
        stats = self.get_cache_stats()
        
        suggestions = []
        
        # Analisar hit rate do cache
        hit_rate = stats['cache']['hit_rate_percent']
        if hit_rate < 70:
            suggestions.append("Considere aumentar a duração do cache para melhorar o hit rate")
        
        # Analisar uso de rate limiting
        rate_info = stats['rate_limiting']
        if rate_info['requests_in_window'] > (rate_info['max_requests'] * 0.8):
            suggestions.append("Próximo do limite de rate limiting. Considere usar mais cache")
        
        # Sugestões gerais
        suggestions.extend([
            "Use get_essential_player_data() para consultas básicas",
            "Use get_quick_rank_data() apenas para rankings",
            "Use get_batch_player_stats() para múltiplos jogadores",
            "Evite buscar partidas recentes desnecessariamente"
        ])
        
        return {
            'current_stats': stats,
            'optimization_suggestions': suggestions,
            'recommended_methods': {
                'basic_stats': 'get_essential_player_data()',
                'ranking_only': 'get_quick_rank_data()',
                'multiple_players': 'get_batch_player_stats()',
                'full_data': 'get_player_stats_with_fallback()'
            }
        }
    
    async def _get_player_by_name(self, player_name: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca dados do jogador pelo nome com cache e retry"""
        try:
            # Verificar cache primeiro
            cache_key = self._generate_cache_key("player", player_name, shard)
            cached_data = self._get_from_cache(cache_key, 'player')
            if cached_data:
                return cached_data
            
            url = f"{self.base_url}/shards/{shard}/players?filter[playerNames]={player_name}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            # Fazer requisição com retry
            response_data = await self._make_request_with_retry(url, headers)
            
            if response_data and response_data.get('data') and len(response_data['data']) > 0:
                player_data = response_data['data'][0]
                
                # Salvar no cache
                self._save_to_cache(cache_key, player_data)
                
                return player_data
            else:
                logger.warning(f"Jogador {player_name} não encontrado")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar jogador {player_name}: {e}")
            return None
    
    async def _get_season_stats(self, player_id: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca estatísticas da temporada atual do jogador com cache"""
        try:
            # Verificar cache primeiro
            cache_key = self._generate_cache_key("season_stats", player_id, shard)
            cached_data = self._get_from_cache(cache_key, 'stats')
            if cached_data:
                return cached_data
            
            # Primeiro, obter a temporada atual
            current_season = await self._get_current_season(shard)
            if not current_season:
                logger.error("Não foi possível obter a temporada atual")
                return None
            
            season_id = current_season['id']
            url = f"{self.base_url}/shards/{shard}/players/{player_id}/seasons/{season_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json"
            }
            
            # Fazer requisição com retry
            response_data = await self._make_request_with_retry(url, headers)
            
            if response_data:
                processed_stats = self._process_season_stats(response_data)
                
                # Salvar no cache
                self._save_to_cache(cache_key, processed_stats)
                
                return processed_stats
            else:
                logger.warning(f"Estatísticas da temporada não encontradas para o jogador")
                return None
                        
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas da temporada: {e}")
            return None
    
    async def _get_current_season(self, shard: str) -> Optional[Dict[str, Any]]:
        """Busca a temporada atual com cache otimizado"""
        try:
            # Verificar cache primeiro (1 hora de duração)
            cache_key = self._generate_cache_key("current_season", shard)
            cached_data = self._get_from_cache(cache_key, 'season')
            if cached_data:
                return cached_data
            
            url = f"{self.base_url}/shards/{shard}/seasons"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json"
            }
            
            # Fazer requisição com retry
            response_data = await self._make_request_with_retry(url, headers)
            
            if response_data:
                seasons = response_data.get('data', [])
                
                # Encontrar temporada atual (isCurrentSeason = true)
                current_season = None
                for season in seasons:
                    if season.get('attributes', {}).get('isCurrentSeason', False):
                        current_season = season
                        break
                
                if current_season:
                    # Salvar no cache
                    self._save_to_cache(cache_key, current_season)
                    return current_season
                else:
                    logger.error("Nenhuma temporada atual encontrada")
                    return None
            else:
                logger.error("Erro ao buscar temporadas")
                return None
                        
        except Exception as e:
            logger.error(f"Erro ao buscar temporada atual: {e}")
            return None
    
    async def _get_recent_matches(self, player_id: str, shard: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Busca partidas recentes do jogador com limite configurável"""
        try:
            # Verificar cache primeiro
            cache_key = self._generate_cache_key("recent_matches", player_id, shard, limit)
            cached_data = self._get_from_cache(cache_key, 'matches')
            if cached_data:
                return cached_data
            
            url = f"{self.base_url}/shards/{shard}/players/{player_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            # Fazer requisição com retry
            response_data = await self._make_request_with_retry(url, headers)
            
            if response_data:
                # Extrair IDs das partidas
                match_relationships = response_data['data']['relationships']['matches']['data']
                match_ids = [match['id'] for match in match_relationships[:limit]]
                
                # Buscar detalhes das partidas (com limite para economizar API calls)
                matches_details = []
                for match_id in match_ids:
                    match_detail = await self._get_match_details(match_id, shard)
                    if match_detail:
                        matches_details.append(match_detail)
                
                # Salvar no cache
                self._save_to_cache(cache_key, matches_details)
                
                return matches_details
            else:
                logger.error("Erro ao buscar partidas")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas recentes: {e}")
            return None
    
    async def _get_match_details(self, match_id: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de uma partida específica com cache otimizado"""
        try:
            # Verificar cache primeiro (2 horas de duração para partidas)
            cache_key = self._generate_cache_key("match_details", match_id, shard)
            cached_data = self._get_from_cache(cache_key, 'matches')
            if cached_data:
                return cached_data
            
            url = f"{self.base_url}/shards/{shard}/matches/{match_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json"
            }
            
            # Fazer requisição com retry
            response_data = await self._make_request_with_retry(url, headers)
            
            if response_data:
                processed_match = self._process_match_data(response_data)
                
                # Salvar no cache
                self._save_to_cache(cache_key, processed_match)
                
                return processed_match
            else:
                logger.error("Erro ao buscar detalhes da partida")
                return None
                        
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da partida {match_id}: {e}")
            return None
    
    def _process_season_stats(self, season_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados de estatísticas da temporada"""
        try:
            attributes = season_data['data']['attributes']
            game_mode_stats = attributes['gameModeStats']
            
            # Mapeamento correto: ranked são os modos competitivos, mm são os normais
            processed_stats = {
                'ranked': {
                    # Modos ranqueados (competitivos) - incluindo MD5
                    'solo': self._extract_mode_stats(game_mode_stats.get('ranked-solo', game_mode_stats.get('solo', {}))),
                    'duo': self._extract_mode_stats(game_mode_stats.get('ranked-duo', game_mode_stats.get('duo', {}))),
                    'squad': self._extract_mode_stats(game_mode_stats.get('ranked-squad', game_mode_stats.get('squad', {})))
                },
                'mm': {
                    # Modos normais (matchmaking casual)
                    'solo': self._extract_mode_stats(game_mode_stats.get('solo-fpp', {})),
                    'duo': self._extract_mode_stats(game_mode_stats.get('duo-fpp', {})),
                    'squad': self._extract_mode_stats(game_mode_stats.get('squad-fpp', {}))
                }
            }
            
            return processed_stats
            
        except Exception as e:
            logger.error(f"Erro ao processar stats da temporada: {e}")
            return {}
    
    def _extract_mode_stats(self, mode_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai estatísticas de um modo específico"""
        if not mode_data:
            return {
                'kd': 0.0,
                'wins': 0,
                'matches': 0,
                'damage_avg': 0.0,
                'kills': 0,
                'deaths': 0,
                'top10s': 0,
                'winrate': 0.0
            }
        
        kills = mode_data.get('kills', 0)
        deaths = max(mode_data.get('losses', 1), 1)  # Evitar divisão por zero
        matches = mode_data.get('roundsPlayed', 0)
        wins = mode_data.get('wins', 0)
        
        return {
            'kd': round(kills / deaths, 2),
            'wins': wins,
            'matches': matches,
            'damage_avg': round(mode_data.get('damageDealt', 0) / max(matches, 1), 2),
            'kills': kills,
            'deaths': deaths,
            'top10s': mode_data.get('top10s', 0),
            'winrate': round((wins / max(matches, 1)) * 100, 2)
        }
    
    def _process_match_data(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados de uma partida"""
        try:
            attributes = match_data['data']['attributes']
            
            return {
                'id': match_data['data']['id'],
                'created_at': attributes.get('createdAt'),
                'duration': attributes.get('duration'),
                'game_mode': attributes.get('gameMode'),
                'map_name': attributes.get('mapName'),
                'match_type': attributes.get('matchType'),
                'replay_url': f"https://pubg.sh/{match_data['data']['id']}"
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar dados da partida: {e}")
            return {}
    
    def calculate_rank(self, stats: Dict[str, Any], mode_type: str = 'ranked') -> str:
        """Calcula rank baseado nas estatísticas"""
        try:
            # Pegar stats do modo específico (squad por padrão)
            mode_stats = stats.get(mode_type, {}).get('squad', {})
            
            kd = mode_stats.get('kd', 0)
            matches = mode_stats.get('matches', 0)
            
            # Critério mínimo de partidas
            if matches < 10:
                return "Sem rank" if mode_type == 'ranked' else "Sem rank MM"
            
            # Definir ranks baseado no K/D
            if mode_type == 'ranked':
                if kd >= 4.0:
                    return "Predador"
                elif kd >= 3.0:
                    return "Diamante"
                elif kd >= 2.0:
                    return "Ouro"
                elif kd >= 1.0:
                    return "Prata"
                else:
                    return "Bronze"
            else:  # MM
                if kd >= 4.0:
                    return "Mestre MM"
                elif kd >= 3.0:
                    return "Diamante MM"
                elif kd >= 2.0:
                    return "Ouro MM"
                elif kd >= 1.0:
                    return "Prata MM"
                else:
                    return "Bronze MM"
                    
        except Exception as e:
            logger.error(f"Erro ao calcular rank: {e}")
            return "Erro"
    
    def _is_cached(self, key: str) -> bool:
        """Verifica se dados estão em cache e ainda válidos"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]['timestamp']
        duration = self.cache[key].get('duration', self.cache_duration)
        
        return (datetime.now().timestamp() - cache_time) < duration
    
    def _cache_data(self, key: str, data: Any, duration: int = None):
        """Salva dados no cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp(),
            'duration': duration or self.cache_duration
        }
    
    def clear_cache(self, cache_type: Optional[str] = None) -> Dict[str, int]:
        """Limpa o cache completamente ou por tipo"""
        if cache_type:
            # Limpar apenas entradas de um tipo específico
            keys_to_remove = []
            for key in self.cache.keys():
                if key.startswith(hashlib.md5(cache_type.encode()).hexdigest()[:8]):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            return {'removed': len(keys_to_remove), 'remaining': len(self.cache)}
        else:
            # Limpar todo o cache
            removed_count = len(self.cache)
            self.cache.clear()
            self.cache_stats = defaultdict(int)
            
            return {'removed': removed_count, 'remaining': 0}
    
    def clear_expired_cache(self) -> Dict[str, int]:
        """Remove apenas entradas expiradas do cache"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            # Determinar tipo de cache baseado na chave
            cache_type = 'stats'  # padrão
            if 'player' in key:
                cache_type = 'player'
            elif 'season' in key:
                cache_type = 'season'
            elif 'match' in key:
                cache_type = 'matches'
            
            duration = self.cache_duration.get(cache_type, 30 * 60)
            if (current_time - entry['timestamp']) > duration:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        return {'removed': len(keys_to_remove), 'remaining': len(self.cache)}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache"""
        total_entries = len(self.cache)
        cache_size_mb = sum(len(str(entry)) for entry in self.cache.values()) / (1024 * 1024)
        
        # Calcular hit rate
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Estatísticas de rate limiting
        current_time = time.time()
        recent_requests = len([req for req in self.rate_limit['requests'] 
                              if current_time - req < self.rate_limit['time_window']])
        
        return {
            'cache': {
                'total_entries': total_entries,
                'cache_size_mb': round(cache_size_mb, 2),
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'saves': self.cache_stats['saves'],
                'hit_rate_percent': round(hit_rate, 2),
                'oldest_entry': min([entry['timestamp'] for entry in self.cache.values()]) if self.cache else None,
                'newest_entry': max([entry['timestamp'] for entry in self.cache.values()]) if self.cache else None
            },
            'rate_limiting': {
                'requests_in_window': recent_requests,
                'max_requests': self.rate_limit['max_requests'],
                'window_seconds': self.rate_limit['time_window'],
                'blocked_until': self.rate_limit['blocked_until'],
                'is_blocked': current_time < self.rate_limit['blocked_until']
            },
            'api_health': {
                'api_key_configured': bool(self.api_key),
                'base_url': self.base_url
            }
        }
    
    async def validate_player(self, player_name: str, shard: str) -> bool:
        """Valida se um jogador existe na API"""
        try:
            player_data = await self._get_player_by_name(player_name, shard)
            return player_data is not None
        except Exception as e:
            logger.error(f"Erro ao validar jogador {player_name}: {e}")
            return False
    
    async def is_api_available(self) -> bool:
        """Verifica se a API está disponível fazendo uma requisição simples"""
        try:
            if not self.api_key:
                return False
            
            # Testar com uma requisição simples para temporadas
            url = f"{self.base_url}/shards/steam/seasons"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json"
            }
            
            response_data = await self._make_request_with_retry(url, headers)
            return response_data is not None
                    
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade da API: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Realiza verificação completa de saúde da API"""
        health_status = {
            'api_key_configured': bool(self.api_key),
            'api_available': False,
            'cache_stats': self.get_cache_stats(),
            'timestamp': time.time()
        }
        
        if self.api_key:
            health_status['api_available'] = await self.is_api_available()
        
        return health_status
    
    def _get_fallback_data(self, data_type: str, player_name: str = None) -> Dict[str, Any]:
        """Retorna dados de fallback quando a API falha"""
        current_time = datetime.now().isoformat()
        
        if data_type == 'player_stats':
            return {
                'player_info': {
                    'name': player_name or 'Unknown',
                    'id': 'fallback_id',
                    'shardId': 'steam'
                },
                'season_stats': {
                    'solo': {
                        'kills': 0,
                        'deaths': 0,
                        'assists': 0,
                        'wins': 0,
                        'top10s': 0,
                        'roundsPlayed': 0,
                        'kd_ratio': 0.0,
                        'avg_damage': 0.0
                    },
                    'duo': {
                        'kills': 0,
                        'deaths': 0,
                        'assists': 0,
                        'wins': 0,
                        'top10s': 0,
                        'roundsPlayed': 0,
                        'kd_ratio': 0.0,
                        'avg_damage': 0.0
                    },
                    'squad': {
                        'kills': 0,
                        'deaths': 0,
                        'assists': 0,
                        'wins': 0,
                        'top10s': 0,
                        'roundsPlayed': 0,
                        'kd_ratio': 0.0,
                        'avg_damage': 0.0
                    }
                },
                'recent_matches': [],
                'last_updated': current_time,
                'fallback_mode': True,
                'fallback_reason': 'API indisponível ou erro na requisição'
            }
        
        return {}
    
    async def get_player_stats_with_fallback(self, player_name: str, shard: str) -> Dict[str, Any]:
        """Busca estatísticas com fallback automático em caso de falha"""
        try:
            # Tentar buscar dados normalmente
            stats = await self.get_player_stats(player_name, shard)
            
            if stats:
                return stats
            else:
                logger.warning(f"API falhou para {player_name}, usando dados de fallback")
                return self._get_fallback_data('player_stats', player_name)
                
        except Exception as e:
            logger.error(f"Erro crítico na API para {player_name}: {e}")
            return self._get_fallback_data('player_stats', player_name)
    
    async def validate_player_with_fallback(self, player_name: str, shard: str = 'steam') -> Dict[str, Any]:
        """Valida jogador com fallback em caso de erro"""
        try:
            # Tentar validação normal
            player_data = await self._get_player_by_name(player_name, shard)
            
            if player_data:
                return {
                    'valid': True,
                    'player_data': player_data,
                    'fallback_mode': False
                }
            else:
                return {
                    'valid': False,
                    'player_data': None,
                    'fallback_mode': False,
                    'error': 'Jogador não encontrado'
                }
                
        except Exception as e:
            logger.error(f"Erro na validação de {player_name}: {e}")
            return {
                'valid': True,  # Assumir válido em caso de erro da API
                'player_data': {
                    'name': player_name,
                    'id': f'fallback_{player_name}',
                    'shardId': shard
                },
                'fallback_mode': True,
                'error': str(e)
            }