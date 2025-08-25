"""Configurações centrais do Hawk Bot."""

import os
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Settings:
    """Classe para gerenciar configurações do bot."""
    
    # Bot Configuration
    DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
    BOT_PREFIX: str = os.getenv('BOT_PREFIX', '!')
    
    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    POSTGRES_URL: Optional[str] = os.getenv('POSTGRES_URL')
    
    # API Keys
    PUBG_API_KEY: Optional[str] = os.getenv('PUBG_API_KEY')
    MEDAL_API_KEY: Optional[str] = os.getenv('MEDAL_API_KEY')
    
    # Web Dashboard
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '10000'))
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Storage Configuration
    STORAGE_TYPE: str = os.getenv('STORAGE_TYPE', 'json')  # 'json' or 'postgres'
    DATA_DIR: str = os.getenv('DATA_DIR', 'data')
    
    # Feature Flags
    ENABLE_MUSIC: bool = os.getenv('ENABLE_MUSIC', 'True').lower() == 'true'
    ENABLE_PUBG: bool = os.getenv('ENABLE_PUBG', 'True').lower() == 'true'
    ENABLE_TOURNAMENTS: bool = os.getenv('ENABLE_TOURNAMENTS', 'True').lower() == 'true'
    ENABLE_ACHIEVEMENTS: bool = os.getenv('ENABLE_ACHIEVEMENTS', 'True').lower() == 'true'
    ENABLE_NOTIFICATIONS: bool = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
    ENABLE_MODERATION: bool = os.getenv('ENABLE_MODERATION', 'True').lower() == 'true'
    ENABLE_MINIGAMES: bool = os.getenv('ENABLE_MINIGAMES', 'True').lower() == 'true'
    ENABLE_CHECKIN: bool = os.getenv('ENABLE_CHECKIN', 'True').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se as configurações essenciais estão presentes."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN é obrigatório")
        return True
    
    @classmethod
    def get_database_url(cls) -> Optional[str]:
        """Retorna a URL do banco de dados preferencial."""
        return cls.POSTGRES_URL or cls.DATABASE_URL
    
    @classmethod
    def is_postgres_enabled(cls) -> bool:
        """Verifica se o PostgreSQL está habilitado e configurado."""
        return cls.STORAGE_TYPE == 'postgres' and cls.get_database_url() is not None

# Instância global das configurações
settings = Settings()