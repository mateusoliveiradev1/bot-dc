# -*- coding: utf-8 -*-
"""
Comandos Modernizados de Música

Sistema avançado de comandos de música com:
- Queue inteligente com recomendações automáticas
- Filtros de áudio avançados
- Sistema de playlists e favoritos
- Análise de padrões de escuta
- Rate limiting e cache inteligente
- Métricas e monitoramento
- Integração com sistemas core modernos

Autor: Assistant
Versão: 2.0.0
"""

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging

# Imports dos sistemas core
try:
    from ..core.secure_logger import SecureLogger
    from ..core.smart_cache import SmartCache
    from ..core.metrics_collector import MetricsCollector
    from ..core.data_validator import DataValidator
    from ..core.event_system import EventSystem
    from ..core.rate_limiter import RateLimiter
except ImportError:
    # Fallback para desenvolvimento
    SecureLogger = None
    SmartCache = None
    MetricsCollector = None
    DataValidator = None
    EventSystem = None
    RateLimiter = None

# Import do sistema de música modernizado
try:
    from ..features.music.modern_system import (
        ModernMusicSystem, Song, Playlist, AudioFilter, QueueMode,
        PlaybackState, MusicGenre, get_audio_filter_description,
        validate_youtube_url, MusicSystemError, PlayerNotFoundError,
        QueueFullError, InvalidSongError, PlaylistNotFoundError,
        RateLimitExceededError
    )
except ImportError:
    # Fallback para desenvolvimento
    ModernMusicSystem = None
    Song = None
    Playlist = None
    AudioFilter = None
    QueueMode = None
    PlaybackState = None
    MusicGenre = None
    get_audio_filter_description = lambda x: "Filtro desconhecido"
    validate_youtube_url = lambda x: True
    MusicSystemError = Exception
    PlayerNotFoundError = Exception
    QueueFullError = Exception
    InvalidSongError = Exception
    PlaylistNotFoundError = Exception
    RateLimitExceededError = Exception

