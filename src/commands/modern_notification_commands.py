#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos Modernizados para Sistema de Notificações Push Avançadas
Comandos inteligentes com IA, personalização e analytics avançados

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

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
    
    class MetricsCollector:
        def __init__(self): pass
        async def increment(self, metric, tags=None): pass
        async def gauge(self, metric, value, tags=None): pass
    
    class DataValidator:
        def __init__(self): pass
        def validate_user_input(self, data): return True
        def sanitize_content(self, content): return content
    
    class EventSystem:
        def __init__(self): pass
        async def emit(self, event, data): pass
    
    class RateLimiter:
        def __init__(self): pass
        async def is_rate_limited(self, key, limit, window): return False
        async def increment(self, key, window): pass

# Importar sistema de notificações
try:
    from src.features.notifications.modern_system import (
        ModernNotificationSystem,
        NotificationType,
        NotificationPriority,
        DeliveryChannel,
        UserBehaviorPattern
    )
except ImportError:
    # Mock para desenvolvimento
    class ModernNotificationSystem:
        def __init__(self, bot): pass
        async def get_user_profile(self, user_id, guild_id=None): return None
        async def get_user_notifications(self, user_id, guild_id=None, unread_only=False, limit=20): return []
        async def mark_notification_as_read(self, notification_id, user_id): return True
        async def mark_all_as_read(self, user_id, guild_id=None): return 0
        async def update_user_preferences(self, user_id, guild_id=None, **preferences): return True
        async def get_analytics(self): return None
        async def get_user_statistics(self, user_id, guild_id=None): return {}
        async def create_custom_template(self, template_id, notification_type, title, message, **kwargs): return True
        async def send_broadcast_notification(self, template_id, target_users, data=None, guild_id=None): return 0
        async def health_check(self): return {'status': 'healthy'}
    
    class NotificationType(Enum):
        ACHIEVEMENT = "achievement"
        SYSTEM = "system"
    
    class NotificationPriority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    class DeliveryChannel(Enum):
        DM = "dm"
        GUILD_CHANNEL = "guild_channel"
    
    class UserBehaviorPattern(Enum):
        COMPETITIVE = "competitive"
        SOCIAL = "social"

# Configurar logger
logger = SecureLogger('ModernNotificationCommands')

