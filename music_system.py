#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Música para Discord
Permite reproduzir música em canais de voz com comandos avançados

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import asyncio
import logging
import yt_dlp
import os
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger('HawkBot.MusicSystem')

class Song:
    """Classe para representar uma música"""
    
    def __init__(self, title: str, url: str, duration: int, requester: discord.Member, thumbnail: str = None):
        self.title = title
        self.url = url
        self.duration = duration
        self.requester = requester
        self.thumbnail = thumbnail
        self.requested_at = datetime.now()
    
    def __str__(self):
        return f"{self.title} - {self.format_duration()}"
    
    def format_duration(self) -> str:
        """Formatar duração em MM:SS"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"

class MusicPlayer:
    """Player de música para um servidor específico"""
    
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue = deque()
        self.current_song: Optional[Song] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.is_playing = False
        self.is_paused = False
        self.loop_mode = False  # False = off, True = current song
        self.volume = 0.5
        self.skip_votes = set()
        self.last_activity = datetime.now()
        self.song_start_time: Optional[datetime] = None
        self.music_history = deque(maxlen=50)  # Histórico das últimas 50 músicas
        self.current_filter = "none"  # Filtro de áudio atual
    
    def add_song(self, song: Song):
        """Adicionar música à fila"""
        self.queue.append(song)
        self.last_activity = datetime.now()
    
    def get_next_song(self) -> Optional[Song]:
        """Obter próxima música da fila"""
        if self.loop_mode and self.current_song:
            return self.current_song
        
        if self.queue:
            return self.queue.popleft()
        
        return None
    
    def clear_queue(self):
        """Limpar fila de músicas"""
        self.queue.clear()
        self.skip_votes.clear()
    
    def shuffle_queue(self):
        """Embaralhar fila de músicas"""
        import random
        queue_list = list(self.queue)
        random.shuffle(queue_list)
        self.queue = deque(queue_list)

class MusicSystem:
    """Sistema principal de música"""
    
    def __init__(self, bot):
        self.bot = bot
        self.players: Dict[int, MusicPlayer] = {}
        self.user_favorites: Dict[int, List[Dict[str, Any]]] = {}  # user_id -> list of favorites
        self.user_playlists: Dict[int, Dict[str, Dict[str, Any]]] = {}  # user_id -> {playlist_name -> playlist_data}
        self.ytdl_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_options)
        self._cleanup_task = None
        
        logger.info("Sistema de Música inicializado")
    
    async def setup_hook(self):
        """Configurar tasks após o bot estar pronto"""
        if self._cleanup_task is None:
            self._cleanup_task = self.bot.loop.create_task(self._cleanup_inactive_players())
    
    def get_player(self, guild_id: int) -> MusicPlayer:
        """Obter ou criar player para um servidor"""
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer(guild_id)
        return self.players[guild_id]
    
    async def search_song(self, query: str) -> Optional[Dict[str, Any]]:
        """Buscar música no YouTube"""
        try:
            # Verificar se é URL ou termo de busca
            if not urlparse(query).scheme:
                query = f"ytsearch:{query}"
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))
            
            if 'entries' in data:
                # Resultado de busca
                if data['entries']:
                    return data['entries'][0]
            else:
                # URL direta
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar música '{query}': {e}")
            return None
    
    async def play_song(self, guild_id: int, voice_channel: discord.VoiceChannel, 
                       query: str, requester: discord.Member) -> tuple[bool, str]:
        """Tocar música ou adicionar à fila"""
        try:
            player = self.get_player(guild_id)
            
            # Buscar música
            song_data = await self.search_song(query)
            if not song_data:
                return False, "Música não encontrada"
            
            # Criar objeto Song
            song = Song(
                title=song_data.get('title', 'Título desconhecido'),
                url=song_data.get('webpage_url', song_data.get('url', '')),
                duration=song_data.get('duration', 0),
                requester=requester
            )
            
            # Conectar ao canal de voz se necessário
            if not player.voice_client:
                player.voice_client = await voice_channel.connect()
            elif player.voice_client.channel != voice_channel:
                await player.voice_client.move_to(voice_channel)
            
            # Adicionar à fila
            player.queue.append(song)
            
            # Se não está tocando, começar a tocar
            if not player.is_playing:
                await self._play_next(guild_id)
                return True, f"Tocando agora: **{song.title}**"
            else:
                return True, f"Adicionado à fila: **{song.title}** (posição {len(player.queue)})"
                
        except Exception as e:
            logger.error(f"Erro ao tocar música: {e}")
            return False, f"Erro ao tocar música: {str(e)}"
    
    def add_skip_vote(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Adiciona um voto para pular a música atual"""
        player = self.get_player(guild_id)
        
        if not player.current_song:
            return {"error": "Nenhuma música tocando"}
        
        # Verificar se já votou
        if user_id in player.skip_votes:
            return {"already_voted": True}
        
        # Adicionar voto
        player.skip_votes.add(user_id)
        
        # Calcular votos necessários (50% dos usuários no canal de voz)
        if player.voice_client and player.voice_client.channel:
            members_in_voice = len([m for m in player.voice_client.channel.members if not m.bot])
            required_votes = max(1, members_in_voice // 2)  # Pelo menos 1 voto, 50% dos membros
        else:
            required_votes = 1
        
        current_votes = len(player.skip_votes)
        should_skip = current_votes >= required_votes
        
        if should_skip:
            # Limpar votos para a próxima música
            player.skip_votes.clear()
        
        return {
            "already_voted": False,
            "should_skip": should_skip,
            "votes": current_votes,
            "required": required_votes
        }
    
    async def play_song(self, guild_id: int, voice_channel, query: str, requester) -> Tuple[bool, str]:
        """Toca uma música"""
        try:
            player = self.get_player(guild_id)
            
            # Buscar música
            song_data = await self.search_song(query)
            if not song_data:
                return False, "❌ Não foi possível encontrar a música solicitada."
            
            # Criar objeto Song
            song = Song(
                title=song_data.get('title', 'Título desconhecido'),
                url=song_data.get('url', song_data.get('webpage_url', '')),
                duration=song_data.get('duration', 0) or 0,
                requester=requester,
                thumbnail=song_data.get('thumbnail')
            )
            
            # Conectar ao canal de voz se necessário
            if not player.voice_client or not player.voice_client.is_connected():
                try:
                    player.voice_client = await voice_channel.connect()
                except Exception as e:
                    return False, f"❌ Erro ao conectar ao canal de voz: {e}"
            
            # Adicionar à fila
            player.add_song(song)
            
            # Se não está tocando, iniciar reprodução
            if not player.is_playing:
                await self._play_next(guild_id)
                return True, f"🎵 **Tocando agora:** {song.title}"
            else:
                return True, f"📝 **Adicionado à fila:** {song.title} (Posição: {len(player.queue)})"
            
        except Exception as e:
            logger.error(f"Erro ao tocar música: {e}")
            return False, f"❌ Erro interno: {e}"
    
    async def _play_next(self, guild_id: int):
        """Tocar próxima música da fila"""
        try:
            player = self.get_player(guild_id)
            
            if not player.voice_client or not player.voice_client.is_connected():
                return
            
            # Obter próxima música
            next_song = player.get_next_song()
            if not next_song:
                player.is_playing = False
                player.current_song = None
                return
            
            player.current_song = next_song
            player.is_playing = True
            player.is_paused = False
            player.skip_votes.clear()
            player.song_start_time = datetime.now()  # Marcar início da música
            player.skip_votes.clear()  # Limpar votos da música anterior
            
            # Obter URL de streaming
            try:
                stream_data = await self.search_song(next_song.url)
                if stream_data and 'url' in stream_data:
                    stream_url = stream_data['url']
                else:
                    stream_url = next_song.url
            except:
                stream_url = next_song.url
            
            # Criar source de áudio
            source = discord.FFmpegPCMAudio(stream_url, **self.ffmpeg_options)
            source = discord.PCMVolumeTransformer(source, volume=player.volume)
            
            # Tocar música
            player.voice_client.play(source, after=lambda e: self._song_finished(guild_id, e))
            
            logger.info(f"Tocando: {next_song.title} no servidor {guild_id}")
            
        except Exception as e:
            logger.error(f"Erro ao tocar próxima música: {e}")
            player.is_playing = False
    
    def _song_finished(self, guild_id: int, error):
        """Callback quando música termina"""
        if error:
            logger.error(f"Erro na reprodução: {error}")
        
        # Adicionar música atual ao histórico antes de prosseguir
        player = self.get_player(guild_id)
        if player.current_song and not player.loop_mode:
            player.music_history.append({
                'song': player.current_song,
                'played_at': datetime.now()
            })
        
        # Agendar próxima música
        coro = self._play_next(guild_id)
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            fut.result()
        except Exception as e:
            logger.error(f"Erro ao agendar próxima música: {e}")
    
    async def pause_resume(self, guild_id: int) -> tuple[bool, str]:
        """Pausar ou retomar reprodução"""
        player = self.get_player(guild_id)
        
        if not player.voice_client or not player.is_playing:
            return False, "❌ Nenhuma música está tocando."
        
        if player.is_paused:
            player.voice_client.resume()
            player.is_paused = False
            return True, "▶️ Música retomada."
        else:
            player.voice_client.pause()
            player.is_paused = True
            return True, "⏸️ Música pausada."
    
    async def skip_song(self, guild_id: int, user_id: int, force: bool = False) -> tuple[bool, str]:
        """Pular música atual"""
        player = self.get_player(guild_id)
        
        if not player.voice_client or not player.is_playing:
            return False, "❌ Nenhuma música está tocando."
        
        # Verificar se é o solicitante da música ou admin
        if force or (player.current_song and player.current_song.requester.id == user_id):
            player.voice_client.stop()
            return True, "⏭️ Música pulada."
        
        # Sistema de votação
        player.skip_votes.add(user_id)
        required_votes = max(2, len(player.voice_client.channel.members) // 2)
        
        if len(player.skip_votes) >= required_votes:
            player.voice_client.stop()
            return True, f"⏭️ Música pulada por votação ({len(player.skip_votes)}/{required_votes})."
        else:
            remaining = required_votes - len(player.skip_votes)
            return True, f"🗳️ Voto registrado. Faltam {remaining} votos para pular."
    
    async def stop_music(self, guild_id: int) -> tuple[bool, str]:
        """Parar música e limpar fila"""
        player = self.get_player(guild_id)
        
        if player.voice_client:
            player.clear_queue()
            player.voice_client.stop()
            player.is_playing = False
            player.current_song = None
            return True, "⏹️ Música parada e fila limpa."
        
        return False, "❌ Não há música tocando."
    
    async def disconnect(self, guild_id: int) -> tuple[bool, str]:
        """Desconectar do canal de voz"""
        player = self.get_player(guild_id)
        
        if player.voice_client:
            await player.voice_client.disconnect()
            player.voice_client = None
            player.clear_queue()
            player.is_playing = False
            player.current_song = None
            return True, "👋 Desconectado do canal de voz."
        
        return False, "❌ Não estou conectado a nenhum canal de voz."
    
    def get_queue_info(self, guild_id: int) -> Dict[str, Any]:
        """Obter informações da fila"""
        player = self.get_player(guild_id)
        
        return {
            'current_song': player.current_song,
            'queue': list(player.queue),
            'is_playing': player.is_playing,
            'is_paused': player.is_paused,
            'loop_mode': player.loop_mode,
            'volume': player.volume,
            'queue_length': len(player.queue)
        }
    
    def get_current_song_info(self, guild_id: int) -> Dict[str, Any]:
        """Obter informações detalhadas da música atual com progresso"""
        player = self.get_player(guild_id)
        
        # Calcular progresso da música atual
        progress = 0
        if player.current_song and player.voice_client and player.voice_client.source:
            # Estimar progresso baseado no tempo desde que começou a tocar
            if hasattr(player, 'song_start_time'):
                elapsed = (datetime.now() - player.song_start_time).total_seconds()
                progress = min(elapsed, player.current_song.duration)
        
        return {
            'current_song': player.current_song,
            'progress': progress,
            'queue': list(player.queue),
            'queue_length': len(player.queue),
            'is_playing': player.is_playing,
            'is_paused': player.is_paused,
            'loop_mode': player.loop_mode,
            'volume': player.volume
        }
    
    def get_music_history(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Obter histórico de músicas tocadas"""
        player = self.get_player(guild_id)
        
        # Converter deque para lista e limitar
        history_list = list(player.music_history)[-limit:]
        history_list.reverse()  # Mais recente primeiro
        
        return history_list
    
    async def set_volume(self, guild_id: int, volume: int) -> tuple[bool, str]:
        """Definir volume (0-100)"""
        if not 0 <= volume <= 100:
            return False, "❌ Volume deve estar entre 0 e 100."
        
        player = self.get_player(guild_id)
        player.volume = volume / 100.0
        
        if player.voice_client and player.voice_client.source:
            player.voice_client.source.volume = player.volume
        
        return True, f"🔊 Volume definido para {volume}%."
    
    async def toggle_loop(self, guild_id: int) -> tuple[bool, str]:
        """Alternar modo de repetição"""
        player = self.get_player(guild_id)
        player.loop_mode = not player.loop_mode
        
        if player.loop_mode:
            return True, "🔂 Modo de repetição ativado."
        else:
            return True, "➡️ Modo de repetição desativado."
    
    async def shuffle_queue(self, guild_id: int) -> tuple[bool, str]:
        """Embaralhar fila"""
        player = self.get_player(guild_id)
        
        if len(player.queue) < 2:
            return False, "❌ Fila deve ter pelo menos 2 músicas para embaralhar."
        
        player.shuffle_queue()
        return True, f"🔀 Fila embaralhada ({len(player.queue)} músicas)."
    
    async def _cleanup_inactive_players(self):
        """Limpar players inativos automaticamente"""
        while True:
            try:
                await asyncio.sleep(300)  # Verificar a cada 5 minutos
                
                current_time = datetime.now()
                inactive_guilds = []
                
                for guild_id, player in self.players.items():
                    # Desconectar se inativo por mais de 10 minutos
                    if (current_time - player.last_activity).total_seconds() > 600:
                        if player.voice_client and not player.is_playing:
                            await self.disconnect(guild_id)
                            inactive_guilds.append(guild_id)
                
                # Remover players inativos
                for guild_id in inactive_guilds:
                    del self.players[guild_id]
                    logger.info(f"Player removido por inatividade: {guild_id}")
                
            except Exception as e:
                logger.error(f"Erro na limpeza automática: {e}")
    
    def get_user_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """Obter lista de favoritos do usuário"""
        favorites_data = self.user_favorites.get(user_id, [])
        
        # Converter dados para objetos Song
        favorites_list = []
        for fav_data in favorites_data:
            # Criar um objeto Song temporário (sem requester real)
            temp_song = Song(
                title=fav_data['title'],
                url=fav_data['url'],
                duration=fav_data['duration'],
                requester=None,  # Será definido quando tocar
                thumbnail=fav_data.get('thumbnail')
            )
            
            favorites_list.append({
                'song': temp_song,
                'added_at': fav_data['added_at']
            })
        
        return favorites_list
    
    async def add_to_favorites(self, user_id: int, song: Song) -> tuple[bool, str]:
        """Adicionar música aos favoritos do usuário"""
        if user_id not in self.user_favorites:
            self.user_favorites[user_id] = []
        
        # Verificar se já está nos favoritos
        for fav in self.user_favorites[user_id]:
            if fav['title'] == song.title and fav['url'] == song.url:
                return False, "❌ Esta música já está nos seus favoritos."
        
        # Limitar a 50 favoritos por usuário
        if len(self.user_favorites[user_id]) >= 50:
            return False, "❌ Você atingiu o limite máximo de 50 favoritos."
        
        favorite_data = {
            'title': song.title,
            'url': song.url,
            'duration': song.duration,
            'thumbnail': song.thumbnail,
            'added_at': datetime.now()
        }
        
        self.user_favorites[user_id].append(favorite_data)
        return True, f"⭐ **{song.title}** foi adicionada aos seus favoritos!"
    
    async def remove_from_favorites(self, user_id: int, index: int) -> tuple[bool, str]:
        """Remover música dos favoritos por índice (0-based)"""
        if user_id not in self.user_favorites or not self.user_favorites[user_id]:
            return False, "❌ Você não possui favoritos."
        
        favorites = self.user_favorites[user_id]
        
        if not 0 <= index < len(favorites):
            return False, f"❌ Índice inválido. Use um número entre 1 e {len(favorites)}."
        
        removed_song = favorites.pop(index)
        return True, f"🗑️ **{removed_song['title']}** foi removida dos seus favoritos."
    
    # Playlist methods
    def get_user_playlists(self, user_id: int) -> List[str]:
        """Retorna lista de nomes das playlists do usuário"""
        if user_id not in self.user_playlists:
            return []
        return list(self.user_playlists[user_id].keys())
    
    def create_playlist(self, user_id: int, name: str, is_public: bool = False) -> bool:
        """Cria uma nova playlist"""
        if user_id not in self.user_playlists:
            self.user_playlists[user_id] = {}
        
        if name in self.user_playlists[user_id]:
            return False  # Playlist já existe
        
        if len(self.user_playlists[user_id]) >= 20:  # Limite de 20 playlists por usuário
            return False
        
        self.user_playlists[user_id][name] = {
            'songs': [],
            'created_at': datetime.now().isoformat(),
            'is_public': is_public,
            'description': ''
        }
        return True
    
    def delete_playlist(self, user_id: int, name: str) -> bool:
        """Deleta uma playlist"""
        if user_id not in self.user_playlists or name not in self.user_playlists[user_id]:
            return False
        
        del self.user_playlists[user_id][name]
        return True
    
    def get_playlist(self, user_id: int, name: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de uma playlist específica"""
        if user_id not in self.user_playlists or name not in self.user_playlists[user_id]:
            return None
        
        playlist_data = self.user_playlists[user_id][name].copy()
        # Converter dados das músicas em objetos Song
        songs = []
        for song_data in playlist_data['songs']:
            song = Song(
                title=song_data['title'],
                url=song_data['url'],
                duration=song_data['duration'],
                requester=song_data['requester'],
                thumbnail=song_data.get('thumbnail', '')
            )
            songs.append({
                'song': song,
                'added_at': song_data['added_at']
            })
        playlist_data['songs'] = songs
        return playlist_data
    
    def add_to_playlist(self, user_id: int, playlist_name: str, song: Song) -> bool:
        """Adiciona uma música à playlist"""
        if user_id not in self.user_playlists or playlist_name not in self.user_playlists[user_id]:
            return False
        
        playlist = self.user_playlists[user_id][playlist_name]
        
        # Verificar se a música já existe na playlist
        for existing_song in playlist['songs']:
            if existing_song['url'] == song.url:
                return False  # Música já existe
        
        if len(playlist['songs']) >= 100:  # Limite de 100 músicas por playlist
            return False
        
        playlist['songs'].append({
            'title': song.title,
            'url': song.url,
            'duration': song.duration,
            'requester': song.requester,
            'thumbnail': song.thumbnail,
            'added_at': datetime.now().isoformat()
        })
        return True
    
    def remove_from_playlist(self, user_id: int, playlist_name: str, index: int) -> bool:
        """Remove uma música da playlist"""
        if user_id not in self.user_playlists or playlist_name not in self.user_playlists[user_id]:
            return False
        
        playlist = self.user_playlists[user_id][playlist_name]
        
        if index < 0 or index >= len(playlist['songs']):
            return False
        
        playlist['songs'].pop(index)
        return True
    
    def get_public_playlists(self) -> List[Dict[str, Any]]:
        """Retorna todas as playlists públicas"""
        public_playlists = []
        
        for user_id, playlists in self.user_playlists.items():
            for playlist_name, playlist_data in playlists.items():
                if playlist_data.get('is_public', False):
                    public_playlists.append({
                        'owner_id': user_id,
                        'name': playlist_name,
                        'song_count': len(playlist_data['songs']),
                        'created_at': playlist_data['created_at']
                    })
        
        return public_playlists
    
    async def play_playlist(self, guild_id: int, voice_channel, playlist_data: Dict[str, Any], requester) -> int:
        """Toca uma playlist inteira, retorna o número de músicas adicionadas"""
        player = self.get_player(guild_id)
        songs_added = 0
        
        for song_entry in playlist_data['songs']:
            song = song_entry['song']
            song.requester = requester  # Atualizar o solicitante
            
            if not player.voice_client:
                try:
                    player.voice_client = await voice_channel.connect()
                except Exception:
                    continue
            
            player.queue.append(song)
            songs_added += 1
        
        if not player.is_playing and player.queue:
            await self._play_next(player)
        
        return songs_added
    
    async def apply_audio_filter(self, guild_id: int, filter_type: str) -> bool:
        """Aplica filtros de áudio à música atual"""
        player = self.get_player(guild_id)
        
        if not player.voice_client or not player.current_song:
            return False
        
        # Definir filtros FFmpeg
        filters = {
            "none": "",
            "bass": "bass=g=10",
            "treble": "treble=g=5",
            "nightcore": "asetrate=48000*1.25,aresample=48000,bass=g=5",
            "vaporwave": "asetrate=48000*0.8,aresample=48000,atempo=1.1",
            "8d": "apulsator=hz=0.125",
            "karaoke": "pan=mono|c0=0.5*c0+-0.5*c1"
        }
        
        try:
            # Parar música atual
            if player.voice_client.is_playing():
                player.voice_client.stop()
            
            # Aplicar filtro e tocar novamente
            player.current_filter = filter_type
            
            # Recriar source com filtro
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': f'-vn {f"-af {filters[filter_type]}" if filters[filter_type] else ""}'
            }
            
            source = discord.FFmpegPCMAudio(
                player.current_song.url,
                **ffmpeg_options
            )
            
            player.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self._song_finished(player), self.bot.loop
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Erro ao aplicar filtro: {e}")
            return False