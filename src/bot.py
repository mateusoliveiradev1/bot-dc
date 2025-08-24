#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Discord Profissional para Clã PUBG - Hawk Esports
Desenvolvido para automação completa de servidor e integração PUBG API

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Literal

# Importar módulos personalizados da nova estrutura
import sys
from pathlib import Path

from core.storage import DataStorage
from core.postgres_storage import PostgreSQLStorage as PostgresStorage
from core.rank import RankSystem
from features.pubg.api import PUBGIntegration
from features.pubg.dual_ranking import DualRankingSystem
from features.pubg.roles import PubgRankRoles
from features.music.player import MusicSystem
from features.music.dynamic_channels import DynamicChannelsSystem
from features.music.channels import MusicChannelsSystem
from features.tournaments.manager import TournamentSystem
from features.tournaments.seasons import SeasonSystem
from features.achievements.system import AchievementSystem
from features.badges.system import BadgeSystem
from features.notifications.system import NotificationsSystem
from features.moderation.system import ModerationSystem
from features.minigames.system import MinigamesSystem
from features.checkin.system import CheckInSystem
from features.checkin.notifications import CheckInNotifications
from features.checkin.reminders import CheckInReminders
from features.checkin.reports import CheckInReports
from integrations.medal import MedalIntegration
from utils import scheduler, embed_templates, keep_alive
from utils.keep_alive import KeepAlive
from utils.charts_system import ChartsSystem
from utils.scheduler import TaskScheduler
from web.app import WebDashboard
from core.registration import Registration

# Importar ServerSetup dos scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'setup'))
from server_setup import ServerSetup

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hawk_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HawkBot')

class HawkBot(commands.Bot):
    """Bot principal do clã Hawk Esports"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Bot oficial do clã Hawk Esports - PUBG'
        )
        
        # Inicializar sistema de armazenamento (PostgreSQL ou JSON)
        self.storage = self._initialize_storage()
        self.embed_templates = embed_templates
        self.server_setup = ServerSetup(self)
        self.registration = Registration(self)
        self.pubg_api = PUBGIntegration()
        self.rank_system = RankSystem(self, self.storage, self.pubg_api)
        self.dual_ranking_system = DualRankingSystem(self, self.storage, self.pubg_api, self.rank_system)
        self.medal_integration = MedalIntegration(self, self.storage)
        self.tournament_system = TournamentSystem(self, self.storage)
        self.web_dashboard = WebDashboard(self)
        self.achievement_system = AchievementSystem(self, self.storage)
        self.music_system = MusicSystem(self)
        self.moderation_system = ModerationSystem(self, self.storage)
        self.minigames_system = MinigamesSystem(self, self.storage)
        self.charts_system = ChartsSystem(self, self.storage)
        self.notifications_system = NotificationsSystem(self, self.storage)
        self.pubg_rank_roles = PubgRankRoles(self, self.storage, self.pubg_api)
        self.badge_system = BadgeSystem(self, self.storage, self.pubg_api, self.dual_ranking_system)
        self.season_system = SeasonSystem(self, self.storage, self.dual_ranking_system, self.badge_system)
        self.dynamic_channels = DynamicChannelsSystem(self, self.storage)
        self.music_channels = MusicChannelsSystem(self, self.storage, self.music_system)
        self.checkin_system = CheckInSystem(self, self.storage)
        self.checkin_notifications = CheckInNotifications(self, self.checkin_system)
        self.checkin_reminders = CheckInReminders(self, self.checkin_system, self.storage)
        self.checkin_reports = CheckInReports(self, self.checkin_system, self.storage)
        self.scheduler = TaskScheduler(self, self.storage, self.rank_system, self.medal_integration)
        
        logger.info("Bot Hawk Esports inicializado com sucesso!")
    
    def _initialize_storage(self):
        """Inicializa o sistema de armazenamento baseado nas variáveis de ambiente"""
        # Verifica se há configuração de PostgreSQL
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if db_host and db_name and db_user and db_password:
            logger.info("🐘 Usando PostgreSQL como sistema de armazenamento")
            return PostgreSQLStorage()
        else:
            logger.info("📁 Usando JSON como sistema de armazenamento (desenvolvimento)")
            return DataStorage()
    
    async def setup_hook(self):
        """Configurações iniciais do bot"""
        try:
            # Inicializar sistema de armazenamento
            if hasattr(self.storage, 'initialize'):
                await self.storage.initialize()
            
            # Inicializar sistema keep alive para Render
            if os.getenv('RENDER'):
                self.keep_alive = KeepAlive(self)
                await self.keep_alive.start()
                logger.info("🔄 Sistema keep alive iniciado para Render")
            
            # Sincronizar comandos slash
            synced = await self.tree.sync()
            logger.info(f"Sincronizados {len(synced)} comandos slash")
            
            # Configurar sistema de música
            await self.music_system.setup_hook()
            
            # Iniciar tarefas automáticas
            if not self.auto_update_ranks.is_running():
                self.auto_update_ranks.start()
            
            # Iniciar sistema de notificações
            self.notifications_system.start_tasks()
            
            # Iniciar sistema de canais dinâmicos
            await self.dynamic_channels.start_cleanup_task()
            
            # Iniciar sistema de canais de música
            await self.music_channels.start_cleanup_task()
            
            # Iniciar sistema de notificações de check-in
            asyncio.create_task(self.checkin_notifications.start_cleanup_task())
            
            # Iniciar sistema de lembretes de check-in
            self.checkin_reminders.start_reminder_task()
            
            # Carregar comandos de check-in
            try:
                await self.load_extension('checkin_commands')
                logger.info("Comandos de check-in carregados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar comandos de check-in: {e}")
                
            # Carregar comandos administrativos de check-in
            try:
                await self.load_extension('checkin_admin')
                logger.info("Comandos administrativos de check-in carregados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar comandos administrativos de check-in: {e}")
                
            # Carregar comandos de lembretes
            try:
                await self.load_extension('reminder_commands')
                logger.info("Comandos de lembretes carregados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar comandos de lembretes: {e}")
                
            # Carregar comandos de relatórios
            try:
                await self.load_extension('report_commands')
                logger.info("Comandos de relatórios carregados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao carregar comandos de relatórios: {e}")
                
        except Exception as e:
            logger.error(f"Erro no setup_hook: {e}")
    
    async def close(self):
        """Método chamado quando o bot é desligado"""
        # Parar sistema keep alive se estiver rodando
        if hasattr(self, 'keep_alive') and self.keep_alive:
            await self.keep_alive.stop()
            logger.info("🔄 Sistema keep alive parado")
        
        # Fechar conexão do storage
        if hasattr(self.storage, 'close'):
            await self.storage.close()
            logger.info("💾 Conexão do armazenamento fechada")
        
        await super().close()
    
    async def on_ready(self):
        """Evento quando bot fica online"""
        logger.info(f'{self.user} está online!')
        logger.info(f'Bot conectado em {len(self.guilds)} servidor(es)')
        
        # Sincronização de comandos desabilitada temporariamente devido ao rate limiting
        # Os comandos existentes continuarão funcionando normalmente
        logger.info("⚠️ Sincronização de comandos slash desabilitada temporariamente")
        logger.info("ℹ️ Comandos existentes continuarão funcionando normalmente")
        
        # Iniciar dashboard web em thread separada
        try:
            import threading
            # Configurar host e porta para Render
            host = '0.0.0.0' if os.getenv('RENDER') else 'localhost'
            port = int(os.getenv('PORT', 5000))  # Render usa variável PORT
            
            dashboard_thread = threading.Thread(
                target=self.web_dashboard.run,
                kwargs={'host': host, 'port': port, 'debug': False}
            )
            dashboard_thread.daemon = True
            dashboard_thread.start()
            logger.info(f"Dashboard web iniciado em http://{host}:{port}")
        except Exception as e:
            logger.error(f"Erro ao iniciar dashboard web: {e}")
        
        # Definir status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Hawk Esports | /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
    
    async def on_member_join(self, member):
        """Evento quando novo membro entra no servidor"""
        await self.registration.handle_new_member(member)
        await self.moderation_system.handle_member_join(member)
        # Integração automática com stats PUBG para novos membros
        await self.dual_ranking_system.auto_update_new_member_pubg(member)
    
    async def on_voice_state_update(self, member, before, after):
        """Evento para gerenciar canais dinâmicos e canais de música"""
        await self.dynamic_channels.on_voice_state_update(member, before, after)
        await self.music_channels.on_voice_state_update(member, before, after)
    
    async def on_message(self, message):
        """Evento para monitorar mensagens (Medal integration e moderação)"""
        if not message.author.bot:
            await self.medal_integration.process_message(message)
            # Verificar moderação automática
            await self.moderation_system.check_message(message)
        
        await self.process_commands(message)
    
    async def on_reaction_add(self, reaction, user):
        """Evento para reações (Quiz mini-games)"""
        if user.bot:
            return
        
        # Verificar se é resposta de quiz
        quiz_result = await self.minigames_system.check_quiz_answer(reaction, user)
        if quiz_result:
            await reaction.message.channel.send(embed=quiz_result)
    
    async def _sync_commands_with_retry(self, max_retries: int = 3):
        """Sincroniza comandos slash com tratamento de rate limit"""
        for attempt in range(max_retries):
            try:
                synced = await self.tree.sync()
                logger.info(f"✅ Sincronizados {len(synced)} comandos slash com sucesso!")
                return
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    retry_after = getattr(e, 'retry_after', 60)
                    logger.warning(f"⚠️ Rate limit detectado. Aguardando {retry_after:.1f} segundos antes de tentar novamente...")
                    logger.warning(f"Tentativa {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries - 1:  # Não esperar na última tentativa
                        await asyncio.sleep(retry_after)
                    else:
                        logger.error("❌ Máximo de tentativas de sincronização atingido. Comandos slash podem não estar atualizados.")
                        logger.info("ℹ️ O bot continuará funcionando normalmente. Os comandos serão sincronizados na próxima reinicialização.")
                else:
                    logger.error(f"❌ Erro HTTP ao sincronizar comandos: {e}")
                    break
            except Exception as e:
                logger.error(f"❌ Erro inesperado ao sincronizar comandos: {e}")
                break
    
    @tasks.loop(minutes=30)
    async def auto_update_ranks(self):
        """Atualização automática de ranks a cada 30 minutos (tempo real)"""
        try:
            for guild in self.guilds:
                await self.rank_system.update_all_ranks(guild)
                
                # Atualizar cargos PUBG automáticos se habilitado
                if hasattr(self, 'pubg_rank_roles') and self.pubg_rank_roles.config.get('enabled', False):
                    updated_count = await self.pubg_rank_roles.update_all_member_ranks(guild)
                    if updated_count > 0:
                        logger.info(f"Cargos PUBG atualizados automaticamente: {updated_count} membros")
                
                # Verificar emblemas automaticamente se habilitado
                if hasattr(self, 'badge_system'):
                    config = await self.badge_system.get_config(guild.id)
                    if config.get('enabled', False) and config.get('auto_check', True):
                        updated_badges = await self.badge_system.check_all_members(guild)
                        if updated_badges > 0:
                            logger.info(f"Emblemas atualizados automaticamente: {updated_badges} membros")
                
                # Verificar temporadas automaticamente se habilitado
                if hasattr(self, 'season_system') and self.season_system.config.get('enabled', False):
                    current_season = self.season_system.get_current_season()
                    if current_season and current_season.has_ended():
                        await self.season_system.end_season(current_season)
                        logger.info(f"Temporada '{current_season.name}' finalizada automaticamente")
                
                # Verificar e resetar rankings temporais automaticamente
                if hasattr(self, 'dual_ranking_system'):
                    # Verificar reset diário (00:00)
                    if self.dual_ranking_system._should_reset_temporal_ranking('daily'):
                        await self.dual_ranking_system._reset_temporal_ranking('daily')
                        logger.info("Ranking diário resetado automaticamente")
                    
                    # Verificar reset semanal (segunda-feira 00:00)
                    if self.dual_ranking_system._should_reset_temporal_ranking('weekly'):
                        await self.dual_ranking_system._reset_temporal_ranking('weekly')
                        logger.info("Ranking semanal resetado automaticamente")
                    
                    # Verificar reset mensal (dia 1 do mês 00:00)
                    if self.dual_ranking_system._should_reset_temporal_ranking('monthly'):
                        await self.dual_ranking_system._reset_temporal_ranking('monthly')
                        logger.info("Ranking mensal resetado automaticamente")
                        
            logger.info("Ranks e emblemas atualizados automaticamente (tempo real)")
        except Exception as e:
            logger.error(f"Erro na atualização automática de ranks: {e}")

# Instanciar o bot
bot = HawkBot()

# ==================== COMANDOS SLASH ====================

@bot.tree.command(name="setup_server", description="🔧 Configura automaticamente o servidor do clã Hawk Esports")
@discord.app_commands.describe(
    confirmar="Digite 'CONFIRMAR' para criar toda a estrutura do servidor"
)
async def setup_server(interaction: discord.Interaction, confirmar: str):
    """Comando para configurar servidor automaticamente"""
    # Verificação removida - qualquer usuário pode executar
    # if not interaction.user.guild_permissions.administrator:
    #     embed = discord.Embed(
    #         title="❌ Acesso Negado",
    #         description="Apenas administradores podem executar este comando.",
    #         color=discord.Color.red()
    #     )
    #     await interaction.response.send_message(embed=embed, ephemeral=True)
    #     return
    
    if confirmar.upper() != "CONFIRMAR":
        embed = discord.Embed(
            title="⚠️ Confirmação Necessária",
            description="Digite `/setup_server confirmar:CONFIRMAR` para prosseguir.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    success = await bot.server_setup.setup_complete_server(interaction.guild)
    
    if success:
        embed = discord.Embed(
            title="✅ Servidor Configurado!",
            description="**Hawk Esports** está pronto para ação!\n\n" +
                       "📋 Novos membros devem usar `/register_pubg` no canal de registro.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="❌ Erro na Configuração",
            description="Ocorreu um erro durante a configuração. Verifique os logs.",
            color=discord.Color.red()
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="register_pubg", description="📋 Registra seu nick PUBG no clã Hawk Esports")
@discord.app_commands.describe(
    nome="Seu nick exato no PUBG",
    shard="Plataforma: steam, psn, xbox, kakao"
)
@discord.app_commands.choices(shard=[
    discord.app_commands.Choice(name="Steam (PC)", value="steam"),
    discord.app_commands.Choice(name="PlayStation", value="psn"),
    discord.app_commands.Choice(name="Xbox", value="xbox"),
    discord.app_commands.Choice(name="Kakao", value="kakao")
])
async def register_pubg(interaction: discord.Interaction, nome: str, shard: str):
    """Comando para registrar jogador PUBG"""
    await interaction.response.defer()
    success = await bot.registration.register_player(interaction.user, nome, shard)
    
    if success:
        embed = discord.Embed(
            title="✅ Registro Concluído!",
            description=f"**Bem-vindo ao Hawk Esports, {interaction.user.mention}!**\n\n" +
                       f"🎮 **Nick PUBG:** {nome}\n" +
                       f"🌐 **Plataforma:** {shard.upper()}\n" +
                       f"🏆 **Role:** Acesso liberado\n\n" +
                       "Use `/meu_status` para verificar suas informações.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Hawk Esports - Rumo à vitória!")
    else:
        embed = discord.Embed(
            title="❌ Erro no Registro",
            description="Não foi possível completar seu registro. Tente novamente.",
            color=discord.Color.red()
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="meu_status", description="📊 Verifica seu status de registro e cargo atual")
async def meu_status(interaction: discord.Interaction):
    """Comando para verificar status do jogador"""
    await interaction.response.defer()
    status_info = await bot.registration.get_player_status(interaction.user)
    
    embed = discord.Embed(
        title="📊 Seu Status - Hawk Esports",
        description=status_info,
        color=discord.Color.blue()
    )
    embed.set_footer(text="Hawk Esports - Sempre evoluindo!")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="leaderboard", description="🏆 Mostra o ranking do clã Hawk Esports")
@discord.app_commands.describe(
    modo="Modo de jogo para o ranking",
    periodo="Período do ranking"
)
@discord.app_commands.choices(
    modo=[
        discord.app_commands.Choice(name="Squad", value="squad"),
        discord.app_commands.Choice(name="Duo", value="duo"),
        discord.app_commands.Choice(name="Solo", value="solo")
    ],
    periodo=[
        discord.app_commands.Choice(name="Diário", value="daily"),
        discord.app_commands.Choice(name="Semanal", value="weekly"),
        discord.app_commands.Choice(name="Mensal", value="monthly"),
        discord.app_commands.Choice(name="Temporada", value="season")
    ]
)
async def leaderboard(interaction: discord.Interaction, modo: str = "squad", periodo: str = "weekly"):
    """Comando para mostrar leaderboard"""
    await interaction.response.defer()
    
    # Se for um período temporal (diário, semanal, mensal), usar o novo método
    if periodo in ["daily", "weekly", "monthly"]:
        embed = await bot.rank_system.generate_temporal_leaderboard(interaction.guild, modo, periodo)
    else:
        embed = await bot.rank_system.generate_leaderboard(interaction.guild, modo, periodo)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="clipes", description="🎬 Lista os últimos clipes de um jogador")
@discord.app_commands.describe(
    jogador="Mencione o jogador ou deixe vazio para seus clipes"
)
async def clipes(interaction: discord.Interaction, jogador: discord.Member = None):
    """Comando para listar clipes"""
    target_user = jogador or interaction.user
    await interaction.response.defer()
    
    clips_embed = await bot.medal_integration.create_clips_list_embed(str(target_user.id))
    await interaction.followup.send(embed=clips_embed)

@bot.tree.command(name="help", description="❓ Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    """Comando de ajuda"""
    embed = discord.Embed(
        title="🦅 Hawk Esports - Comandos Disponíveis",
        description="Bot oficial do clã para automação completa!",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="🔧 Administração",
        value="`/setup_server` - Configura servidor automaticamente",
        inline=False
    )
    
    embed.add_field(
        name="📋 Registro",
        value="`/register_pubg` - Registra seu nick PUBG\n" +
              "`/meu_status` - Verifica seu status",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Rankings",
        value="`/leaderboard` - Mostra ranking do clã\n" +
              "`/ranking_pubg` - Ranking PUBG real\n" +
              "`/ranking_servidor` - Ranking interno\n" +
              "`/meu_rank_duplo` - Seus ranks completos",
        inline=False
    )
    
    embed.add_field(
        name="🏅 Badges",
        value="`/badges_pubg` - Seus badges PUBG\n" +
              "`/badges_servidor` - Seus badges do servidor\n" +
              "`/todos_badges` - Lista todos os badges\n" +
              "`/conquistas` - Sistema de conquistas",
        inline=False
    )
    
    embed.add_field(
        name="🎬 Clipes",
        value="`/clipes` - Lista clipes de jogadores",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Torneios",
        value="`/criar_torneio` - Cria novo torneio\n" +
              "`/participar_torneio` - Participa de torneio\n" +
              "`/torneios` - Lista torneios ativos\n" +
              "`/bracket` - Mostra bracket do torneio\n" +
              "`/resultado_partida` - Reporta resultado",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Dashboard Web",
        value="`/dashboard` - Acessa dashboard web completo",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Conquistas",
        value="`/conquistas` - Vê suas conquistas e badges\n" +
              "`/conquistas_lista` - Lista todas as conquistas\n" +
              "`/ranking_conquistas` - Ranking de conquistas",
        inline=False
    )
    
    embed.add_field(
        name="🎵 Música",
        value="`/play` - Toca música no canal de voz\n" +
              "`/pause` - Pausa/retoma música atual\n" +
              "`/skip` - Pula música atual\n" +
              "`/queue` - Mostra fila de músicas\n" +
              "`/volume` - Define volume (0-100)\n" +
              "`/loop` - Ativa/desativa repetição\n" +
              "`/shuffle` - Embaralha fila\n" +
              "`/stop` - Para música e limpa fila\n" +
              "`/disconnect` - Desconecta do canal de voz",
        inline=False
    )
    
    embed.set_footer(text="Hawk Esports - Dominando os campos de batalha!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== COMANDOS DE TORNEIO ====================

@bot.tree.command(name="criar_torneio", description="🏆 Cria um novo torneio interno")
@discord.app_commands.describe(
    nome="Nome do torneio",
    tipo="Tipo de torneio",
    max_participantes="Número máximo de participantes (padrão: 16)",
    premio="Prêmio do torneio (opcional)"
)
@discord.app_commands.choices(tipo=[
    discord.app_commands.Choice(name="Eliminação Simples", value="single_elimination"),
    discord.app_commands.Choice(name="Eliminação Dupla", value="double_elimination"),
    discord.app_commands.Choice(name="Round Robin", value="round_robin")
])
async def criar_torneio(interaction: discord.Interaction, nome: str, tipo: str, max_participantes: int = 16, premio: str = None):
    """Comando para criar um novo torneio"""
    await bot.tournament_system.create_tournament_command(interaction, nome, tipo, max_participantes, premio)

@bot.tree.command(name="participar_torneio", description="🎮 Participa de um torneio ativo")
@discord.app_commands.describe(
    torneio_id="ID do torneio para participar"
)
async def participar_torneio(interaction: discord.Interaction, torneio_id: str):
    """Comando para participar de um torneio"""
    await bot.tournament_system.join_tournament_command(interaction, torneio_id)

@bot.tree.command(name="torneios", description="🏆 Lista todos os torneios ativos")
async def listar_torneios(interaction: discord.Interaction):
    """Comando para listar torneios ativos"""
    await bot.tournament_system.list_tournaments_command(interaction)

@bot.tree.command(name="bracket", description="🗂️ Mostra o bracket de um torneio")
@discord.app_commands.describe(
    torneio_id="ID do torneio para ver o bracket"
)
async def ver_bracket(interaction: discord.Interaction, torneio_id: str):
    """Comando para ver o bracket de um torneio"""
    await bot.tournament_system.show_bracket_command(interaction, torneio_id)

@bot.tree.command(name="resultado_partida", description="⚔️ Reporta o resultado de uma partida de torneio")
@discord.app_commands.describe(
    torneio_id="ID do torneio",
    partida_id="ID da partida",
    vencedor="Mencione o jogador vencedor"
)
async def resultado_partida(interaction: discord.Interaction, torneio_id: str, partida_id: str, vencedor: discord.Member):
    """Comando para reportar resultado de partida"""
    await bot.tournament_system.report_match_result_command(interaction, torneio_id, partida_id, vencedor)

@bot.tree.command(name="dashboard", description="🌐 Acessa o dashboard web do clã")
async def dashboard_command(interaction: discord.Interaction):
    """Comando para acessar o dashboard web"""
    embed = discord.Embed(
        title="🌐 Dashboard Web - Hawk Esports",
        description="Acesse o dashboard completo com estatísticas em tempo real!",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="📊 Recursos Disponíveis",
        value="• Estatísticas gerais do clã\n" +
              "• Leaderboard em tempo real\n" +
              "• Status dos torneios ativos\n" +
              "• Clipes recentes dos membros\n" +
              "• Gráficos e análises detalhadas",
        inline=False
    )
    
    # Configurar URL baseado no ambiente
    if os.getenv('RENDER'):
        dashboard_url = "https://hawk-esports-bot.onrender.com"  # Substitua pela sua URL do Render
    else:
        dashboard_url = "http://localhost:5000"
    
    embed.add_field(
        name="🔗 Link de Acesso",
        value=f"[**Clique aqui para acessar o Dashboard**]({dashboard_url})",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Informações",
        value="O dashboard é atualizado automaticamente a cada 30 segundos\n" +
              "Funciona melhor em navegadores modernos (Chrome, Firefox, Edge)",
        inline=False
    )
    
    embed.set_footer(text="Hawk Esports - Dashboard Web Profissional")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="conquistas", description="🏆 Vê suas conquistas e badges")
@discord.app_commands.describe(
    usuario="Mencione um usuário para ver suas conquistas (opcional)"
)
async def conquistas(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para ver conquistas de um usuário"""
    await bot.achievement_system.achievements_command(interaction, usuario)

