#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Moderação Automática Modernizado com IA
Detecção avançada de spam, toxicidade, análise de sentimentos e ações inteligentes

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import discord
import asyncio
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Importar sistemas core modernos
try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Fallback para sistemas sem Pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(default=None, **kwargs):
        return default
    
    def validator(field_name, **kwargs):
        def decorator(func):
            return func
        return decorator

try:
    from src.core.smart_cache import SmartCache
    from src.core.secure_logger import SecureLogger
    from src.core.metrics_collector import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
except ImportError:
    # Fallbacks para desenvolvimento
    class SmartCache:
        def __init__(self): self.cache = {}
        async def get(self, key): return self.cache.get(key)
        async def set(self, key, value, ttl=None): self.cache[key] = value
        async def delete(self, key): self.cache.pop(key, None)
    
    class SecureLogger:
        def __init__(self, name): pass
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class MetricsCollector:
        def __init__(self): pass
        async def increment(self, metric, tags=None): pass
        async def gauge(self, metric, value, tags=None): pass
        async def histogram(self, metric, value, tags=None): pass
    
    class DataValidator:
        def __init__(self): pass
        def validate_user_input(self, data): return True
        def sanitize_content(self, content): return content
    
    class EventSystem:
        def __init__(self): pass
        async def emit(self, event, data): pass
        def on(self, event): 
            def decorator(func): return func
            return decorator
    
    class RateLimiter:
        def __init__(self): pass
        async def is_rate_limited(self, key, limit, window): return False
        async def increment(self, key, window): pass

# Configurar logger
logger = SecureLogger('ModernModerationSystem')

class ViolationType(Enum):
    """Tipos de violações detectadas"""
    SPAM = "spam"
    TOXIC_LANGUAGE = "toxic_language"
    CAPS_SPAM = "caps_spam"
    REPEATED_MESSAGES = "repeated_messages"
    MENTION_SPAM = "mention_spam"
    LINK_SPAM = "link_spam"
    EMOJI_SPAM = "emoji_spam"
    RAID_ATTEMPT = "raid_attempt"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    PHISHING = "phishing"
    SCAM = "scam"
    NSFW_CONTENT = "nsfw_content"
    IMPERSONATION = "impersonation"

class ActionType(Enum):
    """Tipos de ações de moderação"""
    WARN = "warn"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"
    DELETE_MESSAGE = "delete_message"
    SLOWMODE = "slowmode"
    QUARANTINE = "quarantine"
    RESTRICT_PERMISSIONS = "restrict_permissions"

