#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Ranking Duplo - Hawk Bot
Gerencia dois tipos de ranking: PUBG (baseado em stats reais) e Interno (baseado em atividades do servidor)

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger('HawkBot.DualRankingSystem')

class RankingType(Enum):
    """Tipos de ranking disponíveis"""
    PUBG = "pubg"
    INTERNAL = "internal"

class InternalRankTier(Enum):
    """Tiers do ranking interno"""
    LEGEND = {"name": "Lenda", "points": 10000, "color": 0xFF6B35, "emoji": "👑"}
    MASTER = {"name": "Mestre", "points": 7500, "color": 0x9B59B6, "emoji": "💎"}
    DIAMOND = {"name": "Diamante", "points": 5000, "color": 0x3498DB, "emoji": "💠"}
    GOLD = {"name": "Ouro", "points": 2500, "color": 0xF1C40F, "emoji": "🏆"}
    SILVER = {"name": "Prata", "points": 1000, "color": 0x95A5A6, "emoji": "🥈"}
    BRONZE = {"name": "Bronze", "points": 500, "color": 0xD35400, "emoji": "🥉"}
    ROOKIE = {"name": "Novato", "points": 0, "color": 0x7F8C8D, "emoji": "🌱"}

class ActivityType(Enum):
    """Tipos de atividades que geram pontos internos"""
    MESSAGE_SENT = {"points": 1, "daily_limit": 50}
    VOICE_MINUTE = {"points": 2, "daily_limit": 120}
    TOURNAMENT_PARTICIPATION = {"points": 100, "daily_limit": None}
    TOURNAMENT_WIN = {"points": 500, "daily_limit": None}
    MINIGAME_WIN = {"points": 25, "daily_limit": 10}
    ACHIEVEMENT_UNLOCK = {"points": 150, "daily_limit": None}
    DAILY_CHALLENGE = {"points": 75, "daily_limit": 1}
    WEEKLY_CHALLENGE = {"points": 200, "daily_limit": None}
    MONTHLY_CHALLENGE = {"points": 500, "daily_limit": None}
    HELPING_MEMBER = {"points": 50, "daily_limit": 5}
    EVENT_PARTICIPATION = {"points": 100, "daily_limit": None}
    STREAK_BONUS = {"points": 25, "daily_limit": 1}

