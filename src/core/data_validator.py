"""Sistema de validação de dados com schemas para o Hawk Bot.

Este módulo fornece:
- Validação de dados usando Pydantic
- Schemas para diferentes tipos de dados
- Validação de comandos e parâmetros
- Sanitização automática de dados
- Validação de configurações
- Sistema de validação customizada
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Type, Callable, Tuple
from datetime import datetime, date
from enum import Enum
from pathlib import Path
import logging

try:
    from pydantic import BaseModel, Field, validator, root_validator, ValidationError
    from pydantic.types import EmailStr, HttpUrl, SecretStr
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda *args, **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f
    root_validator = lambda *args, **kwargs: lambda f: f
    ValidationError = Exception
    EmailStr = str
    HttpUrl = str
    SecretStr = str

try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None

class ValidationLevel(Enum):
    """Níveis de validação"""
    STRICT = "strict"      # Validação rigorosa
    NORMAL = "normal"      # Validação padrão
    LENIENT = "lenient"    # Validação permissiva
    DISABLED = "disabled"  # Validação desabilitada

class DataType(Enum):
    """Tipos de dados suportados"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    EMAIL = "email"
    URL = "url"
    DISCORD_ID = "discord_id"
    DISCORD_TOKEN = "discord_token"
    JSON = "json"
    DATETIME = "datetime"
    DATE = "date"
    LIST = "list"
    DICT = "dict"

