#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Moderação Automática Avançado
Detecção de spam, toxicidade, filtros de palavras e ações automáticas

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
import logging
import asyncio
import re
import json
import os
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('HawkBot.ModerationSystem')

class ViolationType(Enum):
    """Tipos de violações detectadas"""
    SPAM = "spam"
    TOXIC_LANGUAGE = "toxic_language"
    CAPS_SPAM = "caps_spam"
    REPEATED_MESSAGES = "repeated_messages"
    MENTION_SPAM = "mention_spam"
    LINK_SPAM = "link_spam"
    EMOJI_SPAM = "emoji_spam"
    RAID_ATTEMPT = "raid_attempt"
    INAPPROPRIATE_CONTENT = "inappropriate_content"

class ActionType(Enum):
    """Tipos de ações de moderação"""
    WARN = "warn"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"
    DELETE_MESSAGE = "delete_message"
    SLOWMODE = "slowmode"

@dataclass
class ModerationAction:
    """Representa uma ação de moderação"""
    user_id: int
    action_type: ActionType
    violation_type: ViolationType
    reason: str
    timestamp: datetime
    moderator_id: Optional[int] = None
    duration: Optional[timedelta] = None
    evidence: Optional[str] = None

class SpamDetector:
    """Detector de spam avançado"""
    
    def __init__(self):
        # Configurações de detecção
        self.message_limit = 5  # Máximo de mensagens
        self.time_window = 10   # Em segundos
        self.similarity_threshold = 0.8  # Similaridade entre mensagens
        self.caps_threshold = 0.7  # Porcentagem de maiúsculas
        self.mention_limit = 5  # Máximo de menções por mensagem
        self.emoji_limit = 10   # Máximo de emojis por mensagem
        
        # Cache de mensagens por usuário
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        self.user_violations: Dict[int, List[datetime]] = defaultdict(list)
        
    def check_message_spam(self, user_id: int, message: str, config: dict = None) -> Optional[ViolationType]:
        """Verifica se a mensagem é spam"""
        now = datetime.now()
        user_msgs = self.user_messages[user_id]
        
        # Obter configurações de spam
        spam_config = config.get('spam_settings', {}) if config else {}
        message_limit = spam_config.get('message_limit', self.message_limit)
        time_window = spam_config.get('time_window', self.time_window)
        caps_threshold = spam_config.get('caps_threshold', self.caps_threshold)
        
        # Adicionar mensagem atual
        user_msgs.append({
            'content': message.lower().strip(),
            'timestamp': now,
            'original': message
        })
        
        # Verificar spam por frequência
        recent_msgs = [msg for msg in user_msgs if now - msg['timestamp'] <= timedelta(seconds=time_window)]
        if len(recent_msgs) > message_limit:
            return ViolationType.SPAM
        
        # Verificar mensagens repetidas
        if len(recent_msgs) >= 3:
            contents = [msg['content'] for msg in recent_msgs[-3:]]
            if len(set(contents)) == 1:  # Todas iguais
                return ViolationType.REPEATED_MESSAGES
        
        # Verificar CAPS LOCK
        if len(message) > 10:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            if caps_ratio > caps_threshold:
                return ViolationType.CAPS_SPAM
        
        return None
    
    def check_mention_spam(self, message: discord.Message) -> bool:
        """Verifica spam de menções"""
        total_mentions = len(message.mentions) + len(message.role_mentions)
        return total_mentions > self.mention_limit
    
    def check_emoji_spam(self, message: str) -> bool:
        """Verifica spam de emojis"""
        emoji_pattern = r'<:[^:]+:[0-9]+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        emojis = re.findall(emoji_pattern, message)
        return len(emojis) > self.emoji_limit
    
    def check_link_spam(self, message: str) -> bool:
        """Verifica spam de links"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        links = re.findall(url_pattern, message)
        return len(links) > 2

class ToxicityFilter:
    """Filtro de toxicidade e palavras proibidas"""
    
    def __init__(self):
        # Lista de palavras proibidas (expandível)
        self.banned_words = {
            # Palavrões básicos
            'fdp', 'porra', 'caralho', 'merda', 'bosta', 'cu', 'buceta',
            'puta', 'viado', 'gay', 'bicha', 'traveco', 'travecos',
            # Termos tóxicos gaming
            'noob', 'lixo', 'trash', 'ez', 'easy', 'rekt', 'owned',
            'hack', 'hacker', 'cheater', 'cheat', 'aimbot',
            # Discriminação
            'negro', 'preto', 'macaco', 'gorila', 'nazista', 'hitler',
            # Toxicidade geral
            'idiota', 'burro', 'estupido', 'imbecil', 'retardado',
            'cancer', 'aids', 'doente', 'mongoloid'
        }
        
        # Padrões de toxicidade
        self.toxic_patterns = [
            r'k+y+s+',  # kys variations
            r'n+[i1]+g+[g4]+[a4@]+',  # racial slurs
            r'f+[a4@]+g+[g4]+[o0]+t+',  # homophobic slurs
            r'r+[a4@]+p+[e3]+',  # rape
            r's+u+[i1]+c+[i1]+d+[e3]+',  # suicide
        ]
        
    def check_toxicity(self, message: str) -> Optional[List[str]]:
        """Verifica toxicidade na mensagem"""
        message_lower = message.lower()
        violations = []
        
        # Verificar palavras proibidas
        for word in self.banned_words:
            if word in message_lower:
                violations.append(f"Palavra proibida: {word}")
        
        # Verificar padrões tóxicos
        for pattern in self.toxic_patterns:
            if re.search(pattern, message_lower):
                violations.append(f"Padrão tóxico detectado")
        
        return violations if violations else None

class RaidProtection:
    """Proteção contra raids"""
    
    def __init__(self):
        self.join_threshold = 10  # Máximo de joins
        self.time_window = 60     # Em segundos
        self.recent_joins: deque = deque(maxlen=50)
        
    def check_raid(self, member: discord.Member) -> bool:
        """Verifica tentativa de raid"""
        now = datetime.now()
        self.recent_joins.append(now)
        
        # Contar joins recentes
        recent_count = sum(1 for join_time in self.recent_joins 
                          if now - join_time <= timedelta(seconds=self.time_window))
        
        return recent_count > self.join_threshold

class ModerationSystem:
    """Sistema principal de moderação automática"""
    
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        
        # Componentes do sistema
        self.spam_detector = SpamDetector()
        self.toxicity_filter = ToxicityFilter()
        self.raid_protection = RaidProtection()
        
        # Carregar configurações do arquivo
        self.config = self.load_config()
        
        # Configurações
        self.auto_moderation_enabled = True
        self.log_channel_id = None
        self.mod_role_ids: Set[int] = set()
        
        # Sistema de warns
        self.user_warns: Dict[int, List[ModerationAction]] = defaultdict(list)
        # Thresholds configuráveis via JSON
        default_thresholds = {
            3: ActionType.TIMEOUT,   # 3 warns = timeout
            5: ActionType.KICK,      # 5 warns = kick
            7: ActionType.BAN        # 7 warns = ban
        }
        
        # Carregar thresholds do config ou usar padrão
        config_thresholds = self.config.get('warning_thresholds', {})
        self.warn_thresholds = {
            config_thresholds.get('timeout_warnings', 3): ActionType.TIMEOUT,
            config_thresholds.get('kick_warnings', 5): ActionType.KICK,
            config_thresholds.get('ban_warnings', 7): ActionType.BAN
        }
        
        # Cache de ações recentes
        self.recent_actions: Dict[int, List[ModerationAction]] = defaultdict(list)
        
        # Estatísticas
        self.stats = {
            'messages_checked': 0,
            'violations_detected': 0,
            'actions_taken': 0,
            'spam_blocked': 0,
            'toxic_messages_deleted': 0
        }
        
        logger.info("Sistema de Moderação Automática inicializado")
    
    def load_config(self) -> dict:
        """Carrega configurações do arquivo JSON"""
        config_path = 'moderation_config.json'
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Arquivo de configuração {config_path} não encontrado, usando configurações padrão")
                return {}
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            return {}
    
    async def setup_moderation(self, guild: discord.Guild, log_channel: discord.TextChannel):
        """Configura o sistema de moderação para um servidor"""
        self.log_channel_id = log_channel.id
        
        # Salvar configurações
        data = self.storage.load_data()
        if 'moderation_config' not in data:
            data['moderation_config'] = {}
        
        data['moderation_config'][str(guild.id)] = {
            'log_channel_id': log_channel.id,
            'enabled': True,
            'setup_date': datetime.now().isoformat()
        }
        
        self.storage.save_data(data)
        logger.info(f"Moderação configurada para {guild.name}")
    
    async def process_message(self, message: discord.Message) -> bool:
        """Processa uma mensagem para detecção de violações"""
        if not self.auto_moderation_enabled:
            return False
        
        if message.author.bot:
            return False
        
        if self._is_moderator(message.author):
            return False
        
        self.stats['messages_checked'] += 1
        violations = []
        
        # Verificar spam
        spam_type = self.spam_detector.check_message_spam(message.author.id, message.content)
        if spam_type:
            violations.append((spam_type, "Spam detectado"))
        
        # Verificar menções em massa
        if self.spam_detector.check_mention_spam(message):
            violations.append((ViolationType.MENTION_SPAM, "Spam de menções"))
        
        # Verificar emoji spam
        if self.spam_detector.check_emoji_spam(message.content):
            violations.append((ViolationType.EMOJI_SPAM, "Spam de emojis"))
        
        # Verificar link spam
        if self.spam_detector.check_link_spam(message.content):
            violations.append((ViolationType.LINK_SPAM, "Spam de links"))
        
        # Verificar toxicidade
        toxic_words = self.toxicity_filter.check_toxicity(message.content)
        if toxic_words:
            violations.append((ViolationType.TOXIC_LANGUAGE, f"Linguagem tóxica: {', '.join(toxic_words)}"))
        
        # Processar violações
        if violations:
            await self._handle_violations(message, violations)
            return True
        
        return False
    
    async def process_member_join(self, member: discord.Member) -> bool:
        """Processa entrada de novo membro"""
        if self.raid_protection.check_raid(member):
            await self._handle_raid_attempt(member)
            return True
        return False
    
    async def handle_member_join(self, member: discord.Member):
        """Processa entrada de novos membros (proteção anti-raid)"""
        try:
            # Obter configurações de proteção anti-raid
            raid_config = self.config.get('raid_protection', {})
            if not raid_config.get('enabled', True):
                return
            
            max_joins_per_minute = raid_config.get('max_joins_per_minute', 10)
            new_account_threshold = raid_config.get('new_account_threshold_days', 7)
            auto_kick_new_accounts = raid_config.get('auto_kick_new_accounts', False)
            
            now = datetime.now()
            self.raid_protection.recent_joins.append(now)
            
            # Verificar se há muitas entradas em pouco tempo
            recent_joins = [t for t in self.raid_protection.recent_joins if (now - t).total_seconds() < 60]  # último minuto
            
            if len(recent_joins) > max_joins_per_minute:
                # Possível raid detectado
                embed = discord.Embed(
                    title="🚨 Possível Raid Detectado",
                    description=f"Muitas entradas simultâneas detectadas.\n"
                               f"Usuário: {member.mention}\n"
                               f"Conta criada: {member.created_at.strftime('%d/%m/%Y')}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                # Verificar se é conta nova
                account_age = (datetime.now() - member.created_at.replace(tzinfo=None)).days
                if account_age < new_account_threshold:
                    embed.add_field(
                        name="⚠️ Conta Suspeita",
                        value=f"Conta criada há {account_age} dias",
                        inline=False
                    )
                    
                    # Auto-kick contas muito novas durante raid se habilitado
                    if auto_kick_new_accounts:
                        try:
                            await member.kick(reason="Proteção anti-raid: conta muito nova")
                            embed.add_field(
                                name="🦵 Ação Tomada",
                                value="Usuário removido automaticamente",
                                inline=False
                            )
                        except discord.Forbidden:
                            embed.add_field(
                                name="❌ Erro",
                                value="Sem permissão para remover usuário",
                                inline=False
                            )
                
                # Enviar alerta para canal de moderação
                if self.log_channel_id:
                    log_channel = member.guild.get_channel(self.log_channel_id)
                    if log_channel:
                        try:
                            await log_channel.send(embed=embed)
                        except Exception as e:
                            logger.error(f"Erro ao enviar log de raid: {e}")
                
        except Exception as e:
            logger.error(f"Erro na proteção anti-raid: {e}")
    
    async def _handle_violations(self, message: discord.Message, violations: List[tuple]):
        """Processa violações detectadas"""
        self.stats['violations_detected'] += len(violations)
        
        for violation_type, reason in violations:
            # Criar ação de moderação
            action = ModerationAction(
                user_id=message.author.id,
                action_type=ActionType.WARN,
                violation_type=violation_type,
                reason=reason,
                timestamp=datetime.now(),
                evidence=message.content[:500]  # Primeiros 500 chars
            )
            
            # Adicionar warn
            self.user_warns[message.author.id].append(action)
            
            # Deletar mensagem
            try:
                await message.delete()
                self.stats['toxic_messages_deleted'] += 1
            except discord.NotFound:
                pass
            except discord.Forbidden:
                logger.warning(f"Sem permissão para deletar mensagem de {message.author}")
            
            # Verificar se precisa de ação adicional
            warn_count = len(self.user_warns[message.author.id])
            additional_action = None
            
            if warn_count in self.warn_thresholds:
                additional_action = self.warn_thresholds[warn_count]
                await self._execute_action(message.author, additional_action, f"Acumulou {warn_count} warns")
            
            # Log da ação
            await self._log_action(action, message.guild, additional_action)
            
            # Notificar usuário
            await self._notify_user(message.author, action, warn_count)
    
    async def _handle_raid_attempt(self, member: discord.Member):
        """Processa tentativa de raid"""
        action = ModerationAction(
            user_id=member.id,
            action_type=ActionType.BAN,
            violation_type=ViolationType.RAID_ATTEMPT,
            reason="Tentativa de raid detectada",
            timestamp=datetime.now()
        )
        
        try:
            await member.ban(reason="Auto-ban: Tentativa de raid")
            self.stats['actions_taken'] += 1
            await self._log_action(action, member.guild)
        except discord.Forbidden:
            logger.warning(f"Sem permissão para banir {member}")
    
    async def _execute_action(self, user: discord.Member, action_type: ActionType, reason: str):
        """Executa ação de moderação"""
        try:
            # Obter configurações de thresholds
            thresholds = self.config.get('warning_thresholds', {})
            timeout_durations = self.config.get('timeout_durations', {})
            
            if action_type == ActionType.TIMEOUT:
                # Calcular duração baseada no número de warns
                warn_count = len(self.user_warns[user.id])
                if warn_count == 3:
                    duration = timeout_durations.get('first_offense', 300)  # 5 min
                elif warn_count == 4:
                    duration = timeout_durations.get('second_offense', 900)  # 15 min
                else:
                    duration = timeout_durations.get('third_offense', 3600)  # 1 hora
                
                duration = min(duration, 86400)  # Max 24h
                await user.timeout(timedelta(seconds=duration), reason=reason)
            elif action_type == ActionType.KICK:
                await user.kick(reason=reason)
            elif action_type == ActionType.BAN:
                await user.ban(reason=reason)
            
            self.stats['actions_taken'] += 1
            
        except discord.Forbidden:
            logger.warning(f"Sem permissão para executar {action_type.value} em {user}")
        except Exception as e:
            logger.error(f"Erro ao executar ação {action_type.value}: {e}")
    
    async def _log_action(self, action: ModerationAction, guild: discord.Guild, additional_action: ActionType = None):
        """Registra ação no canal de logs"""
        if not self.log_channel_id:
            return
        
        log_channel = guild.get_channel(self.log_channel_id)
        if not log_channel:
            return
        
        user = guild.get_member(action.user_id)
        if not user:
            return
        
        embed = discord.Embed(
            title="🚨 Ação de Moderação Automática",
            color=discord.Color.red(),
            timestamp=action.timestamp
        )
        
        embed.add_field(name="👤 Usuário", value=f"{user.mention} ({user})", inline=True)
        embed.add_field(name="⚠️ Violação", value=action.violation_type.value.replace('_', ' ').title(), inline=True)
        embed.add_field(name="🔨 Ação", value=action.action_type.value.replace('_', ' ').title(), inline=True)
        embed.add_field(name="📝 Motivo", value=action.reason, inline=False)
        
        if action.evidence:
            embed.add_field(name="🔍 Evidência", value=f"```{action.evidence[:200]}```", inline=False)
        
        if additional_action:
            embed.add_field(name="➕ Ação Adicional", value=additional_action.value.replace('_', ' ').title(), inline=True)
        
        warn_count = len(self.user_warns[action.user_id])
        embed.add_field(name="⚠️ Total de Warns", value=str(warn_count), inline=True)
        
        embed.set_footer(text="Sistema de Moderação Automática")
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro ao enviar log: {e}")
    
    async def _notify_user(self, user: discord.Member, action: ModerationAction, warn_count: int):
        """Notifica usuário sobre a ação"""
        try:
            embed = discord.Embed(
                title="⚠️ Aviso de Moderação",
                description=f"Sua mensagem foi removida por violar as regras do servidor.",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="📝 Motivo", value=action.reason, inline=False)
            embed.add_field(name="⚠️ Warns Totais", value=f"{warn_count}/7", inline=True)
            
            if warn_count >= 3:
                embed.add_field(
                    name="🚨 Atenção", 
                    value="Você está próximo de ações mais severas. Respeite as regras!", 
                    inline=False
                )
            
            embed.set_footer(text="Sistema de Moderação Automática - Hawk Esports")
            
            await user.send(embed=embed)
        except discord.Forbidden:
            pass  # Usuário não aceita DMs
        except Exception as e:
            logger.error(f"Erro ao notificar usuário: {e}")
    
    def _is_moderator(self, user: discord.Member) -> bool:
        """Verifica se usuário é moderador"""
        if user.guild_permissions.administrator:
            return True
        
        user_role_ids = {role.id for role in user.roles}
        return bool(user_role_ids.intersection(self.mod_role_ids))
    
    def get_user_warns(self, user_id: int) -> List[ModerationAction]:
        """Retorna warns de um usuário"""
        return self.user_warns.get(user_id, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        return {
            **self.stats,
            'total_users_warned': len(self.user_warns),
            'active_violations': sum(len(warns) for warns in self.user_warns.values())
        }
    
    async def clear_user_warns(self, user_id: int, moderator_id: int) -> int:
        """Limpa warns de um usuário"""
        warn_count = len(self.user_warns.get(user_id, []))
        if warn_count > 0:
            del self.user_warns[user_id]
            logger.info(f"Warns limpos para usuário {user_id} por moderador {moderator_id}")
        return warn_count
    
    def add_mod_role(self, role_id: int):
        """Adiciona role de moderador"""
        self.mod_role_ids.add(role_id)
    
    def remove_mod_role(self, role_id: int):
        """Remove role de moderador"""
        self.mod_role_ids.discard(role_id)
    
    def toggle_auto_moderation(self) -> bool:
        """Alterna moderação automática"""
        self.auto_moderation_enabled = not self.auto_moderation_enabled
        return self.auto_moderation_enabled
    
    # ==================== MÉTODOS DE COMANDO DO DISCORD ====================
    
    async def warn_user(self, user: discord.Member, moderator: discord.Member, reason: str) -> discord.Embed:
        """Comando para advertir usuário manualmente"""
        try:
            # Criar ação de moderação
            action = ModerationAction(
                user_id=user.id,
                action_type=ActionType.WARN,
                violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                reason=reason,
                timestamp=datetime.now(),
                moderator_id=moderator.id
            )
            
            # Adicionar warn
            self.user_warns[user.id].append(action)
            warn_count = len(self.user_warns[user.id])
            
            # Verificar se precisa de ação adicional
            additional_action = None
            if warn_count in self.warn_thresholds:
                additional_action = self.warn_thresholds[warn_count]
                await self._execute_action(user, additional_action, f"Acumulou {warn_count} warns")
            
            # Log da ação
            await self._log_action(action, user.guild, additional_action)
            
            # Notificar usuário
            await self._notify_user(user, action, warn_count)
            
            # Criar embed de resposta
            embed = discord.Embed(
                title="⚠️ Advertência Aplicada",
                description=f"Usuário {user.mention} foi advertido com sucesso.",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="📝 Motivo", value=reason, inline=False)
            embed.add_field(name="⚠️ Total de Warns", value=f"{warn_count}/7", inline=True)
            embed.add_field(name="👮 Moderador", value=moderator.mention, inline=True)
            
            if additional_action:
                embed.add_field(
                    name="🔨 Ação Adicional", 
                    value=additional_action.value.replace('_', ' ').title(), 
                    inline=True
                )
            
            embed.set_footer(text="Sistema de Moderação - Hawk Esports")
            embed.timestamp = datetime.now()
            
            self.stats['actions_taken'] += 1
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao advertir usuário: {e}")
            return discord.Embed(
                title="❌ Erro",
                description=f"Erro ao aplicar advertência: {str(e)}",
                color=discord.Color.red()
            )
    
    async def get_user_warnings(self, user: discord.Member) -> discord.Embed:
        """Comando para mostrar advertências de um usuário"""
        try:
            warns = self.get_user_warns(user.id)
            
            embed = discord.Embed(
                title="📋 Advertências do Usuário",
                description=f"Advertências de {user.mention}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="⚠️ Total de Warns", value=f"{len(warns)}/7", inline=True)
            
            if warns:
                # Mostrar últimas 5 advertências
                recent_warns = warns[-5:]
                warns_text = ""
                
                for i, warn in enumerate(recent_warns, 1):
                    date_str = warn.timestamp.strftime("%d/%m/%Y %H:%M")
                    warns_text += f"**{i}.** {warn.reason}\n📅 {date_str}\n\n"
                
                embed.add_field(name="📝 Últimas Advertências", value=warns_text[:1024], inline=False)
                
                if len(warns) > 5:
                    embed.add_field(
                        name="ℹ️ Informação", 
                        value=f"Mostrando apenas as 5 mais recentes de {len(warns)} advertências.", 
                        inline=False
                    )
            else:
                embed.add_field(name="✅ Status", value="Nenhuma advertência encontrada.", inline=False)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="Sistema de Moderação - Hawk Esports")
            embed.timestamp = datetime.now()
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao buscar advertências: {e}")
            return discord.Embed(
                title="❌ Erro",
                description=f"Erro ao buscar advertências: {str(e)}",
                color=discord.Color.red()
            )
    
    async def clear_user_warnings(self, user: discord.Member, moderator: discord.Member) -> discord.Embed:
        """Comando para limpar advertências de um usuário"""
        try:
            warn_count = await self.clear_user_warns(user.id, moderator.id)
            
            embed = discord.Embed(
                title="🧹 Advertências Removidas",
                description=f"Advertências de {user.mention} foram removidas com sucesso.",
                color=discord.Color.green()
            )
            
            embed.add_field(name="📊 Warns Removidos", value=str(warn_count), inline=True)
            embed.add_field(name="👮 Moderador", value=moderator.mention, inline=True)
            
            embed.set_footer(text="Sistema de Moderação - Hawk Esports")
            embed.timestamp = datetime.now()
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao limpar advertências: {e}")
            return discord.Embed(
                title="❌ Erro",
                description=f"Erro ao limpar advertências: {str(e)}",
                color=discord.Color.red()
            )
    
    async def configure_automod(self, guild_id: int, action: str, value: str = None) -> discord.Embed:
        """Comando para configurar sistema de moderação automática"""
        try:
            embed = discord.Embed(
                title="🛡️ Configuração de Automoderação",
                color=discord.Color.blue()
            )
            
            if action == "toggle":
                enabled = self.toggle_auto_moderation()
                status = "ativada" if enabled else "desativada"
                embed.description = f"Moderação automática foi **{status}**."
                embed.color = discord.Color.green() if enabled else discord.Color.red()
                
            elif action == "spam_limit":
                if value and value.isdigit():
                    new_limit = int(value)
                    if 1 <= new_limit <= 20:
                        self.spam_detector.message_limit = new_limit
                        embed.description = f"Limite de spam definido para **{new_limit}** mensagens."
                        embed.color = discord.Color.green()
                    else:
                        embed.description = "❌ Limite deve estar entre 1 e 20."
                        embed.color = discord.Color.red()
                else:
                    embed.description = "❌ Valor inválido. Use um número entre 1 e 20."
                    embed.color = discord.Color.red()
                    
            elif action == "toxicity_filter":
                if value and value.lower() in ["on", "off"]:
                    enabled = value.lower() == "on"
                    self.toxicity_filter.enabled = enabled
                    status = "ativado" if enabled else "desativado"
                    embed.description = f"Filtro de toxicidade foi **{status}**."
                    embed.color = discord.Color.green() if enabled else discord.Color.red()
                else:
                    embed.description = "❌ Use 'on' ou 'off'."
                    embed.color = discord.Color.red()
                    
            elif action == "raid_protection":
                if value and value.lower() in ["on", "off"]:
                    enabled = value.lower() == "on"
                    self.raid_protection.enabled = enabled
                    status = "ativada" if enabled else "desativada"
                    embed.description = f"Proteção anti-raid foi **{status}**."
                    embed.color = discord.Color.green() if enabled else discord.Color.red()
                else:
                    embed.description = "❌ Use 'on' ou 'off'."
                    embed.color = discord.Color.red()
                    
            elif action == "status":
                embed.description = "📊 **Status da Automoderação**"
                
                status_text = f"""
                🛡️ **Sistema:** {'🟢 Ativo' if self.auto_moderation_enabled else '🔴 Inativo'}
                📨 **Limite de Spam:** {self.spam_detector.message_limit} mensagens
                🚫 **Filtro de Toxicidade:** {'🟢 Ativo' if getattr(self.toxicity_filter, 'enabled', True) else '🔴 Inativo'}
                🛡️ **Proteção Anti-Raid:** {'🟢 Ativa' if getattr(self.raid_protection, 'enabled', True) else '🔴 Inativa'}
                
                📊 **Estatísticas:**
                • Mensagens verificadas: {self.stats['messages_checked']}
                • Violações detectadas: {self.stats['violations_detected']}
                • Ações tomadas: {self.stats['actions_taken']}
                • Usuários com warns: {len(self.user_warns)}
                """
                
                embed.add_field(name="ℹ️ Informações", value=status_text, inline=False)
                
            else:
                embed.description = "❌ Ação inválida."
                embed.color = discord.Color.red()
            
            embed.set_footer(text="Sistema de Moderação - Hawk Esports")
            embed.timestamp = datetime.now()
            
            return embed
            
        except Exception as e:
            logger.error(f"Erro ao configurar automoderação: {e}")
            return discord.Embed(
                title="❌ Erro",
                description=f"Erro ao configurar automoderação: {str(e)}",
                color=discord.Color.red()
            )