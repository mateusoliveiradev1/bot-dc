#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Modernizado de Notificações Push Avançadas
Sistema inteligente de notificações com IA, análise de comportamento e entrega otimizada

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import uuid
import json
import hashlib
from collections import defaultdict, deque
import re

# Importar sistemas core modernos
try:
    from src.core.secure_logger import SecureLogger
    from src.core.smart_cache import SmartCache
    from src.core.metrics_collector import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
except ImportError:
    # Fallbacks para desenvolvimento
    class SecureLogger:
        def __init__(self, name): pass
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    
    class SmartCache:
        def __init__(self): self.cache = {}
        async def get(self, key): return self.cache.get(key)
        async def set(self, key, value, ttl=None): self.cache[key] = value
        async def delete(self, key): self.cache.pop(key, None)
        async def clear(self): self.cache.clear()
    
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
        async def subscribe(self, event, callback): pass
    
    class RateLimiter:
        def __init__(self): pass
        async def is_rate_limited(self, key, limit, window): return False
        async def increment(self, key, window): pass

# Configurar logger
logger = SecureLogger('ModernNotificationSystem')

class NotificationType(Enum):
    """Tipos de notificações modernizados"""
    # Tipos básicos
    RANK_UPDATE = "rank_update"
    ACHIEVEMENT = "achievement"
    TOURNAMENT = "tournament"
    CHALLENGE = "challenge"
    MINIGAME = "minigame"
    MODERATION = "moderation"
    SYSTEM = "system"
    REMINDER = "reminder"
    BIRTHDAY = "birthday"
    CLAN_NEWS = "clan_news"
    PUBG_STATS = "pubg_stats"
    
    # Tipos avançados
    SMART_RECOMMENDATION = "smart_recommendation"
    BEHAVIOR_ALERT = "behavior_alert"
    ENGAGEMENT_BOOST = "engagement_boost"
    PERSONALIZED_TIP = "personalized_tip"
    SOCIAL_UPDATE = "social_update"
    MILESTONE_CELEBRATION = "milestone_celebration"
    TREND_ALERT = "trend_alert"
    COMMUNITY_EVENT = "community_event"
    PERFORMANCE_INSIGHT = "performance_insight"
    FRIENDSHIP_UPDATE = "friendship_update"

class NotificationPriority(IntEnum):
    """Prioridades das notificações com valores numéricos"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class DeliveryChannel(Enum):
    """Canais de entrega de notificações"""
    DM = "dm"
    GUILD_CHANNEL = "guild_channel"
    WEBHOOK = "webhook"
    EMAIL = "email"  # Para futuro
    MOBILE_PUSH = "mobile_push"  # Para futuro
    WEB_PUSH = "web_push"  # Para futuro

class NotificationStatus(Enum):
    """Status das notificações"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class UserBehaviorPattern(Enum):
    """Padrões de comportamento do usuário"""
    HIGHLY_ACTIVE = "highly_active"
    MODERATELY_ACTIVE = "moderately_active"
    LOW_ACTIVITY = "low_activity"
    INACTIVE = "inactive"
    NIGHT_OWL = "night_owl"
    EARLY_BIRD = "early_bird"
    WEEKEND_WARRIOR = "weekend_warrior"
    COMPETITIVE = "competitive"
    SOCIAL = "social"
    CASUAL = "casual"

class NotificationTemplate(BaseModel):
    """Template modernizado para notificações"""
    id: str
    type: NotificationType
    title: str
    message: str
    color: int = Field(default=0x7289DA, ge=0, le=0xFFFFFF)
    emoji: str = "📢"
    priority: NotificationPriority = NotificationPriority.MEDIUM
    requires_action: bool = False
    action_buttons: List[str] = Field(default_factory=list)
    expires_after_minutes: Optional[int] = Field(default=None, ge=1)
    cooldown_minutes: Optional[int] = Field(default=None, ge=1)
    target_patterns: Set[UserBehaviorPattern] = Field(default_factory=set)
    delivery_channels: Set[DeliveryChannel] = Field(default_factory=lambda: {DeliveryChannel.DM})
    personalization_fields: List[str] = Field(default_factory=list)
    ai_enhancement: bool = False
    
    class Config:
        use_enum_values = True