if PYDANTIC_AVAILABLE:
    class BaseValidationSchema(BaseModel):
        """Schema base para validação"""
        
        class Config:
            validate_assignment = True
            extra = "forbid"
            str_strip_whitespace = True
            anystr_lower = False
            use_enum_values = True
    
    class UserSchema(BaseValidationSchema):
        """Schema para validação de dados de usuário"""
        user_id: int = Field(..., gt=0, description="ID do usuário Discord")
        username: str = Field(..., min_length=1, max_length=32, description="Nome de usuário")
        discriminator: Optional[str] = Field(None, regex=r"^\d{4}$", description="Discriminador do usuário")
        email: Optional[EmailStr] = Field(None, description="Email do usuário")
        avatar_url: Optional[HttpUrl] = Field(None, description="URL do avatar")
        is_bot: bool = Field(False, description="Se é um bot")
        is_verified: bool = Field(False, description="Se está verificado")
        created_at: Optional[datetime] = Field(None, description="Data de criação")
        
        @validator('username')
        def validate_username(cls, v):
            if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
                raise ValueError('Username contém caracteres inválidos')
            return v
        
        @validator('user_id')
        def validate_discord_id(cls, v):
            if not (17 <= len(str(v)) <= 19):
                raise ValueError('ID Discord inválido')
            return v
    
    class GuildSchema(BaseValidationSchema):
        """Schema para validação de dados de servidor"""
        guild_id: int = Field(..., gt=0, description="ID do servidor Discord")
        name: str = Field(..., min_length=1, max_length=100, description="Nome do servidor")
        owner_id: int = Field(..., gt=0, description="ID do dono do servidor")
        member_count: Optional[int] = Field(None, ge=0, description="Número de membros")
        icon_url: Optional[HttpUrl] = Field(None, description="URL do ícone")
        region: Optional[str] = Field(None, description="Região do servidor")
        verification_level: Optional[int] = Field(None, ge=0, le=4, description="Nível de verificação")
        created_at: Optional[datetime] = Field(None, description="Data de criação")
        
        @validator('name')
        def validate_guild_name(cls, v):
            if len(v.strip()) == 0:
                raise ValueError('Nome do servidor não pode estar vazio')
            return v.strip()
    
    class ChannelSchema(BaseValidationSchema):
        """Schema para validação de dados de canal"""
        channel_id: int = Field(..., gt=0, description="ID do canal Discord")
        name: str = Field(..., min_length=1, max_length=100, description="Nome do canal")
        guild_id: Optional[int] = Field(None, gt=0, description="ID do servidor")
        channel_type: str = Field(..., description="Tipo do canal")
        topic: Optional[str] = Field(None, max_length=1024, description="Tópico do canal")
        position: Optional[int] = Field(None, ge=0, description="Posição do canal")
        is_nsfw: bool = Field(False, description="Se é NSFW")
        created_at: Optional[datetime] = Field(None, description="Data de criação")
        
        @validator('name')
        def validate_channel_name(cls, v):
            if not re.match(r'^[a-z0-9_-]+$', v.lower()):
                raise ValueError('Nome do canal contém caracteres inválidos')
            return v.lower()
    
    class MessageSchema(BaseValidationSchema):
        """Schema para validação de mensagens"""
        message_id: int = Field(..., gt=0, description="ID da mensagem")
        content: str = Field(..., max_length=2000, description="Conteúdo da mensagem")
        author_id: int = Field(..., gt=0, description="ID do autor")
        channel_id: int = Field(..., gt=0, description="ID do canal")
        guild_id: Optional[int] = Field(None, gt=0, description="ID do servidor")
        timestamp: datetime = Field(..., description="Timestamp da mensagem")
        edited_timestamp: Optional[datetime] = Field(None, description="Timestamp de edição")
        is_pinned: bool = Field(False, description="Se está fixada")
        mention_everyone: bool = Field(False, description="Se menciona everyone")
        
        @validator('content')
        def validate_content(cls, v):
            # Remover caracteres de controle
            v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
            return v.strip()
    
    class CommandSchema(BaseValidationSchema):
        """Schema para validação de comandos"""
        command_name: str = Field(..., min_length=1, max_length=32, description="Nome do comando")
        user_id: int = Field(..., gt=0, description="ID do usuário")
        guild_id: Optional[int] = Field(None, gt=0, description="ID do servidor")
        channel_id: int = Field(..., gt=0, description="ID do canal")
        arguments: List[str] = Field(default_factory=list, description="Argumentos do comando")
        timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
        
        @validator('command_name')
        def validate_command_name(cls, v):
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Nome do comando contém caracteres inválidos')
            return v.lower()
        
        @validator('arguments')
        def validate_arguments(cls, v):
            if len(v) > 20:  # Limite de argumentos
                raise ValueError('Muitos argumentos fornecidos')
            return [arg.strip() for arg in v if arg.strip()]
    
    class ConfigSchema(BaseValidationSchema):
        """Schema para validação de configurações"""
        bot_token: SecretStr = Field(..., description="Token do bot")
        command_prefix: str = Field("!", min_length=1, max_length=5, description="Prefixo de comandos")
        owner_ids: List[int] = Field(default_factory=list, description="IDs dos donos")
        debug_mode: bool = Field(False, description="Modo debug")
        log_level: str = Field("INFO", description="Nível de log")
        database_url: Optional[str] = Field(None, description="URL do banco de dados")
        cache_size: int = Field(1000, gt=0, le=10000, description="Tamanho do cache")
        rate_limit_per_user: int = Field(10, gt=0, le=100, description="Rate limit por usuário")
        
        @validator('bot_token')
        def validate_bot_token(cls, v):
            token_str = v.get_secret_value() if hasattr(v, 'get_secret_value') else str(v)
            if not re.match(r'^[A-Za-z0-9._-]+$', token_str):
                raise ValueError('Token do bot inválido')
            if len(token_str) < 50:
                raise ValueError('Token do bot muito curto')
            return v
        
        @validator('log_level')
        def validate_log_level(cls, v):
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in valid_levels:
                raise ValueError(f'Nível de log deve ser um de: {valid_levels}')
            return v.upper()
        
        @validator('owner_ids')
        def validate_owner_ids(cls, v):
            for owner_id in v:
                if not (17 <= len(str(owner_id)) <= 19):
                    raise ValueError(f'ID de dono inválido: {owner_id}')
            return v
    
    class PUBGPlayerSchema(BaseValidationSchema):
        """Schema para validação de dados de jogador PUBG"""
        player_name: str = Field(..., min_length=1, max_length=24, description="Nome do jogador")
        platform: str = Field(..., description="Plataforma")
        region: Optional[str] = Field(None, description="Região")
        season: Optional[str] = Field(None, description="Temporada")
        game_mode: str = Field("squad", description="Modo de jogo")
        
        @validator('player_name')
        def validate_player_name(cls, v):
            if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
                raise ValueError('Nome do jogador contém caracteres inválidos')
            return v
        
        @validator('platform')
        def validate_platform(cls, v):
            valid_platforms = ['steam', 'xbox', 'psn', 'stadia']
            if v.lower() not in valid_platforms:
                raise ValueError(f'Plataforma deve ser uma de: {valid_platforms}')
            return v.lower()
        
        @validator('game_mode')
        def validate_game_mode(cls, v):
            valid_modes = ['solo', 'duo', 'squad']
            if v.lower() not in valid_modes:
                raise ValueError(f'Modo de jogo deve ser um de: {valid_modes}')
            return v.lower()
    
    class MusicTrackSchema(BaseValidationSchema):
        """Schema para validação de faixas de música"""
        title: str = Field(..., min_length=1, max_length=200, description="Título da música")
        url: HttpUrl = Field(..., description="URL da música")
        duration: Optional[int] = Field(None, gt=0, le=7200, description="Duração em segundos")
        thumbnail: Optional[HttpUrl] = Field(None, description="URL da thumbnail")
        uploader: Optional[str] = Field(None, max_length=100, description="Uploader")
        requested_by: int = Field(..., gt=0, description="ID de quem solicitou")
        
        @validator('title')
        def validate_title(cls, v):
            # Remover caracteres especiais perigosos
            v = re.sub(r'[<>:"/\\|?*]', '', v)
            return v.strip()
        
        @validator('url')
        def validate_music_url(cls, v):
            url_str = str(v)
            valid_domains = ['youtube.com', 'youtu.be', 'soundcloud.com', 'spotify.com']
            if not any(domain in url_str for domain in valid_domains):
                raise ValueError('URL de música não suportada')
            return v
