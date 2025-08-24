"""Sistema de backup automático para o Hawk Bot.

Este módulo fornece:
- Backup automático de dados do bot
- Backup de configurações
- Backup de logs
- Compressão e criptografia
- Rotação de backups
- Restauração de backups
- Sincronização com armazenamento remoto
"""

import asyncio
import os
import shutil
import zipfile
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import tempfile

try:
    import aiofiles
    import aiofiles.os
except ImportError:
    aiofiles = None

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None

class BackupType(Enum):
    """Tipos de backup disponíveis"""
    FULL = "full"          # Backup completo
    INCREMENTAL = "incremental"  # Backup incremental
    DIFFERENTIAL = "differential"  # Backup diferencial
    CONFIG_ONLY = "config_only"   # Apenas configurações
    DATA_ONLY = "data_only"       # Apenas dados
    LOGS_ONLY = "logs_only"       # Apenas logs

class BackupStatus(Enum):
    """Status do backup"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CompressionLevel(Enum):
    """Níveis de compressão"""
    NONE = 0
    FAST = 1
    NORMAL = 6
    BEST = 9

@dataclass
class BackupConfig:
    """Configuração de backup"""
    backup_dir: Path = field(default_factory=lambda: Path("backups"))
    max_backups: int = 10
    compression_level: CompressionLevel = CompressionLevel.NORMAL
    encrypt_backups: bool = True
    encryption_key: Optional[str] = None
    include_logs: bool = True
    include_config: bool = True
    include_data: bool = True
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.tmp", "*.log", "__pycache__", "*.pyc", ".git", "node_modules"
    ])
    auto_backup_interval: int = 24  # horas
    remote_sync_enabled: bool = False
    remote_sync_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackupInfo:
    """Informações sobre um backup"""
    id: str
    type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[Path] = None
    file_size: int = 0
    checksum: Optional[str] = None
    encrypted: bool = False
    compression_level: CompressionLevel = CompressionLevel.NORMAL
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'file_path': str(self.file_path) if self.file_path else None,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'encrypted': self.encrypted,
            'compression_level': self.compression_level.value,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        return cls(
            id=data['id'],
            type=BackupType(data['type']),
            status=BackupStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None,
            file_path=Path(data['file_path']) if data['file_path'] else None,
            file_size=data['file_size'],
            checksum=data['checksum'],
            encrypted=data['encrypted'],
            compression_level=CompressionLevel(data['compression_level']),
            error_message=data['error_message'],
            metadata=data['metadata']
        )

class BackupSystem:
    """Sistema principal de backup"""
    
    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        self.backups: Dict[str, BackupInfo] = {}
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._backup_task: Optional[asyncio.Task] = None
        self._encryption_key: Optional[bytes] = None
        
        # Criar diretório de backup
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar criptografia
        if self.config.encrypt_backups and CRYPTO_AVAILABLE:
            self._setup_encryption()
        
        # Carregar histórico de backups
        self._load_backup_history()
    
    def _setup_encryption(self):
        """Configura a criptografia para backups"""
        if self.config.encryption_key:
            # Usar chave fornecida
            key = self.config.encryption_key.encode()
            # Gerar chave Fernet a partir da chave fornecida
            key_hash = hashlib.sha256(key).digest()
            import base64
            self._encryption_key = base64.urlsafe_b64encode(key_hash[:32])
        else:
            # Gerar nova chave
            self._encryption_key = Fernet.generate_key()
            
            # Salvar chave em arquivo seguro
            key_file = self.config.backup_dir / ".backup_key"
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            
            # Definir permissões restritivas (apenas no Unix)
            if os.name != 'nt':
                os.chmod(key_file, 0o600)
    
    def _load_backup_history(self):
        """Carrega o histórico de backups"""
        history_file = self.config.backup_dir / "backup_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    for backup_data in data.get('backups', []):
                        backup_info = BackupInfo.from_dict(backup_data)
                        self.backups[backup_info.id] = backup_info
            except Exception as e:
                self.logger.error(f"Erro ao carregar histórico de backups: {e}")
    
    def _save_backup_history(self):
        """Salva o histórico de backups"""
        history_file = self.config.backup_dir / "backup_history.json"
        try:
            data = {
                'backups': [backup.to_dict() for backup in self.backups.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar histórico de backups: {e}")
    
    def _generate_backup_id(self) -> str:
        """Gera um ID único para o backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}_{os.urandom(4).hex()}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula o checksum MD5 de um arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _should_include_file(self, file_path: Path, base_path: Path) -> bool:
        """Verifica se um arquivo deve ser incluído no backup"""
        relative_path = file_path.relative_to(base_path)
        
        for pattern in self.config.exclude_patterns:
            if relative_path.match(pattern):
                return False
        
        return True
    
    def _encrypt_file(self, file_path: Path) -> Path:
        """Criptografa um arquivo"""
        if not self._encryption_key or not CRYPTO_AVAILABLE:
            return file_path
        
        fernet = Fernet(self._encryption_key)
        encrypted_path = file_path.with_suffix(file_path.suffix + '.encrypted')
        
        with open(file_path, 'rb') as infile, open(encrypted_path, 'wb') as outfile:
            data = infile.read()
            encrypted_data = fernet.encrypt(data)
            outfile.write(encrypted_data)
        
        return encrypted_path
    
    def _decrypt_file(self, encrypted_path: Path, output_path: Path):
        """Descriptografa um arquivo"""
        if not self._encryption_key or not CRYPTO_AVAILABLE:
            shutil.copy2(encrypted_path, output_path)
            return
        
        fernet = Fernet(self._encryption_key)
        
        with open(encrypted_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            encrypted_data = infile.read()
            decrypted_data = fernet.decrypt(encrypted_data)
            outfile.write(decrypted_data)
    
    async def create_backup(self, backup_type: BackupType = BackupType.FULL,
                          custom_paths: Optional[List[Path]] = None) -> BackupInfo:
        """Cria um novo backup"""
        backup_id = self._generate_backup_id()
        backup_info = BackupInfo(
            id=backup_id,
            type=backup_type,
            status=BackupStatus.PENDING,
            created_at=datetime.now(),
            compression_level=self.config.compression_level,
            encrypted=self.config.encrypt_backups and CRYPTO_AVAILABLE
        )
        
        self.backups[backup_id] = backup_info
        self.logger.info(f"Iniciando backup {backup_id} (tipo: {backup_type.value})")
        
        try:
            backup_info.status = BackupStatus.RUNNING
            
            # Determinar quais arquivos incluir
            files_to_backup = await self._collect_files_for_backup(backup_type, custom_paths)
            
            # Criar arquivo de backup
            backup_filename = f"{backup_id}.zip"
            backup_path = self.config.backup_dir / backup_filename
            
            # Criar backup comprimido
            await self._create_compressed_backup(files_to_backup, backup_path, backup_info)
            
            # Criptografar se necessário
            if backup_info.encrypted:
                encrypted_path = self._encrypt_file(backup_path)
                backup_path.unlink()  # Remover arquivo não criptografado
                backup_path = encrypted_path
            
            # Atualizar informações do backup
            backup_info.file_path = backup_path
            backup_info.file_size = backup_path.stat().st_size
            backup_info.checksum = self._calculate_checksum(backup_path)
            backup_info.completed_at = datetime.now()
            backup_info.status = BackupStatus.COMPLETED
            
            self.logger.info(f"Backup {backup_id} concluído com sucesso")
            
            # Limpar backups antigos
            await self._cleanup_old_backups()
            
            # Salvar histórico
            self._save_backup_history()
            
            return backup_info
            
        except Exception as e:
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            self.logger.error(f"Erro ao criar backup {backup_id}: {e}")
            raise
    
    async def _collect_files_for_backup(self, backup_type: BackupType,
                                      custom_paths: Optional[List[Path]] = None) -> List[Path]:
        """Coleta arquivos para backup baseado no tipo"""
        files = []
        base_dir = Path.cwd()
        
        if custom_paths:
            # Usar caminhos personalizados
            for path in custom_paths:
                if path.is_file():
                    files.append(path)
                elif path.is_dir():
                    for file_path in path.rglob('*'):
                        if file_path.is_file() and self._should_include_file(file_path, base_dir):
                            files.append(file_path)
        else:
            # Coletar baseado no tipo de backup
            if backup_type in [BackupType.FULL, BackupType.CONFIG_ONLY]:
                # Incluir arquivos de configuração
                config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '.env*']
                for pattern in config_patterns:
                    files.extend(base_dir.glob(pattern))
                
                # Incluir diretório de configuração se existir
                config_dir = base_dir / 'config'
                if config_dir.exists():
                    for file_path in config_dir.rglob('*'):
                        if file_path.is_file():
                            files.append(file_path)
            
            if backup_type in [BackupType.FULL, BackupType.DATA_ONLY]:
                # Incluir dados do bot
                data_dirs = ['data', 'database', 'storage']
                for dir_name in data_dirs:
                    data_dir = base_dir / dir_name
                    if data_dir.exists():
                        for file_path in data_dir.rglob('*'):
                            if file_path.is_file() and self._should_include_file(file_path, base_dir):
                                files.append(file_path)
                
                # Incluir código fonte
                src_dir = base_dir / 'src'
                if src_dir.exists():
                    for file_path in src_dir.rglob('*.py'):
                        if self._should_include_file(file_path, base_dir):
                            files.append(file_path)
            
            if backup_type in [BackupType.FULL, BackupType.LOGS_ONLY] and self.config.include_logs:
                # Incluir logs
                logs_dir = base_dir / 'logs'
                if logs_dir.exists():
                    for file_path in logs_dir.rglob('*.log'):
                        if self._should_include_file(file_path, base_dir):
                            files.append(file_path)
        
        # Remover duplicatas e arquivos que não existem
        unique_files = list(set(f for f in files if f.exists()))
        return unique_files
    
    async def _create_compressed_backup(self, files: List[Path], backup_path: Path,
                                      backup_info: BackupInfo):
        """Cria um backup comprimido"""
        compression = zipfile.ZIP_DEFLATED if self.config.compression_level != CompressionLevel.NONE else zipfile.ZIP_STORED
        compresslevel = self.config.compression_level.value if self.config.compression_level != CompressionLevel.NONE else None
        
        base_dir = Path.cwd()
        
        with zipfile.ZipFile(backup_path, 'w', compression=compression, compresslevel=compresslevel) as zipf:
            # Adicionar metadados do backup
            metadata = {
                'backup_id': backup_info.id,
                'backup_type': backup_info.type.value,
                'created_at': backup_info.created_at.isoformat(),
                'file_count': len(files),
                'bot_version': '2.0.0',  # Versão do bot
                'backup_system_version': '1.0.0'
            }
            
            zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Adicionar arquivos
            for file_path in files:
                try:
                    # Calcular caminho relativo
                    if file_path.is_relative_to(base_dir):
                        arcname = file_path.relative_to(base_dir)
                    else:
                        arcname = file_path.name
                    
                    zipf.write(file_path, arcname)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao adicionar arquivo {file_path} ao backup: {e}")
    
    async def _cleanup_old_backups(self):
        """Remove backups antigos baseado na configuração"""
        if self.config.max_backups <= 0:
            return
        
        # Ordenar backups por data de criação
        sorted_backups = sorted(
            [b for b in self.backups.values() if b.status == BackupStatus.COMPLETED],
            key=lambda x: x.created_at,
            reverse=True
        )
        
        # Remover backups excedentes
        backups_to_remove = sorted_backups[self.config.max_backups:]
        
        for backup in backups_to_remove:
            try:
                if backup.file_path and backup.file_path.exists():
                    backup.file_path.unlink()
                    self.logger.info(f"Backup antigo removido: {backup.id}")
                
                del self.backups[backup.id]
                
            except Exception as e:
                self.logger.error(f"Erro ao remover backup {backup.id}: {e}")
    
    async def restore_backup(self, backup_id: str, restore_path: Optional[Path] = None) -> bool:
        """Restaura um backup"""
        if backup_id not in self.backups:
            raise ValueError(f"Backup {backup_id} não encontrado")
        
        backup_info = self.backups[backup_id]
        
        if not backup_info.file_path or not backup_info.file_path.exists():
            raise FileNotFoundError(f"Arquivo de backup {backup_info.file_path} não encontrado")
        
        restore_path = restore_path or Path.cwd() / "restored"
        restore_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Iniciando restauração do backup {backup_id}")
        
        try:
            # Descriptografar se necessário
            backup_file = backup_info.file_path
            if backup_info.encrypted:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    self._decrypt_file(backup_file, tmp_path)
                    backup_file = tmp_path
            
            # Extrair backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_path)
            
            # Limpar arquivo temporário se foi criado
            if backup_info.encrypted and backup_file != backup_info.file_path:
                backup_file.unlink()
            
            self.logger.info(f"Backup {backup_id} restaurado com sucesso em {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup {backup_id}: {e}")
            return False
    
    async def _auto_backup_loop(self):
        """Loop para backups automáticos"""
        while self._running:
            try:
                # Verificar se é hora de fazer backup
                last_backup = max(
                    (b.created_at for b in self.backups.values() if b.status == BackupStatus.COMPLETED),
                    default=datetime.min
                )
                
                hours_since_last = (datetime.now() - last_backup).total_seconds() / 3600
                
                if hours_since_last >= self.config.auto_backup_interval:
                    self.logger.info("Iniciando backup automático")
                    await self.create_backup(BackupType.INCREMENTAL)
                
                # Aguardar próxima verificação (1 hora)
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de backup automático: {e}")
                await asyncio.sleep(300)  # Aguardar 5 minutos em caso de erro
    
    async def start_auto_backup(self):
        """Inicia o sistema de backup automático"""
        if self._running:
            return
        
        self._running = True
        self._backup_task = asyncio.create_task(self._auto_backup_loop())
        self.logger.info("Sistema de backup automático iniciado")
    
    async def stop_auto_backup(self):
        """Para o sistema de backup automático"""
        self._running = False
        
        if self._backup_task:
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Sistema de backup automático parado")
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Obtém informações sobre um backup"""
        return self.backups.get(backup_id)
    
    def list_backups(self, status: Optional[BackupStatus] = None) -> List[BackupInfo]:
        """Lista todos os backups"""
        backups = list(self.backups.values())
        
        if status:
            backups = [b for b in backups if b.status == status]
        
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos backups"""
        backups = list(self.backups.values())
        completed_backups = [b for b in backups if b.status == BackupStatus.COMPLETED]
        
        total_size = sum(b.file_size for b in completed_backups)
        
        return {
            'total_backups': len(backups),
            'completed_backups': len(completed_backups),
            'failed_backups': len([b for b in backups if b.status == BackupStatus.FAILED]),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_backup': min((b.created_at for b in completed_backups), default=None),
            'newest_backup': max((b.created_at for b in completed_backups), default=None),
            'auto_backup_enabled': self._running
        }

