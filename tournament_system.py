#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Torneios Hawk Esports
Gerencia torneios internos com brackets automáticos

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import discord
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math
import random
from enum import Enum

logger = logging.getLogger('HawkBot.TournamentSystem')

class TournamentStatus(Enum):
    """Status possíveis de um torneio"""
    REGISTRATION = "registration"  # Inscrições abertas
    STARTING = "starting"          # Iniciando
    IN_PROGRESS = "in_progress"    # Em andamento
    FINISHED = "finished"          # Finalizado
    CANCELLED = "cancelled"        # Cancelado

class MatchStatus(Enum):
    """Status possíveis de uma partida"""
    PENDING = "pending"            # Aguardando
    IN_PROGRESS = "in_progress"    # Em andamento
    FINISHED = "finished"          # Finalizada
    WALKOVER = "walkover"          # W.O.

class TournamentSystem:
    """Sistema completo de gerenciamento de torneios"""
    
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        
        # Configurações
        self.max_participants = 64
        self.min_participants = 4
        self.registration_time = 30  # minutos
        self.match_timeout = 60      # minutos
        
        # Cache de torneios ativos
        self.active_tournaments = {}
        
        # Emojis para brackets
        self.bracket_emojis = {
            'winner': '🏆',
            'finalist': '🥈',
            'semifinal': '🥉',
            'quarter': '🎯',
            'round': '⚔️',
            'vs': '🆚',
            'tbd': '❓'
        }
        
        logger.info("Sistema de Torneios inicializado")
    
    async def create_tournament(self, guild_id: str, organizer_id: str, 
                              tournament_name: str, game_mode: str = "squad",
                              max_teams: int = 16) -> Dict[str, Any]:
        """Cria um novo torneio"""
        try:
            tournament_id = f"tournament_{guild_id}_{int(datetime.now().timestamp())}"
            
            tournament_data = {
                'id': tournament_id,
                'name': tournament_name,
                'guild_id': guild_id,
                'organizer_id': organizer_id,
                'game_mode': game_mode,
                'max_teams': min(max_teams, self.max_participants),
                'status': TournamentStatus.REGISTRATION.value,
                'participants': [],
                'brackets': {},
                'matches': {},
                'created_at': datetime.now().isoformat(),
                'registration_ends': (datetime.now() + timedelta(minutes=self.registration_time)).isoformat(),
                'prize_pool': [],
                'rules': self._get_default_rules(),
                'current_round': 0,
                'total_rounds': 0
            }
            
            # Salvar no storage
            self.storage.add_tournament(tournament_data)
            
            # Adicionar ao cache
            self.active_tournaments[tournament_id] = tournament_data
            
            logger.info(f"Torneio criado: {tournament_name} ({tournament_id})")
            return tournament_data
            
        except Exception as e:
            logger.error(f"Erro ao criar torneio: {e}")
            raise
    
    async def register_participant(self, tournament_id: str, user_id: str, 
                                 username: str, team_name: str = None) -> bool:
        """Registra um participante no torneio"""
        try:
            # Validar dados de entrada
            if not tournament_id or not user_id or not username:
                logger.warning("Dados inválidos para registro de participante")
                return False
            
            # Limitar tamanho dos campos
            username = username[:50]  # Máximo 50 caracteres
            if team_name:
                team_name = team_name[:30]  # Máximo 30 caracteres
            
            tournament = self.active_tournaments.get(tournament_id)
            if not tournament:
                logger.warning(f"Torneio não encontrado: {tournament_id}")
                return False
            
            # Verificar se inscrições estão abertas
            if tournament['status'] != TournamentStatus.REGISTRATION.value:
                return False
            
            # Verificar se já está registrado
            for participant in tournament['participants']:
                if participant['user_id'] == user_id:
                    return False
            
            # Verificar limite de participantes
            if len(tournament['participants']) >= tournament['max_teams']:
                return False
            
            # Adicionar participante
            participant_data = {
                'user_id': user_id,
                'username': username,
                'team_name': team_name or f"Team {username}",
                'registered_at': datetime.now().isoformat(),
                'seed': len(tournament['participants']) + 1,
                'stats': {
                    'matches_played': 0,
                    'matches_won': 0,
                    'matches_lost': 0,
                    'kills': 0,
                    'placement_points': 0
                }
            }
            
            tournament['participants'].append(participant_data)
            
            # Salvar no storage
            self.storage.update_tournament(tournament_id, tournament)
            
            # Verificar conquistas de participação em torneios
            if hasattr(self.bot, 'achievement_system'):
                try:
                    # Contar quantos torneios o usuário já participou
                    user_tournaments = 0
                    for t_id, t_data in self.active_tournaments.items():
                        for participant in t_data.get('participants', []):
                            if participant.get('user_id') == user_id:
                                user_tournaments += 1
                                break
                    
                    tournament_stats = {
                        'tournaments_participated': user_tournaments,
                        'tournament_wins': 0  # Será atualizado quando ganhar
                    }
                    
                    unlocked = self.bot.achievement_system.check_achievements(user_id, tournament_stats)
                    
                    # Enviar notificações de conquistas
                    if unlocked:
                        guild = self.bot.get_guild(int(tournament['guild_id']))
                        if guild:
                            general_channel = discord.utils.get(guild.channels, name='geral')
                            if general_channel:
                                for achievement in unlocked:
                                    await self.bot.achievement_system.send_achievement_notification(
                                        user_id, achievement, general_channel
                                    )
                except Exception as e:
                    logger.error(f"Erro ao verificar conquistas de torneio: {e}")
            
            logger.info(f"Participante registrado: {username} no torneio {tournament_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar participante: {e}")
            return False
    
    async def start_tournament(self, tournament_id: str) -> bool:
        """Inicia um torneio e gera os brackets"""
        try:
            tournament = self.active_tournaments.get(tournament_id)
            if not tournament:
                return False
            
            # Verificar se tem participantes suficientes
            participant_count = len(tournament['participants'])
            if participant_count < self.min_participants:
                return False
            
            # Atualizar status
            tournament['status'] = TournamentStatus.STARTING.value
            
            # Gerar brackets
            brackets = self._generate_brackets(tournament['participants'])
            tournament['brackets'] = brackets
            
            # Calcular número de rodadas
            tournament['total_rounds'] = math.ceil(math.log2(participant_count))
            tournament['current_round'] = 1
            
            # Gerar primeira rodada de partidas
            first_round_matches = self._generate_first_round_matches(brackets)
            tournament['matches'] = first_round_matches
            
            # Atualizar status para em andamento
            tournament['status'] = TournamentStatus.IN_PROGRESS.value
            tournament['started_at'] = datetime.now().isoformat()
            
            # Atualizar storage
            self.storage.update_tournament(tournament_id, tournament)
            
            logger.info(f"Torneio iniciado: {tournament_id} com {participant_count} participantes")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar torneio: {e}")
            return False
    
    def _generate_brackets(self, participants: List[Dict]) -> Dict:
        """Gera os brackets do torneio"""
        # Embaralhar participantes para randomizar
        shuffled_participants = participants.copy()
        random.shuffle(shuffled_participants)
        
        # Calcular próxima potência de 2
        participant_count = len(participants)
        bracket_size = 2 ** math.ceil(math.log2(participant_count))
        
        # Criar estrutura de brackets
        brackets = {
            'size': bracket_size,
            'rounds': {},
            'participants': shuffled_participants
        }
        
        # Gerar primeira rodada
        first_round = []
        for i in range(0, len(shuffled_participants), 2):
            if i + 1 < len(shuffled_participants):
                match = {
                    'player1': shuffled_participants[i],
                    'player2': shuffled_participants[i + 1],
                    'winner': None
                }
            else:
                # Bye (passa automaticamente)
                match = {
                    'player1': shuffled_participants[i],
                    'player2': None,
                    'winner': shuffled_participants[i]
                }
            first_round.append(match)
        
        brackets['rounds'][1] = first_round
        
        return brackets
    
    def _generate_first_round_matches(self, brackets: Dict) -> Dict:
        """Gera as partidas da primeira rodada"""
        matches = {}
        
        for i, bracket_match in enumerate(brackets['rounds'][1]):
            if bracket_match['player2'] is None:
                # Bye - não precisa de partida
                continue
            
            match_id = f"match_1_{i + 1}"
            match_data = {
                'id': match_id,
                'round': 1,
                'bracket_position': i,
                'player1': bracket_match['player1'],
                'player2': bracket_match['player2'],
                'status': MatchStatus.PENDING.value,
                'winner': None,
                'score': {'player1': 0, 'player2': 0},
                'created_at': datetime.now().isoformat(),
                'scheduled_time': None,
                'result_details': {}
            }
            
            matches[match_id] = match_data
        
        return matches
    
    def _get_default_rules(self) -> List[str]:
        """Retorna as regras padrão do torneio"""
        return [
            "🎯 **Modo de Jogo**: PUBG Squad/Duo/Solo",
            "⏰ **Tempo Limite**: 60 minutos por partida",
            "🏆 **Sistema**: Eliminação simples",
            "📊 **Pontuação**: Kills + Placement",
            "🚫 **Proibido**: Cheats, exploits, toxicidade",
            "📱 **Comprovação**: Screenshots obrigatórios",
            "⚖️ **Disputas**: Decisão dos organizadores",
            "🎁 **Prêmios**: Conforme disponibilidade"
        ]
    
    async def report_match_result(self, tournament_id: str, match_id: str,
                                winner_id: str, score_data: Dict) -> bool:
        """Reporta o resultado de uma partida"""
        try:
            tournament = self.active_tournaments.get(tournament_id)
            if not tournament or match_id not in tournament['matches']:
                return False
            
            match = tournament['matches'][match_id]
            
            # Verificar se a partida está em andamento
            if match['status'] != MatchStatus.IN_PROGRESS.value:
                return False
            
            # Atualizar resultado
            match['winner'] = winner_id
            match['status'] = MatchStatus.FINISHED.value
            match['finished_at'] = datetime.now().isoformat()
            match['score'] = score_data
            
            # Atualizar estatísticas dos participantes
            self._update_participant_stats(tournament, match, winner_id)
            
            # Verificar se a rodada terminou
            if self._is_round_finished(tournament, match['round']):
                await self._advance_to_next_round(tournament_id)
            
            # Atualizar storage
            self.storage.update_tournament(tournament_id, tournament)
            
            logger.info(f"Resultado reportado: {match_id} - Vencedor: {winner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao reportar resultado: {e}")
            return False
    
    def _update_participant_stats(self, tournament: Dict, match: Dict, winner_id: str):
        """Atualiza as estatísticas dos participantes"""
        for participant in tournament['participants']:
            if participant['user_id'] in [match['player1']['user_id'], match['player2']['user_id']]:
                participant['stats']['matches_played'] += 1
                
                if participant['user_id'] == winner_id:
                    participant['stats']['matches_won'] += 1
                else:
                    participant['stats']['matches_lost'] += 1
    
    def _is_round_finished(self, tournament: Dict, round_num: int) -> bool:
        """Verifica se uma rodada terminou"""
        round_matches = [m for m in tournament['matches'].values() 
                        if m['round'] == round_num]
        
        return all(m['status'] == MatchStatus.FINISHED.value for m in round_matches)
    
    async def _advance_to_next_round(self, tournament_id: str):
        """Avança para a próxima rodada"""
        tournament = self.active_tournaments[tournament_id]
        current_round = tournament['current_round']
        
        # Verificar se é a final
        if current_round >= tournament['total_rounds']:
            await self._finish_tournament(tournament_id)
            return
        
        # Gerar próxima rodada
        next_round = current_round + 1
        tournament['current_round'] = next_round
        
        # Obter vencedores da rodada atual
        current_round_matches = [m for m in tournament['matches'].values() 
                               if m['round'] == current_round]
        
        winners = [m['winner'] for m in current_round_matches if m['winner']]
        
        # Gerar partidas da próxima rodada
        next_round_matches = self._generate_next_round_matches(winners, next_round)
        tournament['matches'].update(next_round_matches)
        
        logger.info(f"Torneio {tournament_id} avançou para rodada {next_round}")
    
    def _generate_next_round_matches(self, winners: List[str], round_num: int) -> Dict:
        """Gera as partidas da próxima rodada"""
        matches = {}
        
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                match_id = f"match_{round_num}_{(i // 2) + 1}"
                match_data = {
                    'id': match_id,
                    'round': round_num,
                    'bracket_position': i // 2,
                    'player1': self._get_participant_by_id(winners[i]),
                    'player2': self._get_participant_by_id(winners[i + 1]),
                    'status': MatchStatus.PENDING.value,
                    'winner': None,
                    'score': {'player1': 0, 'player2': 0},
                    'created_at': datetime.now().isoformat(),
                    'scheduled_time': None,
                    'result_details': {}
                }
                
                matches[match_id] = match_data
        
        return matches
    
    def _get_participant_by_id(self, user_id: str) -> Dict:
        """Obtém dados do participante pelo ID"""
        # Buscar em todos os torneios ativos
        for tournament in self.active_tournaments.values():
            for participant in tournament.get('participants', []):
                if participant.get('user_id') == user_id:
                    return participant
        
        # Se não encontrar, retornar dados básicos
        return {'user_id': user_id, 'username': 'Player', 'team_name': f'Team_{user_id[:6]}'}
    
    async def _finish_tournament(self, tournament_id: str):
        """Finaliza um torneio"""
        tournament = self.active_tournaments[tournament_id]
        tournament['status'] = TournamentStatus.FINISHED.value
        tournament['finished_at'] = datetime.now().isoformat()
        
        # Determinar vencedor
        final_matches = [m for m in tournament['matches'].values() 
                        if m['round'] == tournament['total_rounds']]
        
        if final_matches:
            champion = final_matches[0]['winner']
            tournament['champion'] = champion
            
            # Verificar conquistas de vitória em torneio
            if hasattr(self.bot, 'achievement_system'):
                try:
                    # Contar vitórias em torneios do campeão
                    champion_wins = 1  # Esta vitória
                    for t_id, t_data in self.active_tournaments.items():
                        if t_data.get('status') == TournamentStatus.FINISHED.value:
                            if t_data.get('champion') == champion:
                                champion_wins += 1
                    
                    tournament_stats = {
                        'tournament_wins': champion_wins,
                        'tournaments_participated': champion_wins  # Pelo menos as que ganhou
                    }
                    
                    unlocked = self.bot.achievement_system.check_achievements(champion, tournament_stats)
                    
                    # Enviar notificações de conquistas
                    if unlocked:
                        guild = self.bot.get_guild(int(tournament['guild_id']))
                        if guild:
                            general_channel = discord.utils.get(guild.channels, name='geral')
                            if general_channel:
                                for achievement in unlocked:
                                    await self.bot.achievement_system.send_achievement_notification(
                                        champion, achievement, general_channel
                                    )
                except Exception as e:
                    logger.error(f"Erro ao verificar conquistas de vitória em torneio: {e}")
        
        logger.info(f"Torneio finalizado: {tournament_id}")
    
    async def get_tournament_bracket_embed(self, tournament_id: str) -> discord.Embed:
        """Gera embed com o bracket do torneio"""
        tournament = self.active_tournaments.get(tournament_id)
        if not tournament:
            return None
        
        embed = discord.Embed(
            title=f"🏆 {tournament['name']}",
            description=f"**Status**: {tournament['status'].title()}\n**Participantes**: {len(tournament['participants'])}",
            color=0x00ff00
        )
        
        # Adicionar informações das rodadas
        for round_num in range(1, tournament['current_round'] + 1):
            round_matches = [m for m in tournament['matches'].values() 
                           if m['round'] == round_num]
            
            if round_matches:
                round_text = ""
                for match in round_matches:
                    p1_name = match['player1']['team_name'][:15]
                    p2_name = match['player2']['team_name'][:15]
                    
                    if match['status'] == MatchStatus.FINISHED.value:
                        winner_name = self._get_participant_by_id(match['winner'])['team_name'][:15]
                        round_text += f"~~{p1_name}~~ vs ~~{p2_name}~~ → **{winner_name}** {self.bracket_emojis['winner']}\n"
                    else:
                        round_text += f"{p1_name} {self.bracket_emojis['vs']} {p2_name}\n"
                
                embed.add_field(
                    name=f"Rodada {round_num}",
                    value=round_text or "Aguardando...",
                    inline=False
                )
        
        # Adicionar timestamp
        embed.timestamp = datetime.now()
        embed.set_footer(text="Hawk Esports Tournament System")
        
        return embed
    
    async def get_active_tournaments(self, guild_id: str) -> List[Dict]:
        """Retorna torneios ativos de um servidor"""
        return [t for t in self.active_tournaments.values() 
                if t['guild_id'] == guild_id and 
                t['status'] in [TournamentStatus.REGISTRATION.value, 
                              TournamentStatus.IN_PROGRESS.value]]
    
    async def cancel_tournament(self, tournament_id: str, reason: str = "Cancelado pelo organizador") -> bool:
        """Cancela um torneio"""
        try:
            tournament = self.active_tournaments.get(tournament_id)
            if not tournament:
                return False
            
            tournament['status'] = TournamentStatus.CANCELLED.value
            tournament['cancelled_at'] = datetime.now().isoformat()
            tournament['cancel_reason'] = reason
            
            # Atualizar storage
            self.storage.update_tournament(tournament_id, tournament)
            
            logger.info(f"Torneio cancelado: {tournament_id} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao cancelar torneio: {e}")
            return False
    
    # ==================== MÉTODOS DE COMANDO DO DISCORD ====================
    
    async def create_tournament_command(self, interaction: discord.Interaction, nome: str, 
                                      tipo: str, max_participantes: int = 16, premio: str = None):
        """Comando Discord para criar torneio"""
        try:
            await interaction.response.defer()
            
            # Verificar permissões (apenas administradores)
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acesso Negado",
                    description="Apenas administradores podem criar torneios.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Criar torneio
            tournament_data = await self.create_tournament(
                guild_id=str(interaction.guild.id),
                organizer_id=str(interaction.user.id),
                tournament_name=nome,
                game_mode=tipo,
                max_teams=max_participantes
            )
            
            # Criar embed de confirmação
            embed = discord.Embed(
                title="🏆 Torneio Criado!",
                description=f"**{nome}** foi criado com sucesso!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Detalhes",
                value=f"**ID**: `{tournament_data['id']}`\n" +
                      f"**Tipo**: {tipo.replace('_', ' ').title()}\n" +
                      f"**Max Participantes**: {max_participantes}\n" +
                      f"**Status**: Inscrições Abertas",
                inline=False
            )
            
            if premio:
                embed.add_field(
                    name="🎁 Prêmio",
                    value=premio,
                    inline=False
                )
            
            embed.add_field(
                name="📝 Como Participar",
                value=f"Use `/participar_torneio {tournament_data['id']}`",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports Tournament System")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando criar_torneio: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao criar o torneio.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def join_tournament_command(self, interaction: discord.Interaction, torneio_id: str):
        """Comando Discord para participar de torneio"""
        try:
            await interaction.response.defer()
            
            # Registrar participante
            result = await self.register_participant(
                tournament_id=torneio_id,
                user_id=str(interaction.user.id),
                username=interaction.user.display_name,
                team_name=f"Team {interaction.user.display_name}"
            )
            
            if result:
                embed = discord.Embed(
                    title="✅ Inscrição Realizada!",
                    description=f"Você foi inscrito no torneio com sucesso!",
                    color=discord.Color.green()
                )
                
                # Obter dados do torneio
                tournament = self.active_tournaments.get(torneio_id)
                if tournament:
                    embed.add_field(
                        name="🏆 Torneio",
                        value=tournament['name'],
                        inline=True
                    )
                    embed.add_field(
                        name="👥 Participantes",
                        value=f"{len(tournament['participants'])}/{tournament['max_teams']}",
                        inline=True
                    )
            else:
                embed = discord.Embed(
                    title="❌ Falha na Inscrição",
                    description="Não foi possível se inscrever no torneio.\n" +
                              "Possíveis motivos:\n" +
                              "• Torneio não encontrado\n" +
                              "• Inscrições fechadas\n" +
                              "• Já está inscrito\n" +
                              "• Torneio lotado",
                    color=discord.Color.red()
                )
            
            embed.set_footer(text="Hawk Esports Tournament System")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando participar_torneio: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao se inscrever no torneio.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def list_tournaments_command(self, interaction: discord.Interaction):
        """Comando Discord para listar torneios ativos"""
        try:
            await interaction.response.defer()
            
            # Obter torneios ativos
            active_tournaments = await self.get_active_tournaments(str(interaction.guild.id))
            
            embed = discord.Embed(
                title="🏆 Torneios Ativos",
                color=discord.Color.gold()
            )
            
            if not active_tournaments:
                embed.description = "Nenhum torneio ativo no momento."
            else:
                embed.description = f"**{len(active_tournaments)}** torneio(s) ativo(s)"
                
                for tournament in active_tournaments:
                    status_emoji = {
                        'registration': '📝',
                        'in_progress': '⚔️',
                        'starting': '🚀'
                    }.get(tournament['status'], '❓')
                    
                    participants_info = f"{len(tournament['participants'])}/{tournament['max_teams']}"
                    
                    embed.add_field(
                        name=f"{status_emoji} {tournament['name']}",
                        value=f"**ID**: `{tournament['id']}`\n" +
                              f"**Status**: {tournament['status'].replace('_', ' ').title()}\n" +
                              f"**Participantes**: {participants_info}\n" +
                              f"**Criado**: <t:{int(datetime.fromisoformat(tournament['created_at']).timestamp())}:R>",
                        inline=True
                    )
            
            embed.set_footer(text="Hawk Esports Tournament System")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando listar_torneios: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao listar os torneios.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def show_bracket_command(self, interaction: discord.Interaction, torneio_id: str):
        """Comando Discord para mostrar bracket do torneio"""
        try:
            await interaction.response.defer()
            
            # Gerar embed do bracket
            embed = await self.get_tournament_bracket_embed(torneio_id)
            
            if embed:
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Torneio Não Encontrado",
                    description="O torneio especificado não foi encontrado.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro no comando ver_bracket: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao mostrar o bracket.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def report_match_result_command(self, interaction: discord.Interaction, 
                                        torneio_id: str, partida_id: str, vencedor: discord.Member):
        """Comando Discord para reportar resultado de partida"""
        try:
            await interaction.response.defer()
            
            # Verificar permissões (apenas administradores)
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acesso Negado",
                    description="Apenas administradores podem reportar resultados.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Reportar resultado
            score_data = {'player1': 0, 'player2': 1}  # Dados básicos de pontuação
            result = await self.report_match_result(
                tournament_id=torneio_id,
                match_id=partida_id,
                winner_id=str(vencedor.id),
                score_data=score_data
            )
            
            if result:
                embed = discord.Embed(
                    title="✅ Resultado Reportado!",
                    description=f"Resultado da partida `{partida_id}` foi registrado.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🏆 Vencedor",
                    value=vencedor.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Torneio",
                    value=f"`{torneio_id}`",
                    inline=True
                )
            else:
                embed = discord.Embed(
                    title="❌ Falha ao Reportar",
                    description="Não foi possível reportar o resultado.\n" +
                              "Possíveis motivos:\n" +
                              "• Torneio não encontrado\n" +
                              "• Partida não encontrada\n" +
                              "• Partida já finalizada",
                    color=discord.Color.red()
                )
            
            embed.set_footer(text="Hawk Esports Tournament System")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando resultado_partida: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao reportar o resultado.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)