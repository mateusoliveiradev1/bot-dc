# -*- coding: utf-8 -*-
"""
Sistema de Logging Estruturado - Hawk Bot
Logging com contexto, sanitização e estruturação de dados

Este módulo mantém compatibilidade com o código existente enquanto
utiliza o novo sistema de logging seguro internamente.
"""

import logging
import logging.handlers
import json
import traceback
import asyncio
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys
import os

# Adicionar o diretório raiz ao path para importações
sys.path.append('.')

try:
    from src.core.config import get_config
except ImportError as e:
    print(f"Erro ao importar configuração: {e}")
    # Fallback para configuração padrão
    def get_config():
        return type('Config', (), {
            'LOG_LEVEL': 'INFO',
            'LOG_DIR': 'logs',
            'LOG_MAX_SIZE': 10 * 1024 * 1024,
            'LOG_BACKUP_COUNT': 5
        })()

# Importar o novo sistema de logging seguro
try:
    from .secure_logger import (
        SecureLogger, LogContext as SecureLogContext, 
        get_secure_logger, logged_operation, log_context,
        SensitiveDataType, DataSanitizer
    )
    SECURE_LOGGING_AVAILABLE = True
except ImportError:
    SECURE_LOGGING_AVAILABLE = False
    print("Sistema de logging seguro não disponível, usando logging básico")

@dataclass
class LogContext:
    """Contexto para logs estruturados (compatibilidade)"""
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    command: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte contexto para dicionário"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result
    
    def to_secure_context(self) -> 'SecureLogContext':
        """Converte para contexto do sistema seguro"""
        if SECURE_LOGGING_AVAILABLE:
            return SecureLogContext(
                user_id=self.user_id,
                guild_id=self.guild_id,
                channel_id=self.channel_id,
                command=self.command,
                session_id=self.session_id,
                request_id=self.request_id,
                metadata=self.metadata
            )
        return None

class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log em JSON estruturado"""
        # Dados básicos do log
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar dados extras do record
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                extra_data[key] = value
        
        if extra_data:
            log_data['extra'] = extra_data
        
        # Adicionar informações de exceção
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class StructuredLogger:
    """Logger estruturado com contexto e sanitização (wrapper para compatibilidade)"""
    
    def __init__(self, name: str, config=None):
        self.name = name
        self.config = config or get_config()
        
        if SECURE_LOGGING_AVAILABLE:
            # Usar o novo sistema de logging seguro
            self.secure_logger = get_secure_logger(name)
            self.logger = self.secure_logger.logger
        else:
            # Fallback para logging básico
            self.secure_logger = None
            self.logger = logging.getLogger(name)
            self._setup_basic_logger()
    
    def _setup_basic_logger(self):
        """Configura o logger básico (fallback)"""
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Definir nível
        level = getattr(logging, self.config.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Criar diretório de logs
        log_dir = Path(self.config.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        # Formatador JSON
        formatter = StructuredFormatter()
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}.log",
            maxBytes=self.config.LOG_MAX_SIZE,
            backupCount=self.config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para erros (arquivo separado)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}_errors.log",
            maxBytes=self.config.LOG_MAX_SIZE,
            backupCount=self.config.LOG_BACKUP_COUNT * 2,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitiza dados sensíveis antes do log (fallback)"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Sanitizar chaves sensíveis
                if any(sensitive in key.lower() for sensitive in ['token', 'password', 'secret', 'key']):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Sanitizar tokens do Discord e outras informações sensíveis
            import re
            # Token do bot Discord
            data = re.sub(r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}', '[DISCORD_TOKEN]', data)
            # Emails
            data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', data)
            # IPs
            data = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]', data)
            return data
        else:
            return data
    
    def _log_with_context(self, level: int, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log interno com contexto"""
        if self.secure_logger:
            # Usar sistema seguro
            secure_context = context.to_secure_context() if context else None
            
            if level == logging.DEBUG:
                self.secure_logger.debug(message, secure_context, **kwargs)
            elif level == logging.INFO:
                self.secure_logger.info(message, secure_context, **kwargs)
            elif level == logging.WARNING:
                self.secure_logger.warning(message, secure_context, **kwargs)
            elif level == logging.ERROR:
                self.secure_logger.error(message, secure_context, **kwargs)
            elif level == logging.CRITICAL:
                self.secure_logger.critical(message, secure_context, **kwargs)
        else:
            # Fallback para logging básico
            sanitized_message = self._sanitize_data(message)
            
            extra = kwargs.get('extra', {})
            if context:
                extra['context'] = self._sanitize_data(context.to_dict())
            
            # Sanitizar argumentos extras
            for key, value in extra.items():
                extra[key] = self._sanitize_data(value)
            
            kwargs['extra'] = extra
            self.logger.log(level, sanitized_message, **kwargs)
    
    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de debug"""
        self._log_with_context(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de informação"""
        self._log_with_context(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de aviso"""
        self._log_with_context(logging.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log de erro"""
        kwargs['exc_info'] = exc_info
        self._log_with_context(logging.ERROR, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log crítico"""
        kwargs['exc_info'] = exc_info
        self._log_with_context(logging.CRITICAL, message, context, **kwargs)
    
    def security(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de evento de segurança"""
        if self.secure_logger:
            secure_context = context.to_secure_context() if context else None
            self.secure_logger.security(message, secure_context, **kwargs)
        else:
            # Fallback: usar critical para eventos de segurança
            self.critical(f"[SECURITY] {message}", context, **kwargs)
    
    def measure_performance(self, operation: str, context: Optional[LogContext] = None):
        """Context manager para medir performance"""
        if self.secure_logger:
            secure_context = context.to_secure_context() if context else None
            return self.secure_logger.measure_performance(operation, secure_context)
        else:
            # Fallback: context manager vazio
            from contextlib import nullcontext
            return nullcontext()
    
    def add_sanitization_rule(self, name: str, pattern: str, replacement: str):
        """Adiciona regra de sanitização personalizada"""
        if self.secure_logger:
            self.secure_logger.add_sanitization_rule(name, pattern, replacement)

# Logger global
_global_logger: Optional[StructuredLogger] = None

def get_logger(name: str = "HawkBot") -> StructuredLogger:
    """Obtém a instância global do logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger

# Aliases para compatibilidade com o sistema seguro
if SECURE_LOGGING_AVAILABLE:
    # Exportar funcionalidades do sistema seguro
    SecureLogContext = SecureLogContext
    get_secure_logger = get_secure_logger
    logged_operation = logged_operation
    log_context = log_context
    SensitiveDataType = SensitiveDataType
    DataSanitizer = DataSanitizer
else:
    # Stubs para quando o sistema seguro não está disponível
    def logged_operation(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def log_context(**kwargs):
        from contextlib import nullcontext
        return nullcontext()

# Funções de conveniência para compatibilidade
def create_context(**kwargs) -> LogContext:
    """Cria um contexto de logging"""
    return LogContext(**kwargs)

def with_context(context: LogContext):
    """Context manager para definir contexto de logging"""
    if SECURE_LOGGING_AVAILABLE:
        return log_context(**context.to_dict())
    else:
        from contextlib import nullcontext
        return nullcontext()

# Decorador para logging automático (compatibilidade)
def logged(log_args: bool = False, log_result: bool = False, log_duration: bool = True):
    """Decorador para logging automático de funções"""
    if SECURE_LOGGING_AVAILABLE:
        return logged_operation(
            log_args=log_args,
            log_result=log_result,
            log_duration=log_duration
        )
    else:
        def decorator(func):
            return func
        return decorator