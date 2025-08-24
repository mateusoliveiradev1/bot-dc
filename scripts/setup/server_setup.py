#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Configuração Automática do Servidor
Cria automaticamente toda a estrutura do servidor Hawk Esports

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('HawkBot.ServerSetup')

class ServerSetup:
    """Classe responsável pela configuração automática do servidor"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Estrutura completa do servidor
        self.server_structure = {
            "categories": {
                "📌・Informações": {
                    "channels": [
                        {"name": "📜・regras", "type": "text", "topic": "Regras oficiais do clã Hawk Esports"},
                        {"name": "📢・anúncios", "type": "text", "topic": "Anúncios importantes do clã"},
                        {"name": "📊・resultados", "type": "text", "topic": "Resultados de partidas e torneios"},
                        {"name": "📆・calendário", "type": "text", "topic": "Agenda de eventos e treinos"}
                    ]
                },
                "💬・Comunidade": {
                    "channels": [
                        {"name": "💭・geral", "type": "text", "topic": "Conversa geral do clã Hawk Esports"},
                        {"name": "📷・clipes", "type": "text", "topic": "Compartilhe seus melhores clipes PUBG"},
                        {"name": "🎉・eventos", "type": "text", "topic": "Organização de eventos e torneios"}
                    ]
                },
                "🎮・Game": {
                    "channels": [
                        {"name": "🎯・scrims", "type": "text", "topic": "Organização de scrimmages"},
                        {"name": "🏆・ranking", "type": "text", "topic": "Sistema completo de rankings e leaderboards"},
                        {"name": "📊・estatísticas", "type": "text", "topic": "Estatísticas detalhadas dos membros"}
                    ]
                },
                "🎙・Voz": {
                    "channels": [
                        {"name": "Squad 1", "type": "voice", "limit": 4},
                        {"name": "Squad 2", "type": "voice", "limit": 4},
                        {"name": "Squad 3", "type": "voice", "limit": 4},
                        {"name": "Treino", "type": "voice", "limit": 8},
                        {"name": "Estratégia Líder", "type": "voice", "limit": 10}
                    ]
                },
                "🔒・Privados": {
                    "channels": [
                        {"name": "Líder", "type": "text", "topic": "Canal exclusivo da liderança", "private": True},
                        {"name": "Co-Líder", "type": "text", "topic": "Canal dos co-líderes", "private": True},
                        {"name": "Staff", "type": "text", "topic": "Canal da equipe administrativa", "private": True}
                    ]
                },
                "🎵・Música": {
                    "channels": [
                        {"name": "🎵・música", "type": "text", "topic": "Comandos de música e controle do bot"},
                        {"name": "🎧・Música Geral", "type": "voice", "limit": 10},
                        {"name": "🎤・Karaokê", "type": "voice", "limit": 8}
                    ]
                },
                "📋・Registro": {
                    "channels": [
                        {"name": "📋・registro", "type": "text", "topic": "Canal para novos membros registrarem seu nick PUBG"}
                    ]
                }
            },
            "roles": {
                "ranked": [
                    {"name": "Predador", "color": 0xFF0000, "hoist": True},
                    {"name": "Diamante", "color": 0x00FFFF, "hoist": True},
                    {"name": "Ouro", "color": 0xFFD700, "hoist": True},
                    {"name": "Prata", "color": 0xC0C0C0, "hoist": True},
                    {"name": "Bronze", "color": 0xCD7F32, "hoist": True}
                ],
                "mm": [
                    {"name": "Mestre MM", "color": 0x8A2BE2, "hoist": True},
                    {"name": "Diamante MM", "color": 0x4169E1, "hoist": True},
                    {"name": "Ouro MM", "color": 0xFFA500, "hoist": True},
                    {"name": "Prata MM", "color": 0x808080, "hoist": True},
                    {"name": "Bronze MM", "color": 0xA0522D, "hoist": True}
                ],
                "hierarchy": [
                    {"name": "Líder", "color": 0xFF1493, "hoist": True, "permissions": "admin"},
                    {"name": "Co-Líder", "color": 0xFF69B4, "hoist": True, "permissions": "mod"},
                    {"name": "Membro", "color": 0x32CD32, "hoist": True},
                    {"name": "Recruta", "color": 0x90EE90, "hoist": True},
                    {"name": "Inativo", "color": 0x696969, "hoist": False}
                ],
                "special": [
                    {"name": "Acesso liberado", "color": 0x00FF00, "hoist": False},
                    {"name": "Não Registrado", "color": 0xFF6B6B, "hoist": False}
                ]
            }
        }
    
    async def setup_complete_server(self, guild: discord.Guild) -> bool:
        """Configura completamente o servidor com todas as categorias, canais e roles"""
        try:
            logger.info(f"Iniciando configuração completa do servidor {guild.name}")
            
            # Criar roles primeiro
            roles_created = await self._create_all_roles(guild)
            logger.info(f"Criadas {roles_created} roles")
            
            # Criar categorias e canais
            categories_created = await self._create_all_categories_and_channels(guild)
            logger.info(f"Criadas {categories_created} categorias")
            
            # Configurar permissões especiais
            await self._setup_special_permissions(guild)
            
            # Enviar mensagem de boas-vindas no canal de registro
            await self._send_welcome_message(guild)
            
            # Popular canais com conteúdo detalhado
            await self._populate_channel_content(guild)
            
            logger.info("Configuração do servidor concluída com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro na configuração do servidor: {e}")
            return False
    
    async def _create_all_roles(self, guild: discord.Guild) -> int:
        """Cria todas as roles necessárias"""
        roles_created = 0
        existing_roles = [role.name.lower() for role in guild.roles]
        
        # Criar roles por categoria
        for category, roles_list in self.server_structure["roles"].items():
            for role_data in roles_list:
                role_name = role_data["name"]
                
                # Verificar se role já existe
                if role_name.lower() in existing_roles:
                    logger.info(f"Role '{role_name}' já existe, pulando...")
                    continue
                
                try:
                    # Configurar permissões especiais
                    if role_data.get("permissions") == "admin":
                        permissions = discord.Permissions.all()
                    elif role_data.get("permissions") == "mod":
                        permissions = discord.Permissions(
                            manage_messages=True,
                            manage_channels=True,
                            kick_members=True,
                            ban_members=True,
                            manage_roles=True
                        )
                    else:
                        permissions = discord.Permissions()
                    
                    # Criar role
                    await guild.create_role(
                        name=role_name,
                        color=discord.Color(role_data["color"]),
                        hoist=role_data.get("hoist", False),
                        permissions=permissions,
                        reason="Configuração automática Hawk Esports"
                    )
                    
                    roles_created += 1
                    logger.info(f"Role '{role_name}' criada com sucesso")
                    
                except Exception as e:
                    logger.error(f"Erro ao criar role '{role_name}': {e}")
        
        return roles_created
    
    async def _create_all_categories_and_channels(self, guild: discord.Guild) -> int:
        """Cria todas as categorias e canais"""
        categories_created = 0
        existing_categories = [cat.name.lower() for cat in guild.categories]
        
        for category_name, category_data in self.server_structure["categories"].items():
            # Verificar se categoria já existe
            if category_name.lower() in existing_categories:
                logger.info(f"Categoria '{category_name}' já existe, pulando...")
                continue
            
            try:
                # Criar categoria
                category = await guild.create_category(
                    name=category_name,
                    reason="Configuração automática Hawk Esports"
                )
                categories_created += 1
                logger.info(f"Categoria '{category_name}' criada")
                
                # Criar canais da categoria
                await self._create_channels_in_category(guild, category, category_data["channels"])
                
            except Exception as e:
                logger.error(f"Erro ao criar categoria '{category_name}': {e}")
        
        return categories_created
    
    async def _create_channels_in_category(self, guild: discord.Guild, category: discord.CategoryChannel, channels_data: List[Dict]):
        """Cria canais dentro de uma categoria"""
        existing_channels = [ch.name.lower() for ch in guild.channels]
        
        for channel_data in channels_data:
            channel_name = channel_data["name"]
            
            # Verificar se canal já existe
            if channel_name.lower() in existing_channels:
                logger.info(f"Canal '{channel_name}' já existe, pulando...")
                continue
            
            try:
                if channel_data["type"] == "text":
                    # Criar canal de texto
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        topic=channel_data.get("topic", ""),
                        reason="Configuração automática Hawk Esports"
                    )
                    
                elif channel_data["type"] == "voice":
                    # Criar canal de voz
                    channel = await guild.create_voice_channel(
                        name=channel_name,
                        category=category,
                        user_limit=channel_data.get("limit", 0),
                        reason="Configuração automática Hawk Esports"
                    )
                
                # Configurar permissões especiais para canais privados
                if channel_data.get("private", False):
                    await self._setup_private_channel_permissions(guild, channel, channel_name)
                
                logger.info(f"Canal '{channel_name}' criado com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao criar canal '{channel_name}': {e}")
    
    async def _setup_private_channel_permissions(self, guild: discord.Guild, channel, channel_name: str):
        """Configura permissões para canais privados"""
        try:
            # Negar acesso para @everyone
            await channel.set_permissions(
                guild.default_role,
                read_messages=False,
                send_messages=False
            )
            
            # Permitir acesso baseado no nome do canal
            role_name = channel_name.split()[0]  # "Líder", "Co-Líder", "Staff"
            
            # Buscar role correspondente
            target_role = discord.utils.get(guild.roles, name=role_name)
            if target_role:
                await channel.set_permissions(
                    target_role,
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True
                )
                logger.info(f"Permissões configuradas para canal privado '{channel_name}'")
            
        except Exception as e:
            logger.error(f"Erro ao configurar permissões do canal '{channel_name}': {e}")
    
    async def _setup_special_permissions(self, guild: discord.Guild):
        """Configura permissões especiais do servidor com sistema de acesso limitado"""
        try:
            # Buscar roles necessárias
            acesso_role = discord.utils.get(guild.roles, name="Acesso liberado")
            nao_registrado_role = discord.utils.get(guild.roles, name="Não Registrado")
            
            if not acesso_role or not nao_registrado_role:
                logger.warning("Roles 'Acesso liberado' ou 'Não Registrado' não encontradas")
                return
            
            # === CANAIS PÚBLICOS (visíveis para todos) ===
            public_channels = [
                "📜・regras", "📢・anúncios", "📋・registro"
            ]
            
            for channel_name in public_channels:
                channel = discord.utils.get(guild.channels, name=channel_name)
                if channel and isinstance(channel, discord.TextChannel):
                    # @everyone pode ver mas não enviar mensagens
                    await channel.set_permissions(
                        guild.default_role,
                        read_messages=True,
                        send_messages=False,
                        add_reactions=True
                    )
                    
                    # Não registrados podem ver mas não enviar mensagens
                    await channel.set_permissions(
                        nao_registrado_role,
                        read_messages=True,
                        send_messages=False,
                        add_reactions=True
                    )
                    
                    # Registrados podem ver mas não enviar mensagens (exceto registro)
                    if channel_name == "📋・registro":
                        await channel.set_permissions(
                            acesso_role,
                            read_messages=True,
                            send_messages=True,
                            add_reactions=True
                        )
                    else:
                        await channel.set_permissions(
                            acesso_role,
                            read_messages=True,
                            send_messages=False,
                            add_reactions=True
                        )
            
            # === CANAIS RESTRITOS (apenas para registrados) ===
            restricted_channels = [
                "💭・geral", "📷・clipes", "🎉・eventos",
                "🎯・scrims", "📊・estatísticas", "🏆・ranking",
                "📊・resultados", "📆・calendário", "🎵・música"
            ]
            
            for channel_name in restricted_channels:
                channel = discord.utils.get(guild.channels, name=channel_name)
                if channel and isinstance(channel, discord.TextChannel):
                    # @everyone não pode ver
                    await channel.set_permissions(
                        guild.default_role,
                        read_messages=False,
                        send_messages=False
                    )
                    
                    # Não registrados não podem ver
                    await channel.set_permissions(
                        nao_registrado_role,
                        read_messages=False,
                        send_messages=False
                    )
                    
                    # Registrados podem ver e interagir
                    if channel_name in ["🏆・ranking", "📊・resultados", "📆・calendário"]:
                        # Canais somente leitura para registrados
                        await channel.set_permissions(
                            acesso_role,
                            read_messages=True,
                            send_messages=False,
                            add_reactions=True
                        )
                    else:
                        # Canais interativos para registrados
                        await channel.set_permissions(
                            acesso_role,
                            read_messages=True,
                            send_messages=True,
                            add_reactions=True
                        )
            
            # === CANAIS DE VOZ RESTRITOS ===
            voice_channels = [
                "Squad 1", "Squad 2", "Squad 3", "Treino", "Estratégia Líder",
                "🎧・Música Geral", "🎤・Karaokê"
            ]
            
            for channel_name in voice_channels:
                channel = discord.utils.get(guild.channels, name=channel_name)
                if channel and isinstance(channel, discord.VoiceChannel):
                    # @everyone não pode ver
                    await channel.set_permissions(
                        guild.default_role,
                        view_channel=False,
                        connect=False
                    )
                    
                    # Não registrados não podem ver
                    await channel.set_permissions(
                        nao_registrado_role,
                        view_channel=False,
                        connect=False
                    )
                    
                    # Registrados podem ver e conectar
                    await channel.set_permissions(
                        acesso_role,
                        view_channel=True,
                        connect=True,
                        speak=True
                    )
            
            # Configurar permissões do bot em todos os canais
            for channel in guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    await channel.set_permissions(
                        guild.me,
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        view_channel=True,
                        connect=True,
                        speak=True
                    )
            
            logger.info("Sistema de permissões com acesso limitado configurado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar permissões especiais: {e}")
    
    async def _send_welcome_message(self, guild: discord.Guild):
        """Envia mensagem de boas-vindas no canal de registro"""
        try:
            registro_channel = discord.utils.get(guild.channels, name="📋・registro")
            if not registro_channel:
                return
            
            embed = discord.Embed(
                title="🦅 Bem-vindo ao Hawk Esports!",
                description="**O clã mais dominante do PUBG!**\n\n" +
                           "Para ter acesso completo ao servidor, você precisa se registrar:",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="📋 Como se registrar:",
                value="Use o comando: `/register_pubg nome:<seu_nick> shard:<plataforma>`\n\n" +
                      "**Exemplo:** `/register_pubg nome:HawkPlayer shard:steam`",
                inline=False
            )
            
            embed.add_field(
                name="🌐 Plataformas disponíveis:",
                value="• `steam` - PC (Steam)\n" +
                      "• `psn` - PlayStation\n" +
                      "• `xbox` - Xbox\n" +
                      "• `kakao` - Kakao",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Após o registro:",
                value="• Acesso liberado a todos os canais\n" +
                      "• Cargo automático baseado em suas stats\n" +
                      "• Participação nos rankings do clã\n" +
                      "• Integração com seus clipes Medal",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Rumo à vitória! 🦅")
            
            await registro_channel.send(embed=embed)
            
            # Enviar conteúdo detalhado para outros canais
            await self._populate_channel_content(guild)
            
            logger.info("Mensagem de boas-vindas e conteúdo dos canais enviados")
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")
    
    async def _populate_channel_content(self, guild: discord.Guild):
        """Popula todos os canais com conteúdo detalhado"""
        try:
            # Enviar conteúdo para cada canal
            await self._send_rules_content(guild)
            await self._send_announcements_content(guild)
            await self._send_results_content(guild)
            await self._send_calendar_content(guild)
            await self._send_general_content(guild)
            await self._send_clips_content(guild)
            await self._send_events_content(guild)
            await self._send_scrims_content(guild)
            await self._send_ranking_content(guild)
            await self._send_stats_content(guild)
            await self._send_music_content(guild)
            
            logger.info("Conteúdo dos canais populado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao popular conteúdo dos canais: {e}")
    
    async def _send_music_content(self, guild: discord.Guild):
        """Envia conteúdo para o canal de música"""
        try:
            music_channel = discord.utils.get(guild.text_channels, name="🎵・música")
            if not music_channel:
                return
            
            # Embed principal do sistema de música
            embed = discord.Embed(
                title="🎵 Sistema de Música Hawk Esports",
                description="**Bem-vindo ao sistema de música mais avançado do Discord!**\n\n" +
                           "Use os comandos abaixo para controlar a música nos canais de voz.",
                color=0x9B59B6
            )
            
            # Comandos básicos
            embed.add_field(
                name="🎶 Comandos Básicos",
                value="`/play <música>` - Tocar música\n" +
                      "`/pause` - Pausar música\n" +
                      "`/resume` - Retomar música\n" +
                      "`/stop` - Parar música\n" +
                      "`/skip` - Pular música\n" +
                      "`/queue` - Ver fila de músicas",
                inline=True
            )
            
            # Comandos avançados
            embed.add_field(
                name="🎧 Comandos Avançados",
                value="`/nowplaying` - Música atual\n" +
                      "`/seek <tempo>` - Pular para tempo\n" +
                      "`/lyrics` - Letras da música\n" +
                      "`/history` - Histórico\n" +
                      "`/favorites` - Favoritas\n" +
                      "`/voteskip` - Votação para pular",
                inline=True
            )
            
            # Playlists
            embed.add_field(
                name="📋 Playlists",
                value="`/playlist create <nome>` - Criar playlist\n" +
                      "`/playlist add <música>` - Adicionar\n" +
                      "`/playlist show` - Ver playlists\n" +
                      "`/playlist play <nome>` - Tocar playlist\n" +
                      "`/playlist delete <nome>` - Deletar",
                inline=True
            )
            
            # Filtros de áudio
            embed.add_field(
                name="🎛️ Filtros de Áudio",
                value="`/filter bassboost` - Graves\n" +
                      "`/filter nightcore` - Nightcore\n" +
                      "`/filter vaporwave` - Vaporwave\n" +
                      "`/filter 8d` - Áudio 8D\n" +
                      "`/filter karaoke` - Karaokê\n" +
                      "`/filter clear` - Limpar filtros",
                inline=True
            )
            
            # Controles de volume
            embed.add_field(
                name="🔊 Volume e Controles",
                value="`/volume <0-100>` - Ajustar volume\n" +
                      "`/loop` - Repetir música\n" +
                      "`/shuffle` - Embaralhar fila\n" +
                      "`/clear` - Limpar fila\n" +
                      "`/disconnect` - Desconectar bot",
                inline=True
            )
            
            # Informações importantes
            embed.add_field(
                name="ℹ️ Informações Importantes",
                value="• Entre em um canal de voz antes de usar comandos\n" +
                      "• Suporte para YouTube, Spotify, SoundCloud\n" +
                      "• Qualidade de áudio premium\n" +
                      "• Sistema de votação democrático\n" +
                      "• Playlists públicas e privadas",
                inline=False
            )
            
            embed.set_footer(
                text="🎵 Hawk Esports Music System | Use os canais de voz dedicados para melhor experiência",
                icon_url=guild.icon.url if guild.icon else None
            )
            
            await music_channel.send(embed=embed)
            
            # Embed de canais recomendados
            channels_embed = discord.Embed(
                title="🎧 Canais de Música Recomendados",
                description="Use estes canais para a melhor experiência musical:",
                color=0x8E44AD
            )
            
            channels_embed.add_field(
                name="🎧 Música Geral",
                value="Canal principal para ouvir música em grupo\n" +
                      "**Limite:** 10 pessoas\n" +
                      "**Ideal para:** Sessões de música casual",
                inline=True
            )
            
            channels_embed.add_field(
                name="🎤 Karaokê",
                value="Canal dedicado para karaokê e canto\n" +
                      "**Limite:** 8 pessoas\n" +
                      "**Ideal para:** Karaokê e performances",
                inline=True
            )
            
            await music_channel.send(embed=channels_embed)
            
            logger.info("Conteúdo do canal de música enviado")
            
        except Exception as e:
            logger.error(f"Erro ao enviar conteúdo do canal de música: {e}")
    
    async def _send_rules_content(self, guild: discord.Guild):
        """Envia regras detalhadas para o canal de regras"""
        try:
            rules_channel = discord.utils.get(guild.channels, name="📜・regras")
            if not rules_channel:
                return
            
            embed = discord.Embed(
                title="📜 REGRAS OFICIAIS - HAWK ESPORTS",
                description="**Leia atentamente e siga todas as regras para manter um ambiente saudável!**",
                color=0xFF6B35
            )
            
            embed.add_field(
                name="🎯 1. RESPEITO E CONDUTA",
                value="• Trate todos com respeito e cordialidade\n" +
                      "• Proibido discriminação, assédio ou bullying\n" +
                      "• Mantenha conversas construtivas\n" +
                      "• Sem discussões políticas ou religiosas",
                inline=False
            )
            
            embed.add_field(
                name="🎮 2. GAMEPLAY E COMPETIÇÃO",
                value="• Proibido cheats, hacks ou exploits\n" +
                      "• Jogue sempre com fair play\n" +
                      "• Participe ativamente dos treinos\n" +
                      "• Comunique ausências com antecedência",
                inline=False
            )
            
            embed.add_field(
                name="💬 3. COMUNICAÇÃO",
                value="• Use os canais apropriados para cada assunto\n" +
                      "• Evite spam e flood de mensagens\n" +
                      "• Proibido conteúdo NSFW\n" +
                      "• Mantenha conversas em português",
                inline=False
            )
            
            embed.add_field(
                name="🏆 4. HIERARQUIA E ORGANIZAÇÃO",
                value="• Respeite a hierarquia do clã\n" +
                      "• Siga orientações da liderança\n" +
                      "• Participe das atividades do clã\n" +
                      "• Mantenha seu registro PUBG atualizado",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ 5. PUNIÇÕES",
                value="• **1ª Advertência:** Aviso verbal\n" +
                      "• **2ª Advertência:** Timeout 24h\n" +
                      "• **3ª Advertência:** Kick temporário\n" +
                      "• **Infrações graves:** Ban permanente",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Disciplina e Excelência | Última atualização: Janeiro 2025")
            
            await rules_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar regras: {e}")
    
    async def _send_announcements_content(self, guild: discord.Guild):
        """Envia template de anúncios"""
        try:
            announcements_channel = discord.utils.get(guild.channels, name="📢・anúncios")
            if not announcements_channel:
                return
            
            embed = discord.Embed(
                title="📢 CANAL DE ANÚNCIOS OFICIAIS",
                description="**Este canal é destinado apenas para anúncios importantes da liderança!**",
                color=0x00FF00
            )
            
            embed.add_field(
                name="🎯 O que você encontrará aqui:",
                value="• Atualizações importantes do clã\n" +
                      "• Mudanças nas regras ou estrutura\n" +
                      "• Anúncios de torneios e eventos\n" +
                      "• Novidades sobre o PUBG\n" +
                      "• Comunicados da liderança",
                inline=False
            )
            
            embed.add_field(
                name="🔔 Mantenha as notificações ativadas!",
                value="Clique no sino 🔔 para receber notificações de todos os anúncios importantes.",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Fique sempre informado!")
            
            await announcements_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de anúncios: {e}")
    
    async def _send_results_content(self, guild: discord.Guild):
        """Envia template para canal de resultados"""
        try:
            results_channel = discord.utils.get(guild.channels, name="📊・resultados")
            if not results_channel:
                return
            
            embed = discord.Embed(
                title="📊 RESULTADOS DE PARTIDAS E TORNEIOS",
                description="**Acompanhe o desempenho do clã Hawk Esports!**",
                color=0xFFD700
            )
            
            embed.add_field(
                name="🏆 Últimos Resultados:",
                value="*Os resultados das partidas aparecerão aqui automaticamente*\n\n" +
                      "• Scrimmages do clã\n" +
                      "• Torneios oficiais\n" +
                      "• Custom games\n" +
                      "• Estatísticas semanais",
                inline=False
            )
            
            embed.add_field(
                name="📈 Estatísticas Automáticas:",
                value="• K/D médio do clã\n" +
                      "• Taxa de vitórias\n" +
                      "• Posicionamento em rankings\n" +
                      "• Performance individual dos membros",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Resultados atualizados automaticamente")
            
            await results_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de resultados: {e}")
    
    async def _send_calendar_content(self, guild: discord.Guild):
        """Envia template para canal de calendário"""
        try:
            calendar_channel = discord.utils.get(guild.channels, name="📆・calendário")
            if not calendar_channel:
                return
            
            embed = discord.Embed(
                title="📆 CALENDÁRIO DE EVENTOS",
                description="**Agenda oficial do clã Hawk Esports**",
                color=0x9932CC
            )
            
            embed.add_field(
                name="📅 Eventos Regulares:",
                value="• **Segunda-feira:** Treino de Squad (20h)\n" +
                      "• **Quarta-feira:** Scrimmage (21h)\n" +
                      "• **Sexta-feira:** Custom Games (20h)\n" +
                      "• **Domingo:** Reunião de Clã (19h)",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Próximos Torneios:",
                value="*Torneios serão anunciados aqui com antecedência*\n\n" +
                      "• Inscrições abertas\n" +
                      "• Datas e horários\n" +
                      "• Requisitos de participação",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Lembretes:",
                value="• Confirme presença nos eventos\n" +
                      "• Chegue 15 minutos antes\n" +
                      "• Mantenha Discord e PUBG atualizados",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Nunca perca um evento!")
            
            await calendar_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de calendário: {e}")
    
    async def _send_general_content(self, guild: discord.Guild):
        """Envia mensagem de boas-vindas para canal geral"""
        try:
            general_channel = discord.utils.get(guild.channels, name="💭・geral")
            if not general_channel:
                return
            
            embed = discord.Embed(
                title="💭 CHAT GERAL - HAWK ESPORTS",
                description="**Bem-vindos ao coração do clã!**",
                color=0x00BFFF
            )
            
            embed.add_field(
                name="🎯 Este é o lugar para:",
                value="• Conversas gerais sobre PUBG\n" +
                      "• Compartilhar experiências\n" +
                      "• Fazer amizades no clã\n" +
                      "• Discutir estratégias\n" +
                      "• Organizar partidas casuais",
                inline=False
            )
            
            embed.add_field(
                name="🤝 Dicas para uma boa convivência:",
                value="• Seja respeitoso com todos\n" +
                      "• Ajude novos membros\n" +
                      "• Compartilhe conhecimento\n" +
                      "• Mantenha o clima positivo",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Unidos somos mais fortes! 🦅")
            
            await general_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar conteúdo do canal geral: {e}")
    
    async def _send_clips_content(self, guild: discord.Guild):
        """Envia template para canal de clipes"""
        try:
            clips_channel = discord.utils.get(guild.channels, name="📷・clipes")
            if not clips_channel:
                return
            
            embed = discord.Embed(
                title="📷 CLIPES E HIGHLIGHTS",
                description="**Compartilhe seus melhores momentos no PUBG!**",
                color=0xFF1493
            )
            
            embed.add_field(
                name="🎬 O que postar aqui:",
                value="• Clutches épicos\n" +
                      "• Kills impressionantes\n" +
                      "• Momentos engraçados\n" +
                      "• Chicken Dinners\n" +
                      "• Jogadas estratégicas",
                inline=False
            )
            
            embed.add_field(
                name="📱 Como compartilhar:",
                value="• Use Medal.tv para gravar\n" +
                      "• Compartilhe links do YouTube\n" +
                      "• Envie arquivos de vídeo\n" +
                      "• Adicione uma descrição da jogada",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Clipe da Semana:",
                value="• O melhor clipe ganha destaque\n" +
                      "• Votação da comunidade\n" +
                      "• Prêmios especiais para o vencedor",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Mostre suas habilidades!")
            
            await clips_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de clipes: {e}")
    
    async def _send_events_content(self, guild: discord.Guild):
        """Envia template para canal de eventos"""
        try:
            events_channel = discord.utils.get(guild.channels, name="🎉・eventos")
            if not events_channel:
                return
            
            embed = discord.Embed(
                title="🎉 EVENTOS ESPECIAIS",
                description="**Participe dos eventos exclusivos do Hawk Esports!**",
                color=0xFF6347
            )
            
            embed.add_field(
                name="🏆 Tipos de Eventos:",
                value="• **Torneios Internos:** Competições entre membros\n" +
                      "• **Custom Games:** Partidas personalizadas\n" +
                      "• **Desafios Semanais:** Missões especiais\n" +
                      "• **Eventos Temáticos:** Comemorações especiais\n" +
                      "• **Scrimmages:** Treinos competitivos",
                inline=False
            )
            
            embed.add_field(
                name="🎁 Recompensas:",
                value="• Badges exclusivos\n" +
                      "• Cargos especiais temporários\n" +
                      "• XP bonus\n" +
                      "• Reconhecimento no hall da fama",
                inline=False
            )
            
            embed.add_field(
                name="📋 Como Participar:",
                value="• Fique atento aos anúncios\n" +
                      "• Confirme presença com reação\n" +
                      "• Esteja online no horário\n" +
                      "• Siga as regras do evento",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Eventos épicos te esperam!")
            
            await events_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de eventos: {e}")
    
    async def _send_scrims_content(self, guild: discord.Guild):
        """Envia template para canal de scrims"""
        try:
            scrims_channel = discord.utils.get(guild.channels, name="⚔️・scrims")
            if not scrims_channel:
                return
            
            embed = discord.Embed(
                title="⚔️ SCRIMMAGES COMPETITIVOS",
                description="**Treinos sérios para elevar o nível do clã!**",
                color=0x8B0000
            )
            
            embed.add_field(
                name="🎯 Objetivo dos Scrims:",
                value="• Aprimorar estratégias de equipe\n" +
                      "• Testar novas táticas\n" +
                      "• Preparação para torneios\n" +
                      "• Desenvolver comunicação\n" +
                      "• Análise de gameplay",
                inline=False
            )
            
            embed.add_field(
                name="📅 Horários Regulares:",
                value="• **Quarta-feira:** 21h - Scrim Principal\n" +
                      "• **Sábado:** 20h - Scrim de Fim de Semana\n" +
                      "• **Domingo:** 19h - Review e Análise\n" +
                      "*Horários podem variar conforme disponibilidade*",
                inline=False
            )
            
            embed.add_field(
                name="⚡ Requisitos:",
                value="• Patente mínima: Ouro\n" +
                      "• Microfone obrigatório\n" +
                      "• Pontualidade essencial\n" +
                      "• Atitude competitiva e respeitosa",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Treine como um profissional!")
            
            await scrims_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de scrims: {e}")
    
    async def _send_ranking_content(self, guild: discord.Guild):
        """Envia template para canal de ranking"""
        try:
            ranking_channel = discord.utils.get(guild.channels, name="🏆・ranking")
            if not ranking_channel:
                return
            
            # Embed principal do sistema de ranking
            embed = discord.Embed(
                title="🏆 SISTEMA DE RANKING HAWK ESPORTS",
                description="**Sistema completo de classificação com rankings duplos e temporadas!**\n\n" +
                           "Acompanhe sua evolução e compete pelos primeiros lugares!",
                color=0xFFD700
            )
            
            # Comandos de ranking
            embed.add_field(
                name="📊 Comandos de Ranking",
                value="`/rank` - Ver seu ranking atual\n" +
                      "`/leaderboard` - Top 10 geral\n" +
                      "`/season_stats` - Estatísticas da temporada\n" +
                      "`/compare @usuário` - Comparar stats\n" +
                      "`/rank_history` - Histórico de ranks",
                inline=True
            )
            
            # Tipos de ranking
            embed.add_field(
                name="🎯 Tipos de Ranking",
                value="**🏅 Ranking Clássico:**\n" +
                      "Bronze IV → Survivor\n\n" +
                      "**⚔️ Ranking Metro Royale:**\n" +
                      "Bronze MM → Mestre MM\n\n" +
                      "**🏆 Ranking Geral:**\n" +
                      "Baseado em XP total",
                inline=True
            )
            
            # Sistema de pontuação
            embed.add_field(
                name="⭐ Sistema de Pontuação",
                value="**Ganhe XP por:**\n" +
                      "• Vitórias: +50 XP\n" +
                      "• Top 10: +25 XP\n" +
                      "• Kills: +5 XP cada\n" +
                      "• Participação: +10 XP\n" +
                      "• Eventos: +100 XP\n" +
                      "• Atividade Discord: +5 XP/dia",
                inline=False
            )
            
            # Recompensas por temporada
            embed.add_field(
                name="🎁 Recompensas por Temporada",
                value="**🥇 1º Lugar:**\n" +
                      "• Badge Lendário 🏆\n" +
                      "• Cargo \"Campeão da Temporada\"\n" +
                      "• Destaque permanente\n\n" +
                      "**🥈 Top 3:**\n" +
                      "• Badge Épico 🥈\n" +
                      "• Cargo \"Elite\"\n\n" +
                      "**🥉 Top 10:**\n" +
                      "• Badge Raro 🥉\n" +
                      "• Reconhecimento especial",
                inline=True
            )
            
            # Patentes e progressão
            embed.add_field(
                name="🎖️ Sistema de Patentes",
                value="**Clássico:** 🥉 Bronze → 💎 Diamond → 👑 Survivor\n" +
                      "**Metro Royale:** 🥉 Bronze MM → 🏆 Mestre MM\n\n" +
                      "**Progressão Automática:**\n" +
                      "• Cargos atualizados em tempo real\n" +
                      "• Cores exclusivas por patente\n" +
                      "• Emblemas personalizados",
                inline=True
            )
            
            # Temporadas
            embed.add_field(
                name="📅 Sistema de Temporadas",
                value="**Duração:** 30 dias\n" +
                      "**Reset:** Automático\n" +
                      "**Histórico:** Mantido permanentemente\n" +
                      "**Recompensas:** Distribuídas automaticamente\n" +
                      "**Próxima temporada:** Veja com `/season_info`",
                inline=False
            )
            
            embed.set_footer(
                text="🏆 Hawk Esports Ranking System | Rankings atualizados em tempo real",
                icon_url=guild.icon.url if guild.icon else None
            )
            
            await ranking_channel.send(embed=embed)
            
            # Embed de leaderboard exemplo
            leaderboard_embed = discord.Embed(
                title="📊 LEADERBOARD ATUAL",
                description="*Use `/leaderboard` para ver o ranking atualizado em tempo real*",
                color=0xF39C12
            )
            
            leaderboard_embed.add_field(
                name="🏆 Top Geral (Exemplo)",
                value="🥇 **Player1** - 2,450 XP - 👑 Survivor\n" +
                      "🥈 **Player2** - 2,200 XP - 💎 Diamond I\n" +
                      "🥉 **Player3** - 1,980 XP - 💎 Diamond II\n" +
                      "4️⃣ **Player4** - 1,750 XP - 🏆 Master III\n" +
                      "5️⃣ **Player5** - 1,650 XP - 🏆 Master IV",
                inline=True
            )
            
            leaderboard_embed.add_field(
                name="⚔️ Top Metro Royale (Exemplo)",
                value="🥇 **PlayerA** - 1,800 XP - 🏆 Mestre MM\n" +
                      "🥈 **PlayerB** - 1,600 XP - 💎 Diamante MM\n" +
                      "🥉 **PlayerC** - 1,400 XP - 🥇 Ouro MM\n" +
                      "4️⃣ **PlayerD** - 1,200 XP - 🥈 Prata MM\n" +
                      "5️⃣ **PlayerE** - 1,000 XP - 🥉 Bronze MM",
                inline=True
            )
            
            leaderboard_embed.add_field(
                name="📈 Estatísticas da Temporada",
                value="**Temporada Atual:** #12\n" +
                      "**Dias Restantes:** 15 dias\n" +
                      "**Jogadores Ativos:** 45\n" +
                      "**Partidas Registradas:** 1,234\n" +
                      "**XP Total Distribuído:** 125,670",
                inline=False
            )
            
            await ranking_channel.send(embed=leaderboard_embed)
            
            logger.info("Conteúdo do canal de ranking enviado")
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de ranking: {e}")
    
    async def _send_stats_content(self, guild: discord.Guild):
        """Envia template para canal de estatísticas"""
        try:
            stats_channel = discord.utils.get(guild.channels, name="📈・estatísticas")
            if not stats_channel:
                return
            
            embed = discord.Embed(
                title="📈 ESTATÍSTICAS DETALHADAS",
                description="**Análise completa do desempenho do clã!**",
                color=0x32CD32
            )
            
            embed.add_field(
                name="📊 Estatísticas Individuais:",
                value="• K/D Ratio pessoal\n" +
                      "• Taxa de vitórias\n" +
                      "• Damage médio por partida\n" +
                      "• Tempo de sobrevivência\n" +
                      "• Headshot percentage",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Estatísticas do Clã:",
                value="• Performance geral do grupo\n" +
                      "• Comparação com outros clãs\n" +
                      "• Evolução mensal\n" +
                      "• Melhores duplas/squads\n" +
                      "• Recordes estabelecidos",
                inline=False
            )
            
            embed.add_field(
                name="📅 Relatórios Automáticos:",
                value="• **Diário:** Resumo das partidas\n" +
                      "• **Semanal:** Análise detalhada\n" +
                      "• **Mensal:** Relatório completo\n" +
                      "• **Temporada:** Balanço geral",
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Dados que fazem a diferença!")
            
            await stats_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar template de estatísticas: {e}")
    
    async def get_server_info(self, guild: discord.Guild) -> discord.Embed:
        """Retorna informações sobre a estrutura atual do servidor"""
        embed = discord.Embed(
            title=f"📊 Estrutura do Servidor - {guild.name}",
            description="Informações sobre categorias, canais e roles",
            color=discord.Color.blue()
        )
        
        # Contar elementos
        categories_count = len(guild.categories)
        text_channels_count = len([ch for ch in guild.channels if isinstance(ch, discord.TextChannel)])
        voice_channels_count = len([ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)])
        roles_count = len(guild.roles) - 1  # Excluir @everyone
        
        embed.add_field(
            name="📁 Categorias",
            value=f"{categories_count} categorias",
            inline=True
        )
        
        embed.add_field(
            name="💬 Canais de Texto",
            value=f"{text_channels_count} canais",
            inline=True
        )
        
        embed.add_field(
            name="🎙️ Canais de Voz",
            value=f"{voice_channels_count} canais",
            inline=True
        )
        
        embed.add_field(
            name="🏷️ Roles",
            value=f"{roles_count} roles",
            inline=True
        )
        
        embed.add_field(
            name="👥 Membros",
            value=f"{guild.member_count} membros",
            inline=True
        )
        
        embed.set_footer(text="Hawk Esports - Estrutura profissional!")
        
        return embed