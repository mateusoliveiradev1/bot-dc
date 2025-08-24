#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Lembretes Automáticos para Check-in
Gerencia lembretes personalizados e automáticos para sessões

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger('HawkBot.CheckInReminders')

class ReminderType:
    """Tipos de lembretes disponíveis"""
    SESSION_START = "session_start"
    CHECKIN_DEADLINE = "checkin_deadline"
    SESSION_END = "session_end"
    CHECKOUT_REMINDER = "checkout_reminder"
    CUSTOM = "custom"

class CheckInReminders:
    """Sistema de lembretes automáticos para check-in"""
    
    def __init__(self, bot, checkin_system, storage):
        self.bot = bot
        self.checkin_system = checkin_system
        self.storage = storage
        self.active_reminders = {}
        self.reminder_settings = self._load_reminder_settings()
        
        # Task será iniciada no setup_hook do bot
        
        logger.info("Sistema de Lembretes de Check-in inicializado")
    
    def _load_reminder_settings(self) -> Dict[str, Any]:
        """Carrega configurações de lembretes"""
        if "reminder_settings" not in self.storage.data:
            self.storage.data["reminder_settings"] = {
                "default_reminders": {
                    ReminderType.SESSION_START: [30, 15, 5],  # minutos antes
                    ReminderType.CHECKIN_DEADLINE: [10, 5],   # minutos antes do deadline
                    ReminderType.SESSION_END: [15, 5],        # minutos antes do fim
                    ReminderType.CHECKOUT_REMINDER: [30]      # minutos após o fim
                },
                "custom_reminders": {},
                "enabled_reminders": {
                    ReminderType.SESSION_START: True,
                    ReminderType.CHECKIN_DEADLINE: True,
                    ReminderType.SESSION_END: True,
                    ReminderType.CHECKOUT_REMINDER: True
                }
            }
            self.storage.save_data()
        
        return self.storage.data["reminder_settings"]
    
    def _save_reminder_settings(self):
        """Salva configurações de lembretes"""
        self.storage.data["reminder_settings"] = self.reminder_settings
        self.storage.save_data()
    
    @tasks.loop(minutes=1)
    async def reminder_task(self):
        """Task principal de verificação de lembretes"""
        try:
            await self._check_session_reminders()
            await self._check_custom_reminders()
        except Exception as e:
            logger.error(f"Erro na task de lembretes: {e}")
    
    @reminder_task.before_loop
    async def before_reminder_task(self):
        """Aguarda o bot estar pronto"""
        await self.bot.wait_until_ready()
    
    def start_reminder_task(self):
        """Inicia a task de lembretes"""
        if not self.reminder_task.is_running():
            self.reminder_task.start()
            logger.info("Task de lembretes iniciada")
    
    async def _check_session_reminders(self):
        """Verifica lembretes de sessões"""
        now = datetime.now()
        active_sessions = self.checkin_system.get_active_sessions()
        
        for session in active_sessions:
            session_id = session['id']
            start_time = datetime.fromisoformat(session['start_time'])
            end_time = datetime.fromisoformat(session['end_time'])
            
            # Lembretes de início de sessão
            if self.reminder_settings['enabled_reminders'].get(ReminderType.SESSION_START, True):
                await self._check_start_reminders(session, start_time, now)
            
            # Lembretes de deadline de check-in (15 min após início)
            checkin_deadline = start_time + timedelta(minutes=15)
            if self.reminder_settings['enabled_reminders'].get(ReminderType.CHECKIN_DEADLINE, True):
                await self._check_checkin_deadline_reminders(session, checkin_deadline, now)
            
            # Lembretes de fim de sessão
            if self.reminder_settings['enabled_reminders'].get(ReminderType.SESSION_END, True):
                await self._check_end_reminders(session, end_time, now)
            
            # Lembretes de check-out (após fim da sessão)
            if self.reminder_settings['enabled_reminders'].get(ReminderType.CHECKOUT_REMINDER, True):
                await self._check_checkout_reminders(session, end_time, now)
    
    async def _check_start_reminders(self, session: Dict, start_time: datetime, now: datetime):
        """Verifica lembretes de início de sessão"""
        session_id = session['id']
        reminder_times = self.reminder_settings['default_reminders'][ReminderType.SESSION_START]
        
        for minutes_before in reminder_times:
            reminder_time = start_time - timedelta(minutes=minutes_before)
            reminder_key = f"{session_id}_start_{minutes_before}"
            
            if (now >= reminder_time and 
                reminder_key not in self.active_reminders and
                now < start_time):
                
                await self._send_start_reminder(session, minutes_before)
                self.active_reminders[reminder_key] = now.isoformat()
    
    async def _check_checkin_deadline_reminders(self, session: Dict, deadline: datetime, now: datetime):
        """Verifica lembretes de deadline de check-in"""
        session_id = session['id']
        reminder_times = self.reminder_settings['default_reminders'][ReminderType.CHECKIN_DEADLINE]
        
        for minutes_before in reminder_times:
            reminder_time = deadline - timedelta(minutes=minutes_before)
            reminder_key = f"{session_id}_checkin_deadline_{minutes_before}"
            
            if (now >= reminder_time and 
                reminder_key not in self.active_reminders and
                now < deadline):
                
                await self._send_checkin_deadline_reminder(session, minutes_before)
                self.active_reminders[reminder_key] = now.isoformat()
    
    async def _check_end_reminders(self, session: Dict, end_time: datetime, now: datetime):
        """Verifica lembretes de fim de sessão"""
        session_id = session['id']
        reminder_times = self.reminder_settings['default_reminders'][ReminderType.SESSION_END]
        
        for minutes_before in reminder_times:
            reminder_time = end_time - timedelta(minutes=minutes_before)
            reminder_key = f"{session_id}_end_{minutes_before}"
            
            if (now >= reminder_time and 
                reminder_key not in self.active_reminders and
                now < end_time):
                
                await self._send_end_reminder(session, minutes_before)
                self.active_reminders[reminder_key] = now.isoformat()
    
    async def _check_checkout_reminders(self, session: Dict, end_time: datetime, now: datetime):
        """Verifica lembretes de check-out"""
        session_id = session['id']
        reminder_times = self.reminder_settings['default_reminders'][ReminderType.CHECKOUT_REMINDER]
        
        for minutes_after in reminder_times:
            reminder_time = end_time + timedelta(minutes=minutes_after)
            reminder_key = f"{session_id}_checkout_{minutes_after}"
            
            if (now >= reminder_time and 
                reminder_key not in self.active_reminders):
                
                await self._send_checkout_reminder(session)
                self.active_reminders[reminder_key] = now.isoformat()
    
    async def _check_custom_reminders(self):
        """Verifica lembretes personalizados"""
        now = datetime.now()
        custom_reminders = self.reminder_settings.get('custom_reminders', {})
        
        for reminder_id, reminder_data in list(custom_reminders.items()):
            reminder_time = datetime.fromisoformat(reminder_data['time'])
            
            if now >= reminder_time and not reminder_data.get('sent', False):
                await self._send_custom_reminder(reminder_data)
                custom_reminders[reminder_id]['sent'] = True
                self._save_reminder_settings()
    
    async def _send_start_reminder(self, session: Dict, minutes_before: int):
        """Envia lembrete de início de sessão"""
        try:
            embed = discord.Embed(
                title="🚨 Lembrete de Sessão",
                description=f"A sessão **{session['id']}** começará em **{minutes_before} minutos**!",
                color=0xFFD700,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Detalhes",
                value=f"**Tipo:** {session['type'].title()}\n"
                      f"**Início:** <t:{int(datetime.fromisoformat(session['start_time']).timestamp())}:t>\n"
                      f"**Jogadores:** {session['checkin_count']}/{session['max_players']}",
                inline=False
            )
            
            embed.add_field(
                name="⚡ Ação Necessária",
                value="Prepare-se para a sessão e faça seu check-in quando disponível!",
                inline=False
            )
            
            # Enviar para canal de notificações (assumindo que existe)
            # Aqui você pode personalizar para o canal específico da guild
            await self._send_reminder_to_channels(embed, session)
            
            logger.info(f"Lembrete de início enviado para sessão {session['id']} ({minutes_before} min)")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete de início: {e}")
    
    async def _send_checkin_deadline_reminder(self, session: Dict, minutes_before: int):
        """Envia lembrete de deadline de check-in"""
        try:
            embed = discord.Embed(
                title="⏰ Deadline de Check-in",
                description=f"O deadline para check-in na sessão **{session['id']}** é em **{minutes_before} minutos**!",
                color=0xFF6B35,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎯 Última Chance",
                value="Faça seu check-in agora ou perderá a vaga na sessão!",
                inline=False
            )
            
            await self._send_reminder_to_channels(embed, session)
            
            logger.info(f"Lembrete de deadline enviado para sessão {session['id']} ({minutes_before} min)")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete de deadline: {e}")
    
    async def _send_end_reminder(self, session: Dict, minutes_before: int):
        """Envia lembrete de fim de sessão"""
        try:
            embed = discord.Embed(
                title="🏁 Sessão Terminando",
                description=f"A sessão **{session['id']}** terminará em **{minutes_before} minutos**!",
                color=0x8B4513,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Status Atual",
                value=f"**Jogadores Ativos:** {session['checkin_count']}\n"
                      f"**Check-outs:** {session['checkout_count']}",
                inline=False
            )
            
            await self._send_reminder_to_channels(embed, session)
            
            logger.info(f"Lembrete de fim enviado para sessão {session['id']} ({minutes_before} min)")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete de fim: {e}")
    
    async def _send_checkout_reminder(self, session: Dict):
        """Envia lembrete de check-out"""
        try:
            embed = discord.Embed(
                title="👋 Lembrete de Check-out",
                description=f"A sessão **{session['id']}** terminou. Não se esqueça de fazer seu check-out!",
                color=0x4169E1,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 Importante",
                value="O check-out é importante para registrar sua participação completa na sessão.",
                inline=False
            )
            
            await self._send_reminder_to_channels(embed, session)
            
            logger.info(f"Lembrete de check-out enviado para sessão {session['id']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete de check-out: {e}")
    
    async def _send_custom_reminder(self, reminder_data: Dict):
        """Envia lembrete personalizado"""
        try:
            embed = discord.Embed(
                title="📢 Lembrete Personalizado",
                description=reminder_data['message'],
                color=0x9932CC,
                timestamp=datetime.now()
            )
            
            if 'author' in reminder_data:
                embed.set_footer(text=f"Criado por: {reminder_data['author']}")
            
            # Enviar para canal específico se definido
            if 'channel_id' in reminder_data:
                channel = self.bot.get_channel(reminder_data['channel_id'])
                if channel:
                    await channel.send(embed=embed)
            
            logger.info(f"Lembrete personalizado enviado: {reminder_data.get('title', 'Sem título')}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete personalizado: {e}")
    
    async def _send_reminder_to_channels(self, embed: discord.Embed, session: Dict):
        """Envia lembrete para canais apropriados"""
        # Aqui você pode implementar lógica para determinar
        # quais canais devem receber os lembretes baseado na sessão
        # Por exemplo, canal específico da guild, canal de notificações, etc.
        
        # Exemplo básico - enviar para todos os canais de texto das guilds
        for guild in self.bot.guilds:
            # Procurar canal de notificações ou similar
            notification_channels = [
                channel for channel in guild.text_channels 
                if any(keyword in channel.name.lower() 
                      for keyword in ['notif', 'avisos', 'geral', 'check-in'])
            ]
            
            if notification_channels:
                try:
                    await notification_channels[0].send(embed=embed)
                except discord.Forbidden:
                    logger.warning(f"Sem permissão para enviar em {notification_channels[0].name}")
                except Exception as e:
                    logger.error(f"Erro ao enviar lembrete: {e}")
    
    def create_custom_reminder(self, title: str, message: str, reminder_time: datetime, 
                             channel_id: Optional[int] = None, author: Optional[str] = None) -> str:
        """Cria um lembrete personalizado"""
        reminder_id = f"custom_{int(datetime.now().timestamp())}"
        
        reminder_data = {
            'id': reminder_id,
            'title': title,
            'message': message,
            'time': reminder_time.isoformat(),
            'created_at': datetime.now().isoformat(),
            'sent': False
        }
        
        if channel_id:
            reminder_data['channel_id'] = channel_id
        if author:
            reminder_data['author'] = author
        
        self.reminder_settings['custom_reminders'][reminder_id] = reminder_data
        self._save_reminder_settings()
        
        logger.info(f"Lembrete personalizado criado: {title}")
        return reminder_id
    
    def delete_custom_reminder(self, reminder_id: str) -> bool:
        """Remove um lembrete personalizado"""
        if reminder_id in self.reminder_settings['custom_reminders']:
            del self.reminder_settings['custom_reminders'][reminder_id]
            self._save_reminder_settings()
            logger.info(f"Lembrete personalizado removido: {reminder_id}")
            return True
        return False
    
    def get_custom_reminders(self) -> List[Dict]:
        """Retorna lista de lembretes personalizados"""
        return list(self.reminder_settings['custom_reminders'].values())
    
    def update_reminder_settings(self, reminder_type: str, enabled: bool = None, 
                               times: List[int] = None) -> bool:
        """Atualiza configurações de lembretes"""
        try:
            if enabled is not None:
                self.reminder_settings['enabled_reminders'][reminder_type] = enabled
            
            if times is not None:
                self.reminder_settings['default_reminders'][reminder_type] = times
            
            self._save_reminder_settings()
            logger.info(f"Configurações de lembrete atualizadas: {reminder_type}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações de lembrete: {e}")
            return False
    
    def get_reminder_settings(self) -> Dict[str, Any]:
        """Retorna configurações atuais de lembretes"""
        return self.reminder_settings.copy()
    
    def cleanup_old_reminders(self, days_old: int = 7):
        """Remove lembretes antigos do cache"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Limpar lembretes ativos antigos
        old_reminders = [
            key for key, timestamp in self.active_reminders.items()
            if datetime.fromisoformat(timestamp) < cutoff_date
        ]
        
        for key in old_reminders:
            del self.active_reminders[key]
        
        # Limpar lembretes personalizados enviados
        custom_reminders = self.reminder_settings['custom_reminders']
        old_custom = [
            reminder_id for reminder_id, reminder_data in custom_reminders.items()
            if (reminder_data.get('sent', False) and 
                datetime.fromisoformat(reminder_data['created_at']) < cutoff_date)
        ]
        
        for reminder_id in old_custom:
            del custom_reminders[reminder_id]
        
        if old_reminders or old_custom:
            self._save_reminder_settings()
            logger.info(f"Limpeza de lembretes: {len(old_reminders)} ativos, {len(old_custom)} personalizados")
    
    def stop_reminders(self):
        """Para o sistema de lembretes"""
        if self.reminder_task.is_running():
            self.reminder_task.cancel()
        logger.info("Sistema de lembretes parado")