else:
    # Fallback classes quando Pydantic não está disponível
    class BaseValidationSchema:
        pass
    
    class UserSchema(BaseValidationSchema):
        pass
    
    class GuildSchema(BaseValidationSchema):
        pass
    
    class ChannelSchema(BaseValidationSchema):
        pass
    
    class MessageSchema(BaseValidationSchema):
        pass
    
    class CommandSchema(BaseValidationSchema):
        pass
    
    class ConfigSchema(BaseValidationSchema):
        pass
    
    class PUBGPlayerSchema(BaseValidationSchema):
        pass
    
    class MusicTrackSchema(BaseValidationSchema):
        pass

class DataValidator:
    """Sistema principal de validação de dados"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL):
        self.validation_level = validation_level
        self.logger = logging.getLogger(__name__)
        self.custom_validators: Dict[str, Callable] = {}
        self.schemas: Dict[str, Type[BaseValidationSchema]] = {
            'user': UserSchema,
            'guild': GuildSchema,
            'channel': ChannelSchema,
            'message': MessageSchema,
            'command': CommandSchema,
            'config': ConfigSchema,
            'pubg_player': PUBGPlayerSchema,
            'music_track': MusicTrackSchema
        }
        
        # Estatísticas
        self.validation_count = 0
        self.validation_errors = 0
        self.validation_warnings = 0
    
    def add_custom_validator(self, name: str, validator_func: Callable):
        """Adiciona um validador customizado"""
        self.custom_validators[name] = validator_func
        self.logger.info(f"Validador customizado '{name}' adicionado")
    
    def add_schema(self, name: str, schema_class: Type[BaseValidationSchema]):
        """Adiciona um schema customizado"""
        self.schemas[name] = schema_class
        self.logger.info(f"Schema '{name}' adicionado")
    
    def validate_data(self, data: Dict[str, Any], schema_name: str, 
                     strict: Optional[bool] = None) -> Tuple[bool, Optional[Any], List[str]]:
        """Valida dados usando um schema específico"""
        if self.validation_level == ValidationLevel.DISABLED:
            return True, data, []
        
        if not PYDANTIC_AVAILABLE:
            self.logger.warning("Pydantic não disponível, validação básica aplicada")
            return self._basic_validation(data, schema_name)
        
        self.validation_count += 1
        
        if schema_name not in self.schemas:
            error_msg = f"Schema '{schema_name}' não encontrado"
            self.logger.error(error_msg)
            self.validation_errors += 1
            return False, None, [error_msg]
        
        schema_class = self.schemas[schema_name]
        errors = []
        
        try:
            # Determinar se deve usar validação estrita
            use_strict = strict if strict is not None else (self.validation_level == ValidationLevel.STRICT)
            
            if use_strict:
                validated_data = schema_class(**data)
            else:
                # Validação mais permissiva
                filtered_data = self._filter_data_for_schema(data, schema_class)
                validated_data = schema_class(**filtered_data)
            
            return True, validated_data.dict() if hasattr(validated_data, 'dict') else data, []
            
        except ValidationError as e:
            self.validation_errors += 1
            
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                message = error['msg']
                errors.append(f"{field}: {message}")
            
            self.logger.warning(f"Erro de validação para schema '{schema_name}': {errors}")
            
            # Em modo leniente, retornar dados parcialmente validados
            if self.validation_level == ValidationLevel.LENIENT:
                cleaned_data = self._clean_invalid_data(data, e.errors())
                return True, cleaned_data, errors
            
            return False, None, errors
            
        except Exception as e:
            self.validation_errors += 1
            error_msg = f"Erro inesperado na validação: {str(e)}"
            self.logger.error(error_msg)
            return False, None, [error_msg]
    
    def _basic_validation(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, Any, List[str]]:
        """Validação básica quando Pydantic não está disponível"""
        warnings = []
        
        # Validações básicas por tipo de schema
        if schema_name == 'user':
            if 'user_id' not in data or not isinstance(data['user_id'], int):
                return False, None, ['user_id é obrigatório e deve ser um inteiro']
            if data['user_id'] <= 0:
                return False, None, ['user_id deve ser positivo']
        
        elif schema_name == 'command':
            if 'command_name' not in data or not isinstance(data['command_name'], str):
                return False, None, ['command_name é obrigatório e deve ser uma string']
            if not data['command_name'].strip():
                return False, None, ['command_name não pode estar vazio']
        
        elif schema_name == 'config':
            if 'bot_token' not in data:
                return False, None, ['bot_token é obrigatório']
            if len(str(data['bot_token'])) < 50:
                return False, None, ['bot_token muito curto']
        
        return True, data, warnings
    
    def _filter_data_for_schema(self, data: Dict[str, Any], schema_class) -> Dict[str, Any]:
        """Filtra dados para incluir apenas campos válidos do schema"""
        if not hasattr(schema_class, '__fields__'):
            return data
        
        valid_fields = set(schema_class.__fields__.keys())
        return {k: v for k, v in data.items() if k in valid_fields}
    
    def _clean_invalid_data(self, data: Dict[str, Any], errors: List[Dict]) -> Dict[str, Any]:
        """Remove campos inválidos dos dados"""
        invalid_fields = set()
        
        for error in errors:
            if error['loc']:
                invalid_fields.add(error['loc'][0])
        
        return {k: v for k, v in data.items() if k not in invalid_fields}
    
    def validate_discord_user(self, user) -> Tuple[bool, Optional[Dict], List[str]]:
        """Valida um objeto User do Discord"""
        if not DISCORD_AVAILABLE or not user:
            return False, None, ['Discord não disponível ou usuário inválido']
        
        user_data = {
            'user_id': user.id,
            'username': user.name,
            'discriminator': user.discriminator,
            'avatar_url': str(user.avatar_url) if user.avatar else None,
            'is_bot': user.bot,
            'created_at': user.created_at
        }
        
        return self.validate_data(user_data, 'user')
    
    def validate_discord_guild(self, guild) -> Tuple[bool, Optional[Dict], List[str]]:
        """Valida um objeto Guild do Discord"""
        if not DISCORD_AVAILABLE or not guild:
            return False, None, ['Discord não disponível ou servidor inválido']
        
        guild_data = {
            'guild_id': guild.id,
            'name': guild.name,
            'owner_id': guild.owner_id,
            'member_count': guild.member_count,
            'icon_url': str(guild.icon_url) if guild.icon else None,
            'region': str(guild.region) if hasattr(guild, 'region') else None,
            'verification_level': guild.verification_level.value if hasattr(guild.verification_level, 'value') else None,
            'created_at': guild.created_at
        }
        
        return self.validate_data(guild_data, 'guild')
    
    def validate_discord_message(self, message) -> Tuple[bool, Optional[Dict], List[str]]:
        """Valida um objeto Message do Discord"""
        if not DISCORD_AVAILABLE or not message:
            return False, None, ['Discord não disponível ou mensagem inválida']
        
        message_data = {
            'message_id': message.id,
            'content': message.content,
            'author_id': message.author.id,
            'channel_id': message.channel.id,
            'guild_id': message.guild.id if message.guild else None,
            'timestamp': message.created_at,
            'edited_timestamp': message.edited_at,
            'is_pinned': message.pinned,
            'mention_everyone': message.mention_everyone
        }
        
        return self.validate_data(message_data, 'message')
    
    def validate_command_context(self, ctx, command_name: str, arguments: List[str]) -> Tuple[bool, Optional[Dict], List[str]]:
        """Valida contexto de comando"""
        if not DISCORD_AVAILABLE or not ctx:
            return False, None, ['Discord não disponível ou contexto inválido']
        
        command_data = {
            'command_name': command_name,
            'user_id': ctx.author.id,
            'guild_id': ctx.guild.id if ctx.guild else None,
            'channel_id': ctx.channel.id,
            'arguments': arguments,
            'timestamp': datetime.now()
        }
        
        return self.validate_data(command_data, 'command')
    
    def sanitize_input(self, text: str, max_length: int = 2000) -> str:
        """Sanitiza entrada de texto"""
        if not isinstance(text, str):
            text = str(text)
        
        # Remover caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remover caracteres perigosos
        text = re.sub(r'[<>"\']', '', text)
        
        # Limitar comprimento
        if len(text) > max_length:
            text = text[:max_length-3] + '...'
        
        return text.strip()
    
    def validate_json(self, json_str: str) -> Tuple[bool, Optional[Dict], List[str]]:
        """Valida string JSON"""
        try:
            data = json.loads(json_str)
            return True, data, []
        except json.JSONDecodeError as e:
            return False, None, [f"JSON inválido: {str(e)}"]
    
    def validate_custom(self, data: Any, validator_name: str) -> Tuple[bool, Any, List[str]]:
        """Executa validador customizado"""
        if validator_name not in self.custom_validators:
            return False, None, [f"Validador '{validator_name}' não encontrado"]
        
        try:
            validator_func = self.custom_validators[validator_name]
            result = validator_func(data)
            
            if isinstance(result, tuple):
                return result
            else:
                return True, result, []
                
        except Exception as e:
            return False, None, [f"Erro no validador customizado: {str(e)}"]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de validação"""
        success_rate = 0
        if self.validation_count > 0:
            success_rate = ((self.validation_count - self.validation_errors) / self.validation_count) * 100
        
        return {
            'total_validations': self.validation_count,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings,
            'success_rate': round(success_rate, 2),
            'validation_level': self.validation_level.value,
            'pydantic_available': PYDANTIC_AVAILABLE,
            'registered_schemas': list(self.schemas.keys()),
            'custom_validators': list(self.custom_validators.keys())
        }
    
    def reset_stats(self):
        """Reseta estatísticas de validação"""
        self.validation_count = 0
        self.validation_errors = 0
        self.validation_warnings = 0

