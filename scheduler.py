#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Agendamento de Tarefas
Responsável por executar tarefas automáticas em intervalos regulares

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
import discord

logger = logging.getLogger('HawkBot.TaskScheduler')

class TaskScheduler:
    """Sistema de agendamento de tarefas automáticas"""
    
    def __init__(self, bot, storage, rank_system, medal_integration):
        self.bot = bot
        self.storage = storage
        self.rank_system = rank_system
        self.medal_integration = medal_integration
        
        # Configurações de agendamento (tempo real)
        self.rank_update_hour = int(os.getenv('CRON_HOUR', '12'))
        self.rank_update_minute = int(os.getenv('CRON_MINUTE', '0'))
        self.rank_update_interval = int(os.getenv('RANK_UPDATE_INTERVAL', '1'))  # horas (tempo real)
        
        # Estado das tarefas
        self.tasks = {}
        self.running = False
        self.last_executions = {}
        
        # Estatísticas
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'last_execution': None
        }
        
        logger.info("Agendador de tarefas inicializado")
    
    async def start(self):
        """Inicia o sistema de agendamento"""
        try:
            if self.running:
                logger.warning("Agendador já está em execução")
                return
            
            self.running = True
            
            # Registrar tarefas
            await self._register_tasks()
            
            # Iniciar loop principal
            self.tasks['main_loop'] = asyncio.create_task(self._main_loop())
            
            logger.info("Agendador de tarefas iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar agendador: {e}")
            self.running = False
    
    async def stop(self):
        """Para o sistema de agendamento"""
        try:
            self.running = False
            
            # Cancelar todas as tarefas
            for task_name, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.tasks.clear()
            logger.info("Agendador de tarefas parado")
            
        except Exception as e:
            logger.error(f"Erro ao parar agendador: {e}")
    
    async def _register_tasks(self):
        """Registra todas as tarefas automáticas"""
        try:
            # Tarefa de atualização de ranks
            self.tasks['rank_update'] = asyncio.create_task(
                self._schedule_rank_updates()
            )
            
            # Tarefa de limpeza de dados antigos
            self.tasks['data_cleanup'] = asyncio.create_task(
                self._schedule_data_cleanup()
            )
            
            # Tarefa de backup automático
            self.tasks['auto_backup'] = asyncio.create_task(
                self._schedule_auto_backup()
            )
            
            # Tarefa de limpeza de clipes antigos
            self.tasks['clips_cleanup'] = asyncio.create_task(
                self._schedule_clips_cleanup()
            )
            
            # Tarefa de estatísticas diárias
            self.tasks['daily_stats'] = asyncio.create_task(
                self._schedule_daily_stats()
            )
            
            logger.info(f"Registradas {len(self.tasks)} tarefas automáticas")
            
        except Exception as e:
            logger.error(f"Erro ao registrar tarefas: {e}")
    
    async def _main_loop(self):
        """Loop principal do agendador"""
        try:
            while self.running:
                # Verificar se o bot está pronto
                if not self.bot.is_ready():
                    await asyncio.sleep(30)
                    continue
                
                # Executar verificações periódicas
                await self._check_scheduled_tasks()
                
                # Aguardar próxima verificação (a cada 30 segundos para tempo real)
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info("Loop principal do agendador cancelado")
        except Exception as e:
            logger.error(f"Erro no loop principal do agendador: {e}")
    
    async def _check_scheduled_tasks(self):
        """Verifica e executa tarefas agendadas"""
        try:
            current_time = datetime.now()
            
            # Verificar atualização de ranks
            if self._should_execute_rank_update(current_time):
                await self._execute_rank_update()
            
            # Verificar limpeza de dados (diariamente às 2:00)
            if current_time.hour == 2 and current_time.minute == 0:
                if not self._was_executed_today('data_cleanup'):
                    await self._execute_data_cleanup()
            
            # Verificar backup automático (diariamente às 3:00)
            if current_time.hour == 3 and current_time.minute == 0:
                if not self._was_executed_today('auto_backup'):
                    await self._execute_auto_backup()
            
            # Verificar limpeza de clipes (semanalmente, domingo às 4:00)
            if (current_time.weekday() == 6 and current_time.hour == 4 and 
                current_time.minute == 0):
                if not self._was_executed_today('clips_cleanup'):
                    await self._execute_clips_cleanup()
            
            # Verificar estatísticas diárias (diariamente às 23:59)
            if current_time.hour == 23 and current_time.minute == 59:
                if not self._was_executed_today('daily_stats'):
                    await self._execute_daily_stats()
                    
        except Exception as e:
            logger.error(f"Erro ao verificar tarefas agendadas: {e}")
    
    def _should_execute_rank_update(self, current_time: datetime) -> bool:
        """Verifica se deve executar atualização de ranks"""
        try:
            # Verificar horário configurado
            if (current_time.hour == self.rank_update_hour and 
                current_time.minute == self.rank_update_minute):
                
                # Verificar se já foi executado hoje
                if not self._was_executed_today('rank_update'):
                    return True
            
            # Verificar intervalo alternativo
            last_execution = self.last_executions.get('rank_update')
            if last_execution:
                hours_since_last = (current_time - last_execution).total_seconds() / 3600
                if hours_since_last >= self.rank_update_interval:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar atualização de ranks: {e}")
            return False
    
    def _was_executed_today(self, task_name: str) -> bool:
        """Verifica se uma tarefa já foi executada hoje"""
        last_execution = self.last_executions.get(task_name)
        if not last_execution:
            return False
        
        return last_execution.date() == datetime.now().date()
    
    async def _execute_rank_update(self):
        """Executa atualização de ranks"""
        try:
            logger.info("Iniciando atualização automática de ranks")
            
            # Buscar todos os servidores onde o bot está
            for guild in self.bot.guilds:
                try:
                    result = await self.rank_system.update_all_ranks(str(guild.id))
                    
                    if result.get('success', True):  # Assumir sucesso se não especificado
                        logger.info(
                            f"Ranks atualizados no servidor {guild.name}: "
                            f"{result.get('updated', 0)}/{result.get('total_players', 0)}"
                        )
                        
                        # Enviar relatório se houver mudanças significativas
                        if result.get('rank_changes', []):
                            await self._send_rank_update_report(guild, result)
                    else:
                        logger.error(f"Erro na atualização de ranks em {guild.name}")
                        
                except Exception as e:
                    logger.error(f"Erro ao atualizar ranks no servidor {guild.name}: {e}")
            
            self._mark_task_executed('rank_update')
            logger.info("Atualização automática de ranks concluída")
            
        except Exception as e:
            logger.error(f"Erro na execução da atualização de ranks: {e}")
            self._mark_task_failed('rank_update')
    
    async def _execute_data_cleanup(self):
        """Executa limpeza de dados antigos"""
        try:
            logger.info("Iniciando limpeza de dados antigos")
            
            # Limpar dados antigos do storage
            cleaned_items = self.storage.cleanup_old_data(days=90)
            
            # Limpar cache da API PUBG se disponível
            if hasattr(self.rank_system, 'pubg_api'):
                self.rank_system.pubg_api.clear_cache()
            
            self._mark_task_executed('data_cleanup')
            logger.info(f"Limpeza de dados concluída: {cleaned_items} itens removidos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")
            self._mark_task_failed('data_cleanup')
    
    async def _execute_auto_backup(self):
        """Executa backup automático"""
        try:
            logger.info("Iniciando backup automático")
            
            # Criar backup
            backup_path = self.storage.create_backup()
            
            # Limpar backups antigos
            cleaned_backups = self.storage.cleanup_old_backups(keep_days=30)
            
            self._mark_task_executed('auto_backup')
            logger.info(
                f"Backup automático concluído: {backup_path}, "
                f"{cleaned_backups} backups antigos removidos"
            )
            
        except Exception as e:
            logger.error(f"Erro no backup automático: {e}")
            self._mark_task_failed('auto_backup')
    
    async def _execute_clips_cleanup(self):
        """Executa limpeza de clipes antigos"""
        try:
            logger.info("Iniciando limpeza de clipes antigos")
            
            # Limpar clipes antigos (mais de 60 dias)
            removed_clips = await self.medal_integration.cleanup_old_clips(days=60)
            
            self._mark_task_executed('clips_cleanup')
            logger.info(f"Limpeza de clipes concluída: {removed_clips} clipes removidos")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de clipes: {e}")
            self._mark_task_failed('clips_cleanup')
    
    async def _execute_daily_stats(self):
        """Executa coleta de estatísticas diárias"""
        try:
            logger.info("Coletando estatísticas diárias")
            
            # Coletar estatísticas
            stats = {
                'date': datetime.now().date().isoformat(),
                'total_players': len(self.storage.get_all_players()),
                'total_clips': len(self.storage.get_clips()),
                'guilds': len(self.bot.guilds),
                'scheduler_stats': self.execution_stats.copy()
            }
            
            # Salvar estatísticas
            self.storage.save_daily_stats(stats)
            
            self._mark_task_executed('daily_stats')
            logger.info("Estatísticas diárias coletadas")
            
        except Exception as e:
            logger.error(f"Erro ao coletar estatísticas diárias: {e}")
            self._mark_task_failed('daily_stats')
    
    async def _send_rank_update_report(self, guild: discord.Guild, result: Dict[str, Any]):
        """Envia relatório de atualização de ranks"""
        try:
            # Encontrar canal de anúncios
            announcements_channel = discord.utils.get(
                guild.channels,
                name=os.getenv('ANNOUNCEMENTS_CHANNEL_NAME', 'anúncios')
            )
            
            if not announcements_channel:
                return
            
            # Criar embed do relatório
            embed = discord.Embed(
                title="📊 Relatório de Atualização de Ranks",
                description="**Hawk Esports** - Atualização automática concluída",
                color=int(os.getenv('CLAN_EMBED_COLOR', '0x00ff00'), 16),
                timestamp=datetime.now()
            )
            
            # Estatísticas gerais
            embed.add_field(
                name="📈 Estatísticas",
                value=f"Jogadores atualizados: **{result.get('updated', 0)}**\n"
                      f"Total de jogadores: **{result.get('total_players', 0)}**\n"
                      f"Erros: **{result.get('errors', 0)}**",
                inline=True
            )
            
            # Mudanças de rank
            rank_changes = result.get('rank_changes', [])
            if rank_changes:
                changes_text = ""
                for change in rank_changes[:5]:  # Mostrar apenas os primeiros 5
                    changes_text += (
                        f"**{change['player_name']}**\n"
                        f"Ranked: {change['old_ranks']['ranked']} → {change['new_ranks']['ranked']}\n"
                        f"MM: {change['old_ranks']['mm']} → {change['new_ranks']['mm']}\n\n"
                    )
                
                if len(rank_changes) > 5:
                    changes_text += f"... e mais {len(rank_changes) - 5} mudanças"
                
                embed.add_field(
                    name="🔄 Mudanças de Rank",
                    value=changes_text or "Nenhuma mudança",
                    inline=False
                )
            
            # Novas conquistas
            achievements = result.get('new_achievements', [])
            if achievements:
                achievements_text = ""
                for achievement in achievements[:3]:  # Mostrar apenas as primeiras 3
                    achievements_text += (
                        f"**{achievement['player_name']}** - {achievement['achievement']}\n"
                    )
                
                if len(achievements) > 3:
                    achievements_text += f"... e mais {len(achievements) - 3} conquistas"
                
                embed.add_field(
                    name="🏅 Novas Conquistas",
                    value=achievements_text,
                    inline=False
                )
            
            embed.set_footer(
                text="Próxima atualização em 24 horas",
                icon_url=os.getenv('CLAN_LOGO_URL', '')
            )
            
            await announcements_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao enviar relatório de ranks: {e}")
    
    def _mark_task_executed(self, task_name: str):
        """Marca uma tarefa como executada com sucesso"""
        self.last_executions[task_name] = datetime.now()
        self.execution_stats['total_executions'] += 1
        self.execution_stats['successful_executions'] += 1
        self.execution_stats['last_execution'] = datetime.now().isoformat()
    
    def _mark_task_failed(self, task_name: str):
        """Marca uma tarefa como falhada"""
        self.execution_stats['total_executions'] += 1
        self.execution_stats['failed_executions'] += 1
    
    async def _schedule_rank_updates(self):
        """Tarefa dedicada para atualização de ranks (tempo real)"""
        try:
            while self.running:
                await asyncio.sleep(1800)  # Verificar a cada 30 minutos (tempo real)
                
        except asyncio.CancelledError:
            logger.info("Tarefa de atualização de ranks cancelada")
    
    async def _schedule_data_cleanup(self):
        """Tarefa dedicada para limpeza de dados"""
        try:
            while self.running:
                await asyncio.sleep(3600)  # Verificar a cada hora
                
        except asyncio.CancelledError:
            logger.info("Tarefa de limpeza de dados cancelada")
    
    async def _schedule_auto_backup(self):
        """Tarefa dedicada para backup automático"""
        try:
            while self.running:
                await asyncio.sleep(3600)  # Verificar a cada hora
                
        except asyncio.CancelledError:
            logger.info("Tarefa de backup automático cancelada")
    
    async def _schedule_clips_cleanup(self):
        """Tarefa dedicada para limpeza de clipes"""
        try:
            while self.running:
                await asyncio.sleep(3600)  # Verificar a cada hora
                
        except asyncio.CancelledError:
            logger.info("Tarefa de limpeza de clipes cancelada")
    
    async def _schedule_daily_stats(self):
        """Tarefa dedicada para estatísticas diárias"""
        try:
            while self.running:
                await asyncio.sleep(3600)  # Verificar a cada hora
                
        except asyncio.CancelledError:
            logger.info("Tarefa de estatísticas diárias cancelada")
    
    async def force_task_execution(self, task_name: str) -> bool:
        """Força a execução de uma tarefa específica"""
        try:
            logger.info(f"Forçando execução da tarefa: {task_name}")
            
            if task_name == 'rank_update':
                await self._execute_rank_update()
            elif task_name == 'data_cleanup':
                await self._execute_data_cleanup()
            elif task_name == 'auto_backup':
                await self._execute_auto_backup()
            elif task_name == 'clips_cleanup':
                await self._execute_clips_cleanup()
            elif task_name == 'daily_stats':
                await self._execute_daily_stats()
            else:
                logger.warning(f"Tarefa desconhecida: {task_name}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao forçar execução da tarefa {task_name}: {e}")
            return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Retorna status do agendador"""
        return {
            'running': self.running,
            'active_tasks': len([t for t in self.tasks.values() if not t.done()]),
            'total_tasks': len(self.tasks),
            'last_executions': {
                name: execution.isoformat() if execution else None
                for name, execution in self.last_executions.items()
            },
            'execution_stats': self.execution_stats.copy(),
            'next_rank_update': self._get_next_rank_update_time()
        }
    
    def _get_next_rank_update_time(self) -> str:
        """Calcula próxima atualização de ranks"""
        try:
            now = datetime.now()
            next_update = now.replace(
                hour=self.rank_update_hour,
                minute=self.rank_update_minute,
                second=0,
                microsecond=0
            )
            
            # Se já passou da hora hoje, agendar para amanhã
            if next_update <= now:
                next_update += timedelta(days=1)
            
            return next_update.isoformat()
            
        except Exception as e:
            logger.error(f"Erro ao calcular próxima atualização: {e}")
            return "Erro"