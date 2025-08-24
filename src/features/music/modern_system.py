#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Modernizado de Música - Hawk Bot
Sistema avançado de reprodução de música com queue inteligente,
recomendações automáticas e integração com sistemas core modernos.

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import asyncio
import logging
import yt_dlp
import discord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import math
from urllib.parse import urlparse

# Importações dos sistemas core modernos
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f

try:
    from ..core.smart_cache import SmartCache
    from ..core.secure_logger import SecureLogger
    from ..core.typed_config import TypedConfig
    from ..core.metrics_system import MetricsCollector
    from ..core.data_validator import DataValidator
    from ..core.event_system import EventSystem
    from ..core.rate_limiter import RateLimiter
except ImportError:
    # Fallback para compatibilidade
    SmartCache = None
    SecureLogger = None
    TypedConfig = None
    MetricsCollector = None
    DataValidator = None
    EventSystem = None
    RateLimiter = None

logger = logging.getLogger('HawkBot.ModernMusicSystem')

# ==================== ENUMS E CONSTANTES ====================

class PlaybackState(Enum):
    """Estados de reprodução"""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"

class QueueMode(Enum):
    """Modos de fila"""
    NORMAL = "normal"
    SHUFFLE = "shuffle"
    REPEAT_ONE = "repeat_one"
    REPEAT_ALL = "repeat_all"
    SMART = "smart"  # Queue inteligente com recomendações

class AudioFilter(Enum):
    """Filtros de áudio disponíveis"""
    NONE = "none"
    BASS_BOOST = "bass_boost"
    TREBLE_BOOST = "treble_boost"
    NIGHTCORE = "nightcore"
    VAPORWAVE = "vaporwave"
    EIGHT_D = "8d"
    KARAOKE = "karaoke"
    ECHO = "echo"
    REVERB = "reverb"

class MusicGenre(Enum):
    """Gêneros musicais para análise"""
    UNKNOWN = "unknown"
    POP = "pop"
    ROCK = "rock"
    ELECTRONIC = "electronic"
    HIP_HOP = "hip_hop"
    CLASSICAL = "classical"
    JAZZ = "jazz"
    COUNTRY = "country"
    REGGAE = "reggae"
    METAL = "metal"
    INDIE = "indie"

# ==================== MODELOS DE DADOS ====================

if PYDANTIC_AVAILABLE:
    class SongModel(BaseModel):
        """Modelo Pydantic para música"""
        title: str = Field(..., min_length=1, max_length=200)
        url: str = Field(..., min_length=1)
        duration: int = Field(default=0, ge=0)
        requester_id: int = Field(..., gt=0)
        thumbnail: Optional[str] = None
        genre: MusicGenre = Field(default=MusicGenre.UNKNOWN)
        popularity_score: float = Field(default=0.0, ge=0.0, le=1.0)
        requested_at: datetime = Field(default_factory=datetime.now)
        play_count: int = Field(default=0, ge=0)
        skip_count: int = Field(default=0, ge=0)
        
        @validator('url')
        def validate_url(cls, v):
            if not (v.startswith('http') or v.startswith('ytsearch:')):
                raise ValueError('URL deve ser válida')
            return v
    
    class PlaylistModel(BaseModel):
        """Modelo Pydantic para playlist"""
        name: str = Field(..., min_length=1, max_length=50)
        owner_id: int = Field(..., gt=0)
        songs: List[SongModel] = Field(default_factory=list)
        is_public: bool = Field(default=False)
        description: str = Field(default="", max_length=500)
        created_at: datetime = Field(default_factory=datetime.now)
        last_modified: datetime = Field(default_factory=datetime.now)
        play_count: int = Field(default=0, ge=0)
        
        @validator('songs')
        def validate_songs_limit(cls, v):
            if len(v) > 200:
                raise ValueError('Playlist não pode ter mais de 200 músicas')
            return v
    
    class UserPreferencesModel(BaseModel):
        """Modelo para preferências do usuário"""
        user_id: int = Field(..., gt=0)
        favorite_genres: List[MusicGenre] = Field(default_factory=list)
        preferred_duration_range: Tuple[int, int] = Field(default=(0, 600))  # 0-10 min
        volume_preference: float = Field(default=0.5, ge=0.0, le=1.0)
        auto_queue: bool = Field(default=True)
        explicit_content: bool = Field(default=True)
        last_updated: datetime = Field(default_factory=datetime.now)
else:
    # Fallback sem Pydantic
    class SongModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class PlaylistModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class UserPreferencesModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

# ==================== CLASSES PRINCIPAIS ====================

@dataclass
class Song:
    """Classe para representar uma música com dados avançados"""
    title: str
    url: str
    duration: int
    requester: discord.Member
    thumbnail: Optional[str] = None
    genre: MusicGenre = MusicGenre.UNKNOWN
    popularity_score: float = 0.0
    requested_at: datetime = field(default_factory=datetime.now)
    play_count: int = 0
    skip_count: int = 0
    audio_features: Dict[str, float] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.title} - {self.format_duration()}"
    
    def format_duration(self) -> str:
        """Formatar duração em MM:SS ou HH:MM:SS"""
        if self.duration >= 3600:
            hours = self.duration // 3600
            minutes = (self.duration % 3600) // 60
            seconds = self.duration % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_similarity_score(self, other: 'Song') -> float:
        """Calcular similaridade com outra música"""
        score = 0.0
        
        # Gênero (peso 40%)
        if self.genre == other.genre and self.genre != MusicGenre.UNKNOWN:
            score += 0.4
        
        # Duração similar (peso 20%)
        duration_diff = abs(self.duration - other.duration)
        if duration_diff < 60:  # Menos de 1 minuto de diferença
            score += 0.2 * (1 - duration_diff / 60)
        
        # Popularidade similar (peso 20%)
        popularity_diff = abs(self.popularity_score - other.popularity_score)
        score += 0.2 * (1 - popularity_diff)
        
        # Features de áudio (peso 20%)
        if self.audio_features and other.audio_features:
            feature_similarity = 0.0
            common_features = set(self.audio_features.keys()) & set(other.audio_features.keys())
            
            if common_features:
                for feature in common_features:
                    diff = abs(self.audio_features[feature] - other.audio_features[feature])
                    feature_similarity += 1 - diff
                
                feature_similarity /= len(common_features)
                score += 0.2 * feature_similarity
        
        return min(score, 1.0)

@dataclass
class QueueStats:
    """Estatísticas da fila"""
    total_duration: int = 0
    average_duration: float = 0.0
    genre_distribution: Dict[MusicGenre, int] = field(default_factory=dict)
    most_active_requester: Optional[int] = None
    estimated_finish_time: Optional[datetime] = None

