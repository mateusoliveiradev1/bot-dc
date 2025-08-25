# -*- coding: utf-8 -*-
"""
Sistema de Configuração - Hawk Bot
Gerenciamento centralizado de configurações com validação e tipagem

Este módulo mantém compatibilidade com o código existente enquanto
utiliza o novo sistema de configuração tipado internamente.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from pydantic import BaseSettings, Field, validator, SecretStr
from pydantic.env_settings import SettingsSourceCallable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger('HawkBot.Config')

# Configurações padrão (fallback)
DEFAULT_CONFIG = {
    # Discord
    'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN', ''),
    'COMMAND_PREFIX': os.getenv('COMMAND_PREFIX', '!'),
    'OWNER_IDS': [],
    
    # Logging
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'LOG_DIR': os.getenv('LOG_DIR', 'logs'),
    'LOG_MAX_SIZE': int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
    'LOG_BACKUP_COUNT': int(os.getenv('LOG_BACKUP_COUNT', '5')),
    
    # Cache
    'CACHE_ENABLED': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
    'CACHE_TTL': int(os.getenv('CACHE_TTL', '300')),  # 5 minutos
    'CACHE_MAX_SIZE': int(os.getenv('CACHE_MAX_SIZE', '1000')),
    
    # Database
    'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///data/hawkbot.db'),
    'DB_POOL_SIZE': int(os.getenv('DB_POOL_SIZE', '5')),
    'DB_MAX_OVERFLOW': int(os.getenv('DB_MAX_OVERFLOW', '10')),
    
    # PUBG API
    'PUBG_API_KEY': os.getenv('API_PUBG_API_KEY', ''),
    'PUBG_PLATFORM': os.getenv('PUBG_PLATFORM', 'steam'),
    'PUBG_REGION': os.getenv('PUBG_REGION', 'pc-na'),
    
    # Music
    'MUSIC_ENABLED': os.getenv('MUSIC_ENABLED', 'true').lower() == 'true',
    'MUSIC_MAX_QUEUE': int(os.getenv('MUSIC_MAX_QUEUE', '50')),
    'MUSIC_DEFAULT_VOLUME': float(os.getenv('MUSIC_DEFAULT_VOLUME', '0.5')),
    
    # Performance
    'MAX_CONCURRENT_TASKS': int(os.getenv('MAX_CONCURRENT_TASKS', '100')),
    'TASK_TIMEOUT': int(os.getenv('TASK_TIMEOUT', '300')),
    'MEMORY_LIMIT_MB': int(os.getenv('MEMORY_LIMIT_MB', '512')),
    
    # Security
    'RATE_LIMIT_ENABLED': os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
    'MAX_COMMANDS_PER_MINUTE': int(os.getenv('MAX_COMMANDS_PER_MINUTE', '30')),
    'BLACKLISTED_USERS': [],
    
    # Debug
    'DEBUG_MODE': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
    'PROFILING_ENABLED': os.getenv('PROFILING_ENABLED', 'false').lower() == 'true',
}

class LogLevel(str, Enum):
    """Níveis de log disponíveis"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StorageType(str, Enum):
    """Tipos de storage disponíveis"""
    JSON = "json"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"

class CacheConfig(BaseSettings):
    """Configurações do sistema de cache"""
    
    # Cache Redis (opcional)
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    redis_password: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")
    
    # Cache em memória
    memory_cache_size: int = Field(1000, env="MEMORY_CACHE_SIZE")
    default_ttl: int = Field(3600, env="DEFAULT_CACHE_TTL")  # 1 hora
    
    # TTLs específicos por tipo
    pubg_api_ttl: int = Field(300, env="PUBG_API_CACHE_TTL")  # 5 minutos
    ranking_ttl: int = Field(600, env="RANKING_CACHE_TTL")    # 10 minutos
    user_stats_ttl: int = Field(1800, env="USER_STATS_CACHE_TTL")  # 30 minutos
    
    # Configurações de limpeza
    cleanup_interval: int = Field(300, env="CACHE_CLEANUP_INTERVAL")  # 5 minutos
    max_memory_usage: int = Field(100, env="MAX_CACHE_MEMORY_MB")  # 100MB
    
    class Config:
        env_prefix = "CACHE_"

