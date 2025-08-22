#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Cargos Automáticos PUBG - Hawk Bot
Gerencia cargos automáticos baseados nas patentes oficiais do PUBG

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from emoji_system import emoji_system

logger = logging.getLogger('HawkBot.PubgRankRoles')

class PubgRankTier(Enum):
    """Patentes oficiais do PUBG com emojis e cores"""
    # Bronze Tier
    BRONZE_IV = {
        "name": "Bronze IV",
        "emoji": emoji_system.get_emoji('bronze'),
        "color": 0xCD7F32,
        "min_points": 0,
        "max_points": 249,
        "role_name": f"{emoji_system.get_emoji('bronze')} Bronze IV",
        "description": "Patente Bronze IV do PUBG"
    }
    BRONZE_III = {
        "name": "Bronze III",
        "emoji": emoji_system.get_emoji('bronze'),
        "color": 0xCD7F32,
        "min_points": 250,
        "max_points": 499,
        "role_name": f"{emoji_system.get_emoji('bronze')} Bronze III",
        "description": "Patente Bronze III do PUBG"
    }
    BRONZE_II = {
        "name": "Bronze II",
        "emoji": emoji_system.get_emoji('bronze'),
        "color": 0xCD7F32,
        "min_points": 500,
        "max_points": 749,
        "role_name": f"{emoji_system.get_emoji('bronze')} Bronze II",
        "description": "Patente Bronze II do PUBG"
    }
    BRONZE_I = {
        "name": "Bronze I",
        "emoji": emoji_system.get_emoji('bronze'),
        "color": 0xCD7F32,
        "min_points": 750,
        "max_points": 999,
        "role_name": f"{emoji_system.get_emoji('bronze')} Bronze I",
        "description": "Patente Bronze I do PUBG"
    }
    
    # Silver Tier
    SILVER_IV = {
        "name": "Silver IV",
        "emoji": emoji_system.get_emoji('silver'),
        "color": 0xC0C0C0,
        "min_points": 1000,
        "max_points": 1249,
        "role_name": f"{emoji_system.get_emoji('silver')} Silver IV",
        "description": "Patente Silver IV do PUBG"
    }
    SILVER_III = {
        "name": "Silver III",
        "emoji": emoji_system.get_emoji('silver'),
        "color": 0xC0C0C0,
        "min_points": 1250,
        "max_points": 1499,
        "role_name": f"{emoji_system.get_emoji('silver')} Silver III",
        "description": "Patente Silver III do PUBG"
    }
    SILVER_II = {
        "name": "Silver II",
        "emoji": emoji_system.get_emoji('silver'),
        "color": 0xC0C0C0,
        "min_points": 1500,
        "max_points": 1749,
        "role_name": f"{emoji_system.get_emoji('silver')} Silver II",
        "description": "Patente Silver II do PUBG"
    }
    SILVER_I = {
        "name": "Silver I",
        "emoji": emoji_system.get_emoji('silver'),
        "color": 0xC0C0C0,
        "min_points": 1750,
        "max_points": 1999,
        "role_name": f"{emoji_system.get_emoji('silver')} Silver I",
        "description": "Patente Silver I do PUBG"
    }
    
    # Gold Tier
    GOLD_IV = {
        "name": "Gold IV",
        "emoji": emoji_system.get_emoji('gold'),
        "color": 0xFFD700,
        "min_points": 2000,
        "max_points": 2249,
        "role_name": f"{emoji_system.get_emoji('gold')} Gold IV",
        "description": "Patente Gold IV do PUBG"
    }
    GOLD_III = {
        "name": "Gold III",
        "emoji": emoji_system.get_emoji('gold'),
        "color": 0xFFD700,
        "min_points": 2250,
        "max_points": 2499,
        "role_name": f"{emoji_system.get_emoji('gold')} Gold III",
        "description": "Patente Gold III do PUBG"
    }
    GOLD_II = {
        "name": "Gold II",
        "emoji": emoji_system.get_emoji('gold'),
        "color": 0xFFD700,
        "min_points": 2500,
        "max_points": 2749,
        "role_name": f"{emoji_system.get_emoji('gold')} Gold II",
        "description": "Patente Gold II do PUBG"
    }
    GOLD_I = {
        "name": "Gold I",
        "emoji": emoji_system.get_emoji('gold'),
        "color": 0xFFD700,
        "min_points": 2750,
        "max_points": 2999,
        "role_name": f"{emoji_system.get_emoji('gold')} Gold I",
        "description": "Patente Gold I do PUBG"
    }
    
    # Platinum Tier
    PLATINUM_IV = {
        "name": "Platinum IV",
        "emoji": emoji_system.get_emoji('platinum'),
        "color": 0x00CED1,
        "min_points": 3000,
        "max_points": 3249,
        "role_name": f"{emoji_system.get_emoji('platinum')} Platinum IV",
        "description": "Patente Platinum IV do PUBG"
    }
    PLATINUM_III = {
        "name": "Platinum III",
        "emoji": emoji_system.get_emoji('platinum'),
        "color": 0x00CED1,
        "min_points": 3250,
        "max_points": 3499,
        "role_name": f"{emoji_system.get_emoji('platinum')} Platinum III",
        "description": "Patente Platinum III do PUBG"
    }
    PLATINUM_II = {
        "name": "Platinum II",
        "emoji": emoji_system.get_emoji('platinum'),
        "color": 0x00CED1,
        "min_points": 3500,
        "max_points": 3749,
        "role_name": f"{emoji_system.get_emoji('platinum')} Platinum II",
        "description": "Patente Platinum II do PUBG"
    }
    PLATINUM_I = {
        "name": "Platinum I",
        "emoji": emoji_system.get_emoji('platinum'),
        "color": 0x00CED1,
        "min_points": 3750,
        "max_points": 3999,
        "role_name": f"{emoji_system.get_emoji('platinum')} Platinum I",
        "description": "Patente Platinum I do PUBG"
    }
    
    # Crystal Tier
    CRYSTAL_IV = {
        "name": "Crystal IV",
        "emoji": emoji_system.get_emoji('crystal'),
        "color": 0x9370DB,
        "min_points": 4000,
        "max_points": 4249,
        "role_name": f"{emoji_system.get_emoji('crystal')} Crystal IV",
        "description": "Patente Crystal IV do PUBG"
    }
    CRYSTAL_III = {
        "name": "Crystal III",
        "emoji": emoji_system.get_emoji('crystal'),
        "color": 0x9370DB,
        "min_points": 4250,
        "max_points": 4499,
        "role_name": f"{emoji_system.get_emoji('crystal')} Crystal III",
        "description": "Patente Crystal III do PUBG"
    }
    CRYSTAL_II = {
        "name": "Crystal II",
        "emoji": emoji_system.get_emoji('crystal'),
        "color": 0x9370DB,
        "min_points": 4500,
        "max_points": 4749,
        "role_name": f"{emoji_system.get_emoji('crystal')} Crystal II",
        "description": "Patente Crystal II do PUBG"
    }
    CRYSTAL_I = {
        "name": "Crystal I",
        "emoji": emoji_system.get_emoji('crystal'),
        "color": 0x9370DB,
        "min_points": 4750,
        "max_points": 4999,
        "role_name": f"{emoji_system.get_emoji('crystal')} Crystal I",
        "description": "Patente Crystal I do PUBG"
    }
    
    # Diamond Tier
    DIAMOND_IV = {
        "name": "Diamond IV",
        "emoji": emoji_system.get_emoji('diamond'),
        "color": 0x1E90FF,
        "min_points": 5000,
        "max_points": 5249,
        "role_name": f"{emoji_system.get_emoji('diamond')} Diamond IV",
        "description": "Patente Diamond IV do PUBG"
    }
    DIAMOND_III = {
        "name": "Diamond III",
        "emoji": emoji_system.get_emoji('diamond'),
        "color": 0x1E90FF,
        "min_points": 5250,
        "max_points": 5499,
        "role_name": f"{emoji_system.get_emoji('diamond')} Diamond III",
        "description": "Patente Diamond III do PUBG"
    }
    DIAMOND_II = {
        "name": "Diamond II",
        "emoji": emoji_system.get_emoji('diamond'),
        "color": 0x1E90FF,
        "min_points": 5500,
        "max_points": 5749,
        "role_name": f"{emoji_system.get_emoji('diamond')} Diamond II",
        "description": "Patente Diamond II do PUBG"
    }
    DIAMOND_I = {
        "name": "Diamond I",
        "emoji": emoji_system.get_emoji('diamond'),
        "color": 0x1E90FF,
        "min_points": 5750,
        "max_points": 5999,
        "role_name": f"{emoji_system.get_emoji('diamond')} Diamond I",
        "description": "Patente Diamond I do PUBG"
    }
    
    # Master Tier
    MASTER_IV = {
        "name": "Master IV",
        "emoji": emoji_system.get_emoji('master'),
        "color": 0xFF4500,
        "min_points": 6000,
        "max_points": 6249,
        "role_name": f"{emoji_system.get_emoji('master')} Master IV",
        "description": "Patente Master IV do PUBG"
    }
    MASTER_III = {
        "name": "Master III",
        "emoji": emoji_system.get_emoji('master'),
        "color": 0xFF4500,
        "min_points": 6250,
        "max_points": 6499,
        "role_name": f"{emoji_system.get_emoji('master')} Master III",
        "description": "Patente Master III do PUBG"
    }
    MASTER_II = {
        "name": "Master II",
        "emoji": emoji_system.get_emoji('master'),
        "color": 0xFF4500,
        "min_points": 6500,
        "max_points": 6749,
        "role_name": f"{emoji_system.get_emoji('master')} Master II",
        "description": "Patente Master II do PUBG"
    }
    MASTER_I = {
        "name": "Master I",
        "emoji": emoji_system.get_emoji('master'),
        "color": 0xFF4500,
        "min_points": 6750,
        "max_points": 6999,
        "role_name": f"{emoji_system.get_emoji('master')} Master I",
        "description": "Patente Master I do PUBG"
    }
    
    # Survivor Tier (Highest)
    SURVIVOR = {
        "name": "Survivor",
        "emoji": emoji_system.get_emoji('survivor'),
        "color": 0xFF0000,
        "min_points": 7000,
        "max_points": 999999,
        "role_name": f"{emoji_system.get_emoji('survivor')} Survivor",
        "description": "Patente Survivor do PUBG - Elite"
    }

