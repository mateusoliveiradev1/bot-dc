#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Canais Dinâmicos para Discord
Cria voice channels temporários e canais organizados por patente

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

logger = logging.getLogger('HawkBot.DynamicChannels')

class DynamicChannelsSystem:
    """Sistema principal de canais dinâmicos"""
    
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        
        # Configurações
        self.config = self.load_config()
        
        # Canais temporários ativos
        self.temp_channels: Dict[int, Dict] = {}  # channel_id -> info
        
        # Canais por patente
        self.rank_channels: Dict[str, List[int]] = defaultdict(list)  # rank -> [channel_ids]
        
        # Configurações de canais temporários
        self.temp_channel_config = {
            "auto_delete_empty": True,
            "empty_timeout_minutes": 5,
            "max_temp_channels": 20,
            "temp_channel_prefix": "🎮・",
            "creator_permissions": True
        }
        
        # Configurações de canais por patente
        self.rank_channel_config = {
            "auto_create": True,
            "min_members_per_rank": 3,
            "rank_prefixes": {
                "Predador": "🔥・",
                "Diamante": "💎・",
                "Ouro": "🥇・",
                "Prata": "🥈・",
                "Bronze": "🥉・"
            }
        }
        
        # Canais de criação (trigger channels)
        self.trigger_channels: Set[int] = set()
        
        # Task de limpeza
        self.cleanup_task = None
        
        logger.info("Sistema de Canais Dinâmicos inicializado")
    
    def load_config(self) -> dict:
        """Carrega configurações do arquivo JSON"""
        try:
            with open('dynamic_channels_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Criar configuração padrão
            default_config = {
                "temp_channels": {
                    "enabled": True,
                    "auto_delete_empty": True,
                    "empty_timeout_minutes": 5,
                    "max_temp_channels": 20,
                    "temp_channel_prefix": "🎮・",
                    "creator_permissions": True
                },
                "rank_channels": {
                    "enabled": True,
                    "auto_create": True,
                    "min_members_per_rank": 3,
                    "rank_prefixes": {
                        "Predador": "🔥・",
                        "Diamante": "💎・",
                        "Ouro": "🥇・",
                        "Prata": "🥈・",
                        "Bronze": "🥉・"
                    }
                },
                "trigger_channels": [],
                "voice_categories": {
                    "temp_category_name": "🎮・Salas Temporárias",
                    "rank_category_name": "🏆・Canais por Patente"
                }
            }
            
            with open('dynamic_channels_config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return {}
    
    def save_config(self):
        """Salva configurações no arquivo JSON"""
        try:
            with open('dynamic_channels_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    async def setup_trigger_channels(self, guild: discord.Guild):
        """Configura canais de trigger para criação automática"""
        try:
            # Buscar ou criar categoria para salas temporárias
            temp_category_name = self.config.get('voice_categories', {}).get('temp_category_name', '🎮・Salas Temporárias')
            temp_category = discord.utils.get(guild.categories, name=temp_category_name)
            
            if not temp_category:
                temp_category = await guild.create_category(
                    name=temp_category_name,
                    reason="Configuração automática - Canais Dinâmicos"
                )
                logger.info(f"Categoria '{temp_category_name}' criada")
            
            # Criar canal trigger para salas temporárias
            trigger_channel_name = "➕・Criar Sala"
            trigger_channel = discord.utils.get(guild.voice_channels, name=trigger_channel_name)
            
            if not trigger_channel:
                trigger_channel = await guild.create_voice_channel(
                    name=trigger_channel_name,
                    category=temp_category,
                    user_limit=1,
                    reason="Canal trigger para salas temporárias"
                )
                logger.info(f"Canal trigger '{trigger_channel_name}' criado")
            
            # Adicionar à lista de trigger channels
            self.trigger_channels.add(trigger_channel.id)
            
            # Configurar canais por patente se habilitado
            if self.config.get('rank_channels', {}).get('enabled', True):
                await self.setup_rank_channels(guild)
            
            logger.info("Canais dinâmicos configurados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar canais dinâmicos: {e}")
    
    async def setup_rank_channels(self, guild: discord.Guild):
        """Configura canais organizados por patente"""
        try:
            # Buscar ou criar categoria para canais por patente
            rank_category_name = self.config.get('voice_categories', {}).get('rank_category_name', '🏆・Canais por Patente')
            rank_category = discord.utils.get(guild.categories, name=rank_category_name)
            
            if not rank_category:
                rank_category = await guild.create_category(
                    name=rank_category_name,
                    reason="Configuração automática - Canais por Patente"
                )
                logger.info(f"Categoria '{rank_category_name}' criada")
            
            # Obter prefixos das patentes
            rank_prefixes = self.config.get('rank_channels', {}).get('rank_prefixes', {})
            
            # Criar canais para cada patente
            for rank, prefix in rank_prefixes.items():
                channel_name = f"{prefix}{rank} Squad"
                existing_channel = discord.utils.get(guild.voice_channels, name=channel_name)
                
                if not existing_channel:
                    rank_channel = await guild.create_voice_channel(
                        name=channel_name,
                        category=rank_category,
                        user_limit=4,  # Limite padrão para squads
                        reason=f"Canal automático para patente {rank}"
                    )
                    
                    # Configurar permissões baseadas na patente
                    await self.setup_rank_channel_permissions(guild, rank_channel, rank)
                    
                    self.rank_channels[rank].append(rank_channel.id)
                    logger.info(f"Canal '{channel_name}' criado")
                else:
                    self.rank_channels[rank].append(existing_channel.id)
            
        except Exception as e:
            logger.error(f"Erro ao configurar canais por patente: {e}")
    
    async def setup_rank_channel_permissions(self, guild: discord.Guild, channel: discord.VoiceChannel, rank: str):
        """Configura permissões específicas para canais de patente"""
        try:
            # Buscar role da patente
            rank_role = discord.utils.get(guild.roles, name=rank)
            
            if rank_role:
                # Dar prioridade para membros da mesma patente
                await channel.set_permissions(
                    rank_role,
                    priority_speaker=True,
                    reason=f"Prioridade para membros {rank}"
                )
                
                logger.info(f"Permissões configuradas para canal {rank}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar permissões do canal {rank}: {e}")
    
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Evento chamado quando alguém entra/sai de um canal de voz"""
        try:
            # Usuário entrou em um canal
            if after.channel and after.channel.id in self.trigger_channels:
                await self.create_temp_channel(member, after.channel)
            
            # Usuário saiu de um canal temporário
            if before.channel and before.channel.id in self.temp_channels:
                await self.check_empty_temp_channel(before.channel)
            
            # Verificar canais por patente
            if after.channel:
                await self.manage_rank_channels(member, after.channel)
            
        except Exception as e:
            logger.error(f"Erro no evento voice_state_update: {e}")
    
    async def create_temp_channel(self, member: discord.Member, trigger_channel: discord.VoiceChannel):
        """Cria um canal temporário para o membro"""
        try:
            # Verificar limite de canais temporários
            if len(self.temp_channels) >= self.temp_channel_config["max_temp_channels"]:
                logger.warning("Limite de canais temporários atingido")
                return
            
            # Nome do canal temporário
            prefix = self.temp_channel_config["temp_channel_prefix"]
            channel_name = f"{prefix}{member.display_name}'s Squad"
            
            # Criar canal temporário
            temp_channel = await trigger_channel.category.create_voice_channel(
                name=channel_name,
                user_limit=4,
                reason=f"Canal temporário criado por {member.display_name}"
            )
            
            # Configurar permissões do criador
            if self.temp_channel_config["creator_permissions"]:
                await temp_channel.set_permissions(
                    member,
                    manage_channels=True,
                    manage_permissions=True,
                    priority_speaker=True,
                    reason="Permissões do criador do canal"
                )
            
            # Mover membro para o canal temporário
            await member.move_to(temp_channel)
            
            # Registrar canal temporário
            self.temp_channels[temp_channel.id] = {
                "creator_id": member.id,
                "created_at": datetime.now(),
                "name": channel_name
            }
            
            logger.info(f"Canal temporário '{channel_name}' criado por {member.display_name}")
            
        except Exception as e:
            logger.error(f"Erro ao criar canal temporário: {e}")
    
    async def check_empty_temp_channel(self, channel: discord.VoiceChannel):
        """Verifica se um canal temporário está vazio e agenda sua remoção"""
        try:
            if not channel.members:  # Canal vazio
                # Agendar remoção após timeout
                timeout_minutes = self.temp_channel_config["empty_timeout_minutes"]
                await asyncio.sleep(timeout_minutes * 60)
                
                # Verificar novamente se ainda está vazio
                channel = self.bot.get_channel(channel.id)
                if channel and not channel.members:
                    await self.delete_temp_channel(channel)
            
        except Exception as e:
            logger.error(f"Erro ao verificar canal vazio: {e}")
    
    async def delete_temp_channel(self, channel: discord.VoiceChannel):
        """Remove um canal temporário"""
        try:
            channel_info = self.temp_channels.get(channel.id)
            if channel_info:
                await channel.delete(reason="Canal temporário vazio - remoção automática")
                del self.temp_channels[channel.id]
                logger.info(f"Canal temporário '{channel_info['name']}' removido automaticamente")
            
        except Exception as e:
            logger.error(f"Erro ao remover canal temporário: {e}")
    
    async def manage_rank_channels(self, member: discord.Member, channel: discord.VoiceChannel):
        """Gerencia canais baseados na patente do membro"""
        try:
            # Verificar se o membro tem uma patente
            member_rank = self.get_member_rank(member)
            if not member_rank:
                return
            
            # Verificar se precisa criar mais canais para esta patente
            rank_channels = self.rank_channels.get(member_rank, [])
            
            # Contar membros da mesma patente em canais de voz
            same_rank_members = 0
            for ch_id in rank_channels:
                ch = self.bot.get_channel(ch_id)
                if ch and isinstance(ch, discord.VoiceChannel):
                    same_rank_members += len([m for m in ch.members if self.get_member_rank(m) == member_rank])
            
            # Criar canal adicional se necessário
            min_members = self.config.get('rank_channels', {}).get('min_members_per_rank', 3)
            if same_rank_members >= min_members * len(rank_channels):
                await self.create_additional_rank_channel(member.guild, member_rank)
            
        except Exception as e:
            logger.error(f"Erro ao gerenciar canais por patente: {e}")
    
    def get_member_rank(self, member: discord.Member) -> Optional[str]:
        """Obtém a patente de um membro baseada em seus cargos"""
        rank_names = ["Predador", "Diamante", "Ouro", "Prata", "Bronze"]
        
        for role in member.roles:
            if role.name in rank_names:
                return role.name
        
        return None
    
    async def create_additional_rank_channel(self, guild: discord.Guild, rank: str):
        """Cria um canal adicional para uma patente específica"""
        try:
            # Buscar categoria de canais por patente
            rank_category_name = self.config.get('voice_categories', {}).get('rank_category_name', '🏆・Canais por Patente')
            rank_category = discord.utils.get(guild.categories, name=rank_category_name)
            
            if not rank_category:
                return
            
            # Obter prefixo da patente
            rank_prefixes = self.config.get('rank_channels', {}).get('rank_prefixes', {})
            prefix = rank_prefixes.get(rank, "🎮・")
            
            # Contar canais existentes para esta patente
            existing_count = len(self.rank_channels[rank])
            channel_name = f"{prefix}{rank} Squad {existing_count + 1}"
            
            # Criar novo canal
            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=rank_category,
                user_limit=4,
                reason=f"Canal adicional para patente {rank}"
            )
            
            # Configurar permissões
            await self.setup_rank_channel_permissions(guild, new_channel, rank)
            
            # Adicionar à lista
            self.rank_channels[rank].append(new_channel.id)
            
            logger.info(f"Canal adicional '{channel_name}' criado para patente {rank}")
            
        except Exception as e:
            logger.error(f"Erro ao criar canal adicional para {rank}: {e}")
    
    async def start_cleanup_task(self):
        """Inicia task de limpeza automática"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        self.cleanup_task = asyncio.create_task(self.cleanup_loop())
        logger.info("Task de limpeza de canais dinâmicos iniciada")
    
    async def cleanup_loop(self):
        """Loop de limpeza automática"""
        while True:
            try:
                await asyncio.sleep(300)  # Verificar a cada 5 minutos
                await self.cleanup_empty_channels()
                await self.cleanup_old_temp_channels()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro na limpeza automática: {e}")
    
    async def cleanup_empty_channels(self):
        """Remove canais temporários vazios"""
        try:
            channels_to_remove = []
            
            for channel_id, info in self.temp_channels.items():
                channel = self.bot.get_channel(channel_id)
                if not channel or not channel.members:
                    channels_to_remove.append(channel_id)
            
            for channel_id in channels_to_remove:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await self.delete_temp_channel(channel)
            
        except Exception as e:
            logger.error(f"Erro na limpeza de canais vazios: {e}")
    
    async def cleanup_old_temp_channels(self):
        """Remove canais temporários muito antigos"""
        try:
            max_age_hours = 24  # Máximo 24 horas
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            channels_to_remove = []
            
            for channel_id, info in self.temp_channels.items():
                if info['created_at'] < cutoff_time:
                    channels_to_remove.append(channel_id)
            
            for channel_id in channels_to_remove:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await self.delete_temp_channel(channel)
            
        except Exception as e:
            logger.error(f"Erro na limpeza de canais antigos: {e}")
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema"""
        return {
            "temp_channels_active": len(self.temp_channels),
            "rank_channels_total": sum(len(channels) for channels in self.rank_channels.values()),
            "trigger_channels": len(self.trigger_channels),
            "config_loaded": bool(self.config)
        }
    
    async def stop(self):
        """Para o sistema e limpa recursos"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        logger.info("Sistema de Canais Dinâmicos finalizado")