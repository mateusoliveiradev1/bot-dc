#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Notificações Push Personalizadas - Hawk Bot
Desenvolvido para envio de alertas e notificações customizáveis

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
from collections import defaultdict

logger = logging.getLogger('HawkBot.NotificationsSystem')

class NotificationType(Enum):
    """Tipos de notificações disponíveis"""
    RANK_UPDATE = "rank_update"
    NEW_ACHIEVEMENT = "new_achievement"
    TOURNAMENT_START = "tournament_start"
    TOURNAMENT_RESULT = "tournament_result"
    DAILY_CHALLENGE = "daily_challenge"
    MINIGAME_MILESTONE = "minigame_milestone"
    MODERATION_ALERT = "moderation_alert"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    CUSTOM_REMINDER = "custom_reminder"
    BIRTHDAY = "birthday"
    CLAN_NEWS = "clan_news"
    PUBG_STATS_UPDATE = "pubg_stats_update"

class NotificationPriority(Enum):
    """Prioridades das notificações"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template para notificações"""
    id: str
    type: NotificationType
    title: str
    message: str
    color: int
    emoji: str
    priority: NotificationPriority
    requires_action: bool = False
    action_button: Optional[str] = None
    expires_after: Optional[int] = None  # minutos

@dataclass
class UserNotification:
    """Notificação individual do usuário"""
    id: str
    user_id: int
    template_id: str
    title: str
    message: str
    color: int
    emoji: str
    priority: NotificationPriority
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    data: Optional[Dict] = None
    requires_action: bool = False
    action_button: Optional[str] = None
    is_sent: bool = False
    is_read: bool = False
    is_expired: bool = False

