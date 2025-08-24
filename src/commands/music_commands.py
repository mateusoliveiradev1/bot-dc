# -*- coding: utf-8 -*-
"""
Comandos de Música - Hawk Bot
Cog responsável por todos os comandos relacionados ao sistema de música
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger('HawkBot.MusicCommands')

class MusicCommands(commands.Cog):
    """Comandos relacionados ao sistema de música"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("MusicCommands Cog carregado")
    
    @app_commands.command(name="tocar", description="🎵 Toca uma música ou adiciona à fila")
    @app_commands.describe(musica="Nome da música ou URL do YouTube")
    async def tocar(self, interaction: discord.Interaction, musica: str):
        """Toca uma música"""
        await interaction.response.defer()
        
        try:
            # Verificar se o usuário está em um canal de voz
            if not interaction.user.voice:
                await interaction.followup.send(
                    "❌ Você precisa estar em um canal de voz para usar este comando!", 
                    ephemeral=True
                )
                return
            
            result = await self.bot.music_system.play_music(
                interaction.guild, 
                interaction.user.voice.channel, 
                musica, 
                interaction.user
            )
            
            await interaction.followup.send(result)
            
        except Exception as e:
            logger.error(f"Erro no comando tocar: {e}")
            await interaction.followup.send(
                "❌ Erro ao tocar música. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="pausar", description="⏸️ Pausa a música atual")
    async def pausar(self, interaction: discord.Interaction):
        """Pausa a música atual"""
        try:
            result = await self.bot.music_system.pause_music(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando pausar: {e}")
            await interaction.response.send_message(
                "❌ Erro ao pausar música.", 
                ephemeral=True
            )
    
    @app_commands.command(name="continuar", description="▶️ Continua a música pausada")
    async def continuar(self, interaction: discord.Interaction):
        """Continua a música pausada"""
        try:
            result = await self.bot.music_system.resume_music(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando continuar: {e}")
            await interaction.response.send_message(
                "❌ Erro ao continuar música.", 
                ephemeral=True
            )
    
    @app_commands.command(name="pular", description="⏭️ Pula para a próxima música")
    async def pular(self, interaction: discord.Interaction):
        """Pula para a próxima música"""
        try:
            result = await self.bot.music_system.skip_music(interaction.guild, interaction.user)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando pular: {e}")
            await interaction.response.send_message(
                "❌ Erro ao pular música.", 
                ephemeral=True
            )
    
    @app_commands.command(name="parar", description="⏹️ Para a música e limpa a fila")
    async def parar(self, interaction: discord.Interaction):
        """Para a música e limpa a fila"""
        try:
            result = await self.bot.music_system.stop_music(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando parar: {e}")
            await interaction.response.send_message(
                "❌ Erro ao parar música.", 
                ephemeral=True
            )
    
    @app_commands.command(name="fila", description="📋 Mostra a fila de músicas")
    async def fila(self, interaction: discord.Interaction):
        """Mostra a fila de músicas"""
        try:
            embed = await self.bot.music_system.get_queue_embed(interaction.guild)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando fila: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter fila de músicas.", 
                ephemeral=True
            )
    
    @app_commands.command(name="volume", description="🔊 Ajusta o volume da música")
    @app_commands.describe(nivel="Nível do volume (0-100)")
    async def volume(self, interaction: discord.Interaction, nivel: int):
        """Ajusta o volume da música"""
        try:
            if not 0 <= nivel <= 100:
                await interaction.response.send_message(
                    "❌ O volume deve estar entre 0 e 100!", 
                    ephemeral=True
                )
                return
            
            result = await self.bot.music_system.set_volume(interaction.guild, nivel)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando volume: {e}")
            await interaction.response.send_message(
                "❌ Erro ao ajustar volume.", 
                ephemeral=True
            )
    
    @app_commands.command(name="loop", description="🔄 Ativa/desativa o loop da música atual")
    async def loop(self, interaction: discord.Interaction):
        """Ativa/desativa o loop da música atual"""
        try:
            result = await self.bot.music_system.toggle_loop(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando loop: {e}")
            await interaction.response.send_message(
                "❌ Erro ao alternar loop.", 
                ephemeral=True
            )
    
    @app_commands.command(name="embaralhar", description="🔀 Embaralha a fila de músicas")
    async def embaralhar(self, interaction: discord.Interaction):
        """Embaralha a fila de músicas"""
        try:
            result = await self.bot.music_system.shuffle_queue(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando embaralhar: {e}")
            await interaction.response.send_message(
                "❌ Erro ao embaralhar fila.", 
                ephemeral=True
            )
    
    @app_commands.command(name="desconectar", description="🚪 Desconecta o bot do canal de voz")
    async def desconectar(self, interaction: discord.Interaction):
        """Desconecta o bot do canal de voz"""
        try:
            result = await self.bot.music_system.disconnect(interaction.guild)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando desconectar: {e}")
            await interaction.response.send_message(
                "❌ Erro ao desconectar.", 
                ephemeral=True
            )
    
    @app_commands.command(name="tocando_agora", description="🎵 Mostra a música que está tocando")
    async def tocando_agora(self, interaction: discord.Interaction):
        """Mostra a música que está tocando"""
        try:
            embed = await self.bot.music_system.get_now_playing_embed(interaction.guild)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando tocando_agora: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter música atual.", 
                ephemeral=True
            )
    
    @app_commands.command(name="historico_musicas", description="📜 Mostra o histórico de músicas tocadas")
    async def historico_musicas(self, interaction: discord.Interaction):
        """Mostra o histórico de músicas tocadas"""
        try:
            embed = await self.bot.music_system.get_history_embed(interaction.guild)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando historico_musicas: {e}")
            await interaction.response.send_message(
                "❌ Erro ao obter histórico.", 
                ephemeral=True
            )
    
    @app_commands.command(name="favoritos", description="⭐ Gerencia suas músicas favoritas")
    @app_commands.describe(
        acao="Ação a ser realizada",
        musica="Nome da música (apenas para adicionar)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Listar", value="list"),
        app_commands.Choice(name="Adicionar", value="add"),
        app_commands.Choice(name="Remover", value="remove")
    ])
    async def favoritos(self, interaction: discord.Interaction, acao: str, musica: Optional[str] = None):
        """Gerencia músicas favoritas"""
        await interaction.response.defer()
        
        try:
            if acao == "list":
                embed = await self.bot.music_system.get_favorites_embed(interaction.user)
                await interaction.followup.send(embed=embed)
            
            elif acao == "add":
                if not musica:
                    await interaction.followup.send(
                        "❌ Você precisa especificar uma música para adicionar!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.add_favorite(interaction.user, musica)
                await interaction.followup.send(result)
            
            elif acao == "remove":
                if not musica:
                    await interaction.followup.send(
                        "❌ Você precisa especificar uma música para remover!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.remove_favorite(interaction.user, musica)
                await interaction.followup.send(result)
                
        except Exception as e:
            logger.error(f"Erro no comando favoritos: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerenciar favoritos.", 
                ephemeral=True
            )
    
    @app_commands.command(name="filtro_audio", description="🎛️ Aplica filtros de áudio")
    @app_commands.describe(filtro="Tipo de filtro a aplicar")
    @app_commands.choices(filtro=[
        app_commands.Choice(name="Nenhum", value="none"),
        app_commands.Choice(name="Bass Boost", value="bassboost"),
        app_commands.Choice(name="Nightcore", value="nightcore"),
        app_commands.Choice(name="Vaporwave", value="vaporwave"),
        app_commands.Choice(name="8D", value="8d")
    ])
    async def filtro_audio(self, interaction: discord.Interaction, filtro: str):
        """Aplica filtros de áudio"""
        try:
            result = await self.bot.music_system.apply_audio_filter(interaction.guild, filtro)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando filtro_audio: {e}")
            await interaction.response.send_message(
                "❌ Erro ao aplicar filtro.", 
                ephemeral=True
            )
    
    @app_commands.command(name="votar_pular", description="🗳️ Inicia uma votação para pular a música")
    async def votar_pular(self, interaction: discord.Interaction):
        """Inicia uma votação para pular a música"""
        try:
            result = await self.bot.music_system.start_skip_vote(interaction.guild, interaction.user)
            await interaction.response.send_message(result)
        except Exception as e:
            logger.error(f"Erro no comando votar_pular: {e}")
            await interaction.response.send_message(
                "❌ Erro ao iniciar votação.", 
                ephemeral=True
            )
    
    @app_commands.command(name="playlist", description="📝 Gerencia playlists personalizadas")
    @app_commands.describe(
        acao="Ação a ser realizada",
        nome="Nome da playlist",
        musica="Nome da música (para adicionar/remover)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Criar", value="create"),
        app_commands.Choice(name="Listar", value="list"),
        app_commands.Choice(name="Tocar", value="play"),
        app_commands.Choice(name="Adicionar Música", value="add_song"),
        app_commands.Choice(name="Remover Música", value="remove_song"),
        app_commands.Choice(name="Deletar", value="delete")
    ])
    async def playlist(self, interaction: discord.Interaction, acao: str, nome: Optional[str] = None, musica: Optional[str] = None):
        """Gerencia playlists personalizadas"""
        await interaction.response.defer()
        
        try:
            if acao == "create":
                if not nome:
                    await interaction.followup.send(
                        "❌ Você precisa especificar um nome para a playlist!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.create_playlist(interaction.user, nome)
                await interaction.followup.send(result)
            
            elif acao == "list":
                embed = await self.bot.music_system.get_playlists_embed(interaction.user)
                await interaction.followup.send(embed=embed)
            
            elif acao == "play":
                if not nome:
                    await interaction.followup.send(
                        "❌ Você precisa especificar o nome da playlist!", 
                        ephemeral=True
                    )
                    return
                
                if not interaction.user.voice:
                    await interaction.followup.send(
                        "❌ Você precisa estar em um canal de voz!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.play_playlist(
                    interaction.guild, 
                    interaction.user.voice.channel, 
                    interaction.user, 
                    nome
                )
                await interaction.followup.send(result)
            
            elif acao == "add_song":
                if not nome or not musica:
                    await interaction.followup.send(
                        "❌ Você precisa especificar o nome da playlist e da música!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.add_to_playlist(interaction.user, nome, musica)
                await interaction.followup.send(result)
            
            elif acao == "remove_song":
                if not nome or not musica:
                    await interaction.followup.send(
                        "❌ Você precisa especificar o nome da playlist e da música!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.remove_from_playlist(interaction.user, nome, musica)
                await interaction.followup.send(result)
            
            elif acao == "delete":
                if not nome:
                    await interaction.followup.send(
                        "❌ Você precisa especificar o nome da playlist!", 
                        ephemeral=True
                    )
                    return
                
                result = await self.bot.music_system.delete_playlist(interaction.user, nome)
                await interaction.followup.send(result)
                
        except Exception as e:
            logger.error(f"Erro no comando playlist: {e}")
            await interaction.followup.send(
                "❌ Erro ao gerenciar playlist.", 
                ephemeral=True
            )

async def setup(bot):
    """Função para carregar o Cog"""
    await bot.add_cog(MusicCommands(bot))
    logger.info("MusicCommands Cog adicionado ao bot")