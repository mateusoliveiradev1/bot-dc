#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Keep Alive para Render
Evita que o bot hiberne fazendo ping interno a cada 10 minutos
"""

import asyncio
import aiohttp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self, bot, url=None):
        self.bot = bot
        self.url = url or "https://hawk-esports-bot.onrender.com"  # Substitua pela sua URL do Render
        self.session = None
        self.keep_alive_task = None
        
    async def start(self):
        """Inicia o sistema keep alive"""
        if self.keep_alive_task is None or self.keep_alive_task.done():
            self.session = aiohttp.ClientSession()
            self.keep_alive_task = asyncio.create_task(self._keep_alive_loop())
            logger.info("🔄 Sistema Keep Alive iniciado")
    
    async def stop(self):
        """Para o sistema keep alive"""
        if self.keep_alive_task:
            self.keep_alive_task.cancel()
            try:
                await self.keep_alive_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
            
        logger.info("⏹️ Sistema Keep Alive parado")
    
    async def _keep_alive_loop(self):
        """Loop principal do keep alive"""
        while True:
            try:
                await asyncio.sleep(600)  # 10 minutos
                await self._ping_self()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no keep alive: {e}")
                await asyncio.sleep(60)  # Espera 1 minuto antes de tentar novamente
    
    async def _ping_self(self):
        """Faz ping no próprio serviço"""
        try:
            async with self.session.get(f"{self.url}/health", timeout=30) as response:
                if response.status == 200:
                    logger.info(f"✅ Keep alive ping successful - {datetime.now().strftime('%H:%M:%S')}")
                else:
                    logger.warning(f"⚠️ Keep alive ping returned {response.status}")
        except asyncio.TimeoutError:
            logger.warning("⏰ Keep alive ping timeout")
        except Exception as e:
            logger.error(f"❌ Keep alive ping failed: {e}")
    
    async def health_check(self):
        """Endpoint de health check simples"""
        return {
            "status": "ok",
            "bot_status": "online" if self.bot.is_ready() else "offline",
            "timestamp": datetime.now().isoformat(),
            "guilds": len(self.bot.guilds) if self.bot.is_ready() else 0
        }

# Função para adicionar ao web dashboard
def add_health_endpoint(app, keep_alive):
    """Adiciona endpoint de health check ao Flask app"""
    
    @app.route('/health')
    async def health():
        health_data = await keep_alive.health_check()
        return health_data, 200
    
    @app.route('/ping')
    async def ping():
        return {"message": "pong", "timestamp": datetime.now().isoformat()}, 200