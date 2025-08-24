#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos Modernizados de Achievements e Badges - Hawk Bot
Comandos slash modernos para sistema de conquistas e badges com async/await

Autor: Hawk Bot Development Team
Versão: 3.0.0 - Modernizado
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import logging
from pathlib import Path

# Importar sistemas core
try:
    from ..core.secure_logger import SecureLogger
    from ..core.smart_cache import SmartCache
    from ..core.metrics import increment_counter, record_timer, record_gauge
    from ..core.data_validator import validate_input, ValidationSchema
    from ..core.event_system import emit_event, EventData
    from ..core.rate_limiter import rate_limit
    from ..features.achievements.modern_system import (
        get_achievement_system, 
        AchievementCategory, 
        AchievementRarity,
        BadgeType
    )
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
    get_achievement_system = None
    AchievementCategory = None
    AchievementRarity = None
    BadgeType = None

logger = logging.getLogger('HawkBot.ModernAchievementCommands')

# ==================== CLASSE PRINCIPAL ====================

class ModernAchievementCommands(commands.Cog):
    """Comandos modernizados para sistema de conquistas e badges"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Sistemas core
        if SecureLogger:
            self.logger = SecureLogger('ModernAchievementCommands')
        else:
            self.logger = logger
        
        if SmartCache:
            self.cache = SmartCache(
                default_ttl=1800,  # 30 minutos
                max_size=5000,
                cleanup_interval=300  # 5 minutos
            )
        else:
            self.cache = {}
        
        # Rate limiting
        self.command_cooldowns = {}
        
        self.logger.info("Comandos de conquistas modernizados carregados")
    
    def _create_error_embed(self, title: str, description: str, user: discord.User = None) -> discord.Embed:
        """Criar embed de erro padronizado"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_footer(text=f"Solicitado por {user.display_name}", icon_url=user.display_avatar.url)
        else:
            embed.set_footer(text="Hawk Bot - Sistema de Conquistas")
        
        return embed
    
    def _create_success_embed(self, title: str, description: str, user: discord.User = None) -> discord.Embed:
        """Criar embed de sucesso padronizado"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_footer(text=f"Solicitado por {user.display_name}", icon_url=user.display_avatar.url)
        else:
            embed.set_footer(text="Hawk Bot - Sistema de Conquistas")
        
        return embed
    
    def _create_info_embed(self, title: str, description: str, user: discord.User = None) -> discord.Embed:
        """Criar embed informativo padronizado"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_footer(text=f"Solicitado por {user.display_name}", icon_url=user.display_avatar.url)
        else:
            embed.set_footer(text="Hawk Bot - Sistema de Conquistas")
        
        return embed
    
    async def _check_rate_limit(self, user_id: int, command: str, limit: int = 5, window: int = 60) -> bool:
        """Verificar rate limiting para comandos"""
        if rate_limit:
            return await rate_limit(f"achievement_cmd_{command}_{user_id}", limit, window)
        
        # Fallback manual
        now = datetime.now()
        key = f"{command}_{user_id}"
        
        if key not in self.command_cooldowns:
            self.command_cooldowns[key] = []
        
        # Limpar timestamps antigos
        cutoff = now - timedelta(seconds=window)
        self.command_cooldowns[key] = [
            timestamp for timestamp in self.command_cooldowns[key]
            if timestamp > cutoff
        ]
        
        # Verificar limite
        if len(self.command_cooldowns[key]) >= limit:
            return False
        
        # Adicionar timestamp atual
        self.command_cooldowns[key].append(now)
        return True
    
    # ==================== COMANDOS PRINCIPAIS ====================
    
    @app_commands.command(
        name="conquistas",
        description="Visualizar suas conquistas e progresso"
    )
    @app_commands.describe(
        usuario="Usuário para visualizar conquistas (opcional)",
        categoria="Filtrar por categoria específica"
    )
    async def achievements_command(
        self, 
        interaction: discord.Interaction,
        usuario: Optional[discord.User] = None,
        categoria: Optional[str] = None
    ):
        """Comando para visualizar conquistas"""
        try:
            await interaction.response.defer()
            
            # Rate limiting
            if not await self._check_rate_limit(interaction.user.id, "achievements", 10, 60):
                embed = self._create_error_embed(
                    "Rate Limit",
                    "Você está usando este comando muito rapidamente. Tente novamente em alguns segundos.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Métricas
            if increment_counter:
                increment_counter('achievement_commands_total')
            
            # Determinar usuário alvo
            target_user = usuario or interaction.user
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Obter dados do usuário
            user_data = await achievement_system.get_user_achievements_display(target_user.id)
            
            if not user_data:
                embed = self._create_info_embed(
                    "Sem Conquistas",
                    f"{target_user.mention} ainda não possui conquistas desbloqueadas.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Criar embed principal
            embed = discord.Embed(
                title=f"🏆 Conquistas de {target_user.display_name}",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Informações gerais
            embed.add_field(
                name="📊 Estatísticas Gerais",
                value=(
                    f"**Nível:** {user_data.get('level', 1)} ({user_data.get('rank', 'Novato')})\n"
                    f"**Pontos Totais:** {user_data.get('total_points', 0):,}\n"
                    f"**Conquistas:** {user_data.get('achievements_count', 0)}\n"
                    f"**Badges:** {user_data.get('badges_count', 0)}"
                ),
                inline=True
            )
            
            # Progresso para próximo nível
            progress = user_data.get('progress_to_next_level', {})
            if progress:
                progress_bar = self._create_progress_bar(progress.get('percentage', 0))
                embed.add_field(
                    name="📈 Progresso do Nível",
                    value=(
                        f"{progress_bar}\n"
                        f"**{progress.get('current', 0)}/{progress.get('needed', 100)} XP** "
                        f"({progress.get('percentage', 0)}%)"
                    ),
                    inline=True
                )
            
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer
            
            # Conquistas por categoria
            achievements_by_category = user_data.get('achievements_by_category', {})
            
            if categoria:
                # Filtrar por categoria específica
                if categoria.lower() in achievements_by_category:
                    category_achievements = achievements_by_category[categoria.lower()]
                    embed.add_field(
                        name=f"🎯 Categoria: {categoria.title()}",
                        value=self._format_achievements_list(category_achievements[:10]),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="❌ Categoria não encontrada",
                        value=f"A categoria '{categoria}' não foi encontrada ou não possui conquistas.",
                        inline=False
                    )
            else:
                # Mostrar todas as categorias (limitado)
                categories_shown = 0
                for cat_name, cat_achievements in achievements_by_category.items():
                    if categories_shown >= 3:  # Limitar a 3 categorias
                        break
                    
                    embed.add_field(
                        name=f"📂 {cat_name.title()} ({len(cat_achievements)})",
                        value=self._format_achievements_list(cat_achievements[:5]),
                        inline=True
                    )
                    categories_shown += 1
                
                if len(achievements_by_category) > 3:
                    embed.add_field(
                        name="➕ Mais Categorias",
                        value=f"Use `/conquistas categoria:<nome>` para ver categorias específicas.",
                        inline=False
                    )
            
            embed.set_footer(
                text=f"Solicitado por {interaction.user.display_name} • Hawk Bot",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.logger.error(f"Erro no comando conquistas: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao processar suas conquistas. Tente novamente mais tarde.",
                interaction.user
            )
            await interaction.followup.send(embed=embed)
    
    def _create_progress_bar(self, percentage: int, length: int = 10) -> str:
        """Criar barra de progresso visual"""
        filled = int((percentage / 100) * length)
        empty = length - filled
        return f"{'█' * filled}{'░' * empty}"
    
    def _format_achievements_list(self, achievements: List[Dict[str, Any]]) -> str:
        """Formatar lista de conquistas para exibição"""
        if not achievements:
            return "*Nenhuma conquista nesta categoria*"
        
        formatted = []
        for ach in achievements[:5]:  # Limitar a 5
            rarity_emoji = {
                'comum': '⚪',
                'raro': '🔵',
                'épico': '🟣',
                'lendário': '🟠',
                'mítico': '🔴'
            }.get(ach.get('rarity', 'comum'), '⚪')
            
            formatted.append(
                f"{rarity_emoji} {ach.get('icon', '🏆')} **{ach.get('name', 'Conquista')}** "
                f"({ach.get('points', 0)} pts)"
            )
        
        result = "\n".join(formatted)
        if len(achievements) > 5:
            result += f"\n*... e mais {len(achievements) - 5} conquistas*"
        
        return result
    
    @app_commands.command(
        name="ranking_conquistas",
        description="Ver ranking de conquistas do servidor"
    )
    @app_commands.describe(
        categoria="Filtrar ranking por categoria específica",
        limite="Número de usuários a exibir (máximo 20)"
    )
    async def leaderboard_command(
        self,
        interaction: discord.Interaction,
        categoria: Optional[str] = None,
        limite: Optional[int] = 10
    ):
        """Comando para ver ranking de conquistas"""
        try:
            await interaction.response.defer()
            
            # Rate limiting
            if not await self._check_rate_limit(interaction.user.id, "leaderboard", 5, 60):
                embed = self._create_error_embed(
                    "Rate Limit",
                    "Você está usando este comando muito rapidamente. Tente novamente em alguns segundos.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Validar limite
            if limite and (limite < 1 or limite > 20):
                embed = self._create_error_embed(
                    "Limite Inválido",
                    "O limite deve estar entre 1 e 20 usuários.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Métricas
            if increment_counter:
                increment_counter('leaderboard_commands_total')
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Obter leaderboard
            leaderboard_data = await achievement_system.get_leaderboard(
                limit=limite or 10,
                category=categoria
            )
            
            if not leaderboard_data:
                embed = self._create_info_embed(
                    "Ranking Vazio",
                    "Ainda não há dados suficientes para gerar o ranking.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Criar embed do ranking
            title = f"🏆 Ranking de Conquistas"
            if categoria:
                title += f" - {categoria.title()}"
            
            embed = discord.Embed(
                title=title,
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            # Adicionar usuários ao ranking
            ranking_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user_data in enumerate(leaderboard_data, 1):
                try:
                    user = self.bot.get_user(user_data['user_id'])
                    username = user.display_name if user else f"Usuário {user_data['user_id']}"
                    
                    medal = medals[i-1] if i <= 3 else f"{i}."
                    
                    if categoria:
                        points = user_data.get('category_points', 0)
                        achievements = user_data.get('category_achievements', 0)
                    else:
                        points = user_data.get('total_points', 0)
                        achievements = user_data.get('achievements_count', 0)
                    
                    level = user_data.get('level', 1)
                    
                    ranking_text += (
                        f"{medal} **{username}**\n"
                        f"   📊 {points:,} pontos • 🏆 {achievements} conquistas • 📈 Nível {level}\n\n"
                    )
                
                except Exception as e:
                    self.logger.error(f"Erro ao processar usuário no ranking: {e}")
                    continue
            
            if ranking_text:
                embed.description = ranking_text
            else:
                embed.description = "*Nenhum dado disponível para exibição*"
            
            # Adicionar posição do usuário atual
            user_position = None
            for i, user_data in enumerate(leaderboard_data, 1):
                if user_data['user_id'] == interaction.user.id:
                    user_position = i
                    break
            
            if user_position:
                embed.add_field(
                    name="📍 Sua Posição",
                    value=f"Você está na **{user_position}ª posição**!",
                    inline=True
                )
            
            embed.set_footer(
                text=f"Solicitado por {interaction.user.display_name} • Atualizado em",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.logger.error(f"Erro no comando ranking: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao gerar o ranking. Tente novamente mais tarde.",
                interaction.user
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(
        name="verificar_conquistas",
        description="Verificar manualmente suas conquistas pendentes"
    )
    async def check_achievements_command(self, interaction: discord.Interaction):
        """Comando para verificação manual de conquistas"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Rate limiting mais restritivo para verificação manual
            if not await self._check_rate_limit(interaction.user.id, "check", 3, 300):  # 3 por 5 minutos
                embed = self._create_error_embed(
                    "Rate Limit",
                    "Você só pode verificar conquistas manualmente 3 vezes a cada 5 minutos.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Métricas
            if increment_counter:
                increment_counter('manual_achievement_checks_total')
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar conquistas
            with record_timer('manual_achievement_check_duration') if record_timer else nullcontext():
                unlocked_achievements = await achievement_system.check_user_achievements(interaction.user.id)
            
            if unlocked_achievements:
                # Conquistas desbloqueadas
                embed = self._create_success_embed(
                    "Conquistas Desbloqueadas!",
                    f"Parabéns! Você desbloqueou **{len(unlocked_achievements)}** nova(s) conquista(s):",
                    interaction.user
                )
                
                achievements_text = ""
                total_points = 0
                
                for ach in unlocked_achievements[:5]:  # Limitar a 5 para não sobrecarregar
                    achievements_text += (
                        f"{getattr(ach, 'icon', '🏆')} **{getattr(ach, 'name', 'Conquista')}**\n"
                        f"   {getattr(ach, 'description', 'Descrição não disponível')}\n"
                        f"   +{getattr(ach, 'points', 0)} pontos\n\n"
                    )
                    total_points += getattr(ach, 'points', 0)
                
                if len(unlocked_achievements) > 5:
                    achievements_text += f"*... e mais {len(unlocked_achievements) - 5} conquistas!*\n\n"
                
                achievements_text += f"**Total de pontos ganhos: {total_points:,}**"
                
                embed.add_field(
                    name="🎉 Novas Conquistas",
                    value=achievements_text,
                    inline=False
                )
                
                embed.color = discord.Color.gold()
            
            else:
                # Nenhuma conquista nova
                embed = self._create_info_embed(
                    "Verificação Concluída",
                    "Você não possui conquistas pendentes no momento. Continue jogando para desbloquear mais!",
                    interaction.user
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            self.logger.error(f"Erro no comando verificar conquistas: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao verificar suas conquistas. Tente novamente mais tarde.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="progresso_conquista",
        description="Ver progresso detalhado para conquistas específicas"
    )
    @app_commands.describe(
        conquista="Nome ou ID da conquista para verificar progresso"
    )
    async def achievement_progress_command(
        self,
        interaction: discord.Interaction,
        conquista: str
    ):
        """Comando para ver progresso de conquista específica"""
        try:
            await interaction.response.defer()
            
            # Rate limiting
            if not await self._check_rate_limit(interaction.user.id, "progress", 10, 60):
                embed = self._create_error_embed(
                    "Rate Limit",
                    "Você está usando este comando muito rapidamente. Tente novamente em alguns segundos.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Buscar conquista
            target_achievement = None
            conquista_lower = conquista.lower()
            
            for ach_id, ach in achievement_system.achievements.items():
                if (ach_id.lower() == conquista_lower or 
                    getattr(ach, 'name', '').lower() == conquista_lower):
                    target_achievement = ach
                    break
            
            if not target_achievement:
                embed = self._create_error_embed(
                    "Conquista Não Encontrada",
                    f"Não foi possível encontrar a conquista '{conquista}'. "
                    f"Verifique o nome ou ID e tente novamente.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Obter progresso do usuário
            user_progress = await achievement_system.get_user_progress(interaction.user.id)
            user_stats = await achievement_system._get_user_stats(interaction.user.id)
            
            # Verificar se já foi desbloqueada
            is_unlocked = target_achievement.id in user_progress.achievements
            
            # Criar embed de progresso
            embed = discord.Embed(
                title=f"📊 Progresso: {getattr(target_achievement, 'name', 'Conquista')}",
                description=getattr(target_achievement, 'description', 'Descrição não disponível'),
                color=discord.Color.green() if is_unlocked else discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Status da conquista
            status_emoji = "✅" if is_unlocked else "⏳"
            status_text = "Desbloqueada" if is_unlocked else "Pendente"
            
            embed.add_field(
                name="📋 Informações",
                value=(
                    f"**Status:** {status_emoji} {status_text}\n"
                    f"**Categoria:** {getattr(target_achievement, 'category', 'N/A').value if hasattr(getattr(target_achievement, 'category', None), 'value') else 'N/A'}\n"
                    f"**Raridade:** {getattr(target_achievement, 'rarity', 'N/A').value if hasattr(getattr(target_achievement, 'rarity', None), 'value') else 'N/A'}\n"
                    f"**Pontos:** {getattr(target_achievement, 'points', 0)}"
                ),
                inline=True
            )
            
            # Requisitos e progresso
            if hasattr(target_achievement, 'requirements') and not is_unlocked:
                requirements_text = ""
                
                for req in getattr(target_achievement, 'requirements', []):
                    req_type = req.get('type', 'unknown')
                    req_value = req.get('value', 0)
                    req_operator = req.get('operator', '>=')
                    
                    current_value = user_stats.get(req_type, 0)
                    
                    # Calcular progresso
                    if isinstance(req_value, (int, float)) and isinstance(current_value, (int, float)):
                        progress_pct = min(100, (current_value / req_value) * 100) if req_value > 0 else 0
                        progress_bar = self._create_progress_bar(int(progress_pct), 8)
                        
                        requirements_text += (
                            f"**{req_type.replace('_', ' ').title()}:**\n"
                            f"{progress_bar} {current_value:,}/{req_value:,} ({progress_pct:.1f}%)\n\n"
                        )
                    else:
                        requirements_text += (
                            f"**{req_type.replace('_', ' ').title()}:** "
                            f"{current_value} {req_operator} {req_value}\n\n"
                        )
                
                embed.add_field(
                    name="🎯 Requisitos",
                    value=requirements_text or "*Requisitos não disponíveis*",
                    inline=False
                )
            
            elif is_unlocked:
                embed.add_field(
                    name="🎉 Conquista Desbloqueada!",
                    value="Parabéns! Você já possui esta conquista.",
                    inline=False
                )
            
            embed.set_footer(
                text=f"Solicitado por {interaction.user.display_name} • Hawk Bot",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.logger.error(f"Erro no comando progresso conquista: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao verificar o progresso da conquista. Tente novamente mais tarde.",
                interaction.user
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(
        name="badges",
        description="Visualizar seus badges coletados"
    )
    @app_commands.describe(
        usuario="Usuário para visualizar badges (opcional)"
    )
    async def badges_command(
        self,
        interaction: discord.Interaction,
        usuario: Optional[discord.User] = None
    ):
        """Comando para visualizar badges"""
        try:
            await interaction.response.defer()
            
            # Rate limiting
            if not await self._check_rate_limit(interaction.user.id, "badges", 10, 60):
                embed = self._create_error_embed(
                    "Rate Limit",
                    "Você está usando este comando muito rapidamente. Tente novamente em alguns segundos.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Determinar usuário alvo
            target_user = usuario or interaction.user
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Obter progresso do usuário
            user_progress = await achievement_system.get_user_progress(target_user.id)
            
            if not user_progress.badges:
                embed = self._create_info_embed(
                    "Sem Badges",
                    f"{target_user.mention} ainda não possui badges coletados.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Criar embed de badges
            embed = discord.Embed(
                title=f"🎖️ Badges de {target_user.display_name}",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Organizar badges por tipo
            badges_by_type = {}
            
            for badge_id in user_progress.badges:
                if badge_id not in achievement_system.badges:
                    continue
                
                badge = achievement_system.badges[badge_id]
                badge_type = getattr(badge, 'badge_type', BadgeType.ACHIEVEMENT).value if BadgeType else 'achievement'
                
                if badge_type not in badges_by_type:
                    badges_by_type[badge_type] = []
                
                badges_by_type[badge_type].append({
                    'id': badge.id,
                    'name': getattr(badge, 'name', 'Badge'),
                    'description': getattr(badge, 'description', 'Descrição não disponível'),
                    'icon': getattr(badge, 'icon', '🎖️'),
                    'rarity': getattr(badge, 'rarity', AchievementRarity.COMMON).value if AchievementRarity else 'comum'
                })
            
            # Adicionar badges por tipo
            for badge_type, badges_list in badges_by_type.items():
                type_emoji = {
                    'achievement': '🏆',
                    'rank': '📊',
                    'seasonal': '🗓️',
                    'event': '🎉',
                    'custom': '⭐'
                }.get(badge_type, '🎖️')
                
                badges_text = ""
                for badge in badges_list[:5]:  # Limitar a 5 por tipo
                    rarity_emoji = {
                        'comum': '⚪',
                        'raro': '🔵',
                        'épico': '🟣',
                        'lendário': '🟠',
                        'mítico': '🔴'
                    }.get(badge.get('rarity', 'comum'), '⚪')
                    
                    badges_text += (
                        f"{rarity_emoji} {badge.get('icon', '🎖️')} **{badge.get('name', 'Badge')}**\n"
                        f"   {badge.get('description', 'Descrição não disponível')}\n\n"
                    )
                
                if len(badges_list) > 5:
                    badges_text += f"*... e mais {len(badges_list) - 5} badges*"
                
                embed.add_field(
                    name=f"{type_emoji} {badge_type.title()} ({len(badges_list)})",
                    value=badges_text or "*Nenhum badge nesta categoria*",
                    inline=True
                )
            
            embed.add_field(
                name="📊 Resumo",
                value=f"**Total de Badges:** {len(user_progress.badges)}",
                inline=False
            )
            
            embed.set_footer(
                text=f"Solicitado por {interaction.user.display_name} • Hawk Bot",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.logger.error(f"Erro no comando badges: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao processar os badges. Tente novamente mais tarde.",
                interaction.user
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== COMANDOS DE ADMINISTRAÇÃO ====================
    
    @app_commands.command(
        name="admin_conquista",
        description="[ADMIN] Gerenciar conquistas de usuários"
    )
    @app_commands.describe(
        acao="Ação a realizar",
        usuario="Usuário alvo",
        conquista="ID da conquista"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Conceder", value="grant"),
        app_commands.Choice(name="Remover", value="remove"),
        app_commands.Choice(name="Verificar", value="check")
    ])
    async def admin_achievement_command(
        self,
        interaction: discord.Interaction,
        acao: app_commands.Choice[str],
        usuario: discord.User,
        conquista: Optional[str] = None
    ):
        """Comando administrativo para gerenciar conquistas"""
        try:
            # Verificar permissões
            if not interaction.user.guild_permissions.administrator:
                embed = self._create_error_embed(
                    "Sem Permissão",
                    "Você precisa ser administrador para usar este comando.",
                    interaction.user
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Obter sistema de conquistas
            achievement_system = get_achievement_system()
            if not achievement_system:
                embed = self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de conquistas não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if acao.value == "check":
                # Verificar conquistas do usuário
                unlocked = await achievement_system.check_user_achievements(usuario.id)
                
                embed = self._create_success_embed(
                    "Verificação Administrativa",
                    f"Verificação concluída para {usuario.mention}.\n"
                    f"**Conquistas desbloqueadas:** {len(unlocked)}",
                    interaction.user
                )
                
                if unlocked:
                    achievements_text = "\n".join([
                        f"• {getattr(ach, 'name', 'Conquista')} (+{getattr(ach, 'points', 0)} pts)"
                        for ach in unlocked[:5]
                    ])
                    
                    if len(unlocked) > 5:
                        achievements_text += f"\n... e mais {len(unlocked) - 5} conquistas"
                    
                    embed.add_field(
                        name="🎉 Novas Conquistas",
                        value=achievements_text,
                        inline=False
                    )
            
            elif acao.value in ["grant", "remove"]:
                if not conquista:
                    embed = self._create_error_embed(
                        "Parâmetro Obrigatório",
                        "Você deve especificar o ID da conquista para esta ação.",
                        interaction.user
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Buscar conquista
                target_achievement = achievement_system.achievements.get(conquista)
                if not target_achievement:
                    embed = self._create_error_embed(
                        "Conquista Não Encontrada",
                        f"Não foi possível encontrar a conquista com ID '{conquista}'.",
                        interaction.user
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                user_progress = await achievement_system.get_user_progress(usuario.id)
                
                if acao.value == "grant":
                    if conquista in user_progress.achievements:
                        embed = self._create_error_embed(
                            "Conquista Já Desbloqueada",
                            f"{usuario.mention} já possui esta conquista.",
                            interaction.user
                        )
                    else:
                        await achievement_system._unlock_achievement(usuario.id, target_achievement)
                        embed = self._create_success_embed(
                            "Conquista Concedida",
                            f"Conquista **{getattr(target_achievement, 'name', 'Conquista')}** "
                            f"concedida para {usuario.mention}.",
                            interaction.user
                        )
                
                elif acao.value == "remove":
                    if conquista not in user_progress.achievements:
                        embed = self._create_error_embed(
                            "Conquista Não Encontrada",
                            f"{usuario.mention} não possui esta conquista.",
                            interaction.user
                        )
                    else:
                        user_progress.achievements.remove(conquista)
                        user_progress.total_points -= getattr(target_achievement, 'points', 0)
                        user_progress.total_points = max(0, user_progress.total_points)
                        await achievement_system._save_user_progress(usuario.id, user_progress)
                        
                        embed = self._create_success_embed(
                            "Conquista Removida",
                            f"Conquista **{getattr(target_achievement, 'name', 'Conquista')}** "
                            f"removida de {usuario.mention}.",
                            interaction.user
                        )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            self.logger.error(f"Erro no comando admin conquista: {e}")
            embed = self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao processar o comando administrativo.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

# ==================== CONTEXT MANAGER FALLBACK ====================

class nullcontext:
    """Fallback para contexto nulo quando record_timer não está disponível"""
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

# ==================== SETUP ====================

async def setup(bot):
    """Setup do cog"""
    await bot.add_cog(ModernAchievementCommands(bot))
    logger.info("Comandos de conquistas modernizados carregados com sucesso")

if __name__ == "__main__":
    # Exemplo de uso
    pass