# -*- coding: utf-8 -*-
"""
Sistema de Configuração Tipado - Hawk Bot
Configuração com validação automática usando Pydantic
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.env_settings import BaseSettings


class LogLevel(str, Enum):
    """Níveis de log disponíveis"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheStrategy(str, Enum):
    """Estratégias de cache disponíveis"""
    LRU = "LRU"
    LFU = "LFU"
    TTL = "TTL"
    ADAPTIVE = "ADAPTIVE"
    PREDICTIVE = "PREDICTIVE"


class DatabaseType(str, Enum):
    """Tipos de banco de dados suportados"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class LoggingConfig(BaseModel):
    """Configurações de logging"""
    level: LogLevel = LogLevel.INFO
    structured: bool = True
    sanitize_sensitive: bool = True
    log_to_file: bool = True
    log_dir: Path = Field(default_factory=lambda: Path("logs"))
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=20)
    console_output: bool = True
    json_format: bool = True
    
    @validator('log_dir')
    def validate_log_dir(cls, v):
        """Valida e cria o diretório de logs"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v


class CacheConfig(BaseModel):
    """Configurações de cache"""
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.ADAPTIVE
    max_size: int = Field(default=1000, ge=10, le=100000)
    default_ttl_seconds: int = Field(default=300, ge=1, le=86400)
    max_memory_mb: int = Field(default=100, ge=10, le=1000)
    cleanup_interval_seconds: int = Field(default=60, ge=10, le=3600)
    compression_enabled: bool = True
    predictive_learning: bool = True


class DatabaseConfig(BaseModel):
    """Configurações de banco de dados"""
    type: DatabaseType = DatabaseType.SQLITE
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = "hawkbot"
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=5, le=300)
    echo_sql: bool = False
    
    @validator('password')
    def validate_password(cls, v, values):
        """Valida senha para bancos não-SQLite"""
        db_type = values.get('type')
        if db_type != DatabaseType.SQLITE and not v:
            raise ValueError(f"Password is required for {db_type} database")
        return v
    
    @property
    def connection_string(self) -> str:
        """Gera string de conexão baseada no tipo de banco"""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///data/{self.database}.db"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class DiscordConfig(BaseModel):
    """Configurações do Discord"""
    token: str = Field(..., min_length=50)
    command_prefix: str = Field(default="!", min_length=1, max_length=5)
    owner_ids: List[int] = Field(default_factory=list)
    guild_ids: List[int] = Field(default_factory=list)
    max_messages: int = Field(default=1000, ge=100, le=10000)
    case_insensitive: bool = True
    strip_after_prefix: bool = True
    intents_members: bool = True
    intents_presences: bool = False
    intents_message_content: bool = True
    
    @validator('token')
    def validate_token(cls, v):
        """Valida formato básico do token do Discord"""
        if not v or v == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Discord token must be provided")
        # Validação básica do formato do token
        if not (v.startswith(('Bot ', 'Bearer ')) or len(v) > 50):
            raise ValueError("Invalid Discord token format")
        return v


