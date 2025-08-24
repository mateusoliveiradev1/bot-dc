"""Módulo de armazenamento do Hawk Bot."""

from .base import DataStorage
from .postgres_storage import PostgreSQLStorage as PostgresStorage

__all__ = ['DataStorage', 'PostgresStorage']