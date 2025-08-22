#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Gerenciamento de Dados
Responsável por salvar e carregar dados do bot em formato JSON

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import json
import os
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger('HawkBot.Storage')

class DataStorage:
    """Classe para gerenciamento de dados JSON com backup automático"""
    
    def __init__(self, data_file: str = "data.json", backup_dir: str = "backups"):
        self.data_file = Path(data_file)
        self.backup_dir = Path(backup_dir)
        self.data = {}
        
        # Criar diretório de backup se não existir
        self.backup_dir.mkdir(exist_ok=True)
        
        # Carregar dados existentes
        self.load_data()
        
        logger.info(f"Storage inicializado: {self.data_file}")
    
    def load_data(self) -> Dict[str, Any]:
        """Carrega dados do arquivo JSON"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Dados carregados: {len(self.data)} entradas")
            else:
                # Criar estrutura inicial
                self.data = self._create_initial_structure()
                self.save_data()
                logger.info("Arquivo de dados criado com estrutura inicial")
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            # Tentar carregar backup mais recente
            if self._restore_from_backup():
                logger.info("Dados restaurados do backup")
            else:
                self.data = self._create_initial_structure()
                logger.warning("Criada nova estrutura de dados")
        
        return self.data
    
    def save_data(self) -> bool:
        """Salva dados no arquivo JSON"""
        try:
            # Criar backup antes de salvar
            self._create_backup()
            
            # Salvar dados
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug("Dados salvos com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
            return False
    
    def _create_initial_structure(self) -> Dict[str, Any]:
        """Cria estrutura inicial dos dados"""
        return {
            "players": {},
            "guilds": {},
            "clips": {},
            "rankings": {},
            "settings": {
                "last_update": None,
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            },
            "stats": {
                "total_players": 0,
                "total_clips": 0,
                "last_rank_update": None
            }
        }
    
    def _create_backup(self) -> bool:
        """Cria backup dos dados atuais"""
        try:
            if not self.data_file.exists():
                return True
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"data_backup_{timestamp}.json"
            
            shutil.copy2(self.data_file, backup_file)
            
            # Limpar backups antigos
            self._cleanup_old_backups()
            
            logger.debug(f"Backup criado: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False
    
    def _cleanup_old_backups(self, max_backups: int = 7):
        """Remove backups antigos, mantendo apenas os mais recentes"""
        try:
            backup_files = list(self.backup_dir.glob("data_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remover backups excedentes
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
                logger.debug(f"Backup antigo removido: {backup_file}")
                
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {e}")
    
    def _restore_from_backup(self) -> bool:
        """Restaura dados do backup mais recente"""
        try:
            backup_files = list(self.backup_dir.glob("data_backup_*.json"))
            if not backup_files:
                return False
            
            # Pegar backup mais recente
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            logger.info(f"Dados restaurados do backup: {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False
    
    # ==================== MÉTODOS DE JOGADORES ====================
    
    def add_player(self, user_id: str, pubg_name: str, shard: str, guild_id: str) -> bool:
        """Adiciona novo jogador"""
        try:
            if "players" not in self.data:
                self.data["players"] = {}
            
            self.data["players"][user_id] = {
                "pubg_name": pubg_name,
                "shard": shard,
                "guild_id": guild_id,
                "registered_at": datetime.now().isoformat(),
                "last_update": None,
                "stats": {
                    "ranked": {"kd": 0, "wins": 0, "matches": 0, "damage_avg": 0},
                    "mm": {"kd": 0, "wins": 0, "matches": 0, "damage_avg": 0}
                },
                "current_ranks": {
                    "ranked": None,
                    "mm": None
                },
                "clips": []
            }
            
            # Atualizar estatísticas
            self.data["stats"]["total_players"] += 1
            
            self.save_data()
            logger.info(f"Jogador adicionado: {pubg_name} ({user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar jogador: {e}")
            return False
    
    def get_player(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de um jogador"""
        return self.data.get("players", {}).get(user_id)
    
    def update_player_stats(self, user_id: str, stats: Dict[str, Any]) -> bool:
        """Atualiza estatísticas de um jogador"""
        try:
            if user_id not in self.data.get("players", {}):
                return False
            
            self.data["players"][user_id]["stats"] = stats
            self.data["players"][user_id]["last_update"] = datetime.now().isoformat()
            
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar stats do jogador {user_id}: {e}")
            return False
    
    def update_player(self, user_id: str, player_data: Dict[str, Any]) -> bool:
        """Atualiza todos os dados de um jogador"""
        try:
            if user_id not in self.data.get("players", {}):
                return False
            
            # Atualizar dados do jogador
            self.data["players"][user_id].update(player_data)
            
            # Garantir que current_ranks seja atualizado se os ranks estão nos dados
            if "ranked_rank" in player_data or "mm_rank" in player_data:
                if "current_ranks" not in self.data["players"][user_id]:
                    self.data["players"][user_id]["current_ranks"] = {}
                
                if "ranked_rank" in player_data:
                    self.data["players"][user_id]["current_ranks"]["ranked"] = player_data["ranked_rank"]
                
                if "mm_rank" in player_data:
                    self.data["players"][user_id]["current_ranks"]["mm"] = player_data["mm_rank"]
            
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar jogador {user_id}: {e}")
            return False
    
    def update_player_rank(self, user_id: str, rank_type: str, rank: str) -> bool:
        """Atualiza rank de um jogador"""
        try:
            if user_id not in self.data.get("players", {}):
                return False
            
            if "current_ranks" not in self.data["players"][user_id]:
                self.data["players"][user_id]["current_ranks"] = {}
            
            self.data["players"][user_id]["current_ranks"][rank_type] = rank
            
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar rank do jogador {user_id}: {e}")
            return False
    
    def get_all_players(self, guild_id: str = None) -> Dict[str, Any]:
        """Retorna todos os jogadores, opcionalmente filtrados por guild"""
        players = self.data.get("players", {})
        
        if guild_id:
            return {uid: data for uid, data in players.items() 
                   if data.get("guild_id") == guild_id}
        
        return players
    
    # ==================== MÉTODOS DE CLIPES ====================
    
    def add_clip(self, clip_data: Dict[str, Any]) -> bool:
        """Adiciona novo clipe"""
        try:
            if "clips" not in self.data:
                self.data["clips"] = {}
            
            # Usar o ID do clipe fornecido ou gerar um novo
            clip_id = clip_data.get('id', f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            user_id = clip_data.get('discord_user', clip_data.get('player_id'))
            
            # Armazenar o clipe completo
            self.data["clips"][clip_id] = clip_data
            
            # Adicionar à lista de clipes do jogador se ele estiver registrado
            if user_id and user_id in self.data.get("players", {}):
                if "clips" not in self.data["players"][user_id]:
                    self.data["players"][user_id]["clips"] = []
                if clip_id not in self.data["players"][user_id]["clips"]:
                    self.data["players"][user_id]["clips"].append(clip_id)
            
            # Atualizar estatísticas
            if "stats" not in self.data:
                self.data["stats"] = {"total_clips": 0}
            if "total_clips" not in self.data["stats"]:
                self.data["stats"]["total_clips"] = 0
            self.data["stats"]["total_clips"] += 1
            
            self.save_data()
            logger.info(f"Clipe adicionado: {clip_id} de {clip_data.get('player_name', 'Desconhecido')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar clipe: {e}")
            return False
    
    def get_player_clips(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna clipes de um jogador"""
        try:
            player = self.get_player(user_id)
            if not player:
                return []
            
            clip_ids = player.get("clips", [])[-limit:]  # Últimos N clipes
            clips = []
            
            for clip_id in reversed(clip_ids):  # Mais recentes primeiro
                clip_data = self.data.get("clips", {}).get(clip_id)
                if clip_data:
                    clips.append(clip_data)
            
            return clips
            
        except Exception as e:
            logger.error(f"Erro ao buscar clipes do jogador {user_id}: {e}")
            return []
    
    def get_clips(self) -> List[Dict[str, Any]]:
        """Retorna todos os clipes armazenados"""
        try:
            clips_data = self.data.get("clips", {})
            clips = list(clips_data.values())
            
            # Ordenar por data de criação (mais recentes primeiro)
            clips.sort(
                key=lambda x: datetime.fromisoformat(x['created_at']),
                reverse=True
            )
            
            return clips
            
        except Exception as e:
            logger.error(f"Erro ao buscar todos os clipes: {e}")
            return []
    
    def remove_clip(self, clip_id: str) -> bool:
        """Remove um clipe específico pelo ID"""
        try:
            if "clips" not in self.data:
                return False
            
            # Procurar e remover o clipe
            if clip_id in self.data["clips"]:
                user_id = self.data["clips"][clip_id].get("user_id")
                
                # Remover da lista de clipes do jogador
                if user_id and user_id in self.data.get("players", {}):
                    player_clips = self.data["players"][user_id].get("clips", [])
                    if clip_id in player_clips:
                        player_clips.remove(clip_id)
                
                # Remover o clipe
                del self.data["clips"][clip_id]
                
                # Atualizar estatísticas
                self.data["stats"]["total_clips"] -= 1
                
                self.save_data()
                logger.info(f"Clipe {clip_id} removido com sucesso")
                return True
            
            logger.warning(f"Clipe {clip_id} não encontrado para remoção")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover clipe {clip_id}: {e}")
            return False
    
    # ==================== MÉTODOS DE RANKINGS ====================
    
    def save_ranking(self, guild_id: str, ranking_type: str, ranking_data: Dict[str, Any]) -> bool:
        """Salva dados de ranking"""
        try:
            if "rankings" not in self.data:
                self.data["rankings"] = {}
            
            if guild_id not in self.data["rankings"]:
                self.data["rankings"][guild_id] = {}
            
            self.data["rankings"][guild_id][ranking_type] = {
                "data": ranking_data,
                "generated_at": datetime.now().isoformat()
            }
            
            self.data["stats"]["last_rank_update"] = datetime.now().isoformat()
            
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar ranking: {e}")
            return False
    
    def get_ranking(self, guild_id: str, ranking_type: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de ranking"""
        return self.data.get("rankings", {}).get(guild_id, {}).get(ranking_type)
    
    # ==================== MÉTODOS DE CONFIGURAÇÕES ====================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retorna configuração"""
        return self.data.get("settings", {}).get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Define configuração"""
        try:
            if "settings" not in self.data:
                self.data["settings"] = {}
            
            self.data["settings"][key] = value
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir configuração {key}: {e}")
            return False
    
    # ==================== MÉTODOS DE ESTATÍSTICAS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais"""
        return self.data.get("stats", {})
    
    def update_stats(self, stats: Dict[str, Any]) -> bool:
        """Atualiza estatísticas gerais"""
        try:
            if "stats" not in self.data:
                self.data["stats"] = {}
            
            self.data["stats"].update(stats)
            self.save_data()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}")
            return False
    
    # ==================== MÉTODOS UTILITÁRIOS ====================
    
    def cleanup_data(self, days_old: int = 30) -> int:
        """Remove dados antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            removed_count = 0
            
            # Limpar clipes antigos
            clips_to_remove = []
            for clip_id, clip_data in self.data.get("clips", {}).items():
                created_at = datetime.fromisoformat(clip_data["created_at"])
                if created_at < cutoff_date:
                    clips_to_remove.append(clip_id)
            
            for clip_id in clips_to_remove:
                del self.data["clips"][clip_id]
                removed_count += 1
            
            if removed_count > 0:
                self.save_data()
                logger.info(f"Removidos {removed_count} itens antigos")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")
            return 0
    
    def export_data(self, export_file: str) -> bool:
        """Exporta dados para arquivo"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dados exportados para: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {e}")
            return False
    
    def get_data_size(self) -> Dict[str, int]:
        """Retorna informações sobre o tamanho dos dados"""
        try:
            file_size = self.data_file.stat().st_size if self.data_file.exists() else 0
            return {
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'total_entries': len(self.data),
                'players_count': len(self.data.get('players', {})),
                'clips_count': sum(len(player.get('clips', [])) for player in self.data.get('players', {}).values())
            }
        except Exception as e:
            logger.error(f"Erro ao obter tamanho dos dados: {e}")
            return {}
    
    def get_temporal_ranking_data(self, period: str) -> Dict[str, Any]:
        """Obtém dados de ranking temporal"""
        try:
            temporal_rankings = self.data.get('temporal_rankings', {})
            return temporal_rankings.get(period, {})
        except Exception as e:
            logger.error(f"Erro ao obter dados de ranking temporal: {e}")
            return {}
    
    def save_temporal_ranking_data(self, period: str, temporal_data: Dict[str, Any]) -> bool:
        """Salva dados de ranking temporal"""
        try:
            if 'temporal_rankings' not in self.data:
                self.data['temporal_rankings'] = {}
            
            self.data['temporal_rankings'][period] = temporal_data
            return self.save_data()
        except Exception as e:
            logger.error(f"Erro ao salvar dados de ranking temporal: {e}")
            return False
    
    def update_temporal_player_stats(self, user_id: str, period: str, stats: Dict[str, Any]) -> bool:
        """Atualiza estatísticas temporais de um jogador"""
        try:
            if 'temporal_rankings' not in self.data:
                self.data['temporal_rankings'] = {}
            
            if period not in self.data['temporal_rankings']:
                self.data['temporal_rankings'][period] = {
                    'last_reset': datetime.now().isoformat(),
                    'players': {},
                    'period': period
                }
            
            if user_id not in self.data['temporal_rankings'][period]['players']:
                self.data['temporal_rankings'][period]['players'][user_id] = {
                    'kills': 0, 'wins': 0, 'matches': 0, 'damage': 0, 'top10': 0
                }
            
            # Atualizar estatísticas
            player_temporal = self.data['temporal_rankings'][period]['players'][user_id]
            for key, value in stats.items():
                if key in player_temporal:
                    player_temporal[key] += value
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas temporais: {e}")
            return False
    
    def get_temporal_player_stats(self, user_id: str, period: str) -> Dict[str, Any]:
        """Obtém estatísticas temporais de um jogador"""
        try:
            temporal_data = self.get_temporal_ranking_data(period)
            return temporal_data.get('players', {}).get(user_id, {
                'kills': 0, 'wins': 0, 'matches': 0, 'damage': 0, 'top10': 0
            })
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas temporais: {e}")
            return {'kills': 0, 'wins': 0, 'matches': 0, 'damage': 0, 'top10': 0}