class SmartQueue:
    """Fila inteligente com recomendações automáticas"""
    
    def __init__(self, max_size: int = 500):
        self.queue: deque[Song] = deque(maxlen=max_size)
        self.history: deque[Song] = deque(maxlen=100)
        self.mode: QueueMode = QueueMode.NORMAL
        self.auto_fill: bool = True
        self.recommendation_threshold: int = 3  # Adicionar recomendações quando restam 3 músicas
        
    def add(self, song: Song, position: Optional[int] = None) -> bool:
        """Adicionar música à fila"""
        try:
            if position is None:
                self.queue.append(song)
            else:
                # Inserir em posição específica
                queue_list = list(self.queue)
                queue_list.insert(position, song)
                self.queue = deque(queue_list, maxlen=self.queue.maxlen)
            return True
        except Exception:
            return False
    
    def get_next(self) -> Optional[Song]:
        """Obter próxima música baseada no modo"""
        if not self.queue:
            return None
        
        if self.mode == QueueMode.SHUFFLE:
            # Remover música aleatória
            if len(self.queue) > 1:
                index = random.randint(0, len(self.queue) - 1)
                queue_list = list(self.queue)
                song = queue_list.pop(index)
                self.queue = deque(queue_list, maxlen=self.queue.maxlen)
                return song
        
        return self.queue.popleft()
    
    def get_recommendations(self, user_preferences: Dict[str, Any], count: int = 5) -> List[Song]:
        """Gerar recomendações baseadas no histórico e preferências"""
        if not self.history:
            return []
        
        # Analisar padrões do histórico recente
        recent_songs = list(self.history)[-10:]
        
        # Calcular gêneros mais tocados
        genre_counts = {}
        for song in recent_songs:
            genre_counts[song.genre] = genre_counts.get(song.genre, 0) + 1
        
        # Calcular duração média preferida
        avg_duration = sum(song.duration for song in recent_songs) / len(recent_songs)
        
        # Aqui seria implementada a lógica de recomendação real
        # Por enquanto, retorna lista vazia
        return []
    
    def get_stats(self) -> QueueStats:
        """Obter estatísticas da fila"""
        if not self.queue:
            return QueueStats()
        
        total_duration = sum(song.duration for song in self.queue)
        average_duration = total_duration / len(self.queue)
        
        # Distribuição de gêneros
        genre_dist = {}
        for song in self.queue:
            genre_dist[song.genre] = genre_dist.get(song.genre, 0) + 1
        
        # Solicitante mais ativo
        requester_counts = {}
        for song in self.queue:
            uid = song.requester.id if song.requester else 0
            requester_counts[uid] = requester_counts.get(uid, 0) + 1
        
        most_active = max(requester_counts.items(), key=lambda x: x[1])[0] if requester_counts else None
        
        # Tempo estimado de término
        estimated_finish = datetime.now() + timedelta(seconds=total_duration)
        
        return QueueStats(
            total_duration=total_duration,
            average_duration=average_duration,
            genre_distribution=genre_dist,
            most_active_requester=most_active,
            estimated_finish_time=estimated_finish
        )

class ModernMusicPlayer:
    """Player de música modernizado para um servidor"""
    
    def __init__(self, guild_id: int, cache: Optional[SmartCache] = None):
        self.guild_id = guild_id
        self.cache = cache
        
        # Estado do player
        self.current_song: Optional[Song] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.state: PlaybackState = PlaybackState.IDLE
        self.volume: float = 0.5
        self.current_filter: AudioFilter = AudioFilter.NONE
        
        # Fila inteligente
        self.queue = SmartQueue()
        
        # Controles de reprodução
        self.loop_current: bool = False
        self.loop_queue: bool = False
        self.auto_play: bool = True
        
        # Estatísticas e monitoramento
        self.session_stats = {
            'songs_played': 0,
            'total_playtime': 0,
            'skip_count': 0,
            'session_start': datetime.now()
        }
        
        # Sistema de votação
        self.skip_votes: Set[int] = set()
        self.required_skip_votes: int = 1
        
        # Timestamps
        self.last_activity = datetime.now()
        self.song_start_time: Optional[datetime] = None
        self.pause_start_time: Optional[datetime] = None
        self.total_pause_duration: timedelta = timedelta()
        
        # Configurações avançadas
        self.crossfade_duration: float = 2.0  # segundos
        self.buffer_size: int = 1024 * 1024  # 1MB
        self.max_queue_duration: int = 7200  # 2 horas
        
    async def connect(self, voice_channel: discord.VoiceChannel) -> bool:
        """Conectar ao canal de voz"""
        try:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel != voice_channel:
                    await self.voice_client.move_to(voice_channel)
            else:
                self.voice_client = await voice_channel.connect()
            
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao canal de voz: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Desconectar do canal de voz"""
        try:
            if self.voice_client:
                await self.voice_client.disconnect()
                self.voice_client = None
            
            self.state = PlaybackState.IDLE
            self.current_song = None
            return True
        except Exception as e:
            logger.error(f"Erro ao desconectar: {e}")
            return False
    
    def add_song(self, song: Song, position: Optional[int] = None) -> bool:
        """Adicionar música à fila"""
        # Verificar limite de duração total da fila
        current_duration = sum(s.duration for s in self.queue.queue)
        if current_duration + song.duration > self.max_queue_duration:
            return False
        
        success = self.queue.add(song, position)
        if success:
            self.last_activity = datetime.now()
        
        return success
    
    def get_current_position(self) -> int:
        """Obter posição atual da música em segundos"""
        if not self.song_start_time or self.state != PlaybackState.PLAYING:
            return 0
        
        elapsed = datetime.now() - self.song_start_time - self.total_pause_duration
        return int(elapsed.total_seconds())
    
    def get_remaining_time(self) -> int:
        """Obter tempo restante da música atual"""
        if not self.current_song:
            return 0
        
        position = self.get_current_position()
        return max(0, self.current_song.duration - position)
    
    def calculate_skip_votes_needed(self) -> int:
        """Calcular votos necessários para pular"""
        if not self.voice_client or not self.voice_client.channel:
            return 1
        
        # Contar membros não-bot no canal
        members = [m for m in self.voice_client.channel.members if not m.bot]
        
        # 50% dos membros, mínimo 1, máximo 5
        return max(1, min(5, len(members) // 2))
    
    def add_skip_vote(self, user_id: int) -> Dict[str, Any]:
        """Adicionar voto para pular música"""
        if user_id in self.skip_votes:
            return {'already_voted': True, 'votes': len(self.skip_votes)}
        
        self.skip_votes.add(user_id)
        self.required_skip_votes = self.calculate_skip_votes_needed()
        
        should_skip = len(self.skip_votes) >= self.required_skip_votes
        
        return {
            'already_voted': False,
            'should_skip': should_skip,
            'votes': len(self.skip_votes),
            'required': self.required_skip_votes
        }
    
    def clear_skip_votes(self):
        """Limpar votos de skip"""
        self.skip_votes.clear()
    
    def update_activity(self):
        """Atualizar timestamp de última atividade"""
        self.last_activity = datetime.now()
    
    def is_inactive(self, timeout_minutes: int = 10) -> bool:
        """Verificar se o player está inativo"""
        inactive_time = datetime.now() - self.last_activity
        return inactive_time.total_seconds() > (timeout_minutes * 60)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Obter estatísticas da sessão"""
        session_duration = datetime.now() - self.session_stats['session_start']
        
        return {
            **self.session_stats,
            'session_duration': int(session_duration.total_seconds()),
            'current_song': self.current_song.title if self.current_song else None,
            'queue_length': len(self.queue.queue),
            'state': self.state.value
        }

