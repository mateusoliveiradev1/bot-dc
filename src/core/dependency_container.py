# -*- coding: utf-8 -*-
"""
Sistema de Injeção de Dependências - Hawk Bot
Gerenciamento centralizado de serviços e dependências
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar, Optional, List, Callable, get_type_hints
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque
import weakref
import time

logger = logging.getLogger('HawkBot.DependencyContainer')

T = TypeVar('T')

class ServiceLifetime(Enum):
    """Tipos de ciclo de vida dos serviços"""
    SINGLETON = "singleton"  # Uma instância por container
    TRANSIENT = "transient"  # Nova instância a cada resolução
    SCOPED = "scoped"       # Uma instância por escopo

@dataclass
class ServiceDescriptor:
    """Descritor de um serviço registrado"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: Optional[list] = None

class IService(ABC):
    """Interface base para todos os serviços"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Inicializa o serviço"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Limpa recursos do serviço"""
        pass

class DependencyContainer:
    """Container principal para injeção de dependências"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._initialization_order: List[Type] = []
        self._initialized = False
        self._lock = asyncio.Lock()
        self._startup_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None
        self._health_checks: Dict[Type, Callable] = {}
        self._service_stats: Dict[Type, Dict[str, Any]] = defaultdict(dict)
        logger.info("Container de dependências inicializado")
    
    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, 
                          factory: Optional[Callable[[], T]] = None, instance: Optional[T] = None) -> 'DependencyContainer':
        """Registra um serviço como singleton"""
        return self._register_service(service_type, implementation_type, factory, instance, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """Registra um serviço como transient"""
        return self._register_service(service_type, implementation_type, factory, None, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None,
                       factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """Registra um serviço como scoped"""
        return self._register_service(service_type, implementation_type, factory, None, ServiceLifetime.SCOPED)
    
    def _register_service(self, service_type: Type[T], implementation_type: Optional[Type[T]], 
                         factory: Optional[Callable], instance: Optional[T], 
                         lifetime: ServiceLifetime) -> 'DependencyContainer':
        """Registra um serviço no container"""
        if service_type in self._services:
            logger.warning(f"Serviço {service_type.__name__} já registrado, sobrescrevendo")
        
        # Determinar dependências automaticamente
        dependencies = self._get_dependencies(implementation_type or service_type)
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=lifetime,
            dependencies=dependencies
        )
        
        self._services[service_type] = descriptor
        logger.debug(f"Serviço registrado: {service_type.__name__} ({lifetime.value})")
        
        return self
    
    def _get_dependencies(self, service_type: Type) -> list:
        """Obtém as dependências de um serviço através de type hints"""
        try:
            import inspect
            signature = inspect.signature(service_type.__init__)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
            
            return dependencies
        except Exception as e:
            logger.debug(f"Não foi possível determinar dependências para {service_type.__name__}: {e}")
            return []
    
    async def resolve(self, service_type: Type[T], scope_id: Optional[str] = None) -> T:
        """Resolve uma instância do serviço"""
        if service_type not in self._services:
            raise ValueError(f"Serviço {service_type.__name__} não registrado")
        
        descriptor = self._services[service_type]
        
        # Singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type not in self._instances:
                self._instances[service_type] = await self._create_instance(descriptor)
            return self._instances[service_type]
        
        # Scoped
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if not scope_id:
                scope_id = "default"
            
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}
            
            if service_type not in self._scoped_instances[scope_id]:
                self._scoped_instances[scope_id][service_type] = await self._create_instance(descriptor)
            
            return self._scoped_instances[scope_id][service_type]
        
        # Transient
        else:
            return await self._create_instance(descriptor)
    
    async def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Cria uma nova instância do serviço"""
        try:
            # Se já tem uma instância registrada
            if descriptor.instance is not None:
                return descriptor.instance
            
            # Se tem uma factory
            if descriptor.factory is not None:
                if asyncio.iscoroutinefunction(descriptor.factory):
                    return await descriptor.factory()
                else:
                    return descriptor.factory()
            
            # Criar instância através do construtor
            service_class = descriptor.implementation_type or descriptor.service_type
            
            # Resolver dependências
            resolved_dependencies = []
            if descriptor.dependencies:
                for dep_type in descriptor.dependencies:
                    resolved_dep = await self.resolve(dep_type)
                    resolved_dependencies.append(resolved_dep)
            
            # Criar instância
            instance = service_class(*resolved_dependencies)
            
            # Inicializar se for um IService
            if isinstance(instance, IService):
                await instance.initialize()
            
            logger.debug(f"Instância criada: {service_class.__name__}")
            return instance
            
        except Exception as e:
            logger.error(f"Erro ao criar instância de {descriptor.service_type.__name__}: {e}")
            raise
    
    async def initialize_all(self) -> None:
        """Inicializa todos os serviços singleton na ordem correta"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:  # Double-check
                return
            
            self._startup_time = time.time()
            logger.info("Inicializando todos os serviços...")
            
            # Determinar ordem de inicialização baseada em dependências
            initialization_order = self._calculate_initialization_order()
            
            for service_type in initialization_order:
                descriptor = self._services[service_type]
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    start_time = time.time()
                    try:
                        await self.resolve(service_type)
                        
                        # Registrar estatísticas
                        init_time = (time.time() - start_time) * 1000
                        self._service_stats[service_type] = {
                            'initialization_time_ms': init_time,
                            'initialized_at': time.time(),
                            'status': 'healthy'
                        }
                        
                        logger.debug(f"Serviço inicializado: {service_type.__name__} ({init_time:.2f}ms)")
                    except Exception as e:
                        self._service_stats[service_type] = {
                            'initialization_time_ms': (time.time() - start_time) * 1000,
                            'status': 'failed',
                            'error': str(e)
                        }
                        logger.error(f"Erro ao inicializar {service_type.__name__}: {e}")
                        raise
            
            self._initialized = True
            total_time = (time.time() - self._startup_time) * 1000
            logger.info(f"Todos os serviços inicializados ({len(initialization_order)} serviços) ({total_time:.2f}ms)")
    
    def _calculate_initialization_order(self) -> list:
        """Calcula a ordem de inicialização baseada em dependências"""
        # Algoritmo de ordenação topológica simples
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_type):
            if service_type in temp_visited:
                raise ValueError(f"Dependência circular detectada envolvendo {service_type.__name__}")
            
            if service_type not in visited:
                temp_visited.add(service_type)
                
                descriptor = self._services.get(service_type)
                if descriptor and descriptor.dependencies:
                    for dep_type in descriptor.dependencies:
                        if dep_type in self._services:
                            visit(dep_type)
                
                temp_visited.remove(service_type)
                visited.add(service_type)
                order.append(service_type)
        
        for service_type in self._services.keys():
            if service_type not in visited:
                visit(service_type)
        
        return order
    
    async def cleanup(self) -> None:
        """Limpa todos os recursos dos serviços"""
        if not self._initialized:
            return
        
        async with self._lock:
            self._shutdown_time = time.time()
            logger.info("Limpando recursos dos serviços...")
            
            # Limpar singletons na ordem reversa da inicialização
            initialization_order = self._calculate_initialization_order()
            for service_type in reversed(initialization_order):
                if service_type in self._instances:
                    instance = self._instances[service_type]
                    if isinstance(instance, IService):
                        start_time = time.time()
                        try:
                            await instance.cleanup()
                            cleanup_time = (time.time() - start_time) * 1000
                            
                            # Atualizar estatísticas
                            if service_type in self._service_stats:
                                self._service_stats[service_type].update({
                                    'cleanup_time_ms': cleanup_time,
                                    'status': 'cleaned'
                                })
                            
                            logger.debug(f"Serviço limpo: {service_type.__name__} ({cleanup_time:.2f}ms)")
                        except Exception as e:
                            logger.error(f"Erro ao limpar {service_type.__name__}: {e}")
                            if service_type in self._service_stats:
                                self._service_stats[service_type]['status'] = 'cleanup_failed'
            
            # Limpar scoped instances
            for scope_instances in self._scoped_instances.values():
                for service_type, instance in scope_instances.items():
                    if isinstance(instance, IService):
                        try:
                            await instance.cleanup()
                        except Exception as e:
                            logger.error(f"Erro ao limpar scoped {service_type.__name__}: {e}")
            
            self._instances.clear()
            self._scoped_instances.clear()
            self._initialized = False
            
            total_time = (time.time() - self._shutdown_time) * 1000
            logger.info(f"Limpeza de recursos concluída ({total_time:.2f}ms)")
    
    def clear_scope(self, scope_id: str) -> None:
        """Limpa um escopo específico"""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
            logger.debug(f"Escopo '{scope_id}' limpo")
    
    def is_registered(self, service_type: Type) -> bool:
        """Verifica se um serviço está registrado"""
        return service_type in self._services
    
    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """Retorna todos os serviços registrados"""
        return self._services.copy()
    
    def get_service_info(self, service_type: Type) -> Optional[ServiceDescriptor]:
        """Obtém informações sobre um serviço registrado"""
        return self._services.get(service_type)
    
    def register_health_check(self, service_type: Type, health_check: Callable):
        """Registra um health check para um serviço"""
        self._health_checks[service_type] = health_check
    
    async def check_health(self) -> Dict[str, Any]:
        """Verifica a saúde de todos os serviços"""
        health_status = {
            'container_status': 'healthy' if self._initialized else 'not_initialized',
            'services': {},
            'startup_time': self._startup_time,
            'uptime_seconds': time.time() - self._startup_time if self._startup_time else 0
        }
        
        for service_type, instance in self._instances.items():
            service_name = service_type.__name__
            service_health = {
                'status': 'unknown',
                'stats': self._service_stats.get(service_type, {})
            }
            
            try:
                # Verificar se o serviço tem health check customizado
                if service_type in self._health_checks:
                    health_result = await self._health_checks[service_type](instance)
                    service_health['status'] = 'healthy' if health_result else 'unhealthy'
                # Verificar se o serviço implementa IService
                elif isinstance(instance, IService):
                    # Assumir que está saudável se foi inicializado sem erro
                    service_health['status'] = 'healthy'
                else:
                    service_health['status'] = 'healthy'
                    
            except Exception as e:
                service_health['status'] = 'unhealthy'
                service_health['error'] = str(e)
            
            health_status['services'][service_name] = service_health
        
        return health_status
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos serviços"""
        stats = {
            'total_services': len(self._services),
            'initialized_services': len(self._instances),
            'initialization_order': [s.__name__ for s in self._calculate_initialization_order()],
            'startup_time': self._startup_time,
            'is_initialized': self._initialized,
            'services': {}
        }
        
        for service_type, service_stats in self._service_stats.items():
            stats['services'][service_type.__name__] = service_stats
        
        return stats
    
    async def restart_service(self, service_type: Type):
        """Reinicia um serviço específico"""
        if not self._initialized:
            raise RuntimeError("Container não inicializado")
        
        async with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Serviço não registrado: {service_type.__name__}")
            
            logger.info(f"Reiniciando serviço: {service_type.__name__}")
            
            # Finalizar instância atual se existir
            if service_type in self._instances:
                instance = self._instances[service_type]
                if isinstance(instance, IService):
                    try:
                        await instance.cleanup()
                    except Exception as e:
                        logger.error(f"Erro ao finalizar serviço {service_type.__name__}: {e}")
                
                del self._instances[service_type]
            
            # Criar nova instância
            descriptor = self._services[service_type]
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                start_time = time.time()
                try:
                    instance = await self._create_instance(descriptor)
                    if isinstance(instance, IService):
                        await instance.initialize()
                    self._instances[service_type] = instance
                    
                    # Atualizar estatísticas
                    init_time = (time.time() - start_time) * 1000
                    self._service_stats[service_type].update({
                        'last_restart': time.time(),
                        'restart_time_ms': init_time,
                        'status': 'healthy'
                    })
                    
                    logger.info(f"Serviço reiniciado com sucesso: {service_type.__name__}")
                except Exception as e:
                    self._service_stats[service_type].update({
                        'status': 'restart_failed',
                        'error': str(e)
                    })
                    logger.error(f"Falha ao reiniciar serviço {service_type.__name__}: {e}")
                    raise

# Instância global do container
_container = DependencyContainer()

def get_container() -> DependencyContainer:
    """Obtém a instância global do container"""
    return _container

# Decorador para injeção automática
def inject(service_type: Type[T]) -> T:
    """Decorador para injeção automática de dependências"""
    async def resolver():
        return await _container.resolve(service_type)
    return resolver

# Context manager para escopos
class ServiceScope:
    """Context manager para gerenciar escopos de serviços"""
    
    def __init__(self, scope_id: str, container: Optional[DependencyContainer] = None):
        self.scope_id = scope_id
        self.container = container or _container
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.container.clear_scope(self.scope_id)
    
    async def resolve(self, service_type: Type[T]) -> T:
        """Resolve um serviço dentro do escopo"""
        return await self.container.resolve(service_type, self.scope_id)