#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Modernizado de Torneios
Gerencia torneios automatizados com brackets inteligentes e integração com sistemas core

Autor: AI Assistant
Versão: 3.0.0
"""

import asyncio
import json
import math
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

# Imports condicionais para compatibilidade
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f

# Imports dos sistemas core modernos
try:
    from src.core.smart_cache import SmartCache
    from src.core.secure_logger import SecureLogger
    from src.core.typed_config import TypedConfig
    from src.core.metrics_system import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
except ImportError:
    # Fallback para sistemas não disponíveis
    SmartCache = None
    SecureLogger = None
    TypedConfig = None
    MetricsCollector = None
    DataValidator = None
    EventSystem = None
    RateLimiter = None

class TournamentStatus(Enum):
    """Status possíveis de um torneio"""
    REGISTRATION = "registration"  # Inscrições abertas
    STARTING = "starting"          # Iniciando
    IN_PROGRESS = "in_progress"    # Em andamento
    PAUSED = "paused"             # Pausado
    FINISHED = "finished"          # Finalizado
    CANCELLED = "cancelled"        # Cancelado

class MatchStatus(Enum):
    """Status possíveis de uma partida"""
    PENDING = "pending"            # Aguardando
    READY = "ready"               # Pronta para iniciar
    IN_PROGRESS = "in_progress"    # Em andamento
    FINISHED = "finished"          # Finalizada
    WALKOVER = "walkover"          # W.O.
    DISPUTED = "disputed"          # Em disputa

class TournamentType(Enum):
    """Tipos de torneio"""
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"
    BATTLE_ROYALE = "battle_royale"

class GameMode(Enum):
    """Modos de jogo suportados"""
    SOLO = "solo"
    DUO = "duo"
    SQUAD = "squad"
    CUSTOM = "custom"

# Modelos de dados com Pydantic (com fallback)
if PYDANTIC_AVAILABLE:
    class ParticipantModel(BaseModel):
        """Modelo de participante do torneio"""
        user_id: str = Field(..., description="ID do usuário")
        username: str = Field(..., max_length=50, description="Nome do usuário")
        team_name: str = Field(..., max_length=30, description="Nome da equipe")
        discord_tag: Optional[str] = Field(None, description="Tag do Discord")
        registered_at: datetime = Field(default_factory=datetime.now)
        seed: int = Field(default=0, description="Seed do participante")
        elo_rating: Optional[int] = Field(None, description="Rating ELO")
        stats: Dict[str, Any] = Field(default_factory=dict)
        
        @validator('username', 'team_name')
        def validate_names(cls, v):
            if not v or not v.strip():
                raise ValueError("Nome não pode estar vazio")
            return v.strip()
    
    class MatchModel(BaseModel):
        """Modelo de partida do torneio"""
        id: str = Field(..., description="ID da partida")
        tournament_id: str = Field(..., description="ID do torneio")
        round_number: int = Field(..., ge=1, description="Número da rodada")
        bracket_position: int = Field(..., ge=0, description="Posição no bracket")
        player1: ParticipantModel = Field(..., description="Jogador 1")
        player2: Optional[ParticipantModel] = Field(None, description="Jogador 2")
        status: MatchStatus = Field(default=MatchStatus.PENDING)
        winner: Optional[str] = Field(None, description="ID do vencedor")
        score: Dict[str, Any] = Field(default_factory=dict)
        created_at: datetime = Field(default_factory=datetime.now)
        scheduled_time: Optional[datetime] = Field(None)
        started_at: Optional[datetime] = Field(None)
        finished_at: Optional[datetime] = Field(None)
        result_details: Dict[str, Any] = Field(default_factory=dict)
        
    class TournamentModel(BaseModel):
        """Modelo completo de torneio"""
        id: str = Field(..., description="ID único do torneio")
        name: str = Field(..., max_length=100, description="Nome do torneio")
        guild_id: str = Field(..., description="ID do servidor Discord")
        organizer_id: str = Field(..., description="ID do organizador")
        tournament_type: TournamentType = Field(default=TournamentType.SINGLE_ELIMINATION)
        game_mode: GameMode = Field(default=GameMode.SQUAD)
        status: TournamentStatus = Field(default=TournamentStatus.REGISTRATION)
        max_participants: int = Field(default=16, ge=4, le=256)
        min_participants: int = Field(default=4, ge=2)
        participants: List[ParticipantModel] = Field(default_factory=list)
        matches: Dict[str, MatchModel] = Field(default_factory=dict)
        brackets: Dict[str, Any] = Field(default_factory=dict)
        current_round: int = Field(default=0, ge=0)
        total_rounds: int = Field(default=0, ge=0)
        prize_pool: List[str] = Field(default_factory=list)
        rules: List[str] = Field(default_factory=list)
        settings: Dict[str, Any] = Field(default_factory=dict)
        created_at: datetime = Field(default_factory=datetime.now)
        registration_ends: Optional[datetime] = Field(None)
        started_at: Optional[datetime] = Field(None)
        finished_at: Optional[datetime] = Field(None)
        champion: Optional[str] = Field(None, description="ID do campeão")
        
        @validator('max_participants')
        def validate_max_participants(cls, v, values):
            min_p = values.get('min_participants', 2)
            if v < min_p:
                raise ValueError(f"Máximo de participantes deve ser >= {min_p}")
            return v
else:
    # Fallback para quando Pydantic não está disponível
    @dataclass
    class ParticipantModel:
        user_id: str
        username: str
        team_name: str
        discord_tag: Optional[str] = None
        registered_at: datetime = field(default_factory=datetime.now)
        seed: int = 0
        elo_rating: Optional[int] = None
        stats: Dict[str, Any] = field(default_factory=dict)
    
    @dataclass
    class MatchModel:
        id: str
        tournament_id: str
        round_number: int
        bracket_position: int
        player1: ParticipantModel
        player2: Optional[ParticipantModel] = None
        status: MatchStatus = MatchStatus.PENDING
        winner: Optional[str] = None
        score: Dict[str, Any] = field(default_factory=dict)
        created_at: datetime = field(default_factory=datetime.now)
        scheduled_time: Optional[datetime] = None
        started_at: Optional[datetime] = None
        finished_at: Optional[datetime] = None
        result_details: Dict[str, Any] = field(default_factory=dict)
    
    @dataclass
    class TournamentModel:
        id: str
        name: str
        guild_id: str
        organizer_id: str
        tournament_type: TournamentType = TournamentType.SINGLE_ELIMINATION
        game_mode: GameMode = GameMode.SQUAD
        status: TournamentStatus = TournamentStatus.REGISTRATION
        max_participants: int = 16
        min_participants: int = 4
        participants: List[ParticipantModel] = field(default_factory=list)
        matches: Dict[str, MatchModel] = field(default_factory=dict)
        brackets: Dict[str, Any] = field(default_factory=dict)
        current_round: int = 0
        total_rounds: int = 0
        prize_pool: List[str] = field(default_factory=list)
        rules: List[str] = field(default_factory=list)
        settings: Dict[str, Any] = field(default_factory=dict)
        created_at: datetime = field(default_factory=datetime.now)
        registration_ends: Optional[datetime] = None
        started_at: Optional[datetime] = None
        finished_at: Optional[datetime] = None
        champion: Optional[str] = None

class ModernTournamentSystem:
    """Sistema modernizado de torneios com integração aos sistemas core"""
    
    def __init__(self, bot, storage=None):
        self.bot = bot
        self.storage = storage
        
        # Inicializar sistemas core (com fallback)
        self.cache = SmartCache(namespace="tournaments") if SmartCache else {}
        self.logger = SecureLogger("TournamentSystem") if SecureLogger else None
        self.config = TypedConfig() if TypedConfig else None
        self.metrics = MetricsCollector() if MetricsCollector else None
        self.validator = DataValidator() if DataValidator else None
        self.events = EventSystem() if EventSystem else None
        self.rate_limiter = RateLimiter() if RateLimiter else None
        
        # Configurações padrão
        self.default_settings = {
            'max_participants': 64,
            'min_participants': 4,
            'registration_time_minutes': 30,
            'match_timeout_minutes': 60,
            'auto_start_enabled': True,
            'bracket_seeding': 'random',  # random, elo, manual
            'match_check_interval': 300,  # 5 minutos
            'notification_channels': [],
            'admin_roles': [],
            'participant_roles': []
        }
        
        # Cache de torneios ativos
        self.active_tournaments: Dict[str, TournamentModel] = {}
        
        # Emojis para interface
        self.emojis = {
            'trophy': '🏆',
            'medal_gold': '🥇',
            'medal_silver': '🥈',
            'medal_bronze': '🥉',
            'vs': '🆚',
            'sword': '⚔️',
            'target': '🎯',
            'fire': '🔥',
            'crown': '👑',
            'star': '⭐',
            'warning': '⚠️',
            'check': '✅',
            'cross': '❌',
            'clock': '⏰',
            'calendar': '📅',
            'users': '👥',
            'gear': '⚙️'
        }
        
        # Inicializar tarefas assíncronas
        self._background_tasks = set()
        self._start_background_tasks()
        
        if self.logger:
            self.logger.info("Sistema Modernizado de Torneios inicializado")
    
    def _start_background_tasks(self):
        """Inicia tarefas em background"""
        # Tarefa de verificação de torneios
        task = asyncio.create_task(self._tournament_monitor())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        # Tarefa de limpeza de cache
        if self.cache and hasattr(self.cache, 'cleanup'):
            task = asyncio.create_task(self._cache_cleanup())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
    
    async def _tournament_monitor(self):
        """Monitor de torneios em background"""
        while True:
            try:
                await self._check_tournament_timeouts()
                await self._auto_advance_matches()
                await self._send_scheduled_notifications()
                await asyncio.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro no monitor de torneios: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos em caso de erro
    
    async def _cache_cleanup(self):
        """Limpeza periódica do cache"""
        while True:
            try:
                if hasattr(self.cache, 'cleanup'):
                    await self.cache.cleanup()
                await asyncio.sleep(3600)  # Limpar a cada hora
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro na limpeza de cache: {e}")
                await asyncio.sleep(1800)  # Tentar novamente em 30 minutos
    
    async def create_tournament(
        self,
        guild_id: str,
        organizer_id: str,
        name: str,
        tournament_type: TournamentType = TournamentType.SINGLE_ELIMINATION,
        game_mode: GameMode = GameMode.SQUAD,
        max_participants: int = 16,
        **kwargs
    ) -> Optional[TournamentModel]:
        """Cria um novo torneio"""
        try:
            # Rate limiting
            if self.rate_limiter:
                if not await self.rate_limiter.check_rate_limit(
                    f"create_tournament:{organizer_id}", 
                    max_requests=3, 
                    window_seconds=3600
                ):
                    raise ValueError("Limite de criação de torneios excedido")
            
            # Validar dados de entrada
            if self.validator:
                validation_data = {
                    'guild_id': guild_id,
                    'organizer_id': organizer_id,
                    'name': name,
                    'max_participants': max_participants
                }
                if not await self.validator.validate_tournament_data(validation_data):
                    raise ValueError("Dados de torneio inválidos")
            
            # Gerar ID único
            tournament_id = f"tournament_{guild_id}_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
            
            # Configurações do torneio
            settings = self.default_settings.copy()
            settings.update(kwargs.get('settings', {}))
            
            # Criar modelo do torneio
            tournament_data = {
                'id': tournament_id,
                'name': name[:100],  # Limitar tamanho
                'guild_id': guild_id,
                'organizer_id': organizer_id,
                'tournament_type': tournament_type,
                'game_mode': game_mode,
                'max_participants': min(max_participants, settings['max_participants']),
                'min_participants': max(kwargs.get('min_participants', 4), settings['min_participants']),
                'prize_pool': kwargs.get('prize_pool', []),
                'rules': kwargs.get('rules', self._get_default_rules()),
                'settings': settings,
                'registration_ends': datetime.now() + timedelta(minutes=settings['registration_time_minutes'])
            }
            
            tournament = TournamentModel(**tournament_data)
            
            # Salvar no cache
            self.active_tournaments[tournament_id] = tournament
            
            # Salvar no storage persistente
            if self.storage:
                await self._save_tournament_to_storage(tournament)
            
            # Cache inteligente
            if self.cache and hasattr(self.cache, 'set'):
                await self.cache.set(
                    f"tournament:{tournament_id}",
                    tournament,
                    ttl=86400  # 24 horas
                )
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournaments_created')
                await self.metrics.gauge('active_tournaments', len(self.active_tournaments))
            
            # Evento
            if self.events:
                await self.events.emit('tournament_created', {
                    'tournament_id': tournament_id,
                    'guild_id': guild_id,
                    'organizer_id': organizer_id,
                    'name': name
                })
            
            if self.logger:
                self.logger.info(
                    f"Torneio criado: {name} ({tournament_id})",
                    extra={
                        'tournament_id': tournament_id,
                        'guild_id': guild_id,
                        'organizer_id': organizer_id
                    }
                )
            
            return tournament
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao criar torneio: {e}")
            if self.metrics:
                await self.metrics.increment('tournament_creation_errors')
            raise
    
    async def register_participant(
        self,
        tournament_id: str,
        user_id: str,
        username: str,
        team_name: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Registra um participante no torneio"""
        try:
            # Rate limiting
            if self.rate_limiter:
                if not await self.rate_limiter.check_rate_limit(
                    f"register_participant:{user_id}",
                    max_requests=5,
                    window_seconds=300
                ):
                    return False
            
            tournament = await self._get_tournament(tournament_id)
            if not tournament:
                return False
            
            # Verificar se inscrições estão abertas
            if tournament.status != TournamentStatus.REGISTRATION:
                return False
            
            # Verificar se já está registrado
            for participant in tournament.participants:
                if participant.user_id == user_id:
                    return False
            
            # Verificar limite de participantes
            if len(tournament.participants) >= tournament.max_participants:
                return False
            
            # Criar participante
            participant_data = {
                'user_id': user_id,
                'username': username[:50],
                'team_name': (team_name or f"Team {username}")[:30],
                'discord_tag': kwargs.get('discord_tag'),
                'seed': len(tournament.participants) + 1,
                'elo_rating': kwargs.get('elo_rating'),
                'stats': {
                    'matches_played': 0,
                    'matches_won': 0,
                    'matches_lost': 0,
                    'kills': 0,
                    'placement_points': 0,
                    'total_damage': 0
                }
            }
            
            participant = ParticipantModel(**participant_data)
            tournament.participants.append(participant)
            
            # Atualizar cache e storage
            await self._update_tournament(tournament)
            
            # Verificar conquistas
            await self._check_tournament_achievements(user_id, 'participation')
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournament_registrations')
            
            # Evento
            if self.events:
                await self.events.emit('participant_registered', {
                    'tournament_id': tournament_id,
                    'user_id': user_id,
                    'username': username,
                    'participant_count': len(tournament.participants)
                })
            
            # Auto-start se atingir o máximo
            if (len(tournament.participants) >= tournament.max_participants and 
                tournament.settings.get('auto_start_enabled', True)):
                await self.start_tournament(tournament_id)
            
            if self.logger:
                self.logger.info(
                    f"Participante registrado: {username} no torneio {tournament_id}",
                    extra={
                        'tournament_id': tournament_id,
                        'user_id': user_id,
                        'participant_count': len(tournament.participants)
                    }
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao registrar participante: {e}")
            return False
    
    async def start_tournament(self, tournament_id: str) -> bool:
        """Inicia um torneio e gera os brackets"""
        try:
            tournament = await self._get_tournament(tournament_id)
            if not tournament:
                return False
            
            # Verificar se pode iniciar
            if tournament.status != TournamentStatus.REGISTRATION:
                return False
            
            if len(tournament.participants) < tournament.min_participants:
                return False
            
            # Atualizar status
            tournament.status = TournamentStatus.STARTING
            tournament.started_at = datetime.now()
            
            # Gerar brackets baseado no tipo de torneio
            if tournament.tournament_type == TournamentType.SINGLE_ELIMINATION:
                await self._generate_single_elimination_bracket(tournament)
            elif tournament.tournament_type == TournamentType.DOUBLE_ELIMINATION:
                await self._generate_double_elimination_bracket(tournament)
            elif tournament.tournament_type == TournamentType.ROUND_ROBIN:
                await self._generate_round_robin_bracket(tournament)
            elif tournament.tournament_type == TournamentType.SWISS:
                await self._generate_swiss_bracket(tournament)
            else:
                await self._generate_single_elimination_bracket(tournament)  # Fallback
            
            # Atualizar status para em andamento
            tournament.status = TournamentStatus.IN_PROGRESS
            
            # Atualizar cache e storage
            await self._update_tournament(tournament)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournaments_started')
                await self.metrics.histogram('tournament_participants', len(tournament.participants))
            
            # Evento
            if self.events:
                await self.events.emit('tournament_started', {
                    'tournament_id': tournament_id,
                    'participant_count': len(tournament.participants),
                    'tournament_type': tournament.tournament_type.value
                })
            
            if self.logger:
                self.logger.info(
                    f"Torneio iniciado: {tournament_id} com {len(tournament.participants)} participantes",
                    extra={
                        'tournament_id': tournament_id,
                        'participant_count': len(tournament.participants),
                        'tournament_type': tournament.tournament_type.value
                    }
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao iniciar torneio: {e}")
            return False
    
    async def _generate_single_elimination_bracket(self, tournament: TournamentModel):
        """Gera bracket de eliminação simples"""
        participants = tournament.participants.copy()
        
        # Aplicar seeding
        if tournament.settings.get('bracket_seeding') == 'elo' and all(p.elo_rating for p in participants):
            participants.sort(key=lambda p: p.elo_rating or 0, reverse=True)
        elif tournament.settings.get('bracket_seeding') == 'random':
            random.shuffle(participants)
        
        # Calcular próxima potência de 2
        participant_count = len(participants)
        bracket_size = 2 ** math.ceil(math.log2(participant_count))
        
        # Calcular número de rodadas
        tournament.total_rounds = math.ceil(math.log2(participant_count))
        tournament.current_round = 1
        
        # Gerar primeira rodada
        matches = {}
        match_count = 0
        
        for i in range(0, len(participants), 2):
            match_count += 1
            match_id = f"match_1_{match_count}"
            
            if i + 1 < len(participants):
                # Partida normal
                match_data = {
                    'id': match_id,
                    'tournament_id': tournament.id,
                    'round_number': 1,
                    'bracket_position': match_count - 1,
                    'player1': participants[i],
                    'player2': participants[i + 1],
                    'status': MatchStatus.READY
                }
            else:
                # Bye (passa automaticamente)
                match_data = {
                    'id': match_id,
                    'tournament_id': tournament.id,
                    'round_number': 1,
                    'bracket_position': match_count - 1,
                    'player1': participants[i],
                    'player2': None,
                    'status': MatchStatus.FINISHED,
                    'winner': participants[i].user_id,
                    'finished_at': datetime.now()
                }
            
            matches[match_id] = MatchModel(**match_data)
        
        tournament.matches = matches
        
        # Gerar estrutura de brackets
        tournament.brackets = {
            'type': 'single_elimination',
            'size': bracket_size,
            'rounds': tournament.total_rounds,
            'participants': [p.user_id for p in participants]
        }
    
    async def _generate_double_elimination_bracket(self, tournament: TournamentModel):
        """Gera bracket de eliminação dupla"""
        # Implementação simplificada - pode ser expandida
        await self._generate_single_elimination_bracket(tournament)
        tournament.brackets['type'] = 'double_elimination'
        # TODO: Implementar bracket de perdedores
    
    async def _generate_round_robin_bracket(self, tournament: TournamentModel):
        """Gera bracket round robin"""
        participants = tournament.participants.copy()
        participant_count = len(participants)
        
        # Calcular número de rodadas (todos contra todos)
        tournament.total_rounds = participant_count - 1 if participant_count % 2 == 0 else participant_count
        tournament.current_round = 1
        
        matches = {}
        match_count = 0
        
        # Gerar todas as partidas
        for i in range(participant_count):
            for j in range(i + 1, participant_count):
                match_count += 1
                match_id = f"match_rr_{match_count}"
                
                match_data = {
                    'id': match_id,
                    'tournament_id': tournament.id,
                    'round_number': 1,  # Todas na mesma rodada inicialmente
                    'bracket_position': match_count - 1,
                    'player1': participants[i],
                    'player2': participants[j],
                    'status': MatchStatus.READY
                }
                
                matches[match_id] = MatchModel(**match_data)
        
        tournament.matches = matches
        tournament.brackets = {
            'type': 'round_robin',
            'total_matches': match_count,
            'participants': [p.user_id for p in participants]
        }
    
    async def _generate_swiss_bracket(self, tournament: TournamentModel):
        """Gera bracket sistema suíço"""
        # Implementação simplificada
        await self._generate_round_robin_bracket(tournament)
        tournament.brackets['type'] = 'swiss'
        # TODO: Implementar emparelhamento suíço
    
    def _get_default_rules(self) -> List[str]:
        """Retorna as regras padrão do torneio"""
        return [
            f"{self.emojis['target']} **Modo de Jogo**: PUBG Squad/Duo/Solo",
            f"{self.emojis['clock']} **Tempo Limite**: 60 minutos por partida",
            f"{self.emojis['trophy']} **Sistema**: Eliminação simples",
            f"{self.emojis['star']} **Pontuação**: Kills + Placement",
            f"{self.emojis['cross']} **Proibido**: Cheats, exploits, toxicidade",
            f"{self.emojis['gear']} **Comprovação**: Screenshots obrigatórios",
            f"{self.emojis['warning']} **Disputas**: Decisão dos organizadores",
            f"{self.emojis['crown']} **Prêmios**: Conforme disponibilidade"
        ]
    
    async def _get_tournament(self, tournament_id: str) -> Optional[TournamentModel]:
        """Obtém um torneio do cache ou storage"""
        # Tentar cache primeiro
        tournament = self.active_tournaments.get(tournament_id)
        if tournament:
            return tournament
        
        # Tentar cache inteligente
        if self.cache and hasattr(self.cache, 'get'):
            tournament = await self.cache.get(f"tournament:{tournament_id}")
            if tournament:
                self.active_tournaments[tournament_id] = tournament
                return tournament
        
        # Tentar storage persistente
        if self.storage:
            tournament_data = await self._load_tournament_from_storage(tournament_id)
            if tournament_data:
                tournament = TournamentModel(**tournament_data)
                self.active_tournaments[tournament_id] = tournament
                return tournament
        
        return None
    
    async def _update_tournament(self, tournament: TournamentModel):
        """Atualiza torneio no cache e storage"""
        # Atualizar cache local
        self.active_tournaments[tournament.id] = tournament
        
        # Atualizar cache inteligente
        if self.cache and hasattr(self.cache, 'set'):
            await self.cache.set(
                f"tournament:{tournament.id}",
                tournament,
                ttl=86400
            )
        
        # Atualizar storage persistente
        if self.storage:
            await self._save_tournament_to_storage(tournament)
    
    async def _save_tournament_to_storage(self, tournament: TournamentModel):
        """Salva torneio no storage persistente"""
        try:
            if hasattr(self.storage, 'update_tournament'):
                # Converter para dict se necessário
                tournament_dict = tournament.__dict__ if hasattr(tournament, '__dict__') else tournament
                await self.storage.update_tournament(tournament.id, tournament_dict)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao salvar torneio no storage: {e}")
    
    async def _load_tournament_from_storage(self, tournament_id: str) -> Optional[Dict]:
        """Carrega torneio do storage persistente"""
        try:
            if hasattr(self.storage, 'get_tournament'):
                return await self.storage.get_tournament(tournament_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar torneio do storage: {e}")
        return None
    
    async def _check_tournament_achievements(self, user_id: str, achievement_type: str):
        """Verifica conquistas relacionadas a torneios"""
        try:
            if hasattr(self.bot, 'achievement_system'):
                # Contar participações em torneios
                tournament_count = 0
                wins_count = 0
                
                for tournament in self.active_tournaments.values():
                    # Verificar participação
                    for participant in tournament.participants:
                        if participant.user_id == user_id:
                            tournament_count += 1
                            break
                    
                    # Verificar vitórias
                    if tournament.champion == user_id:
                        wins_count += 1
                
                tournament_stats = {
                    'tournaments_participated': tournament_count,
                    'tournament_wins': wins_count
                }
                
                await self.bot.achievement_system.check_achievements(user_id, tournament_stats)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao verificar conquistas de torneio: {e}")
    
    async def _check_tournament_timeouts(self):
        """Verifica timeouts de torneios e partidas"""
        current_time = datetime.now()
        
        for tournament in list(self.active_tournaments.values()):
            try:
                # Verificar timeout de registro
                if (tournament.status == TournamentStatus.REGISTRATION and 
                    tournament.registration_ends and 
                    current_time > tournament.registration_ends):
                    
                    if len(tournament.participants) >= tournament.min_participants:
                        await self.start_tournament(tournament.id)
                    else:
                        await self.cancel_tournament(tournament.id, "Participantes insuficientes")
                
                # Verificar timeout de partidas
                timeout_minutes = tournament.settings.get('match_timeout_minutes', 60)
                for match in tournament.matches.values():
                    if (match.status == MatchStatus.IN_PROGRESS and 
                        match.started_at and 
                        current_time > match.started_at + timedelta(minutes=timeout_minutes)):
                        
                        # Marcar como disputada
                        match.status = MatchStatus.DISPUTED
                        await self._update_tournament(tournament)
                        
                        if self.logger:
                            self.logger.warning(
                                f"Partida {match.id} marcada como disputada por timeout",
                                extra={'tournament_id': tournament.id, 'match_id': match.id}
                            )
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro ao verificar timeout do torneio {tournament.id}: {e}")
    
    async def _auto_advance_matches(self):
        """Avança automaticamente partidas prontas"""
        for tournament in list(self.active_tournaments.values()):
            try:
                if tournament.status != TournamentStatus.IN_PROGRESS:
                    continue
                
                # Verificar se a rodada atual terminou
                current_round_matches = [
                    m for m in tournament.matches.values() 
                    if m.round_number == tournament.current_round
                ]
                
                if current_round_matches and all(
                    m.status in [MatchStatus.FINISHED, MatchStatus.WALKOVER] 
                    for m in current_round_matches
                ):
                    await self._advance_to_next_round(tournament)
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erro ao avançar partidas do torneio {tournament.id}: {e}")
    
    async def _advance_to_next_round(self, tournament: TournamentModel):
        """Avança para a próxima rodada"""
        try:
            # Verificar se é a final
            if tournament.current_round >= tournament.total_rounds:
                await self._finish_tournament(tournament)
                return
            
            # Obter vencedores da rodada atual
            current_round_matches = [
                m for m in tournament.matches.values() 
                if m.round_number == tournament.current_round
            ]
            
            winners = []
            for match in current_round_matches:
                if match.winner:
                    winner_participant = None
                    for participant in tournament.participants:
                        if participant.user_id == match.winner:
                            winner_participant = participant
                            break
                    if winner_participant:
                        winners.append(winner_participant)
            
            if len(winners) < 2:
                # Não há vencedores suficientes, finalizar torneio
                await self._finish_tournament(tournament)
                return
            
            # Avançar para próxima rodada
            tournament.current_round += 1
            next_round = tournament.current_round
            
            # Gerar partidas da próxima rodada
            new_matches = {}
            match_count = 0
            
            for i in range(0, len(winners), 2):
                if i + 1 < len(winners):
                    match_count += 1
                    match_id = f"match_{next_round}_{match_count}"
                    
                    match_data = {
                        'id': match_id,
                        'tournament_id': tournament.id,
                        'round_number': next_round,
                        'bracket_position': match_count - 1,
                        'player1': winners[i],
                        'player2': winners[i + 1],
                        'status': MatchStatus.READY
                    }
                    
                    new_matches[match_id] = MatchModel(**match_data)
            
            # Adicionar novas partidas
            tournament.matches.update(new_matches)
            
            # Atualizar torneio
            await self._update_tournament(tournament)
            
            # Evento
            if self.events:
                await self.events.emit('tournament_round_advanced', {
                    'tournament_id': tournament.id,
                    'round_number': next_round,
                    'matches_count': len(new_matches)
                })
            
            if self.logger:
                self.logger.info(
                    f"Torneio {tournament.id} avançou para rodada {next_round}",
                    extra={
                        'tournament_id': tournament.id,
                        'round_number': next_round,
                        'winners_count': len(winners)
                    }
                )
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao avançar rodada do torneio {tournament.id}: {e}")
    
    async def _finish_tournament(self, tournament: TournamentModel):
        """Finaliza um torneio"""
        try:
            tournament.status = TournamentStatus.FINISHED
            tournament.finished_at = datetime.now()
            
            # Determinar campeão
            final_matches = [
                m for m in tournament.matches.values() 
                if m.round_number == tournament.total_rounds and m.status == MatchStatus.FINISHED
            ]
            
            if final_matches and final_matches[0].winner:
                tournament.champion = final_matches[0].winner
                
                # Verificar conquistas do campeão
                await self._check_tournament_achievements(tournament.champion, 'victory')
            
            # Atualizar torneio
            await self._update_tournament(tournament)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournaments_finished')
                duration = (tournament.finished_at - tournament.started_at).total_seconds()
                await self.metrics.histogram('tournament_duration_seconds', duration)
            
            # Evento
            if self.events:
                await self.events.emit('tournament_finished', {
                    'tournament_id': tournament.id,
                    'champion': tournament.champion,
                    'participant_count': len(tournament.participants),
                    'duration_seconds': (tournament.finished_at - tournament.started_at).total_seconds()
                })
            
            if self.logger:
                self.logger.info(
                    f"Torneio finalizado: {tournament.id}",
                    extra={
                        'tournament_id': tournament.id,
                        'champion': tournament.champion,
                        'participant_count': len(tournament.participants)
                    }
                )
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao finalizar torneio {tournament.id}: {e}")
    
    async def cancel_tournament(self, tournament_id: str, reason: str = "Cancelado") -> bool:
        """Cancela um torneio"""
        try:
            tournament = await self._get_tournament(tournament_id)
            if not tournament:
                return False
            
            tournament.status = TournamentStatus.CANCELLED
            tournament.finished_at = datetime.now()
            
            # Adicionar razão do cancelamento
            if not hasattr(tournament, 'cancel_reason'):
                tournament.cancel_reason = reason
            
            await self._update_tournament(tournament)
            
            # Métricas
            if self.metrics:
                await self.metrics.increment('tournaments_cancelled')
            
            # Evento
            if self.events:
                await self.events.emit('tournament_cancelled', {
                    'tournament_id': tournament_id,
                    'reason': reason
                })
            
            if self.logger:
                self.logger.info(
                    f"Torneio cancelado: {tournament_id} - {reason}",
                    extra={'tournament_id': tournament_id, 'reason': reason}
                )
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao cancelar torneio: {e}")
            return False
    
    async def _send_scheduled_notifications(self):
        """Envia notificações programadas"""
        # Implementação de notificações pode ser adicionada aqui
        pass
    
    async def get_active_tournaments(self, guild_id: str) -> List[TournamentModel]:
        """Retorna torneios ativos de um servidor"""
        return [
            tournament for tournament in self.active_tournaments.values()
            if tournament.guild_id == guild_id and 
            tournament.status in [
                TournamentStatus.REGISTRATION,
                TournamentStatus.STARTING,
                TournamentStatus.IN_PROGRESS,
                TournamentStatus.PAUSED
            ]
        ]
    
    async def get_tournament_stats(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas detalhadas de um torneio"""
        tournament = await self._get_tournament(tournament_id)
        if not tournament:
            return None
        
        stats = {
            'tournament_id': tournament.id,
            'name': tournament.name,
            'status': tournament.status.value,
            'participant_count': len(tournament.participants),
            'matches_total': len(tournament.matches),
            'matches_finished': len([
                m for m in tournament.matches.values() 
                if m.status == MatchStatus.FINISHED
            ]),
            'current_round': tournament.current_round,
            'total_rounds': tournament.total_rounds,
            'created_at': tournament.created_at,
            'started_at': tournament.started_at,
            'finished_at': tournament.finished_at,
            'champion': tournament.champion
        }
        
        # Estatísticas de participantes
        if tournament.participants:
            stats['participants'] = [
                {
                    'user_id': p.user_id,
                    'username': p.username,
                    'team_name': p.team_name,
                    'stats': p.stats
                }
                for p in tournament.participants
            ]
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde do sistema de torneios"""
        try:
            health = {
                'status': 'healthy',
                'active_tournaments': len(self.active_tournaments),
                'background_tasks': len(self._background_tasks),
                'systems': {
                    'cache': self.cache is not None,
                    'logger': self.logger is not None,
                    'metrics': self.metrics is not None,
                    'events': self.events is not None,
                    'rate_limiter': self.rate_limiter is not None,
                    'storage': self.storage is not None
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Verificar cache
            if self.cache and hasattr(self.cache, 'health_check'):
                health['cache_health'] = await self.cache.health_check()
            
            return health
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Limpeza de recursos"""
        try:
            # Cancelar tarefas em background
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            
            # Aguardar conclusão das tarefas
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Limpar cache
            if self.cache and hasattr(self.cache, 'clear'):
                await self.cache.clear()
            
            if self.logger:
                self.logger.info("Sistema de torneios finalizado")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro na limpeza do sistema de torneios: {e}")