class SeverityLevel(Enum):
    """Níveis de severidade"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ModerationConfig(BaseModel):
    """Configuração do sistema de moderação"""
    enabled: bool = Field(default=True, description="Sistema ativo")
    auto_delete: bool = Field(default=True, description="Deletar mensagens automaticamente")
    log_channel_id: Optional[int] = Field(default=None, description="Canal de logs")
    quarantine_role_id: Optional[int] = Field(default=None, description="Role de quarentena")
    
    # Configurações de spam
    spam_message_limit: int = Field(default=5, ge=1, le=20)
    spam_time_window: int = Field(default=10, ge=5, le=60)
    caps_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
    mention_limit: int = Field(default=5, ge=1, le=20)
    emoji_limit: int = Field(default=10, ge=1, le=50)
    
    # Configurações de toxicidade
    toxicity_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
    enable_ai_analysis: bool = Field(default=True, description="Usar análise de IA")
    
    # Configurações de raid
    raid_protection: bool = Field(default=True)
    max_joins_per_minute: int = Field(default=10, ge=1, le=100)
    new_account_threshold_days: int = Field(default=7, ge=1, le=365)
    
    # Thresholds de punição
    warning_thresholds: Dict[int, str] = Field(default_factory=lambda: {
        3: "timeout",
        5: "kick", 
        7: "ban"
    })
    
    # Durações de timeout
    timeout_durations: Dict[str, int] = Field(default_factory=lambda: {
        "first_offense": 300,    # 5 minutos
        "second_offense": 900,   # 15 minutos
        "third_offense": 3600,   # 1 hora
        "repeat_offense": 7200   # 2 horas
    })

@dataclass
class ModerationAction:
    """Representa uma ação de moderação"""
    user_id: int
    guild_id: int
    action_type: ActionType
    violation_type: ViolationType
    reason: str
    timestamp: datetime
    severity: SeverityLevel
    moderator_id: Optional[int] = None
    duration: Optional[timedelta] = None
    evidence: Optional[str] = None
    confidence_score: float = 0.0
    auto_generated: bool = True
    appeal_status: Optional[str] = None

@dataclass
class UserProfile:
    """Perfil de usuário para análise comportamental"""
    user_id: int
    guild_id: int
    join_date: datetime
    total_messages: int = 0
    violations: List[ModerationAction] = field(default_factory=list)
    trust_score: float = 1.0  # 0.0 a 1.0
    last_activity: Optional[datetime] = None
    behavioral_flags: Set[str] = field(default_factory=set)
    
class AIAnalyzer:
    """Analisador de IA para detecção avançada"""
    
    def __init__(self):
        self.toxicity_patterns = {
            # Padrões de ódio
            'hate_speech': [
                r'\b(nazi|hitler|holocaust)\b',
                r'\b(n[i1]gg[e3]r|n[i1]gg[a4])\b',
                r'\b(f[a4]gg[o0]t|f[a4]g)\b',
            ],
            # Padrões de assédio
            'harassment': [
                r'\b(kill yourself|kys)\b',
                r'\b(die|death|suicide)\b.*\b(you|yourself)\b',
                r'\b(rape|molest)\b',
            ],
            # Padrões de spam
            'spam_indicators': [
                r'(.)\1{10,}',  # Caracteres repetidos
                r'\b(free|win|prize|click|link)\b.*\b(now|here|this)\b',
                r'(discord\.gg|bit\.ly|tinyurl)',
            ],
            # Padrões de phishing/scam
            'phishing': [
                r'\b(free nitro|discord gift|steam gift)\b',
                r'\b(click here|download now|limited time)\b',
                r'\b(verify account|suspended|banned)\b.*\b(click|link)\b',
            ]
        }
        
        # Palavras tóxicas por categoria
        self.toxic_words = {
            'profanity': {
                'porra', 'caralho', 'merda', 'bosta', 'cu', 'buceta',
                'puta', 'fdp', 'filho da puta', 'vai se foder'
            },
            'discrimination': {
                'viado', 'gay', 'bicha', 'traveco', 'negro', 'preto',
                'macaco', 'gorila', 'nazista', 'hitler'
            },
            'toxicity': {
                'idiota', 'burro', 'estupido', 'imbecil', 'retardado',
                'cancer', 'aids', 'doente', 'mongoloid', 'lixo', 'trash'
            },
            'gaming_toxicity': {
                'noob', 'ez', 'easy', 'rekt', 'owned', 'git gud',
                'hack', 'hacker', 'cheater', 'cheat', 'aimbot'
            }
        }
    
    async def analyze_message(self, content: str, user_profile: UserProfile) -> Tuple[float, List[ViolationType], Dict[str, Any]]:
        """Analisa mensagem usando IA e retorna score de toxicidade"""
        analysis_result = {
            'patterns_detected': [],
            'word_categories': [],
            'confidence_scores': {},
            'behavioral_indicators': []
        }
        
        violations = []
        toxicity_score = 0.0
        
        content_lower = content.lower()
        
        # Análise de padrões
        for category, patterns in self.toxicity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    analysis_result['patterns_detected'].append(category)
                    
                    if category == 'hate_speech':
                        violations.append(ViolationType.HATE_SPEECH)
                        toxicity_score += 0.9
                    elif category == 'harassment':
                        violations.append(ViolationType.HARASSMENT)
                        toxicity_score += 0.8
                    elif category == 'phishing':
                        violations.append(ViolationType.PHISHING)
                        toxicity_score += 0.7
        
        # Análise de palavras tóxicas
        for category, words in self.toxic_words.items():
            found_words = [word for word in words if word in content_lower]
            if found_words:
                analysis_result['word_categories'].append(category)
                toxicity_score += len(found_words) * 0.1
                violations.append(ViolationType.TOXIC_LANGUAGE)
        
        # Análise comportamental baseada no perfil
        if user_profile.trust_score < 0.5:
            analysis_result['behavioral_indicators'].append('low_trust_score')
            toxicity_score += 0.2
        
        if len(user_profile.violations) > 3:
            analysis_result['behavioral_indicators'].append('repeat_offender')
            toxicity_score += 0.3
        
        # Normalizar score
        toxicity_score = min(toxicity_score, 1.0)
        analysis_result['confidence_scores']['toxicity'] = toxicity_score
        
        return toxicity_score, violations, analysis_result
    
    async def analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Análise básica de sentimento"""
        positive_words = {
            'bom', 'ótimo', 'excelente', 'legal', 'massa', 'top',
            'obrigado', 'valeu', 'parabéns', 'incrível', 'amazing'
        }
        
        negative_words = {
            'ruim', 'péssimo', 'horrível', 'odeio', 'detesto',
            'nojento', 'terrível', 'awful', 'hate', 'terrible'
        }
        
        words = content.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = 1.0 - (positive_score + negative_score)
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }

