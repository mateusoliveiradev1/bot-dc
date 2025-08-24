#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hawk Bot Moderno - Versão Corrigida
Arquitetura moderna com injeção de dependências, cache inteligente e logging estruturado
"""

import os
import sys
import time
import signal
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class ModernHawkBot(commands.Bot):
    """Bot moderno do Hawk com arquitetura aprimorada"""
    
    def __init__(self):
        # Configurar intents do Discord
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        
        # Obter configurações do ambiente
        self.bot_token = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
        self.command_prefix = os.getenv('DISCORD_COMMAND_PREFIX', '!')
        
        if not self.bot_token:
            raise ValueError("Token do Discord não encontrado! Configure DISCORD_BOT_TOKEN no arquivo .env")
        
        # Inicializar bot
        super().__init__(
            command_prefix=self.command_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None
        )
        
        # Variáveis de controle
        self._startup_time = time.time()
        self._shutdown_requested = False
        
        # Configurar logging básico
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ModernHawkBot')
        
        # Estatísticas básicas
        self.stats = {
            'commands_executed': 0,
            'errors_handled': 0,
            'guilds_joined': 0,
            'guilds_left': 0
        }
        
        self.logger.info("ModernHawkBot inicializado")
    
    async def setup_hook(self):
        """Hook de configuração chamado durante a inicialização"""
        try:
            self.logger.info("Iniciando setup do bot...")
            
            # Carregar comandos (Cogs)
            await self._load_commands()
            
            # Configurar handlers de sinal
            self._setup_signal_handlers()
            
            startup_time = (time.time() - self._startup_time) * 1000
            self.logger.info(f"Setup do bot concluído em {startup_time:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"Erro durante setup do bot: {e}", exc_info=True)
            raise
    
    async def _load_commands(self):
        """Carrega todos os comandos (Cogs)"""
        self.logger.info("Carregando comandos...")
        
        cogs_to_load = [
            'src.commands.pubg_commands',
            'src.commands.music_commands', 
            'src.commands.season_commands',
            'src.commands.admin_commands',
            'src.commands.economy_commands'
        ]
        
        loaded_cogs = 0
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                loaded_cogs += 1
                self.logger.info(f"Cog carregado: {cog}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar cog {cog}: {e}")
        
        self.logger.info(f"Carregados {loaded_cogs}/{len(cogs_to_load)} cogs")
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        if sys.platform != 'win32':
            
            def signal_handler(signum, frame):
                self.logger.info(f"Sinal recebido: {signum}")
                self._shutdown_requested = True
                asyncio.create_task(self.close())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
    
    async def on_ready(self):
        """Evento chamado quando o bot está conectado e pronto"""
        startup_time = (time.time() - self._startup_time) * 1000 if self._startup_time else 0
        
        self.logger.info(f"Bot conectado como {self.user} (ID: {self.user.id})")
        self.logger.info(f"Conectado a {len(self.guilds)} servidores")
        self.logger.info(f"Tempo total de inicialização: {startup_time:.2f}ms")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Sincronizados {len(synced)} comandos slash")
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar comandos slash: {e}", exc_info=True)
        
        # Atualizar status
        await self.change_presence(
            activity=discord.Game(name=f"{self.command_prefix}help | {len(self.guilds)} servidores")
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Evento chamado quando o bot entra em um servidor"""
        self.stats['guilds_joined'] += 1
        self.logger.info(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id}) - Membros: {guild.member_count}")
        
        # Atualizar status
        await self.change_presence(
            activity=discord.Game(name=f"{self.command_prefix}help | {len(self.guilds)} servidores")
        )
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Evento chamado quando o bot sai de um servidor"""
        self.stats['guilds_left'] += 1
        self.logger.info(f"Bot removido do servidor: {guild.name} (ID: {guild.id})")
        
        # Atualizar status
        await self.change_presence(
            activity=discord.Game(name=f"{self.command_prefix}help | {len(self.guilds)} servidores")
        )
    
    async def on_command(self, ctx: commands.Context):
        """Evento chamado quando um comando é executado"""
        self.stats['commands_executed'] += 1
        self.logger.info(f"Comando executado: {ctx.command} por {ctx.author} em {ctx.guild}")
    
    async def on_error(self, event: str, *args, **kwargs):
        """Handler global de erros"""
        self.stats['errors_handled'] += 1
        self.logger.error(f"Erro no evento {event}", exc_info=True)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handler de erros de comandos"""
        self.stats['errors_handled'] += 1
        self.logger.error(f"Erro no comando {ctx.command}: {error}")
        
        # Enviar mensagem de erro amigável
        if isinstance(error, commands.CommandNotFound):
            return  # Ignorar comandos não encontrados
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Argumento obrigatório ausente: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Argumento inválido: {error}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ Eu não tenho as permissões necessárias para executar este comando.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Comando em cooldown. Tente novamente em {error.retry_after:.1f}s")
        else:
            await ctx.send(f"❌ Erro inesperado: {error}")
    
    async def close(self):
        """Fecha o bot de forma limpa"""
        if self._shutdown_requested:
            return
        
        self._shutdown_requested = True
        self.logger.info("Iniciando shutdown do bot...")
        
        try:
            # Fechar conexões e limpar recursos
            await super().close()
            
            self.logger.info("Shutdown concluído com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante shutdown: {e}", exc_info=True)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Retorna o status de saúde do bot"""
        return {
            'status': 'healthy' if self.is_ready() else 'starting',
            'uptime': time.time() - self._startup_time if self._startup_time else 0,
            'guilds': len(self.guilds),
            'users': sum(guild.member_count for guild in self.guilds),
            'latency': self.latency * 1000,  # em ms
            'stats': self.stats.copy(),
            'memory_usage': self._get_memory_usage(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Retorna informações de uso de memória"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas do bot"""
        health = await self.get_health_status()
        
        return {
            'health': health,
            'features': {
                'cogs_loaded': len(self.cogs),
                'commands_available': len(self.commands),
                'extensions_loaded': len(self.extensions)
            },
            'discord': {
                'api_version': discord.__version__,
                'gateway_version': self.ws.gateway_version if self.ws else None,
                'shard_count': self.shard_count,
                'shard_id': self.shard_id
            }
        }

