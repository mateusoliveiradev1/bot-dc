#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Sistema de Ranking
Responsável por calcular rankings, atualizar cargos e gerenciar gamificação

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os

logger = logging.getLogger('HawkBot.RankSystem')

class RankSystem:
    """Sistema de ranking e gamificação para o clã Hawk Esports"""
    
    def __init__(self, bot, storage, pubg_api):
        self.bot = bot
        self.storage = storage
        self.pubg_api = pubg_api
        
        # Configurações de ranking
        self.rank_thresholds = {
            'ranked': {
                'Predador': 4.0,
                'Diamante': 3.0,
                'Ouro': 2.0,
                'Prata': 1.0,
                'Bronze': 0.0
            },
            'mm': {
                'Mestre MM': 4.0,
                'Diamante MM': 3.0,
                'Ouro MM': 2.0,
                'Prata MM': 1.0,
                'Bronze MM': 0.0
            }
        }
        
        # Configurações mínimas
        self.min_matches = 10
        
        # Cores dos embeds
        self.embed_color = int(os.getenv('CLAN_EMBED_COLOR', '0x00ff00'), 16)
        
        # Sistema de rankings temporais
        self.temporal_rankings = {
            'daily': {'reset_hours': 24, 'title': 'Ranking Diário'},
            'weekly': {'reset_hours': 168, 'title': 'Ranking Semanal'}, 
            'monthly': {'reset_hours': 720, 'title': 'Ranking Mensal'}
        }
        
        # Badges e conquistas
        self.achievements = {
            'first_win': {'name': '🏆 Primeira Vitória', 'description': 'Primeira vitória registrada'},
            'kd_master': {'name': '💀 Mestre do K/D', 'description': 'K/D acima de 3.0'},
            'win_streak': {'name': '🔥 Sequência de Vitórias', 'description': '5 vitórias seguidas'},
            'damage_dealer': {'name': '💥 Causador de Dano', 'description': 'Dano médio acima de 400'},
            'survivor': {'name': '🛡️ Sobrevivente', 'description': 'Top 10 em 80% das partidas'},
            'veteran': {'name': '⭐ Veterano', 'description': '100+ partidas jogadas'}
        }
        
        logger.info("Sistema de Ranking inicializado")
    
    async def update_player_rank(self, player_id: str, guild_id: str) -> Dict[str, Any]:
        """Atualiza o rank de um jogador específico"""
        try:
            # Buscar dados do jogador
            player_data = self.storage.get_player(player_id)
            if not player_data:
                return {'success': False, 'error': 'Jogador não encontrado'}
            
            # Buscar stats atualizadas da API
            stats = await self.pubg_api.get_player_stats(
                player_data['pubg_name'], 
                player_data['shard']
            )
            
            if not stats:
                return {'success': False, 'error': 'Não foi possível obter estatísticas'}
            
            # Calcular novos ranks
            old_ranked_rank = player_data.get('ranked_rank', 'Sem rank')
            old_mm_rank = player_data.get('mm_rank', 'Sem rank MM')
            
            new_ranked_rank = self._calculate_rank(stats['season_stats'], 'ranked')
            new_mm_rank = self._calculate_rank(stats['season_stats'], 'mm')
            
            # Calcular estatísticas básicas a partir das season_stats
            basic_stats = self._calculate_basic_stats(stats['season_stats'])
            
            # Atualizar dados do jogador
            updated_data = {
                **player_data,
                'ranked_rank': new_ranked_rank,
                'mm_rank': new_mm_rank,
                'stats': basic_stats,  # Adicionar estatísticas básicas
                'current_ranks': {
                    'ranked': new_ranked_rank,
                    'mm': new_mm_rank
                },
                'last_stats_update': datetime.now().isoformat(),
                'season_stats': stats['season_stats']
            }
            
            # Verificar conquistas
            achievements = self._check_achievements(stats['season_stats'], player_data)
            if achievements:
                updated_data['achievements'] = player_data.get('achievements', []) + achievements
            
            # Salvar no storage
            self.storage.update_player(player_id, updated_data)
            
            # Verificar conquistas baseadas em estatísticas
            if hasattr(self.bot, 'achievement_system'):
                try:
                    # Preparar estatísticas para verificação de conquistas
                    ranked_stats = stats['season_stats'].get('ranked', {})
                    mm_stats = stats['season_stats'].get('mm', {})
                    
                    combat_stats = {
                        'kd_ratio': max(ranked_stats.get('squad', {}).get('kd', 0), mm_stats.get('squad', {}).get('kd', 0)),
                        'kills': ranked_stats.get('squad', {}).get('kills', 0) + mm_stats.get('squad', {}).get('kills', 0),
                        'wins': ranked_stats.get('squad', {}).get('wins', 0) + mm_stats.get('squad', {}).get('wins', 0),
                        'matches': ranked_stats.get('squad', {}).get('matches', 0) + mm_stats.get('squad', {}).get('matches', 0),
                        'registration_date': player_data.get('registered_at')
                    }
                    
                    unlocked = self.bot.achievement_system.check_achievements(player_id, combat_stats)
                    
                    # Enviar notificações de conquistas
                    if unlocked:
                        guild = self.bot.get_guild(int(guild_id))
                        if guild:
                            member = guild.get_member(int(player_id))
                            if member:
                                general_channel = discord.utils.get(guild.channels, name='geral')
                                if general_channel:
                                    for achievement in unlocked:
                                        await self.bot.achievement_system.send_achievement_notification(
                                            player_id, achievement, general_channel
                                        )
                except Exception as e:
                    logger.error(f"Erro ao verificar conquistas de combate: {e}")
            
            # Atualizar roles no Discord
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                member = guild.get_member(int(player_id))
                if member:
                    await self._update_member_roles(member, new_ranked_rank, new_mm_rank)
                    
                    # Notificar sobre mudanças de rank
                    if new_ranked_rank != old_ranked_rank or new_mm_rank != old_mm_rank:
                        await self._notify_rank_change(
                            member, old_ranked_rank, new_ranked_rank, 
                            old_mm_rank, new_mm_rank, achievements
                        )
            
            return {
                'success': True,
                'old_ranks': {'ranked': old_ranked_rank, 'mm': old_mm_rank},
                'new_ranks': {'ranked': new_ranked_rank, 'mm': new_mm_rank},
                'achievements': achievements or []
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar rank do jogador {player_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_all_ranks(self, guild_id: str) -> Dict[str, Any]:
        """Atualiza ranks de todos os jogadores registrados"""
        try:
            logger.info("Iniciando atualização de todos os ranks")
            
            # Buscar todos os jogadores
            all_players = self.storage.get_all_players()
            
            results = {
                'total_players': len(all_players),
                'updated': 0,
                'errors': 0,
                'rank_changes': [],
                'new_achievements': []
            }
            
            for player_id, player_data in all_players.items():
                try:
                    # Pequena pausa para não sobrecarregar a API
                    await asyncio.sleep(1)
                    
                    result = await self.update_player_rank(player_id, guild_id)
                    
                    if result['success']:
                        results['updated'] += 1
                        
                        # Registrar mudanças de rank
                        if (result['old_ranks']['ranked'] != result['new_ranks']['ranked'] or 
                            result['old_ranks']['mm'] != result['new_ranks']['mm']):
                            results['rank_changes'].append({
                                'player_id': player_id,
                                'player_name': player_data.get('pubg_name', 'Desconhecido'),
                                'old_ranks': result['old_ranks'],
                                'new_ranks': result['new_ranks']
                            })
                        
                        # Registrar novas conquistas
                        if result['achievements']:
                            results['new_achievements'].extend([
                                {
                                    'player_id': player_id,
                                    'player_name': player_data.get('pubg_name', 'Desconhecido'),
                                    'achievement': achievement
                                }
                                for achievement in result['achievements']
                            ])
                    else:
                        results['errors'] += 1
                        logger.warning(f"Erro ao atualizar {player_id}: {result.get('error')}")
                        
                except Exception as e:
                    results['errors'] += 1
                    logger.error(f"Erro ao processar jogador {player_id}: {e}")
            
            logger.info(f"Atualização concluída: {results['updated']}/{results['total_players']} atualizados")
            return results
            
        except Exception as e:
            logger.error(f"Erro na atualização geral de ranks: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_leaderboard(self, guild_id: str, mode: str = 'squad', 
                                 rank_type: str = 'ranked', limit: int = 10) -> discord.Embed:
        """Gera leaderboard formatado"""
        try:
            # Buscar todos os jogadores
            all_players = self.storage.get_all_players()
            
            # Filtrar e ordenar jogadores
            valid_players = []
            for player_id, player_data in all_players.items():
                stats = player_data.get('season_stats', {})
                mode_stats = stats.get(rank_type, {}).get(mode, {})
                
                if mode_stats.get('matches', 0) >= self.min_matches:
                    valid_players.append({
                        'player_id': player_id,
                        'name': player_data.get('pubg_name', 'Desconhecido'),
                        'rank': player_data.get(f'{rank_type}_rank', 'Sem rank'),
                        'kd': mode_stats.get('kd', 0),
                        'wins': mode_stats.get('wins', 0),
                        'matches': mode_stats.get('matches', 0),
                        'winrate': mode_stats.get('winrate', 0),
                        'damage_avg': mode_stats.get('damage_avg', 0)
                    })
            
            # Ordenar por K/D
            valid_players.sort(key=lambda x: x['kd'], reverse=True)
            
            # Criar embed
            title = f"🏆 Leaderboard {rank_type.upper()} - {mode.upper()}"
            embed = discord.Embed(
                title=title,
                description=f"**Hawk Esports** - Top {min(limit, len(valid_players))} jogadores",
                color=self.embed_color,
                timestamp=datetime.now()
            )
            
            # Adicionar jogadores ao embed
            leaderboard_text = ""
            for i, player in enumerate(valid_players[:limit], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                leaderboard_text += (
                    f"{medal} **{player['name']}** ({player['rank']})\n"
                    f"   K/D: `{player['kd']}` | Vitórias: `{player['wins']}` | "
                    f"WR: `{player['winrate']}%`\n\n"
                )
            
            if leaderboard_text:
                embed.add_field(
                    name="📊 Ranking",
                    value=leaderboard_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📊 Ranking",
                    value="Nenhum jogador com partidas suficientes encontrado.",
                    inline=False
                )
            
            # Adicionar informações extras
            embed.add_field(
                name="ℹ️ Informações",
                value=f"Modo: **{mode.upper()}**\n"
                      f"Tipo: **{rank_type.upper()}**\n"
                      f"Mínimo de partidas: **{self.min_matches}**",
                inline=True
            )
            
            embed.add_field(
                name="📈 Estatísticas",
                value=f"Total de jogadores: **{len(all_players)}**\n"
                      f"Jogadores qualificados: **{len(valid_players)}**\n"
                      f"Última atualização: **Agora**",
                inline=True
            )
            
            # Footer
            embed.set_footer(
                text="Hawk Esports | Sistema de Ranking",
                icon_url=os.getenv('CLAN_LOGO_URL', '')
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard: {e}")
            
            # Embed de erro
            error_embed = discord.Embed(
                title="❌ Erro no Leaderboard",
                description="Não foi possível gerar o leaderboard no momento.",
                color=0xff0000
            )
            return error_embed
    
    async def generate_temporal_leaderboard(self, guild_id: str, period: str = 'daily', 
                                          mode: str = 'squad', rank_type: str = 'ranked', 
                                          limit: int = 10) -> discord.Embed:
        """Gera leaderboard temporal (diário, semanal, mensal)"""
        try:
            if period not in self.temporal_rankings:
                period = 'daily'
            
            # Buscar dados temporais
            temporal_data = self.storage.get_temporal_ranking_data(period)
            current_time = datetime.now()
            
            # Verificar se precisa resetar
            reset_hours = self.temporal_rankings[period]['reset_hours']
            if self._should_reset_temporal_ranking(temporal_data, reset_hours):
                temporal_data = self._reset_temporal_ranking(period)
            
            # Buscar todos os jogadores
            all_players = self.storage.get_all_players()
            
            # Calcular pontos temporais
            temporal_players = []
            for player_id, player_data in all_players.items():
                temporal_stats = self._calculate_temporal_stats(player_data, period, temporal_data)
                if temporal_stats['matches'] > 0:
                    temporal_players.append({
                        'player_id': player_id,
                        'name': player_data.get('pubg_name', 'Desconhecido'),
                        'rank': player_data.get(f'{rank_type}_rank', 'Sem rank'),
                        'points': temporal_stats['points'],
                        'kills': temporal_stats['kills'],
                        'wins': temporal_stats['wins'],
                        'matches': temporal_stats['matches'],
                        'kd': temporal_stats['kd']
                    })
            
            # Ordenar por pontos
            temporal_players.sort(key=lambda x: x['points'], reverse=True)
            
            # Criar embed
            period_title = self.temporal_rankings[period]['title']
            embed = discord.Embed(
                title=f"⏰ {period_title} - {mode.upper()}",
                description=f"**Hawk Esports** - Top {min(limit, len(temporal_players))} jogadores\n🔄 Atualização em tempo real",
                color=self.embed_color,
                timestamp=current_time
            )
            
            # Adicionar jogadores ao embed
            leaderboard_text = ""
            for i, player in enumerate(temporal_players[:limit], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                leaderboard_text += (
                    f"{medal} **{player['name']}** ({player['rank']})\n"
                    f"   Pontos: `{player['points']}` | Kills: `{player['kills']}` | "
                    f"Vitórias: `{player['wins']}`\n\n"
                )
            
            if leaderboard_text:
                embed.add_field(
                    name="📊 Ranking Temporal",
                    value=leaderboard_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📊 Ranking Temporal",
                    value="Nenhuma atividade registrada no período.",
                    inline=False
                )
            
            # Próximo reset
            next_reset = self._get_next_reset_time(period)
            embed.add_field(
                name="⏱️ Próximo Reset",
                value=f"<t:{int(next_reset.timestamp())}:R>",
                inline=True
            )
            
            # Sistema de pontuação
            embed.add_field(
                name="🎯 Sistema de Pontos",
                value="Kill: `+2pts` | Vitória: `+10pts`\nTop 10: `+5pts` | Dano: `+0.01pts/dano`",
                inline=True
            )
            
            embed.set_footer(
                text=f"Hawk Esports | {period_title}",
                icon_url=os.getenv('CLAN_LOGO_URL', '')
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard temporal: {e}")
            
            error_embed = discord.Embed(
                title="❌ Erro no Ranking Temporal",
                description="Não foi possível gerar o ranking temporal no momento.",
                color=0xff0000
            )
            return error_embed
    
    def _should_reset_temporal_ranking(self, temporal_data: Dict, reset_hours: int) -> bool:
        """Verifica se o ranking temporal deve ser resetado"""
        if not temporal_data or 'last_reset' not in temporal_data:
            return True
        
        last_reset = datetime.fromisoformat(temporal_data['last_reset'])
        time_diff = datetime.now() - last_reset
        return time_diff.total_seconds() >= (reset_hours * 3600)
    
    def _reset_temporal_ranking(self, period: str) -> Dict:
        """Reseta o ranking temporal"""
        temporal_data = {
            'last_reset': datetime.now().isoformat(),
            'players': {},
            'period': period
        }
        self.storage.save_temporal_ranking_data(period, temporal_data)
        return temporal_data
    
    def _calculate_temporal_stats(self, player_data: Dict, period: str, temporal_data: Dict) -> Dict:
        """Calcula estatísticas temporais do jogador"""
        player_id = player_data.get('player_id', '')
        temporal_player_data = temporal_data.get('players', {}).get(player_id, {
            'kills': 0, 'wins': 0, 'matches': 0, 'damage': 0, 'top10': 0
        })
        
        # Calcular pontos baseado no sistema
        points = (
            temporal_player_data['kills'] * 2 +  # 2 pontos por kill
            temporal_player_data['wins'] * 10 +   # 10 pontos por vitória
            temporal_player_data['top10'] * 5 +   # 5 pontos por top 10
            temporal_player_data['damage'] * 0.01 # 0.01 pontos por dano
        )
        
        kd = temporal_player_data['kills'] / max(temporal_player_data['matches'], 1)
        
        return {
            'points': round(points, 2),
            'kills': temporal_player_data['kills'],
            'wins': temporal_player_data['wins'],
            'matches': temporal_player_data['matches'],
            'kd': round(kd, 2)
        }
    
    def _get_next_reset_time(self, period: str) -> datetime:
        """Calcula o próximo horário de reset"""
        now = datetime.now()
        reset_hours = self.temporal_rankings[period]['reset_hours']
        
        if period == 'daily':
            # Reset à meia-noite
            next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif period == 'weekly':
            # Reset na segunda-feira à meia-noite
            days_ahead = 0 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
        else:  # monthly
            # Reset no primeiro dia do próximo mês
            if now.month == 12:
                next_reset = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_reset = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return next_reset
    
    def _calculate_basic_stats(self, season_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula estatísticas básicas a partir das season_stats detalhadas"""
        try:
            basic_stats = {
                'ranked': {'kd': 0, 'wins': 0, 'matches': 0, 'damage_avg': 0},
                'mm': {'kd': 0, 'wins': 0, 'matches': 0, 'damage_avg': 0}
            }
            
            for rank_type in ['ranked', 'mm']:
                type_stats = season_stats.get(rank_type, {})
                
                # Combinar estatísticas de todos os modos (solo, duo, squad)
                total_kills = 0
                total_deaths = 0
                total_wins = 0
                total_matches = 0
                total_damage = 0
                
                for mode in ['solo', 'duo', 'squad']:
                    mode_data = type_stats.get(mode, {})
                    total_kills += mode_data.get('kills', 0)
                    total_deaths += mode_data.get('deaths', 0)
                    total_wins += mode_data.get('wins', 0)
                    total_matches += mode_data.get('matches', 0)
                    total_damage += mode_data.get('damage_avg', 0) * mode_data.get('matches', 0)
                
                # Calcular estatísticas básicas
                basic_stats[rank_type] = {
                    'kd': round(total_kills / max(total_deaths, 1), 2),
                    'wins': total_wins,
                    'matches': total_matches,
                    'damage_avg': round(total_damage / max(total_matches, 1), 2)
                }
            
            return basic_stats
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas básicas: {e}")
            return {
                'ranked': {'kd': 0, 'wins': 0, 'matches': 0, 'damage_avg': 0},
                'mm': {'kd': 0, 'wins': 0, 'matches': 0, 'damage_avg': 0}
            }
    
    def _calculate_rank(self, stats: Dict[str, Any], rank_type: str) -> str:
        """Calcula rank baseado nas estatísticas"""
        try:
            # Usar squad como padrão para cálculo de rank
            mode_stats = stats.get(rank_type, {}).get('squad', {})
            
            kd = mode_stats.get('kd', 0)
            matches = mode_stats.get('matches', 0)
            
            # Verificar critério mínimo
            if matches < self.min_matches:
                return "Sem rank" if rank_type == 'ranked' else "Sem rank MM"
            
            # Determinar rank baseado no K/D
            thresholds = self.rank_thresholds[rank_type]
            
            for rank_name, threshold in thresholds.items():
                if kd >= threshold:
                    return rank_name
            
            # Fallback para o menor rank
            return list(thresholds.keys())[-1]
            
        except Exception as e:
            logger.error(f"Erro ao calcular rank: {e}")
            return "Erro"
    
    def _check_achievements(self, stats: Dict[str, Any], player_data: Dict[str, Any]) -> List[str]:
        """Verifica novas conquistas do jogador"""
        try:
            new_achievements = []
            current_achievements = player_data.get('achievements', [])
            
            # Combinar stats de todos os modos
            all_stats = {'matches': 0, 'wins': 0, 'kills': 0, 'damage_avg': 0, 'top10s': 0}
            
            for rank_type in ['ranked', 'mm']:
                for mode in ['solo', 'duo', 'squad']:
                    mode_stats = stats.get(rank_type, {}).get(mode, {})
                    all_stats['matches'] += mode_stats.get('matches', 0)
                    all_stats['wins'] += mode_stats.get('wins', 0)
                    all_stats['kills'] += mode_stats.get('kills', 0)
                    all_stats['top10s'] += mode_stats.get('top10s', 0)
                    
                    if mode_stats.get('damage_avg', 0) > all_stats['damage_avg']:
                        all_stats['damage_avg'] = mode_stats.get('damage_avg', 0)
            
            # Calcular K/D geral
            total_deaths = max(sum(
                stats.get(rt, {}).get(mode, {}).get('deaths', 0)
                for rt in ['ranked', 'mm']
                for mode in ['solo', 'duo', 'squad']
            ), 1)
            
            overall_kd = all_stats['kills'] / total_deaths
            
            # Verificar conquistas
            if 'first_win' not in current_achievements and all_stats['wins'] > 0:
                new_achievements.append('first_win')
            
            if 'kd_master' not in current_achievements and overall_kd >= 3.0:
                new_achievements.append('kd_master')
            
            if 'damage_dealer' not in current_achievements and all_stats['damage_avg'] >= 400:
                new_achievements.append('damage_dealer')
            
            if 'survivor' not in current_achievements and all_stats['matches'] > 0:
                top10_rate = (all_stats['top10s'] / all_stats['matches']) * 100
                if top10_rate >= 80:
                    new_achievements.append('survivor')
            
            if 'veteran' not in current_achievements and all_stats['matches'] >= 100:
                new_achievements.append('veteran')
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Erro ao verificar conquistas: {e}")
            return []
    
    async def _update_member_roles(self, member: discord.Member, ranked_rank: str, mm_rank: str):
        """Atualiza roles do membro no Discord"""
        try:
            guild = member.guild
            
            # Mapear ranks para roles
            rank_roles = {
                # Ranked
                'Predador': 'Predador',
                'Diamante': 'Diamante',
                'Ouro': 'Ouro',
                'Prata': 'Prata',
                'Bronze': 'Bronze',
                # MM
                'Mestre MM': 'Mestre MM',
                'Diamante MM': 'Diamante MM',
                'Ouro MM': 'Ouro MM',
                'Prata MM': 'Prata MM',
                'Bronze MM': 'Bronze MM'
            }
            
            # Remover roles de rank antigos
            roles_to_remove = []
            for role in member.roles:
                if role.name in rank_roles.values():
                    roles_to_remove.append(role)
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Atualização de rank")
            
            # Adicionar novos roles
            roles_to_add = []
            
            if ranked_rank in rank_roles:
                role = discord.utils.get(guild.roles, name=rank_roles[ranked_rank])
                if role:
                    roles_to_add.append(role)
            
            if mm_rank in rank_roles:
                role = discord.utils.get(guild.roles, name=rank_roles[mm_rank])
                if role:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Atualização de rank")
            
            logger.info(f"Roles atualizadas para {member.display_name}: {ranked_rank}, {mm_rank}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar roles de {member.display_name}: {e}")
    
    async def _notify_rank_change(self, member: discord.Member, old_ranked: str, new_ranked: str,
                                old_mm: str, new_mm: str, achievements: List[str]):
        """Notifica sobre mudanças de rank"""
        try:
            # Criar embed de notificação
            embed = discord.Embed(
                title="🎉 Atualização de Rank!",
                description=f"**{member.display_name}** teve seus ranks atualizados!",
                color=self.embed_color,
                timestamp=datetime.now()
            )
            
            # Adicionar mudanças de rank
            rank_changes = ""
            
            if old_ranked != new_ranked:
                rank_changes += f"**Ranked:** {old_ranked} → **{new_ranked}**\n"
            
            if old_mm != new_mm:
                rank_changes += f"**MM:** {old_mm} → **{new_mm}**\n"
            
            if rank_changes:
                embed.add_field(
                    name="📈 Mudanças de Rank",
                    value=rank_changes,
                    inline=False
                )
            
            # Adicionar conquistas
            if achievements:
                achievement_text = "\n".join([
                    f"{self.achievements[ach]['name']} - {self.achievements[ach]['description']}"
                    for ach in achievements if ach in self.achievements
                ])
                
                if achievement_text:
                    embed.add_field(
                        name="🏅 Novas Conquistas",
                        value=achievement_text,
                        inline=False
                    )
            
            embed.set_footer(text="Hawk Esports | Continue assim!")
            
            # Enviar DM para o jogador
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Não foi possível enviar DM para {member.display_name}")
            
            # Enviar no canal de anúncios se configurado
            announcements_channel = discord.utils.get(
                member.guild.channels, 
                name=os.getenv('ANNOUNCEMENTS_CHANNEL_NAME', 'anúncios')
            )
            
            if announcements_channel:
                await announcements_channel.send(f"{member.mention}", embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao notificar mudança de rank: {e}")
    
    def get_rank_info(self, player_id: str) -> Dict[str, Any]:
        """Retorna informações detalhadas de rank de um jogador"""
        try:
            player_data = self.storage.get_player(player_id)
            if not player_data:
                return {'error': 'Jogador não encontrado'}
            
            return {
                'player_name': player_data.get('pubg_name', 'Desconhecido'),
                'ranked_rank': player_data.get('ranked_rank', 'Sem rank'),
                'mm_rank': player_data.get('mm_rank', 'Sem rank MM'),
                'achievements': player_data.get('achievements', []),
                'last_update': player_data.get('last_stats_update', 'Nunca'),
                'season_stats': player_data.get('season_stats', {})
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar info de rank: {e}")
            return {'error': str(e)}