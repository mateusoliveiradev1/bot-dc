#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Integração Medal/MedalBot
Responsável por monitorar, processar e gerenciar clipes do Medal

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse

logger = logging.getLogger('HawkBot.MedalIntegration')

class MedalIntegration:
    """Sistema de integração com Medal/MedalBot para gerenciamento de clipes"""
    
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        
        # Configurações
        self.clips_channel_name = os.getenv('CLIPS_CHANNEL_NAME', 'clipes')
        self.max_clips_per_player = int(os.getenv('MAX_CLIPS_PER_PLAYER', '50'))
        self.embed_color = int(os.getenv('CLAN_EMBED_COLOR', '0x00ff00'), 16)
        
        # Padrões para detectar clipes do Medal
        self.medal_patterns = [
            r'https?://medal\.tv/games/[^\s]+',
            r'https?://medal\.tv/clips/[^\s]+',
            r'https?://medal\.tv/[^\s]+'
        ]
        
        # IDs conhecidos do MedalBot
        self.medal_bot_ids = [
            432610292342587392,  # Medal Bot oficial
            # Adicionar outros IDs se necessário
        ]
        
        # Cache de clipes processados (evitar duplicatas)
        self.processed_clips = set()
        
        logger.info("Integração Medal inicializada")
    
    async def process_message(self, message: discord.Message) -> bool:
        """Processa mensagem em busca de clipes do Medal"""
        try:
            # Verificar se é uma mensagem válida para processamento
            if not self._should_process_message(message):
                return False
            
            # Extrair URLs do Medal
            medal_urls = self._extract_medal_urls(message.content)
            
            if not medal_urls:
                return False
            
            # Processar cada URL encontrada
            processed_any = False
            for url in medal_urls:
                if await self._process_clip_url(message, url):
                    processed_any = True
            
            return processed_any
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem para clipes: {e}")
            return False
    
    def _should_process_message(self, message: discord.Message) -> bool:
        """Verifica se a mensagem deve ser processada"""
        # Não processar mensagens do próprio bot
        if message.author == self.bot.user:
            return False
        
        # Não processar mensagens muito antigas (mais de 1 hora)
        if datetime.now() - message.created_at > timedelta(hours=1):
            return False
        
        # Verificar se tem conteúdo
        if not message.content:
            return False
        
        return True
    
    def _extract_medal_urls(self, content: str) -> List[str]:
        """Extrai URLs do Medal do conteúdo da mensagem"""
        urls = []
        
        for pattern in self.medal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            urls.extend(matches)
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    async def _process_clip_url(self, message: discord.Message, url: str) -> bool:
        """Processa uma URL específica de clipe"""
        try:
            # Verificar se já foi processado
            clip_id = self._extract_clip_id(url)
            if clip_id in self.processed_clips:
                return False
            
            # Tentar identificar o jogador
            player_info = await self._identify_player(message)
            
            # Extrair metadados do clipe
            clip_metadata = await self._extract_clip_metadata(message, url)
            
            # Criar dados do clipe
            clip_data = {
                'id': clip_id,
                'url': url,
                'player_id': player_info.get('player_id'),
                'player_name': player_info.get('player_name', 'Desconhecido'),
                'discord_user': str(message.author.id),
                'discord_username': message.author.display_name,
                'channel_id': str(message.channel.id),
                'message_id': str(message.id),
                'created_at': datetime.now().isoformat(),
                'metadata': clip_metadata,
                'guild_id': str(message.guild.id) if message.guild else None
            }
            
            # Salvar no storage
            self.storage.add_clip(clip_data)
            
            # Marcar como processado
            self.processed_clips.add(clip_id)
            
            # Repostar no canal de clipes se necessário
            await self._repost_clip(message, clip_data)
            
            logger.info(f"Clipe processado: {clip_id} de {player_info.get('player_name', 'Desconhecido')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar clipe {url}: {e}")
            return False
    
    def _extract_clip_id(self, url: str) -> str:
        """Extrai ID único do clipe da URL"""
        try:
            # Tentar extrair ID da URL do Medal
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            # Diferentes formatos de URL do Medal
            if 'clips' in path_parts:
                clip_index = path_parts.index('clips')
                if clip_index + 1 < len(path_parts):
                    return path_parts[clip_index + 1]
            
            # Usar a URL completa como fallback
            return url.split('/')[-1] or url
            
        except Exception as e:
            logger.error(f"Erro ao extrair ID do clipe: {e}")
            return url
    
    async def _identify_player(self, message: discord.Message) -> Dict[str, Any]:
        """Tenta identificar o jogador que postou o clipe"""
        try:
            # Buscar jogador registrado pelo Discord ID
            player_data = self.storage.get_player(str(message.author.id))
            
            if player_data:
                return {
                    'player_id': str(message.author.id),
                    'player_name': player_data.get('pubg_name', 'Desconhecido'),
                    'registered': True
                }
            
            # Se não encontrou, usar dados do Discord
            return {
                'player_id': None,
                'player_name': message.author.display_name,
                'registered': False
            }
            
        except Exception as e:
            logger.error(f"Erro ao identificar jogador: {e}")
            return {
                'player_id': None,
                'player_name': 'Desconhecido',
                'registered': False
            }
    
    async def _extract_clip_metadata(self, message: discord.Message, url: str) -> Dict[str, Any]:
        """Extrai metadados do clipe"""
        try:
            metadata = {
                'original_message': message.content,
                'message_timestamp': message.created_at.isoformat(),
                'channel_name': message.channel.name if hasattr(message.channel, 'name') else 'DM',
                'has_embeds': len(message.embeds) > 0,
                'embed_count': len(message.embeds),
                'reactions': len(message.reactions),
                'is_medal_bot': message.author.id in self.medal_bot_ids
            }
            
            # Extrair informações dos embeds se disponível
            if message.embeds:
                embed = message.embeds[0]
                metadata.update({
                    'embed_title': embed.title,
                    'embed_description': embed.description,
                    'embed_thumbnail': embed.thumbnail.url if embed.thumbnail else None,
                    'embed_video': embed.video.url if embed.video else None
                })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")
            return {}
    
    async def _repost_clip(self, original_message: discord.Message, clip_data: Dict[str, Any]):
        """Reposta o clipe no canal dedicado se necessário"""
        try:
            # Verificar se deve repostar
            if not self._should_repost(original_message):
                return
            
            # Encontrar canal de clipes
            clips_channel = discord.utils.get(
                original_message.guild.channels,
                name=self.clips_channel_name
            )
            
            if not clips_channel:
                logger.warning(f"Canal de clipes '{self.clips_channel_name}' não encontrado")
                return
            
            # Criar embed para o repost
            embed = await self._create_clip_embed(clip_data)
            
            # Enviar no canal de clipes
            await clips_channel.send(embed=embed)
            
            logger.info(f"Clipe repostado no canal {self.clips_channel_name}")
            
        except Exception as e:
            logger.error(f"Erro ao repostar clipe: {e}")
    
    def _should_repost(self, message: discord.Message) -> bool:
        """Verifica se o clipe deve ser repostado"""
        # Não repostar se já está no canal de clipes
        if hasattr(message.channel, 'name') and message.channel.name == self.clips_channel_name:
            return False
        
        # Repostar apenas se for de um jogador registrado ou do MedalBot
        if message.author.id in self.medal_bot_ids:
            return True
        
        player_data = self.storage.get_player(str(message.author.id))
        return player_data is not None
    
    async def _create_clip_embed(self, clip_data: Dict[str, Any]) -> discord.Embed:
        """Cria embed formatado para o clipe"""
        try:
            embed = discord.Embed(
                title="🎬 Novo Clipe - Hawk Esports",
                description=f"Clipe de **{clip_data['player_name']}**",
                color=self.embed_color,
                timestamp=datetime.fromisoformat(clip_data['created_at'])
            )
            
            # Adicionar URL do clipe
            embed.add_field(
                name="🔗 Link do Clipe",
                value=f"[Assistir no Medal]({clip_data['url']})",
                inline=False
            )
            
            # Adicionar informações do jogador
            player_info = f"Discord: <@{clip_data['discord_user']}>\n"
            if clip_data['player_id']:
                player_info += f"PUBG: **{clip_data['player_name']}**"
            else:
                player_info += "*Jogador não registrado*"
            
            embed.add_field(
                name="👤 Jogador",
                value=player_info,
                inline=True
            )
            
            # Adicionar metadados se disponível
            metadata = clip_data.get('metadata', {})
            if metadata.get('embed_title'):
                embed.add_field(
                    name="📝 Título",
                    value=metadata['embed_title'][:100] + ('...' if len(metadata['embed_title']) > 100 else ''),
                    inline=True
                )
            
            # Adicionar thumbnail se disponível
            if metadata.get('embed_thumbnail'):
                embed.set_thumbnail(url=metadata['embed_thumbnail'])
            
            # Footer
            embed.set_footer(
                text="Hawk Esports | Sistema de Clipes",
                icon_url=os.getenv('CLAN_LOGO_URL', '')
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao criar embed do clipe: {e}")
            
            # Embed simples em caso de erro
            return discord.Embed(
                title="🎬 Novo Clipe",
                description=f"[Link do Clipe]({clip_data['url']})",
                color=self.embed_color
            )
    
    async def get_player_clips(self, player_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca clipes de um jogador específico"""
        try:
            all_clips = self.storage.get_clips()
            
            # Filtrar clipes do jogador
            player_clips = [
                clip for clip in all_clips
                if clip.get('player_id') == player_id or clip.get('discord_user') == player_id
            ]
            
            # Ordenar por data (mais recentes primeiro)
            player_clips.sort(
                key=lambda x: datetime.fromisoformat(x['created_at']),
                reverse=True
            )
            
            return player_clips[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar clipes do jogador {player_id}: {e}")
            return []
    
    async def create_clips_list_embed(self, player_id: str, limit: int = 10) -> discord.Embed:
        """Cria embed com lista de clipes de um jogador"""
        try:
            clips = await self.get_player_clips(player_id, limit)
            
            # Buscar informações do jogador
            player_data = self.storage.get_player(player_id)
            player_name = player_data.get('pubg_name', 'Jogador') if player_data else 'Jogador'
            
            embed = discord.Embed(
                title=f"🎬 Clipes de {player_name}",
                description=f"**Hawk Esports** - Últimos {len(clips)} clipes",
                color=self.embed_color,
                timestamp=datetime.now()
            )
            
            if clips:
                clips_text = ""
                for i, clip in enumerate(clips, 1):
                    created_date = datetime.fromisoformat(clip['created_at']).strftime('%d/%m/%Y')
                    clips_text += f"{i}. [Clipe {i}]({clip['url']}) - {created_date}\n"
                
                embed.add_field(
                    name="📋 Lista de Clipes",
                    value=clips_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="📋 Lista de Clipes",
                    value="Nenhum clipe encontrado para este jogador.",
                    inline=False
                )
            
            # Estatísticas
            total_clips = len(await self.get_player_clips(player_id, 1000))  # Buscar todos
            embed.add_field(
                name="📊 Estatísticas",
                value=f"Total de clipes: **{total_clips}**\n"
                      f"Mostrando: **{len(clips)}** mais recentes",
                inline=True
            )
            
            embed.set_footer(
                text="Hawk Esports | Sistema de Clipes",
                icon_url=os.getenv('CLAN_LOGO_URL', '')
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao criar embed de lista de clipes: {e}")
            
            return discord.Embed(
                title="❌ Erro",
                description="Não foi possível carregar os clipes.",
                color=0xff0000
            )
    
    async def cleanup_old_clips(self, days: int = 30):
        """Remove clipes antigos do storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_clips = self.storage.get_clips()
            
            clips_to_remove = []
            for clip in all_clips:
                clip_date = datetime.fromisoformat(clip['created_at'])
                if clip_date < cutoff_date:
                    clips_to_remove.append(clip['id'])
            
            # Remover clipes antigos
            for clip_id in clips_to_remove:
                self.storage.remove_clip(clip_id)
            
            logger.info(f"Removidos {len(clips_to_remove)} clipes antigos (>{days} dias)")
            return len(clips_to_remove)
            
        except Exception as e:
            logger.error(f"Erro ao limpar clipes antigos: {e}")
            return 0
    
    async def get_clips_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos clipes"""
        try:
            all_clips = self.storage.get_clips()
            
            # Estatísticas básicas
            total_clips = len(all_clips)
            
            # Clipes por jogador
            clips_by_player = {}
            for clip in all_clips:
                player_name = clip.get('player_name', 'Desconhecido')
                clips_by_player[player_name] = clips_by_player.get(player_name, 0) + 1
            
            # Top 5 jogadores com mais clipes
            top_players = sorted(
                clips_by_player.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Clipes por período
            now = datetime.now()
            clips_last_7_days = sum(
                1 for clip in all_clips
                if datetime.fromisoformat(clip['created_at']) > now - timedelta(days=7)
            )
            
            clips_last_30_days = sum(
                1 for clip in all_clips
                if datetime.fromisoformat(clip['created_at']) > now - timedelta(days=30)
            )
            
            return {
                'total_clips': total_clips,
                'clips_last_7_days': clips_last_7_days,
                'clips_last_30_days': clips_last_30_days,
                'top_players': top_players,
                'unique_players': len(clips_by_player)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de clipes: {e}")
            return {}
    
    def is_medal_url(self, url: str) -> bool:
        """Verifica se uma URL é do Medal"""
        for pattern in self.medal_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
    
    async def process_medal_clip(self, message: discord.Message) -> bool:
        """Método de compatibilidade - redireciona para process_message"""
        return await self.process_message(message)
    
    async def manual_add_clip(self, user_id: str, url: str, description: str = "") -> bool:
        """Adiciona clipe manualmente"""
        try:
            if not self.is_medal_url(url):
                return False
            
            clip_id = self._extract_clip_id(url)
            
            # Verificar se já existe
            if clip_id in self.processed_clips:
                return False
            
            # Buscar dados do jogador
            player_data = self.storage.get_player(user_id)
            
            clip_data = {
                'id': clip_id,
                'url': url,
                'player_id': user_id if player_data else None,
                'player_name': player_data.get('pubg_name', 'Desconhecido') if player_data else 'Desconhecido',
                'discord_user': user_id,
                'discord_username': 'Manual',
                'channel_id': 'manual',
                'message_id': 'manual',
                'created_at': datetime.now().isoformat(),
                'metadata': {
                    'manual_add': True,
                    'description': description
                },
                'guild_id': None
            }
            
            self.storage.add_clip(clip_data)
            self.processed_clips.add(clip_id)
            
            logger.info(f"Clipe adicionado manualmente: {clip_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar clipe manualmente: {e}")
            return False