@bot.tree.command(name="badges_pubg", description="🎮 Mostra seus badges PUBG específicos")
@discord.app_commands.describe(
    usuario="Mencione um usuário para ver seus badges PUBG (opcional)"
)
async def badges_pubg(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para ver badges PUBG de um usuário"""
    await interaction.response.defer()
    
    target_user = usuario or interaction.user
    
    try:
        embed = await bot.dual_ranking_system.show_pubg_badges(target_user)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando badges_pubg: {e}")
        await interaction.followup.send("❌ Erro ao obter badges PUBG. Tente novamente.", ephemeral=True)

@bot.tree.command(name="badges_servidor", description="🏠 Mostra seus badges do servidor")
@discord.app_commands.describe(
    usuario="Mencione um usuário para ver seus badges do servidor (opcional)"
)
async def badges_servidor(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para ver badges do servidor de um usuário"""
    await interaction.response.defer()
    
    target_user = usuario or interaction.user
    
    try:
        embed = await bot.dual_ranking_system.show_server_badges(target_user)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando badges_servidor: {e}")
        await interaction.followup.send("❌ Erro ao obter badges do servidor. Tente novamente.", ephemeral=True)

@bot.tree.command(name="todos_badges", description="🏆 Mostra todos os badges disponíveis no sistema")
async def todos_badges(interaction: discord.Interaction):
    """Comando para mostrar todos os badges disponíveis"""
    await interaction.response.defer()
    
    try:
        embed = await bot.dual_ranking_system.show_all_available_badges()
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando todos_badges: {e}")
        await interaction.followup.send("❌ Erro ao obter lista de badges. Tente novamente.", ephemeral=True)

@bot.tree.command(name="conquistas_lista", description="📋 Lista todas as conquistas disponíveis")
@discord.app_commands.describe(
    categoria="Filtrar por categoria específica (opcional)"
)
@discord.app_commands.choices(categoria=[
    discord.app_commands.Choice(name="Registro", value="registro"),
    discord.app_commands.Choice(name="Combate", value="combate"),
    discord.app_commands.Choice(name="Vitória", value="vitoria"),
    discord.app_commands.Choice(name="Participação", value="participacao"),
    discord.app_commands.Choice(name="Torneio", value="torneio"),
    discord.app_commands.Choice(name="Conteúdo", value="conteudo"),
    discord.app_commands.Choice(name="Precisão", value="precisao"),
    discord.app_commands.Choice(name="Sobrevivência", value="sobrevivencia"),
    discord.app_commands.Choice(name="Veículo", value="veiculo"),
    discord.app_commands.Choice(name="Armas", value="armas"),
    discord.app_commands.Choice(name="Explosivos", value="explosivos"),
    discord.app_commands.Choice(name="Tempo", value="tempo"),
    discord.app_commands.Choice(name="Equipe", value="equipe"),
    discord.app_commands.Choice(name="Streak", value="streak"),
    discord.app_commands.Choice(name="Rank", value="rank"),
    discord.app_commands.Choice(name="Especial", value="especial")
])
async def conquistas_lista(interaction: discord.Interaction, categoria: str = None):
    """Comando para listar todas as conquistas disponíveis"""
    await bot.achievement_system.achievements_list_command(interaction, categoria)

@bot.tree.command(name="ranking_conquistas", description="🏅 Mostra o ranking de conquistas do clã")
async def ranking_conquistas(interaction: discord.Interaction):
    """Comando para mostrar leaderboard de conquistas"""
    await bot.achievement_system.achievements_leaderboard_command(interaction)

# ==================== COMANDOS DE RANKING DUPLO ====================

@bot.tree.command(name="ranking_pubg", description="🎮 Mostra o ranking PUBG baseado em stats reais")
@discord.app_commands.describe(
    modo="Modo de jogo para o ranking",
    periodo="Período do ranking",
    limite="Número de jogadores no ranking (máximo 20)"
)
@discord.app_commands.choices(
    modo=[
        discord.app_commands.Choice(name="Squad", value="squad"),
        discord.app_commands.Choice(name="Duo", value="duo"),
        discord.app_commands.Choice(name="Solo", value="solo")
    ],
    periodo=[
        discord.app_commands.Choice(name="Diário", value="daily"),
        discord.app_commands.Choice(name="Semanal", value="weekly"),
        discord.app_commands.Choice(name="Mensal", value="monthly"),
        discord.app_commands.Choice(name="Temporada", value="season")
    ]
)
async def ranking_pubg(interaction: discord.Interaction, modo: str = "squad", periodo: str = "weekly", limite: int = 10):
    """Comando para mostrar ranking PUBG real"""
    await interaction.response.defer()
    
    try:
        # Se for um período temporal, usar o novo método
        if periodo in ["daily", "weekly", "monthly"]:
            embed = await bot.rank_system.generate_temporal_leaderboard(
                interaction.guild, 
                modo, 
                periodo,
                limit=min(limite, 20)
            )
        else:
            embed = await bot.dual_ranking_system.generate_leaderboard(
                interaction.guild, 
                "pubg_real", 
                modo, 
                min(limite, 20)
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando ranking_pubg: {e}")
        await interaction.followup.send("❌ Erro ao gerar ranking PUBG. Tente novamente.", ephemeral=True)

@bot.tree.command(name="ranking_servidor", description="🏛️ Mostra o ranking interno do servidor")
@discord.app_commands.describe(
    periodo="Período do ranking",
    limite="Número de jogadores no ranking (máximo 20)"
)
@discord.app_commands.choices(
    periodo=[
        discord.app_commands.Choice(name="Diário", value="daily"),
        discord.app_commands.Choice(name="Semanal", value="weekly"),
        discord.app_commands.Choice(name="Mensal", value="monthly"),
        discord.app_commands.Choice(name="Temporada", value="season")
    ]
)
async def ranking_servidor(interaction: discord.Interaction, periodo: str = "weekly", limite: int = 10):
    """Comando para mostrar ranking interno do servidor"""
    await interaction.response.defer()
    
    try:
        # Se for um período temporal, usar o novo método
        if periodo in ["daily", "weekly", "monthly"]:
            embed = await bot.rank_system.generate_temporal_leaderboard(
                interaction.guild, 
                "squad",  # Modo padrão para ranking do servidor
                periodo,
                limit=min(limite, 20),
                server_ranking=True
            )
        else:
            embed = await bot.dual_ranking_system.generate_leaderboard(
                interaction.guild, 
                "server_internal", 
                None, 
                min(limite, 20)
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando ranking_servidor: {e}")
        await interaction.followup.send("❌ Erro ao gerar ranking do servidor. Tente novamente.", ephemeral=True)

@bot.tree.command(name="meu_rank_duplo", description="📊 Mostra seus ranks PUBG e interno do servidor")
async def meu_rank_duplo(interaction: discord.Interaction):
    """Comando para mostrar ambos os ranks do usuário"""
    await interaction.response.defer()
    
    try:
        embed = await bot.dual_ranking_system.get_user_profile_embed(interaction.user)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando meu_rank_duplo: {e}")
        await interaction.followup.send("❌ Erro ao obter seu perfil. Tente novamente.", ephemeral=True)

@bot.tree.command(name="atividade_servidor", description="📈 Mostra suas estatísticas de atividade no servidor")
async def atividade_servidor(interaction: discord.Interaction):
    """Comando para mostrar estatísticas de atividade"""
    await interaction.response.defer()
    
    try:
        stats = await bot.dual_ranking_system.get_activity_stats(interaction.user.id)
        
        embed = discord.Embed(
            title="📈 Suas Estatísticas de Atividade",
            description=f"Estatísticas de {interaction.user.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💬 Mensagens",
            value=f"**Hoje**: {stats.get('messages_today', 0)}\n**Total**: {stats.get('total_messages', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🎤 Tempo em Voz",
            value=f"**Hoje**: {stats.get('voice_today', 0)} min\n**Total**: {stats.get('total_voice_time', 0)} min",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Pontos do Servidor",
            value=f"**Hoje**: {stats.get('points_today', 0)}\n**Total**: {stats.get('server_points', 0)}",
            inline=True
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Hawk Bot - Sistema de Ranking Duplo")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro no comando atividade_servidor: {e}")
        await interaction.followup.send("❌ Erro ao obter estatísticas. Tente novamente.", ephemeral=True)

# ==================== COMANDOS DE MÚSICA ====================

@bot.tree.command(name="play", description="🎵 Toca uma música no canal de voz")
@discord.app_commands.describe(
    musica="Nome da música ou URL do YouTube"
)
async def play_music(interaction: discord.Interaction, musica: str):
    """Comando para tocar música"""
    # Verificar se o usuário está em um canal de voz
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        success, message = await bot.music_system.play_song(
            interaction.guild.id,
            interaction.user.voice.channel,
            musica,
            interaction.user
        )
        
        if success:
            await interaction.followup.send(message)
        else:
            await interaction.followup.send(message, ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao tocar música: {e}", ephemeral=True)

@bot.tree.command(name="pause", description="⏸️ Pausa ou retoma a música atual")
async def pause_music(interaction: discord.Interaction):
    """Comando para pausar/retomar música"""
    success, message = await bot.music_system.pause_resume(interaction.guild.id)
    await interaction.response.send_message(message, ephemeral=not success)

@bot.tree.command(name="skip", description="⏭️ Pula a música atual")
async def skip_music(interaction: discord.Interaction):
    """Comando para pular música"""
    success, message = await bot.music_system.skip_song(interaction.guild.id, interaction.user.id)
    await interaction.response.send_message(message)

@bot.tree.command(name="stop", description="⏹️ Para a música e limpa a fila")
async def stop_music(interaction: discord.Interaction):
    """Comando para parar música"""
    success, message = await bot.music_system.stop_music(interaction.guild.id)
    await interaction.response.send_message(message)

@bot.tree.command(name="queue", description="📝 Mostra a fila de músicas")
async def show_queue(interaction: discord.Interaction):
    """Comando para mostrar fila de músicas"""
    queue_info = bot.music_system.get_queue_info(interaction.guild.id)
    
    embed = discord.Embed(
        title="🎵 Fila de Músicas",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Música atual
    if queue_info['current_song']:
        current = queue_info['current_song']
        status = "⏸️ Pausada" if queue_info['is_paused'] else "▶️ Tocando"
        loop_status = " 🔂" if queue_info['loop_mode'] else ""
        
        embed.add_field(
            name=f"{status}{loop_status}",
            value=f"**{current.title}**\n" +
                  f"Duração: {current.format_duration()}\n" +
                  f"Solicitada por: {current.requester.mention}",
            inline=False
        )
    else:
        embed.add_field(
            name="Nenhuma música tocando",
            value="Use `/play` para adicionar músicas!",
            inline=False
        )
    
    # Próximas músicas
    if queue_info['queue']:
        next_songs = []
        for i, song in enumerate(list(queue_info['queue'])[:5], 1):
            next_songs.append(f"{i}. **{song.title}** ({song.format_duration()})")
        
        embed.add_field(
            name=f"📝 Próximas ({queue_info['queue_length']} na fila)",
            value="\n".join(next_songs),
            inline=False
        )
        
        if queue_info['queue_length'] > 5:
            embed.add_field(
                name="",
                value=f"... e mais {queue_info['queue_length'] - 5} músicas",
                inline=False
            )
    
    # Informações adicionais
    embed.add_field(
        name="🔊 Volume",
        value=f"{int(queue_info['volume'] * 100)}%",
        inline=True
    )
    
    embed.set_footer(text="Hawk Esports - Sistema de Música")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="volume", description="🔊 Define o volume da música (0-100)")
@discord.app_commands.describe(
    nivel="Nível do volume (0-100)"
)
async def set_volume(interaction: discord.Interaction, nivel: int):
    """Comando para definir volume"""
    success, message = await bot.music_system.set_volume(interaction.guild.id, nivel)
    await interaction.response.send_message(message, ephemeral=not success)

@bot.tree.command(name="loop", description="🔂 Ativa/desativa repetição da música atual")
async def toggle_loop(interaction: discord.Interaction):
    """Comando para alternar modo de repetição"""
    success, message = await bot.music_system.toggle_loop(interaction.guild.id)
    await interaction.response.send_message(message)

@bot.tree.command(name="shuffle", description="🔀 Embaralha a fila de músicas")
async def shuffle_queue(interaction: discord.Interaction):
    """Comando para embaralhar fila"""
    success, message = await bot.music_system.shuffle_queue(interaction.guild.id)
    await interaction.response.send_message(message, ephemeral=not success)

@bot.tree.command(name="disconnect", description="👋 Desconecta o bot do canal de voz")
async def disconnect_bot(interaction: discord.Interaction):
    """Comando para desconectar do canal de voz"""
    success, message = await bot.music_system.disconnect(interaction.guild.id)
    await interaction.response.send_message(message)

@bot.tree.command(name="nowplaying", description="🎵 Mostra a música atual com barra de progresso")
async def now_playing(interaction: discord.Interaction):
    """Comando para mostrar música atual com progresso"""
    player_info = bot.music_system.get_current_song_info(interaction.guild.id)
    
    if not player_info['current_song']:
        await interaction.response.send_message("❌ Nenhuma música está tocando no momento!", ephemeral=True)
        return
    
    song = player_info['current_song']
    progress = player_info['progress']
    duration = song.duration
    
    # Criar barra de progresso visual
    progress_bar_length = 20
    filled_length = int(progress_bar_length * progress / duration) if duration > 0 else 0
    bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
    
    # Formatar tempo atual e total
    current_time = f"{int(progress // 60):02d}:{int(progress % 60):02d}"
    total_time = song.format_duration()
    
    embed = discord.Embed(
        title="🎵 Tocando Agora",
        description=f"**{song.title}**",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    if song.thumbnail:
        embed.set_thumbnail(url=song.thumbnail)
    
    embed.add_field(
        name="⏱️ Progresso",
        value=f"`{current_time}` {bar} `{total_time}`\n`{current_time}/{total_time}`",
        inline=False
    )
    
    embed.add_field(
        name="👤 Solicitada por",
        value=song.requester.mention,
        inline=True
    )
    
    embed.add_field(
        name="🔊 Volume",
        value=f"{int(player_info['volume'] * 100)}%",
        inline=True
    )
    
    status_icons = []
    if player_info['is_paused']:
        status_icons.append("⏸️ Pausada")
    else:
        status_icons.append("▶️ Tocando")
    
    if player_info['loop_mode']:
        status_icons.append("🔂 Loop")
    
    if status_icons:
        embed.add_field(
            name="📊 Status",
            value=" | ".join(status_icons),
            inline=True
        )
    
    # Próximas músicas na fila
    if player_info['queue_length'] > 0:
        next_songs = []
        for i, next_song in enumerate(list(player_info['queue'])[:3], 1):
            next_songs.append(f"{i}. **{next_song.title}** ({next_song.format_duration()})")
        
        embed.add_field(
            name=f"📝 Próximas ({player_info['queue_length']} na fila)",
            value="\n".join(next_songs) if next_songs else "Fila vazia",
            inline=False
        )
    
    embed.set_footer(text="Hawk Esports - Sistema de Música Avançado")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="history", description="📜 Mostra o histórico de músicas tocadas")
@discord.app_commands.describe(
    limite="Número de músicas no histórico (máximo 20)"
)
async def music_history(interaction: discord.Interaction, limite: int = 10):
    """Comando para mostrar histórico de músicas"""
    if limite > 20:
        limite = 20
    elif limite < 1:
        limite = 10
    
    history = bot.music_system.get_music_history(interaction.guild.id, limite)
    
    if not history:
        await interaction.response.send_message("📜 Nenhuma música foi tocada ainda neste servidor!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📜 Histórico de Músicas",
        description=f"Últimas {len(history)} músicas tocadas",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    history_text = []
    for i, song_info in enumerate(history, 1):
        song = song_info['song']
        played_at = song_info['played_at']
        time_ago = datetime.now() - played_at
        
        if time_ago.days > 0:
            time_str = f"{time_ago.days}d atrás"
        elif time_ago.seconds > 3600:
            time_str = f"{time_ago.seconds // 3600}h atrás"
        elif time_ago.seconds > 60:
            time_str = f"{time_ago.seconds // 60}m atrás"
        else:
            time_str = "Agora mesmo"
        
        history_text.append(
            f"`{i:2d}.` **{song.title}** ({song.format_duration()})\n"
            f"     👤 {song.requester.display_name} • ⏰ {time_str}"
        )
    
    # Dividir em chunks se necessário
    if len(history_text) <= 5:
        embed.add_field(
            name="🎵 Músicas Tocadas",
            value="\n\n".join(history_text),
            inline=False
        )
    else:
        # Primeira metade
        embed.add_field(
            name="🎵 Músicas Tocadas (Parte 1)",
            value="\n\n".join(history_text[:5]),
            inline=False
        )
        # Segunda metade
        if len(history_text) > 5:
            embed.add_field(
                name="🎵 Músicas Tocadas (Parte 2)",
                value="\n\n".join(history_text[5:]),
                inline=False
            )
    
    embed.set_footer(text="Hawk Esports - Histórico de Música")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="favorites", description="⭐ Gerencia suas músicas favoritas")
@discord.app_commands.describe(
    acao="Ação a realizar",
    posicao="Posição da música na fila (para adicionar aos favoritos)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="📋 Listar favoritas", value="list"),
    discord.app_commands.Choice(name="⭐ Adicionar atual", value="add_current"),
    discord.app_commands.Choice(name="➕ Adicionar da fila", value="add_queue"),
    discord.app_commands.Choice(name="🗑️ Remover", value="remove"),
    discord.app_commands.Choice(name="🎵 Tocar favorita", value="play")
])
async def music_favorites(interaction: discord.Interaction, acao: str, posicao: int = None):
    """Comando para gerenciar músicas favoritas"""
    user_id = interaction.user.id
    
    if acao == "list":
        favorites = bot.music_system.get_user_favorites(user_id)
        
        if not favorites:
            await interaction.response.send_message("⭐ Você ainda não tem músicas favoritas!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⭐ Suas Músicas Favoritas",
            description=f"Você tem {len(favorites)} música(s) favorita(s)",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        favorites_text = []
        for i, fav_info in enumerate(favorites, 1):
            song = fav_info['song']
            added_at = fav_info['added_at']
            
            favorites_text.append(
                f"`{i:2d}.` **{song.title}** ({song.format_duration()})\n"
                f"     📅 Adicionada em {added_at.strftime('%d/%m/%Y às %H:%M')}"
            )
        
        # Dividir em chunks se necessário
        if len(favorites_text) <= 5:
            embed.add_field(
                name="🎵 Suas Favoritas",
                value="\n\n".join(favorites_text),
                inline=False
            )
        else:
            # Primeira metade
            embed.add_field(
                name="🎵 Suas Favoritas (Parte 1)",
                value="\n\n".join(favorites_text[:5]),
                inline=False
            )
            # Segunda metade
            if len(favorites_text) > 5:
                embed.add_field(
                    name="🎵 Suas Favoritas (Parte 2)",
                    value="\n\n".join(favorites_text[5:]),
                    inline=False
                )
        
        embed.set_footer(text="Use /favorites acao:tocar para tocar uma favorita")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    elif acao == "add_current":
        current_info = bot.music_system.get_current_song_info(interaction.guild.id)
        
        if not current_info['current_song']:
            await interaction.response.send_message("❌ Não há música tocando no momento!", ephemeral=True)
            return
        
        success, message = bot.music_system.add_to_favorites(user_id, current_info['current_song'])
        
        if success:
            embed = discord.Embed(
                title="⭐ Música Adicionada aos Favoritos!",
                description=f"**{current_info['current_song'].title}** foi adicionada às suas favoritas!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "add_queue":
        if posicao is None:
            await interaction.response.send_message("❌ Você precisa especificar a posição da música na fila!", ephemeral=True)
            return
        
        queue_info = bot.music_system.get_queue_info(interaction.guild.id)
        
        if not queue_info['queue'] or posicao < 1 or posicao > len(queue_info['queue']):
            await interaction.response.send_message(f"❌ Posição inválida! A fila tem {len(queue_info['queue'])} música(s).", ephemeral=True)
            return
        
        song = queue_info['queue'][posicao - 1]
        success, message = bot.music_system.add_to_favorites(user_id, song)
        
        if success:
            embed = discord.Embed(
                title="⭐ Música Adicionada aos Favoritos!",
                description=f"**{song.title}** foi adicionada às suas favoritas!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "remove":
        if posicao is None:
            await interaction.response.send_message("❌ Você precisa especificar a posição da música favorita para remover!", ephemeral=True)
            return
        
        success, message = bot.music_system.remove_from_favorites(user_id, posicao - 1)
        
        if success:
            await interaction.response.send_message(f"✅ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "play":
        if posicao is None:
            await interaction.response.send_message("❌ Você precisa especificar a posição da música favorita para tocar!", ephemeral=True)
            return
        
        # Verificar se usuário está em canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
            return
        
        favorites = bot.music_system.get_user_favorites(user_id)
        
        if not favorites or posicao < 1 or posicao > len(favorites):
            await interaction.response.send_message(f"❌ Posição inválida! Você tem {len(favorites)} música(s) favorita(s).", ephemeral=True)
            return
        
        song = favorites[posicao - 1]['song']
        
        # Adicionar à fila
        success, message = await bot.music_system.play_song(
            interaction.guild.id,
            interaction.user.voice.channel,
            song.url,
            interaction.user
        )
        
        if success:
            embed = discord.Embed(
                title="⭐ Favorita Adicionada à Fila!",
                description=f"**{song.title}** foi adicionada à fila!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)

@bot.tree.command(name="playlist", description="🎵 Gerencia suas playlists personalizadas")
@discord.app_commands.describe(
    acao="Ação a realizar",
    nome="Nome da playlist",
    musica="URL ou nome da música (para adicionar/remover)",
    posicao="Posição da música (para remover)",
    publica="Tornar playlist pública (padrão: privada)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="📋 Listar playlists", value="list"),
    discord.app_commands.Choice(name="➕ Criar playlist", value="create"),
    discord.app_commands.Choice(name="🗑️ Deletar playlist", value="delete"),
    discord.app_commands.Choice(name="🎵 Mostrar playlist", value="show"),
    discord.app_commands.Choice(name="➕ Adicionar música", value="add"),
    discord.app_commands.Choice(name="➖ Remover música", value="remove"),
    discord.app_commands.Choice(name="▶️ Tocar playlist", value="play"),
    discord.app_commands.Choice(name="🌐 Playlists públicas", value="public")
])
async def playlist_manager(interaction: discord.Interaction, acao: str, nome: str = None, musica: str = None, posicao: int = None, publica: bool = False):
    """Comando para gerenciar playlists"""
    user_id = interaction.user.id
    
    if acao == "list":
        playlists = bot.music_system.get_user_playlists(user_id)
        
        if not playlists:
            await interaction.response.send_message("🎵 Você ainda não tem playlists criadas!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎵 Suas Playlists",
            description=f"Você tem {len(playlists)} playlist(s)",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        playlist_text = []
        for i, (playlist_name, playlist_data) in enumerate(playlists.items(), 1):
            visibility = "🌐 Pública" if playlist_data.get('public', False) else "🔒 Privada"
            song_count = len(playlist_data.get('songs', []))
            created_at = playlist_data.get('created_at', datetime.now())
            
            playlist_text.append(
                f"`{i:2d}.` **{playlist_name}** ({song_count} música(s))\n"
                f"     {visibility} • 📅 {created_at.strftime('%d/%m/%Y')}"
            )
        
        if len(playlist_text) <= 10:
            embed.add_field(
                name="📋 Suas Playlists",
                value="\n\n".join(playlist_text),
                inline=False
            )
        else:
            # Dividir em duas partes
            embed.add_field(
                name="📋 Suas Playlists (Parte 1)",
                value="\n\n".join(playlist_text[:10]),
                inline=False
            )
            embed.add_field(
                name="📋 Suas Playlists (Parte 2)",
                value="\n\n".join(playlist_text[10:]),
                inline=False
            )
        
        embed.set_footer(text="Use /playlist acao:show nome:<nome> para ver uma playlist")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    elif acao == "create":
        if not nome:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist!", ephemeral=True)
            return
        
        success, message = bot.music_system.create_playlist(user_id, nome, publica)
        
        if success:
            visibility = "pública" if publica else "privada"
            embed = discord.Embed(
                title="✅ Playlist Criada!",
                description=f"Playlist **{nome}** ({visibility}) foi criada com sucesso!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "delete":
        if not nome:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist!", ephemeral=True)
            return
        
        success, message = bot.music_system.delete_playlist(user_id, nome)
        
        if success:
            await interaction.response.send_message(f"✅ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "show":
        if not nome:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist!", ephemeral=True)
            return
        
        playlist_data = bot.music_system.get_playlist(user_id, nome)
        
        if not playlist_data:
            await interaction.response.send_message(f"❌ Playlist '{nome}' não encontrada!", ephemeral=True)
            return
        
        songs = playlist_data.get('songs', [])
        visibility = "🌐 Pública" if playlist_data.get('public', False) else "🔒 Privada"
        created_at = playlist_data.get('created_at', datetime.now())
        
        embed = discord.Embed(
            title=f"🎵 Playlist: {nome}",
            description=f"{visibility} • {len(songs)} música(s) • Criada em {created_at.strftime('%d/%m/%Y')}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if not songs:
            embed.add_field(
                name="📭 Playlist Vazia",
                value="Esta playlist não possui músicas ainda.\nUse `/playlist acao:add` para adicionar músicas!",
                inline=False
            )
        else:
            song_text = []
            for i, song_data in enumerate(songs, 1):
                duration_str = f"{song_data['duration'] // 60}:{song_data['duration'] % 60:02d}" if song_data['duration'] > 0 else "N/A"
                song_text.append(
                    f"`{i:2d}.` **{song_data['title']}** ({duration_str})"
                )
            
            # Dividir em chunks se necessário
            if len(song_text) <= 15:
                embed.add_field(
                    name="🎵 Músicas",
                    value="\n".join(song_text),
                    inline=False
                )
            else:
                # Primeira metade
                embed.add_field(
                    name="🎵 Músicas (Parte 1)",
                    value="\n".join(song_text[:15]),
                    inline=False
                )
                # Segunda metade
                embed.add_field(
                    name="🎵 Músicas (Parte 2)",
                    value="\n".join(song_text[15:]),
                    inline=False
                )
        
        embed.set_footer(text="Use /playlist acao:play para tocar esta playlist")
        await interaction.response.send_message(embed=embed)
    
    elif acao == "add":
        if not nome or not musica:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist e a música!", ephemeral=True)
            return
        
        # Buscar a música
        await interaction.response.defer(ephemeral=True)
        
        song_data = await bot.music_system.search_song(musica)
        if not song_data:
            await interaction.followup.send("❌ Não foi possível encontrar esta música!", ephemeral=True)
            return
        
        success, message = bot.music_system.add_to_playlist(user_id, nome, song_data)
        
        if success:
            embed = discord.Embed(
                title="✅ Música Adicionada!",
                description=f"**{song_data['title']}** foi adicionada à playlist **{nome}**!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
    
    elif acao == "remove":
        if not nome:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist!", ephemeral=True)
            return
        
        if posicao is None:
            await interaction.response.send_message("❌ Você precisa especificar a posição da música para remover!", ephemeral=True)
            return
        
        success, message = bot.music_system.remove_from_playlist(user_id, nome, posicao - 1)
        
        if success:
            await interaction.response.send_message(f"✅ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    elif acao == "play":
        if not nome:
            await interaction.response.send_message("❌ Você precisa especificar o nome da playlist!", ephemeral=True)
            return
        
        # Verificar se usuário está em canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success, message = await bot.music_system.play_playlist(interaction.guild.id, interaction.user.voice.channel, user_id, nome, interaction.user)
        
        if success:
            embed = discord.Embed(
                title="🎵 Playlist Adicionada à Fila!",
                description=f"Playlist **{nome}** foi adicionada à fila de música!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {message}")
    
    elif acao == "public":
        public_playlists = bot.music_system.get_public_playlists()
        
        if not public_playlists:
            await interaction.response.send_message("🌐 Não há playlists públicas disponíveis no momento!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🌐 Playlists Públicas",
            description=f"Encontradas {len(public_playlists)} playlist(s) pública(s)",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        playlist_text = []
        for i, (owner_name, playlist_name, playlist_data) in enumerate(public_playlists, 1):
            song_count = len(playlist_data.get('songs', []))
            created_at = playlist_data.get('created_at', datetime.now())
            
            playlist_text.append(
                f"`{i:2d}.` **{playlist_name}** por {owner_name}\n"
                f"     🎵 {song_count} música(s) • 📅 {created_at.strftime('%d/%m/%Y')}"
            )
        
        if len(playlist_text) <= 10:
            embed.add_field(
                name="🌐 Playlists Disponíveis",
                value="\n\n".join(playlist_text),
                inline=False
            )
        else:
            # Dividir em duas partes
            embed.add_field(
                name="🌐 Playlists Disponíveis (Parte 1)",
                value="\n\n".join(playlist_text[:10]),
                inline=False
            )
            embed.add_field(
                name="🌐 Playlists Disponíveis (Parte 2)",
                value="\n\n".join(playlist_text[10:]),
                inline=False
            )
        
        embed.set_footer(text="Use /playlist acao:show nome:<nome> para ver uma playlist pública")
        await interaction.response.send_message(embed=embed)

# ==================== COMANDOS DE CANAIS DINÂMICOS ====================

@bot.tree.command(name="dynamic_channels", description="🎮 Gerenciar sistema de canais dinâmicos")
@app_commands.describe(
    acao="Ação a ser executada",
    canal="Canal de voz para configurar como trigger (apenas para 'add_trigger' e 'remove_trigger')"
)
@app_commands.choices(acao=[
    app_commands.Choice(name="📊 Status do Sistema", value="status"),
    app_commands.Choice(name="⚙️ Configurar Servidor", value="setup"),
    app_commands.Choice(name="➕ Adicionar Canal Trigger", value="add_trigger"),
    app_commands.Choice(name="➖ Remover Canal Trigger", value="remove_trigger"),
    app_commands.Choice(name="📈 Estatísticas", value="stats"),
    app_commands.Choice(name="🔄 Recarregar Config", value="reload")
])
async def dynamic_channels_cmd(interaction: discord.Interaction, acao: str, canal: discord.VoiceChannel = None):
    """Comando principal para gerenciar canais dinâmicos"""
    
    # Verificar permissões
    if not interaction.user.guild_permissions.manage_channels:
        embed = discord.Embed(
            title="❌ Sem Permissão",
            description="Você precisa da permissão `Gerenciar Canais` para usar este comando.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        if acao == "status":
            config = bot.dynamic_channels.config
            temp_enabled = config.get('temp_channels', {}).get('enabled', True)
            rank_enabled = config.get('rank_channels', {}).get('enabled', True)
            
            embed = discord.Embed(
                title="🎮 Status dos Canais Dinâmicos",
                color=0x00BFFF
            )
            embed.add_field(
                name="📊 Sistema Geral",
                value=f"Status: {'🟢 Ativo' if (temp_enabled or rank_enabled) else '🔴 Inativo'}",
                inline=False
            )
            embed.add_field(
                name="🎮 Canais Temporários",
                value=f"Status: {'🟢 Ativo' if temp_enabled else '🔴 Inativo'}\n"
                      f"Máximo: {config.get('temp_channels', {}).get('max_temp_channels', 20)}\n"
                      f"Timeout: {config.get('temp_channels', {}).get('empty_timeout_minutes', 5)} min",
                inline=True
            )
            embed.add_field(
                name="🏆 Canais por Patente",
                value=f"Status: {'🟢 Ativo' if rank_enabled else '🔴 Inativo'}\n"
                      f"Min. membros: {config.get('rank_channels', {}).get('min_members_per_rank', 3)}",
                inline=True
            )
            
            trigger_channels = config.get('trigger_channels', [])
            if trigger_channels:
                channels_text = "\n".join([f"<#{ch_id}>" for ch_id in trigger_channels])
                embed.add_field(
                    name="🎯 Canais Trigger",
                    value=channels_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎯 Canais Trigger",
                    value="Nenhum configurado",
                    inline=False
                )
        
        elif acao == "setup":
            await bot.dynamic_channels.setup_trigger_channels(interaction.guild)
            embed = discord.Embed(
                title="✅ Sistema Configurado",
                description="Sistema de canais dinâmicos foi configurado com sucesso!\n\n"
                           "📋 **Próximos passos:**\n"
                           "• Use `/dynamic_channels add_trigger` para adicionar canais trigger\n"
                           "• Membros podem entrar nos canais trigger para criar salas temporárias",
                color=0x00FF00
            )
        
        elif acao == "add_trigger":
            if not canal:
                embed = discord.Embed(
                    title="❌ Canal Necessário",
                    description="Você deve especificar um canal de voz para adicionar como trigger.",
                    color=0xFF0000
                )
            else:
                success = await bot.dynamic_channels.add_trigger_channel(canal.id)
                if success:
                    embed = discord.Embed(
                        title="✅ Canal Trigger Adicionado",
                        description=f"O canal {canal.mention} foi configurado como trigger.\n\n"
                                   "Agora quando membros entrarem neste canal, uma sala temporária será criada automaticamente.",
                        color=0x00FF00
                    )
                else:
                    embed = discord.Embed(
                        title="⚠️ Canal já Configurado",
                        description=f"O canal {canal.mention} já está configurado como trigger.",
                        color=0xFFFF00
                    )
        
        elif acao == "remove_trigger":
            if not canal:
                embed = discord.Embed(
                    title="❌ Canal Necessário",
                    description="Você deve especificar um canal de voz para remover como trigger.",
                    color=0xFF0000
                )
            else:
                success = await bot.dynamic_channels.remove_trigger_channel(canal.id)
                if success:
                    embed = discord.Embed(
                        title="✅ Canal Trigger Removido",
                        description=f"O canal {canal.mention} foi removido dos triggers.",
                        color=0x00FF00
                    )
                else:
                    embed = discord.Embed(
                        title="⚠️ Canal não Encontrado",
                        description=f"O canal {canal.mention} não estava configurado como trigger.",
                        color=0xFFFF00
                    )
        
        elif acao == "stats":
            stats = bot.dynamic_channels.get_stats()
            embed = discord.Embed(
                title="📈 Estatísticas dos Canais Dinâmicos",
                color=0x00BFFF
            )
            embed.add_field(
                name="🎮 Canais Temporários",
                value=f"Ativos: {stats['temp_channels_active']}",
                inline=True
            )
            embed.add_field(
                name="🏆 Canais por Patente",
                value=f"Total: {stats['rank_channels_total']}",
                inline=True
            )
            embed.add_field(
                name="🎯 Canais Trigger",
                value=f"Configurados: {stats['trigger_channels']}",
                inline=True
            )
        
        elif acao == "reload":
            bot.dynamic_channels.config = bot.dynamic_channels.load_config()
            embed = discord.Embed(
                title="🔄 Configuração Recarregada",
                description="As configurações dos canais dinâmicos foram recarregadas do arquivo.",
                color=0x00FF00
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando dynamic_channels: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro ao executar o comando: {str(e)}",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="music_channels", description="🎵 Gerencia o sistema de canais de música automáticos")
@discord.app_commands.describe(
    acao="Ação a realizar",
    canal="Canal para configurar (quando aplicável)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Status", value="status"),
    discord.app_commands.Choice(name="Configurar Servidor", value="setup"),
    discord.app_commands.Choice(name="Adicionar Canal Trigger", value="add_trigger"),
    discord.app_commands.Choice(name="Remover Canal Trigger", value="remove_trigger"),
    discord.app_commands.Choice(name="Estatísticas", value="stats"),
    discord.app_commands.Choice(name="Recarregar Config", value="reload")
])
async def music_channels(interaction: discord.Interaction, acao: str, canal: discord.VoiceChannel = None):
    """Comando para gerenciar canais de música automáticos"""
    try:
        # Verificar permissões
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="❌ Acesso Negado",
                description="Você não tem permissão para gerenciar canais de música.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if acao == "status":
            config = bot.music_channels.config
            embed = discord.Embed(
                title="🎵 Status dos Canais de Música",
                description="Estado atual do sistema de canais de música automáticos",
                color=0x9932CC
            )
            embed.add_field(
                name="🔧 Sistema",
                value="✅ Ativo" if config.get('enabled', False) else "❌ Inativo",
                inline=True
            )
            embed.add_field(
                name="🎯 Canais Trigger",
                value=str(len(config.get('trigger_channels', []))),
                inline=True
            )
            embed.add_field(
                name="🎵 Canais Ativos",
                value=str(len(bot.music_channels.active_channels)),
                inline=True
            )
        
        elif acao == "setup":
            success = await bot.music_channels.setup_server(interaction.guild)
            if success:
                embed = discord.Embed(
                    title="✅ Servidor Configurado",
                    description="Sistema de canais de música configurado com sucesso!",
                    color=0x00FF00
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro na Configuração",
                    description="Não foi possível configurar o servidor.",
                    color=0xFF0000
                )
        
        elif acao == "add_trigger":
            if not canal:
                embed = discord.Embed(
                    title="❌ Canal Necessário",
                    description="Você precisa especificar um canal de voz.",
                    color=0xFF0000
                )
            else:
                success = await bot.music_channels.add_trigger_channel(canal.id)
                if success:
                    embed = discord.Embed(
                        title="✅ Canal Adicionado",
                        description=f"Canal {canal.mention} adicionado como trigger de música.",
                        color=0x00FF00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="Não foi possível adicionar o canal.",
                        color=0xFF0000
                    )
        
        elif acao == "remove_trigger":
            if not canal:
                embed = discord.Embed(
                    title="❌ Canal Necessário",
                    description="Você precisa especificar um canal de voz.",
                    color=0xFF0000
                )
            else:
                success = await bot.music_channels.remove_trigger_channel(canal.id)
                if success:
                    embed = discord.Embed(
                        title="✅ Canal Removido",
                        description=f"Canal {canal.mention} removido dos triggers de música.",
                        color=0x00FF00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="Não foi possível remover o canal.",
                        color=0xFF0000
                    )
        
        elif acao == "stats":
            stats = bot.music_channels.get_stats()
            embed = discord.Embed(
                title="📊 Estatísticas dos Canais de Música",
                description="Estatísticas detalhadas do sistema",
                color=0x9932CC
            )
            embed.add_field(
                name="🎵 Canais Criados",
                value=f"Total: {stats['music_channels_total']}",
                inline=True
            )
            embed.add_field(
                name="🎯 Canais Trigger",
                value=f"Configurados: {stats['trigger_channels']}",
                inline=True
            )
            embed.add_field(
                name="🎶 Canais Ativos",
                value=f"Atualmente: {stats['active_channels']}",
                inline=True
            )
        
        elif acao == "reload":
            bot.music_channels.config = bot.music_channels.load_config()
            embed = discord.Embed(
                title="🔄 Configuração Recarregada",
                description="As configurações dos canais de música foram recarregadas do arquivo.",
                color=0x00FF00
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando music_channels: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Ocorreu um erro ao executar o comando: {str(e)}",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== COMANDOS DE MODERAÇÃO ====================

@bot.tree.command(name="warn", description="⚠️ Aplica advertência a um usuário")
@discord.app_commands.describe(
    usuario="Usuário a ser advertido",
    motivo="Motivo da advertência"
)
async def warn_user(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Não especificado"):
    """Comando para advertir usuário"""
    if not interaction.user.guild_permissions.moderate_members:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Você não tem permissão para usar este comando.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    result = await bot.moderation_system.warn_user(usuario, interaction.user, motivo)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="warnings", description="📋 Mostra advertências de um usuário")
@discord.app_commands.describe(usuario="Usuário para verificar advertências")
async def show_warnings(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para mostrar advertências"""
    if usuario is None:
        usuario = interaction.user
    
    if not interaction.user.guild_permissions.moderate_members and usuario != interaction.user:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Você só pode ver suas próprias advertências.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    result = await bot.moderation_system.get_user_warnings(usuario)
    await interaction.followup.send(embed=result, ephemeral=True)

@bot.tree.command(name="clear_warnings", description="🧹 Remove advertências de um usuário")
@discord.app_commands.describe(usuario="Usuário para limpar advertências")
async def clear_warnings(interaction: discord.Interaction, usuario: discord.Member):
    """Comando para limpar advertências"""
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Apenas administradores podem limpar advertências.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    result = await bot.moderation_system.clear_user_warnings(usuario, interaction.user)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="automod", description="🛡️ Configura sistema de moderação automática")
@discord.app_commands.describe(
    acao="Ação a realizar",
    valor="Valor da configuração"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Ativar/Desativar", value="toggle"),
    discord.app_commands.Choice(name="Limite de Spam", value="spam_limit"),
    discord.app_commands.Choice(name="Filtro de Toxicidade", value="toxicity_filter"),
    discord.app_commands.Choice(name="Proteção Anti-Raid", value="raid_protection"),
    discord.app_commands.Choice(name="Status", value="status")
])
async def automod_config(interaction: discord.Interaction, acao: str, valor: str = None):
    """Comando para configurar automoderação"""
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Apenas administradores podem configurar a automoderação.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    result = await bot.moderation_system.configure_automod(interaction.guild.id, acao, valor)
    await interaction.followup.send(embed=result)

# ==================== COMANDOS MINI-GAMES ====================

@bot.tree.command(name="pedra_papel_tesoura", description="🎮 Jogue pedra, papel, tesoura contra o bot")
@discord.app_commands.describe(escolha="Sua escolha: pedra, papel ou tesoura")
@discord.app_commands.choices(escolha=[
    discord.app_commands.Choice(name="🪨 Pedra", value="pedra"),
    discord.app_commands.Choice(name="📄 Papel", value="papel"),
    discord.app_commands.Choice(name="✂️ Tesoura", value="tesoura")
])
async def rock_paper_scissors(interaction: discord.Interaction, escolha: str):
    """Comando para jogar pedra, papel, tesoura"""
    await interaction.response.defer()
    result = await bot.minigames_system.play_rock_paper_scissors(interaction, escolha)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="quiz_pubg", description="🧠 Teste seus conhecimentos sobre PUBG")
@discord.app_commands.describe(dificuldade="Nível de dificuldade do quiz")
@discord.app_commands.choices(dificuldade=[
    discord.app_commands.Choice(name="🟢 Fácil", value="easy"),
    discord.app_commands.Choice(name="🟡 Médio", value="medium"),
    discord.app_commands.Choice(name="🔴 Difícil", value="hard"),
    discord.app_commands.Choice(name="🎲 Aleatório", value="random")
])
async def pubg_quiz(interaction: discord.Interaction, dificuldade: str = "random"):
    """Comando para iniciar quiz PUBG"""
    difficulty = None if dificuldade == "random" else dificuldade
    
    await interaction.response.defer()
    result = await bot.minigames_system.play_quiz(interaction, difficulty)
    
    # Enviar pergunta e adicionar reações
    message = await interaction.followup.send(embed=result)
    
    # Adicionar reações para as opções
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
    for emoji in emojis:
        await message.add_reaction(emoji)

@bot.tree.command(name="roleta", description="🎰 Aposte seus pontos na roleta da sorte")
@discord.app_commands.describe(pontos="Quantidade de pontos para apostar")
async def roulette(interaction: discord.Interaction, pontos: int):
    """Comando para jogar na roleta"""
    await interaction.response.defer()
    result = await bot.minigames_system.play_roulette(interaction, pontos)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="stats_jogos", description="📊 Veja suas estatísticas nos mini-games")
@discord.app_commands.describe(usuario="Usuário para ver estatísticas (opcional)")
async def game_stats(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para ver estatísticas de jogos"""
    target_user = usuario or interaction.user
    
    await interaction.response.defer()
    result = await bot.minigames_system.get_player_stats(target_user)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="desafio_diario", description="🏆 Veja seu desafio diário")
async def daily_challenge(interaction: discord.Interaction):
    """Comando para ver desafio diário"""
    await interaction.response.defer()
    result = await bot.minigames_system.get_daily_challenge_status(interaction.user)
    await interaction.followup.send(embed=result)

@bot.tree.command(name="ranking_jogos", description="🏆 Veja o ranking dos mini-games")
@discord.app_commands.describe(categoria="Categoria do ranking")
@discord.app_commands.choices(categoria=[
    discord.app_commands.Choice(name="💰 Pontos Totais", value="points"),
    discord.app_commands.Choice(name="🎮 Jogos Jogados", value="games"),
    discord.app_commands.Choice(name="🏆 Vitórias", value="wins"),
    discord.app_commands.Choice(name="🧠 Quiz Corretos", value="quiz")
])
async def games_leaderboard(interaction: discord.Interaction, categoria: str = "points"):
    """Comando para ver ranking dos jogos"""
    await interaction.response.defer()
    result = await bot.minigames_system.get_leaderboard(interaction.guild, categoria)
    await interaction.followup.send(embed=result)

# ==================== INICIALIZAÇÃO ====================

# ==================== COMANDOS DE GRÁFICOS ====================

@bot.tree.command(name="grafico_rank", description="📈 Mostra gráfico de progresso do seu rank")
async def grafico_rank(interaction: discord.Interaction):
    """Comando para gerar gráfico de progresso de rank"""
    try:
        await interaction.response.defer()
        
        # Gerar gráfico
        chart_file = await bot.charts_system.generate_rank_progress_chart(interaction.user)
        embed = await bot.charts_system.get_chart_embed('rank_progress', interaction.user)
        
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        logger.error(f"Erro no comando grafico_rank: {e}")
        await interaction.followup.send("❌ Erro ao gerar gráfico de rank. Tente novamente.", ephemeral=True)

@bot.tree.command(name="grafico_jogos", description="🎮 Mostra gráfico de performance nos mini-games")
async def grafico_jogos(interaction: discord.Interaction):
    """Comando para gerar gráfico de performance em jogos"""
    try:
        await interaction.response.defer()
        
        # Gerar gráfico
        chart_file = await bot.charts_system.generate_games_performance_chart(interaction.user)
        embed = await bot.charts_system.get_chart_embed('games_performance', interaction.user)
        
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        logger.error(f"Erro no comando grafico_jogos: {e}")
        await interaction.followup.send("❌ Erro ao gerar gráfico de jogos. Tente novamente.", ephemeral=True)

@bot.tree.command(name="mapa_atividade", description="🔥 Mostra mapa de calor da sua atividade")
async def mapa_atividade(interaction: discord.Interaction):
    """Comando para gerar heatmap de atividade"""
    try:
        await interaction.response.defer()
        
        # Gerar gráfico
        chart_file = await bot.charts_system.generate_activity_heatmap(interaction.user)
        embed = await bot.charts_system.get_chart_embed('activity_heatmap', interaction.user)
        
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        logger.error(f"Erro no comando mapa_atividade: {e}")
        await interaction.followup.send("❌ Erro ao gerar mapa de atividade. Tente novamente.", ephemeral=True)

@bot.tree.command(name="progresso_conquistas", description="🏆 Mostra progresso das suas conquistas")
async def progresso_conquistas(interaction: discord.Interaction):
    """Comando para gerar gráfico de progresso de conquistas"""
    try:
        await interaction.response.defer()
        
        # Gerar gráfico
        chart_file = await bot.charts_system.generate_achievements_progress(interaction.user)
        embed = await bot.charts_system.get_chart_embed('achievements_progress', interaction.user)
        
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        logger.error(f"Erro no comando progresso_conquistas: {e}")
        await interaction.followup.send("❌ Erro ao gerar gráfico de conquistas. Tente novamente.", ephemeral=True)

@bot.tree.command(name="comparacao_radar", description="⚡ Compara sua performance com a média do servidor")
async def comparacao_radar(interaction: discord.Interaction):
    """Comando para gerar gráfico radar de comparação"""
    try:
        await interaction.response.defer()
        
        # Gerar gráfico
        chart_file = await bot.charts_system.generate_comparison_radar(interaction.user)
        embed = await bot.charts_system.get_chart_embed('comparison_radar', interaction.user)
        
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        logger.error(f"Erro no comando comparacao_radar: {e}")
        await interaction.followup.send("❌ Erro ao gerar gráfico de comparação. Tente novamente.", ephemeral=True)

@bot.tree.command(name="relatorio_completo", description="📋 Gera relatório completo com todos os gráficos")
async def relatorio_completo(interaction: discord.Interaction):
    """Comando para gerar relatório completo"""
    try:
        await interaction.response.defer()
        
        # Gerar todos os gráficos
        chart_files = await bot.charts_system.generate_comprehensive_report(interaction.user)
        embed = await bot.charts_system.get_chart_embed('comprehensive', interaction.user)
        
        if chart_files:
            await interaction.followup.send(embed=embed, files=chart_files)
        else:
            await interaction.followup.send("❌ Erro ao gerar relatório completo. Tente novamente.", ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro no comando relatorio_completo: {e}")
        await interaction.followup.send("❌ Erro ao gerar relatório completo. Tente novamente.", ephemeral=True)

@bot.tree.command(name="graficos_help", description="❓ Ajuda sobre o sistema de gráficos")
async def graficos_help(interaction: discord.Interaction):
    """Comando de ajuda para gráficos"""
    embed = discord.Embed(
        title="📊 Sistema de Gráficos - Ajuda",
        description="Visualize seu progresso com gráficos interativos!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📈 Comandos Disponíveis",
        value="• `/grafico_rank` - Progresso de rank\n"
              "• `/grafico_jogos` - Performance em jogos\n"
              "• `/mapa_atividade` - Mapa de atividade\n"
              "• `/progresso_conquistas` - Progresso de conquistas\n"
              "• `/comparacao_radar` - Comparação com servidor\n"
              "• `/relatorio_completo` - Relatório completo",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Informações",
        value="• Gráficos atualizados a cada 5 minutos\n"
              "• Dados coletados de todos os sistemas\n"
              "• Cache automático para melhor performance",
        inline=False
    )
    
    embed.set_footer(text="Hawk Bot - Sistema de Gráficos")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== COMANDOS DE NOTIFICAÇÕES ====================

@bot.tree.command(name="notificacoes", description="Ver suas notificações")
@app_commands.describe(
    apenas_nao_lidas="Mostrar apenas notificações não lidas",
    limite="Número máximo de notificações para mostrar (1-20)"
)
async def notificacoes_command(interaction: discord.Interaction, apenas_nao_lidas: bool = False, limite: int = 10):
    """Comando para ver notificações do usuário"""
    try:
        if limite < 1 or limite > 20:
            limite = 10
        
        notifications = await bot.notifications_system.get_user_notifications(
            interaction.user.id, unread_only=apenas_nao_lidas, limit=limite
        )
        
        if not notifications:
            embed = discord.Embed(
                title="📭 Nenhuma Notificação",
                description="Você não possui notificações" + (" não lidas" if apenas_nao_lidas else "") + ".",
                color=0x95A5A6
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🔔 Suas Notificações ({len(notifications)})",
            color=0x3498DB
        )
        
        for i, notif in enumerate(notifications[:5], 1):  # Mostrar apenas 5 por página
            status_icon = "📖" if notif.is_read else "🔔"
            time_str = notif.created_at.strftime("%d/%m %H:%M")
            
            embed.add_field(
                name=f"{status_icon} {notif.title}",
                value=f"{notif.message[:100]}{'...' if len(notif.message) > 100 else ''}\n*{time_str}*",
                inline=False
            )
        
        if len(notifications) > 5:
            embed.set_footer(text=f"Mostrando 5 de {len(notifications)} notificações. Use /marcar_lidas para gerenciar.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro no comando notificações: {e}")
        await interaction.response.send_message("❌ Erro ao buscar notificações.", ephemeral=True)

@bot.tree.command(name="marcar_lidas", description="Marcar todas as notificações como lidas")
async def marcar_lidas_command(interaction: discord.Interaction):
    """Comando para marcar todas as notificações como lidas"""
    try:
        count = await bot.notifications_system.mark_all_as_read(interaction.user.id)
        
        if count > 0:
            embed = discord.Embed(
                title="✅ Notificações Marcadas",
                description=f"Marcadas {count} notificações como lidas.",
                color=0x27AE60
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Nenhuma Ação Necessária",
                description="Você não possui notificações não lidas.",
                color=0x95A5A6
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro ao marcar notificações como lidas: {e}")
        await interaction.response.send_message("❌ Erro ao marcar notificações.", ephemeral=True)

@bot.tree.command(name="config_notificacoes", description="Configurar suas preferências de notificações")
@app_commands.describe(
    dm_habilitado="Receber notificações por mensagem direta",
    canal_habilitado="Receber notificações no canal do servidor",
    horario_silencioso_inicio="Hora de início do modo silencioso (0-23)",
    horario_silencioso_fim="Hora de fim do modo silencioso (0-23)",
    prioridade_minima="Prioridade mínima das notificações (low/medium/high/urgent)"
)
async def config_notificacoes_command(
    interaction: discord.Interaction,
    dm_habilitado: bool = None,
    canal_habilitado: bool = None,
    horario_silencioso_inicio: int = None,
    horario_silencioso_fim: int = None,
    prioridade_minima: str = None
):
    """Comando para configurar preferências de notificações"""
    try:
        updates = {}
        
        if dm_habilitado is not None:
            updates['dm_enabled'] = dm_habilitado
        
        if canal_habilitado is not None:
            updates['channel_enabled'] = canal_habilitado
        
        if horario_silencioso_inicio is not None:
            if 0 <= horario_silencioso_inicio <= 23:
                updates['quiet_hours_start'] = horario_silencioso_inicio
        
        if horario_silencioso_fim is not None:
            if 0 <= horario_silencioso_fim <= 23:
                updates['quiet_hours_end'] = horario_silencioso_fim
        
        if prioridade_minima:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if prioridade_minima.lower() in valid_priorities:
                from notifications_system import NotificationPriority
                updates['min_priority'] = NotificationPriority(prioridade_minima.lower())
        
        if not updates:
            # Mostrar configurações atuais
            prefs = bot.notifications_system.get_user_preferences(interaction.user.id)
            
            embed = discord.Embed(
                title="⚙️ Suas Configurações de Notificações",
                color=0x3498DB
            )
            
            embed.add_field(
                name="📱 Mensagens Diretas",
                value="✅ Habilitado" if prefs.dm_enabled else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="💬 Canal do Servidor",
                value="✅ Habilitado" if prefs.channel_enabled else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="🌙 Horário Silencioso",
                value=f"{prefs.quiet_hours_start:02d}:00 - {prefs.quiet_hours_end:02d}:00",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Prioridade Mínima",
                value=prefs.min_priority.value.title(),
                inline=True
            )
            
            embed.add_field(
                name="📊 Tipos Habilitados",
                value=f"{len(prefs.enabled_types)} de {len(bot.notifications_system.templates)} tipos",
                inline=True
            )
            
            embed.set_footer(text="Use os parâmetros do comando para alterar as configurações")
            
        else:
            # Aplicar atualizações
            success = await bot.notifications_system.update_user_preferences(interaction.user.id, **updates)
            
            if success:
                embed = discord.Embed(
                    title="✅ Configurações Atualizadas",
                    description="Suas preferências de notificações foram atualizadas com sucesso!",
                    color=0x27AE60
                )
                
                for key, value in updates.items():
                    embed.add_field(
                        name=key.replace('_', ' ').title(),
                        value=str(value),
                        inline=True
                    )
            else:
                embed = discord.Embed(
                    title="❌ Erro na Atualização",
                    description="Não foi possível atualizar suas preferências.",
                    color=0xE74C3C
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro na configuração de notificações: {e}")
        await interaction.response.send_message("❌ Erro ao configurar notificações.", ephemeral=True)

@bot.tree.command(name="lembrete", description="Criar um lembrete personalizado")
@app_commands.describe(
    titulo="Título do lembrete",
    mensagem="Mensagem do lembrete",
    tempo="Tempo para o lembrete (ex: 30m, 2h, 1d)",
    prioridade="Prioridade do lembrete (low/medium/high)"
)
async def lembrete_command(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str,
    tempo: str,
    prioridade: str = "medium"
):
    """Comando para criar lembretes personalizados"""
    try:
        # Parsear tempo
        import re
        time_match = re.match(r'(\d+)([mhd])', tempo.lower())
        if not time_match:
            await interaction.response.send_message(
                "❌ Formato de tempo inválido. Use: 30m (minutos), 2h (horas), 1d (dias)",
                ephemeral=True
            )
            return
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        if unit == 'm':
            delta = timedelta(minutes=amount)
        elif unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'd':
            delta = timedelta(days=amount)
        
        scheduled_for = datetime.now() + delta
        
        # Validar prioridade
        valid_priorities = ['low', 'medium', 'high']
        if prioridade.lower() not in valid_priorities:
            prioridade = 'medium'
        
        from notifications_system import NotificationPriority
        priority_obj = NotificationPriority(prioridade.lower())
        
        # Criar lembrete
        reminder = await bot.notifications_system.create_custom_reminder(
            interaction.user.id, titulo, mensagem, scheduled_for, priority_obj
        )
        
        if reminder:
            embed = discord.Embed(
                title="⏰ Lembrete Criado",
                description=f"Seu lembrete foi agendado para {scheduled_for.strftime('%d/%m/%Y às %H:%M')}.",
                color=0x27AE60
            )
            
            embed.add_field(name="📝 Título", value=titulo, inline=False)
            embed.add_field(name="💬 Mensagem", value=mensagem, inline=False)
            embed.add_field(name="⚡ Prioridade", value=prioridade.title(), inline=True)
            
        else:
            embed = discord.Embed(
                title="❌ Erro ao Criar Lembrete",
                description="Não foi possível criar o lembrete.",
                color=0xE74C3C
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro ao criar lembrete: {e}")
        await interaction.response.send_message("❌ Erro ao criar lembrete.", ephemeral=True)

@bot.tree.command(name="notificacoes_help", description="Ajuda sobre o sistema de notificações")
async def notificacoes_help_command(interaction: discord.Interaction):
    """Comando de ajuda para notificações"""
    embed = discord.Embed(
        title="🔔 Sistema de Notificações - Ajuda",
        description="Sistema completo de notificações push personalizadas do Hawk Bot.",
        color=0x3498DB
    )
    
    embed.add_field(
        name="📋 Comandos Disponíveis",
        value="• `/notificacoes` - Ver suas notificações\n"
              "• `/marcar_lidas` - Marcar todas como lidas\n"
              "• `/config_notificacoes` - Configurar preferências\n"
              "• `/lembrete` - Criar lembrete personalizado",
        inline=False
    )
    
    embed.add_field(
        name="🔔 Tipos de Notificações",
        value="• **Rank**: Promoções e mudanças de rank\n"
              "• **Conquistas**: Novas conquistas desbloqueadas\n"
              "• **Torneios**: Início e resultados de torneios\n"
              "• **Desafios**: Novos desafios diários\n"
              "• **Mini-games**: Marcos e conquistas\n"
              "• **Sistema**: Anúncios importantes\n"
              "• **Lembretes**: Lembretes personalizados",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Configurações",
        value="• **DM/Canal**: Escolha onde receber\n"
              "• **Horário Silencioso**: Defina quando não receber\n"
              "• **Prioridade**: Filtre por importância\n"
              "• **Tipos**: Ative/desative categorias",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Prioridades",
        value="• **Low**: Informações gerais\n"
              "• **Medium**: Eventos importantes\n"
              "• **High**: Conquistas e promoções\n"
              "• **Urgent**: Alertas críticos",
        inline=False
    )
    
    embed.set_footer(text="Hawk Bot - Sistema de Notificações Push")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="templates_demo", description="Demonstra os templates visuais personalizados disponíveis")
@app_commands.describe(template_type="Tipo de template para demonstrar")
@app_commands.choices(template_type=[
    app_commands.Choice(name="Sucesso", value="success"),
    app_commands.Choice(name="Erro", value="error"),
    app_commands.Choice(name="Aviso", value="warning"),
    app_commands.Choice(name="Informação", value="info"),
    app_commands.Choice(name="PUBG Rank", value="pubg_rank"),
    app_commands.Choice(name="Servidor Rank", value="server_rank"),
    app_commands.Choice(name="Torneio", value="tournament"),
    app_commands.Choice(name="Conquista", value="achievement"),
    app_commands.Choice(name="Música", value="music"),
    app_commands.Choice(name="Boas-vindas", value="welcome"),
    app_commands.Choice(name="Leaderboard", value="leaderboard")
])
async def templates_demo(interaction: discord.Interaction, template_type: str = "info"):
    """Demonstra os diferentes templates visuais disponíveis"""
    try:
        user = interaction.user
        
        # Dados de exemplo para diferentes templates
        sample_data = {
            'success': {
                'title': 'Operação Realizada com Sucesso',
                'description': 'Sua solicitação foi processada com sucesso!'
            },
            'error': {
                'title': 'Erro na Operação',
                'description': 'Ocorreu um erro durante o processamento.'
            },
            'warning': {
                'title': 'Atenção Necessária',
                'description': 'Esta ação requer sua atenção.'
            },
            'info': {
                'title': 'Informação Importante',
                'description': 'Aqui estão as informações solicitadas.'
            },
            'pubg_rank': {
                'ranked_rank': 'Diamante III',
                'ranked_points': '4250',
                'mm_rank': 'Mestre V',
                'mm_points': '3890',
                'kd': '2.45',
                'wins': '127',
                'winrate': '68'
            },
            'server_rank': {
                'position': '15',
                'points': '2450',
                'level': '12',
                'recent_activities': [
                    '🎮 Participou de torneio',
                    '💬 Ativo no chat',
                    '🏆 Conquistou badge'
                ]
            },
            'tournament': {
                'name': 'Torneio Hawk Esports',
                'description': 'Campeonato semanal de PUBG',
                'status': 'active',
                'participants': 32,
                'prize': 'R$ 500,00'
            },
            'achievement': {
                'name': 'Mestre dos Headshots',
                'description': 'Conseguiu 100 headshots em partidas ranqueadas',
                'rarity': 'epic'
            },
            'music': {
                'title': 'Imagine Dragons - Believer',
                'artist': 'Imagine Dragons',
                'duration': '3:24'
            },
            'welcome': {
                'member_count': 156
            },
            'leaderboard': [
                {'name': 'PlayerOne', 'rank': 'Predador', 'kd': '3.2', 'points': '5000', 'level': '15'},
                {'name': 'GamerPro', 'rank': 'Mestre I', 'kd': '2.8', 'points': '4500', 'level': '14'},
                {'name': 'SkillMaster', 'rank': 'Diamante V', 'kd': '2.5', 'points': '4200', 'level': '13'}
            ]
        }
        
        # Criar embed baseado no template selecionado
        if template_type in ['success', 'error', 'warning', 'info']:
            data = sample_data[template_type]
            embed = bot.embed_templates.create_embed(template_type, data['title'], data['description'])
            
        elif template_type == 'pubg_rank':
            embed = bot.embed_templates.create_pubg_rank_embed(user, sample_data['pubg_rank'])
            
        elif template_type == 'server_rank':
            embed = bot.embed_templates.create_server_rank_embed(user, sample_data['server_rank'])
            
        elif template_type == 'tournament':
            embed = bot.embed_templates.create_tournament_embed(sample_data['tournament'])
            
        elif template_type == 'achievement':
            embed = bot.embed_templates.create_achievement_embed(user, sample_data['achievement'])
            
        elif template_type == 'music':
            embed = bot.embed_templates.create_music_embed('playing', sample_data['music'])
            
        elif template_type == 'welcome':
            embed = bot.embed_templates.create_welcome_embed(user, sample_data['welcome'])
            
        elif template_type == 'leaderboard':
            embed = bot.embed_templates.create_leaderboard_embed('pubg', sample_data['leaderboard'])
        
        # Adicionar informações sobre o template
        template_info = bot.embed_templates.get_template_info(template_type)
        embed.add_field(
            name="🎨 Informações do Template",
            value=f"**Tipo:** {template_type}\n**Cor:** #{template_info.get('color', 0):06x}\n**Emoji:** {template_info.get('emoji', '❓')}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Erro na demonstração de templates: {e}")
        error_embed = bot.embed_templates.create_error_embed(
            "Erro na Demonstração",
            f"Não foi possível demonstrar o template: {str(e)}"
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

@bot.tree.command(name="test_pubg_api", description="🔧 [ADMIN] Testa conexão com API do PUBG")
async def test_pubg_api(interaction: discord.Interaction, jogador: str = None):
    """Comando para testar a API do PUBG"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        # Se não especificar jogador, usar dados do usuário
        if not jogador:
            player_data = bot.storage.get_player(str(interaction.user.id))
            if not player_data:
                await interaction.followup.send(
                    "❌ Você não está registrado! Use `/register_pubg` primeiro ou especifique um nome de jogador.",
                    ephemeral=True
                )
                return
            jogador = player_data['pubg_name']
            shard = player_data.get('shard', 'steam')
        else:
            shard = 'steam'  # Padrão
        
        embed = discord.Embed(
            title="🔧 Teste da API PUBG",
            description=f"Testando conexão para jogador: **{jogador}**",
            color=discord.Color.blue()
        )
        
        # Testar busca do jogador
        embed.add_field(
            name="1️⃣ Buscando jogador...",
            value="⏳ Processando...",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
        # Buscar stats
        stats = await bot.pubg_api.get_player_stats(jogador, shard)
        
        if stats:
            # Sucesso - mostrar informações
            success_embed = discord.Embed(
                title="✅ API PUBG Funcionando!",
                description=f"Dados obtidos com sucesso para **{jogador}**",
                color=discord.Color.green()
            )
            
            # Informações do jogador
            player_info = stats.get('player_info', {})
            success_embed.add_field(
                name="👤 Informações do Jogador",
                value=f"**Nome:** {player_info.get('name', 'N/A')}\n**Shard:** {player_info.get('shard', 'N/A')}\n**ID:** {player_info.get('id', 'N/A')[:20]}...",
                inline=False
            )
            
            # Stats de temporada
            season_stats = stats.get('season_stats', {})
            ranked_squad = season_stats.get('ranked', {}).get('squad', {})
            
            if ranked_squad:
                success_embed.add_field(
                    name="📊 Stats Ranked Squad",
                    value=f"**K/D:** {ranked_squad.get('kd', 0)}\n**Partidas:** {ranked_squad.get('matches', 0)}\n**Vitórias:** {ranked_squad.get('wins', 0)}\n**Dano Médio:** {ranked_squad.get('damage_avg', 0)}",
                    inline=True
                )
            
            # Calcular rank
            rank = bot.pubg_api.calculate_rank(season_stats, 'ranked')
            success_embed.add_field(
                name="🏆 Rank Calculado",
                value=f"**Ranked:** {rank}",
                inline=True
            )
            
            success_embed.add_field(
                name="⏰ Última Atualização",
                value=stats.get('last_updated', 'N/A'),
                inline=False
            )
            
            await interaction.edit_original_response(embed=success_embed)
            
        else:
            # Erro - mostrar diagnóstico
            error_embed = discord.Embed(
                title="❌ Erro na API PUBG",
                description=f"Não foi possível obter dados para **{jogador}**",
                color=discord.Color.red()
            )
            
            # Verificar possíveis causas
            error_embed.add_field(
                name="🔍 Possíveis Causas",
                value="• Nome do jogador incorreto\n• Jogador não existe no shard especificado\n• API PUBG indisponível\n• Chave da API inválida\n• Limite de requisições excedido",
                inline=False
            )
            
            error_embed.add_field(
                name="💡 Soluções",
                value="• Verifique se o nome está correto\n• Tente com outro shard (steam, psn, xbox)\n• Aguarde alguns minutos e tente novamente",
                inline=False
            )
            
            await interaction.edit_original_response(embed=error_embed)
            
    except Exception as e:
        logger.error(f"Erro no teste da API PUBG: {e}")
        error_embed = discord.Embed(
            title="💥 Erro Interno",
            description=f"Erro durante o teste: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=error_embed)

@bot.tree.command(name="debug_pubg_raw", description="🔍 [ADMIN] Debug completo da API PUBG - dados brutos")
async def debug_pubg_raw(interaction: discord.Interaction, jogador: str = None):
    """Comando para debug completo da API PUBG"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        # Se não especificar jogador, usar dados do usuário
        if not jogador:
            player_data = bot.storage.get_player(str(interaction.user.id))
            if not player_data:
                await interaction.followup.send(
                    "❌ Você não está registrado! Use `/register_pubg` primeiro ou especifique um nome de jogador.",
                    ephemeral=True
                )
                return
            jogador = player_data['pubg_name']
            shard = player_data.get('shard', 'steam')
        else:
            shard = 'steam'  # Padrão
        
        embed = discord.Embed(
            title="🔍 Debug Completo PUBG API",
            description=f"Analisando dados brutos para: **{jogador}**",
            color=discord.Color.orange()
        )
        
        await interaction.followup.send(embed=embed)
        
        # 1. Testar busca do jogador
        try:
            player_info = await bot.pubg_api._get_player_by_name(jogador, shard)
            if player_info:
                embed.add_field(
                    name="✅ 1. Jogador Encontrado",
                    value=f"**ID:** {player_info['id'][:20]}...\n**Nome:** {player_info['name']}\n**Shard:** {shard}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ 1. Jogador NÃO Encontrado",
                    value="Jogador não existe no shard especificado",
                    inline=False
                )
                await interaction.edit_original_response(embed=embed)
                return
        except Exception as e:
            embed.add_field(
                name="💥 1. Erro na Busca do Jogador",
                value=f"Erro: {str(e)}",
                inline=False
            )
            await interaction.edit_original_response(embed=embed)
            return
        
        # 2. Testar temporada atual
        try:
            current_season = await bot.pubg_api._get_current_season(shard)
            if current_season:
                season_id = current_season['id']
                season_name = current_season['attributes'].get('id', 'N/A')
                is_current = current_season['attributes'].get('isCurrentSeason', False)
                embed.add_field(
                    name="✅ 2. Temporada Atual",
                    value=f"**ID:** {season_id}\n**Nome:** {season_name}\n**Atual:** {is_current}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ 2. Temporada NÃO Encontrada",
                    value="Não foi possível obter temporada atual",
                    inline=False
                )
        except Exception as e:
            embed.add_field(
                name="💥 2. Erro na Temporada",
                value=f"Erro: {str(e)}",
                inline=False
            )
        
        # 3. Testar stats da temporada
        try:
            season_stats = await bot.pubg_api._get_season_stats(player_info['id'], current_season['id'], shard)
            if season_stats:
                # Verificar estrutura dos dados
                game_mode_stats = season_stats['data']['attributes']['gameModeStats']
                available_modes = list(game_mode_stats.keys())
                
                embed.add_field(
                    name="✅ 3. Stats da Temporada",
                    value=f"**Modos Disponíveis:** {', '.join(available_modes)}\n**Total de Modos:** {len(available_modes)}",
                    inline=False
                )
                
                # Verificar dados específicos do squad (ranked)
                squad_data = game_mode_stats.get('squad', {})
                if squad_data:
                    matches = squad_data.get('roundsPlayed', 0)
                    kills = squad_data.get('kills', 0)
                    wins = squad_data.get('wins', 0)
                    embed.add_field(
                        name="📊 Squad Stats (Ranked)",
                        value=f"**Partidas:** {matches}\n**Kills:** {kills}\n**Vitórias:** {wins}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="⚠️ Squad Stats",
                        value="Nenhum dado de squad encontrado",
                        inline=True
                    )
                
                # Verificar outros modos
                duo_data = game_mode_stats.get('duo', {})
                solo_data = game_mode_stats.get('solo', {})
                
                if duo_data:
                    embed.add_field(
                        name="📊 Duo Stats",
                        value=f"**Partidas:** {duo_data.get('roundsPlayed', 0)}",
                        inline=True
                    )
                
                if solo_data:
                    embed.add_field(
                        name="📊 Solo Stats",
                        value=f"**Partidas:** {solo_data.get('roundsPlayed', 0)}",
                        inline=True
                    )
                
            else:
                embed.add_field(
                    name="❌ 3. Stats NÃO Encontradas",
                    value="Nenhuma estatística encontrada para esta temporada",
                    inline=False
                )
        except Exception as e:
            embed.add_field(
                name="💥 3. Erro nas Stats",
                value=f"Erro: {str(e)}",
                inline=False
            )
        
        # 4. Testar processamento
        try:
            final_stats = await bot.pubg_api.get_player_stats(jogador, shard)
            if final_stats:
                processed_ranked = final_stats.get('season_stats', {}).get('ranked', {})
                squad_processed = processed_ranked.get('squad', {})
                
                embed.add_field(
                    name="✅ 4. Processamento Final",
                    value=f"**K/D Squad:** {squad_processed.get('kd', 0)}\n**Partidas Squad:** {squad_processed.get('matches', 0)}\n**Rank Calculado:** {bot.pubg_api.calculate_rank(final_stats.get('season_stats', {}), 'ranked')}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ 4. Processamento Falhou",
                    value="Falha no processamento final dos dados",
                    inline=False
                )
        except Exception as e:
            embed.add_field(
                name="💥 4. Erro no Processamento",
                value=f"Erro: {str(e)}",
                inline=False
            )
        
        await interaction.edit_original_response(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no debug da API PUBG: {e}")
        error_embed = discord.Embed(
            title="💥 Erro no Debug",
            description=f"Erro durante o debug: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=error_embed)

@bot.tree.command(name="admin_update_roles", description="🔄 [ADMIN] Atualiza cargo 'Acesso liberado' para todos os membros registrados")
async def admin_update_roles(interaction: discord.Interaction):
    """Comando administrativo para atualizar cargos de acesso para membros já registrados"""
    # Verificar permissões de administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        # Executar atualização
        result = await bot.registration.update_all_access_roles(interaction.guild)
        
        # Criar embed de resposta
        if result['updated'] > 0 or result['already_had'] > 0:
            embed = discord.Embed(
                title="✅ Atualização de Cargos Concluída!",
                description="Processo de atualização do cargo 'Acesso liberado' finalizado.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Nenhuma Atualização Necessária",
                description="Não foram encontrados membros registrados para atualizar.",
                color=discord.Color.blue()
            )
            
        embed.add_field(
            name="📊 Resultados",
            value=(
                f"🆕 **Atualizados:** {result['updated']}\n"
                f"✅ **Já tinham:** {result['already_had']}\n"
                f"❓ **Não encontrados:** {result['not_found']}\n"
                f"📋 **Total registrados:** {result['total_registered']}"
            ),
            inline=False
        )
        
        if result['updated'] > 0:
            embed.add_field(
                name="💡 Dica",
                value="Os membros atualizados agora têm acesso completo ao servidor!",
                inline=False
            )
    
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando admin_update_roles: {e}")
        error_embed = discord.Embed(
            title="❌ Erro na Atualização",
            description=f"Ocorreu um erro durante a atualização: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.tree.command(name="update_access_roles", description="🔄 Atualiza cargo 'Acesso liberado' para todos os membros registrados (Admin)")
async def update_access_roles(interaction: discord.Interaction):
    """Comando para atualizar cargos de acesso para membros já registrados"""
    # Verificar permissões de administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        # Executar atualização
        result = await bot.registration.update_all_access_roles(interaction.guild)
        
        if "error" in result:
            embed = discord.Embed(
                title="❌ Erro na Atualização",
                description=f"Erro: {result['error']}",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="✅ Atualização de Cargos Concluída",
                description="Cargos 'Acesso liberado' atualizados para membros registrados!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Resultados",
                value=(
                    f"🆕 **Atualizados:** {result['updated']}\n"
                    f"✅ **Já tinham:** {result['already_had']}\n"
                    f"❓ **Não encontrados:** {result['not_found']}\n"
                    f"📋 **Total registrados:** {result['total_registered']}"
                ),
                inline=False
            )
            
            if result['updated'] > 0:
                embed.add_field(
                    name="💡 Dica",
                    value="Os membros atualizados agora têm acesso completo ao servidor!",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando update_access_roles: {e}")
        await interaction.followup.send(
            f"❌ Erro ao atualizar cargos: {str(e)}", 
            ephemeral=True
        )

@bot.tree.command(name="tempo_real", description="⚡ [ADMIN] Configura atualizações em tempo real")
@discord.app_commands.describe(
    acao="Ação a realizar",
    valor="Valor da configuração (quando aplicável)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Ativar", value="enable"),
    discord.app_commands.Choice(name="Desativar", value="disable"),
    discord.app_commands.Choice(name="Status", value="status"),
    discord.app_commands.Choice(name="Intervalo Ranks (min)", value="rank_interval"),
    discord.app_commands.Choice(name="Intervalo Stats (min)", value="stats_interval")
])
async def tempo_real_config(interaction: discord.Interaction, acao: str, valor: int = None):
    """Configura sistema de atualizações em tempo real"""
    try:
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
        
        # Carregar configuração atual
        config = bot.dual_ranking_system.config
        real_time_config = config.get('real_time_updates', {})
        
        if acao == "enable":
            real_time_config['enabled'] = True
            bot.dual_ranking_system.save_config()
            
            embed = discord.Embed(
                title="⚡ Tempo Real Ativado",
                description="Sistema de atualizações em tempo real foi **ativado**!",
                color=0x00ff00
            )
            embed.add_field(
                name="📊 Configurações Atuais",
                value=f"• Ranks: A cada {real_time_config.get('rank_update_interval_minutes', 30)} minutos\n"
                      f"• Stats: A cada {real_time_config.get('stats_update_interval_minutes', 15)} minutos\n"
                      f"• Auto-sync: {'✅' if real_time_config.get('auto_sync_on_activity', True) else '❌'}",
                inline=False
            )
            
        elif acao == "disable":
            real_time_config['enabled'] = False
            bot.dual_ranking_system.save_config()
            
            embed = discord.Embed(
                title="⏸️ Tempo Real Desativado",
                description="Sistema de atualizações em tempo real foi **desativado**.",
                color=0xff9900
            )
            embed.add_field(
                name="ℹ️ Informação",
                value="As atualizações voltarão ao modo padrão (6 horas).",
                inline=False
            )
            
        elif acao == "status":
            status = "🟢 Ativo" if real_time_config.get('enabled', False) else "🔴 Inativo"
            
            embed = discord.Embed(
                title="⚡ Status do Tempo Real",
                description=f"Sistema: {status}",
                color=0x00ff00 if real_time_config.get('enabled', False) else 0xff0000
            )
            embed.add_field(
                name="⚙️ Configurações",
                value=f"• Intervalo Ranks: {real_time_config.get('rank_update_interval_minutes', 30)} min\n"
                      f"• Intervalo Stats: {real_time_config.get('stats_update_interval_minutes', 15)} min\n"
                      f"• Auto-sync: {'✅' if real_time_config.get('auto_sync_on_activity', True) else '❌'}\n"
                      f"• Max API calls/hora: {real_time_config.get('max_api_calls_per_hour', 120)}",
                inline=False
            )
            
        elif acao == "rank_interval":
            if valor is None or valor < 5 or valor > 120:
                await interaction.response.send_message("❌ Valor inválido! Use entre 5 e 120 minutos.", ephemeral=True)
                return
                
            real_time_config['rank_update_interval_minutes'] = valor
            bot.dual_ranking_system.save_config()
            
            embed = discord.Embed(
                title="⚡ Intervalo de Ranks Atualizado",
                description=f"Intervalo de atualização de ranks alterado para **{valor} minutos**.",
                color=0x00ff00
            )
            
        elif acao == "stats_interval":
            if valor is None or valor < 5 or valor > 60:
                await interaction.response.send_message("❌ Valor inválido! Use entre 5 e 60 minutos.", ephemeral=True)
                return
                
            real_time_config['stats_update_interval_minutes'] = valor
            bot.dual_ranking_system.save_config()
            
            embed = discord.Embed(
                title="⚡ Intervalo de Stats Atualizado",
                description=f"Intervalo de atualização de estatísticas alterado para **{valor} minutos**.",
                color=0x00ff00
            )
        
        embed.set_footer(text="Hawk Esports • Sistema de Tempo Real")
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando tempo_real: {e}")
        await interaction.response.send_message(f"❌ Erro ao configurar tempo real: {e}", ephemeral=True)

@bot.tree.command(name="force_rank_update", description="🔄 [ADMIN] Força atualização de rank de um jogador")
@discord.app_commands.describe(player="Usuário Discord para atualizar (opcional, atualiza você se não especificado)")
async def force_rank_update(interaction: discord.Interaction, player: discord.Member = None):
    """Força atualização de rank de um jogador específico"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        # Determinar jogador alvo
        target_user = player if player else interaction.user
        user_data = bot.storage.get_player(str(target_user.id))
        
        if not user_data:
            await interaction.followup.send(f"❌ {target_user.mention} não está registrado no sistema.")
            return
        
        embed = discord.Embed(
            title="🔄 Forçando Atualização de Rank",
            description=f"Atualizando dados de **{user_data['pubg_name']}** ({target_user.mention})",
            color=0xFF6B35,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Status",
            value="🔄 Buscando dados da API PUBG...",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
        # Forçar atualização do rank
        result = await bot.rank_system.update_player_rank(str(target_user.id), str(interaction.guild.id))
        
        if result['success']:
            # Buscar dados atualizados
            updated_data = bot.storage.get_player(str(target_user.id))
            
            embed.set_field_at(
                0,
                name="📊 Status",
                value="✅ **Atualização concluída com sucesso!**",
                inline=False
            )
            
            # Mostrar ranks atuais
            current_ranks = updated_data.get('current_ranks', {})
            ranked_rank = current_ranks.get('ranked', 'Sem rank')
            mm_rank = current_ranks.get('mm', 'Sem rank MM')
            
            embed.add_field(
                name="🏆 Ranks Atuais",
                value=f"**Ranqueado:** {ranked_rank}\n**MM:** {mm_rank}",
                inline=False
            )
            
            # Mostrar estatísticas
            season_stats = updated_data.get('season_stats', {})
            ranked_squad = season_stats.get('ranked', {}).get('squad', {})
            mm_squad = season_stats.get('mm', {}).get('squad', {})
            
            if ranked_squad.get('matches', 0) > 0:
                embed.add_field(
                    name="🎯 Squad Ranqueado",
                    value=f"K/D: `{ranked_squad.get('kd', 0)}`\nPartidas: `{ranked_squad.get('matches', 0)}`\nVitórias: `{ranked_squad.get('wins', 0)}`",
                    inline=True
                )
            
            if mm_squad.get('matches', 0) > 0:
                embed.add_field(
                    name="🎮 Squad MM",
                    value=f"K/D: `{mm_squad.get('kd', 0)}`\nPartidas: `{mm_squad.get('matches', 0)}`\nVitórias: `{mm_squad.get('wins', 0)}`",
                    inline=True
                )
            
            # Mostrar conquistas desbloqueadas
            if result.get('achievements'):
                achievements_text = "\n".join([f"🏅 {ach}" for ach in result['achievements']])
                embed.add_field(
                    name="🎉 Novas Conquistas",
                    value=achievements_text,
                    inline=False
                )
            
            embed.color = 0x00FF00  # Verde para sucesso
            
        else:
            embed.set_field_at(
                0,
                name="📊 Status",
                value=f"❌ **Erro na atualização:** {result.get('error', 'Erro desconhecido')}",
                inline=False
            )
            embed.color = 0xFF0000  # Vermelho para erro
        
        await interaction.edit_original_response(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro na Atualização Forçada",
            description=f"Erro inesperado: {str(e)}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="pubg_roles_config", description="⚙️ [ADMIN] Configura sistema de cargos automáticos PUBG")
@discord.app_commands.describe(
    acao="Ação a realizar",
    valor="Valor da configuração (quando aplicável)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Ativar Sistema", value="enable"),
    discord.app_commands.Choice(name="Desativar Sistema", value="disable"),
    discord.app_commands.Choice(name="Status", value="status"),
    discord.app_commands.Choice(name="Criar Cargos", value="create_roles"),
    discord.app_commands.Choice(name="Atualizar Todos", value="update_all"),
    discord.app_commands.Choice(name="Canal Anúncios", value="set_channel"),
    discord.app_commands.Choice(name="Setup Emojis", value="setup_emojis")
])
async def pubg_roles_config(interaction: discord.Interaction, acao: str, valor: str = None):
    """Configura o sistema de cargos automáticos baseados no rank PUBG"""
    # Verificar se é admin
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Apenas administradores podem usar este comando.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        if acao == "enable":
            bot.pubg_rank_roles.config['enabled'] = True
            bot.pubg_rank_roles.save_config()
            embed = discord.Embed(
                title="✅ Sistema Ativado",
                description="Sistema de cargos automáticos PUBG foi ativado.",
                color=0x00FF00
            )
        
        elif acao == "disable":
            bot.pubg_rank_roles.config['enabled'] = False
            bot.pubg_rank_roles.save_config()
            embed = discord.Embed(
                title="⏹️ Sistema Desativado",
                description="Sistema de cargos automáticos PUBG foi desativado.",
                color=0xFFFF00
            )
        
        elif acao == "status":
            config = bot.pubg_rank_roles.config
            status = "🟢 Ativo" if config['enabled'] else "🔴 Inativo"
            channel = f"<#{config['announcement_channel']}>" if config['announcement_channel'] else "Não configurado"
            
            embed = discord.Embed(
                title="📊 Status do Sistema de Cargos PUBG",
                color=0x0099FF
            )
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Atribuição Automática", value="✅" if config['auto_assign'] else "❌", inline=True)
            embed.add_field(name="Canal de Anúncios", value=channel, inline=False)
            embed.add_field(name="Anúncios de Promoção", value="✅" if config['announce_promotions'] else "❌", inline=True)
            embed.add_field(name="Anúncios de Rebaixamento", value="✅" if config['announce_demotions'] else "❌", inline=True)
        
        elif acao == "create_roles":
            created_roles = await bot.pubg_rank_roles.create_rank_roles(interaction.guild)
            if created_roles:
                roles_list = "\n".join([f"• {role.name} {role.mention}" for role in created_roles])
                embed = discord.Embed(
                    title="✅ Cargos Criados",
                    description=f"Foram criados {len(created_roles)} cargos:\n\n{roles_list}",
                    color=0x00FF00
                )
            else:
                embed = discord.Embed(
                    title="ℹ️ Nenhum Cargo Criado",
                    description="Todos os cargos PUBG já existem no servidor.",
                    color=0x0099FF
                )
        
        elif acao == "update_all":
            if not bot.pubg_rank_roles.config['enabled']:
                embed = discord.Embed(
                    title="❌ Sistema Desativado",
                    description="Ative o sistema primeiro com `/pubg_roles_config enable`.",
                    color=0xFF0000
                )
            else:
                updated_count = await bot.pubg_rank_roles.update_all_member_ranks(interaction.guild)
                embed = discord.Embed(
                    title="✅ Atualização Concluída",
                    description=f"Foram atualizados os cargos de {updated_count} membros baseado em seus ranks PUBG.",
                    color=0x00FF00
                )
        
        elif acao == "set_channel":
            if valor:
                try:
                    channel_id = int(valor.replace('<#', '').replace('>', ''))
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        bot.pubg_rank_roles.config['announcement_channel'] = channel_id
                        bot.pubg_rank_roles.save_config()
                        embed = discord.Embed(
                            title="✅ Canal Configurado",
                            description=f"Canal de anúncios definido como {channel.mention}",
                            color=0x00FF00
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Canal Inválido",
                            description="Canal não encontrado.",
                            color=0xFF0000
                        )
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Formato Inválido",
                        description="Use o formato: #canal ou ID do canal",
                        color=0xFF0000
                    )
            else:
                embed = discord.Embed(
                    title="❌ Canal Necessário",
                    description="Especifique o canal: `/pubg_roles_config set_channel #canal`",
                    color=0xFF0000
                )
        
        elif acao == "setup_emojis":
            results = await bot.pubg_rank_roles.setup_emojis(interaction.guild)
            if results:
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                embed = discord.Embed(
                    title="✅ Setup de Emojis Concluído",
                    description=f"Foram processados {success_count}/{total_count} emojis customizados para as patentes PUBG.",
                    color=0x00FF00
                )
                
                # Listar emojis processados
                emoji_list = []
                for emoji_name, success in results.items():
                    status = "✅" if success else "❌"
                    emoji_list.append(f"{status} {emoji_name}")
                
                if emoji_list:
                    embed.add_field(
                        name="📋 Emojis Processados",
                        value="\n".join(emoji_list[:10]),  # Limitar a 10 para não exceder limite
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="ℹ️ Nenhum Emoji Processado",
                    description="Não foram encontrados emojis para processar ou todos já existem no servidor.",
                    color=0x0099FF
                )
        
        else:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Ação não reconhecida.",
                color=0xFF0000
            )
        
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro na Configuração",
            description=f"Erro inesperado: {str(e)}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="meu_rank_pubg", description="🎮 Mostra seu rank PUBG atual e cargo correspondente")
async def meu_rank_pubg(interaction: discord.Interaction):
    """Mostra o rank PUBG do usuário e cargo correspondente"""
    await interaction.response.defer()
    
    try:
        # Verificar se usuário está registrado
        user_data = bot.storage.get_user_data(interaction.user.id)
        if not user_data or 'pubg_name' not in user_data:
            embed = discord.Embed(
                title="❌ Não Registrado",
                description="Você precisa se registrar primeiro com `/register_pubg`.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obter dados PUBG
        pubg_data = await bot.pubg_api.get_player_stats(
            user_data['pubg_name'], 
            user_data.get('shard', 'steam')
        )
        
        if not pubg_data:
            embed = discord.Embed(
                title="❌ Dados Não Encontrados",
                description="Não foi possível obter seus dados PUBG.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Calcular pontos PUBG
        pubg_points = bot.pubg_rank_roles.calculate_pubg_points(pubg_data)
        current_tier = bot.pubg_rank_roles.get_tier_by_points(pubg_points)
        
        # Verificar cargo atual
        current_role = None
        for role in interaction.user.roles:
            if role.name in [tier.role_name for tier in bot.pubg_rank_roles.PubgRankTier]:
                current_role = role
                break
        
        embed = discord.Embed(
            title=f"🎮 Rank PUBG - {interaction.user.display_name}",
            color=current_tier.color
        )
        
        embed.add_field(
            name="🏆 Patente Atual",
            value=f"{current_tier.emoji} **{current_tier.name}**",
            inline=True
        )
        
        embed.add_field(
            name="📊 Pontos PUBG",
            value=f"**{pubg_points:,}** pontos",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Cargo Discord",
            value=current_role.mention if current_role else "❌ Não atribuído",
            inline=True
        )
        
        # Próxima patente
        next_tier = None
        for tier in bot.pubg_rank_roles.PubgRankTier:
            if tier.min_points > pubg_points:
                next_tier = tier
                break
        
        if next_tier:
            points_needed = next_tier.min_points - pubg_points
            embed.add_field(
                name="⬆️ Próxima Patente",
                value=f"{next_tier.emoji} {next_tier.name}\n**{points_needed:,}** pontos necessários",
                inline=False
            )
        else:
            embed.add_field(
                name="👑 Status",
                value="**Você já alcançou a patente máxima!**",
                inline=False
            )
        
        # Estatísticas base
        if 'ranked' in pubg_data and 'squad' in pubg_data['ranked']:
            stats = pubg_data['ranked']['squad']
            embed.add_field(
                name="📈 Estatísticas (Squad Ranked)",
                value=f"**KD:** {stats.get('kd', 0):.2f}\n"
                      f"**Taxa de Vitória:** {stats.get('win_rate', 0):.1f}%\n"
                      f"**Dano Médio:** {stats.get('avg_damage', 0):.0f}",
                inline=True
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro ao Obter Rank",
            description=f"Erro inesperado: {str(e)}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)

# ==================== COMANDOS DO SISTEMA DE EMBLEMAS ====================

@bot.tree.command(name="badges_config", description="⚙️ [ADMIN] Configura sistema de emblemas/badges")
@discord.app_commands.describe(
    acao="Ação a realizar",
    valor="Valor da configuração (quando aplicável)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Ativar Sistema", value="enable"),
    discord.app_commands.Choice(name="Desativar Sistema", value="disable"),
    discord.app_commands.Choice(name="Status", value="status"),
    discord.app_commands.Choice(name="Verificar Todos", value="check_all"),
    discord.app_commands.Choice(name="Canal Anúncios", value="set_channel"),
    discord.app_commands.Choice(name="Reset Emblemas", value="reset_badges")
])
async def badges_config(interaction: discord.Interaction, acao: str, valor: str = None):
    """Configura o sistema de emblemas"""
    # Verificar se é admin
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Apenas administradores podem usar este comando.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        if acao == "enable":
            result = await bot.badge_system.enable_system(interaction.guild.id)
            if result:
                embed = discord.Embed(
                    title="✅ Sistema Ativado",
                    description="Sistema de emblemas foi ativado com sucesso!",
                    color=0x00FF00
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Sistema já Ativo",
                    description="O sistema de emblemas já estava ativado.",
                    color=0xFFFF00
                )
        
        elif acao == "disable":
            result = await bot.badge_system.disable_system(interaction.guild.id)
            embed = discord.Embed(
                title="🔴 Sistema Desativado",
                description="Sistema de emblemas foi desativado.",
                color=0xFF0000
            )
        
        elif acao == "status":
            config = await bot.badge_system.get_config(interaction.guild.id)
            status = "🟢 Ativo" if config.get('enabled', False) else "🔴 Inativo"
            
            embed = discord.Embed(
                title="📊 Status do Sistema de Emblemas",
                color=0x00BFFF
            )
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Verificação Automática", value="✅ Sim" if config.get('auto_check', True) else "❌ Não", inline=True)
            embed.add_field(name="Canal de Anúncios", value=f"<#{config.get('announcement_channel')}>" if config.get('announcement_channel') else "Não definido", inline=True)
        
        elif acao == "check_all":
            embed = discord.Embed(
                title="🔄 Verificando Emblemas",
                description="Iniciando verificação de emblemas para todos os membros...",
                color=0x00BFFF
            )
            await interaction.followup.send(embed=embed)
            
            # Verificar emblemas para todos os membros
            updated_count = await bot.badge_system.check_all_members(interaction.guild)
            
            embed = discord.Embed(
                title="✅ Verificação Concluída",
                description=f"Verificação concluída! {updated_count} membros tiveram emblemas atualizados.",
                color=0x00FF00
            )
            await interaction.followup.send(embed=embed)
            return
        
        elif acao == "set_channel":
            if not valor:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Você precisa mencionar um canal ou fornecer o ID do canal.",
                    color=0xFF0000
                )
            else:
                try:
                    channel_id = int(valor.replace('<#', '').replace('>', ''))
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        await bot.badge_system.set_announcement_channel(interaction.guild.id, channel_id)
                        embed = discord.Embed(
                            title="✅ Canal Definido",
                            description=f"Canal de anúncios definido para {channel.mention}",
                            color=0x00FF00
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Erro",
                            description="Canal não encontrado.",
                            color=0xFF0000
                        )
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="ID de canal inválido.",
                        color=0xFF0000
                    )
        
        elif acao == "reset_badges":
            # Reset de emblemas (cuidado!)
            await bot.badge_system.reset_all_badges(interaction.guild.id)
            embed = discord.Embed(
                title="🔄 Reset Realizado",
                description="Todos os emblemas foram resetados. Use 'Verificar Todos' para recalcular.",
                color=0xFFFF00
            )
        
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao configurar sistema de emblemas: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="reset_servidor", description="🔄 ADMIN: Reseta todos os dados do servidor e apaga todas as mensagens")
@discord.app_commands.describe(
    confirmacao="Digite 'CONFIRMAR' para resetar todos os dados e apagar mensagens"
)
async def reset_servidor(interaction: discord.Interaction, confirmacao: str):
    """Comando para resetar todos os dados do servidor e apagar mensagens (ADMIN ONLY)"""
    # Verificar se é administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando!", ephemeral=True)
        return
    
    if confirmacao.upper() != "CONFIRMAR":
        await interaction.response.send_message(
            "⚠️ Para resetar todos os dados e apagar mensagens, digite: `/reset_servidor confirmacao:CONFIRMAR`\n"
            "**ATENÇÃO:** Esta ação irá apagar TODOS os dados do servidor e TODAS as mensagens!", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        logger.info(f"Iniciando reset completo do servidor por {interaction.user.display_name}")
        
        # Criar backup antes do reset
        if hasattr(bot, 'storage'):
            try:
                if hasattr(bot.storage, 'create_backup'):
                    backup_file = await bot.storage.create_backup()
                    logger.info(f"Backup criado: {backup_file}")
            except Exception as backup_error:
                logger.warning(f"Erro ao criar backup: {backup_error}")
        
        # Reset dos sistemas usando PostgreSQL
        reset_count = 0
        
        # Reset do sistema de badges
        try:
            if hasattr(bot, 'badge_system'):
                bot.badge_system.user_badges = {}
                if hasattr(bot.badge_system, '_save_user_badges'):
                    bot.badge_system._save_user_badges()
                reset_count += 1
                logger.info("✅ Sistema de badges resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar badges: {e}")
        
        # Reset do sistema de conquistas
        try:
            if hasattr(bot, 'achievement_system'):
                bot.achievement_system.user_achievements = {}
                if hasattr(bot.achievement_system, '_save_user_achievements'):
                    bot.achievement_system._save_user_achievements()
                reset_count += 1
                logger.info("✅ Sistema de conquistas resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar conquistas: {e}")
        
        # Reset do sistema de ranking dual
        try:
            if hasattr(bot, 'dual_ranking_system'):
                bot.dual_ranking_system.user_data = {}
                if hasattr(bot.dual_ranking_system, '_save_user_data'):
                    bot.dual_ranking_system._save_user_data()
                reset_count += 1
                logger.info("✅ Sistema de ranking dual resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar ranking dual: {e}")
        
        # Reset do sistema de rank
        try:
            if hasattr(bot, 'rank_system'):
                bot.rank_system.user_data = {}
                if hasattr(bot.rank_system, '_save_user_data'):
                    bot.rank_system._save_user_data()
                reset_count += 1
                logger.info("✅ Sistema de rank resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar rank: {e}")
        
        # Reset do PostgreSQL (se disponível)
        try:
            if hasattr(bot, 'storage') and hasattr(bot.storage, 'db'):
                async with bot.storage.db.pool.acquire() as conn:
                    # Limpar tabelas principais (mantendo estrutura)
                    await conn.execute("DELETE FROM sessions WHERE user_id > 0")
                    await conn.execute("DELETE FROM rankings WHERE user_id > 0")
                    await conn.execute("UPDATE users SET total_sessions = 0, total_time = 0, is_checked_in = false, season_points = 0, total_matches = 0, wins = 0, kills = 0")
                    logger.info("✅ Banco PostgreSQL limpo")
                    reset_count += 1
        except Exception as e:
            logger.error(f"Erro ao limpar PostgreSQL: {e}")
        
        # Reset do sistema de clipes (JSON)
        try:
            if hasattr(bot, 'storage') and hasattr(bot.storage, 'data'):
                if 'clips' in bot.storage.data:
                    bot.storage.data['clips'] = {}
                    bot.storage._save_data()
                    reset_count += 1
                    logger.info("✅ Sistema de clipes resetado")
        except Exception as e:
            logger.error(f"Erro ao resetar clipes: {e}")
        
        # Limpar mensagens de forma mais eficiente
        deleted_messages = 0
        processed_channels = 0
        failed_channels = 0
        
        # Processar canais em lotes menores para evitar rate limiting
        channels_to_process = [ch for ch in interaction.guild.text_channels 
                             if ch.permissions_for(interaction.guild.me).manage_messages]
        
        for i, channel in enumerate(channels_to_process):
            try:
                # Atualizar progresso a cada 5 canais
                if i % 5 == 0 and i > 0:
                    progress_embed = discord.Embed(
                        title="🔄 Reset em Progresso",
                        description=f"Processando canal {i+1}/{len(channels_to_process)}\n"
                                  f"Mensagens deletadas: {deleted_messages}",
                        color=0xFFFF00
                    )
                    try:
                        await interaction.edit_original_response(embed=progress_embed)
                    except:
                        pass
                
                # Usar bulk delete quando possível (mensagens < 14 dias)
                messages_to_delete = []
                old_messages = []
                
                async for message in channel.history(limit=None):
                    # Mensagens mais antigas que 14 dias precisam ser deletadas individualmente
                    if (datetime.utcnow() - message.created_at).days >= 14:
                        old_messages.append(message)
                    else:
                        messages_to_delete.append(message)
                
                # Bulk delete para mensagens recentes
                if messages_to_delete:
                    # Dividir em lotes de 100 (limite do Discord)
                    for j in range(0, len(messages_to_delete), 100):
                        batch = messages_to_delete[j:j+100]
                        try:
                            await channel.delete_messages(batch)
                            deleted_messages += len(batch)
                            await asyncio.sleep(1)  # Pausa entre lotes
                        except discord.HTTPException:
                            # Se bulk delete falhar, deletar individualmente
                            for msg in batch:
                                try:
                                    await msg.delete()
                                    deleted_messages += 1
                                    await asyncio.sleep(0.1)
                                except:
                                    pass
                
                # Deletar mensagens antigas individualmente
                for message in old_messages:
                    try:
                        await message.delete()
                        deleted_messages += 1
                        await asyncio.sleep(0.2)  # Pausa maior para mensagens antigas
                    except:
                        pass
                        
                processed_channels += 1
                logger.info(f"Canal {channel.name} processado: {len(messages_to_delete) + len(old_messages)} mensagens")
                
            except discord.Forbidden:
                logger.warning(f"Sem permissão para acessar canal: {channel.name}")
                failed_channels += 1
            except Exception as channel_error:
                logger.error(f"Erro ao processar canal {channel.name}: {channel_error}")
                failed_channels += 1
        
        # Embed de resultado final
        embed = discord.Embed(
            title="🔄 Reset Completo do Servidor",
            description="Reset executado com sucesso!",
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 Sistemas Resetados",
            value=f"• {reset_count} sistemas limpos\n"
                  f"• Badges e Conquistas\n"
                  f"• Rankings e Estatísticas\n"
                  f"• Banco de Dados PostgreSQL\n"
                  f"• Sistema de Clipes",
            inline=False
        )
        
        embed.add_field(
            name="🗑️ Limpeza de Mensagens",
            value=f"• **{deleted_messages:,}** mensagens deletadas\n"
                  f"• **{processed_channels}** canais processados\n"
                  f"• **{failed_channels}** canais com erro",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Informações",
            value=f"• Backup criado automaticamente\n"
                  f"• Estrutura do servidor mantida\n"
                  f"• Logs detalhados salvos",
            inline=False
        )
        
        embed.set_footer(
            text=f"Reset executado por {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)
        logger.info(f"Reset completo finalizado: {deleted_messages} mensagens, {reset_count} sistemas")
        
    except Exception as e:
        logger.error(f"Erro crítico no reset do servidor: {e}")
        error_embed = discord.Embed(
            title="❌ Erro no Reset",
            description=f"Ocorreu um erro durante o reset:\n```{str(e)[:1000]}```",
            color=0xFF0000
        )
        error_embed.add_field(
            name="🔧 Solução",
            value="• Verifique os logs do bot\n• Tente novamente em alguns minutos\n• Contate o desenvolvedor se persistir",
            inline=False
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.tree.command(name="meus_badges", description="🏆 Mostra seus emblemas conquistados")
@discord.app_commands.describe(
    usuario="Usuário para ver emblemas (opcional)"
)
async def meus_badges(interaction: discord.Interaction, usuario: discord.Member = None):
    """Mostra emblemas do usuário"""
    target_user = usuario or interaction.user
    await interaction.response.defer()
    
    try:
        user_badge_data = bot.badge_system.get_user_badges(str(target_user.id))
        badges = user_badge_data.get("badges", [])
        
        if not badges:
            embed = discord.Embed(
                title="🏆 Emblemas",
                description=f"{target_user.display_name} ainda não conquistou nenhum emblema.",
                color=0x808080
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            await interaction.followup.send(embed=embed)
            return
        
        # Organizar emblemas por categoria
        categories = {}
        for badge_info in badges:
            badge_name = badge_info.get("name")
            category = badge_info.get("category")
            if category not in categories:
                categories[category] = []
            categories[category].append(badge_info)
        
        embed = discord.Embed(
            title=f"🏆 Emblemas de {target_user.display_name}",
            description=f"Total: **{len(badges)}** emblemas conquistados",
            color=0xFFD700
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Adicionar emblemas por categoria
        for category, badge_list in categories.items():
            category_names = {
                'combat': '⚔️ Combate',
                'survival': '🛡️ Sobrevivência', 
                'support': '🤝 Suporte',
                'achievement': '🏆 Conquista',
                'special': '⭐ Especial',
                'weapons': '🔫 Armas',
                'progression': '📈 Progressão',
                'seasonal': '🎯 Sazonal'
            }
            
            badge_text = ""
            for badge in badge_list[:5]:  # Máximo 5 por categoria
                rarity_emoji = {
                    'comum': '🥉',
                    'raro': '🥈', 
                    'épico': '🥇',
                    'lendário': '💎',
                    'mítico': '👑'
                }.get(badge.get('rarity'), '🏅')
                
                badge_text += f"{badge.get('emoji', '🏅')} **{badge.get('name', 'Emblema')}** {rarity_emoji}\n"
            
            if len(badge_list) > 5:
                badge_text += f"*... e mais {len(badge_list) - 5} emblemas*"
            
            embed.add_field(
                name=category_names.get(category, category.title()),
                value=badge_text or "Nenhum emblema",
                inline=True
            )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar emblemas: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="badges_disponiveis", description="📋 Lista todos os emblemas disponíveis")
@discord.app_commands.describe(
    categoria="Filtrar por categoria específica"
)
@discord.app_commands.choices(categoria=[
    discord.app_commands.Choice(name="⚔️ Combate", value="combat"),
    discord.app_commands.Choice(name="🛡️ Sobrevivência", value="survival"),
    discord.app_commands.Choice(name="🤝 Suporte", value="support"),
    discord.app_commands.Choice(name="🏆 Conquista", value="achievement"),
    discord.app_commands.Choice(name="⭐ Especial", value="special")
])
async def badges_disponiveis(interaction: discord.Interaction, categoria: str = None):
    """Lista todos os emblemas disponíveis"""
    await interaction.response.defer()
    
    try:
        all_badges = list(BadgeType)
        
        if categoria:
            all_badges = [b for b in all_badges if b.value['category'] == categoria]
        
        if not all_badges:
            embed = discord.Embed(
                title="📋 Emblemas Disponíveis",
                description="Nenhum emblema encontrado para esta categoria.",
                color=0x808080
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Organizar por raridade
        rarity_order = ['mythic', 'legendary', 'epic', 'rare', 'common']
        all_badges.sort(key=lambda x: rarity_order.index(x.value['rarity']))
        
        embed = discord.Embed(
            title="📋 Emblemas Disponíveis",
            description=f"Total: **{len(all_badges)}** emblemas",
            color=0x00BFFF
        )
        
        current_field = ""
        field_count = 0
        
        for badge in all_badges:
            rarity_emoji = {
                'common': '🥉',
                'rare': '🥈',
                'epic': '🥇', 
                'legendary': '💎',
                'mythic': '👑'
            }.get(badge.value['rarity'], '🏅')
            
            badge_line = f"{badge.value['emoji']} **{badge.value['name']}** {rarity_emoji}\n*{badge.value['description']}*\n\n"
            
            if len(current_field + badge_line) > 1024 or field_count >= 25:
                if current_field:
                    embed.add_field(
                        name=f"Emblemas ({field_count + 1})",
                        value=current_field,
                        inline=False
                    )
                current_field = badge_line
                field_count = 0
            else:
                current_field += badge_line
                field_count += 1
        
        if current_field:
            embed.add_field(
                name=f"Emblemas ({field_count + 1})",
                value=current_field,
                inline=False
            )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao listar emblemas: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ranking_badges", description="🏅 Mostra ranking de emblemas do servidor")
@discord.app_commands.describe(
    limite="Número de usuários no ranking (máximo 20)"
)
async def ranking_badges(interaction: discord.Interaction, limite: int = 10):
    """Mostra ranking de emblemas"""
    await interaction.response.defer()
    
    try:
        if limite > 20:
            limite = 20
        elif limite < 1:
            limite = 10
        
        ranking = await bot.badge_system.get_badges_ranking(interaction.guild.id, limite)
        
        if not ranking:
            embed = discord.Embed(
                title="🏅 Ranking de Emblemas",
                description="Nenhum membro possui emblemas ainda.",
                color=0x808080
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏅 Ranking de Emblemas",
            description=f"Top {len(ranking)} membros com mais emblemas",
            color=0xFFD700
        )
        
        ranking_text = ""
        for i, (user_id, badge_count) in enumerate(ranking, 1):
            try:
                user = interaction.guild.get_member(user_id)
                if user:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                    ranking_text += f"{medal} **{i}º** {user.display_name} - **{badge_count}** emblemas\n"
            except:
                continue
        
        embed.add_field(
            name="🏆 Ranking",
            value=ranking_text or "Nenhum dado disponível",
            inline=False
        )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao gerar ranking: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

# ==================== COMANDOS DO SISTEMA DE TEMPORADAS ====================

@bot.tree.command(name="temporadas_config", description="⚙️ [ADMIN] Configura sistema de temporadas")
@discord.app_commands.describe(
    acao="Ação a realizar",
    valor="Valor da configuração (quando aplicável)"
)
@discord.app_commands.choices(acao=[
    discord.app_commands.Choice(name="Ativar Sistema", value="enable"),
    discord.app_commands.Choice(name="Desativar Sistema", value="disable"),
    discord.app_commands.Choice(name="Status", value="status"),
    discord.app_commands.Choice(name="Criar Temporada", value="create_season"),
    discord.app_commands.Choice(name="Iniciar Temporada", value="start_season"),
    discord.app_commands.Choice(name="Finalizar Temporada", value="end_season"),
    discord.app_commands.Choice(name="Canal Anúncios", value="set_channel")
])
async def temporadas_config(interaction: discord.Interaction, acao: str, valor: str = None):
    """Configura o sistema de temporadas"""
    # Verificar permissões de administrador
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Acesso Negado",
            description="Apenas administradores podem usar este comando.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        if acao == "enable":
            bot.season_system.config["enabled"] = True
            bot.season_system._save_config()
            
            embed = discord.Embed(
                title="✅ Sistema Ativado",
                description="Sistema de temporadas foi ativado com sucesso!",
                color=0x00FF00
            )
            
        elif acao == "disable":
            bot.season_system.config["enabled"] = False
            bot.season_system._save_config()
            
            embed = discord.Embed(
                title="⏹️ Sistema Desativado",
                description="Sistema de temporadas foi desativado.",
                color=0xFFA500
            )
            
        elif acao == "status":
            current_season = bot.season_system.get_current_season()
            total_seasons = len(bot.season_system.get_all_seasons())
            
            embed = discord.Embed(
                title="📊 Status do Sistema de Temporadas",
                color=0x00BFFF
            )
            
            embed.add_field(
                name="🔧 Sistema",
                value="✅ Ativado" if bot.season_system.config["enabled"] else "❌ Desativado",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total de Temporadas",
                value=f"{total_seasons} temporadas",
                inline=True
            )
            
            if current_season:
                embed.add_field(
                    name="🏆 Temporada Atual",
                    value=f"{current_season.name}",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Tempo Restante",
                    value=f"{current_season.get_remaining_days()} dias",
                    inline=True
                )
                
                embed.add_field(
                    name="🎨 Tema",
                    value=current_season.theme.title(),
                    inline=True
                )
                
                embed.add_field(
                    name="🎁 Recompensas",
                    value=f"{len(current_season.rewards)} disponíveis",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🏆 Temporada Atual",
                    value="Nenhuma temporada ativa",
                    inline=False
                )
            
            channel_id = bot.season_system.config.get("announcement_channel_id")
            if channel_id:
                channel = bot.get_channel(channel_id)
                embed.add_field(
                    name="📢 Canal de Anúncios",
                    value=channel.mention if channel else "Canal não encontrado",
                    inline=False
                )
            
        elif acao == "create_season":
            if not valor:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Especifique o nome da temporada no campo 'valor'.",
                    color=0xFF0000
                )
            else:
                season = bot.season_system.create_season(
                    name=valor,
                    description=f"Nova temporada: {valor}"
                )
                
                embed = discord.Embed(
                    title="✅ Temporada Criada",
                    description=f"Temporada '{season.name}' criada com sucesso!",
                    color=0x00FF00
                )
                
                embed.add_field(
                    name="🆔 ID",
                    value=season.season_id,
                    inline=True
                )
                
                embed.add_field(
                    name="📅 Duração",
                    value=f"{season.get_duration_days()} dias",
                    inline=True
                )
                
                embed.add_field(
                    name="🎨 Tema",
                    value=season.theme.title(),
                    inline=True
                )
        
        elif acao == "start_season":
            current_season = bot.season_system.get_current_season()
            if current_season:
                embed = discord.Embed(
                    title="❌ Erro",
                    description=f"Já existe uma temporada ativa: {current_season.name}",
                    color=0xFF0000
                )
            else:
                # Pegar a temporada mais recente que não está ativa
                all_seasons = bot.season_system.get_all_seasons()
                upcoming_seasons = [s for s in all_seasons if s.status.value == "upcoming"]
                
                if not upcoming_seasons:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="Não há temporadas pendentes para iniciar.",
                        color=0xFF0000
                    )
                else:
                    season_to_start = upcoming_seasons[0]
                    success = await bot.season_system.start_season(season_to_start)
                    
                    if success:
                        embed = discord.Embed(
                            title="🚀 Temporada Iniciada",
                            description=f"Temporada '{season_to_start.name}' iniciada com sucesso!",
                            color=0x00FF00
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Erro",
                            description="Falha ao iniciar temporada.",
                            color=0xFF0000
                        )
        
        elif acao == "end_season":
            current_season = bot.season_system.get_current_season()
            if not current_season:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Não há temporada ativa para finalizar.",
                    color=0xFF0000
                )
            else:
                success = await bot.season_system.end_season(current_season)
                
                if success:
                    embed = discord.Embed(
                        title="🏁 Temporada Finalizada",
                        description=f"Temporada '{current_season.name}' finalizada e recompensas distribuídas!",
                        color=0x00FF00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="Falha ao finalizar temporada.",
                        color=0xFF0000
                    )
        
        elif acao == "set_channel":
            if not valor:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Especifique o ID do canal no campo 'valor'.",
                    color=0xFF0000
                )
            else:
                try:
                    channel_id = int(valor)
                    channel = bot.get_channel(channel_id)
                    
                    if not channel:
                        embed = discord.Embed(
                            title="❌ Erro",
                            description="Canal não encontrado.",
                            color=0xFF0000
                        )
                    else:
                        bot.season_system.config["announcement_channel_id"] = channel_id
                        bot.season_system._save_config()
                        
                        embed = discord.Embed(
                            title="✅ Canal Configurado",
                            description=f"Canal de anúncios definido para {channel.mention}",
                            color=0x00FF00
                        )
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="ID do canal inválido.",
                        color=0xFF0000
                    )
        
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Ação não reconhecida.",
                color=0xFF0000
            )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao configurar temporadas: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="temporada_atual", description="🏆 Mostra informações da temporada atual")
async def temporada_atual(interaction: discord.Interaction):
    """Mostra informações da temporada atual"""
    await interaction.response.defer()
    
    try:
        current_season = bot.season_system.get_current_season()
        
        if not current_season:
            embed = discord.Embed(
                title="📅 Nenhuma Temporada Ativa",
                description="Não há temporada ativa no momento.",
                color=0xFFA500
            )
        else:
            theme_data = bot.season_system.config["themes"].get(
                current_season.theme, 
                bot.season_system.config["themes"]["default"]
            )
            
            embed = discord.Embed(
                title=f"{theme_data['emoji']} {current_season.name}",
                description=current_season.description,
                color=theme_data["color"]
            )
            
            embed.add_field(
                name="📅 Duração Total",
                value=f"{current_season.get_duration_days()} dias",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Tempo Restante",
                value=f"{current_season.get_remaining_days()} dias",
                inline=True
            )
            
            embed.add_field(
                name="🎨 Tema",
                value=theme_data.get("name", current_season.theme.title()),
                inline=True
            )
            
            embed.add_field(
                name="🏁 Termina em",
                value=f"<t:{int(current_season.end_date.timestamp())}:F>",
                inline=False
            )
            
            # Mostrar algumas recompensas principais
            if current_season.rewards:
                rewards_text = "\n".join([
                    f"{reward.emoji} **{reward.name}** - {reward.description}"
                    for reward in current_season.rewards[:3]
                ])
                
                if len(current_season.rewards) > 3:
                    rewards_text += f"\n... e mais {len(current_season.rewards) - 3} recompensas!"
                
                embed.add_field(
                    name="🎁 Principais Recompensas",
                    value=rewards_text,
                    inline=False
                )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar temporada atual: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="historico_temporadas", description="📚 Mostra histórico de temporadas")
@discord.app_commands.describe(
    limite="Número de temporadas para mostrar (máximo 10)"
)
async def historico_temporadas(interaction: discord.Interaction, limite: int = 5):
    """Mostra histórico de temporadas"""
    await interaction.response.defer()
    
    try:
        limite = max(1, min(limite, 10))
        all_seasons = bot.season_system.get_all_seasons()
        
        if not all_seasons:
            embed = discord.Embed(
                title="📚 Histórico de Temporadas",
                description="Nenhuma temporada encontrada.",
                color=0xFFA500
            )
        else:
            # Ordenar por data de início (mais recente primeiro)
            sorted_seasons = sorted(all_seasons, key=lambda s: s.start_date, reverse=True)
            seasons_to_show = sorted_seasons[:limite]
            
            embed = discord.Embed(
                title="📚 Histórico de Temporadas",
                description=f"Mostrando {len(seasons_to_show)} de {len(all_seasons)} temporadas",
                color=0x00BFFF
            )
            
            for season in seasons_to_show:
                theme_data = bot.season_system.config["themes"].get(
                    season.theme, 
                    bot.season_system.config["themes"]["default"]
                )
                
                status_emoji = {
                    "active": "🟢",
                    "ended": "🔴",
                    "upcoming": "🟡",
                    "preparing": "⚪"
                }.get(season.status.value, "❓")
                
                season_info = (
                    f"{status_emoji} **{season.status.value.title()}**\n"
                    f"📅 {season.start_date.strftime('%d/%m/%Y')} - {season.end_date.strftime('%d/%m/%Y')}\n"
                    f"🎨 Tema: {theme_data.get('name', season.theme.title())}\n"
                    f"🎁 {len(season.rewards)} recompensas"
                )
                
                embed.add_field(
                    name=f"{theme_data['emoji']} {season.name}",
                    value=season_info,
                    inline=True
                )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar histórico: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ranking_temporada", description="🏆 Mostra ranking da temporada atual")
@discord.app_commands.describe(
    limite="Número de jogadores no ranking (máximo 20)"
)
async def ranking_temporada(interaction: discord.Interaction, limite: int = 10):
    """Mostra ranking da temporada atual"""
    await interaction.response.defer()
    
    try:
        limite = max(1, min(limite, 20))
        current_season = bot.season_system.get_current_season()
        
        if not current_season:
            embed = discord.Embed(
                title="❌ Nenhuma Temporada Ativa",
                description="Não há temporada ativa para mostrar ranking.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Obter rankings atuais
        rankings = await bot.dual_ranking_system.get_all_rankings()
        
        if not rankings:
            embed = discord.Embed(
                title="📊 Ranking da Temporada",
                description="Nenhum jogador ranqueado ainda.",
                color=0xFFA500
            )
        else:
            # Ordenar por pontuação total
            sorted_players = sorted(
                rankings.items(), 
                key=lambda x: x[1].get('total_score', 0), 
                reverse=True
            )[:limite]
            
            theme_data = bot.season_system.config["themes"].get(
                current_season.theme, 
                bot.season_system.config["themes"]["default"]
            )
            
            embed = discord.Embed(
                title=f"{theme_data['emoji']} Ranking - {current_season.name}",
                description=f"Top {len(sorted_players)} jogadores da temporada atual",
                color=theme_data["color"]
            )
            
            ranking_text = ""
            for i, (user_id, data) in enumerate(sorted_players, 1):
                try:
                    user = bot.get_user(int(user_id))
                    username = user.display_name if user else f"Usuário {user_id}"
                    
                    # Emojis para posições
                    position_emoji = {
                        1: "🥇",
                        2: "🥈", 
                        3: "🥉"
                    }.get(i, f"{i}º")
                    
                    total_score = data.get('total_score', 0)
                    games_played = data.get('games_played', 0)
                    
                    ranking_text += f"{position_emoji} **{username}**\n"
                    ranking_text += f"📊 {total_score:,} pontos | 🎮 {games_played} jogos\n\n"
                    
                except Exception:
                    continue
            
            if ranking_text:
                embed.description += f"\n\n{ranking_text}"
            
            embed.add_field(
                name="⏰ Tempo Restante",
                value=f"{current_season.get_remaining_days()} dias",
                inline=True
            )
            
            embed.add_field(
                name="🎁 Recompensas",
                value=f"{len(current_season.rewards)} disponíveis",
                inline=True
            )
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao gerar ranking: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ranking", description="🏆 Mostra rankings temporais específicos")
@discord.app_commands.describe(
    periodo="Período do ranking temporal",
    modo="Modo de jogo para o ranking",
    limite="Número de jogadores no ranking (máximo 20)"
)
@discord.app_commands.choices(
    periodo=[
        discord.app_commands.Choice(name="Diário", value="daily"),
        discord.app_commands.Choice(name="Semanal", value="weekly"),
        discord.app_commands.Choice(name="Mensal", value="monthly")
    ],
    modo=[
        discord.app_commands.Choice(name="Squad", value="squad"),
        discord.app_commands.Choice(name="Duo", value="duo"),
        discord.app_commands.Choice(name="Solo", value="solo")
    ]
)
async def ranking_temporal(interaction: discord.Interaction, periodo: str = "daily", modo: str = "squad", limite: int = 10):
    """Mostra rankings temporais específicos (diário, semanal, mensal)"""
    await interaction.response.defer()
    
    try:
        limite = max(1, min(limite, 20))
        
        # Usar o novo sistema de rankings temporais
        embed = await bot.dual_ranking_system.generate_temporal_leaderboard(
            mode=modo,
            period=periodo,
            limit=limite,
            min_matches=1
        )
        
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"❌ Sem Dados - Ranking {periodo.title()}",
                description=f"Nenhum jogador possui estatísticas para o período {periodo}.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Erro no comando ranking temporal: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description="Ocorreu um erro ao gerar o ranking temporal.",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="minhas_recompensas", description="🎁 Mostra suas recompensas de temporadas")
async def minhas_recompensas(interaction: discord.Interaction):
    """Mostra recompensas de temporadas do usuário"""
    await interaction.response.defer()
    
    try:
        user_id = str(interaction.user.id)
        user_data = bot.storage.get_user_data(user_id)
        
        embed = discord.Embed(
            title="🎁 Minhas Recompensas de Temporadas",
            description=f"Recompensas conquistadas por {interaction.user.display_name}",
            color=0xFFD700
        )
        
        # Títulos de temporadas
        season_titles = user_data.get("season_titles", [])
        if season_titles:
            titles_text = "\n".join([
                f"🏷️ **{title['title']}** - <t:{int(datetime.fromisoformat(title['earned_date']).timestamp())}:d>"
                for title in season_titles[-5:]  # Últimos 5 títulos
            ])
            
            embed.add_field(
                name="🏷️ Títulos Conquistados",
                value=titles_text,
                inline=False
            )
        
        # Moedas acumuladas
        coins = user_data.get("coins", 0)
        embed.add_field(
            name="🪙 Moedas Totais",
            value=f"{coins:,} moedas",
            inline=True
        )
        
        # Histórico de participação em temporadas
        season_history = bot.season_system.get_user_season_history(user_id)
        if season_history:
            embed.add_field(
                name="📊 Temporadas Participadas",
                value=f"{len(season_history)} temporadas",
                inline=True
            )
        
        # Se não tem recompensas
        if not season_titles and coins == 0 and not season_history:
            embed.description = "Você ainda não conquistou recompensas de temporadas.\nParticipe das competições para ganhar prêmios!"
        
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar recompensas: {str(e)}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="filter", description="Aplicar filtros de áudio à música")
async def filter_command(interaction: discord.Interaction, 
                        filter_type: Literal["none", "bass", "treble", "nightcore", "vaporwave", "8d", "karaoke"]):
    """Comando para aplicar filtros de áudio"""
    music_system = bot.get_cog('MusicSystem')
    if not music_system:
        await interaction.response.send_message("❌ Sistema de música não disponível!", ephemeral=True)
        return
    
    player = music_system.get_player(interaction.guild.id)
    if not player.voice_client or not player.current_song:
        await interaction.response.send_message("❌ Não há música tocando no momento!", ephemeral=True)
        return
    
    # Aplicar filtro
    success = await music_system.apply_audio_filter(interaction.guild.id, filter_type)
    
    if success:
        filter_names = {
            "none": "Nenhum",
            "bass": "🔊 Bass Boost",
            "treble": "🎵 Treble Boost",
            "nightcore": "⚡ Nightcore",
            "vaporwave": "🌊 Vaporwave",
            "8d": "🎧 8D Audio",
            "karaoke": "🎤 Karaoke"
        }
        
        embed = discord.Embed(
            title="🎛️ Filtro Aplicado",
            description=f"Filtro **{filter_names[filter_type]}** aplicado com sucesso!",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Erro ao aplicar filtro de áudio!", ephemeral=True)

@bot.tree.command(name="voteskip", description="Votar para pular a música atual")
async def voteskip_command(interaction: discord.Interaction):
    """Comando para votar para pular a música atual"""
    music_system = bot.get_cog('MusicSystem')
    if not music_system:
        await interaction.response.send_message("❌ Sistema de música não disponível!", ephemeral=True)
        return
    
    player = music_system.get_player(interaction.guild.id)
    if not player.voice_client or not player.current_song:
        await interaction.response.send_message("❌ Não há música tocando no momento!", ephemeral=True)
        return
    
    # Verificar se o usuário está no canal de voz
    if not interaction.user.voice or interaction.user.voice.channel != player.voice_client.channel:
        await interaction.response.send_message("❌ Você precisa estar no mesmo canal de voz!", ephemeral=True)
        return
    
    # Adicionar voto
    result = music_system.add_skip_vote(interaction.guild.id, interaction.user.id)
    
    if result["already_voted"]:
        await interaction.response.send_message("❌ Você já votou para pular esta música!", ephemeral=True)
        return
    
    # Verificar se deve pular
    if result["should_skip"]:
        embed = discord.Embed(
            title="⏭️ Música Pulada por Votação",
            description=f"**{player.current_song.title}** foi pulada por votação!",
            color=0xff9500
        )
        embed.add_field(
            name="📊 Votos",
            value=f"{result['votes']}/{result['required']} votos necessários",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Pular música
        if player.voice_client.is_playing():
            player.voice_client.stop()
    else:
        embed = discord.Embed(
            title="🗳️ Voto Registrado",
            description=f"Seu voto para pular **{player.current_song.title}** foi registrado!",
            color=0x00ff00
        )
        embed.add_field(
            name="📊 Progresso",
            value=f"{result['votes']}/{result['required']} votos necessários",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    # Verificar token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN não encontrado no arquivo .env!")
        exit(1)
    
    try:
        # Executar bot
        bot.run(token)
    except Exception as e:
        logger.error(f"Erro fatal ao executar bot: {e}")
        exit(1)