class NotificationPreferences:
    """Preferências de notificação do usuário"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.enabled_types = set(NotificationType)
        self.dm_enabled = True
        self.channel_enabled = True
        self.quiet_hours_start = 22  # 22:00
        self.quiet_hours_end = 8     # 08:00
        self.min_priority = NotificationPriority.LOW
        self.custom_settings = {}
    
    def is_type_enabled(self, notification_type: NotificationType) -> bool:
        """Verifica se um tipo de notificação está habilitado"""
        return notification_type in self.enabled_types
    
    def is_quiet_time(self) -> bool:
        """Verifica se está no horário silencioso"""
        current_hour = datetime.now().hour
        if self.quiet_hours_start > self.quiet_hours_end:
            # Horário atravessa meia-noite (ex: 22:00 - 08:00)
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            # Horário normal (ex: 08:00 - 22:00)
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
    
    def should_receive(self, notification: UserNotification) -> bool:
        """Determina se o usuário deve receber a notificação"""
        # Verificar se o tipo está habilitado
        notification_type = NotificationType(notification.template_id.split('_')[0])
        if not self.is_type_enabled(notification_type):
            return False
        
        # Verificar prioridade mínima
        priority_order = [NotificationPriority.LOW, NotificationPriority.MEDIUM, 
                         NotificationPriority.HIGH, NotificationPriority.URGENT]
        if priority_order.index(notification.priority) < priority_order.index(self.min_priority):
            return False
        
        # Verificar horário silencioso (exceto urgentes)
        if notification.priority != NotificationPriority.URGENT and self.is_quiet_time():
            return False
        
        return True

class NotificationsSystem:
    """Sistema principal de notificações push"""
    
    def __init__(self, bot: commands.Bot, storage):
        self.bot = bot
        self.storage = storage
        self.logger = logging.getLogger('HawkBot.NotificationsSystem')
        
        # Armazenamento
        self.notifications_file = 'notifications_data.json'
        self.templates_file = 'notification_templates.json'
        
        # Cache em memória
        self.user_notifications: Dict[int, List[UserNotification]] = defaultdict(list)
        self.user_preferences: Dict[int, NotificationPreferences] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.pending_notifications: List[UserNotification] = []
        
        # Configurações
        self.max_notifications_per_user = 50
        self.cleanup_interval_hours = 24
        self.batch_send_size = 10
        
        # Inicializar sistema
        self._load_data()
        self._create_default_templates()
        
        self.logger.info("Sistema de Notificações Push inicializado")
    
    def _load_data(self):
        """Carrega dados de notificações e preferências"""
        try:
            # Carregar notificações
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for user_id_str, notifications_data in data.get('notifications', {}).items():
                        user_id = int(user_id_str)
                        for notif_data in notifications_data:
                            notification = self._dict_to_notification(notif_data)
                            self.user_notifications[user_id].append(notification)
                    
                    for user_id_str, prefs_data in data.get('preferences', {}).items():
                        user_id = int(user_id_str)
                        prefs = NotificationPreferences(user_id)
                        prefs.enabled_types = set(NotificationType(t) for t in prefs_data.get('enabled_types', []))
                        prefs.dm_enabled = prefs_data.get('dm_enabled', True)
                        prefs.channel_enabled = prefs_data.get('channel_enabled', True)
                        prefs.quiet_hours_start = prefs_data.get('quiet_hours_start', 22)
                        prefs.quiet_hours_end = prefs_data.get('quiet_hours_end', 8)
                        prefs.min_priority = NotificationPriority(prefs_data.get('min_priority', 'low'))
                        prefs.custom_settings = prefs_data.get('custom_settings', {})
                        self.user_preferences[user_id] = prefs
            
            # Carregar templates
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates_data = json.load(f)
                    for template_id, template_data in templates_data.items():
                        template = NotificationTemplate(
                            id=template_data['id'],
                            type=NotificationType(template_data['type']),
                            title=template_data['title'],
                            message=template_data['message'],
                            color=template_data['color'],
                            emoji=template_data['emoji'],
                            priority=NotificationPriority(template_data['priority']),
                            requires_action=template_data.get('requires_action', False),
                            action_button=template_data.get('action_button'),
                            expires_after=template_data.get('expires_after')
                        )
                        self.templates[template_id] = template
                        
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados de notificações: {e}")
    
    def _save_data(self):
        """Salva dados de notificações e preferências"""
        try:
            # Preparar dados para salvar
            notifications_data = {}
            for user_id, notifications in self.user_notifications.items():
                notifications_data[str(user_id)] = [
                    self._notification_to_dict(notif) for notif in notifications
                ]
            
            preferences_data = {}
            for user_id, prefs in self.user_preferences.items():
                preferences_data[str(user_id)] = {
                    'enabled_types': [t.value for t in prefs.enabled_types],
                    'dm_enabled': prefs.dm_enabled,
                    'channel_enabled': prefs.channel_enabled,
                    'quiet_hours_start': prefs.quiet_hours_start,
                    'quiet_hours_end': prefs.quiet_hours_end,
                    'min_priority': prefs.min_priority.value,
                    'custom_settings': prefs.custom_settings
                }
            
            # Salvar notificações
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'notifications': notifications_data,
                    'preferences': preferences_data
                }, f, indent=2, ensure_ascii=False, default=str)
            
            # Salvar templates
            templates_data = {}
            for template_id, template in self.templates.items():
                templates_data[template_id] = {
                    'id': template.id,
                    'type': template.type.value,
                    'title': template.title,
                    'message': template.message,
                    'color': template.color,
                    'emoji': template.emoji,
                    'priority': template.priority.value,
                    'requires_action': template.requires_action,
                    'action_button': template.action_button,
                    'expires_after': template.expires_after
                }
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados de notificações: {e}")
    
    def _notification_to_dict(self, notification: UserNotification) -> Dict:
        """Converte notificação para dicionário"""
        return {
            'id': notification.id,
            'user_id': notification.user_id,
            'template_id': notification.template_id,
            'title': notification.title,
            'message': notification.message,
            'color': notification.color,
            'emoji': notification.emoji,
            'priority': notification.priority.value,
            'created_at': notification.created_at.isoformat(),
            'scheduled_for': notification.scheduled_for.isoformat() if notification.scheduled_for else None,
            'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
            'data': notification.data,
            'requires_action': notification.requires_action,
            'action_button': notification.action_button,
            'is_sent': notification.is_sent,
            'is_read': notification.is_read,
            'is_expired': notification.is_expired
        }
    
    def _dict_to_notification(self, data: Dict) -> UserNotification:
        """Converte dicionário para notificação"""
        return UserNotification(
            id=data['id'],
            user_id=data['user_id'],
            template_id=data['template_id'],
            title=data['title'],
            message=data['message'],
            color=data['color'],
            emoji=data['emoji'],
            priority=NotificationPriority(data['priority']),
            created_at=datetime.fromisoformat(data['created_at']),
            scheduled_for=datetime.fromisoformat(data['scheduled_for']) if data.get('scheduled_for') else None,
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            read_at=datetime.fromisoformat(data['read_at']) if data.get('read_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            data=data.get('data'),
            requires_action=data.get('requires_action', False),
            action_button=data.get('action_button'),
            is_sent=data.get('is_sent', False),
            is_read=data.get('is_read', False),
            is_expired=data.get('is_expired', False)
        )
    
    def _create_default_templates(self):
        """Cria templates padrão de notificações"""
        default_templates = [
            NotificationTemplate(
                id="rank_update_promotion",
                type=NotificationType.RANK_UPDATE,
                title="🎉 Promoção de Rank!",
                message="Parabéns! Você subiu para o rank **{new_rank}** com {points} pontos!",
                color=0x43B581,
                emoji="🎉",
                priority=NotificationPriority.HIGH
            ),
            NotificationTemplate(
                id="achievement_unlocked",
                type=NotificationType.NEW_ACHIEVEMENT,
                title="🏆 Nova Conquista Desbloqueada!",
                message="Você desbloqueou a conquista **{achievement_name}**!\n{achievement_description}",
                color=0xFFD700,
                emoji="🏆",
                priority=NotificationPriority.MEDIUM
            ),
            NotificationTemplate(
                id="tournament_starting",
                type=NotificationType.TOURNAMENT_START,
                title="⚔️ Torneio Iniciando!",
                message="O torneio **{tournament_name}** está começando em {time_remaining}!\nPrepare-se para a batalha!",
                color=0xF04747,
                emoji="⚔️",
                priority=NotificationPriority.HIGH,
                requires_action=True,
                action_button="Participar"
            ),
            NotificationTemplate(
                id="daily_challenge_available",
                type=NotificationType.DAILY_CHALLENGE,
                title="🎯 Novo Desafio Diário!",
                message="Um novo desafio diário está disponível!\n**{challenge_name}**\nRecompensa: {reward}",
                color=0x7289DA,
                emoji="🎯",
                priority=NotificationPriority.MEDIUM
            ),
            NotificationTemplate(
                id="minigame_milestone",
                type=NotificationType.MINIGAME_MILESTONE,
                title="🎮 Marco Alcançado!",
                message="Você alcançou um marco nos mini-games!\n**{milestone_name}**\n{description}",
                color=0x9B59B6,
                emoji="🎮",
                priority=NotificationPriority.LOW
            ),
            NotificationTemplate(
                id="system_announcement",
                type=NotificationType.SYSTEM_ANNOUNCEMENT,
                title="📢 Anúncio do Sistema",
                message="{announcement_text}",
                color=0x00D4AA,
                emoji="📢",
                priority=NotificationPriority.MEDIUM
            ),
            NotificationTemplate(
                id="birthday_reminder",
                type=NotificationType.BIRTHDAY,
                title="🎂 Feliz Aniversário!",
                message="Hoje é seu aniversário! 🎉\nA equipe Hawk Esports deseja um feliz aniversário!\nVocê ganhou um presente especial!",
                color=0xFF69B4,
                emoji="🎂",
                priority=NotificationPriority.HIGH
            )
        ]
        
        for template in default_templates:
            if template.id not in self.templates:
                self.templates[template.id] = template
    
    def _start_background_tasks(self):
        """Inicia tarefas em background"""
        if not self.notification_sender.is_running():
            self.notification_sender.start()
        if not self.cleanup_task.is_running():
            self.cleanup_task.start()
    
    def start_tasks(self):
        """Inicia as tasks após o bot estar pronto"""
        self._start_background_tasks()
        self.logger.info("Tasks de notificações iniciadas")
    
    def get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """Obtém preferências do usuário"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = NotificationPreferences(user_id)
        return self.user_preferences[user_id]
    
    async def create_notification(self, user_id: int, template_id: str, 
                                data: Optional[Dict] = None, 
                                scheduled_for: Optional[datetime] = None) -> Optional[UserNotification]:
        """Cria uma nova notificação"""
        try:
            if template_id not in self.templates:
                self.logger.error(f"Template {template_id} não encontrado")
                return None
            
            template = self.templates[template_id]
            
            # Formatar mensagem com dados
            title = template.title
            message = template.message
            if data:
                title = title.format(**data)
                message = message.format(**data)
            
            # Calcular expiração
            expires_at = None
            if template.expires_after:
                expires_at = datetime.now() + timedelta(minutes=template.expires_after)
            
            # Criar notificação
            notification = UserNotification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                template_id=template_id,
                title=title,
                message=message,
                color=template.color,
                emoji=template.emoji,
                priority=template.priority,
                created_at=datetime.now(),
                scheduled_for=scheduled_for,
                expires_at=expires_at,
                data=data,
                requires_action=template.requires_action,
                action_button=template.action_button
            )
            
            # Verificar se usuário deve receber
            user_prefs = self.get_user_preferences(user_id)
            if not user_prefs.should_receive(notification):
                self.logger.info(f"Notificação {notification.id} filtrada pelas preferências do usuário {user_id}")
                return None
            
            # Adicionar à lista do usuário
            self.user_notifications[user_id].append(notification)
            
            # Limitar número de notificações por usuário
            if len(self.user_notifications[user_id]) > self.max_notifications_per_user:
                # Remover notificações mais antigas
                self.user_notifications[user_id] = sorted(
                    self.user_notifications[user_id], 
                    key=lambda n: n.created_at, 
                    reverse=True
                )[:self.max_notifications_per_user]
            
            # Adicionar à fila de envio se não agendada
            if not scheduled_for:
                self.pending_notifications.append(notification)
            
            self.logger.info(f"Notificação criada: {notification.id} para usuário {user_id}")
            return notification
            
        except Exception as e:
            self.logger.error(f"Erro ao criar notificação: {e}")
            return None
    
    async def send_notification(self, notification: UserNotification) -> bool:
        """Envia uma notificação específica"""
        try:
            if notification.is_sent or notification.is_expired:
                return False
            
            # Verificar se expirou
            if notification.expires_at and datetime.now() > notification.expires_at:
                notification.is_expired = True
                return False
            
            user = self.bot.get_user(notification.user_id)
            if not user:
                self.logger.warning(f"Usuário {notification.user_id} não encontrado")
                return False
            
            # Criar embed
            embed = discord.Embed(
                title=f"{notification.emoji} {notification.title}",
                description=notification.message,
                color=notification.color,
                timestamp=notification.created_at
            )
            
            # Adicionar campos extras se houver dados
            if notification.data:
                for key, value in notification.data.items():
                    if key not in ['achievement_name', 'tournament_name', 'challenge_name', 'milestone_name']:
                        embed.add_field(name=key.replace('_', ' ').title(), value=str(value), inline=True)
            
            embed.set_footer(text="Hawk Bot - Sistema de Notificações")
            
            # Tentar enviar DM primeiro
            user_prefs = self.get_user_preferences(notification.user_id)
            sent = False
            
            if user_prefs.dm_enabled:
                try:
                    await user.send(embed=embed)
                    sent = True
                    self.logger.info(f"Notificação {notification.id} enviada via DM para {user.display_name}")
                except discord.Forbidden:
                    self.logger.warning(f"Não foi possível enviar DM para {user.display_name}")
            
            # Se DM falhou e canal está habilitado, tentar canal
            if not sent and user_prefs.channel_enabled:
                # Encontrar canal de notificações ou canal geral
                guild = self.bot.guilds[0] if self.bot.guilds else None
                if guild:
                    notification_channel = discord.utils.get(guild.channels, name='notificações') or \
                                         discord.utils.get(guild.channels, name='geral') or \
                                         guild.system_channel
                    
                    if notification_channel:
                        try:
                            await notification_channel.send(f"{user.mention}", embed=embed)
                            sent = True
                            self.logger.info(f"Notificação {notification.id} enviada via canal para {user.display_name}")
                        except discord.Forbidden:
                            self.logger.warning(f"Não foi possível enviar no canal para {user.display_name}")
            
            if sent:
                notification.is_sent = True
                notification.sent_at = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação {notification.id}: {e}")
            return False
    
    @tasks.loop(seconds=30)
    async def notification_sender(self):
        """Task para enviar notificações pendentes"""
        try:
            if not self.pending_notifications:
                return
            
            # Processar em lotes
            batch = self.pending_notifications[:self.batch_send_size]
            self.pending_notifications = self.pending_notifications[self.batch_send_size:]
            
            for notification in batch:
                # Verificar se é hora de enviar (para notificações agendadas)
                if notification.scheduled_for and datetime.now() < notification.scheduled_for:
                    self.pending_notifications.append(notification)  # Reagendar
                    continue
                
                await self.send_notification(notification)
                await asyncio.sleep(1)  # Evitar rate limit
            
            # Salvar dados periodicamente
            if len(self.pending_notifications) % 50 == 0:
                self._save_data()
                
        except Exception as e:
            self.logger.error(f"Erro no sender de notificações: {e}")
    
    @tasks.loop(hours=1)
    async def cleanup_task(self):
        """Task para limpeza de notificações antigas"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned_count = 0
            
            for user_id in list(self.user_notifications.keys()):
                original_count = len(self.user_notifications[user_id])
                
                # Remover notificações antigas ou expiradas
                self.user_notifications[user_id] = [
                    notif for notif in self.user_notifications[user_id]
                    if notif.created_at > cutoff_date and not notif.is_expired
                ]
                
                cleaned_count += original_count - len(self.user_notifications[user_id])
                
                # Remover usuário se não tem notificações
                if not self.user_notifications[user_id]:
                    del self.user_notifications[user_id]
            
            if cleaned_count > 0:
                self.logger.info(f"Limpeza concluída: {cleaned_count} notificações removidas")
                self._save_data()
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza de notificações: {e}")
    
    async def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                                   limit: int = 10) -> List[UserNotification]:
        """Obtém notificações do usuário"""
        notifications = self.user_notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.is_read]
        
        # Ordenar por data de criação (mais recentes primeiro)
        notifications = sorted(notifications, key=lambda n: n.created_at, reverse=True)
        
        return notifications[:limit]
    
    async def mark_as_read(self, user_id: int, notification_id: str) -> bool:
        """Marca notificação como lida"""
        try:
            for notification in self.user_notifications.get(user_id, []):
                if notification.id == notification_id:
                    notification.is_read = True
                    notification.read_at = datetime.now()
                    self._save_data()
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao marcar notificação como lida: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Marca todas as notificações como lidas"""
        try:
            count = 0
            for notification in self.user_notifications.get(user_id, []):
                if not notification.is_read:
                    notification.is_read = True
                    notification.read_at = datetime.now()
                    count += 1
            
            if count > 0:
                self._save_data()
            
            return count
        except Exception as e:
            self.logger.error(f"Erro ao marcar todas as notificações como lidas: {e}")
            return 0
    
    async def update_user_preferences(self, user_id: int, **kwargs) -> bool:
        """Atualiza preferências do usuário"""
        try:
            prefs = self.get_user_preferences(user_id)
            
            for key, value in kwargs.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            self._save_data()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao atualizar preferências: {e}")
            return False
    
    async def create_custom_reminder(self, user_id: int, title: str, message: str, 
                                   scheduled_for: datetime, priority: NotificationPriority = NotificationPriority.MEDIUM) -> Optional[UserNotification]:
        """Cria um lembrete personalizado"""
        try:
            # Criar template temporário
            template_id = f"custom_reminder_{uuid.uuid4().hex[:8]}"
            
            notification = UserNotification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                template_id=template_id,
                title=f"⏰ {title}",
                message=message,
                color=0xFFA500,
                emoji="⏰",
                priority=priority,
                created_at=datetime.now(),
                scheduled_for=scheduled_for
            )
            
            self.user_notifications[user_id].append(notification)
            self.pending_notifications.append(notification)
            
            self.logger.info(f"Lembrete personalizado criado: {notification.id}")
            return notification
            
        except Exception as e:
            self.logger.error(f"Erro ao criar lembrete personalizado: {e}")
            return None
    
    async def broadcast_announcement(self, title: str, message: str, 
                                   priority: NotificationPriority = NotificationPriority.MEDIUM,
                                   target_users: Optional[List[int]] = None) -> int:
        """Envia anúncio para múltiplos usuários"""
        try:
            sent_count = 0
            
            # Se não especificou usuários, enviar para todos com preferências
            if target_users is None:
                target_users = list(self.user_preferences.keys())
            
            for user_id in target_users:
                notification = await self.create_notification(
                    user_id=user_id,
                    template_id="system_announcement",
                    data={'announcement_text': message}
                )
                
                if notification:
                    sent_count += 1
            
            self.logger.info(f"Anúncio enviado para {sent_count} usuários")
            return sent_count
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar anúncio: {e}")
            return 0
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema de notificações"""
        total_notifications = sum(len(notifications) for notifications in self.user_notifications.values())
        total_users = len(self.user_preferences)
        pending_count = len(self.pending_notifications)
        
        # Estatísticas por tipo
        type_stats = defaultdict(int)
        priority_stats = defaultdict(int)
        
        for notifications in self.user_notifications.values():
            for notif in notifications:
                type_stats[notif.template_id] += 1
                priority_stats[notif.priority.value] += 1
        
        return {
            'total_notifications': total_notifications,
            'total_users': total_users,
            'pending_notifications': pending_count,
            'templates_count': len(self.templates),
            'type_distribution': dict(type_stats),
            'priority_distribution': dict(priority_stats)
        }
    
    def stop(self):
        """Para o sistema de notificações"""
        try:
            self.notification_sender.cancel()
            self.cleanup_task.cancel()
            self._save_data()
            self.logger.info("Sistema de Notificações parado")
        except Exception as e:
            self.logger.error(f"Erro ao parar sistema de notificações: {e}")
    
    @notification_sender.before_loop
    async def before_notification_sender(self):
        await self.bot.wait_until_ready()
    
    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        await self.bot.wait_until_ready()