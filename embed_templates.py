import discord
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger('HawkBot.EmbedTemplates')

class EmbedTemplates:
    """Sistema de templates visuais personalizados para diferentes tipos de embeds"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.templates = self._load_templates()
        logger.info("Sistema de Templates de Embeds inicializado")
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Carrega configurações de templates com paleta PUBG oficial"""
        # Paleta de cores PUBG oficial
        PUBG_COLORS = {
            'primary_orange': 0xFF6B35,      # Laranja principal PUBG
            'secondary_blue': 0x1E3A8A,     # Azul escuro PUBG
            'accent_yellow': 0xFBBF24,      # Amarelo de destaque
            'success_green': 0x10B981,      # Verde de sucesso
            'error_red': 0xEF4444,          # Vermelho de erro
            'warning_amber': 0xF59E0B,      # Âmbar de aviso
            'info_cyan': 0x06B6D4,          # Ciano informativo
            'rank_gold': 0xD97706,          # Dourado para ranks
            'tournament_purple': 0x7C3AED,  # Roxo para torneios
            'music_spotify': 0x1DB954,      # Verde Spotify
            'moderation_gray': 0x6B7280,    # Cinza moderação
            'welcome_emerald': 0x059669,    # Verde esmeralda
            'leaderboard_bronze': 0xCD7F32  # Bronze leaderboard
        }
        
        return {
            'success': {
                'color': PUBG_COLORS['success_green'],
                'emoji': '✅',
                'footer_icon': '✨',
                'border_style': '▬' * 30,
                'gradient': True
            },
            'error': {
                'color': PUBG_COLORS['error_red'],
                'emoji': '❌',
                'footer_icon': '⚠️',
                'border_style': '━' * 30,
                'gradient': True
            },
            'warning': {
                'color': PUBG_COLORS['warning_amber'],
                'emoji': '⚠️',
                'footer_icon': '🔔',
                'border_style': '─' * 30,
                'gradient': True
            },
            'info': {
                'color': PUBG_COLORS['info_cyan'],
                'emoji': 'ℹ️',
                'footer_icon': '💡',
                'border_style': '═' * 30,
                'gradient': True
            },
            'pubg_rank': {
                'color': PUBG_COLORS['primary_orange'],
                'emoji': '🎮',
                'footer_icon': '🏆',
                'border_style': '▰' * 25,
                'thumbnail': 'https://cdn.discordapp.com/attachments/pubg_logo.png',
                'gradient': True,
                'banner': True
            },
            'server_rank': {
                'color': PUBG_COLORS['secondary_blue'],
                'emoji': '🏠',
                'footer_icon': '⭐',
                'border_style': '▱' * 25,
                'gradient': True,
                'banner': True
            },
            'tournament': {
                'color': PUBG_COLORS['tournament_purple'],
                'emoji': '🏆',
                'footer_icon': '🎯',
                'border_style': '◆' * 20,
                'gradient': True,
                'banner': True,
                'premium': True
            },
            'achievement': {
                'color': PUBG_COLORS['accent_yellow'],
                'emoji': '🏅',
                'footer_icon': '🌟',
                'border_style': '★' * 15,
                'gradient': True,
                'glow': True
            },
            'music': {
                'color': PUBG_COLORS['music_spotify'],
                'emoji': '🎵',
                'footer_icon': '🎶',
                'border_style': '♪' * 20,
                'gradient': True,
                'animated': True
            },
            'moderation': {
                'color': PUBG_COLORS['moderation_gray'],
                'emoji': '🛡️',
                'footer_icon': '⚖️',
                'border_style': '▌' * 25,
                'gradient': True,
                'serious': True
            },
            'welcome': {
                'color': PUBG_COLORS['welcome_emerald'],
                'emoji': '👋',
                'footer_icon': '🎉',
                'border_style': '🌟' * 10,
                'gradient': True,
                'celebration': True
            },
            'leaderboard': {
                'color': PUBG_COLORS['leaderboard_bronze'],
                'emoji': '📊',
                'footer_icon': '🏆',
                'border_style': '▓' * 20,
                'gradient': True,
                'competitive': True
            },
            'premium': {
                'color': PUBG_COLORS['rank_gold'],
                'emoji': '💎',
                'footer_icon': '👑',
                'border_style': '◈' * 15,
                'gradient': True,
                'premium': True,
                'glow': True
            }
        }
    
    def create_embed(self, template_type: str, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria um embed usando um template específico com recursos visuais avançados"""
        template = self.templates.get(template_type, self.templates['info'])
        
        # Criar título com efeitos especiais
        enhanced_title = self._enhance_title(title, template)
        
        # Criar embed base
        embed = discord.Embed(
            title=enhanced_title,
            description=self._enhance_description(description, template),
            color=template['color'],
            timestamp=kwargs.get('timestamp', datetime.now())
        )
        
        # Configurar thumbnail com prioridade para kwargs
        thumbnail_url = kwargs.get('thumbnail_url') or template.get('thumbnail')
        if thumbnail_url and kwargs.get('show_thumbnail', True):
            embed.set_thumbnail(url=thumbnail_url)
        
        # Configurar banner/image se disponível
        if template.get('banner') and kwargs.get('banner_url'):
            embed.set_image(url=kwargs['banner_url'])
        
        # Configurar autor se fornecido
        if kwargs.get('author_name'):
            embed.set_author(
                name=kwargs['author_name'],
                icon_url=kwargs.get('author_icon_url'),
                url=kwargs.get('author_url')
            )
        
        # Configurar footer aprimorado
        footer_text = self._create_enhanced_footer(template, kwargs)
        embed.set_footer(
            text=footer_text,
            icon_url=kwargs.get('footer_icon_url', 'https://cdn.discordapp.com/attachments/hawk_icon.png')
        )
        
        return embed
    
    def _enhance_title(self, title: str, template: Dict[str, Any]) -> str:
        """Aprimora o título com efeitos visuais baseados no template"""
        emoji = template['emoji']
        
        if template.get('premium'):
            return f"✨ {emoji} **{title}** {emoji} ✨"
        elif template.get('glow'):
            return f"🌟 {emoji} __{title}__ 🌟"
        elif template.get('celebration'):
            return f"🎉 {emoji} **{title}** {emoji} 🎉"
        else:
            return f"{emoji} **{title}**"
    
    def _enhance_description(self, description: str, template: Dict[str, Any]) -> str:
        """Aprimora a descrição com bordas e efeitos especiais"""
        if not description:
            return None
        
        border = template['border_style']
        
        if template.get('premium'):
            return f"╔{border}╗\n║ {description} ║\n╚{border}╝"
        elif template.get('gradient'):
            return f"{border}\n✨ {description} ✨\n{border}"
        else:
            return f"{border}\n{description}\n{border}"
    
    def _create_enhanced_footer(self, template: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        """Cria footer aprimorado com informações contextuais"""
        base_text = kwargs.get('footer_text', 'Hawk Esports')
        footer_icon = template['footer_icon']
        
        # Adicionar informações especiais baseadas no template
        if template.get('competitive'):
            return f"{footer_icon} {base_text} • Ranking Competitivo"
        elif template.get('premium'):
            return f"{footer_icon} {base_text} • Premium Experience"
        elif template.get('animated'):
            return f"{footer_icon} {base_text} • Sistema de Música"
        else:
            return f"{footer_icon} {base_text}"
    
    def create_success_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed de sucesso"""
        return self.create_embed('success', title, description, **kwargs)
    
    def create_error_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed de erro"""
        return self.create_embed('error', title, description, **kwargs)
    
    def create_warning_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed de aviso"""
        return self.create_embed('warning', title, description, **kwargs)
    
    def create_info_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed informativo"""
        return self.create_embed('info', title, description, **kwargs)
    
    def create_premium_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed premium com efeitos especiais"""
        return self.create_embed('premium', title, description, **kwargs)
    
    def create_tournament_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed para torneios com visual competitivo"""
        return self.create_embed('tournament', title, description, **kwargs)
    
    def create_achievement_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed para conquistas com efeito brilhante"""
        return self.create_embed('achievement', title, description, **kwargs)
    
    def create_music_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed para música com animações"""
        return self.create_embed('music', title, description, **kwargs)
    
    def create_leaderboard_embed(self, title: str, description: str = None, **kwargs) -> discord.Embed:
        """Cria embed para leaderboards competitivos"""
        return self.create_embed('leaderboard', title, description, **kwargs)
    
    def create_welcome_embed(self, user: discord.Member, **kwargs) -> discord.Embed:
        """Cria embed de boas-vindas personalizado"""
        description = f"Bem-vindo(a) ao **Hawk Esports**, {user.mention}!\n\n" \
                     f"🎮 Prepare-se para a batalha no PUBG\n" \
                     f"🏆 Conquiste seu lugar no ranking\n" \
                     f"👥 Junte-se à nossa comunidade de elite\n\n" \
                     f"Use `/help` para conhecer todos os comandos!"
        
        embed = self.create_embed(
            'welcome', 
            f"Novo Membro - {user.display_name}",
            description,
            author_name=user.display_name,
            author_icon_url=user.display_avatar.url,
            thumbnail_url=user.display_avatar.url,
            **kwargs
        )
        
        # Adiciona banner de boas-vindas
        template = self.templates['welcome']
        if template.get('banner'):
            import os
            banner_path = os.path.join(os.path.dirname(__file__), 'banners', 'welcome_banner.svg')
            if os.path.exists(banner_path):
                embed.set_image(url=f"attachment://welcome_banner.svg")
        
        # Adicionar campos especiais
        embed.add_field(
            name="🎯 Próximos Passos",
            value="• Use `/register` para se registrar\n• Configure seu perfil PUBG\n• Participe dos torneios",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Recursos Disponíveis",
            value="• Sistema de Ranking\n• Torneios Automáticos\n• Música e Diversão",
            inline=True
        )
        
        return embed
    
    def create_pubg_rank_embed(self, user: discord.Member, rank_data: Dict[str, Any]) -> discord.Embed:
        """Cria embed especializado para ranking PUBG"""
        embed = self.create_embed(
            'pubg_rank',
            f"Ranking PUBG - {user.display_name}",
            "🏆 **Estatísticas do PUBG**"
        )
        
        # Adicionar campos específicos do PUBG
        if rank_data.get('ranked_rank'):
            embed.add_field(
                name="🎯 Rank Ranqueada",
                value=f"**{rank_data['ranked_rank']}**\n{rank_data.get('ranked_points', 'N/A')} pontos",
                inline=True
            )
        
        if rank_data.get('mm_rank'):
            embed.add_field(
                name="⚔️ Rank MM",
                value=f"**{rank_data['mm_rank']}**\n{rank_data.get('mm_points', 'N/A')} pontos",
                inline=True
            )
        
        # Estatísticas gerais
        stats_text = ""
        if rank_data.get('kd'):
            stats_text += f"K/D: **{rank_data['kd']}**\n"
        if rank_data.get('wins'):
            stats_text += f"Vitórias: **{rank_data['wins']}**\n"
        if rank_data.get('winrate'):
            stats_text += f"Taxa de Vitória: **{rank_data['winrate']}%**"
        
        if stats_text:
            embed.add_field(
                name="📊 Estatísticas",
                value=stats_text,
                inline=False
            )
        
        return embed
    
    def create_server_rank_embed(self, user: discord.Member, rank_data: Dict[str, Any]) -> discord.Embed:
        """Cria embed especializado para ranking do servidor"""
        embed = self.create_embed(
            'server_rank',
            f"Ranking do Servidor - {user.display_name}",
            "🏠 **Atividade no Servidor Hawk Esports**"
        )
        
        # Adicionar campos específicos do servidor
        embed.add_field(
            name="🏆 Posição",
            value=f"**#{rank_data.get('position', 'N/A')}**",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Pontos",
            value=f"**{rank_data.get('points', 0)}** pontos",
            inline=True
        )
        
        embed.add_field(
            name="📈 Nível",
            value=f"**{rank_data.get('level', 1)}**",
            inline=True
        )
        
        # Atividades recentes
        if rank_data.get('recent_activities'):
            activities_text = "\n".join(rank_data['recent_activities'][:3])
            embed.add_field(
                name="📋 Atividades Recentes",
                value=activities_text,
                inline=False
            )
        
        return embed
    
    def create_tournament_embed(self, tournament_data: Dict[str, Any]) -> discord.Embed:
        """Cria embed especializado para torneios"""
        embed = self.create_embed(
            'tournament',
            tournament_data.get('name', 'Torneio'),
            f"🏆 **{tournament_data.get('description', 'Torneio Hawk Esports')}**"
        )
        
        # Status do torneio
        status_emoji = {
            'active': '🟢',
            'pending': '🟡',
            'completed': '🔴'
        }
        
        status = tournament_data.get('status', 'pending')
        embed.add_field(
            name="📊 Status",
            value=f"{status_emoji.get(status, '⚪')} **{status.title()}**",
            inline=True
        )
        
        embed.add_field(
            name="👥 Participantes",
            value=f"**{tournament_data.get('participants', 0)}** jogadores",
            inline=True
        )
        
        if tournament_data.get('prize'):
            embed.add_field(
                name="💰 Prêmio",
                value=f"**{tournament_data['prize']}**",
                inline=True
            )
        
        # Adiciona banner de torneios
        template = self.templates['tournament']
        if template.get('banner'):
            import os
            banner_path = os.path.join(os.path.dirname(__file__), 'banners', 'tournament_banner.svg')
            if os.path.exists(banner_path):
                embed.set_image(url=f"attachment://tournament_banner.svg")
        
        return embed
    
    def create_achievement_embed(self, user: discord.Member, achievement_data: Dict[str, Any]) -> discord.Embed:
        """Cria embed especializado para conquistas"""
        embed = self.create_embed(
            'achievement',
            f"Nova Conquista Desbloqueada!",
            f"🎉 **{user.display_name}** conquistou um novo badge!"
        )
        
        # Informações da conquista
        embed.add_field(
            name="🏅 Conquista",
            value=f"**{achievement_data.get('name', 'Badge Especial')}**",
            inline=False
        )
        
        if achievement_data.get('description'):
            embed.add_field(
                name="📝 Descrição",
                value=achievement_data['description'],
                inline=False
            )
        
        if achievement_data.get('rarity'):
            rarity_emojis = {
                'common': '⚪',
                'uncommon': '🟢',
                'rare': '🔵',
                'epic': '🟣',
                'legendary': '🟡'
            }
            
            embed.add_field(
                name="💎 Raridade",
                value=f"{rarity_emojis.get(achievement_data['rarity'], '⚪')} **{achievement_data['rarity'].title()}**",
                inline=True
            )
        
        # Adiciona banner de conquistas
        template = self.templates['achievement']
        if template.get('banner'):
            import os
            banner_path = os.path.join(os.path.dirname(__file__), 'banners', 'achievement_banner.svg')
            if os.path.exists(banner_path):
                embed.set_image(url=f"attachment://achievement_banner.svg")
        
        return embed
    
    def create_music_embed(self, song_title: str, artist: str, duration: str, **kwargs) -> discord.Embed:
        """Cria embed de música com visualização avançada"""
        template = self.templates['music']
        
        embed = discord.Embed(
            title=f"🎵 {song_title}",
            description=f"**Artista:** {artist}\n" +
                       f"⏱️ **Duração:** {duration}\n" +
                       f"🎧 **Qualidade:** {kwargs.get('quality', 'Alta')}\n" +
                       f"📊 **Bitrate:** {kwargs.get('bitrate', '320kbps')}",
            color=template['color']
        )
        
        # Adiciona banner de música
        if template.get('banner'):
            import os
            banner_path = os.path.join(os.path.dirname(__file__), 'banners', 'music_banner.svg')
            if os.path.exists(banner_path):
                embed.set_image(url=f"attachment://music_banner.svg")
        
        # Adicionar barra de progresso se fornecida
        if 'progress' in kwargs:
            progress_bar = self._create_progress_bar(kwargs['progress'])
            embed.add_field(
                name="📊 Progresso",
                value=progress_bar,
                inline=False
            )
        
        embed.set_thumbnail(url=kwargs.get('album_art', ''))
        embed.set_footer(
            text=f"{template['footer_icon']} Hawk Esports • Tocando agora",
            icon_url=kwargs.get('footer_icon_url', 'https://cdn.discordapp.com/attachments/hawk_icon.png')
        )
        
        return embed
    
    def create_welcome_embed(self, user: discord.Member, server_info: Dict[str, Any] = None) -> discord.Embed:
        """Cria embed especializado para boas-vindas"""
        embed = self.create_embed(
            'welcome',
            f"Bem-vindo ao Hawk Esports!",
            f"🎉 **{user.display_name}** acabou de entrar no servidor!"
        )
        
        embed.add_field(
            name="👋 Olá!",
            value=f"Seja bem-vindo(a), {user.mention}!\nEsperamos que se divirta conosco!",
            inline=False
        )
        
        if server_info:
            embed.add_field(
                name="📊 Você é o membro",
                value=f"**#{server_info.get('member_count', 'N/A')}**",
                inline=True
            )
        
        embed.add_field(
            name="🎮 Primeiros Passos",
            value="• Use `/register_pubg` para se registrar\n• Confira `/help` para ver todos os comandos\n• Participe dos nossos torneios!",
            inline=False
        )
        
        # Adicionar avatar do usuário
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        return embed
    
    def create_leaderboard_embed(self, rank_type: str, players: List[Dict[str, Any]], **kwargs) -> discord.Embed:
        """Cria embed especializado para leaderboards"""
        title_map = {
            'pubg': '🎮 Leaderboard PUBG',
            'server': '🏠 Leaderboard do Servidor',
            'tournament': '🏆 Leaderboard do Torneio'
        }
        
        embed = self.create_embed(
            'leaderboard',
            title_map.get(rank_type, '📊 Leaderboard'),
            f"🏆 **Top {len(players)} jogadores**"
        )
        
        # Adicionar jogadores
        leaderboard_text = ""
        for i, player in enumerate(players[:10], 1):  # Limitar a 10
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            leaderboard_text += f"{medal} **{player.get('name', 'Jogador')}**\n"
            
            # Adicionar estatísticas específicas
            if rank_type == 'pubg':
                leaderboard_text += f"   Rank: `{player.get('rank', 'N/A')}` | K/D: `{player.get('kd', 'N/A')}`\n"
            elif rank_type == 'server':
                leaderboard_text += f"   Pontos: `{player.get('points', 0)}` | Nível: `{player.get('level', 1)}`\n"
            
            leaderboard_text += "\n"
        
        if leaderboard_text:
            embed.add_field(
                name="📊 Ranking",
                value=leaderboard_text,
                inline=False
            )
        
        return embed
    
    def get_available_templates(self) -> List[str]:
        """Retorna lista de templates disponíveis"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_type: str) -> Dict[str, Any]:
        """Retorna informações sobre um template específico"""
        return self.templates.get(template_type, {})