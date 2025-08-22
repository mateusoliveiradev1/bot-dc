#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Integração PUBG API
Responsável por buscar estatísticas e dados dos jogadores via API oficial

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger('HawkBot.PUBGAPI')

class PUBGIntegration:
    """Classe para integração com a API oficial do PUBG"""
    
    def __init__(self):
        self.api_key = os.getenv('PUBG_API_KEY')
        self.base_url = "https://api.pubg.com"
        self.cache = {}  # Cache simples para evitar muitas requisições
        self.cache_duration = 30 * 60  # 30 minutos em segundos
        
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
        
        if not self.api_key:
            logger.error("PUBG_API_KEY não encontrada nas variáveis de ambiente!")
        else:
            logger.info("PUBG API inicializada com sucesso")
    
    async def get_player_stats(self, player_name: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca estatísticas completas de um jogador"""
        try:
            # Verificar cache primeiro
            cache_key = f"{player_name}_{shard}_stats"
            if self._is_cached(cache_key):
                logger.debug(f"Retornando stats do cache para {player_name}")
                return self.cache[cache_key]['data']
            
            # Buscar player ID primeiro
            player_data = await self._get_player_by_name(player_name, shard)
            if not player_data:
                return None
            
            player_id = player_data['id']
            
            # Buscar estatísticas de temporada
            season_stats = await self._get_season_stats(player_id, shard)
            if not season_stats:
                return None
            
            # Buscar partidas recentes
            recent_matches = await self._get_recent_matches(player_id, shard)
            
            # Compilar dados completos
            complete_stats = {
                'player_info': {
                    'id': player_id,
                    'name': player_data['attributes']['name'],
                    'shard': shard
                },
                'season_stats': season_stats,
                'recent_matches': recent_matches or [],
                'last_updated': datetime.now().isoformat()
            }
            
            # Salvar no cache
            self._cache_data(cache_key, complete_stats)
            
            logger.info(f"Stats obtidas para {player_name} ({shard})")
            return complete_stats
            
        except Exception as e:
            logger.error(f"Erro ao buscar stats de {player_name}: {e}")
            return None
    
    async def _get_player_by_name(self, player_name: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca jogador pelo nome"""
        try:
            url = f"{self.base_url}/shards/{shard}/players"
            params = {'filter[playerNames]': player_name}
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        players = data.get('data', [])
                        if players:
                            return players[0]
                    elif response.status == 404:
                        logger.warning(f"Jogador não encontrado: {player_name}")
                    else:
                        logger.error(f"Erro na API PUBG: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar jogador {player_name}: {e}")
            return None
    
    async def _get_season_stats(self, player_id: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca estatísticas da temporada atual"""
        try:
            # Primeiro, buscar temporada atual
            current_season = await self._get_current_season(shard)
            if not current_season:
                return None
            
            season_id = current_season['id']
            
            url = f"{self.base_url}/shards/{shard}/players/{player_id}/seasons/{season_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_season_stats(data)
                    else:
                        logger.error(f"Erro ao buscar stats da temporada: {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar stats da temporada: {e}")
            return None
    
    async def _get_current_season(self, shard: str) -> Optional[Dict[str, Any]]:
        """Busca temporada atual"""
        try:
            cache_key = f"current_season_{shard}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            url = f"{self.base_url}/shards/{shard}/seasons"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        seasons = data.get('data', [])
                        
                        # Encontrar temporada atual (mais recente)
                        current_season = None
                        for season in seasons:
                            if season['attributes']['isCurrentSeason']:
                                current_season = season
                                break
                        
                        if not current_season and seasons:
                            current_season = seasons[-1]  # Última temporada
                        
                        if current_season:
                            self._cache_data(cache_key, current_season, duration=3600)  # Cache por 1 hora
                            return current_season
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar temporada atual: {e}")
            return None
    
    async def _get_recent_matches(self, player_id: str, shard: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Busca partidas recentes do jogador"""
        try:
            url = f"{self.base_url}/shards/{shard}/players/{player_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extrair IDs das partidas
                        match_relationships = data['data']['relationships']['matches']['data']
                        match_ids = [match['id'] for match in match_relationships[:limit]]
                        
                        # Buscar detalhes das partidas
                        matches_details = []
                        for match_id in match_ids:
                            match_detail = await self._get_match_details(match_id, shard)
                            if match_detail:
                                matches_details.append(match_detail)
                        
                        return matches_details
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas recentes: {e}")
            return None
    
    async def _get_match_details(self, match_id: str, shard: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de uma partida específica"""
        try:
            cache_key = f"match_{match_id}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            url = f"{self.base_url}/shards/{shard}/matches/{match_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        processed_match = self._process_match_data(data)
                        
                        # Cache por mais tempo (partidas não mudam)
                        self._cache_data(cache_key, processed_match, duration=3600)
                        
                        return processed_match
            
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
    
    def clear_cache(self):
        """Limpa todo o cache"""
        self.cache.clear()
        logger.info("Cache da API PUBG limpo")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_entries = len(self.cache)
        expired_entries = 0
        
        current_time = datetime.now().timestamp()
        for entry in self.cache.values():
            duration = entry.get('duration', self.cache_duration)
            if (current_time - entry['timestamp']) >= duration:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'valid_entries': total_entries - expired_entries
        }
    
    async def validate_player(self, player_name: str, shard: str) -> bool:
        """Valida se um jogador existe na API"""
        try:
            player_data = await self._get_player_by_name(player_name, shard)
            return player_data is not None
        except Exception as e:
            logger.error(f"Erro ao validar jogador {player_name}: {e}")
            return False
    
    def is_api_available(self) -> bool:
        """Verifica se a API está configurada corretamente"""
        return self.api_key is not None and self.api_key.strip() != ""