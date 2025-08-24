import discord
import logging
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger('HawkBot.BadgeSystem')

class BadgeType(Enum):
    """Tipos de emblemas especiais disponíveis"""
    
    # Emblemas de Combat
    FIRST_BLOOD = {
        "name": "First Blood",
        "emoji": "🩸",
        "color": 0xFF0000,
        "description": "Primeira eliminação da partida",
        "rarity": "comum",
        "category": "combat",
        "requirements": {
            "first_kills": 50
        }
    }
    
    CLUTCH_MASTER = {
        "name": "Clutch Master",
        "emoji": "🎯",
        "color": 0xFF4500,
        "description": "Especialista em situações 1vX",
        "rarity": "raro",
        "category": "combat",
        "requirements": {
            "clutch_wins": 25
        }
    }
    
    SNIPER_ELITE = {
        "name": "Sniper Elite",
        "emoji": "🎯",
        "color": 0x00FF00,
        "description": "Mestre dos tiros de longa distância",
        "rarity": "épico",
        "category": "combat",
        "requirements": {
            "headshot_ratio": 0.4,
            "long_range_kills": 100
        }
    }
    
    RAMPAGE = {
        "name": "Rampage",
        "emoji": "💀",
        "color": 0x8B0000,
        "description": "Eliminações múltiplas consecutivas",
        "rarity": "lendário",
        "category": "combat",
        "requirements": {
            "multi_kills": 15,
            "max_kill_streak": 8
        }
    }
    
    # Emblemas de Survival
    SURVIVOR_KING = {
        "name": "Survivor King",
        "emoji": "👑",
        "color": 0xFFD700,
        "description": "Especialista em sobrevivência",
        "rarity": "épico",
        "category": "survival",
        "requirements": {
            "avg_survival_time": 1200,  # 20 minutos
            "top_10_ratio": 0.6
        }
    }
    
    CHICKEN_HUNTER = {
        "name": "Chicken Hunter",
        "emoji": "🐔",
        "color": 0xFFA500,
        "description": "Colecionador de Chicken Dinners",
        "rarity": "raro",
        "category": "survival",
        "requirements": {
            "wins": 100,
            "win_ratio": 0.15
        }
    }
    
    GHOST_WALKER = {
        "name": "Ghost Walker",
        "emoji": "👻",
        "color": 0x9370DB,
        "description": "Mestre da furtividade",
        "rarity": "épico",
        "category": "survival",
        "requirements": {
            "stealth_wins": 20,  # Vitórias com poucos kills
            "avg_damage_per_match": 300
        }
    }
    
    # Emblemas de Support
    TEAM_PLAYER = {
        "name": "Team Player",
        "emoji": "🤝",
        "color": 0x00CED1,
        "description": "Jogador de equipe exemplar",
        "rarity": "comum",
        "category": "support",
        "requirements": {
            "revives": 200,
            "assists": 500
        }
    }
    
    MEDIC = {
        "name": "Medic",
        "emoji": "⚕️",
        "color": 0xFF69B4,
        "description": "Especialista em suporte médico",
        "rarity": "raro",
        "category": "support",
        "requirements": {
            "heals": 1000,
            "revives": 300
        }
    }
    
    # Emblemas de Achievement
    VETERAN = {
        "name": "Veteran",
        "emoji": "🎖️",
        "color": 0x8B4513,
        "description": "Jogador veterano experiente",
        "rarity": "lendário",
        "category": "achievement",
        "requirements": {
            "matches_played": 1000,
            "days_active": 365
        }
    }
    
    PERFECTIONIST = {
        "name": "Perfectionist",
        "emoji": "✨",
        "color": 0xFFFFFF,
        "description": "Busca pela perfeição",
        "rarity": "mítico",
        "category": "achievement",
        "requirements": {
            "perfect_matches": 10,  # Matches com 100% accuracy
            "flawless_wins": 5     # Vitórias sem tomar dano
        }
    }
    
    # Emblemas Especiais
    TOURNAMENT_CHAMPION = {
        "name": "Tournament Champion",
        "emoji": "🏆",
        "color": 0xFFD700,
        "description": "Campeão de torneios",
        "rarity": "lendário",
        "category": "special",
        "requirements": {
            "tournament_wins": 3
        }
    }
    
    COMMUNITY_HERO = {
        "name": "Community Hero",
        "emoji": "🌟",
        "color": 0x00FF7F,
        "description": "Herói da comunidade",
        "rarity": "mítico",
        "category": "special",
        "requirements": {
            "community_points": 10000,
            "helped_members": 100
        }
    }
    
    # Novos Badges de Combate Avançado
    HEADHUNTER = {
        "name": "Headhunter",
        "emoji": "🎯",
        "color": 0xFF6B35,
        "description": "Especialista em headshots",
        "rarity": "raro",
        "category": "combat",
        "requirements": {
            "headshot_ratio": 0.25,
            "headshots": 500
        }
    }
    
    SPRAY_MASTER = {
        "name": "Spray Master",
        "emoji": "💥",
        "color": 0xFF1744,
        "description": "Mestre do spray control",
        "rarity": "épico",
        "category": "combat",
        "requirements": {
            "spray_kills": 200,
            "close_range_accuracy": 0.6
        }
    }
    
    DEMOLITION_EXPERT = {
        "name": "Demolition Expert",
        "emoji": "💣",
        "color": 0xFF5722,
        "description": "Especialista em explosivos",
        "rarity": "raro",
        "category": "combat",
        "requirements": {
            "grenade_kills": 50,
            "explosive_damage": 10000
        }
    }
    
    BERSERKER = {
        "name": "Berserker",
        "emoji": "⚔️",
        "color": 0x8B0000,
        "description": "Fúria incontrolável em combate",
        "rarity": "lendário",
        "category": "combat",
        "requirements": {
            "kill_streak_max": 15,
            "aggressive_kills": 300
        }
    }
    
    SILENT_ASSASSIN = {
        "name": "Silent Assassin",
        "emoji": "🗡️",
        "color": 0x2E2E2E,
        "description": "Eliminações silenciosas e precisas",
        "rarity": "épico",
        "category": "combat",
        "requirements": {
            "stealth_kills": 100,
            "suppressed_weapon_kills": 200
        }
    }
    
    # Badges de Armas Específicas
    RIFLE_EXPERT = {
        "name": "Rifle Expert",
        "emoji": "🔫",
        "color": 0x4CAF50,
        "description": "Mestre dos rifles de assalto",
        "rarity": "raro",
        "category": "weapons",
        "requirements": {
            "ar_kills": 1000,
            "ar_accuracy": 0.3
        }
    }
    
    SNIPER_GOD = {
        "name": "Sniper God",
        "emoji": "🎯",
        "color": 0x1976D2,
        "description": "Divindade dos rifles de precisão",
        "rarity": "mítico",
        "category": "weapons",
        "requirements": {
            "sniper_kills": 500,
            "long_range_headshots": 200,
            "sniper_accuracy": 0.7
        }
    }
    
    SMG_RUSHER = {
        "name": "SMG Rusher",
        "emoji": "🏃",
        "color": 0xFF9800,
        "description": "Velocidade e agressividade com SMGs",
        "rarity": "comum",
        "category": "weapons",
        "requirements": {
            "smg_kills": 800,
            "close_combat_wins": 150
        }
    }
    
    SHOTGUN_SHERIFF = {
        "name": "Shotgun Sheriff",
        "emoji": "🤠",
        "color": 0x795548,
        "description": "Lei e ordem com escopetas",
        "rarity": "raro",
        "category": "weapons",
        "requirements": {
            "shotgun_kills": 300,
            "close_range_eliminations": 200
        }
    }
    
    PISTOL_VIRTUOSO = {
        "name": "Pistol Virtuoso",
        "emoji": "🔫",
        "color": 0x607D8B,
        "description": "Artista das pistolas",
        "rarity": "épico",
        "category": "weapons",
        "requirements": {
            "pistol_kills": 200,
            "pistol_headshots": 100
        }
    }
    
    # Badges de Sobrevivência Avançada
    ZONE_MASTER = {
        "name": "Zone Master",
        "emoji": "🌪️",
        "color": 0x9C27B0,
        "description": "Mestre da rotação de zona",
        "rarity": "raro",
        "category": "survival",
        "requirements": {
            "zone_damage_avoided": 50000,
            "perfect_rotations": 100
        }
    }
    
    LOOT_GOBLIN = {
        "name": "Loot Goblin",
        "emoji": "👹",
        "color": 0x4CAF50,
        "description": "Colecionador compulsivo de loot",
        "rarity": "comum",
        "category": "survival",
        "requirements": {
            "items_looted": 10000,
            "rare_items_found": 500
        }
    }
    
    VEHICLE_MASTER = {
        "name": "Vehicle Master",
        "emoji": "🚗",
        "color": 0xFF5722,
        "description": "Especialista em veículos",
        "rarity": "raro",
        "category": "survival",
        "requirements": {
            "vehicle_distance": 100000,
            "vehicle_kills": 25
        }
    }
    
    CAMPER_KING = {
        "name": "Camper King",
        "emoji": "🏕️",
        "color": 0x8BC34A,
        "description": "Mestre da paciência e posicionamento",
        "rarity": "raro",
        "category": "survival",
        "requirements": {
            "camping_wins": 50,
            "stationary_kills": 200
        }
    }
    
    BRIDGE_TROLL = {
        "name": "Bridge Troll",
        "emoji": "🌉",
        "color": 0x795548,
        "description": "Guardião das pontes",
        "rarity": "épico",
        "category": "survival",
        "requirements": {
            "bridge_kills": 100,
            "bridge_control_time": 3600
        }
    }
    
    # Badges de Suporte Avançado
    GUARDIAN_ANGEL = {
        "name": "Guardian Angel",
        "emoji": "👼",
        "color": 0xFFFFFF,
        "description": "Protetor incansável da equipe",
        "rarity": "lendário",
        "category": "support",
        "requirements": {
            "teammates_saved": 200,
            "damage_blocked": 50000
        }
    }
    
    SUPPLY_SERGEANT = {
        "name": "Supply Sergeant",
        "emoji": "📦",
        "color": 0x607D8B,
        "description": "Especialista em suprimentos",
        "rarity": "raro",
        "category": "support",
        "requirements": {
            "items_shared": 1000,
            "ammo_shared": 5000
        }
    }
    
    INTEL_OFFICER = {
        "name": "Intel Officer",
        "emoji": "🔍",
        "color": 0x3F51B5,
        "description": "Especialista em reconhecimento",
        "rarity": "épico",
        "category": "support",
        "requirements": {
            "enemies_spotted": 1000,
            "recon_assists": 300
        }
    }
    
    SMOKE_TACTICIAN = {
        "name": "Smoke Tactician",
        "emoji": "💨",
        "color": 0x9E9E9E,
        "description": "Mestre das granadas de fumaça",
        "rarity": "raro",
        "category": "support",
        "requirements": {
            "smoke_grenades_used": 500,
            "smoke_assists": 200
        }
    }
    
    # Badges de Progressão
    ROOKIE = {
        "name": "Rookie",
        "emoji": "🥉",
        "color": 0xCD7F32,
        "description": "Primeiro passo na jornada",
        "rarity": "comum",
        "category": "progression",
        "requirements": {
            "matches_played": 10,
            "days_active": 7
        }
    }
    
    REGULAR = {
        "name": "Regular",
        "emoji": "🥈",
        "color": 0xC0C0C0,
        "description": "Jogador regular do servidor",
        "rarity": "comum",
        "category": "progression",
        "requirements": {
            "matches_played": 100,
            "days_active": 30
        }
    }
    
    DEDICATED = {
        "name": "Dedicated",
        "emoji": "🥇",
        "color": 0xFFD700,
        "description": "Jogador dedicado e consistente",
        "rarity": "raro",
        "category": "progression",
        "requirements": {
            "matches_played": 500,
            "days_active": 90
        }
    }
    
    LEGEND = {
        "name": "Legend",
        "emoji": "👑",
        "color": 0x9C27B0,
        "description": "Lenda viva do servidor",
        "rarity": "lendário",
        "category": "progression",
        "requirements": {
            "matches_played": 2000,
            "days_active": 365
        }
    }
    
    # Badges Sazonais
    SEASON_WARRIOR = {
        "name": "Season Warrior",
        "emoji": "⚔️",
        "color": 0xFF6B35,
        "description": "Guerreiro da temporada atual",
        "rarity": "épico",
        "category": "seasonal",
        "requirements": {
            "season_matches": 200,
            "season_wins": 20
        }
    }
    
    EARLY_BIRD = {
        "name": "Early Bird",
        "emoji": "🐦",
        "color": 0x2196F3,
        "description": "Primeiro a experimentar novos recursos",
        "rarity": "especial",
        "category": "seasonal",
        "requirements": {
            "beta_participation": 1,
            "early_adoption": 1
        }
    }
    
    ANNIVERSARY_VETERAN = {
        "name": "Anniversary Veteran",
        "emoji": "🎂",
        "color": 0xE91E63,
        "description": "Presente desde o aniversário do servidor",
        "rarity": "mítico",
        "category": "seasonal",
        "requirements": {
            "anniversary_participation": 1,
            "loyalty_points": 1000
        }
    }