class ModernMusicCommands(commands.Cog):
    """Comandos modernizados de música com funcionalidades avançadas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = getattr(bot, 'secure_logger', None)
        self.cache = getattr(bot, 'smart_cache', None)
        self.metrics = getattr(bot, 'metrics_collector', None)
        self.validator = getattr(bot, 'data_validator', None)
        self.events = getattr(bot, 'event_system', None)
        self.rate_limiter = getattr(bot, 'rate_limiter', None)
        
        # Sistema de música modernizado
        self.music_system = getattr(bot, 'modern_music_system', None)
        
        if self.logger:
            self.logger.info("Comandos modernizados de música inicializados")
    
    async def cog_load(self):
        """Executado quando o cog é carregado"""
        if self.events:
            await self.events.emit('music_commands_loaded', {'timestamp': datetime.now()})
    
    async def cog_unload(self):
        """Executado quando o cog é descarregado"""
        if self.events:
            await self.events.emit('music_commands_unloaded', {'timestamp': datetime.now()})
    
    # ==================== COMANDOS PRINCIPAIS ====================
    
    @app_commands.command(name="tocar", description="🎵 Tocar uma música ou playlist")
    @app_commands.describe(
        query="Nome da música, URL do YouTube ou termo de busca",
        posicao="Posição na fila (1 = próxima música)",
        volume="Volume inicial (0-100)"
    )
    async def play_command(self, interaction: discord.Interaction, 
                          query: str, posicao: Optional[int] = None, 
                          volume: Optional[int] = None):
        """Comando principal para tocar música"""
        await interaction.response.defer()
        
        try:
            # Rate limiting
            if self.rate_limiter:
                is_allowed, retry_after = await self.rate_limiter.check_rate_limit(
                    f"music_play_{interaction.user.id}", 10, 60  # 10 comandos por minuto
                )
                if not is_allowed:
                    embed = self._create_error_embed(
                        "⏰ Rate Limit",
                        f"Muitos comandos! Tente novamente em {retry_after:.1f}s"
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Validações básicas
            if not interaction.user.voice:
                embed = self._create_error_embed(
                    "❌ Erro",
                    "Você precisa estar em um canal de voz!"
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível no momento."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Validar volume se fornecido
            if volume is not None:
                if not 0 <= volume <= 100:
                    embed = self._create_error_embed(
                        "❌ Volume Inválido",
                        "O volume deve estar entre 0 e 100."
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                volume = volume / 100.0
            
            # Buscar música
            embed_searching = self._create_info_embed(
                "🔍 Buscando",
                f"Procurando por: `{query}`"
            )
            await interaction.followup.send(embed=embed_searching)
            
            # Usar cache para buscas recentes
            cache_key = f"music_search_{hash(query)}"
            cached_result = None
            if self.cache:
                cached_result = await self.cache.get(cache_key)
            
            if cached_result:
                songs = cached_result
                if self.logger:
                    self.logger.info(f"Resultado de busca obtido do cache: {query}")
            else:
                songs = await self.music_system.search_songs(query, limit=1)
                if self.cache and songs:
                    await self.cache.set(cache_key, songs, ttl=3600)  # Cache por 1 hora
            
            if not songs:
                embed = self._create_error_embed(
                    "❌ Não Encontrado",
                    f"Nenhuma música encontrada para: `{query}`"
                )
                await interaction.edit_original_response(embed=embed)
                return
            
            song = songs[0]
            
            # Adicionar à fila
            success, message = await self.music_system.add_to_queue(
                interaction.guild.id,
                song,
                interaction.user.voice.channel,
                position=posicao
            )
            
            if not success:
                embed = self._create_error_embed("❌ Erro", message)
                await interaction.edit_original_response(embed=embed)
                return
            
            # Definir volume se especificado
            if volume is not None:
                await self.music_system.set_volume(interaction.guild.id, volume)
            
            # Criar embed de sucesso
            player = self.music_system.get_player(interaction.guild.id)
            if player and player.current_song:
                embed = self._create_now_playing_embed(player.current_song, player)
            else:
                embed = self._create_success_embed(
                    "✅ Adicionado à Fila",
                    f"**{song.title}**\n"
                    f"🕒 Duração: `{self.music_system.format_duration(song.duration)}`\n"
                    f"👤 Solicitado por: {interaction.user.mention}"
                )
            
            await interaction.edit_original_response(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_songs_played_total')
                await self.metrics.increment(f'music_genre_{song.genre.value}_total')
            
            # Evento
            if self.events:
                await self.events.emit('song_added_to_queue', {
                    'guild_id': interaction.guild.id,
                    'user_id': interaction.user.id,
                    'song_title': song.title,
                    'song_duration': song.duration
                })
        
        except RateLimitExceededError:
            embed = self._create_error_embed(
                "⏰ Rate Limit",
                "Muitas solicitações! Aguarde um momento."
            )
            await interaction.edit_original_response(embed=embed)
        
        except QueueFullError:
            embed = self._create_error_embed(
                "📋 Fila Cheia",
                "A fila de música está cheia. Remova algumas músicas primeiro."
            )
            await interaction.edit_original_response(embed=embed)
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando tocar: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="pausar", description="⏸️ Pausar ou retomar a música atual")
    async def pause_command(self, interaction: discord.Interaction):
        """Pausar ou retomar a reprodução"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            player = self.music_system.get_player(interaction.guild.id)
            if not player or not player.current_song:
                embed = self._create_error_embed(
                    "❌ Nada Tocando",
                    "Não há música tocando no momento."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            success, message = await self.music_system.pause_resume(interaction.guild.id)
            
            if success:
                action = "pausada" if player.state == PlaybackState.PAUSED else "retomada"
                embed = self._create_success_embed(
                    f"{'⏸️' if player.state == PlaybackState.PAUSED else '▶️'} Música {action.title()}",
                    f"**{player.current_song.title}** foi {action}."
                )
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment(f'music_pause_resume_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando pausar: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="pular", description="⏭️ Pular a música atual")
    @app_commands.describe(forcado="Pular sem votação (apenas administradores)")
    async def skip_command(self, interaction: discord.Interaction, forcado: bool = False):
        """Pular música atual"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            player = self.music_system.get_player(interaction.guild.id)
            if not player or not player.current_song:
                embed = self._create_error_embed(
                    "❌ Nada Tocando",
                    "Não há música tocando no momento."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar permissões para skip forçado
            if forcado and not interaction.user.guild_permissions.manage_channels:
                embed = self._create_error_embed(
                    "❌ Sem Permissão",
                    "Apenas administradores podem forçar o skip."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if forcado:
                success, message = await self.music_system.skip_song(interaction.guild.id, force=True)
            else:
                success, message = await self.music_system.add_skip_vote(
                    interaction.guild.id, interaction.user.id
                )
            
            if success:
                if "pulada" in message:
                    embed = self._create_success_embed("⏭️ Música Pulada", message)
                else:
                    embed = self._create_info_embed("🗳️ Voto Registrado", message)
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_skips_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando pular: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="parar", description="⏹️ Parar a música e limpar a fila")
    async def stop_command(self, interaction: discord.Interaction):
        """Parar música e limpar fila"""
        await interaction.response.defer()
        
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.manage_channels:
                embed = self._create_error_embed(
                    "❌ Sem Permissão",
                    "Apenas administradores podem parar a música."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            success, message = await self.music_system.stop_music(interaction.guild.id)
            
            if success:
                embed = self._create_success_embed("⏹️ Música Parada", message)
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_stops_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando parar: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="fila", description="📋 Ver a fila de músicas")
    @app_commands.describe(pagina="Página da fila (padrão: 1)")
    async def queue_command(self, interaction: discord.Interaction, pagina: int = 1):
        """Mostrar fila de músicas"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            player = self.music_system.get_player(interaction.guild.id)
            if not player:
                embed = self._create_error_embed(
                    "❌ Player Inativo",
                    "Não há player ativo neste servidor."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            queue_info = player.get_queue_info()
            
            if not queue_info['queue'] and not player.current_song:
                embed = self._create_info_embed(
                    "📋 Fila Vazia",
                    "Não há músicas na fila. Use `/tocar` para adicionar músicas!"
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = self._create_queue_embed(player, queue_info, pagina)
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_queue_views_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando fila: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="volume", description="🔊 Ajustar o volume da música")
    @app_commands.describe(nivel="Nível do volume (0-100)")
    async def volume_command(self, interaction: discord.Interaction, nivel: int):
        """Ajustar volume"""
        await interaction.response.defer()
        
        try:
            # Validar nível
            if not 0 <= nivel <= 100:
                embed = self._create_error_embed(
                    "❌ Volume Inválido",
                    "O volume deve estar entre 0 e 100."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            success, message = await self.music_system.set_volume(
                interaction.guild.id, nivel / 100.0
            )
            
            if success:
                volume_emoji = "🔇" if nivel == 0 else "🔉" if nivel < 50 else "🔊"
                embed = self._create_success_embed(
                    f"{volume_emoji} Volume Ajustado",
                    f"Volume definido para **{nivel}%**"
                )
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_volume_changes_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando volume: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== COMANDOS DE PLAYLIST ====================
    
    @app_commands.command(name="playlist_criar", description="📝 Criar uma nova playlist")
    @app_commands.describe(
        nome="Nome da playlist",
        publica="Tornar a playlist pública (padrão: False)",
        descricao="Descrição da playlist"
    )
    async def create_playlist_command(self, interaction: discord.Interaction, 
                                    nome: str, publica: bool = False, 
                                    descricao: Optional[str] = None):
        """Criar nova playlist"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            success, message = await self.music_system.create_playlist(
                interaction.user.id, nome, publica, descricao
            )
            
            if success:
                visibility = "pública" if publica else "privada"
                embed = self._create_success_embed(
                    "📝 Playlist Criada",
                    f"Playlist **{nome}** ({visibility}) criada com sucesso!\n"
                    f"{f'📄 Descrição: {descricao}' if descricao else ''}"
                )
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_playlists_created_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao criar playlist: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="playlist_tocar", description="▶️ Tocar uma playlist")
    @app_commands.describe(
        nome="Nome da playlist",
        usuario="Usuário dono da playlist (para playlists públicas)",
        embaralhar="Embaralhar a playlist"
    )
    async def play_playlist_command(self, interaction: discord.Interaction, 
                                  nome: str, usuario: Optional[discord.User] = None,
                                  embaralhar: bool = False):
        """Tocar playlist"""
        await interaction.response.defer()
        
        try:
            if not interaction.user.voice:
                embed = self._create_error_embed(
                    "❌ Erro",
                    "Você precisa estar em um canal de voz!"
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            user_id = usuario.id if usuario else interaction.user.id
            
            success, message = await self.music_system.play_playlist(
                interaction.guild.id, user_id, nome, 
                interaction.user.voice.channel, embaralhar
            )
            
            if success:
                shuffle_text = " (embaralhada)" if embaralhar else ""
                embed = self._create_success_embed(
                    "▶️ Playlist Iniciada",
                    f"Tocando playlist **{nome}**{shuffle_text}\n{message}"
                )
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_playlists_played_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao tocar playlist: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== COMANDOS DE FILTROS ====================
    
    @app_commands.command(name="filtro", description="🎛️ Aplicar filtro de áudio")
    @app_commands.describe(tipo="Tipo de filtro a aplicar")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Sem filtro", value="none"),
        app_commands.Choice(name="Realce de graves", value="bass_boost"),
        app_commands.Choice(name="Realce de agudos", value="treble_boost"),
        app_commands.Choice(name="Nightcore", value="nightcore"),
        app_commands.Choice(name="Vaporwave", value="vaporwave"),
        app_commands.Choice(name="8D Audio", value="eight_d"),
        app_commands.Choice(name="Karaokê", value="karaoke"),
        app_commands.Choice(name="Eco", value="echo"),
        app_commands.Choice(name="Reverb", value="reverb")
    ])
    async def filter_command(self, interaction: discord.Interaction, tipo: str):
        """Aplicar filtro de áudio"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Converter string para enum
            filter_map = {
                "none": AudioFilter.NONE,
                "bass_boost": AudioFilter.BASS_BOOST,
                "treble_boost": AudioFilter.TREBLE_BOOST,
                "nightcore": AudioFilter.NIGHTCORE,
                "vaporwave": AudioFilter.VAPORWAVE,
                "eight_d": AudioFilter.EIGHT_D,
                "karaoke": AudioFilter.KARAOKE,
                "echo": AudioFilter.ECHO,
                "reverb": AudioFilter.REVERB
            }
            
            audio_filter = filter_map.get(tipo, AudioFilter.NONE)
            
            success, message = await self.music_system.apply_audio_filter(
                interaction.guild.id, audio_filter
            )
            
            if success:
                filter_desc = get_audio_filter_description(audio_filter)
                embed = self._create_success_embed(
                    "🎛️ Filtro Aplicado",
                    f"Filtro **{filter_desc}** aplicado com sucesso!"
                )
            else:
                embed = self._create_error_embed("❌ Erro", message)
            
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment(f'music_filter_{tipo}_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao aplicar filtro: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== COMANDOS DE ESTATÍSTICAS ====================
    
    @app_commands.command(name="stats_musica", description="📊 Ver estatísticas de música")
    @app_commands.describe(usuario="Ver estatísticas de outro usuário")
    async def music_stats_command(self, interaction: discord.Interaction, 
                                usuario: Optional[discord.User] = None):
        """Ver estatísticas de música"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            target_user = usuario or interaction.user
            stats = self.music_system.analyze_listening_patterns(target_user.id)
            
            embed = self._create_stats_embed(target_user, stats)
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_stats_views_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao obter estatísticas: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="stats_servidor", description="🌐 Ver estatísticas globais do servidor")
    async def server_stats_command(self, interaction: discord.Interaction):
        """Ver estatísticas globais"""
        await interaction.response.defer()
        
        try:
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            stats = self.music_system.get_global_stats()
            health = await self.music_system.health_check()
            
            embed = self._create_global_stats_embed(stats, health)
            await interaction.followup.send(embed=embed)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('music_global_stats_views_total')
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao obter estatísticas globais: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== COMANDOS ADMINISTRATIVOS ====================
    
    @app_commands.command(name="admin_musica", description="⚙️ Comandos administrativos de música")
    @app_commands.describe(
        acao="Ação a executar",
        parametro="Parâmetro adicional (se necessário)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Verificar saúde do sistema", value="health"),
        app_commands.Choice(name="Limpar cache", value="clear_cache"),
        app_commands.Choice(name="Reiniciar player", value="restart_player"),
        app_commands.Choice(name="Exportar dados de usuário", value="export_user"),
        app_commands.Choice(name="Deletar dados de usuário", value="delete_user")
    ])
    async def admin_music_command(self, interaction: discord.Interaction, 
                                acao: str, parametro: Optional[str] = None):
        """Comandos administrativos"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.administrator:
                embed = self._create_error_embed(
                    "❌ Sem Permissão",
                    "Apenas administradores podem usar comandos administrativos."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if not self.music_system:
                embed = self._create_error_embed(
                    "❌ Sistema Indisponível",
                    "Sistema de música não está disponível."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if acao == "health":
                health = await self.music_system.health_check()
                embed = self._create_health_embed(health)
                await interaction.followup.send(embed=embed, ephemeral=True)
            
            elif acao == "clear_cache":
                if self.cache:
                    await self.cache.clear()
                    embed = self._create_success_embed(
                        "🧹 Cache Limpo",
                        "Cache do sistema de música foi limpo com sucesso."
                    )
                else:
                    embed = self._create_info_embed(
                        "ℹ️ Cache Indisponível",
                        "Sistema de cache não está disponível."
                    )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
            elif acao == "restart_player":
                success, message = await self.music_system.restart_player(interaction.guild.id)
                if success:
                    embed = self._create_success_embed("🔄 Player Reiniciado", message)
                else:
                    embed = self._create_error_embed("❌ Erro", message)
                await interaction.followup.send(embed=embed, ephemeral=True)
            
            elif acao in ["export_user", "delete_user"]:
                if not parametro:
                    embed = self._create_error_embed(
                        "❌ Parâmetro Necessário",
                        "Forneça o ID do usuário como parâmetro."
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                try:
                    user_id = int(parametro)
                except ValueError:
                    embed = self._create_error_embed(
                        "❌ ID Inválido",
                        "O ID do usuário deve ser um número."
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                if acao == "export_user":
                    user_data = await self.music_system.export_user_data(user_id)
                    # Aqui você poderia salvar em arquivo e enviar
                    embed = self._create_success_embed(
                        "📤 Dados Exportados",
                        f"Dados do usuário {user_id} exportados com sucesso.\n"
                        f"Total de playlists: {len(user_data['playlists'])}\n"
                        f"Total de favoritos: {len(user_data['favorites'])}"
                    )
                else:  # delete_user
                    success, message = await self.music_system.delete_user_data(user_id)
                    if success:
                        embed = self._create_success_embed("🗑️ Dados Deletados", message)
                    else:
                        embed = self._create_error_embed("❌ Erro", message)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro no comando admin: {e}")
            
            embed = self._create_error_embed(
                "❌ Erro Interno",
                "Ocorreu um erro ao processar sua solicitação."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _create_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        """Criar embed padronizado"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Sistema de Música Modernizado")
        return embed
    
    def _create_success_embed(self, title: str, description: str) -> discord.Embed:
        """Criar embed de sucesso"""
        return self._create_embed(title, description, discord.Color.green())
    
    def _create_error_embed(self, title: str, description: str) -> discord.Embed:
        """Criar embed de erro"""
        return self._create_embed(title, description, discord.Color.red())
    
    def _create_info_embed(self, title: str, description: str) -> discord.Embed:
        """Criar embed informativo"""
        return self._create_embed(title, description, discord.Color.blue())
    
    def _create_now_playing_embed(self, song: Song, player) -> discord.Embed:
        """Criar embed da música atual"""
        embed = discord.Embed(
            title="🎵 Tocando Agora",
            description=f"**{song.title}**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if hasattr(song, 'thumbnail') and song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        embed.add_field(
            name="⏱️ Duração",
            value=self.music_system.format_duration(song.duration),
            inline=True
        )
        
        embed.add_field(
            name="👤 Solicitado por",
            value=song.requester.mention if hasattr(song, 'requester') else "Desconhecido",
            inline=True
        )
        
        embed.add_field(
            name="🔊 Volume",
            value=f"{int(player.volume * 100)}%",
            inline=True
        )
        
        if hasattr(song, 'genre'):
            embed.add_field(
                name="🎭 Gênero",
                value=song.genre.value.title(),
                inline=True
            )
        
        if len(player.queue.queue) > 0:
            embed.add_field(
                name="📋 Próxima",
                value=player.queue.queue[0].title[:50] + ("..." if len(player.queue.queue[0].title) > 50 else ""),
                inline=True
            )
        
        embed.add_field(
            name="📊 Fila",
            value=f"{len(player.queue.queue)} música(s)",
            inline=True
        )
        
        embed.set_footer(text="Sistema de Música Modernizado")
        return embed
    
    def _create_queue_embed(self, player, queue_info: Dict[str, Any], page: int = 1) -> discord.Embed:
        """Criar embed da fila"""
        songs_per_page = 10
        total_pages = max(1, (len(queue_info['queue']) + songs_per_page - 1) // songs_per_page)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * songs_per_page
        end_idx = start_idx + songs_per_page
        
        embed = discord.Embed(
            title="📋 Fila de Música",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Música atual
        if player.current_song:
            embed.add_field(
                name="🎵 Tocando Agora",
                value=f"**{player.current_song.title}**\n"
                      f"⏱️ {self.music_system.format_duration(player.current_song.duration)}",
                inline=False
            )
        
        # Fila
        if queue_info['queue']:
            queue_text = ""
            for i, song in enumerate(queue_info['queue'][start_idx:end_idx], start_idx + 1):
                duration = self.music_system.format_duration(song.duration)
                queue_text += f"`{i}.` **{song.title[:40]}{'...' if len(song.title) > 40 else ''}** `({duration})`\n"
            
            embed.add_field(
                name=f"📝 Próximas Músicas (Página {page}/{total_pages})",
                value=queue_text or "Nenhuma música na fila",
                inline=False
            )
        
        # Informações adicionais
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Total:** {len(queue_info['queue'])} música(s)\n"
                  f"**Duração:** {self.music_system.format_queue_duration(queue_info['total_duration'])}\n"
                  f"**Modo:** {queue_info['mode'].value.title()}",
            inline=True
        )
        
        embed.add_field(
            name="🎛️ Controles",
            value=f"**Volume:** {int(player.volume * 100)}%\n"
                  f"**Loop:** {'✅' if player.loop_mode else '❌'}\n"
                  f"**Auto-play:** {'✅' if player.auto_play else '❌'}",
            inline=True
        )
        
        embed.set_footer(text=f"Sistema de Música Modernizado • Página {page}/{total_pages}")
        return embed
    
    def _create_stats_embed(self, user: discord.User, stats: Dict[str, Any]) -> discord.Embed:
        """Criar embed de estatísticas"""
        embed = discord.Embed(
            title=f"📊 Estatísticas de {user.display_name}",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(
            name="🎵 Músicas",
            value=f"**Total:** {stats['total_songs_requested']}\n"
                  f"**Duração média:** {self.music_system.format_duration(int(stats['average_song_duration']))}\n"
                  f"**Taxa de skip:** {stats['skip_rate']:.1%}",
            inline=True
        )
        
        embed.add_field(
            name="📋 Coleções",
            value=f"**Playlists:** {stats['playlist_count']}\n"
                  f"**Favoritos:** {stats['favorite_count']}",
            inline=True
        )
        
        # Gêneros favoritos
        if stats['favorite_genres']:
            genres_text = "\n".join([f"**{genre.title()}:** {count}" 
                                   for genre, count in list(stats['favorite_genres'].items())[:5]])
            embed.add_field(
                name="🎭 Gêneros Favoritos",
                value=genres_text,
                inline=False
            )
        
        # Horários mais ativos
        if stats['most_active_hours']:
            hours_text = "\n".join([f"**{hour:02d}:00:** {count} música(s)" 
                                  for hour, count in stats['most_active_hours'].items()])
            embed.add_field(
                name="⏰ Horários Mais Ativos",
                value=hours_text,
                inline=False
            )
        
        embed.set_footer(text="Sistema de Música Modernizado")
        return embed
    
    def _create_global_stats_embed(self, stats: Dict[str, Any], health: Dict[str, Any]) -> discord.Embed:
        """Criar embed de estatísticas globais"""
        embed = discord.Embed(
            title="🌐 Estatísticas Globais do Sistema",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        # Status do sistema
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'error': '💥'
        }.get(health['status'], '❓')
        
        embed.add_field(
            name="🏥 Status do Sistema",
            value=f"{status_emoji} **{health['status'].title()}**",
            inline=True
        )
        
        embed.add_field(
            name="🎵 Players",
            value=f"**Total:** {stats['total_players']}\n"
                  f"**Ativos:** {stats['active_players']}\n"
                  f"**Fila média:** {stats['average_queue_length']:.1f}",
            inline=True
        )
        
        embed.add_field(
            name="👥 Usuários",
            value=f"**Total:** {stats['total_users']}\n"
                  f"**Playlists:** {stats['total_playlists']}\n"
                  f"**Favoritos:** {stats['total_favorites']}",
            inline=True
        )
        
        # Gêneros mais populares
        if stats['most_popular_genres']:
            genres_text = "\n".join([f"**{genre.title()}:** {count}" 
                                   for genre, count in list(stats['most_popular_genres'].items())[:5]])
            embed.add_field(
                name="🎭 Gêneros Mais Populares",
                value=genres_text,
                inline=False
            )
        
        embed.set_footer(text="Sistema de Música Modernizado")
        return embed
    
    def _create_health_embed(self, health: Dict[str, Any]) -> discord.Embed:
        """Criar embed de saúde do sistema"""
        status_colors = {
            'healthy': discord.Color.green(),
            'degraded': discord.Color.orange(),
            'unhealthy': discord.Color.red(),
            'error': discord.Color.dark_red()
        }
        
        embed = discord.Embed(
            title="🏥 Saúde do Sistema de Música",
            color=status_colors.get(health['status'], discord.Color.grey()),
            timestamp=datetime.now()
        )
        
        # Status geral
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'error': '💥'
        }.get(health['status'], '❓')
        
        embed.add_field(
            name="📊 Status Geral",
            value=f"{status_emoji} **{health['status'].title()}**",
            inline=True
        )
        
        # Componentes
        components_text = ""
        for component, status in health['components'].items():
            emoji = '✅' if status == 'available' or status == 'healthy' else '❌'
            components_text += f"{emoji} **{component.title()}:** {status}\n"
        
        embed.add_field(
            name="🔧 Componentes",
            value=components_text,
            inline=True
        )
        
        # Métricas
        if health['metrics']:
            metrics_text = "\n".join([f"**{key.replace('_', ' ').title()}:** {value}" 
                                    for key, value in health['metrics'].items()])
            embed.add_field(
                name="📈 Métricas",
                value=metrics_text,
                inline=False
            )
        
        # Issues
        if health['issues']:
            issues_text = "\n".join([f"• {issue}" for issue in health['issues'][:5]])
            embed.add_field(
                name="⚠️ Problemas Detectados",
                value=issues_text,
                inline=False
            )
        
        embed.set_footer(text=f"Verificação realizada em {health['timestamp']}")
        return embed

async def setup(bot):
    """Setup function para carregar o cog"""
    await bot.add_cog(ModernMusicCommands(bot))