# Comandos básicos integrados
@commands.command(name='ping')
async def ping_command(ctx):
    """Verifica a latência do bot"""
    latency = ctx.bot.latency * 1000
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: {latency:.1f}ms",
        color=discord.Color.green() if latency < 100 else discord.Color.orange()
    )
    await ctx.send(embed=embed)

@commands.command(name='status', aliases=['info'])
async def status_command(ctx):
    """Mostra informações do bot"""
    health = await ctx.bot.get_health_status()
    
    embed = discord.Embed(
        title="📊 Status do Hawk Bot",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🌐 Conectividade",
        value=f"**Status:** {health['status'].title()}\n**Latência:** {health['latency']:.1f}ms",
        inline=True
    )
    
    embed.add_field(
        name="📈 Estatísticas",
        value=f"**Servidores:** {health['guilds']}\n**Usuários:** {health['users']:,}",
        inline=True
    )
    
    uptime_seconds = int(health['uptime'])
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    embed.add_field(
        name="⏱️ Tempo Online",
        value=f"{hours}h {minutes}m {seconds}s",
        inline=True
    )
    
    embed.add_field(
        name="🎯 Comandos",
        value=f"**Executados:** {health['stats']['commands_executed']}\n**Erros:** {health['stats']['errors_handled']}",
        inline=True
    )
    
    if 'error' not in health['memory_usage']:
        embed.add_field(
            name="💾 Memória",
            value=f"**Uso:** {health['memory_usage']['rss_mb']:.1f}MB\n**Percentual:** {health['memory_usage']['percent']:.1f}%",
            inline=True
        )
    
    embed.timestamp = datetime.utcnow()
    embed.set_footer(text="Hawk Bot Moderno")
    
    await ctx.send(embed=embed)

@commands.command(name='help')
async def help_command(ctx, *, command_name: str = None):
    """Mostra ajuda sobre comandos"""
    if command_name:
        # Ajuda específica de um comando
        command = ctx.bot.get_command(command_name)
        if not command:
            await ctx.send(f"❌ Comando `{command_name}` não encontrado.")
            return
        
        embed = discord.Embed(
            title=f"📖 Ajuda: {command.name}",
            description=command.help or "Sem descrição disponível.",
            color=discord.Color.blue()
        )
        
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
        
        embed.add_field(
            name="Uso",
            value=f"`{ctx.prefix}{command.name} {command.signature}`",
            inline=False
        )
        
    else:
        # Ajuda geral
        embed = discord.Embed(
            title="📚 Hawk Bot - Comandos Disponíveis",
            description="Use `!help <comando>` para mais detalhes sobre um comando específico.",
            color=discord.Color.blue()
        )
        
        # Agrupar comandos por categoria
        categories = {}
        for command in ctx.bot.commands:
            if command.hidden:
                continue
            
            category = getattr(command.cog, 'qualified_name', 'Geral') if command.cog else 'Geral'
            if category not in categories:
                categories[category] = []
            categories[category].append(command)
        
        for category, commands_list in categories.items():
            command_names = [f"`{cmd.name}`" for cmd in commands_list]
            embed.add_field(
                name=f"📂 {category}",
                value=" • ".join(command_names) or "Nenhum comando",
                inline=False
            )
    
    embed.set_footer(text=f"Prefixo: {ctx.prefix}")
    await ctx.send(embed=embed)

async def main():
    """Função principal"""
    bot = None
    try:
        print("🚀 Iniciando Hawk Bot Moderno...")
        
        # Criar e executar bot
        bot = ModernHawkBot()
        
        # Adicionar comandos básicos
        bot.add_command(ping_command)
        bot.add_command(status_command)
        bot.add_command(help_command)
        
        # Executar bot
        await bot.start(bot.bot_token)
        
    except KeyboardInterrupt:
        print("⚠️ Interrupção do usuário detectada")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        raise
    finally:
        if bot:
            await bot.close()

def main_sync():
    """Função principal síncrona"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Bot interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal durante execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_sync()