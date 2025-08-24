import os
import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Configuração do banco de dados"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Cria configuração a partir das variáveis de ambiente"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'hawk_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
    
    @property
    def url(self) -> str:
        """Retorna a URL de conexão do banco"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class DatabaseManager:
    """Gerenciador de banco de dados PostgreSQL"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Inicializa o pool de conexões"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=1,
                max_size=10
            )
            await self.create_tables()
            print("✅ Banco de dados PostgreSQL conectado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar com o banco de dados: {e}")
            raise
    
    async def close(self):
        """Fecha o pool de conexões"""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Cria as tabelas necessárias"""
        async with self.pool.acquire() as conn:
            # Tabela de usuários
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    display_name VARCHAR(255),
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 0,
                    total_time INTEGER DEFAULT 0,
                    last_checkin TIMESTAMP,
                    last_checkout TIMESTAMP,
                    current_session_start TIMESTAMP,
                    is_checked_in BOOLEAN DEFAULT FALSE,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de sessões
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    session_id VARCHAR(255) UNIQUE,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    session_type VARCHAR(50) DEFAULT 'gaming',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de configurações do bot
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key VARCHAR(255) PRIMARY KEY,
                    value JSONB,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de lembretes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    reminder_type VARCHAR(50),
                    message TEXT,
                    scheduled_time TIMESTAMP,
                    is_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_time ON reminders(scheduled_time)")
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Busca um usuário pelo ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None
    
    async def create_or_update_user(self, user_id: int, username: str, display_name: str) -> Dict[str, Any]:
        """Cria ou atualiza um usuário"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, display_name, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name,
                    updated_at = CURRENT_TIMESTAMP
            """, user_id, username, display_name)
            
            return await self.get_user(user_id)
    
    async def start_session(self, user_id: int, session_id: str) -> bool:
        """Inicia uma sessão de check-in"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Atualiza o usuário
                await conn.execute("""
                    UPDATE users SET
                        is_checked_in = TRUE,
                        current_session_start = CURRENT_TIMESTAMP,
                        last_checkin = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                """, user_id)
                
                # Cria a sessão
                await conn.execute("""
                    INSERT INTO sessions (user_id, session_id, start_time, session_type)
                    VALUES ($1, $2, CURRENT_TIMESTAMP, 'gaming')
                """, user_id, session_id)
                
                return True
    
    async def end_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Finaliza uma sessão de check-in"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Busca a sessão ativa
                session = await conn.fetchrow("""
                    SELECT * FROM sessions 
                    WHERE user_id = $1 AND session_id = $2 AND end_time IS NULL
                """, user_id, session_id)
                
                if not session:
                    return None
                
                # Calcula a duração
                start_time = session['start_time']
                duration = int((datetime.now() - start_time).total_seconds())
                
                # Atualiza a sessão
                await conn.execute("""
                    UPDATE sessions SET
                        end_time = CURRENT_TIMESTAMP,
                        duration = $3
                    WHERE user_id = $1 AND session_id = $2
                """, user_id, session_id, duration)
                
                # Atualiza o usuário
                await conn.execute("""
                    UPDATE users SET
                        is_checked_in = FALSE,
                        current_session_start = NULL,
                        last_checkout = CURRENT_TIMESTAMP,
                        total_sessions = total_sessions + 1,
                        total_time = total_time + $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                """, user_id, duration)
                
                return {
                    'session_id': session_id,
                    'start_time': start_time,
                    'end_time': datetime.now(),
                    'duration': duration
                }
    
    async def get_user_sessions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca as sessões de um usuário"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM sessions 
                WHERE user_id = $1 
                ORDER BY start_time DESC 
                LIMIT $2
            """, user_id, limit)
            
            return [dict(row) for row in rows]
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Busca todos os usuários"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY total_time DESC")
            return [dict(row) for row in rows]
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca o leaderboard de usuários"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, display_name, total_sessions, total_time
                FROM users 
                WHERE total_sessions > 0
                ORDER BY total_time DESC 
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def get_bot_setting(self, key: str) -> Any:
        """Busca uma configuração do bot"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM bot_settings WHERE key = $1", key)
            return row['value'] if row else None
    
    async def set_bot_setting(self, key: str, value: Any, description: str = None):
        """Define uma configuração do bot"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bot_settings (key, value, description, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, bot_settings.description),
                    updated_at = CURRENT_TIMESTAMP
            """, key, json.dumps(value), description)
    
    async def migrate_from_json(self, json_file_path: str):
        """Migra dados do arquivo JSON para o PostgreSQL"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("🔄 Iniciando migração dos dados...")
            
            # Migra usuários
            if 'users' in data:
                for user_id_str, user_data in data['users'].items():
                    user_id = int(user_id_str)
                    await self.create_or_update_user(
                        user_id=user_id,
                        username=user_data.get('username', ''),
                        display_name=user_data.get('display_name', '')
                    )
                    
                    # Atualiza estatísticas
                    async with self.pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE users SET
                                total_sessions = $2,
                                total_time = $3,
                                is_checked_in = $4,
                                last_checkin = $5,
                                last_checkout = $6
                            WHERE user_id = $1
                        """, 
                        user_id,
                        user_data.get('total_sessions', 0),
                        user_data.get('total_time', 0),
                        user_data.get('is_checked_in', False),
                        datetime.fromisoformat(user_data['last_checkin']) if user_data.get('last_checkin') else None,
                        datetime.fromisoformat(user_data['last_checkout']) if user_data.get('last_checkout') else None
                        )
            
            # Migra sessões
            if 'sessions' in data:
                for session_data in data['sessions']:
                    async with self.pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO sessions (user_id, session_id, start_time, end_time, duration, session_type)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (session_id) DO NOTHING
                        """,
                        session_data['user_id'],
                        session_data['session_id'],
                        datetime.fromisoformat(session_data['start_time']),
                        datetime.fromisoformat(session_data['end_time']) if session_data.get('end_time') else None,
                        session_data.get('duration', 0),
                        session_data.get('type', 'gaming')
                        )
            
            print("✅ Migração concluída com sucesso!")
            
        except FileNotFoundError:
            print("⚠️ Arquivo JSON não encontrado, iniciando com banco vazio.")
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            raise