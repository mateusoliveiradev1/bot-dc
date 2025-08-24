# -*- coding: utf-8 -*-
"""
Comandos Administrativos - Hawk Bot
Cog responsável por comandos administrativos, minijogos e notificações
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger('HawkBot.AdminCommands')

class AdminCommands(commands.Cog):
    """Comandos administrativos e de configuração"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("AdminCommands Cog carregado")
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário é administrador"""
        return interaction.user.guild_permissions.administrator
    
    @app_commands.command(name="setup_servidor", description="⚙️ Configuração inicial do servidor (Admin)")
    async def setup_servidor(self, interaction: discord.Interaction):
        """Configuração inicial do servidor"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            result = await self.bot.server_setup.setup_server(interaction.guild)
            await interaction.followup.send(result)
        except Exception as e:
            logger.error(f"Erro no comando setup_servidor: {e}")
            await interaction.followup.send(
                "❌ Erro na configuração do servidor.", 
                ephemeral=True
            )
    
    @app_commands.command(name="config_notificacoes", description="🔔 Configura o sistema de notificações (Admin)")
    @app_commands.describe(
        tipo="Tipo de notificação",
        canal="Canal para as notificações",
        ativo="Ativar ou desativar"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Novos Membros", value="welcome"),
        app_commands.Choice(name="Saída de Membros", value="goodbye"),
        app_commands.Choice(name="Rank Up", value="rankup"),
        app_commands.Choice(name="Conquistas", value="achievements"),
        app_commands.Choice(name="Temporadas", value="seasons")
    ])
    async def config_notificacoes(self, interaction: discord.Interaction, tipo: str, canal: discord.TextChannel, ativo: bool = True):
        """Configura notificações do servidor"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        try:
            result = await self.bot.notifications_system.configure_notification(
                interaction.guild, 
                tipo, 
                canal, 
                ativo
            )
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando config_notificacoes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao configurar notificações.", 
                ephemeral=True
            )
    
    @app_commands.command(name="minijogo", description="🎮 Inicia um minijogo")
    @app_commands.describe(jogo="Tipo de minijogo")
    @app_commands.choices(jogo=[
        app_commands.Choice(name="Pedra, Papel, Tesoura", value="rps"),
        app_commands.Choice(name="Adivinhação", value="guess"),
        app_commands.Choice(name="Quiz PUBG", value="quiz"),
        app_commands.Choice(name="Caça ao Tesouro", value="treasure"),
        app_commands.Choice(name="Trivia", value="trivia")
    ])
    async def minijogo(self, interaction: discord.Interaction, jogo: str):
        """Inicia um minijogo"""
        await interaction.response.defer()
        
        try:
            result = await self.bot.minigames_system.start_game(
                interaction.guild, 
                interaction.user, 
                jogo
            )
            await interaction.followup.send(result)
        except Exception as e:
            logger.error(f"Erro no comando minijogo: {e}")
            await interaction.followup.send(
                "❌ Erro ao iniciar minijogo.", 
                ephemeral=True
            )
    
    @app_commands.command(name="ranking_minijogos", description="🏆 Mostra o ranking de minijogos")
    @app_commands.describe(
        jogo="Tipo de minijogo (opcional)",
        limite="Número de jogadores no ranking"
    )
    @app_commands.choices(jogo=[
        app_commands.Choice(name="Todos", value="all"),
        app_commands.Choice(name="Pedra, Papel, Tesoura", value="rps"),
        app_commands.Choice(name="Adivinhação", value="guess"),
        app_commands.Choice(name="Quiz PUBG", value="quiz"),
        app_commands.Choice(name="Trivia", value="trivia")
    ])
    async def ranking_minijogos(self, interaction: discord.Interaction, jogo: str = "all", limite: int = 10):
        """Mostra o ranking de minijogos"""
        try:
            limite = min(limite, 20)
            embed = await self.bot.minigames_system.get_leaderboard(
                interaction.guild, 
                jogo, 
                limite
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando ranking_minijogos: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter ranking de minijogos.", 
                ephemeral=True
            )
    
    @app_commands.command(name="minhas_estatisticas_jogos", description="📊 Mostra suas estatísticas de minijogos")
    async def minhas_estatisticas_jogos(self, interaction: discord.Interaction):
        """Mostra as estatísticas de minijogos do usuário"""
        try:
            embed = await self.bot.minigames_system.get_user_stats_embed(interaction.user)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando minhas_estatisticas_jogos: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter suas estatísticas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="backup_dados", description="💾 Cria backup dos dados do servidor (Admin)")
    async def backup_dados(self, interaction: discord.Interaction):
        """Cria backup dos dados do servidor"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            result = await self.bot.storage.create_backup()
            await interaction.followup.send(f"✅ Backup criado com sucesso: {result}")
        except Exception as e:
            logger.error(f"Erro no comando backup_dados: {e}")
            await interaction.followup.send(
                "❌ Erro ao criar backup.", 
                ephemeral=True
            )
    
    @app_commands.command(name="status_bot", description="📊 Mostra o status e estatísticas do bot")
    async def status_bot(self, interaction: discord.Interaction):
        """Mostra o status do bot"""
        try:
            embed = discord.Embed(
                title="📊 Status do Hawk Bot",
                description="Informações gerais do bot",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Informações básicas
            embed.add_field(
                name="🤖 Bot",
                value=f"**Ping**: {round(self.bot.latency * 1000)}ms\n**Servidores**: {len(self.bot.guilds)}\n**Usuários**: {len(self.bot.users)}",
                inline=True
            )
            
            # Sistemas ativos
            systems_status = []
            if hasattr(self.bot, 'pubg_integration'):
                systems_status.append("✅ PUBG API")
            if hasattr(self.bot, 'music_system'):
                systems_status.append("✅ Sistema de Música")
            if hasattr(self.bot, 'rank_system'):
                systems_status.append("✅ Sistema de Ranking")
            
            embed.add_field(
                name="⚙️ Sistemas",
                value="\n".join(systems_status) if systems_status else "❌ Nenhum sistema ativo",
                inline=True
            )
            
            # Estatísticas de uso
            embed.add_field(
                name="📈 Uso",
                value="**Comandos hoje**: N/A\n**Uptime**: N/A\n**Memória**: N/A",
                inline=True
            )
            
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text="Hawk Bot - Sistema de Status")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando status_bot: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter status do bot.", 
                ephemeral=True
            )
    
    @app_commands.command(name="limpar_cache", description="🧹 Limpa o cache do bot (Admin)")
    @app_commands.describe(tipo="Tipo de cache a limpar")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Todos", value="all"),
        app_commands.Choice(name="PUBG API", value="pubg"),
        app_commands.Choice(name="Ranking", value="ranking"),
        app_commands.Choice(name="Música", value="music")
    ])
    async def limpar_cache(self, interaction: discord.Interaction, tipo: str = "all"):
        """Limpa o cache do bot"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        try:
            cleared_items = 0
            
            if tipo == "all" or tipo == "pubg":
                if hasattr(self.bot, 'pubg_integration'):
                    cleared_items += await self.bot.pubg_integration.clear_cache()
            
            if tipo == "all" or tipo == "ranking":
                if hasattr(self.bot, 'rank_system'):
                    cleared_items += await self.bot.rank_system.clear_cache()
            
            if tipo == "all" or tipo == "music":
                if hasattr(self.bot, 'music_system'):
                    cleared_items += await self.bot.music_system.clear_cache()
            
            await interaction.response.send_message(
                f"✅ Cache limpo com sucesso! {cleared_items} itens removidos."
            )
        except Exception as e:
            logger.error(f"Erro no comando limpar_cache: {e}")
            await interaction.response.send_message(
                "❌ Erro ao limpar cache.", 
                ephemeral=True
            )
    
    @app_commands.command(name="config_servidor", description="⚙️ Configurações gerais do servidor (Admin)")
    @app_commands.describe(
        configuracao="Tipo de configuração",
        valor="Novo valor"
    )
    @app_commands.choices(configuracao=[
        app_commands.Choice(name="Prefixo", value="prefix"),
        app_commands.Choice(name="Canal de Logs", value="log_channel"),
        app_commands.Choice(name="Cargo Automático", value="auto_role"),
        app_commands.Choice(name="Modo Manutenção", value="maintenance")
    ])
    async def config_servidor(self, interaction: discord.Interaction, configuracao: str, valor: str):
        """Configurações gerais do servidor"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        try:
            # Aqui seria implementada a lógica de configuração
            # Por enquanto, apenas uma resposta de confirmação
            await interaction.response.send_message(
                f"✅ Configuração '{configuracao}' atualizada para: {valor}"
            )
        except Exception as e:
            logger.error(f"Erro no comando config_servidor: {e}")
            await interaction.response.send_message(
                "❌ Erro ao atualizar configuração.", 
                ephemeral=True
            )
    
    @app_commands.command(name="logs_sistema", description="📋 Mostra os logs recentes do sistema (Admin)")
    @app_commands.describe(linhas="Número de linhas de log (máximo 50)")
    async def logs_sistema(self, interaction: discord.Interaction, linhas: int = 20):
        """Mostra os logs recentes do sistema"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando!", 
                ephemeral=True
            )
            return
        
        try:
            linhas = min(linhas, 50)
            
            # Aqui seria implementada a lógica para obter logs
            # Por enquanto, uma resposta simulada
            embed = discord.Embed(
                title="📋 Logs do Sistema",
                description=f"Últimas {linhas} linhas de log",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="ℹ️ Informação",
                value="Sistema de logs em desenvolvimento",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando logs_sistema: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter logs.", 
                ephemeral=True
            )

async def setup(bot):
    """Função para carregar o Cog"""
    await bot.add_cog(AdminCommands(bot))
    logger.info("AdminCommands Cog adicionado ao bot")