class PubgConfig(BaseModel):
    """Configurações da API do PUBG"""
    api_key: Optional[str] = None
    platform: str = Field(default="steam", regex=r"^(steam|xbox|psn|stadia)$")
    region: str = Field(default="pc-na", regex=r"^pc-(na|eu|as|sa|sea|oc|krjp|kakao|console)$")
    cache_duration_minutes: int = Field(default=30, ge=5, le=1440)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Valida chave da API do PUBG"""
        if v and len(v) < 20:
            raise ValueError("PUBG API key appears to be invalid")
        return v


class MusicConfig(BaseModel):
    """Configurações do sistema de música"""
    enabled: bool = True
    max_queue_size: int = Field(default=50, ge=1, le=500)
    max_song_duration_minutes: int = Field(default=30, ge=1, le=180)
    default_volume: float = Field(default=0.5, ge=0.0, le=1.0)
    auto_disconnect_minutes: int = Field(default=5, ge=1, le=60)
    search_results_limit: int = Field(default=10, ge=1, le=25)
    allow_playlists: bool = True
    allow_livestreams: bool = False
    ytdl_options: Dict[str, Any] = Field(default_factory=lambda: {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    })


class SecurityConfig(BaseModel):
    """Configurações de segurança"""
    rate_limit_enabled: bool = True
    max_commands_per_minute: int = Field(default=30, ge=1, le=1000)
    max_commands_per_hour: int = Field(default=500, ge=10, le=10000)
    blacklisted_users: List[int] = Field(default_factory=list)
    blacklisted_guilds: List[int] = Field(default_factory=list)
    admin_only_commands: List[str] = Field(default_factory=list)
    log_security_events: bool = True
    auto_ban_threshold: int = Field(default=10, ge=1, le=100)
    

class PerformanceConfig(BaseModel):
    """Configurações de performance"""
    max_concurrent_tasks: int = Field(default=100, ge=10, le=1000)
    task_timeout_seconds: int = Field(default=300, ge=30, le=3600)
    memory_limit_mb: int = Field(default=512, ge=128, le=4096)
    cpu_usage_threshold: float = Field(default=80.0, ge=10.0, le=95.0)
    enable_profiling: bool = False
    metrics_collection: bool = True
    health_check_interval: int = Field(default=60, ge=10, le=600)


class HawkBotConfig(BaseSettings):
    """Configuração principal do Hawk Bot"""
    
    # Configurações básicas
    bot_name: str = "Hawk Bot"
    version: str = "2.0.0"
    description: str = "Bot Discord para comunidade de esports"
    debug_mode: bool = False
    
    # Configurações por módulo
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    pubg: PubgConfig = Field(default_factory=PubgConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Configurações de ambiente
    environment: str = Field(default="development", regex=r"^(development|staging|production)$")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
        
    @root_validator
    def validate_config(cls, values):
        """Validações globais da configuração"""
        environment = values.get('environment', 'development')
        
        # Em produção, debug deve estar desabilitado
        if environment == 'production' and values.get('debug_mode', False):
            raise ValueError("Debug mode must be disabled in production")
        
        # Validar token do Discord
        discord_config = values.get('discord')
        if discord_config and not discord_config.token:
            raise ValueError("Discord token is required")
        
        return values
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> 'HawkBotConfig':
        """Carrega configuração de um arquivo JSON"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: Union[str, Path], exclude_sensitive: bool = True):
        """Salva configuração em um arquivo JSON"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Preparar dados para serialização
        config_dict = self.dict()
        
        if exclude_sensitive:
            # Remover dados sensíveis
            if 'discord' in config_dict and 'token' in config_dict['discord']:
                config_dict['discord']['token'] = "[REDACTED]"
            if 'database' in config_dict and 'password' in config_dict['database']:
                config_dict['database']['password'] = "[REDACTED]"
            if 'pubg' in config_dict and 'api_key' in config_dict['pubg']:
                config_dict['pubg']['api_key'] = "[REDACTED]"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Retorna informações do ambiente"""
        return {
            'bot_name': self.bot_name,
            'version': self.version,
            'environment': self.environment,
            'debug_mode': self.debug_mode,
            'python_version': os.sys.version,
            'config_loaded_at': str(Path.cwd())
        }
    
    def validate_runtime_requirements(self) -> List[str]:
        """Valida requisitos em tempo de execução"""
        issues = []
        
        # Verificar token do Discord
        if not self.discord.token or self.discord.token == "YOUR_BOT_TOKEN_HERE":
            issues.append("Discord token not configured")
        
        # Verificar diretórios necessários
        try:
            self.logging.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create log directory: {e}")
        
        # Verificar configurações de produção
        if self.environment == 'production':
            if self.debug_mode:
                issues.append("Debug mode should be disabled in production")
            if self.logging.level in [LogLevel.TRACE, LogLevel.DEBUG]:
                issues.append("Log level should not be TRACE/DEBUG in production")
        
        return issues


# Instância global da configuração
_config_instance: Optional[HawkBotConfig] = None


def get_config() -> HawkBotConfig:
    """Obtém a instância global da configuração"""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def load_config(config_path: Optional[Union[str, Path]] = None) -> HawkBotConfig:
    """Carrega configuração de arquivo ou variáveis de ambiente"""
    if config_path:
        return HawkBotConfig.load_from_file(config_path)
    
    # Tentar carregar de arquivo padrão
    default_paths = [
        Path("config.json"),
        Path("config/config.json"),
        Path("src/config/config.json")
    ]
    
    for path in default_paths:
        if path.exists():
            return HawkBotConfig.load_from_file(path)
    
    # Carregar de variáveis de ambiente
    return HawkBotConfig()


def reload_config(config_path: Optional[Union[str, Path]] = None) -> HawkBotConfig:
    """Recarrega a configuração"""
    global _config_instance
    _config_instance = load_config(config_path)
    return _config_instance


def create_default_config(config_path: Union[str, Path]) -> HawkBotConfig:
    """Cria um arquivo de configuração padrão"""
    config = HawkBotConfig()
    config.save_to_file(config_path, exclude_sensitive=False)
    return config


# Funções de conveniência para acessar configurações específicas
def get_discord_config() -> DiscordConfig:
    """Obtém configurações do Discord"""
    return get_config().discord


def get_logging_config() -> LoggingConfig:
    """Obtém configurações de logging"""
    return get_config().logging


def get_cache_config() -> CacheConfig:
    """Obtém configurações de cache"""
    return get_config().cache


def get_database_config() -> DatabaseConfig:
    """Obtém configurações de banco de dados"""
    return get_config().database


def get_pubg_config() -> PubgConfig:
    """Obtém configurações do PUBG"""
    return get_config().pubg


def get_music_config() -> MusicConfig:
    """Obtém configurações de música"""
    return get_config().music


def get_security_config() -> SecurityConfig:
    """Obtém configurações de segurança"""
    return get_config().security


def get_performance_config() -> PerformanceConfig:
    """Obtém configurações de performance"""
    return get_config().performance