# Instância global do validador
_data_validator: Optional[DataValidator] = None

def get_data_validator() -> DataValidator:
    """Obtém a instância global do validador de dados"""
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator

# Funções de conveniência
def validate_data(data: Dict[str, Any], schema_name: str, strict: Optional[bool] = None) -> Tuple[bool, Optional[Any], List[str]]:
    """Valida dados usando schema"""
    return get_data_validator().validate_data(data, schema_name, strict)

def validate_user(user) -> Tuple[bool, Optional[Dict], List[str]]:
    """Valida usuário Discord"""
    return get_data_validator().validate_discord_user(user)

def validate_guild(guild) -> Tuple[bool, Optional[Dict], List[str]]:
    """Valida servidor Discord"""
    return get_data_validator().validate_discord_guild(guild)

def validate_message(message) -> Tuple[bool, Optional[Dict], List[str]]:
    """Valida mensagem Discord"""
    return get_data_validator().validate_discord_message(message)

def validate_command(ctx, command_name: str, arguments: List[str]) -> Tuple[bool, Optional[Dict], List[str]]:
    """Valida contexto de comando"""
    return get_data_validator().validate_command_context(ctx, command_name, arguments)

def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Sanitiza entrada de texto"""
    return get_data_validator().sanitize_input(text, max_length)

def add_custom_validator(name: str, validator_func: Callable):
    """Adiciona validador customizado"""
    get_data_validator().add_custom_validator(name, validator_func)

def add_schema(name: str, schema_class: Type[BaseValidationSchema]):
    """Adiciona schema customizado"""
    get_data_validator().add_schema(name, schema_class)

def get_validation_stats() -> Dict[str, Any]:
    """Obtém estatísticas de validação"""
    return get_data_validator().get_validation_stats()

# Decorador para validação automática
def validate_input(schema_name: str, strict: bool = False):
    """Decorador para validação automática de entrada"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Tentar extrair dados do contexto
            if args and hasattr(args[0], '__dict__'):
                ctx = args[0]
                
                # Validar contexto se for comando Discord
                if DISCORD_AVAILABLE and hasattr(ctx, 'author'):
                    command_name = func.__name__
                    arguments = list(args[1:]) + list(kwargs.values())
                    
                    valid, validated_data, errors = validate_command(ctx, command_name, [str(arg) for arg in arguments])
                    
                    if not valid and errors:
                        if hasattr(ctx, 'send'):
                            await ctx.send(f"❌ Erro de validação: {'; '.join(errors[:3])}")
                        return
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Validadores customizados úteis
def discord_id_validator(value: Any) -> int:
    """Validador para IDs do Discord"""
    try:
        id_int = int(value)
        if not (17 <= len(str(id_int)) <= 19):
            raise ValueError("ID Discord deve ter entre 17 e 19 dígitos")
        return id_int
    except (ValueError, TypeError):
        raise ValueError("ID Discord inválido")

def discord_token_validator(value: str) -> str:
    """Validador para tokens do Discord"""
    if not isinstance(value, str):
        raise ValueError("Token deve ser uma string")
    
    if len(value) < 50:
        raise ValueError("Token muito curto")
    
    if not re.match(r'^[A-Za-z0-9._-]+$', value):
        raise ValueError("Token contém caracteres inválidos")
    
    return value

def pubg_username_validator(value: str) -> str:
    """Validador para nomes de usuário PUBG"""
    if not isinstance(value, str):
        raise ValueError("Nome de usuário deve ser uma string")
    
    value = value.strip()
    
    if not (1 <= len(value) <= 24):
        raise ValueError("Nome de usuário deve ter entre 1 e 24 caracteres")
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise ValueError("Nome de usuário contém caracteres inválidos")
    
    return value

# Registrar validadores customizados padrão
def _register_default_validators():
    """Registra validadores customizados padrão"""
    validator = get_data_validator()
    validator.add_custom_validator('discord_id', discord_id_validator)
    validator.add_custom_validator('discord_token', discord_token_validator)
    validator.add_custom_validator('pubg_username', pubg_username_validator)

# Inicializar validadores padrão
_register_default_validators()