class SmartNotification(BaseModel):
    """Notificação inteligente modernizada"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    guild_id: Optional[int] = None
    template_id: str
    type: NotificationType
    title: str
    message: str
    color: int
    emoji: str
    priority: NotificationPriority
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Dados e personalização
    data: Dict[str, Any] = Field(default_factory=dict)
    personalized_content: Dict[str, str] = Field(default_factory=dict)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Configurações de entrega
    delivery_channels: Set[DeliveryChannel] = Field(default_factory=lambda: {DeliveryChannel.DM})
    requires_action: bool = False
    action_buttons: List[str] = Field(default_factory=list)
    
    # Métricas
    delivery_attempts: int = 0
    engagement_score: float = 0.0
    user_reaction: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserNotificationProfile(BaseModel):
    """Perfil avançado de notificações do usuário"""
    user_id: int
    guild_id: Optional[int] = None
    
    # Preferências básicas
    enabled_types: Set[NotificationType] = Field(default_factory=lambda: set(NotificationType))
    delivery_channels: Set[DeliveryChannel] = Field(default_factory=lambda: {DeliveryChannel.DM})
    min_priority: NotificationPriority = NotificationPriority.LOW
    
    # Horários e frequência
    quiet_hours_start: int = Field(default=22, ge=0, le=23)
    quiet_hours_end: int = Field(default=8, ge=0, le=23)
    timezone_offset: int = Field(default=0, ge=-12, le=12)
    max_notifications_per_hour: int = Field(default=5, ge=1, le=20)
    max_notifications_per_day: int = Field(default=50, ge=1, le=200)
    
    # Configurações inteligentes
    ai_personalization: bool = True
    smart_timing: bool = True
    behavior_based_filtering: bool = True
    engagement_optimization: bool = True
    
    # Padrões de comportamento detectados
    behavior_patterns: Set[UserBehaviorPattern] = Field(default_factory=set)
    activity_peak_hours: List[int] = Field(default_factory=list)
    preferred_notification_types: List[NotificationType] = Field(default_factory=list)
    
    # Estatísticas
    total_notifications_received: int = 0
    total_notifications_read: int = 0
    average_read_time_minutes: float = 0.0
    engagement_score: float = 0.5
    last_activity: Optional[datetime] = None
    
    # Configurações personalizadas
    custom_keywords: List[str] = Field(default_factory=list)
    blocked_keywords: List[str] = Field(default_factory=list)
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

class NotificationAnalytics(BaseModel):
    """Analytics de notificações"""
    total_sent: int = 0
    total_delivered: int = 0
    total_read: int = 0
    total_failed: int = 0
    total_expired: int = 0
    
    delivery_rate: float = 0.0
    read_rate: float = 0.0
    engagement_rate: float = 0.0
    
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_channel: Dict[str, int] = Field(default_factory=dict)
    by_hour: Dict[int, int] = Field(default_factory=dict)
    
    average_delivery_time_seconds: float = 0.0
    average_read_time_minutes: float = 0.0
    
    peak_hours: List[int] = Field(default_factory=list)
    most_engaging_types: List[str] = Field(default_factory=list)

class AIPersonalizationEngine:
    """Engine de personalização com IA"""
    
    def __init__(self):
        self.logger = SecureLogger('AIPersonalizationEngine')
        self.cache = SmartCache()
        
        # Padrões de personalização
        self.personality_patterns = {
            UserBehaviorPattern.COMPETITIVE: {
                'tone': 'motivational',
                'keywords': ['desafio', 'competição', 'ranking', 'vitória'],
                'emoji_preference': ['🏆', '⚔️', '🎯', '💪']
            },
            UserBehaviorPattern.SOCIAL: {
                'tone': 'friendly',
                'keywords': ['comunidade', 'amigos', 'equipe', 'colaboração'],
                'emoji_preference': ['👥', '🤝', '💬', '🎉']
            },
            UserBehaviorPattern.CASUAL: {
                'tone': 'relaxed',
                'keywords': ['diversão', 'relaxar', 'entretenimento'],
                'emoji_preference': ['😊', '🎮', '🌟', '✨']
            }
        }
    
    async def personalize_notification(self, notification: SmartNotification, profile: UserNotificationProfile) -> SmartNotification:
        """Personaliza notificação baseada no perfil do usuário"""
        try:
            # Aplicar personalização baseada em padrões de comportamento
            for pattern in profile.behavior_patterns:
                if pattern in self.personality_patterns:
                    pattern_config = self.personality_patterns[pattern]
                    
                    # Ajustar tom da mensagem
                    notification.message = await self._adjust_message_tone(
                        notification.message, pattern_config['tone']
                    )
                    
                    # Adicionar keywords relevantes
                    notification.personalized_content['keywords'] = pattern_config['keywords']
                    
                    # Sugerir emoji mais adequado
                    if pattern_config['emoji_preference']:
                        notification.emoji = pattern_config['emoji_preference'][0]
            
            # Personalizar baseado em atividade
            if profile.last_activity:
                time_since_activity = datetime.now(timezone.utc) - profile.last_activity
                if time_since_activity.days > 7:
                    notification.message = f"Sentimos sua falta! {notification.message}"
                elif time_since_activity.days > 1:
                    notification.message = f"Bem-vindo de volta! {notification.message}"
            
            # Adicionar insights de IA
            notification.ai_insights = {
                'personalization_applied': True,
                'behavior_patterns_used': [p.value for p in profile.behavior_patterns],
                'engagement_prediction': await self._predict_engagement(notification, profile)
            }
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Erro na personalização: {e}")
            return notification
    
    async def _adjust_message_tone(self, message: str, tone: str) -> str:
        """Ajusta o tom da mensagem"""
        tone_adjustments = {
            'motivational': {
                'prefixes': ['Incrível!', 'Fantástico!', 'Excelente trabalho!'],
                'suffixes': ['Continue assim!', 'Você está arrasando!', 'Rumo ao topo!']
            },
            'friendly': {
                'prefixes': ['Oi!', 'Olá!', 'E aí!'],
                'suffixes': ['Esperamos que goste!', 'Divirta-se!', 'Até mais!']
            },
            'relaxed': {
                'prefixes': ['Ei,', 'Olha só,', 'Que tal'],
                'suffixes': ['Sem pressa!', 'No seu tempo!', 'Relaxe e aproveite!']
            }
        }
        
        if tone in tone_adjustments:
            adjustments = tone_adjustments[tone]
            # Aplicar ajustes de forma inteligente
            if not any(prefix in message for prefix in adjustments['prefixes']):
                import random
                prefix = random.choice(adjustments['prefixes'])
                message = f"{prefix} {message}"
        
        return message
    
    async def _predict_engagement(self, notification: SmartNotification, profile: UserNotificationProfile) -> float:
        """Prediz o engajamento baseado em dados históricos"""
        base_score = 0.5
        
        # Ajustar baseado no tipo de notificação
        if notification.type in profile.preferred_notification_types:
            base_score += 0.2
        
        # Ajustar baseado na prioridade
        priority_bonus = {
            NotificationPriority.LOW: 0.0,
            NotificationPriority.MEDIUM: 0.1,
            NotificationPriority.HIGH: 0.2,
            NotificationPriority.URGENT: 0.3,
            NotificationPriority.CRITICAL: 0.4
        }
        base_score += priority_bonus.get(notification.priority, 0.0)
        
        # Ajustar baseado no histórico de engajamento
        base_score = (base_score + profile.engagement_score) / 2
        
        return min(1.0, max(0.0, base_score))

class SmartDeliveryEngine:
    """Engine inteligente de entrega de notificações"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = SecureLogger('SmartDeliveryEngine')
        self.cache = SmartCache()
        self.metrics = MetricsCollector()
        
        # Configurações de entrega
        self.max_retries = 3
        self.retry_delays = [30, 300, 1800]  # 30s, 5min, 30min
        self.batch_size = 10
        
        # Filas de entrega por prioridade
        self.delivery_queues = {
            NotificationPriority.CRITICAL: deque(),
            NotificationPriority.URGENT: deque(),
            NotificationPriority.HIGH: deque(),
            NotificationPriority.MEDIUM: deque(),
            NotificationPriority.LOW: deque()
        }
    
    async def queue_notification(self, notification: SmartNotification, profile: UserNotificationProfile):
        """Adiciona notificação à fila apropriada"""
        try:
            # Verificar se deve ser entregue agora ou agendada
            if await self._should_deliver_now(notification, profile):
                self.delivery_queues[notification.priority].append(notification)
                await self.metrics.increment('notifications.queued', 
                                            tags={'priority': notification.priority.name})
            else:
                # Agendar para melhor momento
                optimal_time = await self._calculate_optimal_delivery_time(profile)
                notification.scheduled_for = optimal_time
                notification.status = NotificationStatus.SCHEDULED
                
                await self.metrics.increment('notifications.scheduled',
                                            tags={'priority': notification.priority.name})
            
        except Exception as e:
            self.logger.error(f"Erro ao enfileirar notificação: {e}")
    
    async def _should_deliver_now(self, notification: SmartNotification, profile: UserNotificationProfile) -> bool:
        """Determina se a notificação deve ser entregue imediatamente"""
        # Notificações críticas e urgentes sempre são entregues imediatamente
        if notification.priority >= NotificationPriority.URGENT:
            return True
        
        # Verificar horário silencioso
        if await self._is_quiet_time(profile):
            return False
        
        # Verificar limites de frequência
        if await self._exceeds_frequency_limits(notification.user_id, profile):
            return False
        
        # Verificar se usuário está ativo
        if profile.smart_timing and not await self._is_user_likely_active(profile):
            return False
        
        return True
    
    async def _is_quiet_time(self, profile: UserNotificationProfile) -> bool:
        """Verifica se está no horário silencioso do usuário"""
        now = datetime.now(timezone.utc)
        # Ajustar para timezone do usuário
        user_time = now + timedelta(hours=profile.timezone_offset)
        current_hour = user_time.hour
        
        if profile.quiet_hours_start > profile.quiet_hours_end:
            # Horário atravessa meia-noite
            return current_hour >= profile.quiet_hours_start or current_hour < profile.quiet_hours_end
        else:
            return profile.quiet_hours_start <= current_hour < profile.quiet_hours_end
    
    async def _exceeds_frequency_limits(self, user_id: int, profile: UserNotificationProfile) -> bool:
        """Verifica se excede limites de frequência"""
        # Verificar limite por hora
        hour_key = f"notifications:hour:{user_id}:{datetime.now().hour}"
        hour_count = await self.cache.get(hour_key) or 0
        if hour_count >= profile.max_notifications_per_hour:
            return True
        
        # Verificar limite por dia
        day_key = f"notifications:day:{user_id}:{datetime.now().date()}"
        day_count = await self.cache.get(day_key) or 0
        if day_count >= profile.max_notifications_per_day:
            return True
        
        return False
    
    async def _is_user_likely_active(self, profile: UserNotificationProfile) -> bool:
        """Prediz se o usuário está provavelmente ativo"""
        current_hour = datetime.now().hour
        
        # Verificar horários de pico de atividade
        if profile.activity_peak_hours and current_hour in profile.activity_peak_hours:
            return True
        
        # Verificar padrões de comportamento
        now = datetime.now()
        if UserBehaviorPattern.NIGHT_OWL in profile.behavior_patterns and 20 <= current_hour <= 23:
            return True
        if UserBehaviorPattern.EARLY_BIRD in profile.behavior_patterns and 6 <= current_hour <= 9:
            return True
        if UserBehaviorPattern.WEEKEND_WARRIOR in profile.behavior_patterns and now.weekday() >= 5:
            return True
        
        return False
    
    async def _calculate_optimal_delivery_time(self, profile: UserNotificationProfile) -> datetime:
        """Calcula o melhor momento para entregar a notificação"""
        now = datetime.now(timezone.utc)
        
        # Se tem horários de pico definidos, usar o próximo
        if profile.activity_peak_hours:
            current_hour = (now + timedelta(hours=profile.timezone_offset)).hour
            next_peak = None
            
            for peak_hour in sorted(profile.activity_peak_hours):
                if peak_hour > current_hour:
                    next_peak = peak_hour
                    break
            
            if not next_peak:
                next_peak = profile.activity_peak_hours[0]  # Próximo dia
                return now.replace(hour=next_peak, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                return now.replace(hour=next_peak, minute=0, second=0, microsecond=0)
        
        # Fallback: próximo horário fora do período silencioso
        if await self._is_quiet_time(profile):
            quiet_end_hour = profile.quiet_hours_end
            return now.replace(hour=quiet_end_hour, minute=0, second=0, microsecond=0)
        
        # Se não há restrições, entregar em 5 minutos
        return now + timedelta(minutes=5)
    
    async def deliver_notification(self, notification: SmartNotification) -> bool:
        """Entrega uma notificação específica"""
        try:
            notification.status = NotificationStatus.SENDING
            notification.delivery_attempts += 1
            
            # Tentar entregar por cada canal configurado
            delivered = False
            for channel in notification.delivery_channels:
                if await self._deliver_via_channel(notification, channel):
                    delivered = True
                    break
            
            if delivered:
                notification.status = NotificationStatus.DELIVERED
                notification.delivered_at = datetime.now(timezone.utc)
                
                # Atualizar contadores de frequência
                await self._update_frequency_counters(notification.user_id)
                
                await self.metrics.increment('notifications.delivered',
                                            tags={'channel': channel.value, 'type': notification.type.value})
                return True
            else:
                notification.status = NotificationStatus.FAILED
                await self.metrics.increment('notifications.failed',
                                            tags={'type': notification.type.value})
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na entrega de notificação: {e}")
            notification.status = NotificationStatus.FAILED
            return False
    
    async def _deliver_via_channel(self, notification: SmartNotification, channel: DeliveryChannel) -> bool:
        """Entrega notificação via canal específico"""
        try:
            if channel == DeliveryChannel.DM:
                return await self._deliver_via_dm(notification)
            elif channel == DeliveryChannel.GUILD_CHANNEL:
                return await self._deliver_via_guild_channel(notification)
            elif channel == DeliveryChannel.WEBHOOK:
                return await self._deliver_via_webhook(notification)
            else:
                self.logger.warning(f"Canal de entrega não implementado: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na entrega via {channel}: {e}")
            return False
    
    async def _deliver_via_dm(self, notification: SmartNotification) -> bool:
        """Entrega via mensagem direta"""
        try:
            user = self.bot.get_user(notification.user_id)
            if not user:
                user = await self.bot.fetch_user(notification.user_id)
            
            if not user:
                return False
            
            embed = discord.Embed(
                title=f"{notification.emoji} {notification.title}",
                description=notification.message,
                color=notification.color,
                timestamp=notification.created_at
            )
            
            # Adicionar campos personalizados
            if notification.personalized_content:
                for key, value in notification.personalized_content.items():
                    if key != 'keywords':  # Keywords são internas
                        embed.add_field(name=key.title(), value=value, inline=True)
            
            # Adicionar insights de IA se disponíveis
            if notification.ai_insights.get('engagement_prediction'):
                confidence = notification.ai_insights['engagement_prediction']
                if confidence > 0.8:
                    embed.set_footer(text="💡 Esta notificação foi personalizada especialmente para você!")
            
            embed.set_footer(text="Sistema de Notificações Inteligentes")
            
            # Criar view com botões de ação se necessário
            view = None
            if notification.requires_action and notification.action_buttons:
                view = NotificationActionView(notification)
            
            await user.send(embed=embed, view=view)
            return True
            
        except discord.Forbidden:
            self.logger.warning(f"Não foi possível enviar DM para usuário {notification.user_id}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar DM: {e}")
            return False
    
    async def _deliver_via_guild_channel(self, notification: SmartNotification) -> bool:
        """Entrega via canal do servidor"""
        try:
            if not notification.guild_id:
                return False
            
            guild = self.bot.get_guild(notification.guild_id)
            if not guild:
                return False
            
            # Procurar canal de notificações
            channel = None
            for ch in guild.text_channels:
                if ch.name in ['notificações', 'notifications', 'avisos', 'geral']:
                    channel = ch
                    break
            
            if not channel:
                return False
            
            user = guild.get_member(notification.user_id)
            if not user:
                return False
            
            embed = discord.Embed(
                title=f"{notification.emoji} {notification.title}",
                description=f"{user.mention}\n{notification.message}",
                color=notification.color,
                timestamp=notification.created_at
            )
            
            embed.set_footer(text="Sistema de Notificações Inteligentes")
            
            await channel.send(embed=embed)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar para canal do servidor: {e}")
            return False
    
    async def _deliver_via_webhook(self, notification: SmartNotification) -> bool:
        """Entrega via webhook (para integrações externas)"""
        # Implementação futura para webhooks
        return False
    
    async def _update_frequency_counters(self, user_id: int):
        """Atualiza contadores de frequência"""
        now = datetime.now()
        
        # Contador por hora
        hour_key = f"notifications:hour:{user_id}:{now.hour}"
        hour_count = await self.cache.get(hour_key) or 0
        await self.cache.set(hour_key, hour_count + 1, ttl=3600)
        
        # Contador por dia
        day_key = f"notifications:day:{user_id}:{now.date()}"
        day_count = await self.cache.get(day_key) or 0
        await self.cache.set(day_key, day_count + 1, ttl=86400)

class NotificationActionView(discord.ui.View):
    """View para botões de ação em notificações"""
    
    def __init__(self, notification: SmartNotification):
        super().__init__(timeout=300)  # 5 minutos
        self.notification = notification
        
        # Adicionar botões baseados na configuração
        for button_text in notification.action_buttons[:5]:  # Máximo 5 botões
            button = discord.ui.Button(
                label=button_text,
                style=discord.ButtonStyle.primary,
                custom_id=f"notification_action_{button_text.lower().replace(' ', '_')}"
            )
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        """Callback para botões de ação"""
        try:
            button_id = interaction.data['custom_id']
            action = button_id.replace('notification_action_', '').replace('_', ' ').title()
            
            # Registrar interação
            self.notification.user_reaction = action
            self.notification.read_at = datetime.now(timezone.utc)
            self.notification.status = NotificationStatus.READ
            
            await interaction.response.send_message(
                f"✅ Ação '{action}' registrada com sucesso!",
                ephemeral=True
            )
            
            # Desabilitar botões após uso
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(view=self)
            
        except Exception as e:
            logger.error(f"Erro no callback do botão: {e}")
            await interaction.response.send_message(
                "❌ Erro ao processar ação.",
                ephemeral=True
            )

class ModernNotificationSystem:
    """Sistema modernizado de notificações push avançadas"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Inicializar sistemas core
        self.logger = SecureLogger('ModernNotificationSystem')
        self.cache = SmartCache()
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.events = EventSystem()
        self.rate_limiter = RateLimiter()
        
        # Engines especializados
        self.ai_engine = AIPersonalizationEngine()
        self.delivery_engine = SmartDeliveryEngine(bot)
        
        # Armazenamento
        self.notifications: Dict[str, SmartNotification] = {}
        self.user_profiles: Dict[int, UserNotificationProfile] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        
        # Configurações
        self.config = {
            'max_notifications_per_user': 100,
            'cleanup_interval_hours': 24,
            'analytics_retention_days': 30,
            'ai_personalization_enabled': True,
            'smart_delivery_enabled': True
        }
        
        # Inicializar sistema
        self._initialize_system()
        
        self.logger.info("Sistema Modernizado de Notificações inicializado")
    
    def _initialize_system(self):
        """Inicializa o sistema"""
        try:
            # Carregar dados
            asyncio.create_task(self._load_data())
            
            # Criar templates padrão
            self._create_default_templates()
            
            # Iniciar tasks em background
            self._start_background_tasks()
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")
    
    def _create_default_templates(self):
        """Cria templates padrão modernizados"""
        default_templates = [
            NotificationTemplate(
                id="smart_achievement",
                type=NotificationType.ACHIEVEMENT,
                title="🏆 Nova Conquista Desbloqueada!",
                message="Parabéns! Você desbloqueou **{achievement_name}**!\n{achievement_description}",
                color=0xFFD700,
                emoji="🏆",
                priority=NotificationPriority.HIGH,
                ai_enhancement=True,
                personalization_fields=["achievement_name", "achievement_description"],
                target_patterns={UserBehaviorPattern.COMPETITIVE, UserBehaviorPattern.SOCIAL}
            ),
            NotificationTemplate(
                id="personalized_tip",
                type=NotificationType.PERSONALIZED_TIP,
                title="💡 Dica Personalizada",
                message="Com base na sua atividade, temos uma dica para você: {tip_content}",
                color=0x7289DA,
                emoji="💡",
                priority=NotificationPriority.MEDIUM,
                ai_enhancement=True,
                personalization_fields=["tip_content"],
                expires_after_minutes=1440  # 24 horas
            ),
            NotificationTemplate(
                id="engagement_boost",
                type=NotificationType.ENGAGEMENT_BOOST,
                title="🚀 Hora de Voltar à Ação!",
                message="Sentimos sua falta! Que tal participar de {suggested_activity}?",
                color=0xFF6B6B,
                emoji="🚀",
                priority=NotificationPriority.MEDIUM,
                ai_enhancement=True,
                personalization_fields=["suggested_activity"],
                target_patterns={UserBehaviorPattern.LOW_ACTIVITY, UserBehaviorPattern.INACTIVE}
            ),
            NotificationTemplate(
                id="smart_recommendation",
                type=NotificationType.SMART_RECOMMENDATION,
                title="🎯 Recomendação Inteligente",
                message="Baseado no seu perfil, recomendamos: {recommendation}",
                color=0x9B59B6,
                emoji="🎯",
                priority=NotificationPriority.LOW,
                ai_enhancement=True,
                personalization_fields=["recommendation"]
            ),
            NotificationTemplate(
                id="milestone_celebration",
                type=NotificationType.MILESTONE_CELEBRATION,
                title="🎉 Marco Especial Alcançado!",
                message="Incrível! Você alcançou {milestone_name}!\nEste é um momento especial - {celebration_message}",
                color=0x43B581,
                emoji="🎉",
                priority=NotificationPriority.HIGH,
                requires_action=True,
                action_buttons=["Compartilhar", "Ver Detalhes"],
                ai_enhancement=True,
                personalization_fields=["milestone_name", "celebration_message"]
            )
        ]
        
        for template in default_templates:
            self.templates[template.id] = template
    
    async def _load_data(self):
        """Carrega dados do sistema"""
        try:
            # Carregar perfis de usuário do cache
            profiles_data = await self.cache.get('user_notification_profiles') or {}
            for user_id_str, profile_data in profiles_data.items():
                user_id = int(user_id_str)
                profile = UserNotificationProfile(**profile_data)
                self.user_profiles[user_id] = profile
            
            # Carregar notificações pendentes
            notifications_data = await self.cache.get('pending_notifications') or {}
            for notif_id, notif_data in notifications_data.items():
                notification = SmartNotification(**notif_data)
                self.notifications[notif_id] = notification
            
            self.logger.info(f"Dados carregados: {len(self.user_profiles)} perfis, {len(self.notifications)} notificações")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
    
    async def _save_data(self):
        """Salva dados do sistema"""
        try:
            # Salvar perfis de usuário
            profiles_data = {}
            for user_id, profile in self.user_profiles.items():
                profiles_data[str(user_id)] = profile.dict()
            
            await self.cache.set('user_notification_profiles', profiles_data, ttl=86400)
            
            # Salvar notificações pendentes
            notifications_data = {}
            for notif_id, notification in self.notifications.items():
                if notification.status in [NotificationStatus.PENDING, NotificationStatus.SCHEDULED]:
                    notifications_data[notif_id] = notification.dict()
            
            await self.cache.set('pending_notifications', notifications_data, ttl=86400)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")
    
    def _start_background_tasks(self):
        """Inicia tasks em background"""
        try:
            # Task de processamento de notificações
            @tasks.loop(seconds=30)
            async def process_notifications():
                await self._process_notification_queue()
            
            # Task de limpeza
            @tasks.loop(hours=1)
            async def cleanup_task():
                await self._cleanup_expired_notifications()
                await self._update_user_behavior_patterns()
            
            # Task de analytics
            @tasks.loop(minutes=15)
            async def analytics_task():
                await self._update_analytics()
            
            # Iniciar tasks
            process_notifications.start()
            cleanup_task.start()
            analytics_task.start()
            
            self.logger.info("Tasks em background iniciadas")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar tasks: {e}")
    
    async def get_user_profile(self, user_id: int, guild_id: Optional[int] = None) -> UserNotificationProfile:
        """Obtém ou cria perfil de notificações do usuário"""
        profile_key = f"{user_id}_{guild_id}" if guild_id else str(user_id)
        
        if profile_key not in self.user_profiles:
            profile = UserNotificationProfile(user_id=user_id, guild_id=guild_id)
            self.user_profiles[profile_key] = profile
            
            # Detectar padrões iniciais baseados em dados do bot
            await self._detect_initial_behavior_patterns(profile)
        
        return self.user_profiles[profile_key]
    
    async def _detect_initial_behavior_patterns(self, profile: UserNotificationProfile):
        """Detecta padrões iniciais de comportamento"""
        try:
            # Analisar atividade recente do usuário
            user = self.bot.get_user(profile.user_id)
            if not user:
                return
            
            # Padrões baseados em horário de criação da conta
            account_age = datetime.now(timezone.utc) - user.created_at
            if account_age.days < 30:
                profile.behavior_patterns.add(UserBehaviorPattern.CASUAL)
            
            # Padrões baseados em atividade (simulado)
            # Em implementação real, analisaria logs de atividade
            import random
            if random.random() > 0.7:
                profile.behavior_patterns.add(UserBehaviorPattern.HIGHLY_ACTIVE)
            elif random.random() > 0.4:
                profile.behavior_patterns.add(UserBehaviorPattern.MODERATELY_ACTIVE)
            else:
                profile.behavior_patterns.add(UserBehaviorPattern.LOW_ACTIVITY)
            
            # Definir horários de pico aleatórios (em implementação real seria baseado em dados)
            profile.activity_peak_hours = [random.randint(9, 11), random.randint(14, 16), random.randint(19, 22)]
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar padrões iniciais: {e}")
    
    async def create_notification(
        self,
        user_id: int,
        template_id: str,
        data: Dict[str, Any] = None,
        guild_id: Optional[int] = None,
        scheduled_for: Optional[datetime] = None,
        priority_override: Optional[NotificationPriority] = None
    ) -> Optional[SmartNotification]:
        """Cria uma nova notificação inteligente"""
        try:
            # Verificar rate limiting
            rate_key = f"create_notification:{user_id}"
            if await self.rate_limiter.is_rate_limited(rate_key, limit=10, window=60):
                self.logger.warning(f"Rate limit excedido para criação de notificação: {user_id}")
                return None
            
            # Validar template
            if template_id not in self.templates:
                self.logger.error(f"Template não encontrado: {template_id}")
                return None
            
            template = self.templates[template_id]
            profile = await self.get_user_profile(user_id, guild_id)
            
            # Verificar se usuário deve receber este tipo de notificação
            if template.type not in profile.enabled_types:
                self.logger.debug(f"Tipo de notificação desabilitado para usuário {user_id}: {template.type}")
                return None
            
            # Criar notificação base
            notification = SmartNotification(
                user_id=user_id,
                guild_id=guild_id,
                template_id=template_id,
                type=template.type,
                title=template.title,
                message=template.message,
                color=template.color,
                emoji=template.emoji,
                priority=priority_override or template.priority,
                data=data or {},
                delivery_channels=template.delivery_channels,
                requires_action=template.requires_action,
                action_buttons=template.action_buttons.copy(),
                scheduled_for=scheduled_for
            )
            
            # Aplicar expiração se configurada
            if template.expires_after_minutes:
                notification.expires_at = notification.created_at + timedelta(minutes=template.expires_after_minutes)
            
            # Personalizar com dados fornecidos
            if data:
                notification.message = notification.message.format(**data)
                notification.title = notification.title.format(**data)
            
            # Aplicar personalização de IA se habilitada
            if template.ai_enhancement and profile.ai_personalization:
                notification = await self.ai_engine.personalize_notification(notification, profile)
            
            # Adicionar à fila de entrega
            await self.delivery_engine.queue_notification(notification, profile)
            
            # Armazenar notificação
            self.notifications[notification.id] = notification
            
            # Atualizar métricas
            await self.metrics.increment('notifications.created',
                                       tags={'type': template.type.value, 'priority': notification.priority.name})
            
            # Emitir evento
            await self.events.emit('notification_created', {
                'notification_id': notification.id,
                'user_id': user_id,
                'type': template.type.value
            })
            
            # Incrementar rate limiter
            await self.rate_limiter.increment(rate_key, window=60)
            
            self.logger.info(f"Notificação criada: {notification.id} para usuário {user_id}")
            return notification
            
        except Exception as e:
            self.logger.error(f"Erro ao criar notificação: {e}")
            return None
    
    async def get_user_notifications(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[SmartNotification]:
        """Obtém notificações do usuário"""
        try:
            user_notifications = []
            
            for notification in self.notifications.values():
                if notification.user_id != user_id:
                    continue
                
                if guild_id and notification.guild_id != guild_id:
                    continue
                
                if unread_only and notification.status == NotificationStatus.READ:
                    continue
                
                if notification.status == NotificationStatus.EXPIRED:
                    continue
                
                user_notifications.append(notification)
            
            # Ordenar por data de criação (mais recentes primeiro)
            user_notifications.sort(key=lambda n: n.created_at, reverse=True)
            
            return user_notifications[:limit]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter notificações do usuário: {e}")
            return []
    
    async def mark_notification_as_read(self, notification_id: str, user_id: int) -> bool:
        """Marca notificação como lida"""
        try:
            if notification_id not in self.notifications:
                return False
            
            notification = self.notifications[notification_id]
            
            if notification.user_id != user_id:
                return False
            
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.now(timezone.utc)
            
            # Atualizar perfil do usuário
            profile = await self.get_user_profile(user_id, notification.guild_id)
            profile.total_notifications_read += 1
            
            # Calcular tempo de leitura
            if notification.delivered_at:
                read_time = (notification.read_at - notification.delivered_at).total_seconds() / 60
                profile.average_read_time_minutes = (
                    (profile.average_read_time_minutes * (profile.total_notifications_read - 1) + read_time) /
                    profile.total_notifications_read
                )
            
            # Atualizar score de engajamento
            await self._update_engagement_score(profile, notification)
            
            # Métricas
            await self.metrics.increment('notifications.read',
                                       tags={'type': notification.type.value})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao marcar notificação como lida: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: int, guild_id: Optional[int] = None) -> int:
        """Marca todas as notificações como lidas"""
        try:
            marked_count = 0
            
            for notification in self.notifications.values():
                if notification.user_id != user_id:
                    continue
                
                if guild_id and notification.guild_id != guild_id:
                    continue
                
                if notification.status not in [NotificationStatus.DELIVERED, NotificationStatus.PENDING]:
                    continue
                
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.now(timezone.utc)
                marked_count += 1
            
            # Atualizar perfil
            profile = await self.get_user_profile(user_id, guild_id)
            profile.total_notifications_read += marked_count
            
            # Métricas
            await self.metrics.increment('notifications.bulk_read', tags={'count': marked_count})
            
            return marked_count
            
        except Exception as e:
            self.logger.error(f"Erro ao marcar todas como lidas: {e}")
            return 0
    
    async def update_user_preferences(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        **preferences
    ) -> bool:
        """Atualiza preferências do usuário"""
        try:
            profile = await self.get_user_profile(user_id, guild_id)
            
            # Atualizar preferências válidas
            valid_fields = {
                'enabled_types', 'delivery_channels', 'min_priority',
                'quiet_hours_start', 'quiet_hours_end', 'timezone_offset',
                'max_notifications_per_hour', 'max_notifications_per_day',
                'ai_personalization', 'smart_timing', 'behavior_based_filtering',
                'engagement_optimization'
            }
            
            updated_fields = []
            for field, value in preferences.items():
                if field in valid_fields and hasattr(profile, field):
                    setattr(profile, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                await self._save_data()
                
                # Métricas
                await self.metrics.increment('user_preferences.updated',
                                           tags={'user_id': user_id, 'fields': len(updated_fields)})
                
                self.logger.info(f"Preferências atualizadas para usuário {user_id}: {updated_fields}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar preferências: {e}")
            return False
    
    async def _process_notification_queue(self):
        """Processa fila de notificações"""
        try:
            # Processar por ordem de prioridade
            for priority in [NotificationPriority.CRITICAL, NotificationPriority.URGENT, 
                           NotificationPriority.HIGH, NotificationPriority.MEDIUM, NotificationPriority.LOW]:
                
                queue = self.delivery_engine.delivery_queues[priority]
                processed = 0
                
                while queue and processed < self.delivery_engine.batch_size:
                    notification = queue.popleft()
                    
                    # Verificar se não expirou
                    if notification.expires_at and datetime.now(timezone.utc) > notification.expires_at:
                        notification.status = NotificationStatus.EXPIRED
                        continue
                    
                    # Tentar entregar
                    success = await self.delivery_engine.deliver_notification(notification)
                    
                    if not success and notification.delivery_attempts < self.delivery_engine.max_retries:
                        # Reagendar para retry
                        retry_delay = self.delivery_engine.retry_delays[notification.delivery_attempts - 1]
                        notification.scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                        notification.status = NotificationStatus.SCHEDULED
                    
                    processed += 1
            
            # Processar notificações agendadas
            await self._process_scheduled_notifications()
            
        except Exception as e:
            self.logger.error(f"Erro no processamento da fila: {e}")
    
    async def _process_scheduled_notifications(self):
        """Processa notificações agendadas"""
        try:
            now = datetime.now(timezone.utc)
            
            for notification in list(self.notifications.values()):
                if (notification.status == NotificationStatus.SCHEDULED and 
                    notification.scheduled_for and 
                    notification.scheduled_for <= now):
                    
                    # Mover para fila de entrega
                    profile = await self.get_user_profile(notification.user_id, notification.guild_id)
                    await self.delivery_engine.queue_notification(notification, profile)
                    
        except Exception as e:
            self.logger.error(f"Erro no processamento de notificações agendadas: {e}")
    
    async def _cleanup_expired_notifications(self):
        """Remove notificações expiradas"""
        try:
            now = datetime.now(timezone.utc)
            expired_count = 0
            
            for notification_id, notification in list(self.notifications.items()):
                # Remover notificações expiradas
                if (notification.expires_at and now > notification.expires_at) or \
                   (notification.status == NotificationStatus.READ and 
                    (now - notification.read_at).days > 7):
                    
                    notification.status = NotificationStatus.EXPIRED
                    del self.notifications[notification_id]
                    expired_count += 1
            
            if expired_count > 0:
                await self.metrics.gauge('notifications.expired_cleaned', expired_count)
                self.logger.info(f"Limpeza concluída: {expired_count} notificações removidas")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")
    
    async def _update_user_behavior_patterns(self):
        """Atualiza padrões de comportamento dos usuários"""
        try:
            for profile in self.user_profiles.values():
                # Analisar atividade recente
                if profile.last_activity:
                    time_since_activity = datetime.now(timezone.utc) - profile.last_activity
                    
                    # Atualizar padrões baseados em inatividade
                    if time_since_activity.days > 14:
                        profile.behavior_patterns.discard(UserBehaviorPattern.HIGHLY_ACTIVE)
                        profile.behavior_patterns.add(UserBehaviorPattern.INACTIVE)
                    elif time_since_activity.days > 7:
                        profile.behavior_patterns.discard(UserBehaviorPattern.HIGHLY_ACTIVE)
                        profile.behavior_patterns.add(UserBehaviorPattern.LOW_ACTIVITY)
                
                # Atualizar score de engajamento baseado em leituras recentes
                if profile.total_notifications_received > 0:
                    read_rate = profile.total_notifications_read / profile.total_notifications_received
                    profile.engagement_score = (profile.engagement_score + read_rate) / 2
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar padrões de comportamento: {e}")
    
    async def _update_engagement_score(self, profile: UserNotificationProfile, notification: SmartNotification):
        """Atualiza score de engajamento baseado na interação"""
        try:
            # Calcular score baseado em vários fatores
            base_score = 0.5
            
            # Bonus por leitura rápida
            if notification.delivered_at and notification.read_at:
                read_time = (notification.read_at - notification.delivered_at).total_seconds() / 60
                if read_time < 5:  # Leu em menos de 5 minutos
                    base_score += 0.2
                elif read_time < 60:  # Leu em menos de 1 hora
                    base_score += 0.1
            
            # Bonus por interação com botões
            if notification.user_reaction:
                base_score += 0.3
            
            # Bonus por tipo de notificação preferido
            if notification.type in profile.preferred_notification_types:
                base_score += 0.1
            
            # Atualizar score do perfil (média móvel)
            profile.engagement_score = (profile.engagement_score * 0.8) + (base_score * 0.2)
            profile.engagement_score = max(0.0, min(1.0, profile.engagement_score))
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar score de engajamento: {e}")
    
    async def _update_analytics(self):
        """Atualiza analytics do sistema"""
        try:
            analytics = NotificationAnalytics()
            
            # Contar notificações por status
            for notification in self.notifications.values():
                analytics.total_sent += 1
                
                if notification.status == NotificationStatus.DELIVERED:
                    analytics.total_delivered += 1
                elif notification.status == NotificationStatus.READ:
                    analytics.total_read += 1
                elif notification.status == NotificationStatus.FAILED:
                    analytics.total_failed += 1
                elif notification.status == NotificationStatus.EXPIRED:
                    analytics.total_expired += 1
                
                # Por tipo
                type_key = notification.type.value
                analytics.by_type[type_key] = analytics.by_type.get(type_key, 0) + 1
                
                # Por prioridade
                priority_key = notification.priority.name
                analytics.by_priority[priority_key] = analytics.by_priority.get(priority_key, 0) + 1
                
                # Por canal
                for channel in notification.delivery_channels:
                    channel_key = channel.value
                    analytics.by_channel[channel_key] = analytics.by_channel.get(channel_key, 0) + 1
                
                # Por hora
                if notification.created_at:
                    hour = notification.created_at.hour
                    analytics.by_hour[hour] = analytics.by_hour.get(hour, 0) + 1
            
            # Calcular taxas
            if analytics.total_sent > 0:
                analytics.delivery_rate = analytics.total_delivered / analytics.total_sent
                analytics.read_rate = analytics.total_read / analytics.total_sent
                analytics.engagement_rate = (analytics.total_read + (analytics.total_delivered * 0.5)) / analytics.total_sent
            
            # Identificar horários de pico
            if analytics.by_hour:
                sorted_hours = sorted(analytics.by_hour.items(), key=lambda x: x[1], reverse=True)
                analytics.peak_hours = [hour for hour, count in sorted_hours[:3]]
            
            # Tipos mais engajantes
            if analytics.by_type:
                sorted_types = sorted(analytics.by_type.items(), key=lambda x: x[1], reverse=True)
                analytics.most_engaging_types = [type_name for type_name, count in sorted_types[:5]]
            
            # Salvar analytics no cache
            await self.cache.set('notification_analytics', analytics.dict(), ttl=3600)
            
            # Métricas
            await self.metrics.gauge('notifications.total_active', len(self.notifications))
            await self.metrics.gauge('notifications.delivery_rate', analytics.delivery_rate)
            await self.metrics.gauge('notifications.read_rate', analytics.read_rate)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar analytics: {e}")
    
    async def get_analytics(self) -> Optional[NotificationAnalytics]:
        """Obtém analytics do sistema"""
        try:
            analytics_data = await self.cache.get('notification_analytics')
            if analytics_data:
                return NotificationAnalytics(**analytics_data)
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter analytics: {e}")
            return None
    
    async def create_custom_template(
        self,
        template_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        **kwargs
    ) -> bool:
        """Cria template personalizado"""
        try:
            if template_id in self.templates:
                self.logger.warning(f"Template já existe: {template_id}")
                return False
            
            template = NotificationTemplate(
                id=template_id,
                type=notification_type,
                title=title,
                message=message,
                **kwargs
            )
            
            self.templates[template_id] = template
            
            # Salvar templates no cache
            templates_data = {tid: tmpl.dict() for tid, tmpl in self.templates.items()}
            await self.cache.set('notification_templates', templates_data, ttl=86400)
            
            self.logger.info(f"Template personalizado criado: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar template personalizado: {e}")
            return False
    
    async def send_broadcast_notification(
        self,
        template_id: str,
        target_users: List[int],
        data: Dict[str, Any] = None,
        guild_id: Optional[int] = None
    ) -> int:
        """Envia notificação em broadcast para múltiplos usuários"""
        try:
            sent_count = 0
            
            for user_id in target_users:
                notification = await self.create_notification(
                    user_id=user_id,
                    template_id=template_id,
                    data=data,
                    guild_id=guild_id
                )
                
                if notification:
                    sent_count += 1
                
                # Rate limiting para broadcasts
                await asyncio.sleep(0.1)
            
            await self.metrics.increment('notifications.broadcast_sent', 
                                       tags={'count': sent_count, 'template': template_id})
            
            self.logger.info(f"Broadcast enviado: {sent_count}/{len(target_users)} notificações")
            return sent_count
            
        except Exception as e:
            self.logger.error(f"Erro no broadcast: {e}")
            return 0
    
    async def get_user_statistics(self, user_id: int, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtém estatísticas detalhadas do usuário"""
        try:
            profile = await self.get_user_profile(user_id, guild_id)
            user_notifications = await self.get_user_notifications(user_id, guild_id, limit=1000)
            
            stats = {
                'profile': {
                    'total_received': profile.total_notifications_received,
                    'total_read': profile.total_notifications_read,
                    'engagement_score': profile.engagement_score,
                    'average_read_time': profile.average_read_time_minutes,
                    'behavior_patterns': [p.value for p in profile.behavior_patterns],
                    'preferred_types': [t.value for t in profile.preferred_notification_types]
                },
                'recent_activity': {
                    'total_notifications': len(user_notifications),
                    'unread_count': len([n for n in user_notifications if n.status != NotificationStatus.READ]),
                    'last_notification': user_notifications[0].created_at.isoformat() if user_notifications else None
                },
                'preferences': {
                    'enabled_types': [t.value for t in profile.enabled_types],
                    'delivery_channels': [c.value for c in profile.delivery_channels],
                    'min_priority': profile.min_priority.name,
                    'quiet_hours': f"{profile.quiet_hours_start:02d}:00 - {profile.quiet_hours_end:02d}:00",
                    'ai_personalization': profile.ai_personalization,
                    'smart_timing': profile.smart_timing
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do usuário: {e}")
            return {}
    
    async def optimize_delivery_times(self):
        """Otimiza horários de entrega baseado em dados históricos"""
        try:
            for profile in self.user_profiles.values():
                if profile.total_notifications_read < 10:
                    continue  # Dados insuficientes
                
                # Analisar horários de leitura mais frequentes
                read_hours = []
                for notification in self.notifications.values():
                    if (notification.user_id == profile.user_id and 
                        notification.read_at and 
                        notification.status == NotificationStatus.READ):
                        read_hours.append(notification.read_at.hour)
                
                if read_hours:
                    # Encontrar horários de pico
                    from collections import Counter
                    hour_counts = Counter(read_hours)
                    peak_hours = [hour for hour, count in hour_counts.most_common(3)]
                    profile.activity_peak_hours = peak_hours
            
            self.logger.info("Otimização de horários de entrega concluída")
            
        except Exception as e:
            self.logger.error(f"Erro na otimização de horários: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do sistema"""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metrics': {
                    'total_notifications': len(self.notifications),
                    'total_users': len(self.user_profiles),
                    'total_templates': len(self.templates),
                    'pending_notifications': len([n for n in self.notifications.values() 
                                                if n.status == NotificationStatus.PENDING]),
                    'scheduled_notifications': len([n for n in self.notifications.values() 
                                                  if n.status == NotificationStatus.SCHEDULED])
                },
                'queues': {
                    priority.name: len(queue) 
                    for priority, queue in self.delivery_engine.delivery_queues.items()
                },
                'system': {
                    'ai_personalization_enabled': self.config['ai_personalization_enabled'],
                    'smart_delivery_enabled': self.config['smart_delivery_enabled'],
                    'cache_status': 'connected',  # Simplificado
                    'metrics_status': 'connected'  # Simplificado
                }
            }
            
            # Verificar problemas
            issues = []
            
            if health['metrics']['pending_notifications'] > 100:
                issues.append('High number of pending notifications')
                health['status'] = 'warning'
            
            if health['metrics']['total_notifications'] > 10000:
                issues.append('High memory usage - consider cleanup')
                health['status'] = 'warning'
            
            if issues:
                health['issues'] = issues
            
            return health
            
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def shutdown(self):
        """Encerra o sistema graciosamente"""
        try:
            self.logger.info("Iniciando shutdown do sistema de notificações...")
            
            # Salvar dados
            await self._save_data()
            
            # Parar tasks em background
            for task in asyncio.all_tasks():
                if task.get_name().startswith('notification_'):
                    task.cancel()
            
            # Limpar cache
            await self.cache.clear()
            
            self.logger.info("Sistema de notificações encerrado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro no shutdown: {e}")

# Função de inicialização para uso em outros módulos
async def initialize_modern_notification_system(bot: commands.Bot) -> ModernNotificationSystem:
    """Inicializa o sistema modernizado de notificações"""
    try:
        system = ModernNotificationSystem(bot)
        
        # Aguardar inicialização completa
        await asyncio.sleep(1)
        
        logger.info("Sistema Modernizado de Notificações inicializado com sucesso")
        return system
        
    except Exception as e:
        logger.error(f"Erro na inicialização do sistema de notificações: {e}")
        raise

if __name__ == "__main__":
    # Teste básico do sistema
    import asyncio
    
    async def test_system():
        # Mock bot para teste
        class MockBot:
            def get_user(self, user_id): return None
            async def fetch_user(self, user_id): return None
        
        bot = MockBot()
        system = ModernNotificationSystem(bot)
        
        # Teste de criação de notificação
        notification = await system.create_notification(
            user_id=123456789,
            template_id="smart_achievement",
            data={"achievement_name": "Primeiro Login", "achievement_description": "Bem-vindo ao servidor!"}
        )
        
        if notification:
            print(f"✅ Notificação criada: {notification.id}")
        else:
            print("❌ Falha ao criar notificação")
        
        # Teste de health check
        health = await system.health_check()
        print(f"🏥 Health Check: {health['status']}")
    
    # Executar teste se executado diretamente
    # asyncio.run(test_system())