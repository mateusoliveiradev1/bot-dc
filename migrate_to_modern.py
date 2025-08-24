#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Migração - Hawk Bot Legacy para Moderno
Este script ajuda na migração do bot antigo para a nova arquitetura moderna.
"""

import os
import sys
import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Adicionar src ao path para importações
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Importações opcionais - não são críticas para a migração básica
HAS_MODERN_MODULES = False
try:
    from src.core.config import get_config, validate_config
    from src.core.structured_logger import get_structured_logger, log_info, log_warning, log_error, LogCategory
    HAS_MODERN_MODULES = True
except ImportError:
    print("⚠️  Módulos modernos não encontrados, mas continuando com migração básica...")
    # Definir funções dummy para compatibilidade
    def get_config(): return None
    def validate_config(): return True
    def get_structured_logger(*args, **kwargs): return None
    def log_info(*args, **kwargs): pass
    def log_warning(*args, **kwargs): pass
    def log_error(*args, **kwargs): pass
    class LogCategory:
        SYSTEM = "system"

class MigrationManager:
    """Gerenciador de migração do bot legacy para moderno"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "migration_backup"
        self.migration_log = []
        
    def log_migration(self, message: str, level: str = "info"):
        """Registra uma mensagem de migração"""
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.migration_log.append(entry)
        
        # Também imprimir no console
        prefix = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(level, "📝")
        
        print(f"{prefix} {message}")
    
    def create_backup(self) -> bool:
        """Cria backup dos arquivos importantes antes da migração"""
        try:
            self.log_migration("Criando backup dos arquivos existentes...")
            
            # Criar diretório de backup
            self.backup_dir.mkdir(exist_ok=True)
            
            # Arquivos importantes para backup
            files_to_backup = [
                "bot.py",
                ".env",
                "data/",
                "logs/",
                "requirements.txt"
            ]
            
            for file_path in files_to_backup:
                source = self.project_root / file_path
                if source.exists():
                    if source.is_file():
                        dest = self.backup_dir / file_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        self.log_migration(f"Backup criado: {file_path}")
                    elif source.is_dir():
                        dest = self.backup_dir / file_path
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                        self.log_migration(f"Backup de diretório criado: {file_path}")
            
            self.log_migration("Backup concluído com sucesso!", "success")
            return True
            
        except Exception as e:
            self.log_migration(f"Erro ao criar backup: {e}", "error")
            return False
    
    def migrate_env_file(self) -> bool:
        """Migra o arquivo .env antigo para o novo formato"""
        try:
            old_env = self.project_root / ".env"
            new_env_example = self.project_root / ".env.example"
            
            if not old_env.exists():
                self.log_migration("Arquivo .env não encontrado. Criando novo...", "warning")
                if new_env_example.exists():
                    shutil.copy2(new_env_example, old_env)
                    self.log_migration("Arquivo .env criado a partir do exemplo")
                return True
            
            self.log_migration("Migrando configurações do .env...")
            
            # Ler configurações antigas
            old_config = {}
            with open(old_env, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        old_config[key.strip()] = value.strip()
            
            # Mapeamento de configurações antigas para novas
            config_mapping = {
                'DISCORD_TOKEN': 'DISCORD_BOT_TOKEN',
                'BOT_PREFIX': 'DISCORD_COMMAND_PREFIX',
                'DB_HOST': 'DATABASE_POSTGRESQL_HOST',
                'DB_NAME': 'DATABASE_POSTGRESQL_DATABASE',
                'DB_USER': 'DATABASE_POSTGRESQL_USERNAME',
                'DB_PASSWORD': 'DATABASE_POSTGRESQL_PASSWORD',
                'DB_PORT': 'DATABASE_POSTGRESQL_PORT',
                'PUBG_API_KEY': 'API_PUBG_API_KEY',
                'MEDAL_API_KEY': 'API_MEDAL_API_KEY',
                'LOG_LEVEL': 'LOGGING_LEVEL',
                'DEBUG': 'DEBUG_ENABLE_DEBUG_MODE'
            }
            
            # Criar novo arquivo .env
            new_config_lines = []
            
            # Ler template do .env.example
            if new_env_example.exists():
                with open(new_env_example, 'r', encoding='utf-8') as f:
                    template_lines = f.readlines()
                
                for line in template_lines:
                    line = line.rstrip()
                    if '=' in line and not line.startswith('#'):
                        key = line.split('=')[0].strip()
                        
                        # Verificar se temos valor migrado
                        old_key = None
                        for old_k, new_k in config_mapping.items():
                            if new_k == key:
                                old_key = old_k
                                break
                        
                        if old_key and old_key in old_config:
                            new_config_lines.append(f"{key}={old_config[old_key]}")
                            self.log_migration(f"Migrado: {old_key} -> {key}")
                        else:
                            new_config_lines.append(line)
                    else:
                        new_config_lines.append(line)
            
            # Salvar novo .env
            with open(old_env, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_config_lines))
            
            self.log_migration("Migração do .env concluída!", "success")
            return True
            
        except Exception as e:
            self.log_migration(f"Erro ao migrar .env: {e}", "error")
            return False
    
    def check_dependencies(self) -> bool:
        """Verifica se todas as dependências estão instaladas"""
        try:
            self.log_migration("Verificando dependências...")
            
            # Lista de módulos críticos
            critical_modules = [
                'discord',
                'pydantic',
                'aiohttp',
                'asyncpg',
                'psutil'
            ]
            
            missing_modules = []
            
            for module in critical_modules:
                try:
                    __import__(module)
                    self.log_migration(f"✓ {module}")
                except ImportError:
                    missing_modules.append(module)
                    self.log_migration(f"✗ {module} - FALTANDO", "warning")
            
            if missing_modules:
                self.log_migration(f"Módulos faltando: {', '.join(missing_modules)}", "warning")
                self.log_migration("Execute: pip install -r requirements.txt", "warning")
                return False
            
            self.log_migration("Todas as dependências estão instaladas!", "success")
            return True
            
        except Exception as e:
            self.log_migration(f"Erro ao verificar dependências: {e}", "error")
            return False
    
    def create_directories(self) -> bool:
        """Cria diretórios necessários para o bot moderno"""
        try:
            self.log_migration("Criando diretórios necessários...")
            
            directories = [
                "data",
                "logs", 
                "cache",
                "backups",
                "temp"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                self.log_migration(f"Diretório criado/verificado: {directory}")
            
            self.log_migration("Diretórios criados com sucesso!", "success")
            return True
            
        except Exception as e:
            self.log_migration(f"Erro ao criar diretórios: {e}", "error")
            return False
    
    async def test_modern_bot(self) -> bool:
        """Testa se o bot moderno pode ser inicializado"""
        try:
            if not HAS_MODERN_MODULES:
                self.log_migration("Pulando teste do bot moderno - módulos não disponíveis", "warning")
                return True
                
            self.log_migration("Testando inicialização do bot moderno...")
            
            # Tentar importar e validar configuração
            config = get_config()
            is_valid, errors = validate_config()
            
            if not is_valid:
                self.log_migration("Erros de configuração encontrados:", "error")
                for error in errors:
                    self.log_migration(f"  - {error}", "error")
                return False
            
            self.log_migration("Configuração validada com sucesso!", "success")
            
            # Tentar inicializar logger estruturado
            logger = get_structured_logger()
            await logger.initialize()
            
            self.log_migration("Logger estruturado inicializado!", "success")
            
            # Limpar logger
            await logger.cleanup()
            
            self.log_migration("Teste do bot moderno concluído com sucesso!", "success")
            return True
            
        except Exception as e:
            self.log_migration(f"Erro no teste do bot moderno: {e}", "error")
            return False
    
    def generate_migration_report(self) -> str:
        """Gera relatório da migração"""
        report_path = self.project_root / "migration_report.json"
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "backup_location": str(self.backup_dir),
            "log": self.migration_log,
            "summary": {
                "total_steps": len(self.migration_log),
                "errors": len([l for l in self.migration_log if l["level"] == "error"]),
                "warnings": len([l for l in self.migration_log if l["level"] == "warning"]),
                "success": len([l for l in self.migration_log if l["level"] == "success"])
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return str(report_path)
    
    async def run_migration(self) -> bool:
        """Executa o processo completo de migração"""
        self.log_migration("Iniciando migracao para Hawk Bot Moderno...", "info")
        
        steps = [
            ("Criar backup", self.create_backup),
            ("Verificar dependências", self.check_dependencies),
            ("Migrar arquivo .env", self.migrate_env_file),
            ("Criar diretórios", self.create_directories),
            ("Testar bot moderno", self.test_modern_bot)
        ]
        
        success = True
        
        for step_name, step_func in steps:
            self.log_migration(f"\nExecutando: {step_name}")
            
            try:
                if asyncio.iscoroutinefunction(step_func):
                    result = await step_func()
                else:
                    result = step_func()
                
                if not result:
                    self.log_migration(f"Falha em: {step_name}", "error")
                    success = False
                    break
                else:
                    self.log_migration(f"Concluido: {step_name}", "success")
                    
            except Exception as e:
                self.log_migration(f"Erro em {step_name}: {e}", "error")
                success = False
                break
        
        # Gerar relatório
        report_path = self.generate_migration_report()
        
        if success:
            self.log_migration("\nMigracao concluida com sucesso!", "success")
            self.log_migration("\nProximos passos:")
            self.log_migration("1. Revise o arquivo .env com suas configurações")
            self.log_migration("2. Execute: python -m src.core.modern_bot")
            self.log_migration("3. Teste todas as funcionalidades")
            self.log_migration(f"\nRelatorio salvo em: {report_path}")
        else:
            self.log_migration("\nMigracao falhou. Verifique os erros acima.", "error")
            self.log_migration(f"Relatorio de erro salvo em: {report_path}")
        
        return success

async def main():
    """Função principal"""
    print("🦅 Hawk Bot - Script de Migração para Versão Moderna")
    print("=" * 60)
    
    migration = MigrationManager()
    
    # Confirmar migração
    response = input("\n❓ Deseja continuar com a migração? (s/N): ").lower().strip()
    if response not in ['s', 'sim', 'y', 'yes']:
        print("❌ Migração cancelada pelo usuário.")
        return
    
    # Executar migração
    success = await migration.run_migration()
    
    if success:
        print("\n🎉 Migração concluída! O Hawk Bot está pronto para a nova era.")
    else:
        print("\n❌ Migração falhou. Verifique os logs e tente novamente.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Migração interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal durante migração: {e}")
        sys.exit(1)