"""Carregador de variáveis de ambiente para o Hawk Bot."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class EnvLoader:
    """Classe para carregar e gerenciar variáveis de ambiente."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Inicializa o carregador de ambiente.
        
        Args:
            env_file: Caminho para o arquivo .env (opcional)
        """
        self.env_file = env_file or self._find_env_file()
        self.load_environment()
    
    def _find_env_file(self) -> Optional[str]:
        """Encontra o arquivo .env no projeto."""
        current_dir = Path(__file__).parent
        
        # Procura o .env subindo na hierarquia de diretórios
        for _ in range(5):  # Máximo 5 níveis acima
            env_path = current_dir / '.env'
            if env_path.exists():
                return str(env_path)
            current_dir = current_dir.parent
        
        return None
    
    def load_environment(self) -> bool:
        """Carrega as variáveis de ambiente.
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            if self.env_file and os.path.exists(self.env_file):
                load_dotenv(self.env_file)
                return True
            else:
                # Tenta carregar do ambiente atual
                load_dotenv()
                return True
        except Exception as e:
            print(f"Erro ao carregar variáveis de ambiente: {e}")
            return False
    
    @staticmethod
    def get_env(key: str, default: Any = None, required: bool = False) -> Any:
        """Obtém uma variável de ambiente.
        
        Args:
            key: Nome da variável
            default: Valor padrão se não encontrada
            required: Se True, levanta exceção se não encontrada
            
        Returns:
            Valor da variável de ambiente
            
        Raises:
            ValueError: Se a variável é obrigatória e não foi encontrada
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Variável de ambiente obrigatória não encontrada: {key}")
        
        return value
    
    @staticmethod
    def get_bool_env(key: str, default: bool = False) -> bool:
        """Obtém uma variável de ambiente como boolean.
        
        Args:
            key: Nome da variável
            default: Valor padrão
            
        Returns:
            Valor boolean da variável
        """
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_env(key: str, default: int = 0) -> int:
        """Obtém uma variável de ambiente como inteiro.
        
        Args:
            key: Nome da variável
            default: Valor padrão
            
        Returns:
            Valor inteiro da variável
        """
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def get_all_env_vars(self) -> Dict[str, str]:
        """Retorna todas as variáveis de ambiente.
        
        Returns:
            Dicionário com todas as variáveis de ambiente
        """
        return dict(os.environ)
    
    def validate_required_vars(self, required_vars: list) -> bool:
        """Valida se todas as variáveis obrigatórias estão presentes.
        
        Args:
            required_vars: Lista de variáveis obrigatórias
            
        Returns:
            True se todas estão presentes, False caso contrário
        """
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
            return False
        
        return True

# Instância global do carregador
env_loader = EnvLoader()