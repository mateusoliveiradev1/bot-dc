#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Canais de Música Automáticos para Discord
Cria canais de voz dedicados para música com controles automáticos

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import asyncio
import logging
import json
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger('HawkBot.MusicChannels')

class MusicChannelsSystem:
    """Sistema principal de canais de música automáticos"""
    
    def __init__(self, bot, storage, music_system):
        self.bot = bot
        self.storage = storage
        self.music_system = music_system
        
        # Configurações
        self.config = self.load_config()
        
        # Canais de música ativos
        self.music_channels: Dict[int, Dict] = {}  # channel_id -> info
        
        # Configurações de canais de música
        self.music_channel_config = {
            "auto_create": True,
            "max_music_channels": 5,
            "music_channel_prefix": "🎵・",
            "auto_delete_empty": True,
            "empty_timeout_minutes": 10,
            "default_bitrate": 128000,  # 128 kbps
            "default_user_limit": 10
        }
        
        # Canais trigger para música
        self.music_trigger_channels: Set[int] = set()
        
        # Controles de música por canal
        self.channel_controls: Dict[int, Dict] = {}  # channel_id -> controls_info
        
        # Task de limpeza
        self.cleanup_task = None
        
        logger.info("Sistema de Canais de Música inicializado")
    
    def load_config(self) -> dict:
        """Carrega configurações do arquivo JSON"""
        try:
            with open('music_channels_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Criar configuração padrão
            default_config = {
                "music_channels": {
                    "enabled": True,
                    "auto_create": True,
                    "max_music_channels": 5,
                    "music_channel_prefix": "🎵・",
                    "auto_delete_empty": True,
                    "empty_timeout_minutes": 10,
                    "default_bitrate": 128000,
                    "default_user_limit": 10,
                    "quality_presets": {
                        "low": 64000,
                        "medium": 128000,
                        "high": 256000,
                        "ultra": 384000
                    }
                },
                "trigger_channels": [],
                "voice_categories": {
                    "music_category_name": "🎵・Canais de Música"
                },
                "auto_controls": {
                    "enabled": True,
                    "show_now_playing": True,
                    "show_queue_info": True,
                    "auto_update_channel_name": True,
                    "update_interval_seconds": 30
                }
            }
            
            with open('music_channels_config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return {}
    
    def save_config(self):
        """Salva configurações no arquivo JSON"""
        try:
            with open('music_channels_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    async def setup_music_channels(self, guild: discord.Guild):
        """Configura canais de música no servidor"""
        try:
            # Criar categoria para canais de música
            music_category_name = self.config.get('voice_categories', {}).get('music_category_name', '🎵・Canais de Música')
            music_category = discord.utils.get(guild.categories, name=music_category_name)
            
            if not music_category:
                music_category = await guild.create_category(
                    name=music_category_name,
                    reason="Configuração automática de canais de música"
                )
                logger.info(f"Categoria de música criada: {music_category.name}")
            
            # Criar canal trigger principal
            trigger_channel_name = "🎵・Criar Sala de Música"
            trigger_channel = discord.utils.get(music_category.voice_channels, name=trigger_channel_name)
            
            if not trigger_channel:
                trigger_channel = await guild.create_voice_channel(
                    name=trigger_channel_name,
                    category=music_category,
                    bitrate=self.config.get('music_channels', {}).get('default_bitrate', 128000),
                    user_limit=1,  # Apenas para trigger
                    reason="Canal trigger para criação de salas de música"
                )
                logger.info(f"Canal trigger de música criado: {trigger_channel.name}")
            
            # Adicionar às configurações
            if trigger_channel.id not in self.music_trigger_channels:
                self.music_trigger_channels.add(trigger_channel.id)
                
                # Salvar na configuração
                if 'trigger_channels' not in self.config:
                    self.config['trigger_channels'] = []
                if trigger_channel.id not in self.config['trigger_channels']:
                    self.config['trigger_channels'].append(trigger_channel.id)
                    self.save_config()
            
            logger.info("Canais de música configurados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar canais de música: {e}")
    
    async def create_music_channel(self, member: discord.Member, trigger_channel: discord.VoiceChannel) -> Optional[discord.VoiceChannel]:
        """Cria um novo canal de música temporário"""
        try:
            guild = trigger_channel.guild
            
            # Verificar limite de canais
            active_count = len([ch for ch in self.music_channels.values() if ch.get('active', True)])
            max_channels = self.config.get('music_channels', {}).get('max_music_channels', 5)
            
            if active_count >= max_channels:
                logger.warning(f"Limite de canais de música atingido: {active_count}/{max_channels}")
                return None
            
            # Nome do canal
            prefix = self.config.get('music_channels', {}).get('music_channel_prefix', '🎵・')
            channel_name = f"{prefix}{member.display_name}'s Music"
            
            # Criar canal
            music_channel = await guild.create_voice_channel(
                name=channel_name,
                category=trigger_channel.category,
                bitrate=self.config.get('music_channels', {}).get('default_bitrate', 128000),
                user_limit=self.config.get('music_channels', {}).get('default_user_limit', 10),
                reason=f"Canal de música criado por {member.display_name}"
            )
            
            # Configurar permissões especiais para o criador
            await music_channel.set_permissions(
                member,
                manage_channels=True,
                move_members=True,
                mute_members=True,
                deafen_members=True
            )
            
            # Mover o membro para o novo canal
            await member.move_to(music_channel)
            
            # Registrar canal
            self.music_channels[music_channel.id] = {
                'creator': member.id,
                'created_at': datetime.now(),
                'active': True,
                'last_activity': datetime.now(),
                'auto_controls': self.config.get('auto_controls', {}).get('enabled', True)
            }
            
            # Iniciar controles automáticos se habilitado
            if self.config.get('auto_controls', {}).get('enabled', True):
                await self.setup_channel_controls(music_channel)
            
            logger.info(f"Canal de música criado: {music_channel.name} por {member.display_name}")
            return music_channel
            
        except Exception as e:
            logger.error(f"Erro ao criar canal de música: {e}")
            return None
    
    async def setup_channel_controls(self, channel: discord.VoiceChannel):
        """Configura controles automáticos para o canal de música"""
        try:
            # Criar embed de controle
            embed = discord.Embed(
                title="🎵 Controles de Música",
                description="Use os comandos de música neste canal!",
                color=0x1DB954  # Cor do Spotify
            )
            
            embed.add_field(
                name="📋 Comandos Disponíveis",
                value="`/play` - Tocar música\n"
                      "`/pause` - Pausar/Retomar\n"
                      "`/skip` - Pular música\n"
                      "`/queue` - Ver fila\n"
                      "`/volume` - Ajustar volume\n"
                      "`/stop` - Parar música",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Informações",
                value="• Este canal será excluído automaticamente quando vazio\n"
                      "• O criador tem permissões especiais de gerenciamento\n"
                      "• Qualidade de áudio otimizada para música",
                inline=False
            )
            
            # Enviar para canal de texto relacionado (se existir)
            text_channel = discord.utils.get(channel.guild.text_channels, name=f"música-{channel.name.lower().replace(' ', '-')}")
            if not text_channel:
                # Criar canal de texto temporário se não existir
                text_channel = await channel.guild.create_text_channel(
                    name=f"música-{channel.name.lower().replace(' ', '-').replace('🎵・', '')}",
                    category=channel.category,
                    topic=f"Chat para o canal de música {channel.name}",
                    reason="Canal de texto para controles de música"
                )
            
            control_message = await text_channel.send(embed=embed)
            
            # Registrar controles
            self.channel_controls[channel.id] = {
                'text_channel': text_channel.id,
                'control_message': control_message.id,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro ao configurar controles do canal: {e}")
    
    async def update_channel_info(self, channel: discord.VoiceChannel):
        """Atualiza informações do canal com base na música atual"""
        try:
            if not self.config.get('auto_controls', {}).get('auto_update_channel_name', True):
                return
            
            # Obter informações da música atual
            queue_info = self.music_system.get_queue_info(channel.guild.id)
            
            if queue_info['current_song']:
                current_song = queue_info['current_song']
                prefix = self.config.get('music_channels', {}).get('music_channel_prefix', '🎵・')
                
                # Truncar título se muito longo
                title = current_song.title
                if len(title) > 30:
                    title = title[:27] + "..."
                
                new_name = f"{prefix}{title}"
                
                if channel.name != new_name:
                    await channel.edit(name=new_name, reason="Atualização automática com música atual")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar informações do canal: {e}")
    
    async def check_empty_music_channel(self, channel: discord.VoiceChannel):
        """Verifica se canal de música está vazio e agenda exclusão"""
        try:
            if channel.id not in self.music_channels:
                return
            
            if len(channel.members) == 0:
                # Agendar exclusão após timeout
                timeout_minutes = self.config.get('music_channels', {}).get('empty_timeout_minutes', 10)
                await asyncio.sleep(timeout_minutes * 60)
                
                # Verificar novamente se ainda está vazio
                channel = self.bot.get_channel(channel.id)
                if channel and len(channel.members) == 0:
                    await self.delete_music_channel(channel)
            
        except Exception as e:
            logger.error(f"Erro ao verificar canal vazio: {e}")
    
    async def delete_music_channel(self, channel: discord.VoiceChannel):
        """Exclui canal de música e limpa recursos"""
        try:
            channel_id = channel.id
            
            # Parar música se estiver tocando
            await self.music_system.stop_music(channel.guild.id)
            
            # Excluir canal de texto relacionado se existir
            if channel_id in self.channel_controls:
                text_channel_id = self.channel_controls[channel_id].get('text_channel')
                if text_channel_id:
                    text_channel = self.bot.get_channel(text_channel_id)
                    if text_channel:
                        await text_channel.delete(reason="Canal de música excluído")
                
                del self.channel_controls[channel_id]
            
            # Excluir canal de voz
            await channel.delete(reason="Canal de música vazio - exclusão automática")
            
            # Limpar registros
            if channel_id in self.music_channels:
                del self.music_channels[channel_id]
            
            logger.info(f"Canal de música excluído: {channel.name}")
            
        except Exception as e:
            logger.error(f"Erro ao excluir canal de música: {e}")
    
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Evento chamado quando alguém entra/sai de um canal de voz"""
        try:
            # Usuário entrou em um canal trigger de música
            if after.channel and after.channel.id in self.music_trigger_channels:
                music_channel = await self.create_music_channel(member, after.channel)
                if music_channel:
                    # Atualizar atividade
                    self.music_channels[music_channel.id]['last_activity'] = datetime.now()
            
            # Usuário saiu de um canal de música
            if before.channel and before.channel.id in self.music_channels:
                await self.check_empty_music_channel(before.channel)
            
            # Usuário entrou em um canal de música (atualizar atividade)
            if after.channel and after.channel.id in self.music_channels:
                self.music_channels[after.channel.id]['last_activity'] = datetime.now()
                
                # Atualizar informações do canal se música estiver tocando
                if self.config.get('auto_controls', {}).get('enabled', True):
                    await self.update_channel_info(after.channel)
            
        except Exception as e:
            logger.error(f"Erro no evento voice_state_update (música): {e}")
    
    async def add_music_trigger_channel(self, channel_id: int) -> bool:
        """Adiciona um canal como trigger para música"""
        try:
            if channel_id not in self.music_trigger_channels:
                self.music_trigger_channels.add(channel_id)
                
                # Salvar na configuração
                if 'trigger_channels' not in self.config:
                    self.config['trigger_channels'] = []
                if channel_id not in self.config['trigger_channels']:
                    self.config['trigger_channels'].append(channel_id)
                    self.save_config()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao adicionar canal trigger de música: {e}")
            return False
    
    async def remove_music_trigger_channel(self, channel_id: int) -> bool:
        """Remove um canal dos triggers de música"""
        try:
            if channel_id in self.music_trigger_channels:
                self.music_trigger_channels.remove(channel_id)
                
                # Remover da configuração
                if 'trigger_channels' in self.config and channel_id in self.config['trigger_channels']:
                    self.config['trigger_channels'].remove(channel_id)
                    self.save_config()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao remover canal trigger de música: {e}")
            return False
    
    async def cleanup_loop(self):
        """Loop de limpeza automática"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutos
                
                current_time = datetime.now()
                channels_to_remove = []
                
                for channel_id, info in self.music_channels.items():
                    # Verificar canais inativos há muito tempo
                    if current_time - info['last_activity'] > timedelta(hours=1):
                        channel = self.bot.get_channel(channel_id)
                        if channel and len(channel.members) == 0:
                            channels_to_remove.append(channel)
                
                # Remover canais inativos
                for channel in channels_to_remove:
                    await self.delete_music_channel(channel)
                
            except Exception as e:
                logger.error(f"Erro no loop de limpeza de música: {e}")
    
    async def start_cleanup_task(self):
        """Inicia task de limpeza automática"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        self.cleanup_task = asyncio.create_task(self.cleanup_loop())
        logger.info("Task de limpeza de canais de música iniciada")
    
    @property
    def active_channels(self) -> Dict[int, Dict]:
        """Retorna canais de música ativos"""
        return {ch_id: info for ch_id, info in self.music_channels.items() if info.get('active', True)}
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema"""
        return {
            "music_channels_total": len(self.music_channels),
            "active_channels": len(self.active_channels),
            "trigger_channels": len(self.music_trigger_channels),
            "channels_with_controls": len(self.channel_controls),
            "config_loaded": bool(self.config)
        }
    
    async def stop(self):
        """Para o sistema e limpa recursos"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        logger.info("Sistema de Canais de Música finalizado")