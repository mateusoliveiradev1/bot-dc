import discord
import logging
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

class SeasonStatus(Enum):
    """Status da temporada"""
    ACTIVE = "active"
    ENDED = "ended"
    UPCOMING = "upcoming"
    PREPARING = "preparing"

class RewardType(Enum):
    """Tipos de recompensas de temporada"""
    ROLE = "role"
    BADGE = "badge"
    TITLE = "title"
    COINS = "coins"
    EXCLUSIVE_EMOJI = "exclusive_emoji"
    PROFILE_DECORATION = "profile_decoration"

class SeasonReward:
    """Representa uma recompensa de temporada"""
    def __init__(self, reward_id: str, name: str, description: str, 
                 reward_type: RewardType, value: Any, rarity: str = "common",
                 emoji: str = "🏆", requirements: Dict = None):
        self.reward_id = reward_id
        self.name = name
        self.description = description
        self.reward_type = reward_type
        self.value = value
        self.rarity = rarity
        self.emoji = emoji
        self.requirements = requirements or {}
    
    def to_dict(self) -> Dict:
        return {
            "reward_id": self.reward_id,
            "name": self.name,
            "description": self.description,
            "reward_type": self.reward_type.value,
            "value": self.value,
            "rarity": self.rarity,
            "emoji": self.emoji,
            "requirements": self.requirements
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SeasonReward':
        return cls(
            reward_id=data["reward_id"],
            name=data["name"],
            description=data["description"],
            reward_type=RewardType(data["reward_type"]),
            value=data["value"],
            rarity=data.get("rarity", "common"),
            emoji=data.get("emoji", "🏆"),
            requirements=data.get("requirements", {})
        )

class Season:
    """Representa uma temporada"""
    def __init__(self, season_id: str, name: str, description: str,
                 start_date: datetime, end_date: datetime, 
                 rewards: List[SeasonReward] = None, theme: str = "default"):
        self.season_id = season_id
        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.rewards = rewards or []
        self.theme = theme
        self.status = self._calculate_status()
    
    def _calculate_status(self) -> SeasonStatus:
        now = datetime.now()
        if now < self.start_date:
            return SeasonStatus.UPCOMING
        elif now > self.end_date:
            return SeasonStatus.ENDED
        else:
            return SeasonStatus.ACTIVE
    
    def get_duration_days(self) -> int:
        return (self.end_date - self.start_date).days
    
    def get_remaining_days(self) -> int:
        if self.status == SeasonStatus.ACTIVE:
            return max(0, (self.end_date - datetime.now()).days)
        return 0
    
    def to_dict(self) -> Dict:
        return {
            "season_id": self.season_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "rewards": [reward.to_dict() for reward in self.rewards],
            "theme": self.theme
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Season':
        rewards = [SeasonReward.from_dict(r) for r in data.get("rewards", [])]
        return cls(
            season_id=data["season_id"],
            name=data["name"],
            description=data["description"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            rewards=rewards,
            theme=data.get("theme", "default")
        )

class SeasonSystem:
    """Sistema de temporadas com reset periódico e recompensas"""
    
    def __init__(self, bot, storage, dual_ranking_system, badge_system=None):
        self.bot = bot
        self.storage = storage
        self.dual_ranking_system = dual_ranking_system
        self.badge_system = badge_system
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.config_file = "season_system_config.json"
        self.config = self._load_config()
        
        # Dados das temporadas
        self.seasons: Dict[str, Season] = {}
        self.current_season: Optional[Season] = None
        self.season_rankings: Dict[str, Dict] = {}  # season_id -> rankings
        self.user_season_data: Dict[str, Dict] = {}  # user_id -> season data
        
        self._load_seasons()
        self._load_season_data()
        
    def _load_config(self) -> Dict:
        """Carrega configurações do sistema de temporadas"""
        default_config = {
            "enabled": True,
            "auto_create_seasons": True,
            "season_duration_days": 90,  # 3 meses
            "announcement_channel_id": None,
            "reset_rankings_on_season_end": True,
            "preserve_season_history": True,
            "max_seasons_history": 10,
            "reward_distribution": {
                "top_1_percent": ["legendary_role", "exclusive_badge", "1000_coins"],
                "top_5_percent": ["epic_role", "season_badge", "500_coins"],
                "top_10_percent": ["rare_role", "participation_badge", "250_coins"],
                "top_25_percent": ["common_role", "100_coins"],
                "participation": ["participation_title", "50_coins"]
            },
            "themes": {
                "default": {"color": 0x00ff00, "emoji": "🏆"},
                "winter": {"color": 0x87ceeb, "emoji": "❄️"},
                "summer": {"color": 0xffd700, "emoji": "☀️"},
                "autumn": {"color": 0xff8c00, "emoji": "🍂"},
                "spring": {"color": 0x98fb98, "emoji": "🌸"}
            },
            "notifications": {
                "season_start": True,
                "season_end": True,
                "rewards_distributed": True,
                "new_season_announcement": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"Erro ao carregar configuração de temporadas: {e}")
        
        return default_config
    
    def _save_config(self):
        """Salva configurações do sistema de temporadas"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração de temporadas: {e}")
    
    def _load_seasons(self):
        """Carrega dados das temporadas"""
        seasons_data = self.storage.get_setting("seasons", {})
        
        for season_id, season_data in seasons_data.items():
            try:
                season = Season.from_dict(season_data)
                self.seasons[season_id] = season
                
                if season.status == SeasonStatus.ACTIVE:
                    self.current_season = season
            except Exception as e:
                self.logger.error(f"Erro ao carregar temporada {season_id}: {e}")
    
    def _save_seasons(self):
        """Salva temporadas no storage"""
        seasons_data = {}
        for season_id, season in self.seasons.items():
            seasons_data[season_id] = season.to_dict()
        
        self.storage.set_setting("seasons", seasons_data)
    
    def _load_season_data(self):
        """Carrega dados de usuários por temporada"""
        self.season_rankings = self.storage.get_setting("season_rankings", {})
        self.user_season_data = self.storage.get_setting("user_season_data", {})
    
    def _save_season_data(self):
        """Salva dados de usuários por temporada"""
        self.storage.set_setting("season_rankings", self.season_rankings)
        self.storage.set_setting("user_season_data", self.user_season_data)
    
    def create_season(self, name: str, description: str, duration_days: int = None,
                     theme: str = "default", custom_rewards: List[Dict] = None) -> Season:
        """Cria uma nova temporada"""
        if duration_days is None:
            duration_days = self.config["season_duration_days"]
        
        # Gerar ID único
        season_id = f"season_{len(self.seasons) + 1}_{datetime.now().strftime('%Y%m')}"
        
        # Definir datas
        start_date = datetime.now()
        if self.current_season and self.current_season.status == SeasonStatus.ACTIVE:
            start_date = self.current_season.end_date + timedelta(days=1)
        
        end_date = start_date + timedelta(days=duration_days)
        
        # Criar recompensas padrão
        rewards = self._create_default_rewards(theme)
        
        # Adicionar recompensas customizadas
        if custom_rewards:
            for reward_data in custom_rewards:
                reward = SeasonReward.from_dict(reward_data)
                rewards.append(reward)
        
        # Criar temporada
        season = Season(
            season_id=season_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            rewards=rewards,
            theme=theme
        )
        
        self.seasons[season_id] = season
        self._save_seasons()
        
        self.logger.info(f"Nova temporada criada: {name} ({season_id})")
        return season
    
    def _create_default_rewards(self, theme: str) -> List[SeasonReward]:
        """Cria recompensas padrão para uma temporada"""
        theme_data = self.config["themes"].get(theme, self.config["themes"]["default"])
        theme_emoji = theme_data["emoji"]
        
        rewards = [
            # Recompensas para top 1%
            SeasonReward(
                "legendary_champion", 
                f"Campeão Lendário {theme_emoji}",
                "Cargo exclusivo para o top 1% da temporada",
                RewardType.ROLE,
                {"name": f"🏆 Campeão {theme_emoji}", "color": 0xffd700},
                "legendary",
                "🏆",
                {"rank_percentile": 1}
            ),
            SeasonReward(
                "legend_badge",
                f"Emblema de Lenda {theme_emoji}",
                "Emblema exclusivo para campeões da temporada",
                RewardType.BADGE,
                "season_legend",
                "legendary",
                theme_emoji,
                {"rank_percentile": 1}
            ),
            # Recompensas para top 5%
            SeasonReward(
                "master_elite",
                f"Elite Master {theme_emoji}",
                "Cargo para o top 5% da temporada",
                RewardType.ROLE,
                {"name": f"⭐ Elite {theme_emoji}", "color": 0xff6b6b},
                "epic",
                "⭐",
                {"rank_percentile": 5}
            ),
            # Recompensas para top 10%
            SeasonReward(
                "veteran_player",
                f"Jogador Veterano {theme_emoji}",
                "Cargo para o top 10% da temporada",
                RewardType.ROLE,
                {"name": f"🎖️ Veterano {theme_emoji}", "color": 0x4ecdc4},
                "rare",
                "🎖️",
                {"rank_percentile": 10}
            ),
            # Recompensas para participação
            SeasonReward(
                "season_participant",
                f"Participante da Temporada {theme_emoji}",
                "Título para todos que participaram da temporada",
                RewardType.TITLE,
                f"Participante {theme_emoji}",
                "common",
                theme_emoji,
                {"games_played": 10}
            )
        ]
        
        return rewards
    
    async def start_season(self, season: Season) -> bool:
        """Inicia uma temporada"""
        try:
            if self.current_season and self.current_season.status == SeasonStatus.ACTIVE:
                await self.end_season(self.current_season)
            
            self.current_season = season
            season.status = SeasonStatus.ACTIVE
            
            # Resetar rankings se configurado
            if self.config["reset_rankings_on_season_end"]:
                await self._reset_rankings_for_new_season(season.season_id)
            
            # Anunciar início da temporada
            if self.config["notifications"]["season_start"]:
                await self._announce_season_start(season)
            
            self._save_seasons()
            self.logger.info(f"Temporada iniciada: {season.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar temporada: {e}")
            return False
    
    async def end_season(self, season: Season) -> bool:
        """Finaliza uma temporada e distribui recompensas"""
        try:
            season.status = SeasonStatus.ENDED
            
            # Salvar rankings finais da temporada
            await self._save_season_final_rankings(season)
            
            # Distribuir recompensas
            await self._distribute_season_rewards(season)
            
            # Anunciar fim da temporada
            if self.config["notifications"]["season_end"]:
                await self._announce_season_end(season)
            
            if season == self.current_season:
                self.current_season = None
            
            self._save_seasons()
            self.logger.info(f"Temporada finalizada: {season.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar temporada: {e}")
            return False
    
    async def _reset_rankings_for_new_season(self, season_id: str):
        """Reseta rankings para nova temporada"""
        # Salvar rankings atuais como histórico da temporada anterior
        if self.current_season:
            await self._save_season_final_rankings(self.current_season)
        
        # Resetar rankings do sistema dual
        if hasattr(self.dual_ranking_system, 'reset_season_rankings'):
            await self.dual_ranking_system.reset_season_rankings()
        
        # Inicializar dados da nova temporada
        self.season_rankings[season_id] = {}
        self._save_season_data()
    
    async def _save_season_final_rankings(self, season: Season):
        """Salva rankings finais de uma temporada"""
        try:
            # Obter rankings atuais
            current_rankings = await self.dual_ranking_system.get_all_rankings()
            
            # Salvar no histórico da temporada
            self.season_rankings[season.season_id] = {
                "final_rankings": current_rankings,
                "end_date": season.end_date.isoformat(),
                "participants": len(current_rankings)
            }
            
            self._save_season_data()
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar rankings finais: {e}")
    
    async def _distribute_season_rewards(self, season: Season):
        """Distribui recompensas de fim de temporada"""
        try:
            if season.season_id not in self.season_rankings:
                self.logger.warning(f"Sem rankings para temporada {season.season_id}")
                return
            
            rankings = self.season_rankings[season.season_id]["final_rankings"]
            total_players = len(rankings)
            
            if total_players == 0:
                return
            
            # Ordenar jogadores por pontuação
            sorted_players = sorted(rankings.items(), 
                                  key=lambda x: x[1].get('total_score', 0), 
                                  reverse=True)
            
            rewards_given = []
            
            for reward in season.rewards:
                eligible_players = self._get_eligible_players_for_reward(
                    reward, sorted_players, total_players
                )
                
                for user_id in eligible_players:
                    success = await self._give_reward_to_user(user_id, reward, season)
                    if success:
                        rewards_given.append((user_id, reward))
            
            # Anunciar distribuição de recompensas
            if self.config["notifications"]["rewards_distributed"] and rewards_given:
                await self._announce_rewards_distribution(season, rewards_given)
            
        except Exception as e:
            self.logger.error(f"Erro ao distribuir recompensas: {e}")
    
    def _get_eligible_players_for_reward(self, reward: SeasonReward, 
                                       sorted_players: List, total_players: int) -> List[str]:
        """Determina quais jogadores são elegíveis para uma recompensa"""
        eligible = []
        requirements = reward.requirements
        
        if "rank_percentile" in requirements:
            percentile = requirements["rank_percentile"]
            max_players = max(1, int(total_players * percentile / 100))
            
            for i, (user_id, data) in enumerate(sorted_players[:max_players]):
                eligible.append(user_id)
        
        elif "games_played" in requirements:
            min_games = requirements["games_played"]
            
            for user_id, data in sorted_players:
                if data.get('games_played', 0) >= min_games:
                    eligible.append(user_id)
        
        else:
            # Sem requisitos específicos, todos são elegíveis
            eligible = [user_id for user_id, _ in sorted_players]
        
        return eligible
    
    async def _give_reward_to_user(self, user_id: str, reward: SeasonReward, season: Season) -> bool:
        """Dá uma recompensa específica para um usuário"""
        try:
            guild_id = str(self.bot.guilds[0].id) if self.bot.guilds else None
            if not guild_id:
                return False
            
            if reward.reward_type == RewardType.ROLE:
                return await self._give_role_reward(user_id, reward, guild_id)
            elif reward.reward_type == RewardType.BADGE:
                return await self._give_badge_reward(user_id, reward)
            elif reward.reward_type == RewardType.TITLE:
                return await self._give_title_reward(user_id, reward)
            elif reward.reward_type == RewardType.COINS:
                return await self._give_coins_reward(user_id, reward)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao dar recompensa {reward.name} para {user_id}: {e}")
            return False
    
    async def _give_role_reward(self, user_id: str, reward: SeasonReward, guild_id: str) -> bool:
        """Dá um cargo como recompensa"""
        try:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                return False
            
            member = guild.get_member(int(user_id))
            if not member:
                return False
            
            role_data = reward.value
            role_name = role_data["name"]
            role_color = role_data.get("color", 0x00ff00)
            
            # Procurar cargo existente ou criar novo
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = await guild.create_role(
                    name=role_name,
                    color=discord.Color(role_color),
                    reason=f"Recompensa de temporada: {reward.name}"
                )
            
            await member.add_roles(role, reason=f"Recompensa de temporada: {reward.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao dar cargo: {e}")
            return False
    
    async def _give_badge_reward(self, user_id: str, reward: SeasonReward) -> bool:
        """Dá um emblema como recompensa"""
        if not self.badge_system:
            return False
        
        try:
            # Adicionar emblema personalizado de temporada
            badge_data = {
                "badge_id": f"season_{reward.reward_id}",
                "name": reward.name,
                "description": reward.description,
                "emoji": reward.emoji,
                "rarity": reward.rarity,
                "category": "season",
                "earned_date": datetime.now().isoformat()
            }
            
            return await self.badge_system.award_custom_badge(user_id, badge_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao dar emblema: {e}")
            return False
    
    async def _give_title_reward(self, user_id: str, reward: SeasonReward) -> bool:
        """Dá um título como recompensa"""
        try:
            # Salvar título no perfil do usuário
            user_data = self.storage.get_user_data(user_id)
            if "season_titles" not in user_data:
                user_data["season_titles"] = []
            
            title_data = {
                "title": reward.value,
                "season_id": reward.reward_id,
                "earned_date": datetime.now().isoformat()
            }
            
            user_data["season_titles"].append(title_data)
            self.storage.set_user_data(user_id, user_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao dar título: {e}")
            return False
    
    async def _give_coins_reward(self, user_id: str, reward: SeasonReward) -> bool:
        """Dá moedas como recompensa"""
        try:
            coins = int(reward.value)
            user_data = self.storage.get_user_data(user_id)
            current_coins = user_data.get("coins", 0)
            user_data["coins"] = current_coins + coins
            self.storage.set_user_data(user_id, user_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao dar moedas: {e}")
            return False
    
    async def _announce_season_start(self, season: Season):
        """Anuncia o início de uma temporada"""
        if not self.config["announcement_channel_id"]:
            return
        
        try:
            channel = self.bot.get_channel(self.config["announcement_channel_id"])
            if not channel:
                return
            
            theme_data = self.config["themes"].get(season.theme, self.config["themes"]["default"])
            
            embed = discord.Embed(
                title=f"{theme_data['emoji']} Nova Temporada Iniciada!",
                description=f"**{season.name}**\n{season.description}",
                color=theme_data["color"]
            )
            
            embed.add_field(
                name="📅 Duração",
                value=f"{season.get_duration_days()} dias",
                inline=True
            )
            
            embed.add_field(
                name="🏁 Termina em",
                value=f"<t:{int(season.end_date.timestamp())}:R>",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Recompensas",
                value=f"{len(season.rewards)} recompensas disponíveis",
                inline=True
            )
            
            embed.set_footer(text="Boa sorte a todos os competidores!")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao anunciar início de temporada: {e}")
    
    async def _announce_season_end(self, season: Season):
        """Anuncia o fim de uma temporada"""
        if not self.config["announcement_channel_id"]:
            return
        
        try:
            channel = self.bot.get_channel(self.config["announcement_channel_id"])
            if not channel:
                return
            
            theme_data = self.config["themes"].get(season.theme, self.config["themes"]["default"])
            
            embed = discord.Embed(
                title=f"{theme_data['emoji']} Temporada Finalizada!",
                description=f"**{season.name}** chegou ao fim!\n{season.description}",
                color=theme_data["color"]
            )
            
            # Estatísticas da temporada
            if season.season_id in self.season_rankings:
                participants = self.season_rankings[season.season_id].get("participants", 0)
                embed.add_field(
                    name="👥 Participantes",
                    value=f"{participants} jogadores",
                    inline=True
                )
            
            embed.add_field(
                name="🏆 Recompensas",
                value="Sendo distribuídas agora!",
                inline=True
            )
            
            embed.set_footer(text="Obrigado a todos pela participação!")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao anunciar fim de temporada: {e}")
    
    async def _announce_rewards_distribution(self, season: Season, rewards_given: List):
        """Anuncia a distribuição de recompensas"""
        if not self.config["announcement_channel_id"]:
            return
        
        try:
            channel = self.bot.get_channel(self.config["announcement_channel_id"])
            if not channel:
                return
            
            theme_data = self.config["themes"].get(season.theme, self.config["themes"]["default"])
            
            embed = discord.Embed(
                title=f"{theme_data['emoji']} Recompensas Distribuídas!",
                description=f"As recompensas da temporada **{season.name}** foram distribuídas!",
                color=theme_data["color"]
            )
            
            # Contar recompensas por tipo
            reward_counts = {}
            for user_id, reward in rewards_given:
                reward_name = reward.name
                if reward_name not in reward_counts:
                    reward_counts[reward_name] = 0
                reward_counts[reward_name] += 1
            
            # Mostrar estatísticas
            rewards_text = "\n".join([f"{reward.emoji} **{name}**: {count} jogadores" 
                                    for name, count in reward_counts.items()])
            
            if rewards_text:
                embed.add_field(
                    name="🎁 Recompensas Entregues",
                    value=rewards_text,
                    inline=False
                )
            
            embed.set_footer(text="Parabéns a todos os premiados!")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao anunciar distribuição de recompensas: {e}")
    
    def get_current_season(self) -> Optional[Season]:
        """Retorna a temporada atual"""
        return self.current_season
    
    def get_season_by_id(self, season_id: str) -> Optional[Season]:
        """Retorna uma temporada pelo ID"""
        return self.seasons.get(season_id)
    
    def get_all_seasons(self) -> List[Season]:
        """Retorna todas as temporadas"""
        return list(self.seasons.values())
    
    def get_user_season_history(self, user_id: str) -> Dict:
        """Retorna o histórico de temporadas de um usuário"""
        return self.user_season_data.get(user_id, {})
    
    async def check_and_update_seasons(self):
        """Verifica e atualiza status das temporadas (executado periodicamente)"""
        try:
            current_time = datetime.now()
            
            # Verificar se temporada atual expirou
            if (self.current_season and 
                self.current_season.status == SeasonStatus.ACTIVE and 
                current_time > self.current_season.end_date):
                
                await self.end_season(self.current_season)
            
            # Auto-criar nova temporada se configurado
            if (self.config["auto_create_seasons"] and 
                not self.current_season):
                
                await self._auto_create_next_season()
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar temporadas: {e}")
    
    async def _auto_create_next_season(self):
        """Cria automaticamente a próxima temporada"""
        try:
            # Determinar tema baseado no mês
            current_month = datetime.now().month
            theme_map = {
                12: "winter", 1: "winter", 2: "winter",
                3: "spring", 4: "spring", 5: "spring",
                6: "summer", 7: "summer", 8: "summer",
                9: "autumn", 10: "autumn", 11: "autumn"
            }
            
            theme = theme_map.get(current_month, "default")
            season_number = len(self.seasons) + 1
            
            season = self.create_season(
                name=f"Temporada {season_number}",
                description=f"Nova temporada com tema {theme}! Compete pelos melhores rankings e recompensas exclusivas.",
                theme=theme
            )
            
            await self.start_season(season)
            
        except Exception as e:
            self.logger.error(f"Erro ao criar temporada automaticamente: {e}")