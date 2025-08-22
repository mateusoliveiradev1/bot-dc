import discord
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from storage import DataStorage

logger = logging.getLogger('AchievementSystem')

class Achievement:
    """Classe para representar uma conquista"""
    def __init__(self, id: str, name: str, description: str, icon: str, 
                 category: str, points: int, requirements: Dict[str, Any]):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.category = category
        self.points = points
        self.requirements = requirements
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'points': self.points,
            'requirements': self.requirements
        }

class AchievementSystem:
    """Sistema completo de conquistas e badges"""
    
    def __init__(self, bot, storage: DataStorage):
        self.bot = bot
        self.storage = storage
        self.achievements = {}
        self.user_achievements = {}
        
        # Inicializar conquistas padrão
        self._initialize_default_achievements()
        
        # Carregar dados salvos
        self._load_user_achievements()
        
        logger.info("Sistema de Conquistas inicializado com sucesso!")
    
    def _initialize_default_achievements(self):
        """Inicializar conquistas padrão do sistema"""
        default_achievements = [
            # Conquistas de Registro
            Achievement(
                "first_registration", "Bem-vindo ao Clã!", 
                "Registre-se no clã pela primeira vez", "🎯", 
                "registro", 10, {"type": "registration", "count": 1}
            ),
            
            # Conquistas de K/D
            Achievement(
                "kd_warrior", "Guerreiro", 
                "Alcance K/D ratio de 2.0 ou mais", "⚔️", 
                "combate", 25, {"type": "kd_ratio", "value": 2.0}
            ),
            Achievement(
                "kd_legend", "Lenda", 
                "Alcance K/D ratio de 5.0 ou mais", "🏆", 
                "combate", 50, {"type": "kd_ratio", "value": 5.0}
            ),
            Achievement(
                "kd_god", "Deus da Guerra", 
                "Alcance K/D ratio de 10.0 ou mais", "👑", 
                "combate", 100, {"type": "kd_ratio", "value": 10.0}
            ),
            
            # Conquistas de Kills
            Achievement(
                "first_blood", "Primeira Morte", 
                "Consiga sua primeira kill", "🩸", 
                "combate", 5, {"type": "kills", "count": 1}
            ),
            Achievement(
                "killer_100", "Centurião", 
                "Consiga 100 kills", "💀", 
                "combate", 30, {"type": "kills", "count": 100}
            ),
            Achievement(
                "killer_500", "Assassino", 
                "Consiga 500 kills", "🗡️", 
                "combate", 75, {"type": "kills", "count": 500}
            ),
            Achievement(
                "killer_1000", "Exterminador", 
                "Consiga 1000 kills", "☠️", 
                "combate", 150, {"type": "kills", "count": 1000}
            ),
            
            # Conquistas de Vitórias
            Achievement(
                "first_win", "Primeira Vitória", 
                "Consiga sua primeira chicken dinner", "🍗", 
                "vitoria", 15, {"type": "wins", "count": 1}
            ),
            Achievement(
                "winner_10", "Vencedor", 
                "Consiga 10 vitórias", "🥇", 
                "vitoria", 40, {"type": "wins", "count": 10}
            ),
            Achievement(
                "winner_50", "Campeão", 
                "Consiga 50 vitórias", "🏆", 
                "vitoria", 100, {"type": "wins", "count": 50}
            ),
            Achievement(
                "winner_100", "Mestre", 
                "Consiga 100 vitórias", "👑", 
                "vitoria", 200, {"type": "wins", "count": 100}
            ),
            
            # Conquistas de Participação
            Achievement(
                "active_player", "Jogador Ativo", 
                "Jogue por 7 dias consecutivos", "📅", 
                "participacao", 20, {"type": "consecutive_days", "count": 7}
            ),
            Achievement(
                "veteran", "Veterano", 
                "Seja membro do clã por 30 dias", "🎖️", 
                "participacao", 50, {"type": "membership_days", "count": 30}
            ),
            
            # Conquistas de Torneios
            Achievement(
                "tournament_participant", "Competidor", 
                "Participe de seu primeiro torneio", "🎮", 
                "torneio", 25, {"type": "tournament_participation", "count": 1}
            ),
            Achievement(
                "tournament_winner", "Campeão de Torneio", 
                "Vença um torneio interno", "🏆", 
                "torneio", 100, {"type": "tournament_wins", "count": 1}
            ),
            
            # Conquistas de Clipes
            Achievement(
                "content_creator", "Criador de Conteúdo", 
                "Compartilhe 5 clipes no servidor", "🎬", 
                "conteudo", 30, {"type": "clips_shared", "count": 5}
            ),
            Achievement(
                "viral_clip", "Viral", 
                "Tenha um clipe com mais de 100 visualizações", "🌟", 
                "conteudo", 50, {"type": "clip_views", "value": 100}
            ),
            
            # Conquistas de Headshots
            Achievement(
                "headshot_hunter", "Caçador de Headshots", 
                "Consiga 50 headshots", "🎯", 
                "precisao", 25, {"type": "headshots", "count": 50}
            ),
            Achievement(
                "headshot_master", "Mestre dos Headshots", 
                "Consiga 200 headshots", "🏹", 
                "precisao", 60, {"type": "headshots", "count": 200}
            ),
            Achievement(
                "headshot_god", "Deus dos Headshots", 
                "Consiga 500 headshots", "🎯", 
                "precisao", 120, {"type": "headshots", "count": 500}
            ),
            
            # Conquistas de Dano
            Achievement(
                "damage_dealer", "Causador de Dano", 
                "Cause 100,000 de dano total", "💥", 
                "combate", 40, {"type": "damage_dealt", "count": 100000}
            ),
            Achievement(
                "destruction_machine", "Máquina de Destruição", 
                "Cause 500,000 de dano total", "🔥", 
                "combate", 80, {"type": "damage_dealt", "count": 500000}
            ),
            Achievement(
                "apocalypse_bringer", "Portador do Apocalipse", 
                "Cause 1,000,000 de dano total", "☢️", 
                "combate", 150, {"type": "damage_dealt", "count": 1000000}
            ),
            
            # Conquistas de Sobrevivência
            Achievement(
                "survivor_rookie", "Sobrevivente Novato", 
                "Fique entre os 10 primeiros em 25 partidas", "🛡️", 
                "sobrevivencia", 30, {"type": "top10", "count": 25}
            ),
            Achievement(
                "survivor_expert", "Especialista em Sobrevivência", 
                "Fique entre os 10 primeiros em 100 partidas", "🏕️", 
                "sobrevivencia", 70, {"type": "top10", "count": 100}
            ),
            Achievement(
                "survivor_legend", "Lenda da Sobrevivência", 
                "Fique entre os 10 primeiros em 300 partidas", "🦅", 
                "sobrevivencia", 140, {"type": "top10", "count": 300}
            ),
            
            # Conquistas de Distância
            Achievement(
                "long_shot", "Tiro de Longa Distância", 
                "Consiga um kill a mais de 300m", "🔭", 
                "precisao", 35, {"type": "longest_kill", "distance": 300}
            ),
            Achievement(
                "sniper_elite", "Elite dos Snipers", 
                "Consiga um kill a mais de 500m", "🎯", 
                "precisao", 75, {"type": "longest_kill", "distance": 500}
            ),
            Achievement(
                "impossible_shot", "Tiro Impossível", 
                "Consiga um kill a mais de 800m", "🌟", 
                "precisao", 150, {"type": "longest_kill", "distance": 800}
            ),
            
            # Conquistas de Veículos
            Achievement(
                "road_warrior", "Guerreiro da Estrada", 
                "Consiga 10 kills com veículos", "🚗", 
                "veiculo", 40, {"type": "vehicle_kills", "count": 10}
            ),
            Achievement(
                "speed_demon", "Demônio da Velocidade", 
                "Percorra 1000km em veículos", "🏎️", 
                "veiculo", 50, {"type": "vehicle_distance", "distance": 1000000}
            ),
            Achievement(
                "crash_master", "Mestre dos Acidentes", 
                "Destrua 50 veículos", "💥", 
                "veiculo", 60, {"type": "vehicles_destroyed", "count": 50}
            ),
            
            # Conquistas de Armas
            Achievement(
                "rifle_specialist", "Especialista em Rifles", 
                "Consiga 200 kills com rifles de assalto", "🔫", 
                "armas", 45, {"type": "weapon_kills", "weapon_type": "assault_rifle", "count": 200}
            ),
            Achievement(
                "sniper_master", "Mestre dos Snipers", 
                "Consiga 100 kills com rifles de precisão", "🎯", 
                "armas", 55, {"type": "weapon_kills", "weapon_type": "sniper_rifle", "count": 100}
            ),
            Achievement(
                "smg_expert", "Especialista em SMGs", 
                "Consiga 300 kills com SMGs", "🏃", 
                "armas", 40, {"type": "weapon_kills", "weapon_type": "smg", "count": 300}
            ),
            Achievement(
                "shotgun_king", "Rei das Escopetas", 
                "Consiga 150 kills com escopetas", "🤠", 
                "armas", 50, {"type": "weapon_kills", "weapon_type": "shotgun", "count": 150}
            ),
            Achievement(
                "pistol_master", "Mestre das Pistolas", 
                "Consiga 75 kills com pistolas", "🔫", 
                "armas", 65, {"type": "weapon_kills", "weapon_type": "pistol", "count": 75}
            ),
            
            # Conquistas de Granadas
            Achievement(
                "grenade_expert", "Especialista em Granadas", 
                "Consiga 25 kills com granadas", "💣", 
                "explosivos", 45, {"type": "grenade_kills", "count": 25}
            ),
            Achievement(
                "demolition_king", "Rei da Demolição", 
                "Consiga 100 kills com explosivos", "💥", 
                "explosivos", 80, {"type": "explosive_kills", "count": 100}
            ),
            
            # Conquistas de Tempo
            Achievement(
                "speed_runner", "Corredor Veloz", 
                "Vença uma partida em menos de 20 minutos", "⚡", 
                "tempo", 60, {"type": "fastest_win", "time": 1200}
            ),
            Achievement(
                "marathon_man", "Homem Maratona", 
                "Sobreviva por mais de 35 minutos em uma partida", "🏃‍♂️", 
                "tempo", 50, {"type": "longest_survival", "time": 2100}
            ),
            
            # Conquistas de Equipe
            Achievement(
                "team_player", "Jogador de Equipe", 
                "Reviva 50 companheiros de equipe", "🤝", 
                "equipe", 40, {"type": "revives", "count": 50}
            ),
            Achievement(
                "medic", "Médico de Campo", 
                "Cure 10,000 HP de companheiros", "🏥", 
                "equipe", 55, {"type": "healing_done", "amount": 10000}
            ),
            Achievement(
                "support_master", "Mestre do Suporte", 
                "Dê 100 assists", "🎯", 
                "equipe", 45, {"type": "assists", "count": 100}
            ),
            
            # Conquistas de Streak
            Achievement(
                "killing_spree", "Matança", 
                "Consiga 5 kills seguidos sem morrer", "🔥", 
                "streak", 50, {"type": "kill_streak", "count": 5}
            ),
            Achievement(
                "unstoppable", "Imparável", 
                "Consiga 10 kills seguidos sem morrer", "⚡", 
                "streak", 100, {"type": "kill_streak", "count": 10}
            ),
            Achievement(
                "godlike", "Divino", 
                "Consiga 15 kills seguidos sem morrer", "👑", 
                "streak", 200, {"type": "kill_streak", "count": 15}
            ),
            
            # Conquistas de Rank
            Achievement(
                "bronze_warrior", "Guerreiro de Bronze", 
                "Alcance o rank Bronze", "🥉", 
                "rank", 20, {"type": "rank_achieved", "rank": "bronze"}
            ),
            Achievement(
                "silver_soldier", "Soldado de Prata", 
                "Alcance o rank Prata", "🥈", 
                "rank", 40, {"type": "rank_achieved", "rank": "silver"}
            ),
            Achievement(
                "gold_guardian", "Guardião de Ouro", 
                "Alcance o rank Ouro", "🥇", 
                "rank", 80, {"type": "rank_achieved", "rank": "gold"}
            ),
            Achievement(
                "platinum_predator", "Predador de Platina", 
                "Alcance o rank Platina", "💎", 
                "rank", 120, {"type": "rank_achieved", "rank": "platinum"}
            ),
            Achievement(
                "diamond_destroyer", "Destruidor de Diamante", 
                "Alcance o rank Diamante", "💠", 
                "rank", 180, {"type": "rank_achieved", "rank": "diamond"}
            ),
            Achievement(
                "master_legend", "Lenda Mestre", 
                "Alcance o rank Mestre", "🏆", 
                "rank", 250, {"type": "rank_achieved", "rank": "master"}
            ),
            
            # Conquistas Especiais
            Achievement(
                "perfectionist", "Perfeccionista", 
                "Complete todas as conquistas de uma categoria", "💎", 
                "especial", 200, {"type": "category_complete", "category": "any"}
            ),
            Achievement(
                "completionist", "Completista", 
                "Desbloqueie todas as conquistas disponíveis", "🌟", 
                "especial", 500, {"type": "all_achievements"}
            ),
            Achievement(
                "lucky_charm", "Amuleto da Sorte", 
                "Vença 3 partidas seguidas", "🍀", 
                "especial", 75, {"type": "win_streak", "count": 3}
            ),
            Achievement(
                "chicken_dinner_king", "Rei do Chicken Dinner", 
                "Vença 5 partidas em um dia", "👑", 
                "especial", 100, {"type": "daily_wins", "count": 5}
            ),
            Achievement(
                "night_owl", "Coruja Noturna", 
                "Jogue 50 partidas entre 22h e 6h", "🦉", 
                "especial", 60, {"type": "night_matches", "count": 50}
            ),
            Achievement(
                "early_bird", "Madrugador", 
                "Jogue 50 partidas entre 6h e 10h", "🐦", 
                "especial", 60, {"type": "morning_matches", "count": 50}
            )
        ]
        
        for achievement in default_achievements:
            self.achievements[achievement.id] = achievement
    
    def _load_user_achievements(self):
        """Carregar conquistas dos usuários"""
        try:
            self.user_achievements = self.storage.data.get('user_achievements', {})
        except Exception as e:
            logger.error(f"Erro ao carregar conquistas dos usuários: {e}")
            self.user_achievements = {}
    
    def _save_user_achievements(self):
        """Salvar conquistas dos usuários"""
        try:
            self.storage.data['user_achievements'] = self.user_achievements
            self.storage.save_data()
        except Exception as e:
            logger.error(f"Erro ao salvar conquistas dos usuários: {e}")
    
    def check_achievements(self, user_id: str, stats: Dict[str, Any]) -> List[Achievement]:
        """Verificar e desbloquear conquistas para um usuário"""
        unlocked = []
        
        if user_id not in self.user_achievements:
            self.user_achievements[user_id] = {
                'unlocked': [],
                'progress': {},
                'total_points': 0,
                'last_check': datetime.now().isoformat()
            }
        
        user_data = self.user_achievements[user_id]
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in user_data['unlocked']:
                continue
            
            if self._check_achievement_requirement(achievement, stats, user_data):
                user_data['unlocked'].append(achievement_id)
                user_data['total_points'] += achievement.points
                unlocked.append(achievement)
                logger.info(f"Usuário {user_id} desbloqueou conquista: {achievement.name}")
        
        user_data['last_check'] = datetime.now().isoformat()
        self._save_user_achievements()
        
        return unlocked
    
    def _check_achievement_requirement(self, achievement: Achievement, 
                                     stats: Dict[str, Any], user_data: Dict[str, Any]) -> bool:
        """Verificar se os requisitos de uma conquista foram atendidos"""
        req = achievement.requirements
        req_type = req.get('type')
        
        try:
            if req_type == 'registration':
                return True  # Se chegou aqui, já está registrado
            
            elif req_type == 'kd_ratio':
                current_kd = stats.get('kd_ratio', 0)
                return current_kd >= req.get('value', 0)
            
            elif req_type == 'kills':
                current_kills = stats.get('kills', 0)
                return current_kills >= req.get('count', 0)
            
            elif req_type == 'wins':
                current_wins = stats.get('wins', 0)
                return current_wins >= req.get('count', 0)
            
            elif req_type == 'tournament_participation':
                tournaments = stats.get('tournaments_participated', 0)
                return tournaments >= req.get('count', 0)
            
            elif req_type == 'tournament_wins':
                tournament_wins = stats.get('tournament_wins', 0)
                return tournament_wins >= req.get('count', 0)
            
            elif req_type == 'clips_shared':
                clips = stats.get('clips_shared', 0)
                return clips >= req.get('count', 0)
            
            elif req_type == 'clip_views':
                max_views = stats.get('max_clip_views', 0)
                return max_views >= req.get('value', 0)
            
            elif req_type == 'consecutive_days':
                # Implementar lógica de dias consecutivos
                return False  # Por enquanto
            
            elif req_type == 'membership_days':
                registration_date = stats.get('registration_date')
                if registration_date:
                    reg_date = datetime.fromisoformat(registration_date)
                    days_member = (datetime.now() - reg_date).days
                    return days_member >= req.get('count', 0)
                return False
            
            elif req_type == 'category_complete':
                # Verificar se completou uma categoria
                return self._check_category_completion(user_data, req.get('category'))
            
            elif req_type == 'all_achievements':
                # Verificar se desbloqueou todas as conquistas
                return len(user_data['unlocked']) >= len(self.achievements) - 1  # -1 para não contar esta própria
            
        except Exception as e:
            logger.error(f"Erro ao verificar requisito da conquista {achievement.id}: {e}")
        
        return False
    
    def _check_category_completion(self, user_data: Dict[str, Any], category: str) -> bool:
        """Verificar se uma categoria foi completada"""
        if category == 'any':
            # Verificar se completou qualquer categoria
            categories = {}
            for ach_id in user_data['unlocked']:
                if ach_id in self.achievements:
                    cat = self.achievements[ach_id].category
                    categories[cat] = categories.get(cat, 0) + 1
            
            # Contar quantas conquistas existem por categoria
            category_totals = {}
            for achievement in self.achievements.values():
                cat = achievement.category
                if cat != 'especial':  # Não contar conquistas especiais
                    category_totals[cat] = category_totals.get(cat, 0) + 1
            
            # Verificar se alguma categoria foi completada
            for cat, completed in categories.items():
                if cat in category_totals and completed >= category_totals[cat]:
                    return True
        
        return False
    
    def get_user_achievements(self, user_id: str) -> Dict[str, Any]:
        """Obter conquistas de um usuário"""
        if user_id not in self.user_achievements:
            return {
                'unlocked': [],
                'progress': {},
                'total_points': 0,
                'rank': 'Novato'
            }
        
        user_data = self.user_achievements[user_id].copy()
        user_data['rank'] = self._calculate_rank(user_data['total_points'])
        
        return user_data
    
    def _calculate_rank(self, points: int) -> str:
        """Calcular rank baseado nos pontos"""
        if points >= 1000:
            return "Lenda 👑"
        elif points >= 500:
            return "Mestre 🏆"
        elif points >= 250:
            return "Especialista 🎖️"
        elif points >= 100:
            return "Veterano ⭐"
        elif points >= 50:
            return "Experiente 🔥"
        elif points >= 20:
            return "Iniciante 🎯"
        else:
            return "Novato 🌱"
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obter leaderboard de conquistas"""
        leaderboard = []
        
        for user_id, data in self.user_achievements.items():
            leaderboard.append({
                'user_id': user_id,
                'total_points': data.get('total_points', 0),
                'achievements_count': len(data.get('unlocked', [])),
                'rank': self._calculate_rank(data.get('total_points', 0))
            })
        
        # Ordenar por pontos
        leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
        
        return leaderboard[:limit]
    
    def get_all_achievements(self) -> Dict[str, Achievement]:
        """Obter todas as conquistas disponíveis"""
        return self.achievements.copy()
    
    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """Obter conquistas por categoria"""
        achievements = []
        for achievement in self.achievements.values():
            if achievement.category == category:
                achievements.append(achievement)
        return achievements
    
    async def send_achievement_notification(self, user_id: str, achievement: Achievement, channel):
        """Enviar notificação de conquista desbloqueada"""
        try:
            user = self.bot.get_user(int(user_id))
            if not user:
                return
            
            embed = discord.Embed(
                title="🎉 Conquista Desbloqueada!",
                description=f"**{user.display_name}** desbloqueou uma nova conquista!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name=f"{achievement.icon} {achievement.name}",
                value=achievement.description,
                inline=False
            )
            
            embed.add_field(
                name="📊 Pontos Ganhos",
                value=f"+{achievement.points} pontos",
                inline=True
            )
            
            embed.add_field(
                name="📂 Categoria",
                value=achievement.category.title(),
                inline=True
            )
            
            embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
            embed.set_footer(text="Hawk Esports - Sistema de Conquistas")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de conquista: {e}")
    
    # Comandos do Discord
    async def achievements_command(self, interaction: discord.Interaction, usuario: discord.Member = None):
        """Comando para ver conquistas de um usuário"""
        target_user = usuario or interaction.user
        user_data = self.get_user_achievements(str(target_user.id))
        
        embed = discord.Embed(
            title=f"🏆 Conquistas - {target_user.display_name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"**Rank:** {user_data['rank']}\n" +
                  f"**Pontos:** {user_data['total_points']}\n" +
                  f"**Conquistas:** {len(user_data['unlocked'])}/{len(self.achievements)}",
            inline=False
        )
        
        # Mostrar conquistas recentes
        recent_achievements = user_data['unlocked'][-5:] if user_data['unlocked'] else []
        if recent_achievements:
            recent_text = ""
            for ach_id in recent_achievements:
                if ach_id in self.achievements:
                    ach = self.achievements[ach_id]
                    recent_text += f"{ach.icon} **{ach.name}**\n"
            
            embed.add_field(
                name="🆕 Conquistas Recentes",
                value=recent_text or "Nenhuma conquista ainda",
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
        embed.set_footer(text="Use /conquistas_lista para ver todas as conquistas disponíveis")
        
        await interaction.response.send_message(embed=embed)
    
    async def achievements_list_command(self, interaction: discord.Interaction, categoria: str = None):
        """Comando para listar todas as conquistas disponíveis"""
        embed = discord.Embed(
            title="🏆 Lista de Conquistas Disponíveis",
            color=discord.Color.blue()
        )
        
        # Agrupar por categoria
        categories = {}
        for achievement in self.achievements.values():
            cat = achievement.category
            if categoria and cat != categoria:
                continue
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(achievement)
        
        for cat, achievements in categories.items():
            achievement_text = ""
            for ach in achievements[:5]:  # Limitar para não exceder limite do embed
                achievement_text += f"{ach.icon} **{ach.name}** ({ach.points}pts)\n{ach.description}\n\n"
            
            if achievement_text:
                embed.add_field(
                    name=f"📂 {cat.title()}",
                    value=achievement_text,
                    inline=False
                )
        
        embed.set_footer(text="Hawk Esports - Sistema de Conquistas")
        
        await interaction.response.send_message(embed=embed)
    
    async def achievements_leaderboard_command(self, interaction: discord.Interaction):
        """Comando para mostrar leaderboard de conquistas"""
        leaderboard = self.get_leaderboard(10)
        
        embed = discord.Embed(
            title="🏆 Ranking de Conquistas",
            description="Top 10 jogadores com mais pontos de conquista",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for i, entry in enumerate(leaderboard, 1):
            try:
                user = self.bot.get_user(int(entry['user_id']))
                username = user.display_name if user else "Usuário Desconhecido"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                
                leaderboard_text += f"{medal} **{i}.** {username}\n"
                leaderboard_text += f"   {entry['rank']} - {entry['total_points']} pontos\n"
                leaderboard_text += f"   {entry['achievements_count']} conquistas\n\n"
                
            except Exception as e:
                logger.error(f"Erro ao processar entrada do leaderboard: {e}")
                continue
        
        embed.description = leaderboard_text or "Nenhum jogador com conquistas ainda."
        embed.set_footer(text="Hawk Esports - Sistema de Conquistas")
        
        await interaction.response.send_message(embed=embed)