class BadgeRarity(Enum):
    """Raridades dos emblemas"""
    COMUM = {"name": "Comum", "color": 0x808080, "weight": 1}
    RARO = {"name": "Raro", "color": 0x0080FF, "weight": 2}
    ÉPICO = {"name": "Épico", "color": 0x8000FF, "weight": 3}
    LENDÁRIO = {"name": "Lendário", "color": 0xFF8000, "weight": 4}
    MÍTICO = {"name": "Mítico", "color": 0xFF0080, "weight": 5}

class BadgeSystem:
    """Sistema de emblemas/badges personalizados"""
    
    def __init__(self, bot, storage, pubg_api, dual_ranking):
        self.bot = bot
        self.storage = storage
        self.pubg_api = pubg_api
        self.dual_ranking = dual_ranking
        self.config_file = "badge_system_config.json"
        self.config = self._load_config()
        self.user_badges = self._load_user_badges()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do sistema de emblemas"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config de emblemas: {e}")
        
        # Configuração padrão
        return {
            "enabled": True,
            "auto_check": True,
            "announcement_channel": None,
            "announce_new_badges": True,
            "display_in_profile": True,
            "max_display_badges": 5,
            "check_interval_hours": 6,
            "rarity_multipliers": {
                "comum": 1.0,
                "raro": 1.5,
                "épico": 2.0,
                "lendário": 3.0,
                "mítico": 5.0
            }
        }
    
    def _save_config(self):
        """Salva configurações do sistema"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar config de emblemas: {e}")
    
    def _load_user_badges(self) -> Dict[str, Dict[str, Any]]:
        """Carrega emblemas dos usuários"""
        try:
            badges_file = "user_badges.json"
            if os.path.exists(badges_file):
                with open(badges_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar emblemas dos usuários: {e}")
        return {}
    
    def _save_user_badges(self):
        """Salva emblemas dos usuários"""
        try:
            badges_file = "user_badges.json"
            with open(badges_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_badges, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar emblemas dos usuários: {e}")
    
    def get_badge_by_name(self, badge_name: str) -> Optional[Dict[str, Any]]:
        """Obtém dados de um emblema pelo nome"""
        for badge in BadgeType:
            if badge.value["name"].lower() == badge_name.lower():
                return badge.value
        return None
    
    def get_badges_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obtém todos os emblemas de uma categoria"""
        badges = []
        for badge in BadgeType:
            if badge.value["category"] == category:
                badges.append(badge.value)
        return badges
    
    def get_badges_by_rarity(self, rarity: str) -> List[Dict[str, Any]]:
        """Obtém todos os emblemas de uma raridade"""
        badges = []
        for badge in BadgeType:
            if badge.value["rarity"] == rarity:
                badges.append(badge.value)
        return badges
    
    def get_all_badges(self) -> List[Dict[str, Any]]:
        """Obtém todos os emblemas disponíveis"""
        badges = []
        for badge in BadgeType:
            badges.append(badge.value)
        return badges
    
    async def check_user_badges(self, user_id: str, pubg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verifica quais emblemas um usuário deve receber"""
        if not self.config.get("enabled", True):
            return []
        
        new_badges = []
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_badges:
            self.user_badges[user_id_str] = {
                "badges": [],
                "last_check": datetime.now().isoformat(),
                "total_score": 0
            }
        
        current_badges = [b["name"] for b in self.user_badges[user_id_str]["badges"]]
        
        # Verifica cada tipo de emblema
        for badge_type in BadgeType:
            badge_data = badge_type.value
            badge_name = badge_data["name"]
            
            # Pula se já possui o emblema
            if badge_name in current_badges:
                continue
            
            # Verifica requisitos
            if self._check_badge_requirements(badge_data, pubg_data):
                badge_info = {
                    "name": badge_name,
                    "emoji": badge_data["emoji"],
                    "color": badge_data["color"],
                    "description": badge_data["description"],
                    "rarity": badge_data["rarity"],
                    "category": badge_data["category"],
                    "earned_date": datetime.now().isoformat()
                }
                
                self.user_badges[user_id_str]["badges"].append(badge_info)
                new_badges.append(badge_info)
        
        # Atualiza pontuação total
        self._update_user_badge_score(user_id_str)
        
        # Salva alterações
        if new_badges:
            self._save_user_badges()
        
        return new_badges
    
    def _check_badge_requirements(self, badge_data: Dict[str, Any], pubg_data: Dict[str, Any]) -> bool:
        """Verifica se os requisitos de um emblema foram atendidos"""
        requirements = badge_data.get("requirements", {})
        
        for req_key, req_value in requirements.items():
            if req_key == "first_kills":
                if pubg_data.get("first_kills", 0) < req_value:
                    return False
            elif req_key == "clutch_wins":
                if pubg_data.get("clutch_wins", 0) < req_value:
                    return False
            elif req_key == "headshot_ratio":
                if pubg_data.get("headshot_ratio", 0) < req_value:
                    return False
            elif req_key == "long_range_kills":
                if pubg_data.get("long_range_kills", 0) < req_value:
                    return False
            elif req_key == "multi_kills":
                if pubg_data.get("multi_kills", 0) < req_value:
                    return False
            elif req_key == "max_kill_streak":
                if pubg_data.get("max_kill_streak", 0) < req_value:
                    return False
            elif req_key == "avg_survival_time":
                if pubg_data.get("avg_survival_time", 0) < req_value:
                    return False
            elif req_key == "top_10_ratio":
                if pubg_data.get("top_10_ratio", 0) < req_value:
                    return False
            elif req_key == "wins":
                if pubg_data.get("wins", 0) < req_value:
                    return False
            elif req_key == "win_ratio":
                if pubg_data.get("win_ratio", 0) < req_value:
                    return False
            elif req_key == "stealth_wins":
                if pubg_data.get("stealth_wins", 0) < req_value:
                    return False
            elif req_key == "avg_damage_per_match":
                if pubg_data.get("avg_damage_per_match", 0) < req_value:
                    return False
            elif req_key == "revives":
                if pubg_data.get("revives", 0) < req_value:
                    return False
            elif req_key == "assists":
                if pubg_data.get("assists", 0) < req_value:
                    return False
            elif req_key == "heals":
                if pubg_data.get("heals", 0) < req_value:
                    return False
            elif req_key == "matches_played":
                if pubg_data.get("matches_played", 0) < req_value:
                    return False
            elif req_key == "days_active":
                if pubg_data.get("days_active", 0) < req_value:
                    return False
            elif req_key == "perfect_matches":
                if pubg_data.get("perfect_matches", 0) < req_value:
                    return False
            elif req_key == "flawless_wins":
                if pubg_data.get("flawless_wins", 0) < req_value:
                    return False
            elif req_key == "tournament_wins":
                if pubg_data.get("tournament_wins", 0) < req_value:
                    return False
            elif req_key == "community_points":
                if pubg_data.get("community_points", 0) < req_value:
                    return False
            elif req_key == "helped_members":
                if pubg_data.get("helped_members", 0) < req_value:
                    return False
        
        return True
    
    def _update_user_badge_score(self, user_id: str):
        """Atualiza a pontuação total de emblemas do usuário"""
        total_score = 0
        multipliers = self.config.get("rarity_multipliers", {})
        
        for badge in self.user_badges[user_id]["badges"]:
            rarity = badge["rarity"]
            multiplier = multipliers.get(rarity, 1.0)
            total_score += int(100 * multiplier)
        
        self.user_badges[user_id]["total_score"] = total_score
    
    def get_user_badges(self, user_id: str) -> Dict[str, Any]:
        """Obtém todos os emblemas de um usuário"""
        user_id_str = str(user_id)
        return self.user_badges.get(user_id_str, {
            "badges": [],
            "last_check": None,
            "total_score": 0
        })
    
    def get_user_display_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtém os emblemas para exibição (limitado)"""
        user_badges = self.get_user_badges(user_id)
        badges = user_badges["badges"]
        
        # Ordena por raridade e data
        rarity_order = {"mítico": 5, "lendário": 4, "épico": 3, "raro": 2, "comum": 1}
        badges.sort(key=lambda x: (rarity_order.get(x["rarity"], 0), x["earned_date"]), reverse=True)
        
        max_display = self.config.get("max_display_badges", 5)
        return badges[:max_display]
    
    async def announce_new_badge(self, member: discord.Member, badge: Dict[str, Any]):
        """Anuncia um novo emblema obtido"""
        if not self.config.get("announce_new_badges", True):
            return
        
        channel_id = self.config.get("announcement_channel")
        if not channel_id:
            return
        
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
            
            embed = discord.Embed(
                title="🎉 Novo Emblema Conquistado!",
                description=f"{member.mention} conquistou o emblema **{badge['emoji']} {badge['name']}**!",
                color=badge["color"]
            )
            
            embed.add_field(
                name="Descrição",
                value=badge["description"],
                inline=False
            )
            
            embed.add_field(
                name="Raridade",
                value=badge["rarity"].title(),
                inline=True
            )
            
            embed.add_field(
                name="Categoria",
                value=badge["category"].title(),
                inline=True
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.now()
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao anunciar novo emblema: {e}")
    
    async def bulk_check_badges(self, guild: discord.Guild) -> Dict[str, Any]:
        """Verifica emblemas para todos os membros do servidor"""
        if not self.config.get("enabled", True):
            return {"success": False, "message": "Sistema de emblemas desabilitado"}
        
        try:
            updated_count = 0
            new_badges_count = 0
            
            for member in guild.members:
                if member.bot:
                    continue
                
                # Obtém dados PUBG do usuário
                user_data = self.storage.get_user_data(str(member.id))
                if not user_data or not user_data.get("pubg_name"):
                    continue
                
                try:
                    pubg_data = await self.pubg_api.get_player_stats(user_data["pubg_name"])
                    if pubg_data:
                        new_badges = await self.check_user_badges(str(member.id), pubg_data)
                        if new_badges:
                            updated_count += 1
                            new_badges_count += len(new_badges)
                            
                            # Anuncia novos emblemas
                            for badge in new_badges:
                                await self.announce_new_badge(member, badge)
                                await asyncio.sleep(1)  # Evita spam
                        
                except Exception as e:
                    logger.error(f"Erro ao verificar emblemas para {member.display_name}: {e}")
                    continue
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            return {
                "success": True,
                "updated_users": updated_count,
                "new_badges": new_badges_count,
                "message": f"Verificação concluída: {updated_count} usuários atualizados, {new_badges_count} novos emblemas"
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação em massa de emblemas: {e}")
            return {"success": False, "message": f"Erro: {str(e)}"}
    
    def get_leaderboard(self, guild: discord.Guild, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtém ranking de emblemas"""
        leaderboard = []
        
        for member in guild.members:
            if member.bot:
                continue
            
            user_badges = self.get_user_badges(str(member.id))
            if user_badges["badges"]:
                leaderboard.append({
                    "user_id": str(member.id),
                    "display_name": member.display_name,
                    "badge_count": len(user_badges["badges"]),
                    "total_score": user_badges["total_score"],
                    "top_badges": self.get_user_display_badges(str(member.id))[:3]
                })
        
        # Ordena por pontuação total e quantidade de emblemas
        leaderboard.sort(key=lambda x: (x["total_score"], x["badge_count"]), reverse=True)
        
        return leaderboard[:limit]
    
    async def enable_system(self, guild_id: int) -> bool:
        """Ativa o sistema de emblemas"""
        if self.config.get("enabled", True):
            return False  # Já estava ativo
        
        self.config["enabled"] = True
        self._save_config()
        logger.info(f"Sistema de emblemas ativado para guild {guild_id}")
        return True
    
    async def disable_system(self, guild_id: int) -> bool:
        """Desativa o sistema de emblemas"""
        self.config["enabled"] = False
        self._save_config()
        logger.info(f"Sistema de emblemas desativado para guild {guild_id}")
        return True
    
    async def get_config(self, guild_id: int) -> Dict[str, Any]:
        """Obtém configuração atual do sistema"""
        return self.config.copy()
    
    async def check_all_members(self, guild: discord.Guild) -> int:
        """Verifica emblemas para todos os membros do servidor"""
        result = await self.bulk_check_badges(guild)
        return result.get("updated_users", 0)
    
    async def set_announcement_channel(self, guild_id: int, channel_id: int) -> bool:
        """Define canal de anúncios de emblemas"""
        self.config["announcement_channel"] = channel_id
        self._save_config()
        logger.info(f"Canal de anúncios de emblemas definido: {channel_id}")
        return True
    
    async def reset_all_badges(self, guild_id: int) -> bool:
        """Reset todos os emblemas do servidor"""
        self.user_badges = {}
        self._save_user_badges()
        logger.warning(f"Todos os emblemas foram resetados para guild {guild_id}")
        return True