class PubgRankRoles:
    """Sistema de cargos automáticos baseado nas patentes do PUBG"""
    
    def __init__(self, bot, storage, dual_ranking_system):
        self.bot = bot
        self.storage = storage
        self.dual_ranking = dual_ranking_system
        self.config_file = "pubg_rank_roles_config.json"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do sistema de cargos"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config de cargos PUBG: {e}")
        
        # Configuração padrão
        return {
            "enabled": True,
            "auto_assign": True,
            "remove_old_roles": True,
            "announcement_channel": None,
            "announce_promotions": True,
            "announce_demotions": False,
            "role_permissions": {
                "create_roles": True,
                "manage_roles": True
            }
        }
    
    def _save_config(self):
        """Salva configurações do sistema"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar config de cargos PUBG: {e}")
    
    async def setup_emojis(self, guild: discord.Guild) -> Dict[str, bool]:
        """Faz upload dos emojis customizados para o servidor"""
        try:
            # Fazer upload dos emojis
            results = await emoji_system.upload_emojis_to_guild(guild)
            
            # Atualizar IDs dos emojis
            emoji_system.update_emoji_ids(guild)
            
            logger.info(f"Setup de emojis concluído: {len(results)} emojis processados")
            return results
            
        except Exception as e:
            logger.error(f"Erro no setup de emojis: {e}")
            return {}
    
    def get_rank_by_points(self, points: int) -> Dict[str, Any]:
        """Retorna a patente baseada nos pontos"""
        for rank in PubgRankTier:
            rank_data = rank.value
            if rank_data["min_points"] <= points <= rank_data["max_points"]:
                return rank_data
        
        # Se não encontrar, retorna Bronze IV
        return PubgRankTier.BRONZE_IV.value
    
    async def create_rank_role(self, guild: discord.Guild, rank_data: Dict[str, Any]) -> Optional[discord.Role]:
        """Cria um cargo de patente no servidor"""
        try:
            role_name = rank_data["role_name"]
            
            # Verifica se o cargo já existe
            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                return existing_role
            
            # Cria o novo cargo
            role = await guild.create_role(
                name=role_name,
                color=discord.Color(rank_data["color"]),
                reason=f"Cargo automático PUBG: {rank_data['description']}",
                mentionable=True
            )
            
            logger.info(f"Cargo criado: {role_name} no servidor {guild.name}")
            return role
            
        except Exception as e:
            logger.error(f"Erro ao criar cargo {rank_data['role_name']}: {e}")
            return None
    
    async def update_member_rank_role(self, member: discord.Member, pubg_points: int) -> Dict[str, Any]:
        """Atualiza o cargo de patente de um membro"""
        try:
            if not self.config["enabled"]:
                return {"success": False, "reason": "Sistema desabilitado"}
            
            # Determina a nova patente
            new_rank = self.get_rank_by_points(pubg_points)
            new_role_name = new_rank["role_name"]
            
            # Cria o cargo se não existir
            new_role = await self.create_rank_role(member.guild, new_rank)
            if not new_role:
                return {"success": False, "reason": "Erro ao criar cargo"}
            
            # Remove cargos de patente antigos
            old_rank_roles = []
            if self.config["remove_old_roles"]:
                for role in member.roles:
                    if any(tier.value["role_name"] == role.name for tier in PubgRankTier):
                        if role.name != new_role_name:
                            old_rank_roles.append(role)
                            await member.remove_roles(role, reason="Atualização automática de patente PUBG")
            
            # Adiciona o novo cargo se não tiver
            role_changed = False
            if new_role not in member.roles:
                await member.add_roles(new_role, reason="Atualização automática de patente PUBG")
                role_changed = True
            
            # Anuncia mudança se configurado
            if role_changed and self.config["announce_promotions"]:
                await self._announce_rank_change(member, new_rank, old_rank_roles)
            
            return {
                "success": True,
                "new_rank": new_rank,
                "role_changed": role_changed,
                "old_roles_removed": len(old_rank_roles)
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cargo de {member.display_name}: {e}")
            return {"success": False, "reason": str(e)}
    
    async def _announce_rank_change(self, member: discord.Member, new_rank: Dict[str, Any], old_roles: List[discord.Role]):
        """Anuncia mudança de patente"""
        try:
            if not self.config["announcement_channel"]:
                return
            
            channel = self.bot.get_channel(self.config["announcement_channel"])
            if not channel:
                return
            
            embed = discord.Embed(
                title="🎖️ Atualização de Patente PUBG",
                color=new_rank["color"],
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Jogador",
                value=member.mention,
                inline=True
            )
            
            embed.add_field(
                name="Nova Patente",
                value=f"{new_rank['emoji']} {new_rank['name']}",
                inline=True
            )
            
            if old_roles:
                old_rank_names = ", ".join([role.name for role in old_roles])
                embed.add_field(
                    name="Patente Anterior",
                    value=old_rank_names,
                    inline=False
                )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Sistema Automático de Patentes PUBG")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao anunciar mudança de patente: {e}")
    
    async def bulk_update_ranks(self, guild: discord.Guild) -> Dict[str, Any]:
        """Atualiza todas as patentes do servidor"""
        try:
            updated_count = 0
            error_count = 0
            
            # Busca todos os membros com dados PUBG
            data = self.storage.load_data()
            
            for member in guild.members:
                if member.bot:
                    continue
                
                user_id = str(member.id)
                if user_id in data.get("users", {}):
                    user_data = data["users"][user_id]
                    pubg_data = user_data.get("pubg_stats", {})
                    
                    if pubg_data:
                        # Calcula pontos PUBG baseado nas stats
                        pubg_points = self._calculate_pubg_points(pubg_data)
                        
                        result = await self.update_member_rank_role(member, pubg_points)
                        if result["success"]:
                            updated_count += 1
                        else:
                            error_count += 1
            
            return {
                "success": True,
                "updated": updated_count,
                "errors": error_count
            }
            
        except Exception as e:
            logger.error(f"Erro na atualização em massa: {e}")
            return {"success": False, "reason": str(e)}
    
    def _calculate_pubg_points(self, pubg_data: Dict[str, Any]) -> int:
        """Calcula pontos PUBG baseado nas estatísticas"""
        try:
            # Pesos para diferentes métricas (baseado na config existente)
            weights = {
                "kd_ratio": 0.3,
                "win_rate": 0.25,
                "avg_damage": 0.2,
                "total_wins": 0.15,
                "survival_time": 0.1
            }
            
            # Extrai métricas
            kd = pubg_data.get("kd_ratio", 0)
            win_rate = pubg_data.get("win_rate", 0)
            avg_damage = pubg_data.get("avg_damage", 0)
            total_wins = pubg_data.get("total_wins", 0)
            survival_time = pubg_data.get("avg_survival_time", 0)
            
            # Normaliza valores para escala de pontos
            normalized_kd = min(kd * 1000, 3000)  # KD até 3.0 = 3000 pontos
            normalized_wr = win_rate * 2000  # Win rate 100% = 2000 pontos
            normalized_dmg = min(avg_damage * 5, 3000)  # 600 damage = 3000 pontos
            normalized_wins = min(total_wins * 10, 2000)  # 200 wins = 2000 pontos
            normalized_survival = min(survival_time / 60 * 100, 1000)  # 10min = 1000 pontos
            
            # Calcula pontuação final
            total_points = (
                normalized_kd * weights["kd_ratio"] +
                normalized_wr * weights["win_rate"] +
                normalized_dmg * weights["avg_damage"] +
                normalized_wins * weights["total_wins"] +
                normalized_survival * weights["survival_time"]
            )
            
            return int(total_points)
            
        except Exception as e:
            logger.error(f"Erro ao calcular pontos PUBG: {e}")
            return 0
    
    async def setup_rank_roles_command(self, ctx):
        """Comando para configurar cargos de patente"""
        try:
            embed = discord.Embed(
                title="🎖️ Sistema de Cargos PUBG",
                description="Configuração do sistema de cargos automáticos baseado nas patentes do PUBG",
                color=0x00ff00
            )
            
            # Lista todas as patentes
            rank_list = []
            for rank in PubgRankTier:
                rank_data = rank.value
                rank_list.append(f"{rank_data['emoji']} {rank_data['name']} ({rank_data['min_points']}-{rank_data['max_points']} pts)")
            
            embed.add_field(
                name="Patentes Disponíveis",
                value="\n".join(rank_list[:15]),  # Primeiras 15
                inline=False
            )
            
            if len(rank_list) > 15:
                embed.add_field(
                    name="Patentes Superiores",
                    value="\n".join(rank_list[15:]),
                    inline=False
                )
            
            embed.add_field(
                name="Status",
                value=f"{'✅ Ativo' if self.config['enabled'] else '❌ Desativo'}",
                inline=True
            )
            
            embed.add_field(
                name="Atribuição Automática",
                value=f"{'✅ Sim' if self.config['auto_assign'] else '❌ Não'}",
                inline=True
            )
            
            embed.set_footer(text="Use /pubg_ranks update para atualizar todos os cargos")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro no comando setup_rank_roles: {e}")
            await ctx.send("❌ Erro ao exibir configurações dos cargos PUBG.")