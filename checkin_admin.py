#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extensão de comandos administrativos de check-in para o bot Discord
"""

import discord
from discord.ext import commands
from src.features.checkin.admin import CheckInAdmin
from src.core.storage import DataStorage

async def setup(bot):
    """Configura a extensão de comandos administrativos de check-in"""
    # Criar instância do sistema de armazenamento se não existir
    if not hasattr(bot, 'storage'):
        bot.storage = DataStorage()
    
    # Criar e adicionar o cog
    cog = CheckInAdmin(bot)
    cog.setup_checkin_system(bot.storage)
    await bot.add_cog(cog)
    
async def teardown(bot):
    """Remove a extensão de comandos administrativos de check-in"""
    await bot.remove_cog('CheckInAdmin')