class NotificationSettingsView(discord.ui.View):
    """View interativa para configurações de notificações"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int] = None):
        super().__init__(timeout=300)
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
        self.profile = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id
    
    @discord.ui.button(label="🔔 Tipos de Notificação", style=discord.ButtonStyle.primary)
    async def notification_types(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configurar tipos de notificação"""
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="🔔 Configurar Tipos de Notificação",
                description="Escolha quais tipos de notificação você deseja receber:",
                color=0x7289DA
            )
            
            # Criar select menu para tipos
            type_options = []
            for notif_type in NotificationType:
                is_enabled = notif_type in profile.enabled_types
                emoji = "✅" if is_enabled else "❌"
                type_options.append(discord.SelectOption(
                    label=notif_type.value.replace('_', ' ').title(),
                    value=notif_type.value,
                    emoji=emoji,
                    description=f"{'Habilitado' if is_enabled else 'Desabilitado'}"
                ))
            
            select = NotificationTypeSelect(self.notification_system, self.user_id, self.guild_id, type_options)
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao configurar tipos: {e}")
            await interaction.response.send_message("❌ Erro ao carregar configurações.", ephemeral=True)
    
    @discord.ui.button(label="⏰ Horário Silencioso", style=discord.ButtonStyle.secondary)
    async def quiet_hours(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configurar horário silencioso"""
        try:
            modal = QuietHoursModal(self.notification_system, self.user_id, self.guild_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Erro ao abrir modal de horário: {e}")
            await interaction.response.send_message("❌ Erro ao abrir configurações.", ephemeral=True)
    
    @discord.ui.button(label="🎯 Prioridade Mínima", style=discord.ButtonStyle.secondary)
    async def min_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configurar prioridade mínima"""
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="🎯 Configurar Prioridade Mínima",
                description="Escolha a prioridade mínima das notificações que deseja receber:",
                color=0x7289DA
            )
            
            priority_options = []
            for priority in NotificationPriority:
                is_current = priority == profile.min_priority
                emoji = "🔸" if is_current else "⚪"
                priority_options.append(discord.SelectOption(
                    label=priority.name.title(),
                    value=str(priority.value),
                    emoji=emoji,
                    description=f"{'Atual' if is_current else 'Disponível'}"
                ))
            
            select = PrioritySelect(self.notification_system, self.user_id, self.guild_id, priority_options)
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao configurar prioridade: {e}")
            await interaction.response.send_message("❌ Erro ao carregar configurações.", ephemeral=True)
    
    @discord.ui.button(label="🤖 IA e Personalização", style=discord.ButtonStyle.success)
    async def ai_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configurar IA e personalização"""
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="🤖 Configurações de IA e Personalização",
                description="Configure como a IA personaliza suas notificações:",
                color=0x43B581
            )
            
            embed.add_field(
                name="🎨 Personalização com IA",
                value="✅ Habilitado" if profile.ai_personalization else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Timing Inteligente",
                value="✅ Habilitado" if profile.smart_timing else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Filtragem por Comportamento",
                value="✅ Habilitado" if profile.behavior_based_filtering else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="📈 Otimização de Engajamento",
                value="✅ Habilitado" if profile.engagement_optimization else "❌ Desabilitado",
                inline=True
            )
            
            embed.add_field(
                name="🧠 Padrões Detectados",
                value=", ".join([p.value.replace('_', ' ').title() for p in profile.behavior_patterns]) or "Nenhum",
                inline=False
            )
            
            view = AISettingsView(self.notification_system, self.user_id, self.guild_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao configurar IA: {e}")
            await interaction.response.send_message("❌ Erro ao carregar configurações de IA.", ephemeral=True)
    
    @discord.ui.button(label="📊 Estatísticas", style=discord.ButtonStyle.secondary)
    async def statistics(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar estatísticas do usuário"""
        try:
            stats = await self.notification_system.get_user_statistics(self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="📊 Suas Estatísticas de Notificações",
                color=0x9B59B6
            )
            
            if stats:
                profile_stats = stats.get('profile', {})
                recent_stats = stats.get('recent_activity', {})
                
                embed.add_field(
                    name="📈 Engajamento",
                    value=f"**Score:** {profile_stats.get('engagement_score', 0):.2f}\n"
                          f"**Recebidas:** {profile_stats.get('total_received', 0)}\n"
                          f"**Lidas:** {profile_stats.get('total_read', 0)}\n"
                          f"**Tempo médio de leitura:** {profile_stats.get('average_read_time', 0):.1f}min",
                    inline=True
                )
                
                embed.add_field(
                    name="📱 Atividade Recente",
                    value=f"**Total:** {recent_stats.get('total_notifications', 0)}\n"
                          f"**Não lidas:** {recent_stats.get('unread_count', 0)}\n"
                          f"**Última:** {recent_stats.get('last_notification', 'Nunca')[:10] if recent_stats.get('last_notification') else 'Nunca'}",
                    inline=True
                )
                
                behavior_patterns = profile_stats.get('behavior_patterns', [])
                if behavior_patterns:
                    embed.add_field(
                        name="🧠 Padrões de Comportamento",
                        value="\n".join([f"• {pattern.replace('_', ' ').title()}" for pattern in behavior_patterns[:5]]),
                        inline=False
                    )
            else:
                embed.description = "Nenhuma estatística disponível ainda."
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar estatísticas: {e}")
            await interaction.response.send_message("❌ Erro ao carregar estatísticas.", ephemeral=True)