# Instância global do sistema de backup
_backup_system: Optional[BackupSystem] = None

def get_backup_system(config: Optional[BackupConfig] = None) -> BackupSystem:
    """Obtém a instância global do sistema de backup"""
    global _backup_system
    if _backup_system is None:
        _backup_system = BackupSystem(config)
    return _backup_system

# Funções de conveniência
async def create_backup(backup_type: BackupType = BackupType.FULL,
                      custom_paths: Optional[List[Path]] = None) -> BackupInfo:
    """Cria um backup"""
    return await get_backup_system().create_backup(backup_type, custom_paths)

async def restore_backup(backup_id: str, restore_path: Optional[Path] = None) -> bool:
    """Restaura um backup"""
    return await get_backup_system().restore_backup(backup_id, restore_path)

async def start_auto_backup():
    """Inicia o sistema de backup automático"""
    await get_backup_system().start_auto_backup()

async def stop_auto_backup():
    """Para o sistema de backup automático"""
    await get_backup_system().stop_auto_backup()

def list_backups(status: Optional[BackupStatus] = None) -> List[BackupInfo]:
    """Lista backups"""
    return get_backup_system().list_backups(status)

def get_backup_stats() -> Dict[str, Any]:
    """Obtém estatísticas dos backups"""
    return get_backup_system().get_backup_stats()