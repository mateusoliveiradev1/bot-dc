#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples do bot moderno
"""

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class SimpleModernBot(commands.Bot):
    """Versão simplificada do bot moderno para teste"""
    
    def __init__(self):
        # Configurar intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        # Inicializar bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True
        )
        
        print("Bot moderno simplificado inicializado")
    
    async def on_ready(self):
        """Evento chamado quando o bot está pronto"""
        print(f"Bot conectado como {self.user} (ID: {self.user.id})")
        print(f"Conectado a {len(self.guilds)} servidores")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            print(f"Sincronizados {len(synced)} comandos slash")
        except Exception as e:
            print(f"Erro ao sincronizar comandos slash: {e}")
    
    async def on_guild_join(self, guild):
        """Evento chamado quando o bot entra em um servidor"""
        print(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild):
        """Evento chamado quando o bot sai de um servidor"""
        print(f"Bot removido do servidor: {guild.name} (ID: {guild.id})")
    
    async def on_error(self, event, *args, **kwargs):
        """Handler global de erros"""
        print(f"Erro no evento {event}")
    
    async def on_command_error(self, ctx, error):
        """Handler de erros de comandos"""
        print(f"Erro no comando {ctx.command}: {error}")
        await ctx.send(f"Erro: {error}")

@commands.command(name='ping')
async def ping_command(ctx):
    """Comando de teste ping"""
    await ctx.send('Pong! Bot moderno funcionando!')

@commands.command(name='status')
async def status_command(ctx):
    """Comando de status do bot"""
    embed = discord.Embed(
        title="Status do Bot Moderno",
        description="Bot está funcionando corretamente!",
        color=discord.Color.green()
    )
    embed.add_field(name="Servidores", value=len(ctx.bot.guilds), inline=True)
    embed.add_field(name="Usuários", value=sum(guild.member_count for guild in ctx.bot.guilds), inline=True)
    await ctx.send(embed=embed)

async def main():
    """Função principal"""
    bot = None
    try:
        print("Iniciando Bot Moderno Simplificado...")
        
        # Criar bot
        bot = SimpleModernBot()
        
        # Adicionar comandos
        bot.add_command(ping_command)
        bot.add_command(status_command)
        
        # Obter token
        token = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
        if not token:
            print("Erro: Token do Discord não encontrado!")
            print("Configure DISCORD_BOT_TOKEN ou DISCORD_TOKEN no arquivo .env")
            return
        
        # Executar bot
        await bot.start(token)
        
    except KeyboardInterrupt:
        print("Interrupção do usuário detectada")
    except Exception as e:
        print(f"Erro fatal: {e}")
        raise
    finally:
        if bot:
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro fatal durante execução: {e}")