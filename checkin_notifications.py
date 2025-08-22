import discord
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from checkin_system import CheckInSystem, SessionType, CheckInStatus

logger = logging.getLogger(__name__)

class CheckInNotifications:
    def __init__(self, bot, checkin_system: CheckInSystem):
        self.bot = bot
        self.checkin_system = checkin_system
        self.notification_tasks: Dict[str, asyncio.Task] = {}
        
    async def setup_session_notifications(self, session_id: str, channel_id: int):
        """Configura notificações automáticas para uma sessão"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        # Cancelar notificações existentes para esta sessão
        await self.cancel_session_notifications(session_id)
        
        # Criar tarefas de notificação
        tasks = []
        
        # Notificação de início da sessão (5 minutos antes)
        start_time = datetime.fromisoformat(session['start_time'])
        reminder_time = start_time - timedelta(minutes=5)
        if reminder_time > datetime.now():
            task = asyncio.create_task(
                self._schedule_notification(
                    reminder_time,
                    self._send_session_start_reminder,
                    session_id, channel_id
                )
            )
            tasks.append(task)
            
        # Notificação de início da sessão
        if start_time > datetime.now():
            task = asyncio.create_task(
                self._schedule_notification(
                    start_time,
                    self._send_session_started,
                    session_id, channel_id
                )
            )
            tasks.append(task)
            
        # Lembretes de check-in (a cada 10 minutos após o início)
        checkin_reminder_times = [
            start_time + timedelta(minutes=10),
            start_time + timedelta(minutes=20),
            start_time + timedelta(minutes=30)
        ]
        
        for reminder_time in checkin_reminder_times:
            if reminder_time > datetime.now():
                task = asyncio.create_task(
                    self._schedule_notification(
                        reminder_time,
                        self._send_checkin_reminder,
                        session_id, channel_id
                    )
                )
                tasks.append(task)
                
        # Notificação de fim da sessão (5 minutos antes)
        if session['end_time']:
            end_time = datetime.fromisoformat(session['end_time'])
            end_reminder_time = end_time - timedelta(minutes=5)
            if end_reminder_time > datetime.now():
                task = asyncio.create_task(
                    self._schedule_notification(
                        end_reminder_time,
                        self._send_session_end_reminder,
                        session_id, channel_id
                    )
                )
                tasks.append(task)
                
        self.notification_tasks[session_id] = tasks
        
    async def cancel_session_notifications(self, session_id: str):
        """Cancela todas as notificações de uma sessão"""
        if session_id in self.notification_tasks:
            for task in self.notification_tasks[session_id]:
                if not task.done():
                    task.cancel()
            del self.notification_tasks[session_id]
            
    async def _schedule_notification(self, when: datetime, callback, *args):
        """Agenda uma notificação para um horário específico"""
        now = datetime.now()
        if when <= now:
            return
            
        delay = (when - now).total_seconds()
        await asyncio.sleep(delay)
        
        try:
            await callback(*args)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            
    async def _send_session_start_reminder(self, session_id: str, channel_id: int):
        """Envia lembrete de início da sessão"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="🔔 Lembrete de Sessão",
            description=f"A sessão **{session['name']}** começará em 5 minutos!",
            color=0xFFAA00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Tipo",
            value=session['session_type'].replace('_', ' ').title(),
            inline=True
        )
        
        embed.add_field(
            name="Início",
            value=f"<t:{int(datetime.fromisoformat(session['start_time']).timestamp())}:t>",
            inline=True
        )
        
        if session['max_players']:
            embed.add_field(
                name="Vagas",
                value=f"{len(session['checked_in_players'])}/{session['max_players']}",
                inline=True
            )
            
        embed.set_footer(text="Prepare-se para fazer check-in!")
        
        await channel.send(embed=embed)
        
    async def _send_session_started(self, session_id: str, channel_id: int):
        """Envia notificação de início da sessão"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="🚀 Sessão Iniciada!",
            description=f"A sessão **{session['name']}** começou agora!",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Tipo",
            value=session['session_type'].replace('_', ' ').title(),
            inline=True
        )
        
        if session['max_players']:
            embed.add_field(
                name="Vagas Disponíveis",
                value=f"{session['max_players'] - len(session['checked_in_players'])}",
                inline=True
            )
            
        embed.add_field(
            name="Como Participar",
            value="Use `/checkin` para entrar na sessão!",
            inline=False
        )
        
        await channel.send(embed=embed)
        
    async def _send_checkin_reminder(self, session_id: str, channel_id: int):
        """Envia lembrete de check-in"""
        session = self.checkin_system.get_session_info(session_id)
        if not session or session['status'] != 'active':
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        # Verificar se ainda há vagas
        if session['max_players'] and len(session['checked_in_players']) >= session['max_players']:
            return
            
        embed = discord.Embed(
            title="⏰ Lembrete de Check-in",
            description=f"A sessão **{session['name']}** ainda tem vagas disponíveis!",
            color=0x0099FF,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Vagas Restantes",
            value=f"{session['max_players'] - len(session['checked_in_players']) if session['max_players'] else '∞'}",
            inline=True
        )
        
        embed.add_field(
            name="Participantes",
            value=f"{len(session['checked_in_players'])}",
            inline=True
        )
        
        embed.add_field(
            name="Como Entrar",
            value="Use `/checkin` para participar!",
            inline=False
        )
        
        await channel.send(embed=embed)
        
    async def _send_session_end_reminder(self, session_id: str, channel_id: int):
        """Envia lembrete de fim da sessão"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="⚠️ Sessão Terminando",
            description=f"A sessão **{session['name']}** terminará em 5 minutos!",
            color=0xFF6600,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Participantes Ativos",
            value=f"{len(session['checked_in_players'])}",
            inline=True
        )
        
        embed.add_field(
            name="Fim",
            value=f"<t:{int(datetime.fromisoformat(session['end_time']).timestamp())}:t>",
            inline=True
        )
        
        embed.add_field(
            name="Lembrete",
            value="Não esqueça de fazer check-out!",
            inline=False
        )
        
        await channel.send(embed=embed)
        
    async def send_checkin_notification(self, session_id: str, user_id: int, channel_id: int):
        """Envia notificação quando alguém faz check-in"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        user = self.bot.get_user(user_id)
        if not user:
            return
            
        embed = discord.Embed(
            title="✅ Check-in Realizado",
            description=f"{user.mention} fez check-in na sessão **{session['name']}**!",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Participantes",
            value=f"{len(session['checked_in_players'])}{f'/{session["max_players"]}' if session['max_players'] else ''}",
            inline=True
        )
        
        if session['max_players']:
            remaining = session['max_players'] - len(session['checked_in_players'])
            embed.add_field(
                name="Vagas Restantes",
                value=f"{remaining}",
                inline=True
            )
            
        await channel.send(embed=embed)
        
    async def send_checkout_notification(self, session_id: str, user_id: int, channel_id: int):
        """Envia notificação quando alguém faz check-out"""
        session = self.checkin_system.get_session_info(session_id)
        if not session:
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        user = self.bot.get_user(user_id)
        if not user:
            return
            
        embed = discord.Embed(
            title="❌ Check-out Realizado",
            description=f"{user.mention} fez check-out da sessão **{session['name']}**.",
            color=0xFF4444,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Participantes",
            value=f"{len(session['checked_in_players'])}{f'/{session["max_players"]}' if session['max_players'] else ''}",
            inline=True
        )
        
        if session['max_players']:
            remaining = session['max_players'] - len(session['checked_in_players'])
            embed.add_field(
                name="Vagas Disponíveis",
                value=f"{remaining}",
                inline=True
            )
            
        await channel.send(embed=embed)
        
    async def cleanup_finished_sessions(self):
        """Remove notificações de sessões finalizadas"""
        finished_sessions = []
        
        for session_id in list(self.notification_tasks.keys()):
            session = self.checkin_system.get_session_info(session_id)
            if not session or session['status'] in ['completed', 'cancelled']:
                finished_sessions.append(session_id)
                
        for session_id in finished_sessions:
            await self.cancel_session_notifications(session_id)
            
    async def start_cleanup_task(self):
        """Inicia tarefa de limpeza automática"""
        while True:
            try:
                await self.cleanup_finished_sessions()
                await asyncio.sleep(300)  # Verificar a cada 5 minutos
            except Exception as e:
                logger.error(f"Erro na limpeza de notificações: {e}")
                await asyncio.sleep(60)  # Tentar novamente em 1 minuto