# -*- coding: utf-8 -*-
"""
Comandos PUBG - Hawk Bot
Cog responsável por todos os comandos relacionados ao PUBG
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger('HawkBot.PUBGCommands')

class PUBGCommands(commands.Cog):
    """Comandos relacionados ao PUBG e ranking"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("PUBGCommands Cog carregado")
    
    @app_commands.command(name="register_pubg", description="📋 Registra seu nick PUBG no clã Hawk Esports")
    @app_commands.describe(
        nome="Seu nick exato no PUBG",
        shard="Plataforma: steam, psn, xbox, kakao"
    )
    @app_commands.choices(shard=[
        app_commands.Choice(name="Steam (PC)", value="steam"),
        app_commands.Choice(name="PlayStation", value="psn"),
        app_commands.Choice(name="Xbox", value="xbox"),
        app_commands.Choice(name="Kakao", value="kakao")
    ])
    async def register_pubg(self, interaction: discord.Interaction, nome: str, shard: str):
        """Registra o nick PUBG do usuário"""
        await interaction.response.defer()
        
        try:
            success, message = await self.bot.registration.register_pubg_player(
                interaction.user, nome, shard
            )
            
            if success:
                await interaction.followup.send(message)
            else:
                await interaction.followup.send(message, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Erro no registro PUBG: {e}")
            await interaction.followup.send(
                "❌ Erro interno no registro. Tente novamente em alguns minutos.", 
                ephemeral=True
            )
    
    @app_commands.command(name="meu_status", description="📊 Verifica seu status de registro e cargo atual")
    async def meu_status(self, interaction: discord.Interaction):
        """Mostra o status de registro do usuário"""
        await interaction.response.defer()
        
        try:
            embed = await self.bot.registration.get_user_status(interaction.user)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            await interaction.followup.send(
                "❌ Erro ao obter seu status. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="leaderboard", description="🏆 Mostra o ranking do clã Hawk Esports")
    @app_commands.describe(
        modo="Modo de jogo para o ranking",
        periodo="Período do ranking"
    )
    @app_commands.choices(
        modo=[
            app_commands.Choice(name="Squad", value="squad"),
            app_commands.Choice(name="Duo", value="duo"),
            app_commands.Choice(name="Solo", value="solo")
        ],
        periodo=[
            app_commands.Choice(name="Diário", value="daily"),
            app_commands.Choice(name="Semanal", value="weekly"),
            app_commands.Choice(name="Mensal", value="monthly"),
            app_commands.Choice(name="Temporada", value="season")
        ]
    )
    async def leaderboard(self, interaction: discord.Interaction, modo: str = "squad", periodo: str = "weekly"):
        """Mostra o leaderboard do clã"""
        await interaction.response.defer()
        
        try:
            embed = await self.bot.rank_system.generate_leaderboard(
                interaction.guild, modo, periodo
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no leaderboard: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerar ranking. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="meu_rank_duplo", description="📊 Mostra seus ranks PUBG e interno do servidor")
    async def meu_rank_duplo(self, interaction: discord.Interaction):
        """Mostra ambos os ranks do usuário"""
        await interaction.response.defer()
        
        try:
            embed = await self.bot.dual_ranking_system.get_user_profile_embed(interaction.user)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando meu_rank_duplo: {e}")
            await interaction.followup.send(
                "❌ Erro ao obter seu perfil. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="atividade_servidor", description="📈 Mostra suas estatísticas de atividade no servidor")
    async def atividade_servidor(self, interaction: discord.Interaction):
        """Mostra estatísticas de atividade do usuário"""
        await interaction.response.defer()
        
        try:
            stats = await self.bot.dual_ranking_system.get_activity_stats(interaction.user.id)
            
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
            await interaction.followup.send(
                "❌ Erro ao obter estatísticas. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="meu_rank_pubg", description="🎮 Mostra seu rank PUBG atual e cargo correspondente")
    async def meu_rank_pubg(self, interaction: discord.Interaction):
        """Mostra o rank PUBG do usuário"""
        await interaction.response.defer()
        
        try:
            embed = await self.bot.pubg_rank_roles.get_user_rank_embed(interaction.user)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando meu_rank_pubg: {e}")
            await interaction.followup.send(
                "❌ Erro ao obter seu rank PUBG. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="ranking_servidor", description="🏠 Mostra o ranking interno do servidor")
    @app_commands.describe(
        periodo="Período do ranking",
        limite="Número de jogadores no ranking (máximo 20)"
    )
    @app_commands.choices(
        periodo=[
            app_commands.Choice(name="Diário", value="daily"),
            app_commands.Choice(name="Semanal", value="weekly"),
            app_commands.Choice(name="Mensal", value="monthly"),
            app_commands.Choice(name="Geral", value="all_time")
        ]
    )
    async def ranking_servidor(self, interaction: discord.Interaction, periodo: str = "weekly", limite: int = 10):
        """Mostra o ranking interno do servidor"""
        await interaction.response.defer()
        
        try:
            # Limitar o número de jogadores
            limite = min(limite, 20)
            
            # Se for um período temporal, usar o novo método
            if periodo in ["daily", "weekly", "monthly"]:
                embed = await self.bot.rank_system.generate_temporal_leaderboard(
                    interaction.guild, 
                    "squad",  # Modo padrão para ranking do servidor
                    periodo,
                    limit=limite,
                    server_ranking=True
                )
            else:
                embed = await self.bot.dual_ranking_system.generate_leaderboard(
                    interaction.guild, 
                    "server_internal", 
                    None, 
                    limite
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando ranking_servidor: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerar ranking do servidor. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="ranking", description="🏆 Mostra rankings temporais específicos")
    @app_commands.describe(
        periodo="Período do ranking temporal",
        modo="Modo de jogo para o ranking",
        limite="Número de jogadores no ranking (máximo 20)"
    )
    @app_commands.choices(
        periodo=[
            app_commands.Choice(name="Diário", value="daily"),
            app_commands.Choice(name="Semanal", value="weekly"),
            app_commands.Choice(name="Mensal", value="monthly")
        ],
        modo=[
            app_commands.Choice(name="Squad", value="squad"),
            app_commands.Choice(name="Duo", value="duo"),
            app_commands.Choice(name="Solo", value="solo")
        ]
    )
    async def ranking_temporal(self, interaction: discord.Interaction, periodo: str = "daily", modo: str = "squad", limite: int = 10):
        """Mostra rankings temporais específicos"""
        await interaction.response.defer()
        
        try:
            limite = min(limite, 20)
            
            embed = await self.bot.rank_system.generate_temporal_leaderboard(
                interaction.guild,
                modo,
                periodo,
                limit=limite
            )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando ranking_temporal: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerar ranking temporal. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="clipes", description="🎬 Lista os últimos clipes de um jogador")
    @app_commands.describe(
        jogador="Mencione o jogador ou deixe vazio para seus clipes"
    )
    async def clipes(self, interaction: discord.Interaction, jogador: Optional[discord.Member] = None):
        """Lista os clipes de um jogador"""
        target_user = jogador or interaction.user
        
        try:
            clips = await self.bot.medal_integration.get_user_clips(target_user.id)
            
            if not clips:
                await interaction.response.send_message(
                    f"🎬 {target_user.display_name} ainda não possui clipes registrados!", 
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"🎬 Clipes de {target_user.display_name}",
                description=f"Últimos {len(clips)} clipes",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            
            for i, clip in enumerate(clips[:5], 1):
                embed.add_field(
                    name=f"{i}. {clip.get('title', 'Clip sem título')}",
                    value=f"📅 {clip.get('date', 'Data não disponível')}\n🔗 [Assistir]({clip.get('url', '#')})",
                    inline=False
                )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text="Hawk Bot - Sistema de Clipes")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando clipes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter clipes. Tente novamente.", 
                ephemeral=True
            )

async def setup(bot):
    """Função para carregar o Cog"""
    await bot.add_cog(PUBGCommands(bot))
    logger.info("PUBGCommands Cog adicionado ao bot")