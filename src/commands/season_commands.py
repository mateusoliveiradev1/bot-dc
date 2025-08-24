# -*- coding: utf-8 -*-
"""
Comandos de Temporadas e Emblemas - Hawk Bot
Cog responsável por comandos relacionados a temporadas, emblemas e conquistas
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger('HawkBot.SeasonCommands')

class SeasonCommands(commands.Cog):
    """Comandos relacionados a temporadas, emblemas e conquistas"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("SeasonCommands Cog carregado")
    
    @app_commands.command(name="badges_disponiveis", description="🏅 Mostra todos os emblemas disponíveis")
    async def badges_disponiveis(self, interaction: discord.Interaction):
        """Mostra todos os emblemas disponíveis"""
        try:
            embed = await self.bot.achievement_system.get_available_badges_embed()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando badges_disponiveis: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter emblemas disponíveis.", 
                ephemeral=True
            )
    
    @app_commands.command(name="ranking_badges", description="🏆 Mostra o ranking de emblemas dos membros")
    @app_commands.describe(limite="Número de membros no ranking (máximo 20)")
    async def ranking_badges(self, interaction: discord.Interaction, limite: int = 10):
        """Mostra o ranking de emblemas"""
        await interaction.response.defer()
        
        try:
            limite = min(limite, 20)
            embed = await self.bot.achievement_system.get_badges_leaderboard(
                interaction.guild, 
                limite
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando ranking_badges: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerar ranking de emblemas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="meus_badges", description="🎖️ Mostra seus emblemas conquistados")
    async def meus_badges(self, interaction: discord.Interaction):
        """Mostra os emblemas do usuário"""
        try:
            embed = await self.bot.achievement_system.get_user_badges_embed(interaction.user)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando meus_badges: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter seus emblemas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="temporadas_config", description="⚙️ Configurações das temporadas (Admin)")
    @app_commands.describe(
        acao="Ação a ser realizada",
        nome="Nome da temporada",
        duracao="Duração em dias"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Criar Nova", value="create"),
        app_commands.Choice(name="Iniciar", value="start"),
        app_commands.Choice(name="Finalizar", value="end"),
        app_commands.Choice(name="Listar", value="list")
    ])
    async def temporadas_config(self, interaction: discord.Interaction, acao: str, nome: Optional[str] = None, duracao: Optional[int] = None):
        """Configurações das temporadas (apenas admins)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            if acao == "create":
                if not nome or not duracao:
                    await interaction.followup.send(
                        "❌ Você precisa especificar nome e duração da temporada!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.season_system.create_season(nome, duracao)
                await interaction.followup.send(result)
            
            elif acao == "start":
                if not nome:
                    await interaction.followup.send(
                        "❌ Você precisa especificar o nome da temporada!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.season_system.start_season(nome)
                await interaction.followup.send(result)
            
            elif acao == "end":
                result = await self.bot.season_system.end_current_season()
                await interaction.followup.send(result)
            
            elif acao == "list":
                embed = await self.bot.season_system.get_seasons_list_embed()
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erro no comando temporadas_config: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerenciar temporadas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="temporada_atual", description="📅 Mostra informações da temporada atual")
    async def temporada_atual(self, interaction: discord.Interaction):
        """Mostra informações da temporada atual"""
        try:
            embed = await self.bot.season_system.get_current_season_embed()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando temporada_atual: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter temporada atual.", 
                ephemeral=True
            )
    
    @app_commands.command(name="historico_temporadas", description="📜 Mostra o histórico de temporadas")
    async def historico_temporadas(self, interaction: discord.Interaction):
        """Mostra o histórico de temporadas"""
        try:
            embed = await self.bot.season_system.get_seasons_history_embed()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando historico_temporadas: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter histórico de temporadas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="ranking_temporada", description="🏆 Mostra o ranking da temporada atual")
    @app_commands.describe(
        modo="Modo de jogo para o ranking",
        limite="Número de jogadores no ranking (máximo 20)"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Squad", value="squad"),
        app_commands.Choice(name="Duo", value="duo"),
        app_commands.Choice(name="Solo", value="solo"),
        app_commands.Choice(name="Geral", value="overall")
    ])
    async def ranking_temporada(self, interaction: discord.Interaction, modo: str = "squad", limite: int = 10):
        """Mostra o ranking da temporada atual"""
        await interaction.response.defer()
        
        try:
            limite = min(limite, 20)
            embed = await self.bot.season_system.get_season_leaderboard(
                interaction.guild, 
                modo, 
                limite
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando ranking_temporada: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerar ranking da temporada.", 
                ephemeral=True
            )
    
    @app_commands.command(name="minhas_recompensas", description="🎁 Mostra suas recompensas de temporadas")
    async def minhas_recompensas(self, interaction: discord.Interaction):
        """Mostra as recompensas do usuário"""
        try:
            embed = await self.bot.season_system.get_user_rewards_embed(interaction.user)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando minhas_recompensas: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter suas recompensas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="conquistas", description="🏆 Mostra suas conquistas e progresso")
    async def conquistas(self, interaction: discord.Interaction):
        """Mostra as conquistas do usuário"""
        try:
            embed = await self.bot.achievement_system.get_user_achievements_embed(interaction.user)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando conquistas: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter suas conquistas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="progresso_conquista", description="📊 Mostra o progresso de uma conquista específica")
    @app_commands.describe(conquista="Nome da conquista")
    async def progresso_conquista(self, interaction: discord.Interaction, conquista: str):
        """Mostra o progresso de uma conquista específica"""
        try:
            embed = await self.bot.achievement_system.get_achievement_progress_embed(
                interaction.user, 
                conquista
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando progresso_conquista: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter progresso da conquista.", 
                ephemeral=True
            )
    
    @app_commands.command(name="recompensas_temporada", description="🎁 Lista as recompensas disponíveis na temporada")
    async def recompensas_temporada(self, interaction: discord.Interaction):
        """Lista as recompensas disponíveis na temporada"""
        try:
            embed = await self.bot.season_system.get_season_rewards_embed()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando recompensas_temporada: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter recompensas da temporada.", 
                ephemeral=True
            )
    
    @app_commands.command(name="estatisticas_temporada", description="📈 Mostra suas estatísticas na temporada atual")
    async def estatisticas_temporada(self, interaction: discord.Interaction):
        """Mostra as estatísticas do usuário na temporada"""
        try:
            embed = await self.bot.season_system.get_user_season_stats_embed(interaction.user)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando estatisticas_temporada: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter suas estatísticas da temporada.", 
                ephemeral=True
            )

async def setup(bot):
    """Função para carregar o Cog"""
    await bot.add_cog(SeasonCommands(bot))
    logger.info("SeasonCommands Cog adicionado ao bot")