class DualRankingSystem:
    """Sistema de ranking duplo para PUBG e atividades internas"""
    
    def __init__(self, bot, storage, pubg_api, rank_system):
        self.bot = bot
        self.storage = storage
        self.pubg_api = pubg_api
        self.rank_system = rank_system  # Sistema PUBG existente
        
        # Configurações
        self.data_file = "dual_ranking_data.json"
        self.config_file = "dual_ranking_config.json"
        
        # Dados internos
        self.internal_data = self._load_internal_data()
        self.config = self._load_config()
        
        # Cache para otimização
        self._leaderboard_cache = {}
        self._cache_expiry = {}
        
        logger.info("Sistema de Ranking Duplo inicializado")
    
    def _load_internal_data(self) -> Dict[str, Any]:
        """Carrega dados do ranking interno"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar dados internos: {e}")
        
        return {
            "players": {},
            "daily_activities": {},
            "streaks": {},
            "last_reset": datetime.now().isoformat()
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do sistema"""
        default_config = {
            "point_multipliers": {
                "weekend": 1.5,
                "event_day": 2.0,
                "birthday": 3.0
            },
            "streak_bonuses": {
                "3_days": 50,
                "7_days": 150,
                "14_days": 300,
                "30_days": 750
            },
            "rank_roles": {
                "internal": {
                    "Lenda": "Lenda Interna",
                    "Mestre": "Mestre Interno",
                    "Diamante": "Diamante Interno",
                    "Ouro": "Ouro Interno",
                    "Prata": "Prata Interno",
                    "Bronze": "Bronze Interno",
                    "Novato": "Novato Interno"
                },
                "pubg": {
                    "Predador": "Predador PUBG",
                    "Diamante": "Diamante PUBG",
                    "Ouro": "Ouro PUBG",
                    "Prata": "Prata PUBG",
                    "Bronze": "Bronze PUBG"
                }
            },
            "daily_reset_hour": 0,
            "leaderboard_cache_minutes": 15
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge com configurações padrão
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
        
        # Salvar configurações padrão
        self._save_config(default_config)
        return default_config
    
    def _save_internal_data(self):
        """Salva dados do ranking interno"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.internal_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar dados internos: {e}")
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configurações"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
    
    def _get_internal_rank(self, points: int) -> Dict[str, Any]:
        """Determina o rank interno baseado nos pontos"""
        for tier in reversed(list(InternalRankTier)):
            if points >= tier.value["points"]:
                return {
                    "name": tier.value["name"],
                    "points_required": tier.value["points"],
                    "color": tier.value["color"],
                    "emoji": tier.value["emoji"],
                    "tier": tier.name
                }
        
        # Fallback para Novato
        rookie = InternalRankTier.ROOKIE.value
        return {
            "name": rookie["name"],
            "points_required": rookie["points"],
            "color": rookie["color"],
            "emoji": rookie["emoji"],
            "tier": "ROOKIE"
        }
    
    def _get_next_rank(self, current_points: int) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre o próximo rank"""
        for tier in list(InternalRankTier):
            if current_points < tier.value["points"]:
                return {
                    "name": tier.value["name"],
                    "points_required": tier.value["points"],
                    "points_needed": tier.value["points"] - current_points,
                    "color": tier.value["color"],
                    "emoji": tier.value["emoji"]
                }
        return None
    
    async def add_internal_points(self, user_id: str, activity_type: ActivityType, 
                                amount: int = None, reason: str = None) -> Dict[str, Any]:
        """Adiciona pontos internos para um usuário"""
        try:
            user_id = str(user_id)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Inicializar dados do usuário se necessário
            if user_id not in self.internal_data["players"]:
                self.internal_data["players"][user_id] = {
                    "total_points": 0,
                    "current_rank": "Novato",
                    "rank_history": [],
                    "last_activity": None,
                    "achievements": []
                }
            
            if user_id not in self.internal_data["daily_activities"]:
                self.internal_data["daily_activities"][user_id] = {}
            
            if today not in self.internal_data["daily_activities"][user_id]:
                self.internal_data["daily_activities"][user_id][today] = {}
            
            # Verificar limite diário
            activity_config = activity_type.value
            daily_limit = activity_config.get("daily_limit")
            base_points = amount if amount is not None else activity_config["points"]
            
            if daily_limit is not None:
                current_count = self.internal_data["daily_activities"][user_id][today].get(activity_type.name, 0)
                if current_count >= daily_limit:
                    return {
                        "success": False,
                        "error": f"Limite diário de {daily_limit} atingido para {activity_type.name}",
                        "points_added": 0
                    }
            
            # Aplicar multiplicadores
            final_points = self._apply_multipliers(base_points, user_id)
            
            # Atualizar dados
            old_points = self.internal_data["players"][user_id]["total_points"]
            old_rank = self._get_internal_rank(old_points)
            
            self.internal_data["players"][user_id]["total_points"] += final_points
            self.internal_data["players"][user_id]["last_activity"] = datetime.now().isoformat()
            
            # Atualizar contadores diários
            if activity_type.name not in self.internal_data["daily_activities"][user_id][today]:
                self.internal_data["daily_activities"][user_id][today][activity_type.name] = 0
            self.internal_data["daily_activities"][user_id][today][activity_type.name] += 1
            
            # Verificar mudança de rank
            new_points = self.internal_data["players"][user_id]["total_points"]
            new_rank = self._get_internal_rank(new_points)
            
            rank_changed = old_rank["name"] != new_rank["name"]
            if rank_changed:
                self.internal_data["players"][user_id]["current_rank"] = new_rank["name"]
                self.internal_data["players"][user_id]["rank_history"].append({
                    "rank": new_rank["name"],
                    "points": new_points,
                    "date": datetime.now().isoformat(),
                    "previous_rank": old_rank["name"]
                })
            
            # Verificar streak
            streak_bonus = await self._check_streak_bonus(user_id)
            if streak_bonus > 0:
                self.internal_data["players"][user_id]["total_points"] += streak_bonus
                final_points += streak_bonus
            
            # Salvar dados
            self._save_internal_data()
            
            # Limpar cache
            self._clear_leaderboard_cache()
            
            return {
                "success": True,
                "points_added": final_points,
                "total_points": self.internal_data["players"][user_id]["total_points"],
                "old_rank": old_rank,
                "new_rank": new_rank,
                "rank_changed": rank_changed,
                "streak_bonus": streak_bonus,
                "reason": reason or activity_type.name
            }
            
        except Exception as e:
            logger.error(f"Erro ao adicionar pontos internos: {e}")
            return {"success": False, "error": str(e), "points_added": 0}
    
    def _apply_multipliers(self, base_points: int, user_id: str) -> int:
        """Aplica multiplicadores baseados em eventos especiais"""
        multiplier = 1.0
        now = datetime.now()
        
        # Multiplicador de fim de semana
        if now.weekday() >= 5:  # Sábado ou Domingo
            multiplier *= self.config["point_multipliers"]["weekend"]
        
        # Verificar se é aniversário do usuário
        # (implementar lógica de aniversário se necessário)
        
        return int(base_points * multiplier)
    
    async def _check_streak_bonus(self, user_id: str) -> int:
        """Verifica e aplica bônus de streak"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            if user_id not in self.internal_data["streaks"]:
                self.internal_data["streaks"][user_id] = {
                    "current_streak": 0,
                    "last_activity_date": None,
                    "best_streak": 0
                }
            
            streak_data = self.internal_data["streaks"][user_id]
            last_date = streak_data["last_activity_date"]
            
            if last_date == yesterday:
                # Continuar streak
                streak_data["current_streak"] += 1
            elif last_date != today:
                # Resetar streak se não foi ontem nem hoje
                streak_data["current_streak"] = 1
            
            streak_data["last_activity_date"] = today
            
            # Atualizar melhor streak
            if streak_data["current_streak"] > streak_data["best_streak"]:
                streak_data["best_streak"] = streak_data["current_streak"]
            
            # Calcular bônus
            current_streak = streak_data["current_streak"]
            bonus = 0
            
            for days, bonus_points in self.config["streak_bonuses"].items():
                required_days = int(days.split('_')[0])
                if current_streak >= required_days and current_streak % required_days == 0:
                    bonus = max(bonus, bonus_points)
            
            return bonus
            
        except Exception as e:
            logger.error(f"Erro ao verificar streak bonus: {e}")
            return 0
    
    def _clear_leaderboard_cache(self):
        """Limpa cache dos leaderboards"""
        self._leaderboard_cache.clear()
        self._cache_expiry.clear()
    
    async def get_user_profile(self, user_id: str, ranking_type: RankingType = None) -> Dict[str, Any]:
        """Retorna perfil completo do usuário com ambos os rankings"""
        try:
            user_id = str(user_id)
            profile = {
                "user_id": user_id,
                "pubg_ranking": None,
                "internal_ranking": None,
                "combined_stats": {}
            }
            
            # Ranking PUBG (usar sistema existente)
            if ranking_type is None or ranking_type == RankingType.PUBG:
                pubg_data = self.storage.get_player(user_id)
                if pubg_data:
                    profile["pubg_ranking"] = {
                        "ranked_rank": pubg_data.get("ranked_rank", "Sem rank"),
                        "mm_rank": pubg_data.get("mm_rank", "Sem rank MM"),
                        "pubg_name": pubg_data.get("pubg_name"),
                        "season_stats": pubg_data.get("season_stats", {}),
                        "last_update": pubg_data.get("last_stats_update")
                    }
            
            # Ranking Interno
            if ranking_type is None or ranking_type == RankingType.INTERNAL:
                if user_id in self.internal_data["players"]:
                    internal_data = self.internal_data["players"][user_id]
                    current_points = internal_data["total_points"]
                    current_rank = self._get_internal_rank(current_points)
                    next_rank = self._get_next_rank(current_points)
                    
                    # Estatísticas de streak
                    streak_data = self.internal_data["streaks"].get(user_id, {})
                    
                    profile["internal_ranking"] = {
                        "total_points": current_points,
                        "current_rank": current_rank,
                        "next_rank": next_rank,
                        "rank_history": internal_data.get("rank_history", []),
                        "last_activity": internal_data.get("last_activity"),
                        "current_streak": streak_data.get("current_streak", 0),
                        "best_streak": streak_data.get("best_streak", 0),
                        "achievements": internal_data.get("achievements", [])
                    }
                else:
                    # Usuário novo
                    rookie_rank = self._get_internal_rank(0)
                    next_rank = self._get_next_rank(0)
                    
                    profile["internal_ranking"] = {
                        "total_points": 0,
                        "current_rank": rookie_rank,
                        "next_rank": next_rank,
                        "rank_history": [],
                        "last_activity": None,
                        "current_streak": 0,
                        "best_streak": 0,
                        "achievements": []
                    }
            
            return profile
            
        except Exception as e:
            logger.error(f"Erro ao obter perfil do usuário: {e}")
            return {"error": str(e)}
    
    async def get_user_profile_embed(self, user: discord.Member) -> discord.Embed:
        """Retorna embed com perfil completo do usuário com ambos os rankings"""
        try:
            user_id = str(user.id)
            profile = await self.get_user_profile(user_id)
            
            if "error" in profile:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Erro ao obter perfil do usuário.",
                    color=0xFF0000
                )
                return embed
            
            # Obter nome e avatar do usuário (com fallback para testes)
            display_name = getattr(user, 'display_name', f'Usuário {user_id[:8]}')
            avatar_url = getattr(user, 'display_avatar', None)
            avatar_url = avatar_url.url if avatar_url else None
            
            # Criar embed principal
            embed = discord.Embed(
                title="📊 Perfil Completo - Ranking Duplo",
                description=f"**{display_name}** - Rankings PUBG e Servidor",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            
            # Ranking PUBG
            pubg_ranking = profile.get("pubg_ranking")
            if pubg_ranking:
                pubg_text = f"**Nome PUBG:** {pubg_ranking.get('pubg_name', 'N/A')}\n"
                pubg_text += f"**Rank Ranqueada:** {pubg_ranking.get('ranked_rank', 'Sem rank')}\n"
                pubg_text += f"**Rank MM:** {pubg_ranking.get('mm_rank', 'Sem rank MM')}\n"
                
                # Estatísticas da temporada
                season_stats = pubg_ranking.get('season_stats', {})
                if season_stats:
                    ranked_stats = season_stats.get('ranked', {})
                    squad_stats = ranked_stats.get('squad', {})
                    if squad_stats:
                        pubg_text += f"**K/D:** {squad_stats.get('kd', 'N/A')}\n"
                        pubg_text += f"**Vitórias:** {squad_stats.get('wins', 'N/A')}\n"
                        pubg_text += f"**Partidas:** {squad_stats.get('matches', 'N/A')}"
                
                embed.add_field(
                    name="🎮 Ranking PUBG",
                    value=pubg_text,
                    inline=True
                )
            else:
                embed.add_field(
                    name="🎮 Ranking PUBG",
                    value="❌ **Não registrado**\n\nUse `/register_pubg` para se registrar!",
                    inline=True
                )
            
            # Ranking Interno
            internal_ranking = profile.get("internal_ranking")
            if internal_ranking:
                current_rank = internal_ranking.get('current_rank', {})
                next_rank = internal_ranking.get('next_rank')
                
                internal_text = f"**Rank:** {current_rank.get('name', 'Rookie')} {current_rank.get('emoji', '🥉')}\n"
                internal_text += f"**Pontos:** {internal_ranking.get('total_points', 0)}\n"
                internal_text += f"**Sequência Atual:** {internal_ranking.get('current_streak', 0)} dias\n"
                internal_text += f"**Melhor Sequência:** {internal_ranking.get('best_streak', 0)} dias\n"
                
                if next_rank:
                    points_needed = next_rank.get('min_points', 0) - internal_ranking.get('total_points', 0)
                    if points_needed > 0:
                        internal_text += f"**Próximo Rank:** {next_rank.get('name', 'N/A')} ({points_needed} pts)"
                    else:
                        internal_text += f"**Rank Máximo Atingido!** 🏆"
                
                embed.add_field(
                    name="🏠 Ranking Interno",
                    value=internal_text,
                    inline=True
                )
            else:
                embed.add_field(
                    name="🏠 Ranking Interno",
                    value="❌ **Sem dados**\n\nParticipe mais do servidor para ganhar pontos!",
                    inline=True
                )
            
            # Estatísticas combinadas
            embed.add_field(
                name="📈 Progresso",
                value="• Use `/ranking_pubg` para ver ranking PUBG\n" +
                      "• Use `/ranking_servidor` para ver ranking interno\n" +
                      "• Participe de atividades para ganhar pontos!",
                inline=False
            )
            
            # Footer com informações adicionais
            footer_text = "💡 Dica: Mantenha-se ativo para subir no ranking interno!"
            if avatar_url:
                embed.set_footer(text=footer_text, icon_url=avatar_url)
            else:
                embed.set_footer(text=footer_text)
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao criar embed do perfil: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao gerar perfil do usuário.",
                color=0xFF0000
            )
            return embed
    
    async def generate_dual_leaderboard(self, guild_id: str, ranking_type: RankingType, 
                                      limit: int = 10) -> discord.Embed:
        """Gera leaderboard para o tipo de ranking especificado"""
        try:
            cache_key = f"{ranking_type.value}_{limit}"
            now = datetime.now()
            
            # Verificar cache
            if (cache_key in self._leaderboard_cache and 
                cache_key in self._cache_expiry and 
                now < self._cache_expiry[cache_key]):
                return self._leaderboard_cache[cache_key]
            
            if ranking_type == RankingType.PUBG:
                # Usar sistema existente para PUBG
                embed = await self.rank_system.generate_leaderboard(guild_id, limit=limit)
                embed.title = "🎮 Ranking PUBG - Hawk Esports"
                embed.description = "**Baseado em estatísticas reais do PUBG**"
            
            elif ranking_type == RankingType.INTERNAL:
                # Gerar leaderboard interno
                embed = await self._generate_internal_leaderboard(guild_id, limit)
            
            # Cache do resultado
            cache_expiry = now + timedelta(minutes=self.config["leaderboard_cache_minutes"])
            self._leaderboard_cache[cache_key] = embed
            self._cache_expiry[cache_key] = cache_expiry
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard duplo: {e}")
            return discord.Embed(
                title="❌ Erro",
                description="Não foi possível gerar o leaderboard.",
                color=0xFF0000
            )
    
    async def _generate_internal_leaderboard(self, guild_id: str, limit: int) -> discord.Embed:
        """Gera leaderboard do ranking interno"""
        try:
            # Ordenar jogadores por pontos
            sorted_players = sorted(
                self.internal_data["players"].items(),
                key=lambda x: x[1]["total_points"],
                reverse=True
            )
            
            # Criar embed
            embed = discord.Embed(
                title="🏆 Ranking Interno - Hawk Esports",
                description="**Baseado em atividades do servidor**",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            # Adicionar jogadores
            leaderboard_text = ""
            guild = self.bot.get_guild(int(guild_id))
            
            for i, (user_id, data) in enumerate(sorted_players[:limit], 1):
                try:
                    member = guild.get_member(int(user_id)) if guild else None
                    display_name = member.display_name if member else f"Usuário {user_id[:8]}"
                    
                    rank_info = self._get_internal_rank(data["total_points"])
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    
                    streak_data = self.internal_data["streaks"].get(user_id, {})
                    current_streak = streak_data.get("current_streak", 0)
                    
                    leaderboard_text += (
                        f"{medal} **{display_name}** {rank_info['emoji']}\n"
                        f"   {rank_info['name']} | {data['total_points']:,} pts"
                    )
                    
                    if current_streak > 0:
                        leaderboard_text += f" | 🔥 {current_streak} dias"
                    
                    leaderboard_text += "\n\n"
                    
                except Exception as e:
                    logger.error(f"Erro ao processar jogador {user_id}: {e}")
                    continue
            
            if leaderboard_text:
                embed.add_field(
                    name="📊 Top Jogadores",
                    value=leaderboard_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📊 Top Jogadores",
                    value="Nenhum jogador encontrado.",
                    inline=False
                )
            
            # Estatísticas gerais
            total_players = len(self.internal_data["players"])
            active_today = len([p for p in self.internal_data["players"].values() 
                              if p.get("last_activity") and 
                              datetime.fromisoformat(p["last_activity"]).date() == datetime.now().date()])
            
            embed.add_field(
                name="📈 Estatísticas",
                value=f"Total de jogadores: **{total_players}**\n"
                      f"Ativos hoje: **{active_today}**\n"
                      f"Última atualização: **Agora**",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Como Ganhar Pontos",
                value="• Enviar mensagens (1 pt)\n"
                      "• Participar de voice (2 pts/min)\n"
                      "• Ganhar mini-games (25 pts)\n"
                      "• Participar de torneios (100+ pts)\n"
                      "• Completar desafios (75+ pts)",
                inline=True
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard interno: {e}")
            raise
    
    async def update_member_roles(self, member: discord.Member):
        """Atualiza roles do membro baseado em ambos os rankings"""
        try:
            user_id = str(member.id)
            guild_id = str(member.guild.id)
            
            # Obter perfil completo
            profile = await self.get_user_profile(user_id)
            
            # Roles a adicionar e remover
            roles_to_add = []
            roles_to_remove = []
            
            # Processar roles do ranking PUBG
            if profile.get("pubg_ranking"):
                pubg_rank = profile["pubg_ranking"].get("ranked_rank", "Sem rank")
                if pubg_rank in self.config["rank_roles"]["pubg"]:
                    role_name = self.config["rank_roles"]["pubg"][pubg_rank]
                    role = discord.utils.get(member.guild.roles, name=role_name)
                    if role:
                        roles_to_add.append(role)
                
                # Remover outras roles PUBG
                for rank_name, role_name in self.config["rank_roles"]["pubg"].items():
                    if rank_name != pubg_rank:
                        role = discord.utils.get(member.guild.roles, name=role_name)
                        if role and role in member.roles:
                            roles_to_remove.append(role)
            
            # Processar roles do ranking interno
            if profile.get("internal_ranking"):
                internal_rank = profile["internal_ranking"]["current_rank"]["name"]
                if internal_rank in self.config["rank_roles"]["internal"]:
                    role_name = self.config["rank_roles"]["internal"][internal_rank]
                    role = discord.utils.get(member.guild.roles, name=role_name)
                    if role:
                        roles_to_add.append(role)
                
                # Remover outras roles internas
                for rank_name, role_name in self.config["rank_roles"]["internal"].items():
                    if rank_name != internal_rank:
                        role = discord.utils.get(member.guild.roles, name=role_name)
                        if role and role in member.roles:
                            roles_to_remove.append(role)
            
            # Aplicar mudanças de roles
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Atualização de ranking")
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Atualização de ranking")
            
            logger.info(f"Roles atualizadas para {member.display_name}: +{len(roles_to_add)}, -{len(roles_to_remove)}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar roles do membro {member.display_name}: {e}")
    
    async def reset_daily_activities(self):
        """Reseta atividades diárias (executar diariamente)"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Limpar dados antigos (manter apenas últimos 30 dias)
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            for user_id in list(self.internal_data["daily_activities"].keys()):
                user_activities = self.internal_data["daily_activities"][user_id]
                dates_to_remove = [date for date in user_activities.keys() if date < cutoff_date]
                
                for date in dates_to_remove:
                    del user_activities[date]
                
                # Remover usuário se não tem atividades
                if not user_activities:
                    del self.internal_data["daily_activities"][user_id]
            
            self.internal_data["last_reset"] = datetime.now().isoformat()
            self._save_internal_data()
            
            logger.info("Reset diário de atividades concluído")
            
        except Exception as e:
            logger.error(f"Erro no reset diário: {e}")
    
    def get_activity_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Retorna estatísticas de atividade dos últimos N dias"""
        try:
            user_id = str(user_id)
            stats = {
                "total_points_earned": 0,
                "activities_by_type": {},
                "daily_breakdown": {},
                "most_active_day": None,
                "average_daily_points": 0
            }
            
            if user_id not in self.internal_data["daily_activities"]:
                return stats
            
            user_activities = self.internal_data["daily_activities"][user_id]
            
            # Calcular estatísticas dos últimos N dias
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                if date in user_activities:
                    daily_data = user_activities[date]
                    daily_points = 0
                    
                    for activity_type, count in daily_data.items():
                        try:
                            activity_enum = ActivityType[activity_type]
                            points_per_activity = activity_enum.value["points"]
                            total_points = points_per_activity * count
                            
                            daily_points += total_points
                            
                            if activity_type not in stats["activities_by_type"]:
                                stats["activities_by_type"][activity_type] = {"count": 0, "points": 0}
                            
                            stats["activities_by_type"][activity_type]["count"] += count
                            stats["activities_by_type"][activity_type]["points"] += total_points
                            
                        except KeyError:
                            continue
                    
                    stats["daily_breakdown"][date] = daily_points
                    stats["total_points_earned"] += daily_points
            
            # Encontrar dia mais ativo
            if stats["daily_breakdown"]:
                stats["most_active_day"] = max(stats["daily_breakdown"].items(), key=lambda x: x[1])
                stats["average_daily_points"] = stats["total_points_earned"] / len(stats["daily_breakdown"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de atividade: {e}")
            return {"error": str(e)}
    
    async def show_pubg_badges(self, user: discord.Member) -> discord.Embed:
        """Mostra badges PUBG de um usuário"""
        try:
            # Obter dados do usuário
            user_data = self.storage.get_player(str(user.id))
            if not user_data:
                embed = discord.Embed(
                    title="🎮 Badges PUBG",
                    description=f"{user.display_name} não está registrado no sistema PUBG.",
                    color=0x808080
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                return embed
            
            # Obter badges do badge_system
            from badge_system import BadgeSystem
            badge_system = getattr(self.bot, 'badge_system', None)
            if not badge_system:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Sistema de badges não disponível.",
                    color=0xFF0000
                )
                return embed
            
            user_badges = badge_system.get_user_badges(str(user.id))
            pubg_badges = [b for b in user_badges.get('badges', []) if b.get('category') == 'combat' or b.get('category') == 'survival']
            
            embed = discord.Embed(
                title="🎮 Badges PUBG",
                description=f"Badges relacionados ao PUBG de {user.display_name}",
                color=0x00FF00
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            if not pubg_badges:
                embed.add_field(
                    name="📋 Status",
                    value="Nenhum badge PUBG conquistado ainda.",
                    inline=False
                )
            else:
                # Organizar por categoria
                combat_badges = [b for b in pubg_badges if b.get('category') == 'combat']
                survival_badges = [b for b in pubg_badges if b.get('category') == 'survival']
                
                if combat_badges:
                    combat_text = "\n".join([f"{b['emoji']} **{b['name']}** - {b['description']}" for b in combat_badges[:5]])
                    embed.add_field(
                        name="⚔️ Combate",
                        value=combat_text,
                        inline=False
                    )
                
                if survival_badges:
                    survival_text = "\n".join([f"{b['emoji']} **{b['name']}** - {b['description']}" for b in survival_badges[:5]])
                    embed.add_field(
                        name="🛡️ Sobrevivência",
                        value=survival_text,
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Resumo",
                    value=f"Total: **{len(pubg_badges)}** badges PUBG\nPontuação: **{sum(100 for b in pubg_badges)}** pts",
                    inline=True
                )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao mostrar badges PUBG: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao obter badges PUBG.",
                color=0xFF0000
            )
            return embed
    
    async def show_server_badges(self, user: discord.Member) -> discord.Embed:
        """Mostra badges do servidor de um usuário"""
        try:
            # Obter badges do badge_system
            from badge_system import BadgeSystem
            badge_system = getattr(self.bot, 'badge_system', None)
            if not badge_system:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Sistema de badges não disponível.",
                    color=0xFF0000
                )
                return embed
            
            user_badges = badge_system.get_user_badges(str(user.id))
            server_badges = [b for b in user_badges.get('badges', []) if b.get('category') in ['support', 'achievement', 'special']]
            
            embed = discord.Embed(
                title="🏠 Badges do Servidor",
                description=f"Badges de atividades do servidor de {user.display_name}",
                color=0x3498DB
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            if not server_badges:
                embed.add_field(
                    name="📋 Status",
                    value="Nenhum badge do servidor conquistado ainda.\n\n💡 **Dica:** Participe mais das atividades do servidor para conquistar badges!",
                    inline=False
                )
            else:
                # Organizar por categoria
                support_badges = [b for b in server_badges if b.get('category') == 'support']
                achievement_badges = [b for b in server_badges if b.get('category') == 'achievement']
                special_badges = [b for b in server_badges if b.get('category') == 'special']
                
                if support_badges:
                    support_text = "\n".join([f"{b['emoji']} **{b['name']}** - {b['description']}" for b in support_badges[:3]])
                    embed.add_field(
                        name="🤝 Suporte",
                        value=support_text,
                        inline=False
                    )
                
                if achievement_badges:
                    achievement_text = "\n".join([f"{b['emoji']} **{b['name']}** - {b['description']}" for b in achievement_badges[:3]])
                    embed.add_field(
                        name="🏅 Conquistas",
                        value=achievement_text,
                        inline=False
                    )
                
                if special_badges:
                    special_text = "\n".join([f"{b['emoji']} **{b['name']}** - {b['description']}" for b in special_badges[:3]])
                    embed.add_field(
                        name="⭐ Especiais",
                        value=special_text,
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Resumo",
                    value=f"Total: **{len(server_badges)}** badges\nPontuação: **{sum(100 for b in server_badges)}** pts",
                    inline=True
                )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao mostrar badges do servidor: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao obter badges do servidor.",
                color=0xFF0000
            )
            return embed
    
    async def show_all_available_badges(self) -> discord.Embed:
        """Mostra todos os badges disponíveis no sistema"""
        try:
            from badge_system import BadgeType
            
            embed = discord.Embed(
                title="🏆 Todos os Badges Disponíveis",
                description="Lista completa de badges que podem ser conquistados",
                color=0xFFD700
            )
            
            # Organizar badges por categoria
            categories = {}
            for badge_type in BadgeType:
                badge_data = badge_type.value
                category = badge_data['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(badge_data)
            
            # Mapear emojis de categoria
            category_emojis = {
                'combat': '⚔️',
                'survival': '🛡️',
                'support': '🤝',
                'achievement': '🏅',
                'special': '⭐'
            }
            
            # Adicionar cada categoria
            for category, badges in categories.items():
                emoji = category_emojis.get(category, '📋')
                category_name = category.title()
                
                badge_list = []
                for badge in badges[:5]:  # Limitar a 5 por categoria
                    rarity_emoji = {
                        'comum': '⚪',
                        'raro': '🔵', 
                        'épico': '🟣',
                        'lendário': '🟠',
                        'mítico': '🔴'
                    }.get(badge['rarity'], '⚪')
                    
                    badge_list.append(f"{badge['emoji']} **{badge['name']}** {rarity_emoji}\n└ {badge['description']}")
                
                if badge_list:
                    embed.add_field(
                        name=f"{emoji} {category_name}",
                        value="\n\n".join(badge_list),
                        inline=False
                    )
            
            embed.add_field(
                name="💡 Como Conquistar",
                value="• **Combate**: Elimine inimigos e vença partidas\n"
                      "• **Sobrevivência**: Sobreviva e use estratégias\n"
                      "• **Suporte**: Ajude outros membros\n"
                      "• **Conquistas**: Complete desafios especiais\n"
                      "• **Especiais**: Eventos e atividades únicas",
                inline=False
            )
            
            embed.set_footer(text="Use /badges_pubg ou /badges_servidor para ver seus badges")
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao mostrar todos os badges: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao obter lista de badges.",
                color=0xFF0000
            )
            return embed