class NotificationTypeSelect(discord.ui.Select):
    """Select menu para tipos de notificação"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int], options: List[discord.SelectOption]):
        super().__init__(placeholder="Selecione os tipos para alternar...", options=options, max_values=len(options))
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
    
    async def callback(self, interaction: discord.Interaction):
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            
            # Alternar tipos selecionados
            selected_types = {NotificationType(value) for value in self.values}
            
            # Atualizar tipos habilitados
            await self.notification_system.update_user_preferences(
                self.user_id,
                self.guild_id,
                enabled_types=selected_types
            )
            
            embed = discord.Embed(
                title="✅ Tipos de Notificação Atualizados",
                description=f"Você receberá notificações dos seguintes tipos:\n\n" +
                           "\n".join([f"• {t.value.replace('_', ' ').title()}" for t in selected_types]),
                color=0x43B581
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tipos: {e}")
            await interaction.response.send_message("❌ Erro ao atualizar configurações.", ephemeral=True)

class PrioritySelect(discord.ui.Select):
    """Select menu para prioridade mínima"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int], options: List[discord.SelectOption]):
        super().__init__(placeholder="Selecione a prioridade mínima...", options=options)
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
    
    async def callback(self, interaction: discord.Interaction):
        try:
            priority_value = int(self.values[0])
            priority = NotificationPriority(priority_value)
            
            await self.notification_system.update_user_preferences(
                self.user_id,
                self.guild_id,
                min_priority=priority
            )
            
            embed = discord.Embed(
                title="✅ Prioridade Mínima Atualizada",
                description=f"Você receberá apenas notificações com prioridade **{priority.name.title()}** ou superior.",
                color=0x43B581
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar prioridade: {e}")
            await interaction.response.send_message("❌ Erro ao atualizar prioridade.", ephemeral=True)

class QuietHoursModal(discord.ui.Modal):
    """Modal para configurar horário silencioso"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int]):
        super().__init__(title="⏰ Configurar Horário Silencioso")
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
    
    start_hour = discord.ui.TextInput(
        label="Hora de Início (0-23)",
        placeholder="22",
        max_length=2,
        required=True
    )
    
    end_hour = discord.ui.TextInput(
        label="Hora de Fim (0-23)",
        placeholder="8",
        max_length=2,
        required=True
    )
    
    timezone_offset = discord.ui.TextInput(
        label="Fuso Horário (UTC offset, ex: -3)",
        placeholder="0",
        max_length=3,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            start = int(self.start_hour.value)
            end = int(self.end_hour.value)
            tz_offset = int(self.timezone_offset.value) if self.timezone_offset.value else 0
            
            if not (0 <= start <= 23) or not (0 <= end <= 23):
                await interaction.response.send_message("❌ Horários devem estar entre 0 e 23.", ephemeral=True)
                return
            
            if not (-12 <= tz_offset <= 12):
                await interaction.response.send_message("❌ Fuso horário deve estar entre -12 e 12.", ephemeral=True)
                return
            
            await self.notification_system.update_user_preferences(
                self.user_id,
                self.guild_id,
                quiet_hours_start=start,
                quiet_hours_end=end,
                timezone_offset=tz_offset
            )
            
            embed = discord.Embed(
                title="✅ Horário Silencioso Configurado",
                description=f"**Período silencioso:** {start:02d}:00 - {end:02d}:00\n"
                           f"**Fuso horário:** UTC{tz_offset:+d}\n\n"
                           "Durante este período, você não receberá notificações de baixa e média prioridade.",
                color=0x43B581
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ Por favor, insira apenas números válidos.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao configurar horário silencioso: {e}")
            await interaction.response.send_message("❌ Erro ao salvar configurações.", ephemeral=True)

class AISettingsView(discord.ui.View):
    """View para configurações de IA"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int]):
        super().__init__(timeout=300)
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
    
    @discord.ui.button(label="🎨 Personalização IA", style=discord.ButtonStyle.primary)
    async def toggle_ai_personalization(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            new_value = not profile.ai_personalization
            
            await self.notification_system.update_user_preferences(
                self.user_id,
                self.guild_id,
                ai_personalization=new_value
            )
            
            status = "habilitada" if new_value else "desabilitada"
            await interaction.response.send_message(
                f"✅ Personalização com IA {status}!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao alternar personalização IA: {e}")
            await interaction.response.send_message("❌ Erro ao atualizar configuração.", ephemeral=True)
    
    @discord.ui.button(label="⏰ Timing Inteligente", style=discord.ButtonStyle.secondary)
    async def toggle_smart_timing(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            profile = await self.notification_system.get_user_profile(self.user_id, self.guild_id)
            new_value = not profile.smart_timing
            
            await self.notification_system.update_user_preferences(
                self.user_id,
                self.guild_id,
                smart_timing=new_value
            )
            
            status = "habilitado" if new_value else "desabilitado"
            await interaction.response.send_message(
                f"✅ Timing inteligente {status}!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao alternar timing inteligente: {e}")
            await interaction.response.send_message("❌ Erro ao atualizar configuração.", ephemeral=True)

class ModernNotificationCommands(commands.Cog):
    """Comandos modernizados para sistema de notificações push avançadas"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Inicializar sistemas core
        self.logger = SecureLogger('ModernNotificationCommands')
        self.cache = SmartCache()
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.events = EventSystem()
        self.rate_limiter = RateLimiter()
        
        # Sistema de notificações (será injetado)
        self.notification_system: Optional[ModernNotificationSystem] = None
        
        self.logger.info("Comandos Modernos de Notificações carregados")
    
    def set_notification_system(self, notification_system: ModernNotificationSystem):
        """Injeta o sistema de notificações"""
        self.notification_system = notification_system
        self.logger.info("Sistema de notificações injetado nos comandos")
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """Verificação global do cog"""
        if not self.notification_system:
            await ctx.send("❌ Sistema de notificações não está disponível.")
            return False
        return True
    
    @app_commands.command(name="notificacoes", description="Gerenciar suas notificações inteligentes")
    @app_commands.describe(
        acao="Ação a ser realizada",
        filtro="Filtrar notificações (opcional)"
    )
    async def notificacoes(
        self,
        interaction: discord.Interaction,
        acao: Optional[str] = None,
        filtro: Optional[str] = None
    ):
        """Comando principal para gerenciar notificações"""
        try:
            # Rate limiting
            rate_key = f"notifications_cmd:{interaction.user.id}"
            if await self.rate_limiter.is_rate_limited(rate_key, limit=10, window=60):
                await interaction.response.send_message(
                    "⏰ Você está usando este comando muito rapidamente. Tente novamente em alguns segundos.",
                    ephemeral=True
                )
                return
            
            await self.rate_limiter.increment(rate_key, window=60)
            
            if not acao or acao.lower() == "listar":
                await self._show_notifications(interaction, filtro)
            elif acao.lower() == "configurar":
                await self._show_settings(interaction)
            elif acao.lower() == "estatisticas":
                await self._show_statistics(interaction)
            else:
                await interaction.response.send_message(
                    "❌ Ação inválida. Use: `listar`, `configurar` ou `estatisticas`",
                    ephemeral=True
                )
            
            # Métricas
            await self.metrics.increment('commands.notifications.used',
                                       tags={'action': acao or 'listar', 'user_id': interaction.user.id})
            
        except Exception as e:
            self.logger.error(f"Erro no comando notificações: {e}")
            await interaction.response.send_message(
                "❌ Erro interno. Tente novamente mais tarde.",
                ephemeral=True
            )
    
    async def _show_notifications(self, interaction: discord.Interaction, filtro: Optional[str]):
        """Mostra lista de notificações do usuário"""
        try:
            unread_only = filtro and filtro.lower() == "nao_lidas"
            notifications = await self.notification_system.get_user_notifications(
                interaction.user.id,
                interaction.guild_id,
                unread_only=unread_only,
                limit=10
            )
            
            if not notifications:
                embed = discord.Embed(
                    title="📭 Nenhuma Notificação",
                    description="Você não possui notificações" + (" não lidas" if unread_only else "") + " no momento.",
                    color=0x95A5A6
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"📬 Suas Notificações {'Não Lidas' if unread_only else ''}",
                description=f"Mostrando {len(notifications)} notificações mais recentes:",
                color=0x7289DA
            )
            
            for i, notification in enumerate(notifications[:5], 1):
                status_emoji = "🔴" if notification.status.value != "read" else "✅"
                priority_emoji = {
                    1: "🔵",  # LOW
                    2: "🟡",  # MEDIUM
                    3: "🟠",  # HIGH
                    4: "🔴",  # URGENT
                    5: "🚨"   # CRITICAL
                }.get(notification.priority.value, "⚪")
                
                time_ago = self._format_time_ago(notification.created_at)
                
                embed.add_field(
                    name=f"{status_emoji} {priority_emoji} {notification.title}",
                    value=f"{notification.message[:100]}{'...' if len(notification.message) > 100 else ''}\n"
                          f"*{time_ago}*",
                    inline=False
                )
            
            if len(notifications) > 5:
                embed.set_footer(text=f"E mais {len(notifications) - 5} notificações...")
            
            # Botões de ação
            view = NotificationListView(self.notification_system, interaction.user.id, interaction.guild_id, notifications)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar notificações: {e}")
            raise
    
    async def _show_settings(self, interaction: discord.Interaction):
        """Mostra configurações de notificações"""
        try:
            profile = await self.notification_system.get_user_profile(interaction.user.id, interaction.guild_id)
            
            embed = discord.Embed(
                title="⚙️ Configurações de Notificações Inteligentes",
                description="Configure como você deseja receber suas notificações:",
                color=0x7289DA
            )
            
            # Informações básicas
            embed.add_field(
                name="🔔 Tipos Habilitados",
                value=f"{len(profile.enabled_types)}/{len(NotificationType)} tipos",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Prioridade Mínima",
                value=profile.min_priority.name.title(),
                inline=True
            )
            
            embed.add_field(
                name="⏰ Horário Silencioso",
                value=f"{profile.quiet_hours_start:02d}:00 - {profile.quiet_hours_end:02d}:00",
                inline=True
            )
            
            embed.add_field(
                name="🤖 IA Personalizada",
                value="✅ Habilitada" if profile.ai_personalization else "❌ Desabilitada",
                inline=True
            )
            
            embed.add_field(
                name="📈 Score de Engajamento",
                value=f"{profile.engagement_score:.2f}/1.00",
                inline=True
            )
            
            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Recebidas:** {profile.total_notifications_received}\n"
                      f"**Lidas:** {profile.total_notifications_read}",
                inline=True
            )
            
            view = NotificationSettingsView(self.notification_system, interaction.user.id, interaction.guild_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar configurações: {e}")
            raise
    
    async def _show_statistics(self, interaction: discord.Interaction):
        """Mostra estatísticas detalhadas"""
        try:
            stats = await self.notification_system.get_user_statistics(interaction.user.id, interaction.guild_id)
            
            if not stats:
                await interaction.response.send_message(
                    "📊 Ainda não há estatísticas suficientes para exibir.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📊 Suas Estatísticas Detalhadas",
                color=0x9B59B6
            )
            
            profile_stats = stats.get('profile', {})
            recent_stats = stats.get('recent_activity', {})
            preferences = stats.get('preferences', {})
            
            # Estatísticas de engajamento
            embed.add_field(
                name="📈 Engajamento",
                value=f"**Score:** {profile_stats.get('engagement_score', 0):.2f}/1.00\n"
                      f"**Taxa de leitura:** {(profile_stats.get('total_read', 0) / max(profile_stats.get('total_received', 1), 1) * 100):.1f}%\n"
                      f"**Tempo médio:** {profile_stats.get('average_read_time', 0):.1f}min",
                inline=True
            )
            
            # Atividade recente
            embed.add_field(
                name="📱 Atividade Recente",
                value=f"**Total:** {recent_stats.get('total_notifications', 0)}\n"
                      f"**Não lidas:** {recent_stats.get('unread_count', 0)}\n"
                      f"**Última:** {recent_stats.get('last_notification', 'Nunca')[:10] if recent_stats.get('last_notification') else 'Nunca'}",
                inline=True
            )
            
            # Configurações atuais
            embed.add_field(
                name="⚙️ Configurações",
                value=f"**IA:** {'✅' if preferences.get('ai_personalization') else '❌'}\n"
                      f"**Timing:** {'✅' if preferences.get('smart_timing') else '❌'}\n"
                      f"**Prioridade:** {preferences.get('min_priority', 'N/A')}",
                inline=True
            )
            
            # Padrões de comportamento
            behavior_patterns = profile_stats.get('behavior_patterns', [])
            if behavior_patterns:
                embed.add_field(
                    name="🧠 Padrões Detectados",
                    value="\n".join([f"• {pattern.replace('_', ' ').title()}" for pattern in behavior_patterns[:5]]),
                    inline=False
                )
            
            # Tipos preferidos
            preferred_types = profile_stats.get('preferred_types', [])
            if preferred_types:
                embed.add_field(
                    name="❤️ Tipos Preferidos",
                    value="\n".join([f"• {ptype.replace('_', ' ').title()}" for ptype in preferred_types[:5]]),
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar estatísticas: {e}")
            raise
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Formata tempo decorrido"""
        try:
            now = datetime.now(timezone.utc)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days}d atrás"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}h atrás"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}min atrás"
            else:
                return "Agora mesmo"
                
        except Exception:
            return "Tempo desconhecido"
    
    @app_commands.command(name="marcar_lidas", description="Marcar notificações como lidas")
    @app_commands.describe(
        todas="Marcar todas as notificações como lidas",
        notification_id="ID específico da notificação (opcional)"
    )
    async def marcar_lidas(
        self,
        interaction: discord.Interaction,
        todas: bool = False,
        notification_id: Optional[str] = None
    ):
        """Marca notificações como lidas"""
        try:
            # Rate limiting
            rate_key = f"mark_read:{interaction.user.id}"
            if await self.rate_limiter.is_rate_limited(rate_key, limit=5, window=60):
                await interaction.response.send_message(
                    "⏰ Aguarde um pouco antes de marcar mais notificações.",
                    ephemeral=True
                )
                return
            
            await self.rate_limiter.increment(rate_key, window=60)
            
            if notification_id:
                # Marcar notificação específica
                success = await self.notification_system.mark_notification_as_read(
                    notification_id, interaction.user.id
                )
                
                if success:
                    embed = discord.Embed(
                        title="✅ Notificação Marcada como Lida",
                        description="A notificação foi marcada como lida com sucesso.",
                        color=0x43B581
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="Não foi possível marcar a notificação como lida.",
                        color=0xE74C3C
                    )
                    
            elif todas:
                # Marcar todas como lidas
                count = await self.notification_system.mark_all_as_read(
                    interaction.user.id, interaction.guild_id
                )
                
                embed = discord.Embed(
                    title="✅ Notificações Marcadas como Lidas",
                    description=f"{count} notificações foram marcadas como lidas.",
                    color=0x43B581
                )
                
            else:
                embed = discord.Embed(
                    title="❓ Como usar",
                    description="Use `todas: True` para marcar todas como lidas ou forneça um `notification_id` específico.",
                    color=0x95A5A6
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Métricas
            await self.metrics.increment('commands.mark_read.used',
                                       tags={'type': 'all' if todas else 'specific', 'user_id': interaction.user.id})
            
        except Exception as e:
            self.logger.error(f"Erro ao marcar como lidas: {e}")
            await interaction.response.send_message(
                "❌ Erro interno. Tente novamente mais tarde.",
                ephemeral=True
            )
    
    @app_commands.command(name="config_notificacoes", description="Configurar sistema de notificações (Admin)")
    @app_commands.describe(
        acao="Ação administrativa",
        parametro="Parâmetro da ação",
        valor="Valor do parâmetro"
    )
    @app_commands.default_permissions(administrator=True)
    async def config_notificacoes(
        self,
        interaction: discord.Interaction,
        acao: str,
        parametro: Optional[str] = None,
        valor: Optional[str] = None
    ):
        """Configurações administrativas do sistema de notificações"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Você precisa ser administrador para usar este comando.",
                    ephemeral=True
                )
                return
            
            if acao.lower() == "status":
                await self._show_system_status(interaction)
            elif acao.lower() == "analytics":
                await self._show_system_analytics(interaction)
            elif acao.lower() == "broadcast":
                await self._handle_broadcast(interaction, parametro, valor)
            elif acao.lower() == "template":
                await self._handle_template_creation(interaction, parametro, valor)
            else:
                await interaction.response.send_message(
                    "❌ Ação inválida. Use: `status`, `analytics`, `broadcast` ou `template`",
                    ephemeral=True
                )
            
            # Métricas
            await self.metrics.increment('commands.admin_notifications.used',
                                       tags={'action': acao, 'user_id': interaction.user.id})
            
        except Exception as e:
            self.logger.error(f"Erro no comando admin: {e}")
            await interaction.response.send_message(
                "❌ Erro interno. Tente novamente mais tarde.",
                ephemeral=True
            )
    
    async def _show_system_status(self, interaction: discord.Interaction):
        """Mostra status do sistema"""
        try:
            health = await self.notification_system.health_check()
            
            status_color = {
                'healthy': 0x43B581,
                'warning': 0xF39C12,
                'error': 0xE74C3C
            }.get(health['status'], 0x95A5A6)
            
            embed = discord.Embed(
                title=f"🏥 Status do Sistema de Notificações",
                description=f"**Status:** {health['status'].upper()}",
                color=status_color,
                timestamp=datetime.fromisoformat(health['timestamp'].replace('Z', '+00:00'))
            )
            
            metrics = health.get('metrics', {})
            embed.add_field(
                name="📊 Métricas",
                value=f"**Notificações:** {metrics.get('total_notifications', 0)}\n"
                      f"**Usuários:** {metrics.get('total_users', 0)}\n"
                      f"**Templates:** {metrics.get('total_templates', 0)}",
                inline=True
            )
            
            embed.add_field(
                name="⏳ Filas",
                value=f"**Pendentes:** {metrics.get('pending_notifications', 0)}\n"
                      f"**Agendadas:** {metrics.get('scheduled_notifications', 0)}",
                inline=True
            )
            
            queues = health.get('queues', {})
            if queues:
                queue_info = "\n".join([f"**{priority}:** {count}" for priority, count in queues.items()])
                embed.add_field(
                    name="🚦 Filas por Prioridade",
                    value=queue_info,
                    inline=True
                )
            
            if 'issues' in health:
                embed.add_field(
                    name="⚠️ Problemas Detectados",
                    value="\n".join([f"• {issue}" for issue in health['issues']]),
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar status: {e}")
            raise
    
    async def _show_system_analytics(self, interaction: discord.Interaction):
        """Mostra analytics do sistema"""
        try:
            analytics = await self.notification_system.get_analytics()
            
            if not analytics:
                await interaction.response.send_message(
                    "📊 Analytics ainda não disponíveis.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📈 Analytics do Sistema",
                color=0x9B59B6
            )
            
            # Estatísticas gerais
            embed.add_field(
                name="📊 Estatísticas Gerais",
                value=f"**Enviadas:** {analytics.total_sent}\n"
                      f"**Entregues:** {analytics.total_delivered}\n"
                      f"**Lidas:** {analytics.total_read}\n"
                      f"**Falharam:** {analytics.total_failed}",
                inline=True
            )
            
            # Taxas
            embed.add_field(
                name="📈 Taxas de Sucesso",
                value=f"**Entrega:** {analytics.delivery_rate:.1%}\n"
                      f"**Leitura:** {analytics.read_rate:.1%}\n"
                      f"**Engajamento:** {analytics.engagement_rate:.1%}",
                inline=True
            )
            
            # Tempos médios
            embed.add_field(
                name="⏱️ Tempos Médios",
                value=f"**Entrega:** {analytics.average_delivery_time_seconds:.1f}s\n"
                      f"**Leitura:** {analytics.average_read_time_minutes:.1f}min",
                inline=True
            )
            
            # Tipos mais populares
            if analytics.most_engaging_types:
                embed.add_field(
                    name="🏆 Tipos Mais Engajantes",
                    value="\n".join([f"• {t.replace('_', ' ').title()}" for t in analytics.most_engaging_types[:5]]),
                    inline=False
                )
            
            # Horários de pico
            if analytics.peak_hours:
                peak_hours_str = ", ".join([f"{h:02d}:00" for h in analytics.peak_hours])
                embed.add_field(
                    name="🕐 Horários de Pico",
                    value=peak_hours_str,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar analytics: {e}")
            raise
    
    async def _handle_broadcast(self, interaction: discord.Interaction, template_id: Optional[str], message: Optional[str]):
        """Lida com broadcast de notificações"""
        if not template_id:
            await interaction.response.send_message(
                "❌ Forneça um template_id para o broadcast.",
                ephemeral=True
            )
            return
        
        # Obter todos os membros do servidor
        target_users = [member.id for member in interaction.guild.members if not member.bot]
        
        if not target_users:
            await interaction.response.send_message(
                "❌ Nenhum usuário encontrado para broadcast.",
                ephemeral=True
            )
            return
        
        # Confirmar broadcast
        embed = discord.Embed(
            title="📢 Confirmar Broadcast",
            description=f"Deseja enviar notificação para **{len(target_users)}** usuários?\n\n"
                       f"**Template:** {template_id}\n"
                       f"**Mensagem:** {message or 'Padrão do template'}",
            color=0xF39C12
        )
        
        view = BroadcastConfirmView(self.notification_system, template_id, target_users, interaction.guild_id, message)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _handle_template_creation(self, interaction: discord.Interaction, template_data: Optional[str], extra: Optional[str]):
        """Lida com criação de templates"""
        await interaction.response.send_message(
            "🔧 Funcionalidade de criação de templates em desenvolvimento.\n"
            "Use o sistema web ou contate um desenvolvedor.",
            ephemeral=True
        )

class NotificationListView(discord.ui.View):
    """View para lista de notificações"""
    
    def __init__(self, notification_system: ModernNotificationSystem, user_id: int, guild_id: Optional[int], notifications: List):
        super().__init__(timeout=300)
        self.notification_system = notification_system
        self.user_id = user_id
        self.guild_id = guild_id
        self.notifications = notifications
    
    @discord.ui.button(label="✅ Marcar Todas como Lidas", style=discord.ButtonStyle.success)
    async def mark_all_read(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            count = await self.notification_system.mark_all_as_read(self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="✅ Notificações Marcadas",
                description=f"{count} notificações foram marcadas como lidas.",
                color=0x43B581
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao marcar todas como lidas: {e}")
            await interaction.response.send_message("❌ Erro ao marcar notificações.", ephemeral=True)
    
    @discord.ui.button(label="⚙️ Configurações", style=discord.ButtonStyle.secondary)
    async def open_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            settings_view = NotificationSettingsView(self.notification_system, self.user_id, self.guild_id)
            
            embed = discord.Embed(
                title="⚙️ Configurações de Notificações",
                description="Configure suas preferências de notificação:",
                color=0x7289DA
            )
            
            await interaction.response.send_message(embed=embed, view=settings_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao abrir configurações: {e}")
            await interaction.response.send_message("❌ Erro ao abrir configurações.", ephemeral=True)

class BroadcastConfirmView(discord.ui.View):
    """View para confirmar broadcast"""
    
    def __init__(self, notification_system: ModernNotificationSystem, template_id: str, target_users: List[int], guild_id: int, message: Optional[str]):
        super().__init__(timeout=60)
        self.notification_system = notification_system
        self.template_id = template_id
        self.target_users = target_users
        self.guild_id = guild_id
        self.message = message
    
    @discord.ui.button(label="✅ Confirmar Broadcast", style=discord.ButtonStyle.danger)
    async def confirm_broadcast(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            
            data = {'message': self.message} if self.message else None
            sent_count = await self.notification_system.send_broadcast_notification(
                self.template_id,
                self.target_users,
                data,
                self.guild_id
            )
            
            embed = discord.Embed(
                title="📢 Broadcast Enviado",
                description=f"Notificação enviada para **{sent_count}/{len(self.target_users)}** usuários.",
                color=0x43B581
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro no broadcast: {e}")
            await interaction.followup.send("❌ Erro ao enviar broadcast.", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_broadcast(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Broadcast cancelado.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup do cog"""
    await bot.add_cog(ModernNotificationCommands(bot))
    logger.info("Cog ModernNotificationCommands carregado com sucesso")

if __name__ == "__main__":
    print("✅ Comandos Modernos de Notificações - Módulo carregado")