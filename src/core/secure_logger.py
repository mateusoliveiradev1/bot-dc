# -*- coding: utf-8 -*-
"""
Sistema de Logging Seguro - Hawk Bot
Logging com sanitização automática de dados sensíveis e estruturação avançada
"""

import logging
import logging.handlers
import re
import json
import traceback
import asyncio
import threading
from typing import Any, Dict, List, Optional, Union, Callable, Pattern
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import sys
import os
from contextlib import contextmanager
from collections import deque, defaultdict
import time

class LogLevel(Enum):
    """Níveis de log personalizados"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    SECURITY = 60  # Nível especial para eventos de segurança

class SensitiveDataType(Enum):
    """Tipos de dados sensíveis para sanitização"""
    TOKEN = "token"
    PASSWORD = "password"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    CREDIT_CARD = "credit_card"
    PHONE = "phone"
    API_KEY = "api_key"
    SESSION_ID = "session_id"
    PERSONAL_NAME = "personal_name"
    CUSTOM = "custom"

@dataclass
class SanitizationRule:
    """Regra de sanitização para dados sensíveis"""
    name: str
    pattern: Pattern[str]
    replacement: str
    data_type: SensitiveDataType
    enabled: bool = True
    case_sensitive: bool = False
    
    def sanitize(self, text: str) -> str:
        """Aplica a sanitização no texto"""
        if not self.enabled:
            return text
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.sub(self.pattern, self.replacement, text, flags=flags)

@dataclass
class LogContext:
    """Contexto adicional para logs estruturados"""
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    command: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte contexto para dicionário"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result

class LogFormatter(logging.Formatter):
    """Formatador personalizado para logs estruturados"""
    
    def __init__(self, 
                 include_context: bool = True,
                 include_stack_trace: bool = True,
                 json_format: bool = False):
        self.include_context = include_context
        self.include_stack_trace = include_stack_trace
        self.json_format = json_format
        
        if json_format:
            super().__init__()
        else:
            fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro de log"""
        # Adicionar informações extras
        record.timestamp_iso = datetime.now(timezone.utc).isoformat()
        record.thread_name = threading.current_thread().name
        record.process_id = os.getpid()
        
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Formata como JSON estruturado"""
        log_data = {
            "timestamp": record.timestamp_iso,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread_name,
            "process_id": record.process_id
        }
        
        # Adicionar contexto se disponível
        if self.include_context and hasattr(record, 'context'):
            log_data["context"] = record.context.to_dict()
        
        # Adicionar stack trace para erros
        if self.include_stack_trace and record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Adicionar campos extras
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'exc_info', 'exc_text', 'stack_info', 'getMessage']:
                    log_data["extra"] = log_data.get("extra", {})
                    log_data["extra"][key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Formata como texto legível"""
        formatted = super().format(record)
        
        # Adicionar contexto se disponível
        if self.include_context and hasattr(record, 'context'):
            context_data = record.context.to_dict()
            if context_data:
                context_str = " | ".join([f"{k}={v}" for k, v in context_data.items()])
                formatted += f" | Context: {context_str}"
        
        return formatted

