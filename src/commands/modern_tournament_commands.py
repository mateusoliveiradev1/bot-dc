#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos Modernizados de Torneios
Comandos Discord para o sistema de torneios automatizados

Autor: AI Assistant
Versão: 3.0.0
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

import discord
from discord import app_commands
from discord.ext import commands

# Imports condicionais para compatibilidade
try:
    from src.features.tournaments.modern_system import (
        ModernTournamentSystem, TournamentModel, TournamentStatus, 
        MatchStatus, TournamentType, GameMode
    )
except ImportError:
    ModernTournamentSystem = None
    TournamentModel = None
    TournamentStatus = None
    MatchStatus = None
    TournamentType = None
    GameMode = None

# Imports dos sistemas core modernos
try:
    from src.core.smart_cache import SmartCache
    from src.core.secure_logger import SecureLogger
    from src.core.typed_config import TypedConfig
    from src.core.metrics_system import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
except ImportError:
    # Fallback para sistemas não disponíveis
    SmartCache = None
    SecureLogger = None
    TypedConfig = None
    MetricsCollector = None
    DataValidator = None
    EventSystem = None
    RateLimiter = None

class ModernTournamentCommands(commands.Cog):
    """Comandos modernizados para sistema de torneios"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Inicializar sistemas core (com fallback)
        self.cache = SmartCache(namespace="tournament_commands") if SmartCache else {}
        self.logger = SecureLogger("TournamentCommands") if SecureLogger else None
        self.config = TypedConfig() if TypedConfig else None
        self.metrics = MetricsCollector() if MetricsCollector else None
        self.validator = DataValidator() if DataValidator else None
        self.events = EventSystem() if EventSystem else None
        self.rate_limiter = RateLimiter() if RateLimiter else None
        
        # Sistema de torneios
        self.tournament_system = None
        if ModernTournamentSystem:
            self.tournament_system = ModernTournamentSystem(bot)
        
        # Emojis para interface
        self.emojis = {
            'trophy': '🏆',
            'medal_gold': '🥇',
            'medal_silver': '🥈',
            'medal_bronze': '🥉',
            'vs': '🆚',
            'sword': '⚔️',
            'target': '🎯',
            'fire': '🔥',
            'crown': '👑',
            'star': '⭐',
            'warning': '⚠️',
            'check': '✅',
            'cross': '❌',
            'clock': '⏰',
            'calendar': '📅',
            'users': '👥',
            'gear': '⚙️',
            'loading': '⏳',
            'info': 'ℹ️'
        }
        
        # Cores para embeds
        self.colors = {
            'success': 0x00ff00,
            'error': 0xff0000,
            'warning': 0xffaa00,
            'info': 0x0099ff,
            'tournament': 0x9932cc,
            'match': 0xff6347
        }
        
        if self.logger:
            self.logger.info("Comandos Modernizados de Torneios inicializados")
    
    def _create_embed(
        self, 
        title: str, 
        description: str = None, 
        color: int = None, 
        embed_type: str = 'info'
    ) -> discord.Embed:
        """Cria embed padronizado"""
        if color is None:
            color = self.colors.get(embed_type, self.colors['info'])
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        embed.set_footer(
            text="Sistema de Torneios Modernizado",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed
    
    def _create_error_embed(self, message: str) -> discord.Embed:
        """Cria embed de erro padronizado"""
        return self._create_embed(
            f"{self.emojis['cross']} Erro",
            message,
            embed_type='error'
        )
    
    def _create_success_embed(self, message: str) -> discord.Embed:
        """Cria embed de sucesso padronizado"""
        return self._create_embed(
            f"{self.emojis['check']} Sucesso",
            message,
            embed_type='success'
        )
    
    def _create_warning_embed(self, message: str) -> discord.Embed:
        """Cria embed de aviso padronizado"""
        return self._create_embed(
            f"{self.emojis['warning']} Aviso",
            message,
            embed_type='warning'
        )
    
    async def _check_permissions(self, interaction: discord.Interaction, required_permission: str = None) -> bool:
        """Verifica permissões do usuário"""
        if not required_permission:
            return True
        
        if required_permission == 'manage_guild':
            return interaction.user.guild_permissions.manage_guild
        elif required_permission == 'administrator':
            return interaction.user.guild_permissions.administrator
        elif required_permission == 'manage_channels':
            return interaction.user.guild_permissions.manage_channels
        
        return False
    
    async def _apply_rate_limit(self, user_id: str, command_name: str) -> bool:
        """Aplica rate limiting"""
        if not self.rate_limiter:
            return True
        
        return await self.rate_limiter.check_rate_limit(
            f"{command_name}:{user_id}",
            max_requests=5,
            window_seconds=300
        )
    
    @app_commands.command(
        name="criar_torneio",
        description="Cria um novo torneio no servidor"
    )
    @app_commands.describe(
        nome="Nome do torneio",
        tipo="Tipo de torneio",
        modo_jogo="Modo de jogo",
        max_participantes="Máximo de participantes (4-64)",
        min_participantes="Mínimo de participantes (2-32)",
        tempo_registro="Tempo para registro em minutos (5-120)"
    )
    async def criar_torneio(
        self,
        interaction: discord.Interaction,
        nome: str,
        tipo: str = "single_elimination",
        modo_jogo: str = "squad",
        max_participantes: int = 16,
        min_participantes: int = 4,
        tempo_registro: int = 30
    ):
        """Comando para criar torneio"""
        try:
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar permissões
            if not await self._check_permissions(interaction, 'manage_guild'):
                embed = self._create_error_embed(
                    "Você precisa da permissão 'Gerenciar Servidor' para criar torneios."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "criar_torneio"):
                embed = self._create_warning_embed(
                    "Você está criando torneios muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validar parâmetros
            if len(nome) < 3 or len(nome) > 100:
                embed = self._create_error_embed(
                    "O nome do torneio deve ter entre 3 e 100 caracteres."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if max_participantes < 4 or max_participantes > 64:
                embed = self._create_error_embed(
                    "O máximo de participantes deve estar entre 4 e 64."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if min_participantes < 2 or min_participantes > max_participantes:
                embed = self._create_error_embed(
                    "O mínimo de participantes deve estar entre 2 e o máximo definido."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if tempo_registro < 5 or tempo_registro > 120:
                embed = self._create_error_embed(
                    "O tempo de registro deve estar entre 5 e 120 minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Converter tipos
            try:
                tournament_type = TournamentType(tipo) if TournamentType else tipo
                game_mode = GameMode(modo_jogo) if GameMode else modo_jogo
            except ValueError:
                embed = self._create_error_embed(
                    "Tipo de torneio ou modo de jogo inválido."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Resposta inicial
            embed = self._create_embed(
                f"{self.emojis['loading']} Criando Torneio",
                "Configurando o torneio, aguarde...",
                embed_type='info'
            )
            await interaction.response.send_message(embed=embed)
            
            # Criar torneio
            tournament = await self.tournament_system.create_tournament(
                guild_id=str(interaction.guild.id),
                organizer_id=str(interaction.user.id),
                name=nome,
                tournament_type=tournament_type,
                game_mode=game_mode,
                max_participants=max_participantes,
                min_participants=min_participantes,
                settings={
                    'registration_time_minutes': tempo_registro
                }
            )
            
            if not tournament:
                embed = self._create_error_embed(
                    "Erro ao criar o torneio. Tente novamente."
                )
                await interaction.edit_original_response(embed=embed)
                return
            
            # Embed de sucesso
            embed = self._create_embed(
                f"{self.emojis['trophy']} Torneio Criado!",
                f"**{nome}** foi criado com sucesso!",
                embed_type='tournament'
            )
            
            embed.add_field(
                name=f"{self.emojis['info']} Informações",
                value=(
                    f"**ID:** `{tournament.id}`\n"
                    f"**Tipo:** {tipo.replace('_', ' ').title()}\n"
                    f"**Modo:** {modo_jogo.title()}\n"
                    f"**Participantes:** {min_participantes}-{max_participantes}\n"
                    f"**Registro até:** <t:{int((datetime.now() + timedelta(minutes=tempo_registro)).timestamp())}:R>"
                ),
                inline=True
            )
            
            embed.add_field(
                name=f"{self.emojis['users']} Participação",
                value=(
                    f"Use `/participar_torneio` para se inscrever\n"
                    f"Use `/torneios` para ver torneios ativos\n"
                    f"Use `/bracket` para ver o bracket"
                ),
                inline=True
            )
            
            embed.add_field(
                name=f"{self.emojis['gear']} Status",
                value=(
                    f"**Status:** {tournament.status.value.title()}\n"
                    f"**Inscritos:** 0/{max_participantes}\n"
                    f"**Organizador:** {interaction.user.mention}"
                ),
                inline=False
            )
            
            await interaction.edit_original_response(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournament_commands_used')
                await self.metrics.increment('tournaments_created_via_command')
            
            if self.logger:
                self.logger.info(
                    f"Torneio criado via comando: {nome} por {interaction.user}",
                    extra={
                        'tournament_id': tournament.id,
                        'guild_id': interaction.guild.id,
                        'user_id': interaction.user.id
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao criar torneio: {str(e)}"
            )
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando criar_torneio: {e}")
    
    @app_commands.command(
        name="participar_torneio",
        description="Participa de um torneio ativo"
    )
    @app_commands.describe(
        torneio_id="ID do torneio (opcional, mostra lista se não fornecido)",
        nome_equipe="Nome da sua equipe (opcional)"
    )
    async def participar_torneio(
        self,
        interaction: discord.Interaction,
        torneio_id: str = None,
        nome_equipe: str = None
    ):
        """Comando para participar de torneio"""
        try:
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "participar_torneio"):
                embed = self._create_warning_embed(
                    "Você está tentando participar muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Se não forneceu ID, mostrar lista de torneios
            if not torneio_id:
                active_tournaments = await self.tournament_system.get_active_tournaments(
                    str(interaction.guild.id)
                )
                
                if not active_tournaments:
                    embed = self._create_embed(
                        f"{self.emojis['info']} Nenhum Torneio Ativo",
                        "Não há torneios com inscrições abertas no momento.",
                        embed_type='info'
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                embed = self._create_embed(
                    f"{self.emojis['trophy']} Torneios Disponíveis",
                    "Escolha um torneio para participar:",
                    embed_type='tournament'
                )
                
                for tournament in active_tournaments[:5]:  # Limitar a 5
                    if tournament.status == TournamentStatus.REGISTRATION:
                        participants_count = len(tournament.participants)
                        embed.add_field(
                            name=f"{tournament.name}",
                            value=(
                                f"**ID:** `{tournament.id}`\n"
                                f"**Participantes:** {participants_count}/{tournament.max_participants}\n"
                                f"**Tipo:** {tournament.tournament_type.value.replace('_', ' ').title()}\n"
                                f"**Registro até:** <t:{int(tournament.registration_ends.timestamp())}:R>"
                            ),
                            inline=True
                        )
                
                embed.add_field(
                    name=f"{self.emojis['info']} Como Participar",
                    value="Use `/participar_torneio torneio_id:<ID>` para se inscrever",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Resposta inicial
            embed = self._create_embed(
                f"{self.emojis['loading']} Processando Inscrição",
                "Verificando torneio e processando sua inscrição...",
                embed_type='info'
            )
            await interaction.response.send_message(embed=embed)
            
            # Tentar registrar participante
            success = await self.tournament_system.register_participant(
                tournament_id=torneio_id,
                user_id=str(interaction.user.id),
                username=interaction.user.display_name,
                team_name=nome_equipe,
                discord_tag=str(interaction.user)
            )
            
            if success:
                # Obter informações atualizadas do torneio
                tournament = await self.tournament_system._get_tournament(torneio_id)
                
                embed = self._create_success_embed(
                    f"Você foi inscrito no torneio **{tournament.name}**!"
                )
                
                participants_count = len(tournament.participants)
                embed.add_field(
                    name=f"{self.emojis['users']} Status da Inscrição",
                    value=(
                        f"**Participantes:** {participants_count}/{tournament.max_participants}\n"
                        f"**Sua Equipe:** {nome_equipe or f'Team {interaction.user.display_name}'}\n"
                        f"**Posição:** #{participants_count}"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name=f"{self.emojis['info']} Próximos Passos",
                    value=(
                        f"• Aguarde o início do torneio\n"
                        f"• Use `/bracket` para ver o bracket\n"
                        f"• Fique atento às notificações"
                    ),
                    inline=True
                )
                
                # Verificar se o torneio pode iniciar
                if participants_count >= tournament.max_participants:
                    embed.add_field(
                        name=f"{self.emojis['fire']} Torneio Completo!",
                        value="O torneio atingiu o máximo de participantes e iniciará em breve!",
                        inline=False
                    )
                
                await interaction.edit_original_response(embed=embed)
                
                # Métricas
                if self.metrics:
                    await self.metrics.increment('tournament_registrations_via_command')
            
            else:
                embed = self._create_error_embed(
                    "Não foi possível inscrever você no torneio."
                )
                
                embed.add_field(
                    name=f"{self.emojis['info']} Possíveis Motivos",
                    value=(
                        "• Torneio não encontrado ou inválido\n"
                        "• Inscrições fechadas\n"
                        "• Você já está inscrito\n"
                        "• Torneio lotado\n"
                        "• Limite de tentativas excedido"
                    ),
                    inline=False
                )
                
                await interaction.edit_original_response(embed=embed)
            
            if self.logger:
                self.logger.info(
                    f"Tentativa de inscrição: {interaction.user} -> {torneio_id} (sucesso: {success})",
                    extra={
                        'tournament_id': torneio_id,
                        'user_id': interaction.user.id,
                        'success': success
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao processar inscrição: {str(e)}"
            )
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando participar_torneio: {e}")
    
    @app_commands.command(
        name="torneios",
        description="Lista todos os torneios ativos do servidor"
    )
    async def listar_torneios(self, interaction: discord.Interaction):
        """Comando para listar torneios"""
        try:
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "torneios"):
                embed = self._create_warning_embed(
                    "Você está consultando torneios muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Obter torneios ativos
            active_tournaments = await self.tournament_system.get_active_tournaments(
                str(interaction.guild.id)
            )
            
            if not active_tournaments:
                embed = self._create_embed(
                    f"{self.emojis['info']} Nenhum Torneio Ativo",
                    "Não há torneios ativos no momento neste servidor.",
                    embed_type='info'
                )
                
                embed.add_field(
                    name=f"{self.emojis['trophy']} Criar Torneio",
                    value="Use `/criar_torneio` para criar um novo torneio!",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                return
            
            # Criar embed com lista de torneios
            embed = self._create_embed(
                f"{self.emojis['trophy']} Torneios Ativos ({len(active_tournaments)})",
                f"Torneios ativos no servidor **{interaction.guild.name}**",
                embed_type='tournament'
            )
            
            for i, tournament in enumerate(active_tournaments[:10], 1):  # Limitar a 10
                status_emoji = {
                    'registration': self.emojis['calendar'],
                    'starting': self.emojis['loading'],
                    'in_progress': self.emojis['fire'],
                    'paused': self.emojis['warning']
                }.get(tournament.status.value, self.emojis['info'])
                
                participants_count = len(tournament.participants)
                
                field_value = (
                    f"**Status:** {status_emoji} {tournament.status.value.replace('_', ' ').title()}\n"
                    f"**Participantes:** {participants_count}/{tournament.max_participants}\n"
                    f"**Tipo:** {tournament.tournament_type.value.replace('_', ' ').title()}\n"
                    f"**ID:** `{tournament.id}`"
                )
                
                if tournament.status == TournamentStatus.REGISTRATION and tournament.registration_ends:
                    field_value += f"\n**Registro até:** <t:{int(tournament.registration_ends.timestamp())}:R>"
                elif tournament.started_at:
                    field_value += f"\n**Iniciado:** <t:{int(tournament.started_at.timestamp())}:R>"
                
                embed.add_field(
                    name=f"{i}. {tournament.name}",
                    value=field_value,
                    inline=True
                )
            
            if len(active_tournaments) > 10:
                embed.add_field(
                    name=f"{self.emojis['info']} Mais Torneios",
                    value=f"E mais {len(active_tournaments) - 10} torneios...",
                    inline=False
                )
            
            embed.add_field(
                name=f"{self.emojis['gear']} Comandos Úteis",
                value=(
                    f"• `/participar_torneio` - Participar de um torneio\n"
                    f"• `/bracket` - Ver bracket de um torneio\n"
                    f"• `/stats_torneio` - Ver estatísticas detalhadas"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournament_list_commands_used')
            
            if self.logger:
                self.logger.info(
                    f"Lista de torneios consultada por {interaction.user}",
                    extra={
                        'guild_id': interaction.guild.id,
                        'user_id': interaction.user.id,
                        'tournaments_count': len(active_tournaments)
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao listar torneios: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando torneios: {e}")
    
    @app_commands.command(
        name="bracket",
        description="Mostra o bracket de um torneio"
    )
    @app_commands.describe(
        torneio_id="ID do torneio"
    )
    async def mostrar_bracket(
        self,
        interaction: discord.Interaction,
        torneio_id: str
    ):
        """Comando para mostrar bracket"""
        try:
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "bracket"):
                embed = self._create_warning_embed(
                    "Você está consultando brackets muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Obter torneio
            tournament = await self.tournament_system._get_tournament(torneio_id)
            
            if not tournament:
                embed = self._create_error_embed(
                    "Torneio não encontrado ou inválido."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar se é do mesmo servidor
            if tournament.guild_id != str(interaction.guild.id):
                embed = self._create_error_embed(
                    "Este torneio não pertence a este servidor."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Criar embed do bracket
            embed = self._create_embed(
                f"{self.emojis['trophy']} Bracket - {tournament.name}",
                f"**Status:** {tournament.status.value.replace('_', ' ').title()}",
                embed_type='tournament'
            )
            
            # Informações gerais
            participants_count = len(tournament.participants)
            embed.add_field(
                name=f"{self.emojis['info']} Informações Gerais",
                value=(
                    f"**Participantes:** {participants_count}/{tournament.max_participants}\n"
                    f"**Tipo:** {tournament.tournament_type.value.replace('_', ' ').title()}\n"
                    f"**Rodada Atual:** {tournament.current_round}/{tournament.total_rounds}\n"
                    f"**Partidas:** {len(tournament.matches)}"
                ),
                inline=True
            )
            
            # Status do torneio
            status_info = ""
            if tournament.status == TournamentStatus.REGISTRATION:
                if tournament.registration_ends:
                    status_info = f"**Registro até:** <t:{int(tournament.registration_ends.timestamp())}:R>"
            elif tournament.status == TournamentStatus.IN_PROGRESS:
                if tournament.started_at:
                    status_info = f"**Iniciado:** <t:{int(tournament.started_at.timestamp())}:R>"
            elif tournament.status == TournamentStatus.FINISHED:
                if tournament.champion:
                    champion_name = "Desconhecido"
                    for participant in tournament.participants:
                        if participant.user_id == tournament.champion:
                            champion_name = participant.username
                            break
                    status_info = f"**Campeão:** {self.emojis['crown']} {champion_name}"
            
            if status_info:
                embed.add_field(
                    name=f"{self.emojis['calendar']} Status",
                    value=status_info,
                    inline=True
                )
            
            # Mostrar partidas por rodada
            if tournament.matches:
                rounds = {}
                for match in tournament.matches.values():
                    round_num = match.round_number
                    if round_num not in rounds:
                        rounds[round_num] = []
                    rounds[round_num].append(match)
                
                # Mostrar até 3 rodadas
                for round_num in sorted(rounds.keys())[:3]:
                    matches = rounds[round_num]
                    round_text = ""
                    
                    for i, match in enumerate(matches[:5], 1):  # Máximo 5 partidas por rodada
                        player1_name = match.player1.username if match.player1 else "TBD"
                        player2_name = match.player2.username if match.player2 else "BYE"
                        
                        status_emoji = {
                            'pending': self.emojis['clock'],
                            'ready': self.emojis['target'],
                            'in_progress': self.emojis['fire'],
                            'finished': self.emojis['check'],
                            'walkover': self.emojis['warning'],
                            'disputed': self.emojis['cross']
                        }.get(match.status.value, self.emojis['info'])
                        
                        if match.status == MatchStatus.FINISHED and match.winner:
                            winner_name = player1_name if match.winner == match.player1.user_id else player2_name
                            round_text += f"{status_emoji} **{winner_name}** vs ~~{player2_name if match.winner == match.player1.user_id else player1_name}~~\n"
                        else:
                            round_text += f"{status_emoji} {player1_name} {self.emojis['vs']} {player2_name}\n"
                    
                    if len(matches) > 5:
                        round_text += f"... e mais {len(matches) - 5} partidas\n"
                    
                    embed.add_field(
                        name=f"{self.emojis['sword']} Rodada {round_num}",
                        value=round_text or "Nenhuma partida",
                        inline=False
                    )
            
            else:
                embed.add_field(
                    name=f"{self.emojis['info']} Bracket",
                    value="Bracket ainda não foi gerado. Aguarde o início do torneio.",
                    inline=False
                )
            
            # Participantes (se em registro)
            if tournament.status == TournamentStatus.REGISTRATION and tournament.participants:
                participants_text = ""
                for i, participant in enumerate(tournament.participants[:10], 1):
                    participants_text += f"{i}. {participant.username} ({participant.team_name})\n"
                
                if len(tournament.participants) > 10:
                    participants_text += f"... e mais {len(tournament.participants) - 10} participantes"
                
                embed.add_field(
                    name=f"{self.emojis['users']} Participantes Inscritos",
                    value=participants_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('bracket_commands_used')
            
            if self.logger:
                self.logger.info(
                    f"Bracket consultado: {torneio_id} por {interaction.user}",
                    extra={
                        'tournament_id': torneio_id,
                        'user_id': interaction.user.id
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao mostrar bracket: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando bracket: {e}")
    
    @app_commands.command(
        name="stats_torneio",
        description="Mostra estatísticas detalhadas de um torneio"
    )
    @app_commands.describe(
        torneio_id="ID do torneio"
    )
    async def stats_torneio(
        self,
        interaction: discord.Interaction,
        torneio_id: str
    ):
        """Comando para mostrar estatísticas do torneio"""
        try:
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "stats_torneio"):
                embed = self._create_warning_embed(
                    "Você está consultando estatísticas muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Obter estatísticas
            stats = await self.tournament_system.get_tournament_stats(torneio_id)
            
            if not stats:
                embed = self._create_error_embed(
                    "Torneio não encontrado ou estatísticas indisponíveis."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Criar embed de estatísticas
            embed = self._create_embed(
                f"{self.emojis['trophy']} Estatísticas - {stats['name']}",
                f"Estatísticas detalhadas do torneio",
                embed_type='tournament'
            )
            
            # Informações básicas
            embed.add_field(
                name=f"{self.emojis['info']} Informações Básicas",
                value=(
                    f"**ID:** `{stats['tournament_id']}`\n"
                    f"**Status:** {stats['status'].replace('_', ' ').title()}\n"
                    f"**Participantes:** {stats['participant_count']}\n"
                    f"**Criado:** <t:{int(stats['created_at'].timestamp())}:R>"
                ),
                inline=True
            )
            
            # Progresso
            embed.add_field(
                name=f"{self.emojis['fire']} Progresso",
                value=(
                    f"**Rodada Atual:** {stats['current_round']}/{stats['total_rounds']}\n"
                    f"**Partidas Total:** {stats['matches_total']}\n"
                    f"**Partidas Finalizadas:** {stats['matches_finished']}\n"
                    f"**Progresso:** {(stats['matches_finished']/max(stats['matches_total'], 1)*100):.1f}%"
                ),
                inline=True
            )
            
            # Datas importantes
            dates_info = ""
            if stats.get('started_at'):
                dates_info += f"**Iniciado:** <t:{int(stats['started_at'].timestamp())}:R>\n"
            if stats.get('finished_at'):
                dates_info += f"**Finalizado:** <t:{int(stats['finished_at'].timestamp())}:R>\n"
            if stats.get('champion'):
                champion_name = "Desconhecido"
                if 'participants' in stats:
                    for participant in stats['participants']:
                        if participant['user_id'] == stats['champion']:
                            champion_name = participant['username']
                            break
                dates_info += f"**Campeão:** {self.emojis['crown']} {champion_name}"
            
            if dates_info:
                embed.add_field(
                    name=f"{self.emojis['calendar']} Timeline",
                    value=dates_info,
                    inline=True
                )
            
            # Top participantes (se disponível)
            if 'participants' in stats and stats['participants']:
                top_participants = sorted(
                    stats['participants'],
                    key=lambda p: p.get('stats', {}).get('matches_won', 0),
                    reverse=True
                )[:5]
                
                participants_text = ""
                for i, participant in enumerate(top_participants, 1):
                    wins = participant.get('stats', {}).get('matches_won', 0)
                    losses = participant.get('stats', {}).get('matches_lost', 0)
                    
                    medal = {
                        1: self.emojis['medal_gold'],
                        2: self.emojis['medal_silver'],
                        3: self.emojis['medal_bronze']
                    }.get(i, f"{i}.")
                    
                    participants_text += f"{medal} **{participant['username']}** ({wins}W/{losses}L)\n"
                
                embed.add_field(
                    name=f"{self.emojis['star']} Top Participantes",
                    value=participants_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournament_stats_commands_used')
            
            if self.logger:
                self.logger.info(
                    f"Estatísticas consultadas: {torneio_id} por {interaction.user}",
                    extra={
                        'tournament_id': torneio_id,
                        'user_id': interaction.user.id
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao obter estatísticas: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando stats_torneio: {e}")
    
    # Comandos administrativos
    @app_commands.command(
        name="admin_torneio",
        description="[ADMIN] Gerencia torneios (iniciar, cancelar, etc.)"
    )
    @app_commands.describe(
        acao="Ação a ser executada",
        torneio_id="ID do torneio",
        motivo="Motivo da ação (para cancelamento)"
    )
    async def admin_torneio(
        self,
        interaction: discord.Interaction,
        acao: str,
        torneio_id: str,
        motivo: str = "Ação administrativa"
    ):
        """Comando administrativo para gerenciar torneios"""
        try:
            # Verificar permissões
            if not await self._check_permissions(interaction, 'administrator'):
                embed = self._create_error_embed(
                    "Você precisa de permissões de administrador para usar este comando."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rate limiting
            if not await self._apply_rate_limit(str(interaction.user.id), "admin_torneio"):
                embed = self._create_warning_embed(
                    "Você está usando comandos administrativos muito rapidamente. Tente novamente em alguns minutos."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Obter torneio
            tournament = await self.tournament_system._get_tournament(torneio_id)
            
            if not tournament:
                embed = self._create_error_embed(
                    "Torneio não encontrado ou inválido."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar se é do mesmo servidor
            if tournament.guild_id != str(interaction.guild.id):
                embed = self._create_error_embed(
                    "Este torneio não pertence a este servidor."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Executar ação
            success = False
            result_message = ""
            
            if acao.lower() in ['iniciar', 'start']:
                if tournament.status == TournamentStatus.REGISTRATION:
                    success = await self.tournament_system.start_tournament(torneio_id)
                    result_message = "Torneio iniciado com sucesso!" if success else "Erro ao iniciar torneio."
                else:
                    result_message = "Torneio não está em fase de registro."
            
            elif acao.lower() in ['cancelar', 'cancel']:
                if tournament.status not in [TournamentStatus.FINISHED, TournamentStatus.CANCELLED]:
                    success = await self.tournament_system.cancel_tournament(torneio_id, motivo)
                    result_message = f"Torneio cancelado: {motivo}" if success else "Erro ao cancelar torneio."
                else:
                    result_message = "Torneio já foi finalizado ou cancelado."
            
            else:
                result_message = "Ação inválida. Use: iniciar, cancelar"
            
            # Resposta
            if success:
                embed = self._create_success_embed(result_message)
                embed.add_field(
                    name=f"{self.emojis['info']} Detalhes",
                    value=(
                        f"**Torneio:** {tournament.name}\n"
                        f"**Ação:** {acao.title()}\n"
                        f"**Administrador:** {interaction.user.mention}\n"
                        f"**Timestamp:** <t:{int(datetime.now().timestamp())}:F>"
                    ),
                    inline=False
                )
            else:
                embed = self._create_error_embed(result_message)
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('admin_tournament_commands_used')
                if success:
                    await self.metrics.increment(f'tournament_{acao.lower()}_admin')
            
            if self.logger:
                self.logger.info(
                    f"Ação administrativa: {acao} em {torneio_id} por {interaction.user} (sucesso: {success})",
                    extra={
                        'tournament_id': torneio_id,
                        'action': acao,
                        'admin_id': interaction.user.id,
                        'success': success
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado na ação administrativa: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando admin_torneio: {e}")
    
    @app_commands.command(
        name="saude_torneios",
        description="[ADMIN] Verifica a saúde do sistema de torneios"
    )
    async def saude_torneios(self, interaction: discord.Interaction):
        """Comando para verificar saúde do sistema"""
        try:
            # Verificar permissões
            if not await self._check_permissions(interaction, 'manage_guild'):
                embed = self._create_error_embed(
                    "Você precisa da permissão 'Gerenciar Servidor' para usar este comando."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar se o sistema está disponível
            if not self.tournament_system:
                embed = self._create_error_embed(
                    "Sistema de torneios não está disponível no momento."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Obter informações de saúde
            health = await self.tournament_system.health_check()
            
            # Criar embed de saúde
            status_color = self.colors['success'] if health['status'] == 'healthy' else self.colors['error']
            status_emoji = self.emojis['check'] if health['status'] == 'healthy' else self.emojis['cross']
            
            embed = self._create_embed(
                f"{status_emoji} Saúde do Sistema de Torneios",
                f"**Status Geral:** {health['status'].title()}",
                color=status_color
            )
            
            # Estatísticas gerais
            embed.add_field(
                name=f"{self.emojis['info']} Estatísticas",
                value=(
                    f"**Torneios Ativos:** {health.get('active_tournaments', 0)}\n"
                    f"**Tarefas em Background:** {health.get('background_tasks', 0)}\n"
                    f"**Última Verificação:** <t:{int(datetime.now().timestamp())}:R>"
                ),
                inline=True
            )
            
            # Status dos sistemas
            systems = health.get('systems', {})
            systems_text = ""
            for system, status in systems.items():
                status_icon = self.emojis['check'] if status else self.emojis['cross']
                systems_text += f"{status_icon} **{system.title()}:** {'Ativo' if status else 'Inativo'}\n"
            
            embed.add_field(
                name=f"{self.emojis['gear']} Sistemas Core",
                value=systems_text or "Nenhum sistema reportado",
                inline=True
            )
            
            # Informações adicionais
            if 'error' in health:
                embed.add_field(
                    name=f"{self.emojis['warning']} Erro",
                    value=f"```{health['error']}```",
                    inline=False
                )
            
            if 'cache_health' in health:
                cache_status = health['cache_health']
                embed.add_field(
                    name=f"{self.emojis['info']} Cache",
                    value=f"**Status:** {cache_status.get('status', 'unknown')}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('health_check_commands_used')
            
            if self.logger:
                self.logger.info(
                    f"Verificação de saúde executada por {interaction.user}",
                    extra={
                        'user_id': interaction.user.id,
                        'health_status': health['status']
                    }
                )
        
        except Exception as e:
            embed = self._create_error_embed(
                f"Erro inesperado ao verificar saúde: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if self.logger:
                self.logger.error(f"Erro no comando saude_torneios: {e}")

# Função para setup do cog
async def setup(bot):
    """Configura o cog de comandos de torneios"""
    await bot.add_cog(ModernTournamentCommands(bot))

# Função para cleanup do cog
async def teardown(bot):
    """Limpa recursos do cog"""
    cog = bot.get_cog('ModernTournamentCommands')
    if cog and hasattr(cog, 'tournament_system') and cog.tournament_system:
        await cog.tournament_system.cleanup()