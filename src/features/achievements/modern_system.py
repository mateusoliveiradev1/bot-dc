#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Achievements e Badges Modernizado - Hawk Bot
Sistema avançado de conquistas, badges e gamificação com async/await

Autor: Hawk Bot Development Team
Versão: 3.0.0 - Modernizado
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
from pathlib import Path

# Importar sistemas core
try:
    from ...core.secure_logger import SecureLogger
    from ...core.smart_cache import SmartCache
    from ...core.metrics import increment_counter, record_timer, record_gauge
    from ...core.data_validator import validate_input, ValidationSchema
    from ...core.event_system import emit_event, EventData
    from ...core.rate_limiter import rate_limit
    from ...core.typed_config import TypedConfig
except ImportError:
    SecureLogger = None
    SmartCache = None
    increment_counter = None
    record_timer = None
    record_gauge = None
    validate_input = None
    ValidationSchema = None
    emit_event = None
    EventData = None
    rate_limit = None
    TypedConfig = None

# Importar Pydantic com fallback
try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    BaseModel = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f

logger = logging.getLogger('HawkBot.ModernAchievements')

# ==================== ENUMS E TIPOS ====================

class AchievementRarity(Enum):
    """Raridade das conquistas"""
    COMMON = "comum"
    RARE = "raro"
    EPIC = "épico"
    LEGENDARY = "lendário"
    MYTHIC = "mítico"

class AchievementCategory(Enum):
    """Categorias de conquistas"""
    COMBAT = "combate"
    SURVIVAL = "sobrevivencia"
    TEAMWORK = "equipe"
    PROGRESSION = "progressao"
    SPECIAL = "especial"
    TOURNAMENT = "torneio"
    CONTENT = "conteudo"
    SOCIAL = "social"

class BadgeType(Enum):
    """Tipos de badges"""
    ACHIEVEMENT = "conquista"
    RANK = "rank"
    SEASONAL = "temporada"
    EVENT = "evento"
    CUSTOM = "personalizado"

# ==================== MODELOS DE DADOS ====================

@dataclass
class AchievementRequirement:
    """Requisito para uma conquista"""
    type: str
    value: Union[int, float, str]
    operator: str = ">="  # >=, >, ==, <, <=
    additional_params: Dict[str, Any] = field(default_factory=dict)

if BaseModel != object:
    class AchievementModel(BaseModel):
        """Modelo Pydantic para conquista"""
        id: str = Field(..., description="ID único da conquista")
        name: str = Field(..., description="Nome da conquista")
        description: str = Field(..., description="Descrição da conquista")
        icon: str = Field(..., description="Emoji/ícone da conquista")
        category: AchievementCategory = Field(..., description="Categoria")
        rarity: AchievementRarity = Field(default=AchievementRarity.COMMON)
        points: int = Field(default=10, ge=1, le=1000)
        requirements: List[Dict[str, Any]] = Field(default_factory=list)
        hidden: bool = Field(default=False, description="Conquista oculta")
        seasonal: bool = Field(default=False, description="Conquista sazonal")
        created_at: datetime = Field(default_factory=datetime.now)
        
        @validator('points')
        def validate_points(cls, v, values):
            """Validar pontos baseado na raridade"""
            rarity = values.get('rarity', AchievementRarity.COMMON)
            min_points = {
                AchievementRarity.COMMON: 5,
                AchievementRarity.RARE: 15,
                AchievementRarity.EPIC: 30,
                AchievementRarity.LEGENDARY: 75,
                AchievementRarity.MYTHIC: 150
            }
            if v < min_points.get(rarity, 5):
                raise ValueError(f"Pontos insuficientes para raridade {rarity.value}")
            return v
    
    class BadgeModel(BaseModel):
        """Modelo Pydantic para badge"""
        id: str = Field(..., description="ID único do badge")
        name: str = Field(..., description="Nome do badge")
        description: str = Field(..., description="Descrição do badge")
        icon: str = Field(..., description="Emoji/ícone do badge")
        color: int = Field(default=0x00FF00, description="Cor do badge")
        badge_type: BadgeType = Field(default=BadgeType.ACHIEVEMENT)
        rarity: AchievementRarity = Field(default=AchievementRarity.COMMON)
        requirements: List[Dict[str, Any]] = Field(default_factory=list)
        expires_at: Optional[datetime] = Field(default=None)
        transferable: bool = Field(default=False)
        created_at: datetime = Field(default_factory=datetime.now)
    
    class UserProgressModel(BaseModel):
        """Modelo para progresso do usuário"""
        user_id: int = Field(..., description="ID do usuário Discord")
        achievements: List[str] = Field(default_factory=list)
        badges: List[str] = Field(default_factory=list)
        total_points: int = Field(default=0, ge=0)
        level: int = Field(default=1, ge=1)
        experience: int = Field(default=0, ge=0)
        progress: Dict[str, Any] = Field(default_factory=dict)
        statistics: Dict[str, Any] = Field(default_factory=dict)
        last_updated: datetime = Field(default_factory=datetime.now)
        
        @validator('level')
        def calculate_level(cls, v, values):
            """Calcular nível baseado na experiência"""
            exp = values.get('experience', 0)
            # Fórmula: level = sqrt(exp / 100) + 1
            import math
            calculated_level = int(math.sqrt(exp / 100)) + 1
            return max(calculated_level, 1)
