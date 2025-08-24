"""Sistema de métricas e monitoramento para o Hawk Bot.

Este módulo fornece funcionalidades para:
- Coleta de métricas de performance
- Monitoramento de recursos do sistema
- Alertas automáticos
- Dashboards de métricas
- Exportação para sistemas externos
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import logging
from pathlib import Path

try:
    import aiofiles
except ImportError:
    aiofiles = None

class MetricType(Enum):
    """Tipos de métricas disponíveis"""
    COUNTER = "counter"  # Valor que só aumenta
    GAUGE = "gauge"      # Valor que pode aumentar/diminuir
    HISTOGRAM = "histogram"  # Distribuição de valores
    TIMER = "timer"      # Medição de tempo
    RATE = "rate"        # Taxa por segundo

class AlertLevel(Enum):
    """Níveis de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricValue:
    """Representa um valor de métrica com timestamp"""
    value: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }

@dataclass
class Alert:
    """Representa um alerta do sistema"""
    metric_name: str
    level: AlertLevel
    message: str
    value: Union[int, float]
    threshold: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_name': self.metric_name,
            'level': self.level.value,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }

class Metric:
    """Classe base para métricas"""
    
    def __init__(self, name: str, metric_type: MetricType, description: str = "",
                 tags: Optional[Dict[str, str]] = None):
        self.name = name
        self.type = metric_type
        self.description = description
        self.tags = tags or {}
        self.values: deque = deque(maxlen=1000)  # Manter últimos 1000 valores
        self._lock = threading.Lock()
    
    def add_value(self, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Adiciona um valor à métrica"""
        with self._lock:
            metric_tags = {**self.tags, **(tags or {})}
            self.values.append(MetricValue(value, datetime.now(), metric_tags))
    
    def get_current_value(self) -> Optional[Union[int, float]]:
        """Retorna o valor mais recente"""
        with self._lock:
            return self.values[-1].value if self.values else None
    
    def get_values(self, since: Optional[datetime] = None) -> List[MetricValue]:
        """Retorna valores desde um timestamp específico"""
        with self._lock:
            if since is None:
                return list(self.values)
            return [v for v in self.values if v.timestamp >= since]
    
    def get_average(self, since: Optional[datetime] = None) -> Optional[float]:
        """Calcula a média dos valores"""
        values = self.get_values(since)
        if not values:
            return None
        return sum(v.value for v in values) / len(values)
    
    def get_max(self, since: Optional[datetime] = None) -> Optional[Union[int, float]]:
        """Retorna o valor máximo"""
        values = self.get_values(since)
        if not values:
            return None
        return max(v.value for v in values)
    
    def get_min(self, since: Optional[datetime] = None) -> Optional[Union[int, float]]:
        """Retorna o valor mínimo"""
        values = self.get_values(since)
        if not values:
            return None
        return min(v.value for v in values)

class Counter(Metric):
    """Métrica de contador (só aumenta)"""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        super().__init__(name, MetricType.COUNTER, description, tags)
        self._count = 0
    
    def increment(self, amount: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None):
        """Incrementa o contador"""
        self._count += amount
        self.add_value(self._count, tags)
    
    def get_count(self) -> Union[int, float]:
        """Retorna o valor atual do contador"""
        return self._count

class Gauge(Metric):
    """Métrica de gauge (pode aumentar/diminuir)"""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        super().__init__(name, MetricType.GAUGE, description, tags)
    
    def set(self, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Define o valor do gauge"""
        self.add_value(value, tags)
    
    def increment(self, amount: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None):
        """Incrementa o gauge"""
        current = self.get_current_value() or 0
        self.set(current + amount, tags)
    
    def decrement(self, amount: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None):
        """Decrementa o gauge"""
        current = self.get_current_value() or 0
        self.set(current - amount, tags)

class Timer:
    """Context manager para medir tempo de execução"""
    
    def __init__(self, metric: Metric, tags: Optional[Dict[str, str]] = None):
        self.metric = metric
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.metric.add_value(duration, self.tags)

class MetricsCollector:
    """Coletor principal de métricas"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.collectors: List[Callable] = []
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def register_metric(self, metric: Metric) -> Metric:
        """Registra uma nova métrica"""
        with self._lock:
            self.metrics[metric.name] = metric
        return metric
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Obtém uma métrica pelo nome"""
        return self.metrics.get(name)
    
    def create_counter(self, name: str, description: str = "", 
                     tags: Optional[Dict[str, str]] = None) -> Counter:
        """Cria e registra um contador"""
        counter = Counter(name, description, tags)
        return self.register_metric(counter)
    
    def create_gauge(self, name: str, description: str = "",
                    tags: Optional[Dict[str, str]] = None) -> Gauge:
        """Cria e registra um gauge"""
        gauge = Gauge(name, description, tags)
        return self.register_metric(gauge)
    
    def create_timer(self, name: str, description: str = "",
                    tags: Optional[Dict[str, str]] = None) -> Metric:
        """Cria uma métrica de timer"""
        timer_metric = Metric(name, MetricType.TIMER, description, tags)
        return self.register_metric(timer_metric)
    
    def time_function(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """Decorador para medir tempo de execução de funções"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                metric = self.get_metric(metric_name)
                if metric is None:
                    metric = self.create_timer(metric_name, f"Timer for {func.__name__}")
                
                with Timer(metric, tags):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def add_alert_rule(self, metric_name: str, threshold: Union[int, float],
                      condition: str = ">", level: AlertLevel = AlertLevel.WARNING,
                      message: Optional[str] = None):
        """Adiciona uma regra de alerta"""
        self.alert_rules[metric_name] = {
            'threshold': threshold,
            'condition': condition,
            'level': level,
            'message': message or f"{metric_name} {condition} {threshold}"
        }
    
    def check_alerts(self):
        """Verifica se alguma métrica acionou um alerta"""
        for metric_name, rule in self.alert_rules.items():
            metric = self.get_metric(metric_name)
            if metric is None:
                continue
            
            current_value = metric.get_current_value()
            if current_value is None:
                continue
            
            threshold = rule['threshold']
            condition = rule['condition']
            
            triggered = False
            if condition == ">" and current_value > threshold:
                triggered = True
            elif condition == "<" and current_value < threshold:
                triggered = True
            elif condition == ">=" and current_value >= threshold:
                triggered = True
            elif condition == "<=" and current_value <= threshold:
                triggered = True
            elif condition == "==" and current_value == threshold:
                triggered = True
            
            if triggered:
                alert = Alert(
                    metric_name=metric_name,
                    level=rule['level'],
                    message=rule['message'],
                    value=current_value,
                    threshold=threshold
                )
                self.alerts.append(alert)
                self.logger.warning(f"Alert triggered: {alert.message}")
    
    def add_collector(self, collector_func: Callable):
        """Adiciona uma função coletora personalizada"""
        self.collectors.append(collector_func)
    
    async def collect_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_metric = self.get_metric("system.cpu.percent")
            if cpu_metric is None:
                cpu_metric = self.create_gauge("system.cpu.percent", "CPU usage percentage")
            cpu_metric.set(cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_metric = self.get_metric("system.memory.percent")
            if memory_metric is None:
                memory_metric = self.create_gauge("system.memory.percent", "Memory usage percentage")
            memory_metric.set(memory.percent)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_metric = self.get_metric("system.disk.percent")
            if disk_metric is None:
                disk_metric = self.create_gauge("system.disk.percent", "Disk usage percentage")
            disk_metric.set((disk.used / disk.total) * 100)
            
            # Rede
            network = psutil.net_io_counters()
            if hasattr(self, '_last_network_stats'):
                bytes_sent_rate = network.bytes_sent - self._last_network_stats.bytes_sent
                bytes_recv_rate = network.bytes_recv - self._last_network_stats.bytes_recv
                
                sent_metric = self.get_metric("system.network.bytes_sent_rate")
                if sent_metric is None:
                    sent_metric = self.create_gauge("system.network.bytes_sent_rate", "Network bytes sent per second")
                sent_metric.set(bytes_sent_rate)
                
                recv_metric = self.get_metric("system.network.bytes_recv_rate")
                if recv_metric is None:
                    recv_metric = self.create_gauge("system.network.bytes_recv_rate", "Network bytes received per second")
                recv_metric.set(bytes_recv_rate)
            
            self._last_network_stats = network
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas do sistema: {e}")
    
    async def _collection_loop(self):
        """Loop principal de coleta de métricas"""
        while self._running:
            try:
                # Coletar métricas do sistema
                await self.collect_system_metrics()
                
                # Executar coletores personalizados
                for collector in self.collectors:
                    try:
                        if asyncio.iscoroutinefunction(collector):
                            await collector()
                        else:
                            collector()
                    except Exception as e:
                        self.logger.error(f"Erro no coletor personalizado: {e}")
                
                # Verificar alertas
                self.check_alerts()
                
                # Aguardar próxima coleta
                await asyncio.sleep(10)  # Coletar a cada 10 segundos
                
            except Exception as e:
                self.logger.error(f"Erro no loop de coleta: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Inicia a coleta de métricas"""
        if self._running:
            return
        
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Sistema de métricas iniciado")
    
    async def stop(self):
        """Para a coleta de métricas"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Sistema de métricas parado")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todas as métricas em formato de dicionário"""
        result = {}
        for name, metric in self.metrics.items():
            current_value = metric.get_current_value()
            result[name] = {
                'type': metric.type.value,
                'description': metric.description,
                'current_value': current_value,
                'tags': metric.tags,
                'average_1h': metric.get_average(datetime.now() - timedelta(hours=1)),
                'max_1h': metric.get_max(datetime.now() - timedelta(hours=1)),
                'min_1h': metric.get_min(datetime.now() - timedelta(hours=1))
            }
        return result
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Alert]:
        """Retorna alertas filtrados por status"""
        if resolved is None:
            return self.alerts
        return [alert for alert in self.alerts if alert.resolved == resolved]
    
    async def export_metrics(self, file_path: str):
        """Exporta métricas para arquivo JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.get_all_metrics(),
            'alerts': [alert.to_dict() for alert in self.alerts]
        }
        
        if aiofiles:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        else:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

# Instância global do coletor de métricas
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Obtém a instância global do coletor de métricas"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

# Funções de conveniência
def create_counter(name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> Counter:
    """Cria um contador"""
    return get_metrics_collector().create_counter(name, description, tags)

def create_gauge(name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> Gauge:
    """Cria um gauge"""
    return get_metrics_collector().create_gauge(name, description, tags)

def create_timer(name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> Metric:
    """Cria um timer"""
    return get_metrics_collector().create_timer(name, description, tags)

def time_function(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorador para medir tempo de execução"""
    return get_metrics_collector().time_function(metric_name, tags)

def add_alert_rule(metric_name: str, threshold: Union[int, float], 
                  condition: str = ">", level: AlertLevel = AlertLevel.WARNING,
                  message: Optional[str] = None):
    """Adiciona uma regra de alerta"""
    get_metrics_collector().add_alert_rule(metric_name, threshold, condition, level, message)

async def start_metrics_collection():
    """Inicia a coleta de métricas"""
    await get_metrics_collector().start()

async def stop_metrics_collection():
    """Para a coleta de métricas"""
    await get_metrics_collector().stop()

# Configurar alertas padrão
def setup_default_alerts():
    """Configura alertas padrão do sistema"""
    add_alert_rule("system.cpu.percent", 80, ">", AlertLevel.WARNING, "CPU usage above 80%")
    add_alert_rule("system.cpu.percent", 95, ">", AlertLevel.CRITICAL, "CPU usage above 95%")
    add_alert_rule("system.memory.percent", 85, ">", AlertLevel.WARNING, "Memory usage above 85%")
    add_alert_rule("system.memory.percent", 95, ">", AlertLevel.CRITICAL, "Memory usage above 95%")
    add_alert_rule("system.disk.percent", 90, ">", AlertLevel.WARNING, "Disk usage above 90%")
    add_alert_rule("system.disk.percent", 98, ">", AlertLevel.CRITICAL, "Disk usage above 98%")