class SpamDetector:
    """Detector de spam modernizado"""
    
    def __init__(self, cache: SmartCache, metrics: MetricsCollector):
        self.cache = cache
        self.metrics = metrics
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque(maxlen=20))
        self.similarity_threshold = 0.85
    
    async def check_spam(self, user_id: int, guild_id: int, content: str, config: ModerationConfig) -> Tuple[Optional[ViolationType], float]:
        """Verifica spam com análise avançada"""
        now = datetime.now()
        cache_key = f"spam_check:{guild_id}:{user_id}"
        
        # Obter histórico do cache
        user_history = await self.cache.get(cache_key) or []
        
        # Adicionar mensagem atual
        message_data = {
            'content': content.lower().strip(),
            'timestamp': now.isoformat(),
            'length': len(content)
        }
        user_history.append(message_data)
        
        # Manter apenas mensagens recentes
        cutoff_time = now - timedelta(seconds=config.spam_time_window)
        user_history = [
            msg for msg in user_history 
            if datetime.fromisoformat(msg['timestamp']) > cutoff_time
        ]
        
        # Salvar no cache
        await self.cache.set(cache_key, user_history, ttl=config.spam_time_window)
        
        confidence = 0.0
        
        # Verificar frequência de mensagens
        if len(user_history) > config.spam_message_limit:
            confidence += 0.8
            await self.metrics.increment('moderation.spam.frequency_detected', 
                                       tags={'guild_id': guild_id})
            return ViolationType.SPAM, confidence
        
        # Verificar mensagens repetidas
        if len(user_history) >= 3:
            recent_contents = [msg['content'] for msg in user_history[-3:]]
            if len(set(recent_contents)) == 1:  # Todas iguais
                confidence += 0.9
                await self.metrics.increment('moderation.spam.repeated_detected',
                                           tags={'guild_id': guild_id})
                return ViolationType.REPEATED_MESSAGES, confidence
        
        # Verificar similaridade entre mensagens
        if len(user_history) >= 2:
            last_content = user_history[-1]['content']
            prev_content = user_history[-2]['content']
            similarity = self._calculate_similarity(last_content, prev_content)
            
            if similarity > self.similarity_threshold:
                confidence += similarity
                return ViolationType.REPEATED_MESSAGES, confidence
        
        # Verificar CAPS LOCK
        if len(content) > 10:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > config.caps_threshold:
                confidence += caps_ratio
                await self.metrics.increment('moderation.spam.caps_detected',
                                           tags={'guild_id': guild_id})
                return ViolationType.CAPS_SPAM, confidence
        
        return None, 0.0
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos"""
        if not text1 or not text2:
            return 0.0
        
        # Algoritmo simples de similaridade
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 1.0 if text1 == text2 else 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def check_mention_spam(self, message: discord.Message, config: ModerationConfig) -> bool:
        """Verifica spam de menções"""
        total_mentions = len(message.mentions) + len(message.role_mentions)
        if message.mention_everyone:
            total_mentions += 10  # Penalidade alta para @everyone
        
        return total_mentions > config.mention_limit
    
    async def check_emoji_spam(self, content: str, config: ModerationConfig) -> bool:
        """Verifica spam de emojis"""
        # Padrão para emojis customizados e Unicode
        emoji_pattern = r'<a?:[^:]+:[0-9]+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        emojis = re.findall(emoji_pattern, content)
        return len(emojis) > config.emoji_limit

class RaidProtection:
    """Proteção contra raids modernizada"""
    
    def __init__(self, cache: SmartCache, metrics: MetricsCollector):
        self.cache = cache
        self.metrics = metrics
    
    async def check_raid(self, member: discord.Member, config: ModerationConfig) -> Tuple[bool, Dict[str, Any]]:
        """Verifica tentativa de raid"""
        now = datetime.now()
        guild_id = member.guild.id
        cache_key = f"raid_protection:{guild_id}"
        
        # Obter histórico de joins
        join_history = await self.cache.get(cache_key) or []
        
        # Adicionar join atual
        join_data = {
            'user_id': member.id,
            'timestamp': now.isoformat(),
            'account_age_days': (now - member.created_at.replace(tzinfo=None)).days,
            'avatar_hash': str(member.avatar) if member.avatar else None
        }
        join_history.append(join_data)
        
        # Manter apenas joins do último minuto
        cutoff_time = now - timedelta(minutes=1)
        join_history = [
            join for join in join_history
            if datetime.fromisoformat(join['timestamp']) > cutoff_time
        ]
        
        # Salvar no cache
        await self.cache.set(cache_key, join_history, ttl=60)
        
        analysis = {
            'joins_last_minute': len(join_history),
            'new_accounts': sum(1 for j in join_history if j['account_age_days'] < config.new_account_threshold_days),
            'suspicious_patterns': []
        }
        
        # Verificar número de joins
        if len(join_history) > config.max_joins_per_minute:
            analysis['suspicious_patterns'].append('high_join_rate')
            await self.metrics.increment('moderation.raid.high_join_rate',
                                       tags={'guild_id': guild_id})
        
        # Verificar contas novas
        new_account_ratio = analysis['new_accounts'] / len(join_history) if join_history else 0
        if new_account_ratio > 0.7:  # 70% de contas novas
            analysis['suspicious_patterns'].append('new_account_wave')
        
        # Verificar avatars similares (possível bot farm)
        avatar_hashes = [j['avatar_hash'] for j in join_history if j['avatar_hash']]
        if len(avatar_hashes) > 3:
            unique_avatars = len(set(avatar_hashes))
            if unique_avatars / len(avatar_hashes) < 0.5:  # Muitos avatars iguais
                analysis['suspicious_patterns'].append('similar_avatars')
        
        is_raid = len(analysis['suspicious_patterns']) >= 2
        
        if is_raid:
            await self.metrics.increment('moderation.raid.detected',
                                       tags={'guild_id': guild_id})
        
        return is_raid, analysis

class ModernModerationSystem:
    """Sistema principal de moderação modernizado"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Inicializar sistemas core
        self.cache = SmartCache()
        self.logger = SecureLogger('ModernModerationSystem')
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.events = EventSystem()
        self.rate_limiter = RateLimiter()
        
        # Componentes especializados
        self.ai_analyzer = AIAnalyzer()
        self.spam_detector = SpamDetector(self.cache, self.metrics)
        self.raid_protection = RaidProtection(self.cache, self.metrics)
        
        # Configurações por servidor
        self.guild_configs: Dict[int, ModerationConfig] = {}
        self.user_profiles: Dict[Tuple[int, int], UserProfile] = {}  # (user_id, guild_id)
        
        # Estatísticas globais
        self.stats = {
            'messages_processed': 0,
            'violations_detected': 0,
            'actions_taken': 0,
            'ai_analyses_performed': 0,
            'false_positives': 0
        }
        
        self.logger.info("Sistema de Moderação Modernizado inicializado")
    
    async def load_guild_config(self, guild_id: int) -> ModerationConfig:
        """Carrega configuração do servidor"""
        if guild_id not in self.guild_configs:
            # Tentar carregar do cache
            cache_key = f"moderation_config:{guild_id}"
            cached_config = await self.cache.get(cache_key)
            
            if cached_config:
                self.guild_configs[guild_id] = ModerationConfig(**cached_config)
            else:
                # Usar configuração padrão
                self.guild_configs[guild_id] = ModerationConfig()
                await self.save_guild_config(guild_id)
        
        return self.guild_configs[guild_id]
    
    async def save_guild_config(self, guild_id: int):
        """Salva configuração do servidor"""
        if guild_id in self.guild_configs:
            cache_key = f"moderation_config:{guild_id}"
            config_dict = self.guild_configs[guild_id].__dict__
            await self.cache.set(cache_key, config_dict, ttl=86400)  # 24 horas
    
    async def get_user_profile(self, user_id: int, guild_id: int) -> UserProfile:
        """Obtém perfil do usuário"""
        profile_key = (user_id, guild_id)
        
        if profile_key not in self.user_profiles:
            # Tentar carregar do cache
            cache_key = f"user_profile:{guild_id}:{user_id}"
            cached_profile = await self.cache.get(cache_key)
            
            if cached_profile:
                # Reconstruir objetos datetime e outros tipos
                cached_profile['join_date'] = datetime.fromisoformat(cached_profile['join_date'])
                if cached_profile.get('last_activity'):
                    cached_profile['last_activity'] = datetime.fromisoformat(cached_profile['last_activity'])
                
                self.user_profiles[profile_key] = UserProfile(**cached_profile)
            else:
                # Criar novo perfil
                guild = self.bot.get_guild(guild_id)
                member = guild.get_member(user_id) if guild else None
                join_date = member.joined_at.replace(tzinfo=None) if member and member.joined_at else datetime.now()
                
                self.user_profiles[profile_key] = UserProfile(
                    user_id=user_id,
                    guild_id=guild_id,
                    join_date=join_date
                )
                await self.save_user_profile(user_id, guild_id)
        
        return self.user_profiles[profile_key]
    
    async def save_user_profile(self, user_id: int, guild_id: int):
        """Salva perfil do usuário"""
        profile_key = (user_id, guild_id)
        if profile_key in self.user_profiles:
            cache_key = f"user_profile:{guild_id}:{user_id}"
            profile = self.user_profiles[profile_key]
            
            # Converter para dict serializável
            profile_dict = {
                'user_id': profile.user_id,
                'guild_id': profile.guild_id,
                'join_date': profile.join_date.isoformat(),
                'total_messages': profile.total_messages,
                'trust_score': profile.trust_score,
                'last_activity': profile.last_activity.isoformat() if profile.last_activity else None,
                'behavioral_flags': list(profile.behavioral_flags)
            }
            
            await self.cache.set(cache_key, profile_dict, ttl=86400)  # 24 horas
    
    async def process_message(self, message: discord.Message) -> bool:
        """Processa mensagem para detecção de violações"""
        if message.author.bot or not message.guild:
            return False
        
        # Verificar rate limiting
        rate_key = f"moderation_check:{message.guild.id}:{message.author.id}"
        if await self.rate_limiter.is_rate_limited(rate_key, limit=10, window=60):
            return False
        
        await self.rate_limiter.increment(rate_key, window=60)
        
        # Carregar configuração e perfil
        config = await self.load_guild_config(message.guild.id)
        if not config.enabled:
            return False
        
        user_profile = await self.get_user_profile(message.author.id, message.guild.id)
        
        # Verificar se é moderador
        if await self._is_moderator(message.author):
            return False
        
        self.stats['messages_processed'] += 1
        await self.metrics.increment('moderation.messages_processed',
                                   tags={'guild_id': message.guild.id})
        
        violations = []
        max_confidence = 0.0
        
        # Análise de spam
        spam_violation, spam_confidence = await self.spam_detector.check_spam(
            message.author.id, message.guild.id, message.content, config
        )
        if spam_violation:
            violations.append((spam_violation, spam_confidence, "Spam detectado"))
            max_confidence = max(max_confidence, spam_confidence)
        
        # Verificar menções em massa
        if await self.spam_detector.check_mention_spam(message, config):
            violations.append((ViolationType.MENTION_SPAM, 0.8, "Spam de menções"))
            max_confidence = max(max_confidence, 0.8)
        
        # Verificar emoji spam
        if await self.spam_detector.check_emoji_spam(message.content, config):
            violations.append((ViolationType.EMOJI_SPAM, 0.6, "Spam de emojis"))
            max_confidence = max(max_confidence, 0.6)
        
        # Análise de IA para toxicidade
        if config.enable_ai_analysis:
            toxicity_score, ai_violations, analysis_result = await self.ai_analyzer.analyze_message(
                message.content, user_profile
            )
            
            self.stats['ai_analyses_performed'] += 1
            
            if toxicity_score > config.toxicity_threshold:
                for violation_type in ai_violations:
                    violations.append((violation_type, toxicity_score, f"IA detectou: {violation_type.value}"))
                max_confidence = max(max_confidence, toxicity_score)
        
        # Processar violações encontradas
        if violations:
            await self._handle_violations(message, violations, user_profile, config, max_confidence)
            return True
        
        # Atualizar perfil do usuário (mensagem limpa)
        user_profile.total_messages += 1
        user_profile.last_activity = datetime.now()
        user_profile.trust_score = min(user_profile.trust_score + 0.001, 1.0)  # Pequeno aumento na confiança
        await self.save_user_profile(message.author.id, message.guild.id)
        
        return False
    
    async def process_member_join(self, member: discord.Member) -> bool:
        """Processa entrada de novo membro"""
        config = await self.load_guild_config(member.guild.id)
        if not config.raid_protection:
            return False
        
        is_raid, analysis = await self.raid_protection.check_raid(member, config)
        
        if is_raid:
            await self._handle_raid_attempt(member, analysis, config)
            return True
        
        return False
    
    async def _handle_violations(self, message: discord.Message, violations: List[Tuple], 
                               user_profile: UserProfile, config: ModerationConfig, confidence: float):
        """Processa violações detectadas"""
        self.stats['violations_detected'] += len(violations)
        
        for violation_type, violation_confidence, reason in violations:
            # Determinar severidade
            severity = self._calculate_severity(violation_type, violation_confidence, user_profile)
            
            # Criar ação de moderação
            action = ModerationAction(
                user_id=message.author.id,
                guild_id=message.guild.id,
                action_type=ActionType.WARN,
                violation_type=violation_type,
                reason=reason,
                timestamp=datetime.now(),
                severity=severity,
                evidence=message.content[:500],
                confidence_score=violation_confidence,
                auto_generated=True
            )
            
            # Adicionar ao perfil do usuário
            user_profile.violations.append(action)
            user_profile.trust_score = max(user_profile.trust_score - 0.1, 0.0)
            
            # Deletar mensagem se configurado
            if config.auto_delete:
                try:
                    await message.delete()
                    await self.metrics.increment('moderation.messages_deleted',
                                               tags={'guild_id': message.guild.id})
                except (discord.NotFound, discord.Forbidden):
                    pass
            
            # Verificar se precisa de ação adicional
            warn_count = len(user_profile.violations)
            additional_action = None
            
            for threshold, action_type in config.warning_thresholds.items():
                if warn_count >= threshold:
                    additional_action = ActionType(action_type)
                    break
            
            if additional_action:
                await self._execute_action(message.author, additional_action, 
                                         f"Acumulou {warn_count} violações", config)
                action.action_type = additional_action
                self.stats['actions_taken'] += 1
            
            # Emitir evento
            await self.events.emit('moderation_action', {
                'action': action,
                'user': message.author,
                'guild': message.guild,
                'confidence': confidence
            })
            
            # Log da ação
            await self._log_action(action, message.guild, config)
            
            # Notificar usuário
            await self._notify_user(message.author, action, warn_count)
        
        # Salvar perfil atualizado
        await self.save_user_profile(message.author.id, message.guild.id)
    
    def _calculate_severity(self, violation_type: ViolationType, confidence: float, 
                          user_profile: UserProfile) -> SeverityLevel:
        """Calcula severidade da violação"""
        base_severity = {
            ViolationType.SPAM: SeverityLevel.LOW,
            ViolationType.CAPS_SPAM: SeverityLevel.LOW,
            ViolationType.EMOJI_SPAM: SeverityLevel.LOW,
            ViolationType.TOXIC_LANGUAGE: SeverityLevel.MEDIUM,
            ViolationType.HARASSMENT: SeverityLevel.HIGH,
            ViolationType.HATE_SPEECH: SeverityLevel.CRITICAL,
            ViolationType.PHISHING: SeverityLevel.HIGH,
            ViolationType.RAID_ATTEMPT: SeverityLevel.CRITICAL
        }.get(violation_type, SeverityLevel.MEDIUM)
        
        # Ajustar baseado na confiança
        if confidence > 0.9:
            severity_value = min(base_severity.value + 1, 4)
        elif confidence < 0.5:
            severity_value = max(base_severity.value - 1, 1)
        else:
            severity_value = base_severity.value
        
        # Ajustar baseado no histórico do usuário
        if len(user_profile.violations) > 5:
            severity_value = min(severity_value + 1, 4)
        
        return SeverityLevel(severity_value)
    
    async def _execute_action(self, user: discord.Member, action_type: ActionType, 
                            reason: str, config: ModerationConfig):
        """Executa ação de moderação"""
        try:
            if action_type == ActionType.TIMEOUT:
                # Calcular duração baseada no histórico
                user_profile = await self.get_user_profile(user.id, user.guild.id)
                violation_count = len(user_profile.violations)
                
                if violation_count <= 3:
                    duration = config.timeout_durations.get('first_offense', 300)
                elif violation_count <= 5:
                    duration = config.timeout_durations.get('second_offense', 900)
                else:
                    duration = config.timeout_durations.get('repeat_offense', 7200)
                
                duration = min(duration, 86400)  # Max 24h
                await user.timeout(timedelta(seconds=duration), reason=reason)
                
            elif action_type == ActionType.KICK:
                await user.kick(reason=reason)
                
            elif action_type == ActionType.BAN:
                await user.ban(reason=reason, delete_message_days=1)
                
            elif action_type == ActionType.QUARANTINE:
                # Aplicar role de quarentena se configurado
                if config.quarantine_role_id:
                    quarantine_role = user.guild.get_role(config.quarantine_role_id)
                    if quarantine_role:
                        await user.add_roles(quarantine_role, reason=reason)
            
            await self.metrics.increment('moderation.actions_executed',
                                       tags={'guild_id': user.guild.id, 'action': action_type.value})
            
        except discord.Forbidden:
            self.logger.warning(f"Sem permissão para executar {action_type.value} em {user}")
        except Exception as e:
            self.logger.error(f"Erro ao executar ação {action_type.value}: {e}")
    
    async def _handle_raid_attempt(self, member: discord.Member, analysis: Dict[str, Any], 
                                 config: ModerationConfig):
        """Processa tentativa de raid"""
        action = ModerationAction(
            user_id=member.id,
            guild_id=member.guild.id,
            action_type=ActionType.BAN,
            violation_type=ViolationType.RAID_ATTEMPT,
            reason=f"Raid detectado: {', '.join(analysis['suspicious_patterns'])}",
            timestamp=datetime.now(),
            severity=SeverityLevel.CRITICAL,
            confidence_score=0.9,
            auto_generated=True
        )
        
        try:
            await member.ban(reason=action.reason, delete_message_days=0)
            self.stats['actions_taken'] += 1
            
            # Emitir evento
            await self.events.emit('raid_detected', {
                'member': member,
                'analysis': analysis,
                'action': action
            })
            
            # Log da ação
            await self._log_action(action, member.guild, config)
            
        except discord.Forbidden:
            self.logger.warning(f"Sem permissão para banir {member} durante raid")
    
    async def _log_action(self, action: ModerationAction, guild: discord.Guild, 
                        config: ModerationConfig):
        """Registra ação no canal de logs"""
        if not config.log_channel_id:
            return
        
        log_channel = guild.get_channel(config.log_channel_id)
        if not log_channel:
            return
        
        user = guild.get_member(action.user_id)
        if not user:
            return
        
        # Criar embed com informações detalhadas
        color_map = {
            SeverityLevel.LOW: discord.Color.yellow(),
            SeverityLevel.MEDIUM: discord.Color.orange(),
            SeverityLevel.HIGH: discord.Color.red(),
            SeverityLevel.CRITICAL: discord.Color.dark_red()
        }
        
        embed = discord.Embed(
            title="🤖 Ação de Moderação Automática",
            color=color_map.get(action.severity, discord.Color.blue()),
            timestamp=action.timestamp
        )
        
        embed.add_field(name="👤 Usuário", value=f"{user.mention} ({user})", inline=True)
        embed.add_field(name="⚠️ Violação", value=action.violation_type.value.replace('_', ' ').title(), inline=True)
        embed.add_field(name="🎯 Ação", value=action.action_type.value.replace('_', ' ').title(), inline=True)
        embed.add_field(name="📝 Motivo", value=action.reason, inline=False)
        embed.add_field(name="🎚️ Severidade", value=action.severity.name, inline=True)
        embed.add_field(name="🎯 Confiança", value=f"{action.confidence_score:.2%}", inline=True)
        embed.add_field(name="🤖 Automático", value="Sim" if action.auto_generated else "Não", inline=True)
        
        if action.evidence:
            embed.add_field(name="📋 Evidência", value=f"```{action.evidence[:200]}```", inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Erro ao enviar log: {e}")
    
    async def _notify_user(self, user: discord.Member, action: ModerationAction, warn_count: int):
        """Notifica usuário sobre a ação"""
        try:
            embed = discord.Embed(
                title="⚠️ Aviso de Moderação",
                description=f"Você recebeu uma advertência em **{user.guild.name}**",
                color=discord.Color.orange(),
                timestamp=action.timestamp
            )
            
            embed.add_field(name="📝 Motivo", value=action.reason, inline=False)
            embed.add_field(name="📊 Total de Advertências", value=str(warn_count), inline=True)
            embed.add_field(name="🎯 Ação", value=action.action_type.value.replace('_', ' ').title(), inline=True)
            
            if action.action_type == ActionType.TIMEOUT and action.duration:
                embed.add_field(name="⏰ Duração", value=str(action.duration), inline=True)
            
            embed.add_field(
                name="💡 Dica",
                value="Respeite as regras do servidor para evitar futuras punições.",
                inline=False
            )
            
            await user.send(embed=embed)
            
        except discord.Forbidden:
            pass  # Usuário não aceita DMs
        except Exception as e:
            self.logger.error(f"Erro ao notificar usuário: {e}")
    
    async def _is_moderator(self, member: discord.Member) -> bool:
        """Verifica se o usuário é moderador"""
        if member.guild_permissions.administrator:
            return True
        
        if member.guild_permissions.moderate_members:
            return True
        
        # Verificar roles específicas (pode ser configurado)
        mod_role_names = {'moderador', 'mod', 'staff', 'admin'}
        user_roles = {role.name.lower() for role in member.roles}
        
        return bool(mod_role_names.intersection(user_roles))
    
    async def get_user_warnings(self, user_id: int, guild_id: int) -> List[ModerationAction]:
        """Obtém advertências do usuário"""
        user_profile = await self.get_user_profile(user_id, guild_id)
        return user_profile.violations
    
    async def clear_user_warnings(self, user_id: int, guild_id: int, moderator_id: int) -> int:
        """Limpa advertências do usuário"""
        user_profile = await self.get_user_profile(user_id, guild_id)
        warning_count = len(user_profile.violations)
        
        user_profile.violations.clear()
        user_profile.trust_score = min(user_profile.trust_score + 0.2, 1.0)
        
        await self.save_user_profile(user_id, guild_id)
        
        # Emitir evento
        await self.events.emit('warnings_cleared', {
            'user_id': user_id,
            'guild_id': guild_id,
            'moderator_id': moderator_id,
            'cleared_count': warning_count
        })
        
        return warning_count
    
    async def get_moderation_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtém estatísticas de moderação"""
        stats = self.stats.copy()
        
        if guild_id:
            # Estatísticas específicas do servidor
            guild_users = [p for p in self.user_profiles.values() if p.guild_id == guild_id]
            stats['guild_users_monitored'] = len(guild_users)
            stats['guild_total_violations'] = sum(len(p.violations) for p in guild_users)
            stats['guild_avg_trust_score'] = sum(p.trust_score for p in guild_users) / len(guild_users) if guild_users else 0
        
        return stats
    
    async def update_guild_config(self, guild_id: int, **kwargs) -> ModerationConfig:
        """Atualiza configuração do servidor"""
        config = await self.load_guild_config(guild_id)
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        await self.save_guild_config(guild_id)
        
        # Emitir evento
        await self.events.emit('config_updated', {
            'guild_id': guild_id,
            'changes': kwargs
        })
        
        return config
    
    async def export_user_data(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Exporta dados do usuário (LGPD/GDPR)"""
        user_profile = await self.get_user_profile(user_id, guild_id)
        
        return {
            'user_id': user_profile.user_id,
            'guild_id': user_profile.guild_id,
            'join_date': user_profile.join_date.isoformat(),
            'total_messages': user_profile.total_messages,
            'trust_score': user_profile.trust_score,
            'violations': [
                {
                    'type': v.violation_type.value,
                    'reason': v.reason,
                    'timestamp': v.timestamp.isoformat(),
                    'severity': v.severity.name,
                    'confidence': v.confidence_score
                }
                for v in user_profile.violations
            ],
            'behavioral_flags': list(user_profile.behavioral_flags),
            'export_timestamp': datetime.now().isoformat()
        }
    
    async def delete_user_data(self, user_id: int, guild_id: int) -> bool:
        """Deleta dados do usuário (LGPD/GDPR)"""
        try:
            # Remover do cache
            profile_key = (user_id, guild_id)
            if profile_key in self.user_profiles:
                del self.user_profiles[profile_key]
            
            # Remover do cache persistente
            cache_key = f"user_profile:{guild_id}:{user_id}"
            await self.cache.delete(cache_key)
            
            # Emitir evento
            await self.events.emit('user_data_deleted', {
                'user_id': user_id,
                'guild_id': guild_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao deletar dados do usuário: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do sistema"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'stats': self.stats
        }
        
        # Verificar componentes
        try:
            # Cache
            test_key = f"health_check:{datetime.now().timestamp()}"
            await self.cache.set(test_key, 'test', ttl=10)
            cached_value = await self.cache.get(test_key)
            health_status['components']['cache'] = 'healthy' if cached_value == 'test' else 'unhealthy'
            await self.cache.delete(test_key)
            
            # AI Analyzer
            test_analysis = await self.ai_analyzer.analyze_sentiment("test message")
            health_status['components']['ai_analyzer'] = 'healthy' if test_analysis else 'unhealthy'
            
            # Rate Limiter
            test_rate_key = f"health_test:{datetime.now().timestamp()}"
            rate_limited = await self.rate_limiter.is_rate_limited(test_rate_key, 1, 60)
            health_status['components']['rate_limiter'] = 'healthy' if not rate_limited else 'unhealthy'
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status