else:
    # Fallback para quando Pydantic não está disponível
    class AchievementModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class BadgeModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class UserProgressModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

# ==================== SISTEMA PRINCIPAL ====================

class ModernAchievementSystem:
    """Sistema modernizado de conquistas e badges"""
    
    def __init__(self, bot, config_path: Optional[str] = None):
        self.bot = bot
        self.config_path = config_path or "config/achievements.json"
        
        # Sistemas core
        if SecureLogger:
            self.logger = SecureLogger('ModernAchievements')
        else:
            self.logger = logger
        
        if SmartCache:
            self.cache = SmartCache(
                default_ttl=3600,  # 1 hora
                max_size=10000,
                cleanup_interval=300  # 5 minutos
            )
        else:
            self.cache = {}
        
        # Configuração
        self.config = self._load_config()
        
        # Armazenamento
        self.achievements: Dict[str, AchievementModel] = {}
        self.badges: Dict[str, BadgeModel] = {}
        self.user_progress: Dict[int, UserProgressModel] = {}
        
        # Métricas
        self.metrics = {
            'achievements_unlocked': 0,
            'badges_earned': 0,
            'users_active': 0,
            'total_points_awarded': 0
        }
        
        # Inicialização
        asyncio.create_task(self._initialize())
        
        self.logger.info("Sistema de conquistas modernizado inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carregar configuração do sistema"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Erro ao carregar configuração: {e}")
        
        # Configuração padrão
        return {
            "enabled": True,
            "auto_check": True,
            "check_interval_minutes": 30,
            "max_achievements_per_check": 5,
            "experience_multiplier": 1.0,
            "level_formula": "sqrt",
            "rarity_multipliers": {
                "comum": 1.0,
                "raro": 1.5,
                "épico": 2.5,
                "lendário": 4.0,
                "mítico": 6.0
            },
            "notifications": {
                "dm_on_achievement": True,
                "channel_announcements": True,
                "announcement_channel_id": None
            }
        }
    
    async def _initialize(self):
        """Inicialização assíncrona do sistema"""
        try:
            await self._load_default_achievements()
            await self._load_default_badges()
            await self._load_user_progress()
            
            # Iniciar tarefas em background
            if self.config.get("auto_check", True):
                asyncio.create_task(self._auto_check_loop())
            
            self.logger.info("Inicialização assíncrona concluída")
        
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")
    
    async def _load_default_achievements(self):
        """Carregar conquistas padrão"""
        default_achievements = [
            # Conquistas de Combate
            {
                "id": "first_kill",
                "name": "Primeira Morte",
                "description": "Consiga sua primeira eliminação",
                "icon": "🩸",
                "category": AchievementCategory.COMBAT,
                "rarity": AchievementRarity.COMMON,
                "points": 10,
                "requirements": [{"type": "kills", "value": 1, "operator": ">="}]
            },
            {
                "id": "kill_master",
                "name": "Mestre das Eliminações",
                "description": "Consiga 100 eliminações",
                "icon": "💀",
                "category": AchievementCategory.COMBAT,
                "rarity": AchievementRarity.RARE,
                "points": 50,
                "requirements": [{"type": "kills", "value": 100, "operator": ">="}]
            },
            {
                "id": "legendary_killer",
                "name": "Assassino Lendário",
                "description": "Consiga 1000 eliminações",
                "icon": "☠️",
                "category": AchievementCategory.COMBAT,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 200,
                "requirements": [{"type": "kills", "value": 1000, "operator": ">="}]
            },
            
            # Conquistas de K/D
            {
                "id": "kd_warrior",
                "name": "Guerreiro",
                "description": "Alcance K/D de 2.0 ou mais",
                "icon": "⚔️",
                "category": AchievementCategory.COMBAT,
                "rarity": AchievementRarity.RARE,
                "points": 75,
                "requirements": [{"type": "kd_ratio", "value": 2.0, "operator": ">="}]
            },
            {
                "id": "kd_legend",
                "name": "Lenda do K/D",
                "description": "Alcance K/D de 5.0 ou mais",
                "icon": "🏆",
                "category": AchievementCategory.COMBAT,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 150,
                "requirements": [{"type": "kd_ratio", "value": 5.0, "operator": ">="}]
            },
            
            # Conquistas de Vitórias
            {
                "id": "first_win",
                "name": "Primeira Vitória",
                "description": "Consiga sua primeira vitória",
                "icon": "🎉",
                "category": AchievementCategory.PROGRESSION,
                "rarity": AchievementRarity.COMMON,
                "points": 15,
                "requirements": [{"type": "wins", "value": 1, "operator": ">="}]
            },
            {
                "id": "win_streak_5",
                "name": "Sequência Vitoriosa",
                "description": "Vença 5 partidas seguidas",
                "icon": "🔥",
                "category": AchievementCategory.SPECIAL,
                "rarity": AchievementRarity.EPIC,
                "points": 100,
                "requirements": [{"type": "win_streak", "value": 5, "operator": ">="}]
            },
            
            # Conquistas de Equipe
            {
                "id": "team_player",
                "name": "Jogador de Equipe",
                "description": "Consiga 50 assists",
                "icon": "🤝",
                "category": AchievementCategory.TEAMWORK,
                "rarity": AchievementRarity.RARE,
                "points": 60,
                "requirements": [{"type": "assists", "value": 50, "operator": ">="}]
            },
            {
                "id": "medic",
                "name": "Médico de Campo",
                "description": "Reviva 25 companheiros",
                "icon": "🏥",
                "category": AchievementCategory.TEAMWORK,
                "rarity": AchievementRarity.EPIC,
                "points": 80,
                "requirements": [{"type": "revives", "value": 25, "operator": ">="}]
            },
            
            # Conquistas de Torneios
            {
                "id": "tournament_participant",
                "name": "Competidor",
                "description": "Participe de um torneio",
                "icon": "🎮",
                "category": AchievementCategory.TOURNAMENT,
                "rarity": AchievementRarity.COMMON,
                "points": 25,
                "requirements": [{"type": "tournaments_participated", "value": 1, "operator": ">="}]
            },
            {
                "id": "tournament_champion",
                "name": "Campeão",
                "description": "Vença um torneio",
                "icon": "👑",
                "category": AchievementCategory.TOURNAMENT,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 250,
                "requirements": [{"type": "tournament_wins", "value": 1, "operator": ">="}]
            },
            
            # Conquistas Especiais
            {
                "id": "completionist",
                "name": "Completista",
                "description": "Desbloqueie 50 conquistas",
                "icon": "🌟",
                "category": AchievementCategory.SPECIAL,
                "rarity": AchievementRarity.MYTHIC,
                "points": 500,
                "requirements": [{"type": "achievements_unlocked", "value": 50, "operator": ">="}]
            }
        ]
        
        for ach_data in default_achievements:
            try:
                if BaseModel != object:
                    achievement = AchievementModel(**ach_data)
                else:
                    achievement = AchievementModel(**ach_data)
                
                self.achievements[achievement.id] = achievement
            except Exception as e:
                self.logger.error(f"Erro ao carregar conquista {ach_data.get('id', 'unknown')}: {e}")
        
        self.logger.info(f"Carregadas {len(self.achievements)} conquistas padrão")
    
    async def _load_default_badges(self):
        """Carregar badges padrão"""
        default_badges = [
            # Badges de Rank
            {
                "id": "bronze_rank",
                "name": "Bronze",
                "description": "Alcançou o rank Bronze",
                "icon": "🥉",
                "color": 0xCD7F32,
                "badge_type": BadgeType.RANK,
                "rarity": AchievementRarity.COMMON,
                "requirements": [{"type": "rank", "value": "bronze", "operator": "=="}]
            },
            {
                "id": "silver_rank",
                "name": "Prata",
                "description": "Alcançou o rank Prata",
                "icon": "🥈",
                "color": 0xC0C0C0,
                "badge_type": BadgeType.RANK,
                "rarity": AchievementRarity.RARE,
                "requirements": [{"type": "rank", "value": "silver", "operator": "=="}]
            },
            {
                "id": "gold_rank",
                "name": "Ouro",
                "description": "Alcançou o rank Ouro",
                "icon": "🥇",
                "color": 0xFFD700,
                "badge_type": BadgeType.RANK,
                "rarity": AchievementRarity.EPIC,
                "requirements": [{"type": "rank", "value": "gold", "operator": "=="}]
            },
            
            # Badges de Eventos
            {
                "id": "beta_tester",
                "name": "Beta Tester",
                "description": "Participou da fase beta",
                "icon": "🧪",
                "color": 0x9932CC,
                "badge_type": BadgeType.EVENT,
                "rarity": AchievementRarity.LEGENDARY,
                "requirements": [{"type": "beta_participation", "value": True, "operator": "=="}]
            },
            {
                "id": "founder",
                "name": "Fundador",
                "description": "Membro fundador do clã",
                "icon": "👑",
                "color": 0xFF6B35,
                "badge_type": BadgeType.EVENT,
                "rarity": AchievementRarity.MYTHIC,
                "requirements": [{"type": "founder_status", "value": True, "operator": "=="}]
            }
        ]
        
        for badge_data in default_badges:
            try:
                if BaseModel != object:
                    badge = BadgeModel(**badge_data)
                else:
                    badge = BadgeModel(**badge_data)
                
                self.badges[badge.id] = badge
            except Exception as e:
                self.logger.error(f"Erro ao carregar badge {badge_data.get('id', 'unknown')}: {e}")
        
        self.logger.info(f"Carregados {len(self.badges)} badges padrão")
    
    async def _load_user_progress(self):
        """Carregar progresso dos usuários"""
        try:
            # Aqui você carregaria do banco de dados ou arquivo
            # Por enquanto, inicializar vazio
            self.user_progress = {}
            self.logger.info("Progresso dos usuários carregado")
        except Exception as e:
            self.logger.error(f"Erro ao carregar progresso dos usuários: {e}")
    
    async def _auto_check_loop(self):
        """Loop automático de verificação de conquistas"""
        interval = self.config.get("check_interval_minutes", 30) * 60
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                if not self.config.get("auto_check", True):
                    continue
                
                # Verificar conquistas para usuários ativos
                active_users = await self._get_active_users()
                
                for user_id in active_users:
                    try:
                        await self.check_user_achievements(user_id)
                    except Exception as e:
                        self.logger.error(f"Erro ao verificar conquistas do usuário {user_id}: {e}")
                
                self.logger.debug(f"Verificação automática concluída para {len(active_users)} usuários")
            
            except Exception as e:
                self.logger.error(f"Erro no loop de verificação automática: {e}")
    
    async def _get_active_users(self) -> List[int]:
        """Obter lista de usuários ativos"""
        # Implementar lógica para obter usuários ativos
        # Por exemplo, usuários que jogaram nas últimas 24h
        return list(self.user_progress.keys())[:50]  # Limitar a 50 por verificação
    
    async def check_user_achievements(self, user_id: int, stats: Optional[Dict[str, Any]] = None) -> List[AchievementModel]:
        """Verificar e desbloquear conquistas para um usuário"""
        try:
            if increment_counter:
                increment_counter('achievement_checks_total')
            
            # Obter progresso do usuário
            user_progress = await self.get_user_progress(user_id)
            
            # Obter estatísticas se não fornecidas
            if stats is None:
                stats = await self._get_user_stats(user_id)
            
            unlocked_achievements = []
            max_per_check = self.config.get("max_achievements_per_check", 5)
            
            for achievement_id, achievement in self.achievements.items():
                if len(unlocked_achievements) >= max_per_check:
                    break
                
                if achievement_id in user_progress.achievements:
                    continue  # Já desbloqueada
                
                if await self._check_achievement_requirements(achievement, stats, user_progress):
                    # Desbloquear conquista
                    await self._unlock_achievement(user_id, achievement)
                    unlocked_achievements.append(achievement)
            
            # Atualizar métricas
            if unlocked_achievements:
                if increment_counter:
                    increment_counter('achievements_unlocked_total', len(unlocked_achievements))
                
                if record_gauge:
                    record_gauge('user_total_achievements', len(user_progress.achievements) + len(unlocked_achievements))
            
            return unlocked_achievements
        
        except Exception as e:
            self.logger.error(f"Erro ao verificar conquistas do usuário {user_id}: {e}")
            return []
    
    async def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas do usuário"""
        # Cache key
        cache_key = f"user_stats_{user_id}"
        
        if SmartCache and hasattr(self.cache, 'get'):
            cached_stats = await self.cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        # Obter estatísticas do banco de dados ou API
        stats = {
            'kills': 0,
            'deaths': 0,
            'wins': 0,
            'matches_played': 0,
            'kd_ratio': 0.0,
            'win_rate': 0.0,
            'assists': 0,
            'revives': 0,
            'tournaments_participated': 0,
            'tournament_wins': 0,
            'achievements_unlocked': 0,
            'rank': 'unranked'
        }
        
        # Aqui você integraria com seu sistema de estatísticas
        # Por exemplo, PUBG API, banco de dados, etc.
        
        # Salvar no cache
        if SmartCache and hasattr(self.cache, 'set'):
            await self.cache.set(cache_key, stats, ttl=1800)  # 30 minutos
        
        return stats
    
    async def _check_achievement_requirements(self, achievement: AchievementModel, 
                                           stats: Dict[str, Any], 
                                           user_progress: 'UserProgressModel') -> bool:
        """Verificar se os requisitos de uma conquista foram atendidos"""
        try:
            if not hasattr(achievement, 'requirements'):
                return False
            
            requirements = achievement.requirements if hasattr(achievement, 'requirements') else []
            
            for req in requirements:
                req_type = req.get('type')
                req_value = req.get('value')
                req_operator = req.get('operator', '>=')
                
                current_value = stats.get(req_type, 0)
                
                # Verificar operador
                if req_operator == '>=':
                    if not (current_value >= req_value):
                        return False
                elif req_operator == '>':
                    if not (current_value > req_value):
                        return False
                elif req_operator == '==':
                    if not (current_value == req_value):
                        return False
                elif req_operator == '<=':
                    if not (current_value <= req_value):
                        return False
                elif req_operator == '<':
                    if not (current_value < req_value):
                        return False
                else:
                    return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao verificar requisitos da conquista {achievement.id}: {e}")
            return False
    
    async def _unlock_achievement(self, user_id: int, achievement: AchievementModel):
        """Desbloquear uma conquista para o usuário"""
        try:
            user_progress = await self.get_user_progress(user_id)
            
            # Adicionar conquista
            user_progress.achievements.append(achievement.id)
            
            # Calcular pontos com multiplicador de raridade
            rarity_multiplier = self.config.get("rarity_multipliers", {}).get(
                achievement.rarity.value if hasattr(achievement, 'rarity') else 'comum', 1.0
            )
            points_earned = int(achievement.points * rarity_multiplier)
            
            # Atualizar pontos e experiência
            user_progress.total_points += points_earned
            user_progress.experience += points_earned * self.config.get("experience_multiplier", 1.0)
            
            # Recalcular nível
            user_progress.level = self._calculate_level(user_progress.experience)
            
            # Atualizar timestamp
            user_progress.last_updated = datetime.now()
            
            # Salvar progresso
            await self._save_user_progress(user_id, user_progress)
            
            # Emitir evento
            if emit_event:
                await emit_event('achievement_unlocked', {
                    'user_id': user_id,
                    'achievement_id': achievement.id,
                    'achievement_name': achievement.name,
                    'points_earned': points_earned,
                    'total_points': user_progress.total_points,
                    'new_level': user_progress.level
                })
            
            # Enviar notificação
            if self.config.get("notifications", {}).get("dm_on_achievement", True):
                await self._send_achievement_notification(user_id, achievement, points_earned)
            
            self.logger.info(f"Usuário {user_id} desbloqueou conquista: {achievement.name} (+{points_earned} pontos)")
        
        except Exception as e:
            self.logger.error(f"Erro ao desbloquear conquista {achievement.id} para usuário {user_id}: {e}")
    
    def _calculate_level(self, experience: int) -> int:
        """Calcular nível baseado na experiência"""
        formula = self.config.get("level_formula", "sqrt")
        
        if formula == "sqrt":
            import math
            return max(int(math.sqrt(experience / 100)) + 1, 1)
        elif formula == "linear":
            return max(experience // 1000 + 1, 1)
        else:
            return max(experience // 500 + 1, 1)
    
    async def get_user_progress(self, user_id: int) -> 'UserProgressModel':
        """Obter progresso do usuário"""
        if user_id not in self.user_progress:
            # Criar novo progresso
            if BaseModel != object:
                progress = UserProgressModel(user_id=user_id)
            else:
                progress = UserProgressModel(
                    user_id=user_id,
                    achievements=[],
                    badges=[],
                    total_points=0,
                    level=1,
                    experience=0,
                    progress={},
                    statistics={},
                    last_updated=datetime.now()
                )
            
            self.user_progress[user_id] = progress
        
        return self.user_progress[user_id]
    
    async def _save_user_progress(self, user_id: int, progress: 'UserProgressModel'):
        """Salvar progresso do usuário"""
        try:
            self.user_progress[user_id] = progress
            
            # Aqui você salvaria no banco de dados
            # Por enquanto, apenas manter em memória
            
            # Invalidar cache
            if SmartCache and hasattr(self.cache, 'delete'):
                await self.cache.delete(f"user_progress_{user_id}")
        
        except Exception as e:
            self.logger.error(f"Erro ao salvar progresso do usuário {user_id}: {e}")
    
    async def _send_achievement_notification(self, user_id: int, achievement: AchievementModel, points_earned: int):
        """Enviar notificação de conquista desbloqueada"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                return
            
            embed = discord.Embed(
                title=f"🏆 Conquista Desbloqueada!",
                description=f"**{achievement.name}**\n{achievement.description}",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Recompensa",
                value=f"{achievement.icon} +{points_earned} pontos",
                inline=True
            )
            
            rarity_colors = {
                AchievementRarity.COMMON: 0x808080,
                AchievementRarity.RARE: 0x0080FF,
                AchievementRarity.EPIC: 0x8000FF,
                AchievementRarity.LEGENDARY: 0xFF8000,
                AchievementRarity.MYTHIC: 0xFF0080
            }
            
            if hasattr(achievement, 'rarity'):
                embed.color = rarity_colors.get(achievement.rarity, discord.Color.gold())
                embed.add_field(
                    name="Raridade",
                    value=achievement.rarity.value.title(),
                    inline=True
                )
            
            embed.set_footer(text="Hawk Bot - Sistema de Conquistas")
            
            await user.send(embed=embed)
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação para usuário {user_id}: {e}")
    
    async def get_leaderboard(self, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obter leaderboard de conquistas"""
        try:
            # Filtrar usuários por categoria se especificada
            users_data = []
            
            for user_id, progress in self.user_progress.items():
                user_data = {
                    'user_id': user_id,
                    'total_points': progress.total_points,
                    'level': progress.level,
                    'achievements_count': len(progress.achievements),
                    'badges_count': len(progress.badges)
                }
                
                if category:
                    # Filtrar conquistas por categoria
                    category_achievements = [
                        ach_id for ach_id in progress.achievements
                        if ach_id in self.achievements and 
                        hasattr(self.achievements[ach_id], 'category') and
                        self.achievements[ach_id].category.value == category
                    ]
                    user_data['category_achievements'] = len(category_achievements)
                    user_data['category_points'] = sum(
                        self.achievements[ach_id].points for ach_id in category_achievements
                        if ach_id in self.achievements
                    )
                
                users_data.append(user_data)
            
            # Ordenar por pontos totais ou pontos da categoria
            sort_key = 'category_points' if category else 'total_points'
            users_data.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
            
            return users_data[:limit]
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar leaderboard: {e}")
            return []
    
    async def get_user_achievements_display(self, user_id: int) -> Dict[str, Any]:
        """Obter conquistas do usuário formatadas para exibição"""
        try:
            progress = await self.get_user_progress(user_id)
            
            # Organizar conquistas por categoria
            achievements_by_category = {}
            
            for ach_id in progress.achievements:
                if ach_id not in self.achievements:
                    continue
                
                achievement = self.achievements[ach_id]
                category = achievement.category.value if hasattr(achievement, 'category') else 'geral'
                
                if category not in achievements_by_category:
                    achievements_by_category[category] = []
                
                achievements_by_category[category].append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'points': achievement.points,
                    'rarity': achievement.rarity.value if hasattr(achievement, 'rarity') else 'comum'
                })
            
            return {
                'user_id': user_id,
                'total_points': progress.total_points,
                'level': progress.level,
                'experience': progress.experience,
                'achievements_count': len(progress.achievements),
                'badges_count': len(progress.badges),
                'achievements_by_category': achievements_by_category,
                'progress_to_next_level': self._calculate_progress_to_next_level(progress.experience),
                'rank': self._calculate_user_rank(progress.total_points)
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao obter conquistas do usuário {user_id}: {e}")
            return {}
    
    def _calculate_progress_to_next_level(self, experience: int) -> Dict[str, int]:
        """Calcular progresso para o próximo nível"""
        current_level = self._calculate_level(experience)
        next_level = current_level + 1
        
        # Calcular experiência necessária para o próximo nível
        if self.config.get("level_formula", "sqrt") == "sqrt":
            exp_for_next = ((next_level - 1) ** 2) * 100
            exp_for_current = ((current_level - 1) ** 2) * 100
        else:
            exp_for_next = (next_level - 1) * 1000
            exp_for_current = (current_level - 1) * 1000
        
        progress = experience - exp_for_current
        needed = exp_for_next - exp_for_current
        
        return {
            'current': progress,
            'needed': needed,
            'percentage': int((progress / needed) * 100) if needed > 0 else 100
        }
    
    def _calculate_user_rank(self, total_points: int) -> str:
        """Calcular rank do usuário baseado nos pontos"""
        if total_points >= 5000:
            return "Lenda"
        elif total_points >= 2500:
            return "Mestre"
        elif total_points >= 1000:
            return "Especialista"
        elif total_points >= 500:
            return "Veterano"
        elif total_points >= 200:
            return "Experiente"
        elif total_points >= 50:
            return "Iniciante"
        else:
            return "Novato"

# ==================== INSTÂNCIA GLOBAL ====================

_achievement_system: Optional[ModernAchievementSystem] = None

def get_achievement_system() -> Optional[ModernAchievementSystem]:
    """Obter instância global do sistema de conquistas"""
    return _achievement_system

def initialize_achievement_system(bot, config_path: Optional[str] = None) -> ModernAchievementSystem:
    """Inicializar sistema global de conquistas"""
    global _achievement_system
    _achievement_system = ModernAchievementSystem(bot, config_path)
    return _achievement_system

# ==================== FUNÇÕES DE CONVENIÊNCIA ====================

async def check_user_achievements_quick(user_id: int, stats: Optional[Dict[str, Any]] = None) -> List[AchievementModel]:
    """Verificação rápida de conquistas"""
    system = get_achievement_system()
    if system:
        return await system.check_user_achievements(user_id, stats)
    return []

async def get_user_progress_quick(user_id: int) -> Optional['UserProgressModel']:
    """Obter progresso do usuário rapidamente"""
    system = get_achievement_system()
    if system:
        return await system.get_user_progress(user_id)
    return None

async def get_leaderboard_quick(limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obter leaderboard rapidamente"""
    system = get_achievement_system()
    if system:
        return await system.get_leaderboard(limit, category)
    return []

if __name__ == "__main__":
    # Exemplo de uso
    pass