class DatabaseConfig(BaseSettings):
    """Configurações do banco de dados"""
    
    # Tipo de storage
    storage_type: StorageType = Field(StorageType.JSON, env="STORAGE_TYPE")
    
    # PostgreSQL
    postgres_host: Optional[str] = Field(None, env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_user: Optional[str] = Field(None, env="POSTGRES_USER")
    postgres_password: Optional[SecretStr] = Field(None, env="POSTGRES_PASSWORD")
    postgres_database: Optional[str] = Field(None, env="POSTGRES_DATABASE")
    
    # Pool de conexões
    min_connections: int = Field(5, env="DB_MIN_CONNECTIONS")
    max_connections: int = Field(20, env="DB_MAX_CONNECTIONS")
    connection_timeout: int = Field(30, env="DB_CONNECTION_TIMEOUT")
    
    # JSON Storage
    json_data_path: Path = Field(Path("data"), env="JSON_DATA_PATH")
    backup_enabled: bool = Field(True, env="BACKUP_ENABLED")
    backup_interval: int = Field(3600, env="BACKUP_INTERVAL")  # 1 hora
    max_backups: int = Field(10, env="MAX_BACKUPS")
    
    @validator('postgres_password', pre=True)
    def validate_postgres_config(cls, v, values):
        """Valida configuração do PostgreSQL"""
        storage_type = values.get('storage_type')
        if storage_type == StorageType.POSTGRESQL:
            required_fields = ['postgres_host', 'postgres_user', 'postgres_database']
            for field in required_fields:
                if not values.get(field):
                    raise ValueError(f"{field} é obrigatório quando usando PostgreSQL")
        return v
    
    @property
    def postgres_url(self) -> Optional[str]:
        """Constrói a URL do PostgreSQL"""
        if self.storage_type != StorageType.POSTGRESQL:
            return None
        
        password = self.postgres_password.get_secret_value() if self.postgres_password else ""
        return f"postgresql://{self.postgres_user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
    
    class Config:
        env_prefix = "DB_"

class APIConfig(BaseSettings):
    """Configurações das APIs externas"""
    
    # PUBG API
    pubg_api_key: Optional[SecretStr] = Field(None, env="API_PUBG_API_KEY")
    pubg_api_base_url: str = Field("https://api.pubg.com", env="PUBG_API_BASE_URL")
    pubg_rate_limit: int = Field(8, env="PUBG_RATE_LIMIT")  # requests per minute
    
    # Medal.tv API
    medal_api_key: Optional[SecretStr] = Field(None, env="MEDAL_API_KEY")
    medal_api_base_url: str = Field("https://developers.medal.tv", env="MEDAL_API_BASE_URL")
    
    # Timeouts e retries
    api_timeout: int = Field(30, env="API_TIMEOUT")
    max_retries: int = Field(3, env="API_MAX_RETRIES")
    retry_delay: float = Field(1.0, env="API_RETRY_DELAY")
    
    @validator('pubg_api_key')
    def validate_pubg_api_key(cls, v):
        """Valida a chave da API do PUBG"""
        if v and len(v.get_secret_value()) < 10:
            raise ValueError("PUBG API key deve ter pelo menos 10 caracteres")
        return v
    
    class Config:
        env_prefix = "API_"

class DiscordConfig(BaseSettings):
    """Configurações do Discord"""
    
    # Bot token
    bot_token: SecretStr = Field(..., env="DISCORD_BOT_TOKEN")
    
    # Configurações do bot
    command_prefix: str = Field("!", env="DISCORD_PREFIX")
    case_insensitive: bool = Field(True, env="DISCORD_CASE_INSENSITIVE")
    
    # Intents
    enable_message_content: bool = Field(True, env="DISCORD_MESSAGE_CONTENT")
    enable_guild_members: bool = Field(True, env="DISCORD_GUILD_MEMBERS")
    enable_voice_states: bool = Field(True, env="DISCORD_VOICE_STATES")
    
    # Limites e timeouts
    max_message_length: int = Field(2000, env="DISCORD_MAX_MESSAGE_LENGTH")
    command_timeout: int = Field(30, env="DISCORD_COMMAND_TIMEOUT")
    
    # Canais especiais
    log_channel_id: Optional[int] = Field(None, env="DISCORD_LOG_CHANNEL")
    error_channel_id: Optional[int] = Field(None, env="DISCORD_ERROR_CHANNEL")
    
    @validator('bot_token')
    def validate_bot_token(cls, v):
        """Valida o token do bot"""
        token = v.get_secret_value()
        if not token or len(token) < 50:
            raise ValueError("Discord bot token inválido")
        return v
    
    class Config:
        env_prefix = "DISCORD_"

class LoggingConfig(BaseSettings):
    """Configurações de logging"""
    
    # Nível de log
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    
    # Arquivos de log
    log_to_file: bool = Field(True, env="LOG_TO_FILE")
    log_file_path: Path = Field(Path("logs/hawk_bot.log"), env="LOG_FILE_PATH")
    max_log_size: int = Field(10, env="MAX_LOG_SIZE_MB")  # MB
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # Formatação
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    date_format: str = Field("%Y-%m-%d %H:%M:%S", env="LOG_DATE_FORMAT")
    
    # Sanitização
    sanitize_logs: bool = Field(True, env="SANITIZE_LOGS")
    sensitive_fields: List[str] = Field(
        ["token", "password", "api_key", "secret", "auth"],
        env="SENSITIVE_LOG_FIELDS"
    )
    
    # Logging estruturado
    structured_logging: bool = Field(True, env="STRUCTURED_LOGGING")
    include_trace_id: bool = Field(True, env="INCLUDE_TRACE_ID")
    
    class Config:
        env_prefix = "LOG_"

class PerformanceConfig(BaseSettings):
    """Configurações de performance"""
    
    # Limites de recursos
    max_memory_usage: int = Field(512, env="MAX_MEMORY_MB")  # MB
    max_cpu_usage: float = Field(80.0, env="MAX_CPU_PERCENT")
    
    # Timeouts
    startup_timeout: int = Field(60, env="STARTUP_TIMEOUT")
    shutdown_timeout: int = Field(30, env="SHUTDOWN_TIMEOUT")
    
    # Monitoramento
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(8080, env="METRICS_PORT")
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    
    # Otimizações
    enable_lazy_loading: bool = Field(True, env="ENABLE_LAZY_LOADING")
    preload_critical_data: bool = Field(True, env="PRELOAD_CRITICAL_DATA")
    
    class Config:
        env_prefix = "PERF_"

class HawkBotConfig(BaseSettings):
    """Configuração principal do Hawk Bot"""
    
    # Informações básicas
    app_name: str = Field("Hawk Bot", env="APP_NAME")
    version: str = Field("2.0.0", env="APP_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Configurações dos subsistemas
    discord: DiscordConfig = DiscordConfig()
    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()
    api: APIConfig = APIConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    # Configurações específicas do bot
    enable_music_system: bool = Field(True, env="ENABLE_MUSIC")
    enable_pubg_integration: bool = Field(True, env="ENABLE_PUBG")
    enable_ranking_system: bool = Field(True, env="ENABLE_RANKING")
    enable_achievements: bool = Field(True, env="ENABLE_ACHIEVEMENTS")
    enable_seasons: bool = Field(True, env="ENABLE_SEASONS")
    enable_minigames: bool = Field(True, env="ENABLE_MINIGAMES")
    
    # Paths importantes
    data_directory: Path = Field(Path("data"), env="DATA_DIRECTORY")
    logs_directory: Path = Field(Path("logs"), env="LOGS_DIRECTORY")
    temp_directory: Path = Field(Path("temp"), env="TEMP_DIRECTORY")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Valida o ambiente"""
        valid_envs = ['development', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"Environment deve ser um de: {valid_envs}")
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Garante que os diretórios necessários existam"""
        directories = [
            self.data_directory,
            self.logs_directory,
            self.temp_directory,
            self.database.json_data_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.environment == "development"
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Retorna as feature flags ativas"""
        return {
            'music_system': self.enable_music_system,
            'pubg_integration': self.enable_pubg_integration,
            'ranking_system': self.enable_ranking_system,
            'achievements': self.enable_achievements,
            'seasons': self.enable_seasons,
            'minigames': self.enable_minigames
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            """Customiza as fontes de configuração"""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

# Instância global da configuração
_config: Optional[HawkBotConfig] = None

def get_config() -> HawkBotConfig:
    """Obtém a instância global da configuração"""
    global _config
    if _config is None:
        _config = HawkBotConfig()
        logger.info(f"Configuração carregada: {_config.app_name} v{_config.version} ({_config.environment})")
    return _config

def reload_config() -> HawkBotConfig:
    """Recarrega a configuração"""
    global _config
    _config = None
    return get_config()

# Função para validar configuração
def validate_config() -> tuple[bool, List[str]]:
    """Valida a configuração atual"""
    errors = []
    
    try:
        config = get_config()
        
        # Validações específicas
        if config.enable_pubg_integration and not config.api.pubg_api_key:
            errors.append("PUBG integration habilitada mas PUBG_API_KEY não configurada")
        
        if config.database.storage_type == StorageType.POSTGRESQL:
            if not config.database.postgres_host:
                errors.append("PostgreSQL selecionado mas POSTGRES_HOST não configurado")
        
        # Verificar se diretórios são acessíveis
        for directory in [config.data_directory, config.logs_directory]:
            if not directory.exists() or not os.access(directory, os.W_OK):
                errors.append(f"Diretório não acessível: {directory}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Erro na validação da configuração: {str(e)}"]

# Classe de compatibilidade com o código existente
class Config:
    """Classe de configuração compatível com o código existente"""
    
    def __init__(self):
        self._typed_config = get_config()
    
    # Propriedades para compatibilidade com o código existente
    @property
    def bot_name(self) -> str:
        return self._typed_config.app_name
    
    @property
    def version(self) -> str:
        return self._typed_config.version
    
    @property
    def debug_mode(self) -> bool:
        return self._typed_config.debug
    
    @property
    def discord_token(self) -> str:
        return self._typed_config.discord.bot_token.get_secret_value()
    
    @property
    def command_prefix(self) -> str:
        return self._typed_config.discord.command_prefix
    
    @property
    def owner_ids(self) -> List[int]:
        return []
    
    @property
    def log_level(self) -> str:
        return self._typed_config.logging.log_level.value
    
    @property
    def log_dir(self) -> Path:
        return self._typed_config.logging.log_file_path.parent
    
    @property
    def database_url(self) -> str:
        if self._typed_config.database.storage_type == StorageType.POSTGRESQL:
            return self._typed_config.database.postgres_url or "sqlite:///data/hawkbot.db"
        return "sqlite:///data/hawkbot.db"
    
    def get_database_url(self) -> str:
        """Retorna a URL do banco de dados"""
        return self.database_url
    
    def get_discord_token(self) -> str:
        """Retorna o token do Discord"""
        return self.discord_token
    
    def get_pubg_api_key(self) -> Optional[str]:
        """Retorna a chave da API do PUBG"""
        if self._typed_config.api.pubg_api_key:
            return self._typed_config.api.pubg_api_key.get_secret_value()
        return None
    
    def is_debug_mode(self) -> bool:
        """Verifica se está em modo debug"""
        return self.debug_mode
    
    def get_log_config(self) -> Dict[str, Any]:
        """Retorna configurações de logging"""
        logging_config = self._typed_config.logging
        return {
            'level': logging_config.log_level.value,
            'dir': str(logging_config.log_file_path.parent),
            'max_size': logging_config.max_log_size * 1024 * 1024,
            'backup_count': logging_config.backup_count,
            'structured': logging_config.structured_logging
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Retorna configurações de cache"""
        cache_config = self._typed_config.cache
        return {
            'enabled': True,
            'ttl': cache_config.default_ttl,
            'max_size': cache_config.memory_cache_size,
            'strategy': 'LRU'
        }
    
    def validate_config(self) -> List[str]:
        """Valida a configuração e retorna lista de erros"""
        is_valid, errors = validate_config()
        return errors
    
    # Propriedades adicionais para compatibilidade
    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level
    
    @property
    def LOG_DIR(self) -> str:
        return str(self.log_dir)
    
    @property
    def LOG_MAX_SIZE(self) -> int:
        return self._typed_config.logging.max_log_size * 1024 * 1024
    
    @property
    def LOG_BACKUP_COUNT(self) -> int:
        return self._typed_config.logging.backup_count
    
    @property
    def DISCORD_TOKEN(self) -> str:
        return self.discord_token
    
    @property
    def COMMAND_PREFIX(self) -> str:
        return self.command_prefix
    
    @property
    def CACHE_ENABLED(self) -> bool:
        return True
    
    @property
    def CACHE_TTL(self) -> int:
        return self._typed_config.cache.default_ttl
    
    @property
    def CACHE_MAX_SIZE(self) -> int:
        return self._typed_config.cache.memory_cache_size
    
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url
    
    @property
    def PUBG_API_KEY(self) -> str:
        return self.get_pubg_api_key() or ''
    
    @property
    def MUSIC_ENABLED(self) -> bool:
        return self._typed_config.enable_music_system
    
    @property
    def DEBUG_MODE(self) -> bool:
        return self.debug_mode

# Instância global para compatibilidade
_legacy_config: Optional[Config] = None

def get_legacy_config() -> Config:
    """Obtém a instância da configuração legada para compatibilidade"""
    global _legacy_config
    if _legacy_config is None:
        _legacy_config = Config()
    return _legacy_config