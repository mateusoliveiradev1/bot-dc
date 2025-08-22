import os
import discord
from typing import Dict, Optional

class EmojiSystem:
    """Sistema de emojis customizados para o bot PUBG"""
    
    def __init__(self):
        self.emoji_map = {
            # Patentes do PUBG
            'bronze': '<:bronze:bronze_rank>',
            'silver': '<:silver:silver_rank>',
            'gold': '<:gold:gold_rank>',
            'platinum': '<:platinum:platinum_rank>',
            'diamond': '<:diamond:diamond_rank>',
            'crystal': '<:crystal:crystal_rank>',
            'master': '<:master:master_rank>',
            'survivor': '<:survivor:survivor_rank>',
            
            # Armas
            'ak47': '<:ak47:ak47_weapon>',
            
            # Conquistas
            'first_blood': '<:first_blood:first_blood>',
            'clutch_master': '<:clutch_master:clutch_master>',
            
            # Emojis padrão como fallback
            'trophy': '🏆',
            'target': '🎯',
            'fire': '🔥',
            'star': '⭐',
            'crown': '👑',
            'medal': '🏅',
            'gun': '🔫',
            'crosshair': '⊕',
            'blood': '🩸'
        }
        
        self.rank_emojis = {
            'Bronze IV': 'bronze',
            'Bronze III': 'bronze',
            'Bronze II': 'bronze', 
            'Bronze I': 'bronze',
            'Silver IV': 'silver',
            'Silver III': 'silver',
            'Silver II': 'silver',
            'Silver I': 'silver',
            'Gold IV': 'gold',
            'Gold III': 'gold',
            'Gold II': 'gold',
            'Gold I': 'gold',
            'Platinum IV': 'platinum',
            'Platinum III': 'platinum',
            'Platinum II': 'platinum',
            'Platinum I': 'platinum',
            'Diamond IV': 'diamond',
            'Diamond III': 'diamond',
            'Diamond II': 'diamond',
            'Diamond I': 'diamond',
            'Crystal IV': 'crystal',
            'Crystal III': 'crystal',
            'Crystal II': 'crystal',
            'Crystal I': 'crystal',
            'Master IV': 'master',
            'Master III': 'master',
            'Master II': 'master',
            'Master I': 'master',
            'Survivor': 'survivor'
        }
    
    def get_emoji(self, emoji_name: str) -> str:
        """Retorna o emoji customizado ou fallback"""
        return self.emoji_map.get(emoji_name, emoji_name)
    
    def get_rank_emoji(self, rank: str) -> str:
        """Retorna o emoji da patente específica"""
        emoji_key = self.rank_emojis.get(rank, 'bronze')
        return self.get_emoji(emoji_key)
    
    def format_rank_display(self, rank: str) -> str:
        """Formata a exibição da patente com emoji"""
        emoji = self.get_rank_emoji(rank)
        return f"{emoji} {rank}"
    
    def get_achievement_emoji(self, achievement_type: str) -> str:
        """Retorna emoji para tipo de conquista"""
        achievement_emojis = {
            'first_blood': 'first_blood',
            'clutch': 'clutch_master',
            'headshot': 'target',
            'win': 'trophy',
            'kill_streak': 'fire',
            'survival': 'survivor'
        }
        
        emoji_key = achievement_emojis.get(achievement_type, 'medal')
        return self.get_emoji(emoji_key)
    
    def get_weapon_emoji(self, weapon_name: str) -> str:
        """Retorna emoji para arma específica"""
        weapon_emojis = {
            'ak47': 'ak47',
            'akm': 'ak47',
            'm416': 'gun',
            'scar-l': 'gun',
            'awm': 'gun',
            'kar98k': 'gun'
        }
        
        weapon_key = weapon_emojis.get(weapon_name.lower(), 'gun')
        return self.get_emoji(weapon_key)
    
    async def upload_emojis_to_guild(self, guild: discord.Guild) -> Dict[str, bool]:
        """Faz upload dos emojis SVG para o servidor Discord"""
        results = {}
        emoji_dir = os.path.join(os.path.dirname(__file__), 'emojis')
        
        if not os.path.exists(emoji_dir):
            return results
        
        for filename in os.listdir(emoji_dir):
            if filename.endswith('.svg'):
                emoji_name = filename.replace('.svg', '')
                file_path = os.path.join(emoji_dir, filename)
                
                try:
                    # Verifica se o emoji já existe
                    existing_emoji = discord.utils.get(guild.emojis, name=emoji_name)
                    if existing_emoji:
                        results[emoji_name] = True
                        continue
                    
                    # Faz upload do emoji
                    with open(file_path, 'rb') as f:
                        emoji_data = f.read()
                        await guild.create_custom_emoji(
                            name=emoji_name,
                            image=emoji_data,
                            reason="Sistema de emojis PUBG Hawk Esports"
                        )
                    
                    results[emoji_name] = True
                    
                except Exception as e:
                    print(f"Erro ao fazer upload do emoji {emoji_name}: {e}")
                    results[emoji_name] = False
        
        return results
    
    def update_emoji_ids(self, guild: discord.Guild):
        """Atualiza os IDs dos emojis após upload"""
        for emoji in guild.emojis:
            if emoji.name in [key.split(':')[1] for key in self.emoji_map.values() if '<:' in key]:
                # Atualiza o mapeamento com o ID real do emoji
                for key, value in self.emoji_map.items():
                    if f':{emoji.name}>' in value:
                        self.emoji_map[key] = f'<:{emoji.name}:{emoji.id}>'

# Instância global do sistema de emojis
emoji_system = EmojiSystem()