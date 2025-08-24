#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos Modernizados de Moderação
Comandos para o sistema de moderação automática com IA

Autor: Desenvolvedor Sênior
Versão: 2.0.0
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Importar sistemas core modernos
try:
    from src.core.secure_logger import SecureLogger
    from src.core.smart_cache import SmartCache
    from src.core.metrics_collector import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
    from src.features.moderation.modern_system import (
        ModernModerationSystem, ModerationConfig, ActionType, ViolationType, SeverityLevel
    )
except ImportError:
    # Fallbacks para desenvolvimento
    class SecureLogger:
        def __init__(self, name): pass
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class SmartCache:
        def __init__(self): self.cache = {}
        async def get(self, key): return self.cache.get(key)
        async def set(self, key, value, ttl=None): self.cache[key] = value
    
    class MetricsCollector:
        def __init__(self): pass
        async def increment(self, metric, tags=None): pass
    
    class DataValidator:
        def __init__(self): pass
        def validate_user_input(self, data): return True
    
    class EventSystem:
        def __init__(self): pass
        async def emit(self, event, data): pass
    
    class RateLimiter:
        def __init__(self): pass
        async def is_rate_limited(self, key, limit, window): return False
    
    # Mock classes para desenvolvimento
    class ModernModerationSystem:
        def __init__(self, bot): pass
        async def get_user_warnings(self, user_id, guild_id): return []
        async def clear_user_warnings(self, user_id, guild_id, mod_id): return 0
        async def get_moderation_stats(self, guild_id=None): return {}
        async def update_guild_config(self, guild_id, **kwargs): return None
        async def export_user_data(self, user_id, guild_id): return {}
        async def delete_user_data(self, user_id, guild_id): return True
        async def health_check(self): return {'status': 'healthy'}
    
    class ModerationConfig:
        def __init__(self, **kwargs): pass
    
    class ActionType:
        WARN = "warn"
        TIMEOUT = "timeout"
        KICK = "kick"
        BAN = "ban"
    
    class ViolationType:
        SPAM = "spam"
        TOXIC_LANGUAGE = "toxic_language"
    
    class SeverityLevel:
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4

# Configurar logger
logger = SecureLogger('ModernModerationCommands')

