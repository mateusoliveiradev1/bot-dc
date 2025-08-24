"""Módulo de configuração do Hawk Bot."""

from .settings import settings, Settings
from .env_loader import env_loader, EnvLoader

# Importar configuração moderna se disponível
try:
    from ..config import get_config, validate_config, HawkBotConfig
    __all__ = ['settings', 'Settings', 'env_loader', 'EnvLoader', 'get_config', 'validate_config', 'HawkBotConfig']
except ImportError:
    __all__ = ['settings', 'Settings', 'env_loader', 'EnvLoader']