class ModernMusicSystem:
    """Sistema modernizado de música com funcionalidades avançadas"""
    
    def __init__(self, bot, config: Optional[Dict[str, Any]] = None):
        self.bot = bot
        self.config = config or {}
        
        # Sistemas core
        self.cache = SmartCache(default_ttl=3600) if SmartCache else None
        self.logger = SecureLogger('ModernMusicSystem') if SecureLogger else logger
        self.metrics = MetricsCollector() if MetricsCollector else None
        self.validator = DataValidator() if DataValidator else None
        self.events = EventSystem() if EventSystem else None
        self.rate_limiter = RateLimiter() if RateLimiter else None
        
        # Players por servidor
        self.players: Dict[int, ModernMusicPlayer] = {}
        
        # Dados persistentes
        self.user_preferences: Dict[int, UserPreferencesModel] = {}
        self.user_playlists: Dict[int, Dict[str, PlaylistModel]] = {}
        self.user_favorites: Dict[int, List[SongModel]] = {}
        
        # Configurações do YouTube-DL
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
            'source_address': '0.0.0.0',
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False
        }
        
        self.ffmpeg_options = {
            'before_options': (
                '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
                '-probesize 32M -analyzeduration 0 -loglevel panic'
            ),
            'options': '-vn -b:a 128k'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_options)
        
        # Tasks de background
        self._cleanup_task: Optional[asyncio.Task] = None
        self._recommendation_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Filtros de áudio
        self.audio_filters = {
            AudioFilter.NONE: "",
            AudioFilter.BASS_BOOST: "bass=g=10,dynaudnorm",
            AudioFilter.TREBLE_BOOST: "treble=g=5,dynaudnorm",
            AudioFilter.NIGHTCORE: "asetrate=48000*1.25,aresample=48000,bass=g=5",
            AudioFilter.VAPORWAVE: "asetrate=48000*0.8,aresample=48000,atempo=1.1",
            AudioFilter.EIGHT_D: "apulsator=hz=0.125",
            AudioFilter.KARAOKE: "pan=mono|c0=0.5*c0+-0.5*c1",
            AudioFilter.ECHO: "aecho=0.8:0.9:1000:0.3",
            AudioFilter.REVERB: "afreqshift=0,areverb=roomsize=0.5:damping=0.5"
        }
        
        if self.logger:
            self.logger.info("Sistema Modernizado de Música inicializado")
    
    async def setup_hook(self):
        """Configurar tasks de background"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_players())
        
        if not self._recommendation_task:
            self._recommendation_task = asyncio.create_task(self._auto_recommendation_system())
        
        if not self._metrics_task and self.metrics:
            self._metrics_task = asyncio.create_task(self._collect_metrics())
    
    async def shutdown(self):
        """Encerrar sistema e limpar recursos"""
        # Cancelar tasks
        for task in [self._cleanup_task, self._recommendation_task, self._metrics_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Desconectar todos os players
        for player in self.players.values():
            await player.disconnect()
        
        self.players.clear()
        
        if self.logger:
            self.logger.info("Sistema de música encerrado")
    
    def get_player(self, guild_id: int) -> ModernMusicPlayer:
        """Obter ou criar player para um servidor"""
        if guild_id not in self.players:
            self.players[guild_id] = ModernMusicPlayer(guild_id, self.cache)
        
        return self.players[guild_id]
    
    async def search_song(self, query: str, requester: discord.Member) -> Optional[Song]:
        """Buscar música com cache inteligente"""
        try:
            # Verificar rate limit
            if self.rate_limiter:
                if not await self.rate_limiter.check_rate_limit(
                    f"music_search_{requester.id}", max_requests=10, window=60
                ):
                    return None
            
            # Verificar cache
            cache_key = f"music_search_{hash(query)}"
            if self.cache:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    # Criar objeto Song a partir do cache
                    return Song(
                        title=cached_result['title'],
                        url=cached_result['url'],
                        duration=cached_result['duration'],
                        requester=requester,
                        thumbnail=cached_result.get('thumbnail'),
                        genre=MusicGenre(cached_result.get('genre', 'unknown'))
                    )
            
            # Preparar query
            if not urlparse(query).scheme:
                query = f"ytsearch:{query}"
            
            # Buscar no YouTube
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(query, download=False)
            )
            
            if not data:
                return None
            
            # Processar resultado
            if 'entries' in data and data['entries']:
                song_data = data['entries'][0]
            else:
                song_data = data
            
            if not song_data:
                return None
            
            # Criar objeto Song
            song = Song(
                title=song_data.get('title', 'Título desconhecido'),
                url=song_data.get('webpage_url', song_data.get('url', '')),
                duration=song_data.get('duration', 0) or 0,
                requester=requester,
                thumbnail=song_data.get('thumbnail'),
                genre=self._detect_genre(song_data)
            )
            
            # Salvar no cache
            if self.cache:
                cache_data = {
                    'title': song.title,
                    'url': song.url,
                    'duration': song.duration,
                    'thumbnail': song.thumbnail,
                    'genre': song.genre.value
                }
                await self.cache.set(cache_key, cache_data, ttl=3600)
            
            # Coletar métricas
            if self.metrics:
                await self.metrics.increment('music_searches_total')
                await self.metrics.histogram('music_search_duration', song.duration)
            
            return song
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao buscar música '{query}': {e}")
            
            if self.metrics:
                await self.metrics.increment('music_search_errors_total')
            
            return None
    
    def _detect_genre(self, song_data: Dict[str, Any]) -> MusicGenre:
        """Detectar gênero musical baseado nos metadados"""
        title = song_data.get('title', '').lower()
        description = song_data.get('description', '').lower()
        tags = song_data.get('tags', [])
        
        # Palavras-chave por gênero
        genre_keywords = {
            MusicGenre.ROCK: ['rock', 'metal', 'punk', 'grunge', 'alternative'],
            MusicGenre.POP: ['pop', 'mainstream', 'chart', 'hit'],
            MusicGenre.ELECTRONIC: ['electronic', 'edm', 'techno', 'house', 'dubstep', 'trance'],
            MusicGenre.HIP_HOP: ['hip hop', 'rap', 'trap', 'drill'],
            MusicGenre.CLASSICAL: ['classical', 'orchestra', 'symphony', 'piano', 'violin'],
            MusicGenre.JAZZ: ['jazz', 'blues', 'swing', 'bebop'],
            MusicGenre.COUNTRY: ['country', 'folk', 'bluegrass'],
            MusicGenre.REGGAE: ['reggae', 'ska', 'dub'],
            MusicGenre.INDIE: ['indie', 'independent', 'alternative']
        }
        
        # Verificar título e descrição
        text_to_check = f"{title} {description}"
        for genre, keywords in genre_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                return genre
        
        # Verificar tags
        if tags:
            tag_text = ' '.join(str(tag).lower() for tag in tags)
            for genre, keywords in genre_keywords.items():
                if any(keyword in tag_text for keyword in keywords):
                    return genre
        
        return MusicGenre.UNKNOWN
    
    async def play_song(self, guild_id: int, voice_channel: discord.VoiceChannel, 
                       query: str, requester: discord.Member) -> Tuple[bool, str]:
        """Tocar música ou adicionar à fila"""
        try:
            player = self.get_player(guild_id)
            
            # Conectar ao canal de voz
            if not await player.connect(voice_channel):
                return False, "❌ Não foi possível conectar ao canal de voz."
            
            # Buscar música
            song = await self.search_song(query, requester)
            if not song:
                return False, "❌ Não foi possível encontrar a música solicitada."
            
            # Validar duração (máximo 1 hora)
            if song.duration > 3600:
                return False, "❌ Música muito longa (máximo 1 hora)."
            
            # Adicionar à fila
            if not player.add_song(song):
                return False, "❌ Não foi possível adicionar à fila (limite atingido)."
            
            # Iniciar reprodução se não estiver tocando
            if player.state == PlaybackState.IDLE:
                await self._play_next(guild_id)
                return True, f"🎵 **Tocando agora:** {song.title}"
            else:
                queue_position = len(player.queue.queue)
                return True, f"📝 **Adicionado à fila:** {song.title} (Posição: {queue_position})"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao tocar música: {e}")
            return False, f"❌ Erro interno: {str(e)}"
    
    async def _play_next(self, guild_id: int):
        """Tocar próxima música da fila"""
        try:
            player = self.get_player(guild_id)
            
            if not player.voice_client or not player.voice_client.is_connected():
                return
            
            # Obter próxima música
            next_song = player.queue.get_next()
            
            # Verificar loop da música atual
            if not next_song and player.loop_current and player.current_song:
                next_song = player.current_song
            
            # Verificar loop da fila
            elif not next_song and player.loop_queue and player.queue.history:
                # Recarregar fila com histórico
                for song in player.queue.history:
                    player.queue.add(song)
                next_song = player.queue.get_next()
            
            if not next_song:
                player.state = PlaybackState.IDLE
                player.current_song = None
                
                # Emitir evento de fila vazia
                if self.events:
                    await self.events.emit('music_queue_empty', {
                        'guild_id': guild_id,
                        'player': player
                    })
                
                return
            
            # Configurar estado do player
            player.current_song = next_song
            player.state = PlaybackState.BUFFERING
            player.clear_skip_votes()
            player.song_start_time = datetime.now()
            player.total_pause_duration = timedelta()
            
            # Obter URL de streaming
            try:
                stream_data = await self.search_song(next_song.url, next_song.requester)
                if stream_data and stream_data.url:
                    stream_url = stream_data.url
                else:
                    stream_url = next_song.url
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Erro ao obter URL de streaming: {e}")
                stream_url = next_song.url
            
            # Aplicar filtros de áudio
            ffmpeg_options = self.ffmpeg_options.copy()
            if player.current_filter != AudioFilter.NONE:
                filter_string = self.audio_filters.get(player.current_filter, "")
                if filter_string:
                    ffmpeg_options['options'] += f" -af {filter_string}"
            
            # Criar source de áudio
            try:
                source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
                source = discord.PCMVolumeTransformer(source, volume=player.volume)
                
                # Tocar música
                player.voice_client.play(
                    source, 
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self._song_finished(guild_id, e), self.bot.loop
                    )
                )
                
                player.state = PlaybackState.PLAYING
                player.session_stats['songs_played'] += 1
                next_song.play_count += 1
                
                # Adicionar ao histórico
                player.queue.history.append(next_song)
                
                # Emitir evento de música iniciada
                if self.events:
                    await self.events.emit('music_song_started', {
                        'guild_id': guild_id,
                        'song': next_song,
                        'player': player
                    })
                
                # Coletar métricas
                if self.metrics:
                    await self.metrics.increment('music_songs_played_total')
                    await self.metrics.histogram('music_song_duration', next_song.duration)
                
                if self.logger:
                    self.logger.info(f"Tocando: {next_song.title} no servidor {guild_id}")
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro ao criar source de áudio: {e}")
                
                player.state = PlaybackState.ERROR
                
                # Tentar próxima música
                await asyncio.sleep(1)
                await self._play_next(guild_id)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao tocar próxima música: {e}")
            
            player = self.get_player(guild_id)
            player.state = PlaybackState.ERROR
    
    async def _song_finished(self, guild_id: int, error):
        """Callback quando música termina"""
        if error and self.logger:
            self.logger.error(f"Erro na reprodução: {error}")
        
        player = self.get_player(guild_id)
        
        # Atualizar estatísticas
        if player.current_song:
            player.session_stats['total_playtime'] += player.current_song.duration
        
        # Emitir evento de música finalizada
        if self.events:
            await self.events.emit('music_song_finished', {
                'guild_id': guild_id,
                'song': player.current_song,
                'error': error,
                'player': player
            })
        
        # Tocar próxima música
        await self._play_next(guild_id)
    
    async def pause_resume(self, guild_id: int) -> Tuple[bool, str]:
        """Pausar ou retomar reprodução"""
        player = self.get_player(guild_id)
        
        if not player.voice_client or player.state not in [PlaybackState.PLAYING, PlaybackState.PAUSED]:
            return False, "❌ Nenhuma música está tocando."
        
        if player.state == PlaybackState.PAUSED:
            player.voice_client.resume()
            player.state = PlaybackState.PLAYING
            
            # Calcular tempo pausado
            if player.pause_start_time:
                pause_duration = datetime.now() - player.pause_start_time
                player.total_pause_duration += pause_duration
                player.pause_start_time = None
            
            player.update_activity()
            return True, "▶️ Música retomada."
        else:
            player.voice_client.pause()
            player.state = PlaybackState.PAUSED
            player.pause_start_time = datetime.now()
            return True, "⏸️ Música pausada."
    
    async def skip_song(self, guild_id: int, user_id: int, force: bool = False) -> Tuple[bool, str]:
        """Pular música atual"""
        player = self.get_player(guild_id)
        
        if player.state not in [PlaybackState.PLAYING, PlaybackState.PAUSED]:
            return False, "❌ Nenhuma música está tocando."
        
        # Verificar se é o solicitante da música ou força
        if force or (player.current_song and player.current_song.requester.id == user_id):
            if player.current_song:
                player.current_song.skip_count += 1
                player.session_stats['skip_count'] += 1
            
            player.voice_client.stop()
            return True, "⏭️ Música pulada."
        
        # Sistema de votação
        vote_result = player.add_skip_vote(user_id)
        
        if vote_result['already_voted']:
            return True, f"🗳️ Você já votou para pular. Votos: {vote_result['votes']}/{player.required_skip_votes}"
        
        if vote_result['should_skip']:
            if player.current_song:
                player.current_song.skip_count += 1
                player.session_stats['skip_count'] += 1
            
            player.voice_client.stop()
            return True, f"⏭️ Música pulada por votação ({vote_result['votes']}/{vote_result['required']})."
        else:
            remaining = vote_result['required'] - vote_result['votes']
            return True, f"🗳️ Voto registrado. Faltam {remaining} votos para pular."
    
    async def stop_music(self, guild_id: int) -> Tuple[bool, str]:
        """Parar música e limpar fila"""
        player = self.get_player(guild_id)
        
        if not player.voice_client:
            return False, "❌ Não há música tocando."
        
        # Parar reprodução
        if player.voice_client.is_playing() or player.voice_client.is_paused():
            player.voice_client.stop()
        
        # Limpar fila e estado
        player.queue.queue.clear()
        player.state = PlaybackState.IDLE
        player.current_song = None
        player.clear_skip_votes()
        
        return True, "⏹️ Música parada e fila limpa."
    
    async def disconnect(self, guild_id: int) -> Tuple[bool, str]:
        """Desconectar do canal de voz"""
        player = self.get_player(guild_id)
        
        if not player.voice_client:
            return False, "❌ Não estou conectado a nenhum canal de voz."
        
        await player.disconnect()
        return True, "👋 Desconectado do canal de voz."
    
    async def set_volume(self, guild_id: int, volume: int) -> Tuple[bool, str]:
        """Definir volume (0-100)"""
        if not 0 <= volume <= 100:
            return False, "❌ Volume deve estar entre 0 e 100."
        
        player = self.get_player(guild_id)
        player.volume = volume / 100.0
        
        if player.voice_client and player.voice_client.source:
            player.voice_client.source.volume = player.volume
        
        return True, f"🔊 Volume definido para {volume}%."
    
    async def set_filter(self, guild_id: int, filter_type: AudioFilter) -> Tuple[bool, str]:
        """Aplicar filtro de áudio"""
        player = self.get_player(guild_id)
        
        if player.current_filter == filter_type:
            return True, f"🎛️ Filtro '{filter_type.value}' já está ativo."
        
        player.current_filter = filter_type
        
        # Se há música tocando, reaplicar com novo filtro
        if player.state == PlaybackState.PLAYING and player.current_song:
            # Salvar posição atual
            current_position = player.get_current_position()
            
            # Parar e reiniciar com filtro
            player.voice_client.stop()
            
            # Aguardar um pouco para evitar conflitos
            await asyncio.sleep(0.5)
            
            # Reiniciar reprodução (o filtro será aplicado automaticamente)
            await self._play_next(guild_id)
        
        filter_name = filter_type.value.replace('_', ' ').title()
        return True, f"🎛️ Filtro '{filter_name}' aplicado."
    
    def get_queue_info(self, guild_id: int) -> Dict[str, Any]:
        """Obter informações detalhadas da fila"""
        player = self.get_player(guild_id)
        queue_stats = player.queue.get_stats()
        
        return {
            'current_song': player.current_song,
            'queue': list(player.queue.queue),
            'queue_length': len(player.queue.queue),
            'state': player.state.value,
            'volume': int(player.volume * 100),
            'current_filter': player.current_filter.value,
            'loop_current': player.loop_current,
            'loop_queue': player.loop_queue,
            'auto_play': player.auto_play,
            'stats': queue_stats,
            'session_stats': player.get_session_stats(),
            'current_position': player.get_current_position(),
            'remaining_time': player.get_remaining_time()
        }
    
    async def shuffle_queue(self, guild_id: int) -> Tuple[bool, str]:
        """Embaralhar fila"""
        player = self.get_player(guild_id)
        
        if len(player.queue.queue) < 2:
            return False, "❌ Fila deve ter pelo menos 2 músicas para embaralhar."
        
        # Embaralhar fila
        queue_list = list(player.queue.queue)
        random.shuffle(queue_list)
        player.queue.queue = deque(queue_list, maxlen=player.queue.queue.maxlen)
        
        return True, f"🔀 Fila embaralhada ({len(player.queue.queue)} músicas)."
    
    async def toggle_loop(self, guild_id: int, loop_type: str = "current") -> Tuple[bool, str]:
        """Alternar modo de repetição"""
        player = self.get_player(guild_id)
        
        if loop_type == "current":
            player.loop_current = not player.loop_current
            if player.loop_current:
                player.loop_queue = False  # Desativar loop da fila
                return True, "🔂 Repetição da música atual ativada."
            else:
                return True, "➡️ Repetição da música atual desativada."
        
        elif loop_type == "queue":
            player.loop_queue = not player.loop_queue
            if player.loop_queue:
                player.loop_current = False  # Desativar loop da música
                return True, "🔁 Repetição da fila ativada."
            else:
                return True, "➡️ Repetição da fila desativada."
        
        else:
            return False, "❌ Tipo de loop inválido. Use 'current' ou 'queue'."
    
    # ==================== SISTEMA DE PLAYLISTS ====================
    
    async def create_playlist(self, user_id: int, name: str, is_public: bool = False) -> Tuple[bool, str]:
        """Criar nova playlist"""
        if user_id not in self.user_playlists:
            self.user_playlists[user_id] = {}
        
        user_playlists = self.user_playlists[user_id]
        
        # Verificar se já existe
        if name in user_playlists:
            return False, "❌ Já existe uma playlist com esse nome."
        
        # Verificar limite
        if len(user_playlists) >= 25:
            return False, "❌ Você atingiu o limite máximo de 25 playlists."
        
        # Validar nome
        if len(name) < 1 or len(name) > 50:
            return False, "❌ Nome da playlist deve ter entre 1 e 50 caracteres."
        
        # Criar playlist
        if PYDANTIC_AVAILABLE:
            playlist = PlaylistModel(
                name=name,
                owner_id=user_id,
                is_public=is_public
            )
        else:
            playlist = PlaylistModel(
                name=name,
                owner_id=user_id,
                songs=[],
                is_public=is_public,
                description="",
                created_at=datetime.now(),
                last_modified=datetime.now(),
                play_count=0
            )
        
        user_playlists[name] = playlist
        
        return True, f"📝 Playlist '{name}' criada com sucesso!"
    
    async def delete_playlist(self, user_id: int, name: str) -> Tuple[bool, str]:
        """Deletar playlist"""
        if user_id not in self.user_playlists or name not in self.user_playlists[user_id]:
            return False, "❌ Playlist não encontrada."
        
        del self.user_playlists[user_id][name]
        return True, f"🗑️ Playlist '{name}' deletada com sucesso."
    
    async def add_to_playlist(self, user_id: int, playlist_name: str, song: Song) -> Tuple[bool, str]:
        """Adicionar música à playlist"""
        if user_id not in self.user_playlists or playlist_name not in self.user_playlists[user_id]:
            return False, "❌ Playlist não encontrada."
        
        playlist = self.user_playlists[user_id][playlist_name]
        
        # Verificar se música já existe
        for existing_song in playlist.songs:
            if existing_song.url == song.url:
                return False, "❌ Esta música já está na playlist."
        
        # Verificar limite
        if len(playlist.songs) >= 200:
            return False, "❌ Playlist atingiu o limite máximo de 200 músicas."
        
        # Adicionar música
        if PYDANTIC_AVAILABLE:
            song_model = SongModel(
                title=song.title,
                url=song.url,
                duration=song.duration,
                requester_id=song.requester.id,
                thumbnail=song.thumbnail,
                genre=song.genre
            )
        else:
            song_model = SongModel(
                title=song.title,
                url=song.url,
                duration=song.duration,
                requester_id=song.requester.id,
                thumbnail=song.thumbnail,
                genre=song.genre,
                popularity_score=song.popularity_score,
                requested_at=song.requested_at,
                play_count=song.play_count,
                skip_count=song.skip_count
            )
        
        playlist.songs.append(song_model)
        playlist.last_modified = datetime.now()
        
        return True, f"➕ '{song.title}' adicionada à playlist '{playlist_name}'."
    
    async def remove_from_playlist(self, user_id: int, playlist_name: str, index: int) -> Tuple[bool, str]:
        """Remover música da playlist"""
        if user_id not in self.user_playlists or playlist_name not in self.user_playlists[user_id]:
            return False, "❌ Playlist não encontrada."
        
        playlist = self.user_playlists[user_id][playlist_name]
        
        if not 0 <= index < len(playlist.songs):
            return False, f"❌ Índice inválido. Use um número entre 1 e {len(playlist.songs)}."
        
        removed_song = playlist.songs.pop(index)
        playlist.last_modified = datetime.now()
        
        return True, f"➖ '{removed_song.title}' removida da playlist '{playlist_name}'."
    
    async def play_playlist(self, guild_id: int, voice_channel: discord.VoiceChannel, 
                           user_id: int, playlist_name: str, requester: discord.Member) -> Tuple[bool, str]:
        """Tocar playlist inteira"""
        if user_id not in self.user_playlists or playlist_name not in self.user_playlists[user_id]:
            return False, "❌ Playlist não encontrada."
        
        playlist = self.user_playlists[user_id][playlist_name]
        
        if not playlist.songs:
            return False, "❌ Playlist está vazia."
        
        player = self.get_player(guild_id)
        
        # Conectar ao canal de voz
        if not await player.connect(voice_channel):
            return False, "❌ Não foi possível conectar ao canal de voz."
        
        songs_added = 0
        
        # Adicionar todas as músicas à fila
        for song_model in playlist.songs:
            # Converter SongModel para Song
            song = Song(
                title=song_model.title,
                url=song_model.url,
                duration=song_model.duration,
                requester=requester,
                thumbnail=song_model.thumbnail,
                genre=song_model.genre if hasattr(song_model, 'genre') else MusicGenre.UNKNOWN
            )
            
            if player.add_song(song):
                songs_added += 1
            else:
                break  # Parar se não conseguir adicionar mais
        
        # Iniciar reprodução se não estiver tocando
        if player.state == PlaybackState.IDLE and songs_added > 0:
            await self._play_next(guild_id)
        
        # Atualizar estatísticas da playlist
        playlist.play_count += 1
        
        return True, f"📝 Playlist '{playlist_name}' adicionada à fila ({songs_added} músicas)."
    
    def get_user_playlists(self, user_id: int) -> List[Dict[str, Any]]:
        """Obter playlists do usuário"""
        if user_id not in self.user_playlists:
            return []
        
        playlists = []
        for name, playlist in self.user_playlists[user_id].items():
            playlists.append({
                'name': name,
                'song_count': len(playlist.songs),
                'is_public': playlist.is_public,
                'created_at': playlist.created_at,
                'play_count': playlist.play_count
            })
        
        return playlists
    
    # ==================== SISTEMA DE FAVORITOS ====================
    
    async def add_to_favorites(self, user_id: int, song: Song) -> Tuple[bool, str]:
        """Adicionar música aos favoritos"""
        if user_id not in self.user_favorites:
            self.user_favorites[user_id] = []
        
        favorites = self.user_favorites[user_id]
        
        # Verificar se já está nos favoritos
        for fav_song in favorites:
            if fav_song.url == song.url:
                return False, "❌ Esta música já está nos seus favoritos."
        
        # Verificar limite
        if len(favorites) >= 100:
            return False, "❌ Você atingiu o limite máximo de 100 favoritos."
        
        # Adicionar aos favoritos
        if PYDANTIC_AVAILABLE:
            fav_song = SongModel(
                title=song.title,
                url=song.url,
                duration=song.duration,
                requester_id=song.requester.id,
                thumbnail=song.thumbnail,
                genre=song.genre
            )
        else:
            fav_song = SongModel(
                title=song.title,
                url=song.url,
                duration=song.duration,
                requester_id=song.requester.id,
                thumbnail=song.thumbnail,
                genre=song.genre,
                popularity_score=song.popularity_score,
                requested_at=song.requested_at,
                play_count=song.play_count,
                skip_count=song.skip_count
            )
        
        favorites.append(fav_song)
        
        return True, f"⭐ '{song.title}' adicionada aos favoritos!"
    
    async def remove_from_favorites(self, user_id: int, index: int) -> Tuple[bool, str]:
        """Remover música dos favoritos"""
        if user_id not in self.user_favorites or not self.user_favorites[user_id]:
            return False, "❌ Você não possui favoritos."
        
        favorites = self.user_favorites[user_id]
        
        if not 0 <= index < len(favorites):
            return False, f"❌ Índice inválido. Use um número entre 1 e {len(favorites)}."
        
        removed_song = favorites.pop(index)
        return True, f"🗑️ '{removed_song.title}' removida dos favoritos."
    
    def get_user_favorites(self, user_id: int) -> List[SongModel]:
        """Obter favoritos do usuário"""
        return self.user_favorites.get(user_id, [])
    
    # ==================== TASKS DE BACKGROUND ====================
    
    async def _cleanup_inactive_players(self):
        """Limpar players inativos automaticamente"""
        while True:
            try:
                await asyncio.sleep(300)  # Verificar a cada 5 minutos
                
                inactive_guilds = []
                
                for guild_id, player in self.players.items():
                    if player.is_inactive(timeout_minutes=15):
                        if self.logger:
                            self.logger.info(f"Desconectando player inativo: {guild_id}")
                        
                        await player.disconnect()
                        inactive_guilds.append(guild_id)
                
                # Remover players inativos
                for guild_id in inactive_guilds:
                    del self.players[guild_id]
                
                if self.metrics and inactive_guilds:
                    await self.metrics.increment('music_players_cleaned_total', len(inactive_guilds))
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro na limpeza de players: {e}")
    
    async def _auto_recommendation_system(self):
        """Sistema automático de recomendações"""
        while True:
            try:
                await asyncio.sleep(60)  # Verificar a cada minuto
                
                for guild_id, player in self.players.items():
                    # Verificar se precisa de recomendações
                    if (player.auto_play and 
                        len(player.queue.queue) <= player.queue.recommendation_threshold and
                        player.queue.history):
                        
                        # Gerar recomendações baseadas no histórico
                        recommendations = await self._generate_recommendations(player)
                        
                        # Adicionar recomendações à fila
                        for song in recommendations[:3]:  # Máximo 3 recomendações
                            player.add_song(song)
                        
                        if recommendations and self.logger:
                            self.logger.info(f"Adicionadas {len(recommendations)} recomendações para {guild_id}")
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro no sistema de recomendações: {e}")
    
    async def _collect_metrics(self):
        """Coletar métricas do sistema"""
        while True:
            try:
                await asyncio.sleep(30)  # Coletar a cada 30 segundos
                
                if not self.metrics:
                    continue
                
                # Métricas gerais
                await self.metrics.gauge('music_active_players', len(self.players))
                
                total_queue_size = sum(len(p.queue.queue) for p in self.players.values())
                await self.metrics.gauge('music_total_queue_size', total_queue_size)
                
                playing_players = sum(1 for p in self.players.values() 
                                    if p.state == PlaybackState.PLAYING)
                await self.metrics.gauge('music_playing_players', playing_players)
                
                # Métricas por estado
                state_counts = {}
                for player in self.players.values():
                    state = player.state.value
                    state_counts[state] = state_counts.get(state, 0) + 1
                
                for state, count in state_counts.items():
                    await self.metrics.gauge(f'music_players_state_{state}', count)
                
                # Métricas de gêneros
                genre_counts = {}
                for player in self.players.values():
                    for song in player.queue.queue:
                        genre = song.genre.value
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
                
                for genre, count in genre_counts.items():
                    await self.metrics.gauge(f'music_queue_genre_{genre}', count)
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro na coleta de métricas: {e}")
    
    async def _generate_recommendations(self, player: ModernMusicPlayer) -> List[Song]:
        """Gerar recomendações baseadas no histórico do player"""
        try:
            if not player.queue.history:
                return []
            
            # Analisar últimas 10 músicas
            recent_songs = list(player.queue.history)[-10:]
            
            # Calcular gêneros mais populares
            genre_scores = {}
            for song in recent_songs:
                genre = song.genre
                genre_scores[genre] = genre_scores.get(genre, 0) + 1
            
            # Calcular duração média preferida
            avg_duration = sum(song.duration for song in recent_songs) / len(recent_songs)
            duration_tolerance = 120  # 2 minutos de tolerância
            
            # Aqui seria implementada a lógica real de recomendação
            # Por enquanto, retorna lista vazia pois precisaria de uma API externa
            # ou base de dados de músicas para fazer recomendações reais
            
            return []
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao gerar recomendações: {e}")
            return []
    
    # ==================== SISTEMA DE PREFERÊNCIAS ====================
    
    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> Tuple[bool, str]:
        """Atualizar preferências do usuário"""
        try:
            if PYDANTIC_AVAILABLE:
                user_prefs = UserPreferencesModel(
                    user_id=user_id,
                    **preferences
                )
            else:
                user_prefs = UserPreferencesModel(
                    user_id=user_id,
                    favorite_genres=preferences.get('favorite_genres', []),
                    preferred_duration_range=preferences.get('preferred_duration_range', (0, 600)),
                    volume_preference=preferences.get('volume_preference', 0.5),
                    auto_queue=preferences.get('auto_queue', True),
                    explicit_content=preferences.get('explicit_content', True),
                    last_updated=datetime.now()
                )
            
            self.user_preferences[user_id] = user_prefs
            
            return True, "✅ Preferências atualizadas com sucesso!"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao atualizar preferências: {e}")
            return False, f"❌ Erro ao atualizar preferências: {str(e)}"
    
    def get_user_preferences(self, user_id: int) -> Optional[UserPreferencesModel]:
        """Obter preferências do usuário"""
        return self.user_preferences.get(user_id)
    
    # ==================== SISTEMA DE ANÁLISE ====================
    
    def analyze_listening_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analisar padrões de escuta do usuário"""
        analysis = {
            'total_songs_requested': 0,
            'favorite_genres': {},
            'average_song_duration': 0,
            'most_active_hours': {},
            'skip_rate': 0.0,
            'playlist_count': 0,
            'favorite_count': 0
        }
        
        try:
            # Analisar histórico de todos os players
            user_songs = []
            for player in self.players.values():
                for song in player.queue.history:
                    if song.requester.id == user_id:
                        user_songs.append(song)
            
            if not user_songs:
                return analysis
            
            # Estatísticas básicas
            analysis['total_songs_requested'] = len(user_songs)
            analysis['average_song_duration'] = sum(s.duration for s in user_songs) / len(user_songs)
            
            # Gêneros favoritos
            genre_counts = {}
            for song in user_songs:
                genre = song.genre.value
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            analysis['favorite_genres'] = dict(sorted(genre_counts.items(), 
                                                    key=lambda x: x[1], reverse=True)[:5])
            
            # Taxa de skip
            total_plays = sum(s.play_count for s in user_songs)
            total_skips = sum(s.skip_count for s in user_songs)
            if total_plays > 0:
                analysis['skip_rate'] = total_skips / total_plays
            
            # Horários mais ativos
            hour_counts = {}
            for song in user_songs:
                hour = song.requested_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            analysis['most_active_hours'] = dict(sorted(hour_counts.items(), 
                                                       key=lambda x: x[1], reverse=True)[:3])
            
            # Contadores de playlists e favoritos
            analysis['playlist_count'] = len(self.user_playlists.get(user_id, {}))
            analysis['favorite_count'] = len(self.user_favorites.get(user_id, []))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro na análise de padrões: {e}")
        
        return analysis
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obter estatísticas globais do sistema"""
        stats = {
            'total_players': len(self.players),
            'active_players': 0,
            'total_songs_in_queues': 0,
            'total_users': len(self.user_preferences),
            'total_playlists': 0,
            'total_favorites': 0,
            'most_popular_genres': {},
            'average_queue_length': 0,
            'system_uptime': 0
        }
        
        try:
            # Estatísticas dos players
            active_count = 0
            total_queue_songs = 0
            genre_counts = {}
            
            for player in self.players.values():
                if player.state != PlaybackState.IDLE:
                    active_count += 1
                
                queue_length = len(player.queue.queue)
                total_queue_songs += queue_length
                
                # Contar gêneros
                for song in player.queue.queue:
                    genre = song.genre.value
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            stats['active_players'] = active_count
            stats['total_songs_in_queues'] = total_queue_songs
            stats['average_queue_length'] = total_queue_songs / len(self.players) if self.players else 0
            stats['most_popular_genres'] = dict(sorted(genre_counts.items(), 
                                                     key=lambda x: x[1], reverse=True)[:5])
            
            # Estatísticas de playlists e favoritos
            total_playlists = sum(len(playlists) for playlists in self.user_playlists.values())
            total_favorites = sum(len(favorites) for favorites in self.user_favorites.values())
            
            stats['total_playlists'] = total_playlists
            stats['total_favorites'] = total_favorites
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao obter estatísticas globais: {e}")
        
        return stats
    
    # ==================== SISTEMA DE SAÚDE ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do sistema"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'metrics': {},
            'issues': []
        }
        
        try:
            # Verificar componentes core
            health['components']['cache'] = 'available' if self.cache else 'unavailable'
            health['components']['logger'] = 'available' if self.logger else 'unavailable'
            health['components']['metrics'] = 'available' if self.metrics else 'unavailable'
            health['components']['events'] = 'available' if self.events else 'unavailable'
            health['components']['rate_limiter'] = 'available' if self.rate_limiter else 'unavailable'
            
            # Verificar YouTube-DL
            try:
                # Teste simples de extração
                test_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.ytdl.extract_info('ytsearch:test', download=False)
                    ),
                    timeout=10
                )
                health['components']['ytdl'] = 'healthy' if test_data else 'degraded'
            except asyncio.TimeoutError:
                health['components']['ytdl'] = 'timeout'
                health['issues'].append('YouTube-DL timeout durante teste')
            except Exception as e:
                health['components']['ytdl'] = 'error'
                health['issues'].append(f'YouTube-DL error: {str(e)}')
            
            # Verificar players
            healthy_players = 0
            error_players = 0
            
            for guild_id, player in self.players.items():
                if player.state == PlaybackState.ERROR:
                    error_players += 1
                    health['issues'].append(f'Player {guild_id} em estado de erro')
                else:
                    healthy_players += 1
            
            health['components']['players'] = {
                'total': len(self.players),
                'healthy': healthy_players,
                'errors': error_players
            }
            
            # Métricas de performance
            health['metrics'] = {
                'total_players': len(self.players),
                'active_players': sum(1 for p in self.players.values() 
                                    if p.state != PlaybackState.IDLE),
                'total_queue_size': sum(len(p.queue.queue) for p in self.players.values()),
                'memory_usage': 'N/A',  # Seria implementado com psutil
                'cpu_usage': 'N/A'      # Seria implementado com psutil
            }
            
            # Determinar status geral
            if health['issues']:
                if error_players > 0 or health['components']['ytdl'] == 'error':
                    health['status'] = 'unhealthy'
                else:
                    health['status'] = 'degraded'
            
        except Exception as e:
            health['status'] = 'error'
            health['issues'].append(f'Erro durante verificação de saúde: {str(e)}')
            
            if self.logger:
                self.logger.error(f"Erro na verificação de saúde: {e}")
        
        return health
    
    # ==================== UTILITÁRIOS ====================
    
    def format_duration(self, seconds: int) -> str:
        """Formatar duração em formato legível"""
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
    
    def format_queue_duration(self, queue_duration: int) -> str:
        """Formatar duração total da fila"""
        if queue_duration < 60:
            return f"{queue_duration}s"
        elif queue_duration < 3600:
            minutes = queue_duration // 60
            seconds = queue_duration % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = queue_duration // 3600
            minutes = (queue_duration % 3600) // 60
            return f"{hours}h {minutes}m"
    
    async def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Exportar dados do usuário (LGPD/GDPR compliance)"""
        user_data = {
            'user_id': user_id,
            'export_timestamp': datetime.now().isoformat(),
            'preferences': None,
            'playlists': [],
            'favorites': [],
            'listening_history': [],
            'statistics': None
        }
        
        try:
            # Preferências
            if user_id in self.user_preferences:
                prefs = self.user_preferences[user_id]
                user_data['preferences'] = {
                    'favorite_genres': [g.value for g in prefs.favorite_genres] if hasattr(prefs, 'favorite_genres') else [],
                    'preferred_duration_range': prefs.preferred_duration_range if hasattr(prefs, 'preferred_duration_range') else (0, 600),
                    'volume_preference': prefs.volume_preference if hasattr(prefs, 'volume_preference') else 0.5,
                    'auto_queue': prefs.auto_queue if hasattr(prefs, 'auto_queue') else True,
                    'explicit_content': prefs.explicit_content if hasattr(prefs, 'explicit_content') else True,
                    'last_updated': prefs.last_updated.isoformat() if hasattr(prefs, 'last_updated') else None
                }
            
            # Playlists
            if user_id in self.user_playlists:
                for name, playlist in self.user_playlists[user_id].items():
                    playlist_data = {
                        'name': name,
                        'is_public': playlist.is_public,
                        'description': playlist.description if hasattr(playlist, 'description') else '',
                        'created_at': playlist.created_at.isoformat() if hasattr(playlist, 'created_at') else None,
                        'songs': []
                    }
                    
                    for song in playlist.songs:
                        playlist_data['songs'].append({
                            'title': song.title,
                            'url': song.url,
                            'duration': song.duration,
                            'genre': song.genre.value if hasattr(song, 'genre') else 'unknown'
                        })
                    
                    user_data['playlists'].append(playlist_data)
            
            # Favoritos
            if user_id in self.user_favorites:
                for song in self.user_favorites[user_id]:
                    user_data['favorites'].append({
                        'title': song.title,
                        'url': song.url,
                        'duration': song.duration,
                        'genre': song.genre.value if hasattr(song, 'genre') else 'unknown'
                    })
            
            # Estatísticas
            user_data['statistics'] = self.analyze_listening_patterns(user_id)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao exportar dados do usuário {user_id}: {e}")
        
        return user_data
    
    async def delete_user_data(self, user_id: int) -> Tuple[bool, str]:
        """Deletar todos os dados do usuário (LGPD/GDPR compliance)"""
        try:
            deleted_items = []
            
            # Remover preferências
            if user_id in self.user_preferences:
                del self.user_preferences[user_id]
                deleted_items.append('preferências')
            
            # Remover playlists
            if user_id in self.user_playlists:
                playlist_count = len(self.user_playlists[user_id])
                del self.user_playlists[user_id]
                deleted_items.append(f'{playlist_count} playlists')
            
            # Remover favoritos
            if user_id in self.user_favorites:
                favorite_count = len(self.user_favorites[user_id])
                del self.user_favorites[user_id]
                deleted_items.append(f'{favorite_count} favoritos')
            
            if deleted_items:
                items_str = ', '.join(deleted_items)
                return True, f"✅ Dados removidos: {items_str}"
            else:
                return True, "ℹ️ Nenhum dado encontrado para este usuário."
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao deletar dados do usuário {user_id}: {e}")
            return False, f"❌ Erro ao deletar dados: {str(e)}"

