#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extensão de comandos de lembretes para o bot Discord
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio

class ReminderCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="lembrete", description="Cria um lembrete")
    @app_commands.describe(
        tempo="Tempo em minutos para o lembrete",
        mensagem="Mensagem do lembrete (opcional)"
    )
    async def lembrete(self, interaction: discord.Interaction, tempo: int, mensagem: Optional[str] = "Lembrete!"):
        """Cria um lembrete simples"""
        if tempo <= 0 or tempo > 1440:  # Máximo 24 horas
            await interaction.response.send_message("❌ O tempo deve ser entre 1 e 1440 minutos (24 horas).", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⏰ Lembrete Criado",
            description=f"Você será lembrado em {tempo} minutos.",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="📝 Mensagem", value=mensagem, inline=False)
        embed.add_field(name="⏰ Tempo", value=f"{tempo} minutos", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Agendar lembrete (implementação básica)
        await asyncio.sleep(tempo * 60)
        
        try:
            embed_reminder = discord.Embed(
                title="🔔 Lembrete!",
                description=mensagem,
                color=0xff9900,
                timestamp=datetime.now()
            )
            await interaction.user.send(embed=embed_reminder)
        except discord.Forbidden:
            # Se não conseguir enviar DM, tenta no canal
            try:
                await interaction.followup.send(f"🔔 {interaction.user.mention} - {mensagem}")
            except:
                pass

async def setup(bot):
    """Configura a extensão de comandos de lembretes"""
    await bot.add_cog(ReminderCommands(bot))
    
async def teardown(bot):
    """Remove a extensão de comandos de lembretes"""
    await bot.remove_cog('ReminderCommands')