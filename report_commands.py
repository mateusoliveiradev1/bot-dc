#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extensão de comandos de relatórios para o bot Discord
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional

class ReportCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="relatorio_checkin", description="Gera relatório de check-ins")
    @app_commands.describe(
        periodo="Período em dias para o relatório (padrão: 7)"
    )
    async def relatorio_checkin(self, interaction: discord.Interaction, periodo: Optional[int] = 7):
        """Gera relatório de check-ins"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
        
        if periodo <= 0 or periodo > 365:
            await interaction.response.send_message("❌ O período deve ser entre 1 e 365 dias.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Relatório de Check-ins",
            description=f"Relatório dos últimos {periodo} dias",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Dados simulados para demonstração
        embed.add_field(name="📈 Total de Check-ins", value="42", inline=True)
        embed.add_field(name="👥 Usuários Únicos", value="15", inline=True)
        embed.add_field(name="🎯 Sessões Ativas", value="3", inline=True)
        
        embed.add_field(name="⭐ Top Participante", value="@Usuario#1234", inline=True)
        embed.add_field(name="🏆 Check-ins do Top", value="8", inline=True)
        embed.add_field(name="📅 Período", value=f"{periodo} dias", inline=True)
        
        embed.set_footer(text="Relatório gerado automaticamente")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="relatorio_servidor", description="Gera relatório geral do servidor")
    async def relatorio_servidor(self, interaction: discord.Interaction):
        """Gera relatório geral do servidor"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
        
        guild = interaction.guild
        
        embed = discord.Embed(
            title="📊 Relatório do Servidor",
            description=f"Estatísticas de **{guild.name}**",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👥 Membros Totais", value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Canais de Texto", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="🔊 Canais de Voz", value=str(len(guild.voice_channels)), inline=True)
        
        embed.add_field(name="📅 Criado em", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text="Relatório gerado automaticamente")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Configura a extensão de comandos de relatórios"""
    await bot.add_cog(ReportCommands(bot))
    
async def teardown(bot):
    """Remove a extensão de comandos de relatórios"""
    await bot.remove_cog('ReportCommands')