#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Registro Automático
Gerencia registro de novos membros e atribuição de roles

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger('HawkBot.Registration')

class Registration:
    """Classe responsável pelo sistema de registro automático"""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = bot.storage
        
        # Configurações de registro
        self.access_role_name = "Acesso liberado"
        self.registration_channel_name = "📋・registro"
        
        logger.info("Sistema de registro inicializado")
    
    async def handle_new_member(self, member: discord.Member):
        """Processa novo membro que entrou no servidor"""
        try:
            logger.info(f"Novo membro: {member.name} ({member.id})")
            
            # Atribuir role "Não Registrado" automaticamente
            await self._grant_unregistered_role(member)
            
            # Enviar mensagem de boas-vindas via DM
            await self._send_welcome_dm(member)
            
            # Enviar notificação no canal de registro
            await self._send_registration_notification(member)
            
        except Exception as e:
            logger.error(f"Erro ao processar novo membro {member.name}: {e}")
    
    async def register_player(self, user: discord.User, pubg_name: str, shard: str) -> bool:
        """Registra um jogador no sistema"""
        try:
            # Verificar se já está registrado
            existing_player = self.storage.get_player(str(user.id))
            if existing_player:
                logger.info(f"Jogador {user.name} já está registrado")
                return False
            
            # Validar shard
            valid_shards = ['steam', 'psn', 'xbox', 'kakao']
            if shard.lower() not in valid_shards:
                logger.warning(f"Shard inválido: {shard}")
                return False
            
            # Adicionar jogador ao storage
            guild_id = str(user.mutual_guilds[0].id) if user.mutual_guilds else None
            success = self.storage.add_player(
                str(user.id), 
                pubg_name, 
                shard.lower(), 
                guild_id
            )
            
            if not success:
                return False
            
            # Remover role "Não Registrado" e atribuir "Acesso liberado"
            await self._remove_unregistered_role(user)
            await self._grant_access_role(user)
            
            # Verificar conquistas de registro
            if hasattr(self.bot, 'achievement_system'):
                try:
                    stats = {
                        'registration_date': datetime.now().isoformat(),
                        'pubg_name': pubg_name,
                        'shard': shard
                    }
                    unlocked = self.bot.achievement_system.check_achievements(str(user.id), stats)
                    
                    # Enviar notificações de conquistas
                    if unlocked:
                        registration_channel = discord.utils.get(user.mutual_guilds[0].channels, name='registros')
                        if registration_channel:
                            for achievement in unlocked:
                                await self.bot.achievement_system.send_achievement_notification(
                                    str(user.id), achievement, registration_channel
                                )
                except Exception as e:
                    logger.error(f"Erro ao verificar conquistas de registro: {e}")
            
            # Enviar mensagem de confirmação via DM
            await self._send_registration_confirmation(user, pubg_name, shard)
            
            logger.info(f"Jogador registrado: {pubg_name} ({user.name})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar jogador {user.name}: {e}")
            return False
    
    async def get_player_status(self, user: discord.User) -> str:
        """Retorna status detalhado do jogador"""
        try:
            player_data = self.storage.get_player(str(user.id))
            
            if not player_data:
                return (
                    "❌ **Não Registrado**\n\n"
                    "Você ainda não está registrado no sistema.\n"
                    "Use `/register_pubg` para se registrar e ter acesso completo ao servidor.\n\n"
                    "**Como registrar:**\n"
                    "`/register_pubg nome:<seu_nick> shard:<plataforma>`"
                )
            
            # Informações básicas
            pubg_name = player_data.get('pubg_name', 'N/A')
            shard = player_data.get('shard', 'N/A').upper()
            registered_at = player_data.get('registered_at', 'N/A')
            
            # Converter data de registro
            try:
                reg_date = datetime.fromisoformat(registered_at)
                reg_date_str = reg_date.strftime('%d/%m/%Y às %H:%M')
            except:
                reg_date_str = 'Data inválida'
            
            # Ranks atuais
            current_ranks = player_data.get('current_ranks', {})
            ranked_rank = current_ranks.get('ranked', 'Não definido')
            mm_rank = current_ranks.get('mm', 'Não definido')
            
            # Estatísticas
            stats = player_data.get('stats', {})
            ranked_stats = stats.get('ranked', {})
            mm_stats = stats.get('mm', {})
            
            # Verificar se tem role de acesso
            has_access = await self._check_access_role(user)
            access_status = "✅ Liberado" if has_access else "❌ Pendente"
            
            status_text = (
                f"✅ **Registrado com Sucesso**\n\n"
                f"🎮 **Nick PUBG:** {pubg_name}\n"
                f"🌐 **Plataforma:** {shard}\n"
                f"📅 **Registrado em:** {reg_date_str}\n"
                f"🔓 **Acesso:** {access_status}\n\n"
                f"🏆 **Ranks Atuais:**\n"
                f"• **Ranked:** {ranked_rank}\n"
                f"• **MM:** {mm_rank}\n\n"
                f"📊 **Estatísticas Ranked:**\n"
                f"• **K/D:** {ranked_stats.get('kd', 0):.2f}\n"
                f"• **Vitórias:** {ranked_stats.get('wins', 0)}\n"
                f"• **Partidas:** {ranked_stats.get('matches', 0)}\n\n"
                f"📈 **Estatísticas MM:**\n"
                f"• **K/D:** {mm_stats.get('kd', 0):.2f}\n"
                f"• **Vitórias:** {mm_stats.get('wins', 0)}\n"
                f"• **Partidas:** {mm_stats.get('matches', 0)}"
            )
            
            return status_text
            
        except Exception as e:
            logger.error(f"Erro ao obter status do jogador {user.name}: {e}")
            return "❌ Erro ao obter informações do jogador."
    
    async def _grant_access_role(self, user: discord.User):
        """Concede role de acesso liberado ao usuário"""
        try:
            # Encontrar guild mutual
            guild = None
            for g in user.mutual_guilds:
                guild = g
                break
            
            if not guild:
                logger.warning(f"Nenhuma guild mutual encontrada para {user.name}")
                return
            
            # Buscar member no guild
            member = guild.get_member(user.id)
            if not member:
                logger.warning(f"Member {user.name} não encontrado no guild {guild.name}")
                return
            
            # Buscar role de acesso
            access_role = discord.utils.get(guild.roles, name=self.access_role_name)
            if not access_role:
                logger.warning(f"Role '{self.access_role_name}' não encontrada no guild {guild.name}")
                return
            
            # Verificar se já tem a role
            if access_role in member.roles:
                logger.info(f"Member {user.name} já possui role de acesso")
                return
            
            # Adicionar role
            await member.add_roles(access_role, reason="Registro PUBG concluído")
            logger.info(f"Role '{self.access_role_name}' concedida a {user.name}")
            
        except Exception as e:
            logger.error(f"Erro ao conceder role de acesso a {user.name}: {e}")
    
    async def _check_access_role(self, user: discord.User) -> bool:
        """Verifica se usuário tem role de acesso"""
        try:
            # Encontrar guild mutual
            guild = None
            for g in user.mutual_guilds:
                guild = g
                break
            
            if not guild:
                return False
            
            # Buscar member no guild
            member = guild.get_member(user.id)
            if not member:
                return False
            
            # Buscar role de acesso
            access_role = discord.utils.get(guild.roles, name=self.access_role_name)
            if not access_role:
                return False
            
            return access_role in member.roles
            
        except Exception as e:
            logger.error(f"Erro ao verificar role de acesso de {user.name}: {e}")
            return False
    
    async def _send_welcome_dm(self, member: discord.Member):
        """Envia mensagem de boas-vindas via DM"""
        try:
            embed = discord.Embed(
                title="🦅 Bem-vindo ao Hawk Esports!",
                description=f"Olá **{member.name}**! Seja bem-vindo ao clã mais dominante do PUBG!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🎯 Próximo Passo: Registro",
                value=(
                    "Para ter acesso completo ao servidor, você precisa se registrar:\n\n"
                    "**Vá ao canal** <#📋・registro> **e use:**\n"
                    "`/register_pubg nome:<seu_nick> shard:<plataforma>`\n\n"
                    "**Exemplo:**\n"
                    "`/register_pubg nome:HawkPlayer shard:steam`"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🌐 Plataformas Disponíveis",
                value=(
                    "• `steam` - PC (Steam)\n"
                    "• `psn` - PlayStation\n"
                    "• `xbox` - Xbox\n"
                    "• `kakao` - Kakao"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🏆 Após o Registro",
                value=(
                    "• ✅ Acesso a todos os canais\n"
                    "• 🏷️ Cargo baseado em suas stats\n"
                    "• 📊 Participação nos rankings\n"
                    "• 🎬 Integração com clipes Medal\n"
                    "• 🎮 Participação em scrims e eventos"
                ),
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Rumo à vitória! 🦅")
            embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
            
            await member.send(embed=embed)
            logger.info(f"Mensagem de boas-vindas enviada via DM para {member.name}")
            
        except discord.Forbidden:
            logger.warning(f"Não foi possível enviar DM para {member.name} (DMs fechadas)")
        except Exception as e:
            logger.error(f"Erro ao enviar DM de boas-vindas para {member.name}: {e}")
    
    async def _send_registration_notification(self, member: discord.Member):
        """Envia notificação de novo membro no canal de registro com sistema de boas-vindas completo"""
        try:
            # Buscar canal de registro
            registration_channel = discord.utils.get(
                member.guild.channels, 
                name=self.registration_channel_name
            )
            
            if not registration_channel:
                logger.warning(f"Canal de registro não encontrado: {self.registration_channel_name}")
                return
            
            # Embed principal de boas-vindas
            welcome_embed = discord.Embed(
                title="🎉 Bem-vindo(a) ao Hawk Esports!",
                description=f"Olá **{member.mention}**! Seja muito bem-vindo(a) ao nosso servidor!",
                color=0x00ff88
            )
            
            welcome_embed.add_field(
                name="🚨 ACESSO LIMITADO",
                value=(
                    "⚠️ **Você possui acesso limitado!**\n"
                    "Para ter acesso completo aos canais e recursos do servidor, "
                    "você precisa se registrar primeiro."
                ),
                inline=False
            )
            
            welcome_embed.add_field(
                name="📋 Como se Registrar",
                value=(
                    "Use o comando abaixo para se registrar:\n"
                    "`/register_pubg nome:<seu_nick_pubg> shard:<plataforma>`\n\n"
                    "**Plataformas disponíveis:**\n"
                    "• `steam` - PC (Steam)\n"
                    "• `psn` - PlayStation\n"
                    "• `xbox` - Xbox\n"
                    "• `kakao` - PC (Kakao)"
                ),
                inline=False
            )
            
            welcome_embed.add_field(
                name="✨ Após o Registro",
                value=(
                    "🔓 **Acesso completo aos canais**\n"
                    "🏆 **Sistema de ranking automático**\n"
                    "📊 **Estatísticas detalhadas**\n"
                    "🎯 **Participação em scrims e eventos**\n"
                    "🎵 **Canais de voz exclusivos**"
                ),
                inline=False
            )
            
            welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            welcome_embed.set_footer(
                text=f"Membro #{member.guild.member_count} • Registre-se para acesso completo!",
                icon_url=member.guild.icon.url if member.guild.icon else None
            )
            welcome_embed.timestamp = datetime.now()
            
            # Embed de exemplo de registro
            example_embed = discord.Embed(
                title="💡 Exemplo de Registro",
                description="Veja como usar o comando de registro:",
                color=0x3498db
            )
            
            example_embed.add_field(
                name="📝 Exemplo Prático",
                value=(
                    "`/register_pubg nome:HawkPlayer123 shard:steam`\n\n"
                    "**Substitua:**\n"
                    "• `HawkPlayer123` pelo seu nick no PUBG\n"
                    "• `steam` pela sua plataforma"
                ),
                inline=False
            )
            
            example_embed.add_field(
                name="❓ Precisa de Ajuda?",
                value=(
                    "Se tiver dúvidas, mencione um **@Moderador** ou **@Admin**\n"
                    "Estamos aqui para ajudar! 😊"
                ),
                inline=False
            )
            
            # Enviar embeds
            await registration_channel.send(embed=welcome_embed)
            await registration_channel.send(embed=example_embed)
            
            logger.info(f"Sistema de boas-vindas completo enviado para {member.name}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de registro para {member.name}: {e}")
    
    async def _send_registration_confirmation(self, user: discord.User, pubg_name: str, shard: str):
        """Envia confirmação de registro via DM"""
        try:
            embed = discord.Embed(
                title="✅ Registro Concluído!",
                description=f"Parabéns **{user.name}**! Seu registro foi concluído com sucesso!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🎮 Informações Registradas",
                value=(
                    f"**Nick PUBG:** {pubg_name}\n"
                    f"**Plataforma:** {shard.upper()}\n"
                    f"**Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🏆 Próximos Passos",
                value=(
                    "• ✅ Você agora tem acesso completo ao servidor\n"
                    "• 📊 Suas stats serão atualizadas automaticamente\n"
                    "• 🏷️ Seu cargo será definido baseado no seu desempenho\n"
                    "• 🎬 Seus clipes Medal serão integrados automaticamente\n"
                    "• 🎮 Participe dos rankings usando `/leaderboard`"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📋 Comandos Úteis",
                value=(
                    "• `/meu_status` - Ver suas informações\n"
                    "• `/leaderboard` - Ver ranking do clã\n"
                    "• `/clipes` - Ver seus clipes\n"
                    "• `/help` - Lista todos os comandos"
                ),
                inline=False
            )
            
            embed.set_footer(text="Hawk Esports - Bem-vindo à família! 🦅")
            
            await user.send(embed=embed)
            logger.info(f"Confirmação de registro enviada via DM para {user.name}")
            
        except discord.Forbidden:
            logger.warning(f"Não foi possível enviar confirmação via DM para {user.name}")
        except Exception as e:
            logger.error(f"Erro ao enviar confirmação de registro para {user.name}: {e}")
    
    async def unregister_player(self, user_id: str) -> bool:
        """Remove registro de um jogador (admin only)"""
        try:
            player_data = self.storage.get_player(user_id)
            if not player_data:
                return False
            
            # Remover do storage
            if user_id in self.storage.data.get("players", {}):
                del self.storage.data["players"][user_id]
                self.storage.save_data()
                
                logger.info(f"Registro removido para usuário {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover registro do usuário {user_id}: {e}")
            return False
    
    async def get_registration_stats(self, guild_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de registro do guild"""
        try:
            all_players = self.storage.get_all_players(guild_id)
            
            # Contar por shard
            shard_counts = {}
            total_registered = len(all_players)
            
            for player_data in all_players.values():
                shard = player_data.get('shard', 'unknown')
                shard_counts[shard] = shard_counts.get(shard, 0) + 1
            
            # Registros recentes (últimos 7 dias)
            recent_registrations = 0
            cutoff_date = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 dias atrás
            
            for player_data in all_players.values():
                try:
                    reg_date = datetime.fromisoformat(player_data.get('registered_at', ''))
                    if reg_date.timestamp() > cutoff_date:
                        recent_registrations += 1
                except:
                    continue
            
            return {
                "total_registered": total_registered,
                "shard_distribution": shard_counts,
                "recent_registrations": recent_registrations
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de registro: {e}")
            return {}
    
    async def update_all_access_roles(self, guild: discord.Guild) -> Dict[str, int]:
        """Atualiza cargo 'Acesso liberado' para todos os membros registrados"""
        try:
            logger.info(f"Iniciando atualização de cargos de acesso para {guild.name}")
            
            # Buscar cargo de acesso
            access_role = discord.utils.get(guild.roles, name=self.access_role_name)
            if not access_role:
                logger.error(f"Cargo '{self.access_role_name}' não encontrado no servidor")
                return {"error": "Cargo não encontrado"}
            
            # Obter todos os jogadores registrados
            all_players = self.storage.get_all_players(str(guild.id))
            
            updated_count = 0
            already_had_count = 0
            not_found_count = 0
            
            for user_id, player_data in all_players.items():
                try:
                    # Buscar membro no servidor
                    member = guild.get_member(int(user_id))
                    if not member:
                        not_found_count += 1
                        continue
                    
                    # Verificar se já tem o cargo
                    if access_role in member.roles:
                        already_had_count += 1
                        continue
                    
                    # Adicionar cargo
                    await member.add_roles(access_role, reason="Atualização em massa - Registro PUBG")
                    updated_count += 1
                    logger.info(f"Cargo '{self.access_role_name}' adicionado para {member.display_name}")
                    
                    # Pequena pausa para evitar rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Erro ao atualizar cargo para usuário {user_id}: {e}")
                    continue
            
            logger.info(f"Atualização concluída: {updated_count} atualizados, {already_had_count} já tinham, {not_found_count} não encontrados")
            
            return {
                "updated": updated_count,
                "already_had": already_had_count,
                "not_found": not_found_count,
                "total_registered": len(all_players)
            }
    
    async def _grant_unregistered_role(self, member: discord.Member):
        """Concede a role 'Não Registrado' para um membro"""
        try:
            guild = member.guild
            unregistered_role = discord.utils.get(guild.roles, name="Não Registrado")
            
            if not unregistered_role:
                logger.warning(f"Role 'Não Registrado' não encontrada no servidor {guild.name}")
                return False
            
            if unregistered_role in member.roles:
                logger.info(f"Membro {member.name} já possui a role 'Não Registrado'")
                return True
            
            await member.add_roles(unregistered_role, reason="Novo membro - acesso limitado")
            logger.info(f"Role 'Não Registrado' concedida para {member.name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conceder role 'Não Registrado' para {member.name}: {e}")
            return False
    
    async def _remove_unregistered_role(self, user: discord.User):
        """Remove a role 'Não Registrado' de um usuário"""
        try:
            # Encontrar o membro no servidor
            member = None
            for guild in self.bot.guilds:
                member = guild.get_member(user.id)
                if member:
                    break
            
            if not member:
                logger.warning(f"Membro {user.name} não encontrado em nenhum servidor")
                return False
            
            guild = member.guild
            unregistered_role = discord.utils.get(guild.roles, name="Não Registrado")
            
            if not unregistered_role:
                logger.warning(f"Role 'Não Registrado' não encontrada no servidor {guild.name}")
                return False
            
            if unregistered_role not in member.roles:
                logger.info(f"Membro {member.name} não possui a role 'Não Registrado'")
                return True
            
            await member.remove_roles(unregistered_role, reason="Usuário registrado - acesso liberado")
            logger.info(f"Role 'Não Registrado' removida de {member.name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover role 'Não Registrado' de {user.name}: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Erro na atualização em massa de cargos de acesso: {e}")
            return {"error": str(e)}