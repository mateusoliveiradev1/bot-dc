import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database import DatabaseManager, DatabaseConfig

class PostgreSQLStorage:
    """Sistema de armazenamento usando PostgreSQL"""
    
    def __init__(self):
        self.db_config = DatabaseConfig.from_env()
        self.db = DatabaseManager(self.db_config)
        self._initialized = False
    
    async def initialize(self):
        """Inicializa o sistema de armazenamento"""
        if not self._initialized:
            await self.db.initialize()
            
            # Migra dados do JSON se existir
            json_file = 'data.json'
            if os.path.exists(json_file):
                await self.db.migrate_from_json(json_file)
                # Renomeia o arquivo para backup
                backup_name = f'data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                os.rename(json_file, f'backups/{backup_name}')
                print(f"📦 Dados JSON migrados e backup salvo como {backup_name}")
            
            self._initialized = True
    
    async def close(self):
        """Fecha as conexões do banco"""
        await self.db.close()
    
    # Métodos de usuário
    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Busca dados de um usuário"""
        user = await self.db.get_user(user_id)
        if not user:
            return self._create_default_user_data()
        
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'total_sessions': user['total_sessions'],
            'total_time': user['total_time'],
            'is_checked_in': user['is_checked_in'],
            'last_checkin': user['last_checkin'].isoformat() if user['last_checkin'] else None,
            'last_checkout': user['last_checkout'].isoformat() if user['last_checkout'] else None,
            'current_session_start': user['current_session_start'].isoformat() if user['current_session_start'] else None,
            'settings': user['settings'] or {},
            'joined_at': user['joined_at'].isoformat() if user['joined_at'] else None
        }
    
    async def update_user_data(self, user_id: int, username: str, display_name: str, data: Dict[str, Any]):
        """Atualiza dados de um usuário"""
        await self.db.create_or_update_user(user_id, username, display_name)
        
        # Atualiza campos específicos se fornecidos
        if data:
            async with self.db.pool.acquire() as conn:
                update_fields = []
                values = []
                param_count = 1
                
                for key, value in data.items():
                    if key in ['total_sessions', 'total_time', 'is_checked_in', 'settings']:
                        update_fields.append(f"{key} = ${param_count + 1}")
                        values.append(value)
                        param_count += 1
                
                if update_fields:
                    query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = $1"
                    await conn.execute(query, user_id, *values)
    
    async def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """Busca todos os usuários"""
        users = await self.db.get_all_users()
        result = {}
        
        for user in users:
            result[str(user['user_id'])] = {
                'user_id': user['user_id'],
                'username': user['username'],
                'display_name': user['display_name'],
                'total_sessions': user['total_sessions'],
                'total_time': user['total_time'],
                'is_checked_in': user['is_checked_in'],
                'last_checkin': user['last_checkin'].isoformat() if user['last_checkin'] else None,
                'last_checkout': user['last_checkout'].isoformat() if user['last_checkout'] else None,
                'current_session_start': user['current_session_start'].isoformat() if user['current_session_start'] else None,
                'settings': user['settings'] or {},
                'joined_at': user['joined_at'].isoformat() if user['joined_at'] else None
            }
        
        return result
    
    # Métodos de sessão
    async def start_session(self, user_id: int, session_id: str, username: str, display_name: str) -> bool:
        """Inicia uma sessão"""
        await self.db.create_or_update_user(user_id, username, display_name)
        return await self.db.start_session(user_id, session_id)
    
    async def end_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Finaliza uma sessão"""
        return await self.db.end_session(user_id, session_id)
    
    async def get_user_sessions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca sessões de um usuário"""
        sessions = await self.db.get_user_sessions(user_id, limit)
        result = []
        
        for session in sessions:
            result.append({
                'session_id': session['session_id'],
                'user_id': session['user_id'],
                'start_time': session['start_time'].isoformat(),
                'end_time': session['end_time'].isoformat() if session['end_time'] else None,
                'duration': session['duration'],
                'type': session['session_type'],
                'notes': session['notes']
            })
        
        return result
    
    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Busca todas as sessões"""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT s.*, u.username, u.display_name 
                FROM sessions s 
                JOIN users u ON s.user_id = u.user_id 
                ORDER BY s.start_time DESC
            """)
            
            result = []
            for row in rows:
                result.append({
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'display_name': row['display_name'],
                    'start_time': row['start_time'].isoformat(),
                    'end_time': row['end_time'].isoformat() if row['end_time'] else None,
                    'duration': row['duration'],
                    'type': row['session_type'],
                    'notes': row['notes']
                })
            
            return result
    
    # Métodos de configuração
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Busca uma configuração"""
        value = await self.db.get_bot_setting(key)
        return value if value is not None else default
    
    async def set_setting(self, key: str, value: Any, description: str = None):
        """Define uma configuração"""
        await self.db.set_bot_setting(key, value, description)
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Busca todas as configurações"""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT key, value FROM bot_settings")
            return {row['key']: row['value'] for row in rows}
    
    # Métodos de estatísticas
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca o leaderboard"""
        users = await self.db.get_leaderboard(limit)
        result = []
        
        for i, user in enumerate(users, 1):
            result.append({
                'rank': i,
                'user_id': user['user_id'],
                'username': user['username'],
                'display_name': user['display_name'],
                'total_sessions': user['total_sessions'],
                'total_time': user['total_time']
            })
        
        return result
    
    async def get_session_stats(self, days: int = 30) -> Dict[str, Any]:
        """Busca estatísticas de sessões"""
        async with self.db.pool.acquire() as conn:
            # Estatísticas gerais
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    COALESCE(SUM(duration), 0) as total_time,
                    COALESCE(AVG(duration), 0) as avg_duration
                FROM sessions 
                WHERE start_time >= NOW() - INTERVAL '%s days'
            """ % days)
            
            # Sessões por dia
            daily_stats = await conn.fetch("""
                SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as sessions,
                    COUNT(DISTINCT user_id) as users,
                    COALESCE(SUM(duration), 0) as total_time
                FROM sessions 
                WHERE start_time >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(start_time)
                ORDER BY date DESC
            """ % days)
            
            return {
                'period_days': days,
                'total_sessions': stats['total_sessions'],
                'unique_users': stats['unique_users'],
                'total_time': stats['total_time'],
                'average_duration': int(stats['avg_duration']),
                'daily_stats': [
                    {
                        'date': row['date'].isoformat(),
                        'sessions': row['sessions'],
                        'users': row['users'],
                        'total_time': row['total_time']
                    }
                    for row in daily_stats
                ]
            }
    
    # Métodos de backup e manutenção
    async def create_backup(self) -> str:
        """Cria um backup dos dados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/postgres_backup_{timestamp}.json"
        
        # Busca todos os dados
        users = await self.get_all_users()
        sessions = await self.get_all_sessions()
        settings = await self.get_all_settings()
        
        backup_data = {
            'timestamp': timestamp,
            'users': users,
            'sessions': sessions,
            'settings': settings
        }
        
        os.makedirs('backups', exist_ok=True)
        
        import json
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return backup_file
    
    async def cleanup_old_sessions(self, days: int = 90):
        """Remove sessões antigas"""
        async with self.db.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM sessions 
                WHERE start_time < NOW() - INTERVAL '%s days'
            """ % days)
            
            return result
    
    def _create_default_user_data(self) -> Dict[str, Any]:
        """Cria dados padrão para um novo usuário"""
        return {
            'user_id': 0,
            'username': '',
            'display_name': '',
            'total_sessions': 0,
            'total_time': 0,
            'is_checked_in': False,
            'last_checkin': None,
            'last_checkout': None,
            'current_session_start': None,
            'settings': {},
            'joined_at': None
        }
    
    # Métodos para compatibilidade com o sistema antigo
    async def load_data(self):
        """Carrega dados (compatibilidade)"""
        await self.initialize()
    
    async def save_data(self):
        """Salva dados (compatibilidade - não faz nada no PostgreSQL)"""
        pass
    
    async def get_data(self) -> Dict[str, Any]:
        """Busca todos os dados (compatibilidade)"""
        users = await self.get_all_users()
        sessions = await self.get_all_sessions()
        settings = await self.get_all_settings()
        
        return {
            'users': users,
            'sessions': sessions,
            'settings': settings
        }