# ==================== FUNÇÕES AUXILIARES ====================

def create_modern_music_system(bot, config: Optional[Dict[str, Any]] = None) -> ModernMusicSystem:
    """Factory function para criar sistema de música modernizado"""
    return ModernMusicSystem(bot, config)

def get_audio_filter_description(filter_type: AudioFilter) -> str:
    """Obter descrição do filtro de áudio"""
    descriptions = {
        AudioFilter.NONE: "Sem filtro",
        AudioFilter.BASS_BOOST: "Realce de graves",
        AudioFilter.TREBLE_BOOST: "Realce de agudos",
        AudioFilter.NIGHTCORE: "Efeito Nightcore (velocidade aumentada)",
        AudioFilter.VAPORWAVE: "Efeito Vaporwave (velocidade reduzida)",
        AudioFilter.EIGHT_D: "Áudio 8D (efeito espacial)",
        AudioFilter.KARAOKE: "Modo Karaokê (redução vocal)",
        AudioFilter.ECHO: "Efeito de eco",
        AudioFilter.REVERB: "Efeito de reverberação"
    }
    return descriptions.get(filter_type, "Filtro desconhecido")

def validate_youtube_url(url: str) -> bool:
    """Validar se é uma URL válida do YouTube"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([\w-]+)'
    ]
    
    import re
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False

# ==================== EXCEÇÕES CUSTOMIZADAS ====================

class MusicSystemError(Exception):
    """Exceção base do sistema de música"""
    pass

class PlayerNotFoundError(MusicSystemError):
    """Player não encontrado"""
    pass

class QueueFullError(MusicSystemError):
    """Fila cheia"""
    pass

class InvalidSongError(MusicSystemError):
    """Música inválida"""
    pass

class PlaylistNotFoundError(MusicSystemError):
    """Playlist não encontrada"""
    pass

class RateLimitExceededError(MusicSystemError):
    """Rate limit excedido"""
    pass

# ==================== CONSTANTES ====================

DEFAULT_MUSIC_CONFIG = {
    'max_queue_size': 500,
    'max_song_duration': 3600,  # 1 hora
    'max_queue_duration': 7200,  # 2 horas
    'cleanup_interval': 300,     # 5 minutos
    'recommendation_threshold': 3,
    'max_playlists_per_user': 25,
    'max_songs_per_playlist': 200,
    'max_favorites_per_user': 100,
    'default_volume': 0.5,
    'skip_vote_threshold': 0.5,  # 50% dos usuários
    'inactive_timeout': 900,     # 15 minutos
    'enable_auto_recommendations': True,
    'enable_smart_queue': True,
    'enable_audio_filters': True,
    'enable_crossfade': False,
    'crossfade_duration': 2.0
}

if __name__ == "__main__":
    # Exemplo de uso (apenas para testes)
    import asyncio
    
    async def test_system():
        """Teste básico do sistema"""
        system = ModernMusicSystem(None)
        
        # Verificar saúde
        health = await system.health_check()
        print(f"Status do sistema: {health['status']}")
        
        # Estatísticas globais
        stats = system.get_global_stats()
        print(f"Players ativos: {stats['active_players']}")
        
        await system.shutdown()
    
    # asyncio.run(test_system())