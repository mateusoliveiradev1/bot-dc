#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos PUBG Modernizados - Hawk Bot
Comandos modernos para PUBG com async/await e integração completa

Autor: Hawk Bot Development Team
Versão: 3.0.0 - Modernizado
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import logging

# Importar sistema PUBG modernizado
try:
    from ..features.pubg.modern_pubg_system import (
        ModernPUBGSystem, PUBGShard, GameMode, RankTier,
        get_pubg_system, get_player_stats_quick
    )
except ImportError:
    ModernPUBGSystem = None
    PUBGShard = None
    GameMode = None
    RankTier = None
    get_pubg_system = None
    get_player_stats_quick = None

# Importar sistemas core
try:
    from ..core.secure_logger import SecureLogger
    from ..core.metrics import increment_counter, record_timer
    from ..core.data_validator import validate_input
    from ..core.event_system import emit_event
    from ..core.rate_limiter import rate_limit
except ImportError:
    SecureLogger = None
    increment_counter = None
    record_timer = None
    validate_input = None
    emit_event = None
    rate_limit = None

logger = logging.getLogger('HawkBot.ModernPUBGCommands')

class ModernPUBGCommands(commands.Cog):
    """Comandos PUBG modernizados com async/await"""
    
    def __init__(self, bot):
        self.bot = bot
        self.pubg_system = get_pubg_system() if get_pubg_system else None
        
        # Logger seguro
        if SecureLogger:
            self.secure_logger = SecureLogger('ModernPUBGCommands')
        else:
            self.secure_logger = logger
        
        # Cache de comandos para evitar spam
        self.command_cache = {}
        self.cache_duration = 300  # 5 minutos
        
        logger.info("Comandos PUBG modernizados carregados")
    
    def _get_cache_key(self, user_id: int, command: str, *args) -> str:
        """Gera chave de cache para comando"""
        return f"{user_id}:{command}:{'_'.join(str(arg) for arg in args)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se cache do comando ainda é válido"""
        if cache_key not in self.command_cache:
            return False
        
        cache_time = self.command_cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration
    
    def _save_to_cache(self, cache_key: str, data: Any):
        """Salva resultado no cache"""
        self.command_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Limpeza automática do cache
        if len(self.command_cache) > 100:
            oldest_keys = sorted(
                self.command_cache.keys(),
                key=lambda k: self.command_cache[k]['timestamp']
            )[:20]
            for key in oldest_keys:
                del self.command_cache[key]
    
    async def _create_error_embed(self, title: str, description: str, user: discord.User = None) -> discord.Embed:
        """Cria embed de erro padronizado"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_footer(
                text=f"Solicitado por {user.display_name}",
                icon_url=user.display_avatar.url
            )
        
        return embed
    
    async def _create_success_embed(self, title: str, description: str = None, user: discord.User = None) -> discord.Embed:
        """Cria embed de sucesso padronizado"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_footer(
                text=f"Solicitado por {user.display_name}",
                icon_url=user.display_avatar.url
            )
        
        return embed
    
    @app_commands.command(
        name="pubg_register",
        description="🎮 Registra seu nick PUBG no sistema modernizado"
    )
    @app_commands.describe(
        nome="Seu nick exato no PUBG",
        plataforma="Plataforma onde você joga PUBG"
    )
    @app_commands.choices(plataforma=[
        app_commands.Choice(name="Steam (PC)", value="steam"),
        app_commands.Choice(name="PlayStation", value="psn"),
        app_commands.Choice(name="Xbox", value="xbox"),
        app_commands.Choice(name="Kakao", value="kakao"),
        app_commands.Choice(name="Stadia", value="stadia")
    ])
    async def pubg_register(self, interaction: discord.Interaction, nome: str, plataforma: str):
        """Registra o nick PUBG do usuário no sistema modernizado"""
        await interaction.response.defer()
        
        try:
            # Validar entrada
            if validate_input:
                validation_result = await validate_input({
                    'nome': nome,
                    'plataforma': plataforma
                }, 'pubg_registration')
                
                if not validation_result.is_valid:
                    embed = await self._create_error_embed(
                        "Dados Inválidos",
                        f"Erro na validação: {validation_result.errors[0]}",
                        interaction.user
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Registrar métrica
            if increment_counter:
                increment_counter('pubg_registrations_total')
            
            if not self.pubg_system:
                embed = await self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema PUBG não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Buscar jogador na API PUBG
            async with self.pubg_system as pubg:
                with record_timer('pubg_registration_duration') if record_timer else nullcontext():
                    player = await pubg.get_player_by_name(nome, plataforma)
                
                if not player:
                    embed = await self._create_error_embed(
                        "Jogador Não Encontrado",
                        f"Não foi possível encontrar o jogador **{nome}** na plataforma **{plataforma.upper()}**.\n\n"
                        "**Possíveis causas:**\n"
                        "• Nome digitado incorretamente\n"
                        "• Jogador não existe na plataforma selecionada\n"
                        "• Perfil privado ou inativo\n\n"
                        "**Dica:** Verifique se o nome está exatamente como aparece no jogo.",
                        interaction.user
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Salvar no sistema do bot (assumindo que existe um storage)
                if hasattr(self.bot, 'storage'):
                    user_data = {
                        'discord_id': interaction.user.id,
                        'pubg_id': player.id if hasattr(player, 'id') else player['id'],
                        'pubg_name': player.name if hasattr(player, 'name') else player['name'],
                        'shard': plataforma,
                        'registered_at': datetime.now().isoformat()
                    }
                    
                    # Salvar dados do usuário
                    self.bot.storage.save_user_pubg_data(interaction.user.id, user_data)
                
                # Criar embed de sucesso
                embed = discord.Embed(
                    title="🎮 Registro PUBG Concluído!",
                    description=f"Jogador **{player.name if hasattr(player, 'name') else player['name']}** registrado com sucesso!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📋 Informações",
                    value=f"**Nome:** {player.name if hasattr(player, 'name') else player['name']}\n"
                          f"**Plataforma:** {plataforma.upper()}\n"
                          f"**ID:** `{(player.id if hasattr(player, 'id') else player['id'])[:8]}...`",
                    inline=True
                )
                
                embed.add_field(
                    name="🚀 Próximos Passos",
                    value="• Use `/pubg_stats` para ver suas estatísticas\n"
                          "• Use `/pubg_rank` para ver seu ranking\n"
                          "• Participe dos rankings do servidor!",
                    inline=True
                )
                
                embed.set_footer(
                    text=f"Registrado por {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                await interaction.followup.send(embed=embed)
                
                # Emitir evento
                if emit_event:
                    await emit_event('pubg_player_registered', {
                        'discord_user_id': interaction.user.id,
                        'pubg_name': player.name if hasattr(player, 'name') else player['name'],
                        'shard': plataforma
                    })
        
        except Exception as e:
            self.secure_logger.error(f"Erro no registro PUBG: {e}", extra={
                'user_id': interaction.user.id,
                'pubg_name': nome,
                'shard': plataforma
            })
            
            embed = await self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro interno durante o registro. Tente novamente em alguns minutos.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="pubg_stats",
        description="📊 Mostra suas estatísticas PUBG detalhadas"
    )
    @app_commands.describe(
        usuario="Usuário para consultar (opcional)",
        modo="Modo de jogo específico (opcional)"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Squad", value="squad"),
        app_commands.Choice(name="Squad FPP", value="squad-fpp"),
        app_commands.Choice(name="Duo", value="duo"),
        app_commands.Choice(name="Duo FPP", value="duo-fpp"),
        app_commands.Choice(name="Solo", value="solo"),
        app_commands.Choice(name="Solo FPP", value="solo-fpp")
    ])
    async def pubg_stats(self, interaction: discord.Interaction, usuario: Optional[discord.Member] = None, modo: Optional[str] = None):
        """Mostra estatísticas PUBG detalhadas"""
        await interaction.response.defer()
        
        target_user = usuario or interaction.user
        
        try:
            # Verificar cache
            cache_key = self._get_cache_key(target_user.id, 'stats', modo or 'all')
            if self._is_cache_valid(cache_key):
                cached_embed = self.command_cache[cache_key]['data']
                await interaction.followup.send(embed=cached_embed)
                return
            
            # Registrar métrica
            if increment_counter:
                increment_counter('pubg_stats_requests_total')
            
            if not self.pubg_system:
                embed = await self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema PUBG não está disponível no momento.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Buscar dados do usuário no storage
            if not hasattr(self.bot, 'storage'):
                embed = await self._create_error_embed(
                    "Sistema de Dados Indisponível",
                    "O sistema de armazenamento não está disponível.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            user_data = self.bot.storage.get_user_pubg_data(target_user.id)
            if not user_data:
                embed = await self._create_error_embed(
                    "Usuário Não Registrado",
                    f"{'Você não está' if target_user == interaction.user else f'{target_user.display_name} não está'} registrado no sistema PUBG.\n\n"
                    "Use `/pubg_register` para se registrar primeiro.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Buscar perfil completo
            async with self.pubg_system as pubg:
                with record_timer('pubg_stats_fetch_duration') if record_timer else nullcontext():
                    profile = await pubg.get_player_complete_profile(
                        user_data['pubg_name'],
                        user_data['shard']
                    )
                
                if not profile:
                    embed = await self._create_error_embed(
                        "Dados Não Disponíveis",
                        "Não foi possível obter as estatísticas do jogador no momento.",
                        interaction.user
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Criar embed com estatísticas
                embed = discord.Embed(
                    title=f"📊 Estatísticas PUBG - {profile['player']['name']}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.set_thumbnail(url=target_user.display_avatar.url)
                
                # Informações básicas
                embed.add_field(
                    name="👤 Jogador",
                    value=f"**Nome:** {profile['player']['name']}\n"
                          f"**Plataforma:** {profile['player']['shard'].upper()}\n"
                          f"**Temporada:** {profile['season']['id']}",
                    inline=True
                )
                
                # Estatísticas por modo
                stats = profile.get('stats', {})
                if not stats:
                    embed.add_field(
                        name="⚠️ Sem Dados",
                        value="Nenhuma estatística encontrada para esta temporada.",
                        inline=False
                    )
                else:
                    # Se modo específico foi solicitado
                    if modo and modo in stats:
                        stat_data = stats[modo]
                        embed.add_field(
                            name=f"🎮 {modo.upper()}",
                            value=self._format_stats(stat_data),
                            inline=False
                        )
                    else:
                        # Mostrar todos os modos (limitado a 3 para não sobrecarregar)
                        modes_shown = 0
                        priority_modes = ['squad', 'duo', 'solo']
                        
                        for mode in priority_modes:
                            if mode in stats and modes_shown < 3:
                                stat_data = stats[mode]
                                embed.add_field(
                                    name=f"🎮 {mode.upper()}",
                                    value=self._format_stats(stat_data),
                                    inline=True
                                )
                                modes_shown += 1
                
                # Informações adicionais
                embed.add_field(
                    name="📈 Qualidade dos Dados",
                    value=f"**Status:** {stats.get(list(stats.keys())[0], {}).get('data_quality', 'unknown').title() if stats else 'N/A'}\n"
                          f"**Atualizado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    inline=False
                )
                
                embed.set_footer(
                    text=f"Solicitado por {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                # Salvar no cache
                self._save_to_cache(cache_key, embed)
                
                await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.secure_logger.error(f"Erro ao buscar estatísticas PUBG: {e}", extra={
                'user_id': target_user.id,
                'requested_by': interaction.user.id,
                'mode': modo
            })
            
            embed = await self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao buscar as estatísticas. Tente novamente em alguns minutos.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    def _format_stats(self, stat_data: Dict[str, Any]) -> str:
        """Formata estatísticas para exibição"""
        if hasattr(stat_data, 'dict'):
            stat_data = stat_data.dict()
        
        matches = stat_data.get('matches_played', 0)
        wins = stat_data.get('wins', 0)
        kills = stat_data.get('kills', 0)
        deaths = stat_data.get('deaths', 0)
        kd = stat_data.get('kd_ratio', 0.0)
        win_rate = stat_data.get('win_rate', 0.0)
        avg_damage = stat_data.get('avg_damage', 0.0)
        
        return (
            f"**Partidas:** {matches}\n"
            f"**Vitórias:** {wins}\n"
            f"**K/D:** {kd}\n"
            f"**Taxa de Vitória:** {win_rate}%\n"
            f"**Dano Médio:** {avg_damage:.0f}"
        )
    
    @app_commands.command(
        name="pubg_leaderboard",
        description="🏆 Mostra o ranking PUBG do servidor"
    )
    @app_commands.describe(
        modo="Modo de jogo para o ranking",
        limite="Número de jogadores no ranking (máximo 20)"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Squad", value="squad"),
        app_commands.Choice(name="Duo", value="duo"),
        app_commands.Choice(name="Solo", value="solo")
    ])
    async def pubg_leaderboard(self, interaction: discord.Interaction, modo: str = "squad", limite: int = 10):
        """Mostra ranking PUBG do servidor"""
        await interaction.response.defer()
        
        try:
            # Limitar o número de resultados
            limite = min(max(limite, 5), 20)
            
            # Verificar cache
            cache_key = self._get_cache_key(interaction.guild.id, 'leaderboard', modo, limite)
            if self._is_cache_valid(cache_key):
                cached_embed = self.command_cache[cache_key]['data']
                await interaction.followup.send(embed=cached_embed)
                return
            
            # Registrar métrica
            if increment_counter:
                increment_counter('pubg_leaderboard_requests_total')
            
            if not hasattr(self.bot, 'storage'):
                embed = await self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema de dados não está disponível.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Buscar todos os usuários registrados do servidor
            guild_members = [member.id for member in interaction.guild.members if not member.bot]
            registered_users = self.bot.storage.get_guild_pubg_users(interaction.guild.id, guild_members)
            
            if not registered_users:
                embed = await self._create_error_embed(
                    "Nenhum Usuário Registrado",
                    "Nenhum membro do servidor está registrado no sistema PUBG.\n\n"
                    "Use `/pubg_register` para se registrar!",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Buscar estatísticas de todos os usuários
            leaderboard_data = []
            
            if self.pubg_system:
                async with self.pubg_system as pubg:
                    for user_data in registered_users[:limite]:  # Limitar para evitar muitas requisições
                        try:
                            profile = await pubg.get_player_complete_profile(
                                user_data['pubg_name'],
                                user_data['shard']
                            )
                            
                            if profile and 'stats' in profile and modo in profile['stats']:
                                stat_data = profile['stats'][modo]
                                
                                # Calcular pontuação para ranking
                                score = self._calculate_ranking_score(stat_data)
                                
                                leaderboard_data.append({
                                    'discord_id': user_data['discord_id'],
                                    'pubg_name': profile['player']['name'],
                                    'stats': stat_data,
                                    'score': score
                                })
                        
                        except Exception as e:
                            logger.warning(f"Erro ao buscar dados de {user_data['pubg_name']}: {e}")
                            continue
            
            if not leaderboard_data:
                embed = await self._create_error_embed(
                    "Dados Indisponíveis",
                    "Não foi possível obter dados suficientes para gerar o ranking.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Ordenar por pontuação
            leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
            
            # Criar embed do leaderboard
            embed = discord.Embed(
                title=f"🏆 Ranking PUBG - {modo.upper()}",
                description=f"Top {len(leaderboard_data)} jogadores do servidor",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            # Adicionar jogadores ao ranking
            ranking_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, player_data in enumerate(leaderboard_data[:limite]):
                position = i + 1
                medal = medals[i] if i < 3 else f"**{position}.**"
                
                # Buscar membro do Discord
                member = interaction.guild.get_member(player_data['discord_id'])
                display_name = member.display_name if member else "Usuário Desconhecido"
                
                stats = player_data['stats']
                if hasattr(stats, 'dict'):
                    stats = stats.dict()
                
                ranking_text += (
                    f"{medal} **{display_name}**\n"
                    f"└ `{player_data['pubg_name']}` • "
                    f"K/D: {stats.get('kd_ratio', 0):.2f} • "
                    f"WR: {stats.get('win_rate', 0):.1f}% • "
                    f"Partidas: {stats.get('matches_played', 0)}\n\n"
                )
            
            embed.description = ranking_text
            
            embed.add_field(
                name="📊 Critério de Ranking",
                value="Baseado em K/D, taxa de vitória e número de partidas",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Atualização",
                value="Dados atualizados em tempo real",
                inline=True
            )
            
            embed.set_footer(
                text=f"Solicitado por {interaction.user.display_name} • {interaction.guild.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Salvar no cache
            self._save_to_cache(cache_key, embed)
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            self.secure_logger.error(f"Erro ao gerar leaderboard PUBG: {e}", extra={
                'guild_id': interaction.guild.id,
                'mode': modo,
                'limit': limite
            })
            
            embed = await self._create_error_embed(
                "Erro Interno",
                "Ocorreu um erro ao gerar o ranking. Tente novamente em alguns minutos.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    def _calculate_ranking_score(self, stats: Dict[str, Any]) -> float:
        """Calcula pontuação para ranking baseada nas estatísticas"""
        if hasattr(stats, 'dict'):
            stats = stats.dict()
        
        matches = stats.get('matches_played', 0)
        kd = stats.get('kd_ratio', 0.0)
        win_rate = stats.get('win_rate', 0.0)
        
        # Penalizar jogadores com poucas partidas
        match_factor = min(matches / 50, 1.0)  # Fator máximo com 50+ partidas
        
        # Fórmula de pontuação balanceada
        score = (kd * 0.4 + win_rate * 0.4 + matches * 0.001) * match_factor
        
        return round(score, 3)
    
    @app_commands.command(
        name="pubg_health",
        description="🔧 Verifica o status da API PUBG"
    )
    async def pubg_health(self, interaction: discord.Interaction):
        """Verifica o status da API PUBG"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            if not self.pubg_system:
                embed = await self._create_error_embed(
                    "Sistema Indisponível",
                    "O sistema PUBG não está configurado.",
                    interaction.user
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar saúde da API
            async with self.pubg_system as pubg:
                health_data = await pubg.health_check()
            
            # Criar embed baseado no status
            if health_data['status'] == 'healthy':
                embed = discord.Embed(
                    title="✅ API PUBG Saudável",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            elif health_data['status'] == 'degraded':
                embed = discord.Embed(
                    title="⚠️ API PUBG Degradada",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="❌ API PUBG Indisponível",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            
            # Adicionar informações detalhadas
            embed.add_field(
                name="📊 Status",
                value=f"**Estado:** {health_data['status'].title()}\n"
                      f"**Tempo de Resposta:** {health_data.get('response_time_ms', 'N/A')}ms",
                inline=True
            )
            
            metrics = health_data.get('metrics', {})
            embed.add_field(
                name="📈 Métricas",
                value=f"**Requisições:** {metrics.get('requests_made', 0)}\n"
                      f"**Cache Hits:** {metrics.get('cache_hits', 0)}\n"
                      f"**Erros:** {metrics.get('errors', 0)}",
                inline=True
            )
            
            embed.add_field(
                name="🕐 Última Verificação",
                value=health_data.get('last_check', 'N/A'),
                inline=False
            )
            
            embed.set_footer(
                text=f"Verificado por {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            self.secure_logger.error(f"Erro ao verificar saúde da API PUBG: {e}")
            
            embed = await self._create_error_embed(
                "Erro na Verificação",
                "Não foi possível verificar o status da API PUBG.",
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

# ==================== SETUP DO COG ====================

async def setup(bot):
    """Setup do cog"""
    await bot.add_cog(ModernPUBGCommands(bot))
    logger.info("Cog ModernPUBGCommands carregado com sucesso")

# ==================== CONTEXT MANAGER HELPER ====================

from contextlib import nullcontext

if __name__ == "__main__":
    # Exemplo de uso dos comandos
    pass