class DataSanitizer:
    """Sanitizador de dados sensíveis"""
    
    def __init__(self):
        self.rules: List[SanitizationRule] = []
        self._setup_default_rules()
        self._compiled_patterns: Dict[str, Pattern] = {}
    
    def _setup_default_rules(self):
        """Configura regras padrão de sanitização"""
        # Tokens do Discord
        self.add_rule(
            "discord_bot_token",
            r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}",
            "[DISCORD_BOT_TOKEN]",
            SensitiveDataType.TOKEN
        )
        
        # Tokens de usuário Discord
        self.add_rule(
            "discord_user_token",
            r"[A-Za-z\d]{24}\.[\w-]{6}\.[\w-]{27}",
            "[DISCORD_USER_TOKEN]",
            SensitiveDataType.TOKEN
        )
        
        # Senhas genéricas
        self.add_rule(
            "password_fields",
            r"(?i)(password|passwd|pwd|secret)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?",
            r"\1: [PASSWORD]",
            SensitiveDataType.PASSWORD
        )
        
        # Emails
        self.add_rule(
            "email_addresses",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL]",
            SensitiveDataType.EMAIL
        )
        
        # IPs
        self.add_rule(
            "ip_addresses",
            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "[IP_ADDRESS]",
            SensitiveDataType.IP_ADDRESS
        )
        
        # IDs de usuário Discord
        self.add_rule(
            "discord_user_ids",
            r"(?i)user[_\s]*id\s*[:=]\s*['\"]?(\d{17,19})['\"]?",
            "user_id: [USER_ID]",
            SensitiveDataType.USER_ID
        )
        
        # Chaves de API genéricas
        self.add_rule(
            "api_keys",
            r"(?i)(api[_\s]*key|apikey|access[_\s]*token)\s*[:=]\s*['\"]?([A-Za-z0-9\-_]{20,})['\"]?",
            r"\1: [API_KEY]",
            SensitiveDataType.API_KEY
        )
        
        # Session IDs
        self.add_rule(
            "session_ids",
            r"(?i)session[_\s]*id\s*[:=]\s*['\"]?([A-Za-z0-9\-_]{16,})['\"]?",
            "session_id: [SESSION_ID]",
            SensitiveDataType.SESSION_ID
        )
        
        # Cartões de crédito (básico)
        self.add_rule(
            "credit_cards",
            r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
            "[CREDIT_CARD]",
            SensitiveDataType.CREDIT_CARD
        )
        
        # Telefones (formato brasileiro)
        self.add_rule(
            "phone_numbers",
            r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\s-]?\d{4}\b",
            "[PHONE]",
            SensitiveDataType.PHONE
        )
    
    def add_rule(self, 
                 name: str, 
                 pattern: Union[str, Pattern], 
                 replacement: str,
                 data_type: SensitiveDataType,
                 enabled: bool = True,
                 case_sensitive: bool = False):
        """Adiciona uma nova regra de sanitização"""
        if isinstance(pattern, str):
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled_pattern = re.compile(pattern, flags)
        else:
            compiled_pattern = pattern
        
        rule = SanitizationRule(
            name=name,
            pattern=compiled_pattern,
            replacement=replacement,
            data_type=data_type,
            enabled=enabled,
            case_sensitive=case_sensitive
        )
        
        # Remover regra existente com o mesmo nome
        self.rules = [r for r in self.rules if r.name != name]
        self.rules.append(rule)
    
    def remove_rule(self, name: str):
        """Remove uma regra de sanitização"""
        self.rules = [r for r in self.rules if r.name != name]
    
    def enable_rule(self, name: str, enabled: bool = True):
        """Habilita/desabilita uma regra"""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = enabled
                break
    
    def sanitize(self, text: str) -> str:
        """Sanitiza um texto aplicando todas as regras ativas"""
        if not isinstance(text, str):
            text = str(text)
        
        result = text
        for rule in self.rules:
            if rule.enabled:
                result = rule.sanitize(result)
        
        return result
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza um dicionário recursivamente"""
        result = {}
        for key, value in data.items():
            sanitized_key = self.sanitize(key)
            
            if isinstance(value, dict):
                result[sanitized_key] = self.sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                result[sanitized_key] = [self.sanitize_dict(item) if isinstance(item, dict) 
                                       else self.sanitize(str(item)) for item in value]
            else:
                result[sanitized_key] = self.sanitize(str(value))
        
        return result

class SecureLogHandler(logging.Handler):
    """Handler de log seguro com sanitização automática"""
    
    def __init__(self, 
                 base_handler: logging.Handler,
                 sanitizer: Optional[DataSanitizer] = None):
        super().__init__()
        self.base_handler = base_handler
        self.sanitizer = sanitizer or DataSanitizer()
        self.setLevel(base_handler.level)
        self.setFormatter(base_handler.formatter)
    
    def emit(self, record: logging.LogRecord):
        """Emite o log após sanitização"""
        try:
            # Sanitizar a mensagem
            if hasattr(record, 'msg') and record.msg:
                record.msg = self.sanitizer.sanitize(str(record.msg))
            
            # Sanitizar argumentos
            if hasattr(record, 'args') and record.args:
                sanitized_args = []
                for arg in record.args:
                    if isinstance(arg, dict):
                        sanitized_args.append(self.sanitizer.sanitize_dict(arg))
                    else:
                        sanitized_args.append(self.sanitizer.sanitize(str(arg)))
                record.args = tuple(sanitized_args)
            
            # Sanitizar contexto se presente
            if hasattr(record, 'context') and record.context:
                context_dict = record.context.to_dict()
                sanitized_context_dict = self.sanitizer.sanitize_dict(context_dict)
                # Recriar contexto com dados sanitizados
                record.context = LogContext(**sanitized_context_dict)
            
            # Delegar para o handler base
            self.base_handler.emit(record)
            
        except Exception as e:
            self.handleError(record)

class PerformanceLogger:
    """Logger para métricas de performance"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    
    @contextmanager
    def measure(self, operation: str, context: Optional[LogContext] = None):
        """Context manager para medir tempo de operação"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            duration_ms = (end_time - start_time) * 1000
            memory_delta = end_memory - start_memory
            
            # Armazenar métrica
            self.metrics[operation].append({
                'duration_ms': duration_ms,
                'memory_delta_mb': memory_delta,
                'timestamp': time.time()
            })
            
            # Log da performance
            perf_context = context or LogContext()
            perf_context.operation = operation
            perf_context.duration_ms = duration_ms
            perf_context.metadata = {
                'memory_delta_mb': memory_delta,
                'start_memory_mb': start_memory,
                'end_memory_mb': end_memory
            }
            
            self.logger.info(
                f"Performance: {operation} completed in {duration_ms:.2f}ms",
                extra={'context': perf_context}
            )
    
    def _get_memory_usage(self) -> float:
        """Obtém uso atual de memória em MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Obtém estatísticas de uma operação"""
        if operation not in self.metrics:
            return {}
        
        durations = [m['duration_ms'] for m in self.metrics[operation]]
        memory_deltas = [m['memory_delta_mb'] for m in self.metrics[operation]]
        
        if not durations:
            return {}
        
        return {
            'operation': operation,
            'count': len(durations),
            'avg_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
            'total_calls': len(durations)
        }

class SecureLogger:
    """Logger principal com recursos de segurança avançados"""
    
    def __init__(self, 
                 name: str,
                 log_dir: Optional[Path] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 json_format: bool = False,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 sanitizer: Optional[DataSanitizer] = None):
        
        self.name = name
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.sanitizer = sanitizer or DataSanitizer()
        self.performance_logger = None
        
        # Configurar logger principal
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LogLevel.TRACE.value)
        
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Configurar formatador
        formatter = LogFormatter(
            include_context=True,
            include_stack_trace=True,
            json_format=json_format
        )
        
        # Handler para console
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            secure_console = SecureLogHandler(console_handler, self.sanitizer)
            secure_console.setFormatter(formatter)
            self.logger.addHandler(secure_console)
        
        # Handler para arquivo
        if enable_file:
            file_path = self.log_dir / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(LogLevel.TRACE.value)
            secure_file = SecureLogHandler(file_handler, self.sanitizer)
            secure_file.setFormatter(formatter)
            self.logger.addHandler(secure_file)
        
        # Handler para logs de segurança (arquivo separado)
        security_file_path = self.log_dir / f"{name}_security.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count * 2,  # Manter mais backups de segurança
            encoding='utf-8'
        )
        security_handler.setLevel(LogLevel.SECURITY.value)
        security_handler.addFilter(lambda record: record.levelno >= LogLevel.SECURITY.value)
        secure_security = SecureLogHandler(security_handler, self.sanitizer)
        secure_security.setFormatter(formatter)
        self.logger.addHandler(secure_security)
        
        # Configurar performance logger
        self.performance_logger = PerformanceLogger(self.logger)
        
        # Adicionar nível SECURITY personalizado
        logging.addLevelName(LogLevel.SECURITY.value, "SECURITY")
        logging.addLevelName(LogLevel.TRACE.value, "TRACE")
    
    def _log_with_context(self, level: int, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log interno com contexto"""
        extra = kwargs.get('extra', {})
        if context:
            extra['context'] = context
        kwargs['extra'] = extra
        
        self.logger.log(level, message, **kwargs)
    
    def trace(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de trace (mais detalhado que debug)"""
        self._log_with_context(LogLevel.TRACE.value, message, context, **kwargs)
    
    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de debug"""
        self._log_with_context(LogLevel.DEBUG.value, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de informação"""
        self._log_with_context(LogLevel.INFO.value, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de aviso"""
        self._log_with_context(LogLevel.WARNING.value, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log de erro"""
        kwargs['exc_info'] = exc_info
        self._log_with_context(LogLevel.ERROR.value, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[LogContext] = None, exc_info: bool = True, **kwargs):
        """Log crítico"""
        kwargs['exc_info'] = exc_info
        self._log_with_context(LogLevel.CRITICAL.value, message, context, **kwargs)
    
    def security(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log de evento de segurança"""
        # Adicionar timestamp de segurança
        security_context = context or LogContext()
        security_context.metadata = security_context.metadata or {}
        security_context.metadata['security_event'] = True
        security_context.metadata['security_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        self._log_with_context(LogLevel.SECURITY.value, f"[SECURITY] {message}", security_context, **kwargs)
    
    def measure_performance(self, operation: str, context: Optional[LogContext] = None):
        """Context manager para medir performance"""
        return self.performance_logger.measure(operation, context)
    
    def get_performance_stats(self, operation: str) -> Dict[str, Any]:
        """Obtém estatísticas de performance"""
        return self.performance_logger.get_stats(operation)
    
    def add_sanitization_rule(self, 
                             name: str, 
                             pattern: Union[str, Pattern], 
                             replacement: str,
                             data_type: SensitiveDataType = SensitiveDataType.CUSTOM):
        """Adiciona regra de sanitização personalizada"""
        self.sanitizer.add_rule(name, pattern, replacement, data_type)
    
    def set_level(self, level: Union[int, str, LogLevel]):
        """Define o nível de log"""
        if isinstance(level, LogLevel):
            level = level.value
        elif isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        
        self.logger.setLevel(level)

# Logger global seguro
_global_secure_logger: Optional[SecureLogger] = None

def get_secure_logger(name: str = "HawkBot") -> SecureLogger:
    """Obtém a instância global do logger seguro"""
    global _global_secure_logger
    if _global_secure_logger is None:
        _global_secure_logger = SecureLogger(
            name=name,
            log_dir=Path("logs"),
            max_file_size=10 * 1024 * 1024,  # 10MB
            backup_count=5,
            json_format=False,
            enable_console=True,
            enable_file=True
        )
    return _global_secure_logger

# Decorador para logging automático
def logged_operation(operation_name: str = None, 
                    log_args: bool = False,
                    log_result: bool = False,
                    log_performance: bool = True):
    """Decorador para logging automático de operações"""
    def decorator(func: Callable):
        op_name = operation_name or f"{func.__module__}.{func.__qualname__}"
        
        async def async_wrapper(*args, **kwargs):
            logger = get_secure_logger()
            context = LogContext(
                component=func.__module__,
                operation=func.__qualname__
            )
            
            # Log de entrada
            if log_args:
                logger.debug(f"Iniciando {op_name}", context)
            else:
                logger.debug(f"Iniciando {op_name}", context)
            
            try:
                if log_performance:
                    with logger.measure_performance(op_name, context):
                        result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Log de sucesso
                if log_result and result is not None:
                    logger.debug(f"{op_name} concluído com sucesso", context)
                else:
                    logger.debug(f"{op_name} concluído", context)
                
                return result
                
            except Exception as e:
                logger.error(f"Erro em {op_name}: {str(e)}", context)
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = get_secure_logger()
            context = LogContext(
                component=func.__module__,
                operation=func.__qualname__
            )
            
            # Log de entrada
            logger.debug(f"Iniciando {op_name}", context)
            
            try:
                if log_performance:
                    # Para funções síncronas, usar asyncio.run para o context manager
                    import asyncio
                    async def measure_sync():
                        with logger.measure_performance(op_name, context):
                            return func(*args, **kwargs)
                    
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Se já há um loop rodando, executar diretamente
                            result = func(*args, **kwargs)
                        else:
                            result = loop.run_until_complete(measure_sync())
                    except RuntimeError:
                        result = asyncio.run(measure_sync())
                else:
                    result = func(*args, **kwargs)
                
                # Log de sucesso
                logger.debug(f"{op_name} concluído", context)
                return result
                
            except Exception as e:
                logger.error(f"Erro em {op_name}: {str(e)}", context)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Context manager para contexto de log
@contextmanager
def log_context(**context_kwargs):
    """Context manager para definir contexto de log temporário"""
    context = LogContext(**context_kwargs)
    # Aqui você poderia implementar thread-local storage para o contexto
    # Por simplicidade, apenas yielding o contexto
    yield context