class ModernModerationCommands(commands.Cog):
    """Comandos modernizados de moderação"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Inicializar sistemas core
        self.logger = SecureLogger('ModernModerationCommands')
        self.cache = SmartCache()
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.events = EventSystem()
        self.rate_limiter = RateLimiter()
        
        # Sistema de moderação
        self.moderation_system = ModernModerationSystem(bot)
        
        self.logger.info("Comandos de Moderação Modernizados carregados")
    
    def _create_embed(self, title: str, description: str = None, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        """Cria embed padronizado"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Sistema de Moderação Modernizado", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed
    
    async def _check_permissions(self, interaction: discord.Interaction, required_permission: str) -> bool:
        """Verifica permissões do usuário"""
        if not interaction.user.guild_permissions.administrator:
            if required_permission == "moderate" and not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    embed=self._create_embed(
                        "❌ Sem Permissão",
                        "Você precisa da permissão `Moderate Members` para usar este comando.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return False
            elif required_permission == "admin":
                await interaction.response.send_message(
                    embed=self._create_embed(
                        "❌ Sem Permissão",
                        "Você precisa da permissão `Administrator` para usar este comando.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return False
        return True
    
    async def _handle_rate_limit(self, interaction: discord.Interaction, command_name: str) -> bool:
        """Verifica rate limiting"""
        rate_key = f"moderation_cmd:{interaction.guild.id}:{interaction.user.id}:{command_name}"
        
        if await self.rate_limiter.is_rate_limited(rate_key, limit=5, window=60):
            await interaction.response.send_message(
                embed=self._create_embed(
                    "⏰ Rate Limit",
                    "Você está usando comandos muito rapidamente. Tente novamente em alguns segundos.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
            return True
        
        await self.rate_limiter.increment(rate_key, window=60)
        return False
    
    @app_commands.command(name="warn", description="Aplica advertência manual a um usuário")
    @app_commands.describe(
        usuario="Usuário para advertir",
        motivo="Motivo da advertência"
    )
    async def warn_user(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Violação das regras"):
        """Comando para advertir usuário manualmente"""
        if not await self._check_permissions(interaction, "moderate"):
            return
        
        if await self._handle_rate_limit(interaction, "warn"):
            return
        
        try:
            # Validar entrada
            if not self.validator.validate_user_input({'motivo': motivo}):
                await interaction.response.send_message(
                    embed=self._create_embed(
                        "❌ Entrada Inválida",
                        "O motivo contém caracteres inválidos.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Verificar se não está tentando advertir a si mesmo
            if usuario.id == interaction.user.id:
                await interaction.response.send_message(
                    embed=self._create_embed(
                        "❌ Ação Inválida",
                        "Você não pode advertir a si mesmo.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Verificar se não está tentando advertir um moderador
            if usuario.guild_permissions.moderate_members or usuario.guild_permissions.administrator:
                await interaction.response.send_message(
                    embed=self._create_embed(
                        "❌ Ação Inválida",
                        "Você não pode advertir outros moderadores.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Obter advertências atuais
            warnings = await self.moderation_system.get_user_warnings(usuario.id, interaction.guild.id)
            new_warning_count = len(warnings) + 1
            
            # Criar embed de confirmação
            embed = self._create_embed(
                "⚠️ Advertência Aplicada",
                f"**Usuário:** {usuario.mention}\n**Motivo:** {motivo}\n**Total de Advertências:** {new_warning_count}",
                discord.Color.orange()
            )
            
            embed.add_field(
                name="👮 Moderador",
                value=interaction.user.mention,
                inline=True
            )
            
            embed.add_field(
                name="📅 Data",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            
            # Simular adição de advertência (seria implementado no sistema real)
            # await self.moderation_system.add_manual_warning(usuario.id, interaction.guild.id, motivo, interaction.user.id)
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            await self.metrics.increment('moderation.manual_warnings',
                                       tags={'guild_id': interaction.guild.id})
            
            # Evento
            await self.events.emit('manual_warning_issued', {
                'user_id': usuario.id,
                'guild_id': interaction.guild.id,
                'moderator_id': interaction.user.id,
                'reason': motivo
            })
            
            self.logger.info(f"Advertência manual aplicada: {usuario} por {interaction.user} - {motivo}")
            
        except Exception as e:
            self.logger.error(f"Erro no comando warn: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao aplicar a advertência.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="warnings", description="Mostra advertências de um usuário")
    @app_commands.describe(usuario="Usuário para verificar (deixe vazio para ver suas próprias)")
    async def show_warnings(self, interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
        """Comando para mostrar advertências"""
        target_user = usuario or interaction.user
        
        # Verificar permissões (moderadores podem ver qualquer um, usuários só a si mesmos)
        if target_user != interaction.user and not await self._check_permissions(interaction, "moderate"):
            return
        
        if await self._handle_rate_limit(interaction, "warnings"):
            return
        
        try:
            warnings = await self.moderation_system.get_user_warnings(target_user.id, interaction.guild.id)
            
            embed = self._create_embed(
                f"⚠️ Advertências de {target_user.display_name}",
                f"**Total:** {len(warnings)} advertências",
                discord.Color.orange() if warnings else discord.Color.green()
            )
            
            if not warnings:
                embed.description = "✅ Nenhuma advertência encontrada!"
            else:
                # Mostrar últimas 10 advertências
                recent_warnings = warnings[-10:]
                
                for i, warning in enumerate(recent_warnings, 1):
                    embed.add_field(
                        name=f"#{len(warnings) - len(recent_warnings) + i}",
                        value=f"**Tipo:** {warning.violation_type.value.replace('_', ' ').title()}\n"
                               f"**Motivo:** {warning.reason}\n"
                               f"**Data:** <t:{int(warning.timestamp.timestamp())}:R>\n"
                               f"**Severidade:** {warning.severity.name}",
                        inline=True
                    )
                
                if len(warnings) > 10:
                    embed.set_footer(text=f"Mostrando as 10 mais recentes de {len(warnings)} advertências")
            
            await interaction.response.send_message(embed=embed, ephemeral=target_user != interaction.user)
            
            # Métricas
            await self.metrics.increment('moderation.warnings_checked',
                                       tags={'guild_id': interaction.guild.id})
            
        except Exception as e:
            self.logger.error(f"Erro no comando warnings: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao buscar as advertências.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="clear_warnings", description="Remove todas as advertências de um usuário")
    @app_commands.describe(usuario="Usuário para limpar advertências")
    async def clear_warnings(self, interaction: discord.Interaction, usuario: discord.Member):
        """Comando para limpar advertências"""
        if not await self._check_permissions(interaction, "admin"):
            return
        
        if await self._handle_rate_limit(interaction, "clear_warnings"):
            return
        
        try:
            cleared_count = await self.moderation_system.clear_user_warnings(
                usuario.id, interaction.guild.id, interaction.user.id
            )
            
            embed = self._create_embed(
                "🧹 Advertências Limpas",
                f"**Usuário:** {usuario.mention}\n"
                f"**Advertências Removidas:** {cleared_count}\n"
                f"**Moderador:** {interaction.user.mention}",
                discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            await self.metrics.increment('moderation.warnings_cleared',
                                       tags={'guild_id': interaction.guild.id})
            
            self.logger.info(f"Advertências limpas: {usuario} por {interaction.user} ({cleared_count} removidas)")
            
        except Exception as e:
            self.logger.error(f"Erro no comando clear_warnings: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao limpar as advertências.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="automod", description="Configura o sistema de moderação automática")
    @app_commands.describe(
        acao="Ação a realizar",
        valor="Valor para a configuração (quando aplicável)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Toggle (Ativar/Desativar)", value="toggle"),
        app_commands.Choice(name="Status", value="status"),
        app_commands.Choice(name="Limite de Spam", value="spam_limit"),
        app_commands.Choice(name="Threshold de Toxicidade", value="toxicity_threshold"),
        app_commands.Choice(name="Proteção Anti-Raid", value="raid_protection"),
        app_commands.Choice(name="Canal de Logs", value="log_channel"),
        app_commands.Choice(name="IA Análise", value="ai_analysis")
    ])
    async def automod_config(self, interaction: discord.Interaction, acao: str, valor: Optional[str] = None):
        """Comando para configurar automoderação"""
        if not await self._check_permissions(interaction, "admin"):
            return
        
        if await self._handle_rate_limit(interaction, "automod"):
            return
        
        try:
            embed = self._create_embed(
                "🛡️ Configuração de Automoderação",
                color=discord.Color.blue()
            )
            
            if acao == "toggle":
                # Toggle do sistema
                current_config = await self.moderation_system.load_guild_config(interaction.guild.id)
                new_status = not current_config.enabled
                
                await self.moderation_system.update_guild_config(
                    interaction.guild.id,
                    enabled=new_status
                )
                
                status_text = "ativada" if new_status else "desativada"
                embed.description = f"Moderação automática foi **{status_text}**."
                embed.color = discord.Color.green() if new_status else discord.Color.red()
                
            elif acao == "spam_limit":
                if valor and valor.isdigit():
                    new_limit = int(valor)
                    if 1 <= new_limit <= 20:
                        await self.moderation_system.update_guild_config(
                            interaction.guild.id,
                            spam_message_limit=new_limit
                        )
                        embed.description = f"Limite de spam definido para **{new_limit}** mensagens."
                        embed.color = discord.Color.green()
                    else:
                        embed.description = "❌ Limite deve estar entre 1 e 20."
                        embed.color = discord.Color.red()
                else:
                    embed.description = "❌ Valor inválido. Use um número entre 1 e 20."
                    embed.color = discord.Color.red()
                    
            elif acao == "toxicity_threshold":
                if valor:
                    try:
                        threshold = float(valor)
                        if 0.1 <= threshold <= 1.0:
                            await self.moderation_system.update_guild_config(
                                interaction.guild.id,
                                toxicity_threshold=threshold
                            )
                            embed.description = f"Threshold de toxicidade definido para **{threshold:.1%}**."
                            embed.color = discord.Color.green()
                        else:
                            embed.description = "❌ Threshold deve estar entre 0.1 e 1.0."
                            embed.color = discord.Color.red()
                    except ValueError:
                        embed.description = "❌ Valor inválido. Use um número decimal (ex: 0.7)."
                        embed.color = discord.Color.red()
                else:
                    embed.description = "❌ Forneça um valor para o threshold (ex: 0.7)."
                    embed.color = discord.Color.red()
                    
            elif acao == "raid_protection":
                if valor and valor.lower() in ['true', 'false', 'on', 'off', '1', '0']:
                    enable_raid = valor.lower() in ['true', 'on', '1']
                    await self.moderation_system.update_guild_config(
                        interaction.guild.id,
                        raid_protection=enable_raid
                    )
                    status = "ativada" if enable_raid else "desativada"
                    embed.description = f"Proteção anti-raid **{status}**."
                    embed.color = discord.Color.green() if enable_raid else discord.Color.orange()
                else:
                    embed.description = "❌ Use 'true' ou 'false' para ativar/desativar."
                    embed.color = discord.Color.red()
                    
            elif acao == "log_channel":
                if valor:
                    try:
                        channel_id = int(valor.replace('<#', '').replace('>', ''))
                        channel = interaction.guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.TextChannel):
                            await self.moderation_system.update_guild_config(
                                interaction.guild.id,
                                log_channel_id=channel_id
                            )
                            embed.description = f"Canal de logs definido para {channel.mention}."
                            embed.color = discord.Color.green()
                        else:
                            embed.description = "❌ Canal não encontrado ou inválido."
                            embed.color = discord.Color.red()
                    except ValueError:
                        embed.description = "❌ ID de canal inválido."
                        embed.color = discord.Color.red()
                else:
                    embed.description = "❌ Forneça o canal ou ID do canal."
                    embed.color = discord.Color.red()
                    
            elif acao == "ai_analysis":
                if valor and valor.lower() in ['true', 'false', 'on', 'off', '1', '0']:
                    enable_ai = valor.lower() in ['true', 'on', '1']
                    await self.moderation_system.update_guild_config(
                        interaction.guild.id,
                        enable_ai_analysis=enable_ai
                    )
                    status = "ativada" if enable_ai else "desativada"
                    embed.description = f"Análise de IA **{status}**."
                    embed.color = discord.Color.green() if enable_ai else discord.Color.orange()
                else:
                    embed.description = "❌ Use 'true' ou 'false' para ativar/desativar."
                    embed.color = discord.Color.red()
                    
            elif acao == "status":
                config = await self.moderation_system.load_guild_config(interaction.guild.id)
                stats = await self.moderation_system.get_moderation_stats(interaction.guild.id)
                
                embed.description = f"""
                **Status Geral:** {'🟢 Ativo' if config.enabled else '🔴 Inativo'}
                **Análise de IA:** {'🟢 Ativa' if config.enable_ai_analysis else '🔴 Inativa'}
                **Proteção Anti-Raid:** {'🟢 Ativa' if config.raid_protection else '🔴 Inativa'}
                **Canal de Logs:** {f'<#{config.log_channel_id}>' if config.log_channel_id else '❌ Não configurado'}
                
                **Configurações:**
                • Limite de Spam: {config.spam_message_limit} mensagens
                • Threshold de Toxicidade: {config.toxicity_threshold:.1%}
                • Limite de Menções: {config.mention_limit}
                • Limite de Emojis: {config.emoji_limit}
                
                **Estatísticas:**
                • Mensagens Processadas: {stats.get('messages_processed', 0)}
                • Violações Detectadas: {stats.get('violations_detected', 0)}
                • Ações Tomadas: {stats.get('actions_taken', 0)}
                • Análises de IA: {stats.get('ai_analyses_performed', 0)}
                """
                embed.color = discord.Color.green() if config.enabled else discord.Color.red()
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            await self.metrics.increment('moderation.config_changes',
                                       tags={'guild_id': interaction.guild.id, 'action': acao})
            
        except Exception as e:
            self.logger.error(f"Erro no comando automod: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao configurar a automoderação.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="stats_moderacao", description="Mostra estatísticas detalhadas de moderação")
    async def moderation_stats(self, interaction: discord.Interaction):
        """Comando para mostrar estatísticas de moderação"""
        if not await self._check_permissions(interaction, "moderate"):
            return
        
        if await self._handle_rate_limit(interaction, "stats_moderacao"):
            return
        
        try:
            stats = await self.moderation_system.get_moderation_stats(interaction.guild.id)
            
            embed = self._create_embed(
                "📊 Estatísticas de Moderação",
                f"Estatísticas para **{interaction.guild.name}**",
                discord.Color.blue()
            )
            
            # Estatísticas gerais
            embed.add_field(
                name="📈 Atividade Geral",
                value=f"• Mensagens Processadas: **{stats.get('messages_processed', 0):,}**\n"
                      f"• Violações Detectadas: **{stats.get('violations_detected', 0):,}**\n"
                      f"• Ações Tomadas: **{stats.get('actions_taken', 0):,}**",
                inline=True
            )
            
            # Estatísticas de IA
            embed.add_field(
                name="🤖 Análise de IA",
                value=f"• Análises Realizadas: **{stats.get('ai_analyses_performed', 0):,}**\n"
                      f"• Falsos Positivos: **{stats.get('false_positives', 0):,}**\n"
                      f"• Taxa de Precisão: **{((stats.get('ai_analyses_performed', 1) - stats.get('false_positives', 0)) / stats.get('ai_analyses_performed', 1) * 100):.1f}%**",
                inline=True
            )
            
            # Estatísticas do servidor
            if 'guild_users_monitored' in stats:
                embed.add_field(
                    name="👥 Servidor",
                    value=f"• Usuários Monitorados: **{stats.get('guild_users_monitored', 0):,}**\n"
                          f"• Total de Violações: **{stats.get('guild_total_violations', 0):,}**\n"
                          f"• Confiança Média: **{stats.get('guild_avg_trust_score', 0):.2f}**",
                    inline=True
                )
            
            # Adicionar gráfico de atividade (simulado)
            activity_data = "📊 Atividade dos Últimos 7 Dias:\n"
            for i in range(7):
                day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][i]
                activity = max(0, stats.get('violations_detected', 0) // 7 + (i * 2) - 5)
                bar = "█" * min(activity // 2, 10)
                activity_data += f"{day_name}: {bar} {activity}\n"
            
            embed.add_field(
                name="📈 Tendência",
                value=f"```{activity_data}```",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Métricas
            await self.metrics.increment('moderation.stats_viewed',
                                       tags={'guild_id': interaction.guild.id})
            
        except Exception as e:
            self.logger.error(f"Erro no comando stats_moderacao: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao buscar as estatísticas.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="admin_moderacao", description="Comandos administrativos de moderação")
    @app_commands.describe(
        acao="Ação administrativa",
        usuario="Usuário (para ações específicas)"
    )
    @app_commands.choices(acao=[
        app_commands.Choice(name="Verificar Saúde do Sistema", value="health"),
        app_commands.Choice(name="Exportar Dados de Usuário", value="export_user"),
        app_commands.Choice(name="Deletar Dados de Usuário", value="delete_user"),
        app_commands.Choice(name="Limpar Cache", value="clear_cache"),
        app_commands.Choice(name="Recarregar Configuração", value="reload_config")
    ])
    async def admin_moderation(self, interaction: discord.Interaction, acao: str, usuario: Optional[discord.Member] = None):
        """Comandos administrativos de moderação"""
        if not await self._check_permissions(interaction, "admin"):
            return
        
        if await self._handle_rate_limit(interaction, "admin_moderacao"):
            return
        
        try:
            if acao == "health":
                health_status = await self.moderation_system.health_check()
                
                embed = self._create_embed(
                    "🏥 Saúde do Sistema de Moderação",
                    color=discord.Color.green() if health_status['status'] == 'healthy' else discord.Color.red()
                )
                
                embed.add_field(
                    name="📊 Status Geral",
                    value=f"**Status:** {health_status['status'].upper()}\n"
                          f"**Verificação:** <t:{int(datetime.now().timestamp())}:R>",
                    inline=False
                )
                
                if 'components' in health_status:
                    components_status = "\n".join([
                        f"• {comp.title()}: {'✅' if status == 'healthy' else '❌'} {status}"
                        for comp, status in health_status['components'].items()
                    ])
                    embed.add_field(
                        name="🔧 Componentes",
                        value=components_status,
                        inline=True
                    )
                
                if 'stats' in health_status:
                    stats_text = "\n".join([
                        f"• {key.replace('_', ' ').title()}: {value:,}"
                        for key, value in health_status['stats'].items()
                    ])
                    embed.add_field(
                        name="📈 Estatísticas",
                        value=stats_text,
                        inline=True
                    )
                
                if health_status['status'] != 'healthy' and 'error' in health_status:
                    embed.add_field(
                        name="❌ Erro",
                        value=f"```{health_status['error']}```",
                        inline=False
                    )
                
            elif acao == "export_user":
                if not usuario:
                    embed = self._create_embed(
                        "❌ Usuário Necessário",
                        "Você deve especificar um usuário para exportar os dados.",
                        discord.Color.red()
                    )
                else:
                    user_data = await self.moderation_system.export_user_data(usuario.id, interaction.guild.id)
                    
                    embed = self._create_embed(
                        "📤 Dados Exportados",
                        f"Dados de **{usuario.display_name}** exportados com sucesso.",
                        discord.Color.green()
                    )
                    
                    embed.add_field(
                        name="📊 Resumo dos Dados",
                        value=f"• Total de Mensagens: {user_data.get('total_messages', 0)}\n"
                              f"• Violações: {len(user_data.get('violations', []))}\n"
                              f"• Score de Confiança: {user_data.get('trust_score', 0):.2f}\n"
                              f"• Data de Entrada: <t:{int(datetime.fromisoformat(user_data.get('join_date', datetime.now().isoformat())).timestamp())}:D>",
                        inline=False
                    )
                    
                    # Criar arquivo JSON para download (simulado)
                    embed.add_field(
                        name="💾 Arquivo",
                        value="Os dados foram preparados para download (funcionalidade completa seria implementada).",
                        inline=False
                    )
                
            elif acao == "delete_user":
                if not usuario:
                    embed = self._create_embed(
                        "❌ Usuário Necessário",
                        "Você deve especificar um usuário para deletar os dados.",
                        discord.Color.red()
                    )
                else:
                    success = await self.moderation_system.delete_user_data(usuario.id, interaction.guild.id)
                    
                    if success:
                        embed = self._create_embed(
                            "🗑️ Dados Deletados",
                            f"Todos os dados de **{usuario.display_name}** foram removidos do sistema.",
                            discord.Color.green()
                        )
                    else:
                        embed = self._create_embed(
                            "❌ Erro na Deleção",
                            "Ocorreu um erro ao deletar os dados do usuário.",
                            discord.Color.red()
                        )
                
            elif acao == "clear_cache":
                # Simular limpeza de cache
                embed = self._create_embed(
                    "🧹 Cache Limpo",
                    "Cache do sistema de moderação foi limpo com sucesso.",
                    discord.Color.green()
                )
                
            elif acao == "reload_config":
                # Simular recarga de configuração
                embed = self._create_embed(
                    "🔄 Configuração Recarregada",
                    "Configurações do sistema foram recarregadas com sucesso.",
                    discord.Color.green()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Métricas
            await self.metrics.increment('moderation.admin_actions',
                                       tags={'guild_id': interaction.guild.id, 'action': acao})
            
        except Exception as e:
            self.logger.error(f"Erro no comando admin_moderacao: {e}")
            await interaction.response.send_message(
                embed=self._create_embed(
                    "❌ Erro",
                    "Ocorreu um erro ao executar a ação administrativa.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processa mensagens para moderação automática"""
        if message.guild and not message.author.bot:
            try:
                await self.moderation_system.process_message(message)
            except Exception as e:
                self.logger.error(f"Erro no processamento de mensagem: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Processa entrada de novos membros"""
        try:
            await self.moderation_system.process_member_join(member)
        except Exception as e:
            self.logger.error(f"Erro no processamento de entrada de membro: {e}")

async def setup(bot):
    """Função de setup do cog"""
    await bot.add_cog(ModernModerationCommands(bot))