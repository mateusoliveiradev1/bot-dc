"""Dashboard web para visualização de métricas do Hawk Bot.

Este módulo fornece:
- Interface web para visualização de métricas
- Gráficos em tempo real
- Alertas visuais
- API REST para métricas
- Exportação de dados
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from aiohttp import web, WSMsgType
    from aiohttp.web import Application, Request, Response, WebSocketResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None
    Application = None
    Request = None
    Response = None
    WebSocketResponse = None

from .metrics import get_metrics_collector, MetricsCollector, AlertLevel

class MetricsDashboard:
    """Dashboard web para métricas"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp é necessário para o dashboard de métricas")
        
        self.host = host
        self.port = port
        self.app: Optional[Application] = None
        self.metrics_collector = get_metrics_collector()
        self.websockets: List[WebSocketResponse] = []
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
    
    def create_app(self) -> Application:
        """Cria a aplicação web"""
        app = web.Application()
        
        # Rotas da API
        app.router.add_get('/api/metrics', self.get_metrics_api)
        app.router.add_get('/api/metrics/{metric_name}', self.get_metric_api)
        app.router.add_get('/api/alerts', self.get_alerts_api)
        app.router.add_post('/api/alerts/{alert_id}/resolve', self.resolve_alert_api)
        app.router.add_get('/api/health', self.health_check_api)
        
        # WebSocket para atualizações em tempo real
        app.router.add_get('/ws', self.websocket_handler)
        
        # Rotas estáticas
        app.router.add_get('/', self.dashboard_page)
        app.router.add_get('/dashboard', self.dashboard_page)
        
        # Servir arquivos estáticos (CSS, JS)
        static_dir = Path(__file__).parent / 'static'
        if static_dir.exists():
            app.router.add_static('/static/', static_dir)
        
        return app
    
    async def get_metrics_api(self, request: Request) -> Response:
        """API endpoint para obter todas as métricas"""
        try:
            metrics = self.metrics_collector.get_all_metrics()
            return web.json_response({
                'status': 'success',
                'data': metrics,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def get_metric_api(self, request: Request) -> Response:
        """API endpoint para obter uma métrica específica"""
        try:
            metric_name = request.match_info['metric_name']
            metric = self.metrics_collector.get_metric(metric_name)
            
            if metric is None:
                return web.json_response({
                    'status': 'error',
                    'message': f'Métrica {metric_name} não encontrada'
                }, status=404)
            
            # Obter histórico
            since_param = request.query.get('since')
            since = None
            if since_param:
                try:
                    hours = int(since_param)
                    since = datetime.now() - timedelta(hours=hours)
                except ValueError:
                    pass
            
            values = metric.get_values(since)
            
            return web.json_response({
                'status': 'success',
                'data': {
                    'name': metric.name,
                    'type': metric.type.value,
                    'description': metric.description,
                    'current_value': metric.get_current_value(),
                    'values': [v.to_dict() for v in values[-100:]],  # Últimos 100 valores
                    'stats': {
                        'average': metric.get_average(since),
                        'max': metric.get_max(since),
                        'min': metric.get_min(since)
                    }
                }
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def get_alerts_api(self, request: Request) -> Response:
        """API endpoint para obter alertas"""
        try:
            resolved_param = request.query.get('resolved')
            resolved = None
            if resolved_param is not None:
                resolved = resolved_param.lower() == 'true'
            
            alerts = self.metrics_collector.get_alerts(resolved)
            
            return web.json_response({
                'status': 'success',
                'data': [alert.to_dict() for alert in alerts],
                'count': len(alerts)
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def resolve_alert_api(self, request: Request) -> Response:
        """API endpoint para resolver um alerta"""
        try:
            alert_id = int(request.match_info['alert_id'])
            alerts = self.metrics_collector.get_alerts()
            
            if alert_id >= len(alerts):
                return web.json_response({
                    'status': 'error',
                    'message': 'Alerta não encontrado'
                }, status=404)
            
            alerts[alert_id].resolved = True
            
            return web.json_response({
                'status': 'success',
                'message': 'Alerta resolvido'
            })
        except Exception as e:
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    async def health_check_api(self, request: Request) -> Response:
        """API endpoint para verificação de saúde"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics_count': len(self.metrics_collector.metrics),
            'alerts_count': len(self.metrics_collector.get_alerts(False))
        })
    
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Handler para conexões WebSocket"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.append(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'ping':
                            await ws.send_str(json.dumps({'type': 'pong'}))
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            print(f'WebSocket handler error: {e}')
        finally:
            if ws in self.websockets:
                self.websockets.remove(ws)
        
        return ws
    
    async def broadcast_metrics(self):
        """Envia métricas para todos os clientes WebSocket conectados"""
        if not self.websockets:
            return
        
        try:
            metrics = self.metrics_collector.get_all_metrics()
            alerts = [alert.to_dict() for alert in self.metrics_collector.get_alerts(False)]
            
            message = json.dumps({
                'type': 'metrics_update',
                'data': {
                    'metrics': metrics,
                    'alerts': alerts,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
            # Remover conexões fechadas
            active_websockets = []
            for ws in self.websockets:
                if ws.closed:
                    continue
                try:
                    await ws.send_str(message)
                    active_websockets.append(ws)
                except Exception:
                    pass
            
            self.websockets = active_websockets
            
        except Exception as e:
            print(f'Erro ao enviar métricas via WebSocket: {e}')
    
    async def dashboard_page(self, request: Request) -> Response:
        """Página principal do dashboard"""
        html_content = self._get_dashboard_html()
        return web.Response(text=html_content, content_type='text/html')
    
    def _get_dashboard_html(self) -> str:
        """Gera o HTML do dashboard"""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hawk Bot - Dashboard de Métricas</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .status-item {
            text-align: center;
            color: white;
        }
        
        .status-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .metric-title {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .metric-description {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        .metric-stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #888;
        }
        
        .alerts-section {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .alert-item {
            padding: 10px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background: #fee;
            border-color: #e74c3c;
        }
        
        .alert-warning {
            background: #ffeaa7;
            border-color: #fdcb6e;
        }
        
        .alert-info {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }
        
        .connected {
            background: #27ae60;
        }
        
        .disconnected {
            background: #e74c3c;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: white;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Conectando...</div>
    
    <div class="container">
        <div class="header">
            <h1>🦅 Hawk Bot Dashboard</h1>
            <p>Monitoramento de Métricas em Tempo Real</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-value" id="metricsCount">-</div>
                <div>Métricas</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="alertsCount">-</div>
                <div>Alertas Ativos</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="lastUpdate">-</div>
                <div>Última Atualização</div>
            </div>
        </div>
        
        <div class="metrics-grid" id="metricsGrid">
            <div class="loading">Carregando métricas...</div>
        </div>
        
        <div class="alerts-section">
            <h2>🚨 Alertas Ativos</h2>
            <div id="alertsList">
                <div class="loading">Carregando alertas...</div>
            </div>
        </div>
    </div>
    
    <script>
        class MetricsDashboard {
            constructor() {
                this.ws = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.reconnectDelay = 1000;
                
                this.init();
            }
            
            init() {
                this.connectWebSocket();
                this.loadInitialData();
            }
            
            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('WebSocket conectado');
                    this.updateConnectionStatus(true);
                    this.reconnectAttempts = 0;
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'metrics_update') {
                            this.updateMetrics(data.data);
                        }
                    } catch (e) {
                        console.error('Erro ao processar mensagem WebSocket:', e);
                    }
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocket desconectado');
                    this.updateConnectionStatus(false);
                    this.scheduleReconnect();
                };
                
                this.ws.onerror = (error) => {
                    console.error('Erro WebSocket:', error);
                };
            }
            
            scheduleReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        console.log(`Tentativa de reconexão ${this.reconnectAttempts}`);
                        this.connectWebSocket();
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            }
            
            updateConnectionStatus(connected) {
                const statusEl = document.getElementById('connectionStatus');
                if (connected) {
                    statusEl.textContent = 'Conectado';
                    statusEl.className = 'connection-status connected';
                } else {
                    statusEl.textContent = 'Desconectado';
                    statusEl.className = 'connection-status disconnected';
                }
            }
            
            async loadInitialData() {
                try {
                    const response = await fetch('/api/metrics');
                    const data = await response.json();
                    if (data.status === 'success') {
                        this.updateMetrics({
                            metrics: data.data,
                            alerts: [],
                            timestamp: data.timestamp
                        });
                    }
                } catch (e) {
                    console.error('Erro ao carregar dados iniciais:', e);
                }
                
                try {
                    const response = await fetch('/api/alerts');
                    const data = await response.json();
                    if (data.status === 'success') {
                        this.updateAlerts(data.data);
                    }
                } catch (e) {
                    console.error('Erro ao carregar alertas:', e);
                }
            }
            
            updateMetrics(data) {
                const { metrics, alerts, timestamp } = data;
                
                // Atualizar contadores
                document.getElementById('metricsCount').textContent = Object.keys(metrics).length;
                document.getElementById('alertsCount').textContent = alerts.length;
                document.getElementById('lastUpdate').textContent = new Date(timestamp).toLocaleTimeString();
                
                // Atualizar grid de métricas
                this.renderMetrics(metrics);
                
                // Atualizar alertas
                this.updateAlerts(alerts);
            }
            
            renderMetrics(metrics) {
                const grid = document.getElementById('metricsGrid');
                
                const html = Object.entries(metrics).map(([name, metric]) => {
                    const value = metric.current_value;
                    const formattedValue = typeof value === 'number' ? 
                        (value % 1 === 0 ? value.toString() : value.toFixed(2)) : 
                        (value || 'N/A');
                    
                    return `
                        <div class="metric-card">
                            <div class="metric-title">${name}</div>
                            <div class="metric-value">${formattedValue}</div>
                            <div class="metric-description">${metric.description || 'Sem descrição'}</div>
                            <div class="metric-stats">
                                <span>Média 1h: ${metric.average_1h ? metric.average_1h.toFixed(2) : 'N/A'}</span>
                                <span>Máx 1h: ${metric.max_1h || 'N/A'}</span>
                                <span>Mín 1h: ${metric.min_1h || 'N/A'}</span>
                            </div>
                        </div>
                    `;
                }).join('');
                
                grid.innerHTML = html || '<div class="loading">Nenhuma métrica disponível</div>';
            }
            
            updateAlerts(alerts) {
                const alertsList = document.getElementById('alertsList');
                
                if (!alerts || alerts.length === 0) {
                    alertsList.innerHTML = '<p>✅ Nenhum alerta ativo</p>';
                    return;
                }
                
                const html = alerts.map(alert => {
                    const levelClass = `alert-${alert.level}`;
                    const time = new Date(alert.timestamp).toLocaleString();
                    
                    return `
                        <div class="alert-item ${levelClass}">
                            <strong>${alert.metric_name}</strong> - ${alert.message}<br>
                            <small>Valor: ${alert.value} | Limite: ${alert.threshold} | ${time}</small>
                        </div>
                    `;
                }).join('');
                
                alertsList.innerHTML = html;
            }
        }
        
        // Inicializar dashboard quando a página carregar
        document.addEventListener('DOMContentLoaded', () => {
            new MetricsDashboard();
        });
    </script>
</body>
</html>
        """
    
    async def _update_loop(self):
        """Loop para enviar atualizações via WebSocket"""
        while self._running:
            try:
                await self.broadcast_metrics()
                await asyncio.sleep(5)  # Atualizar a cada 5 segundos
            except Exception as e:
                print(f'Erro no loop de atualização: {e}')
                await asyncio.sleep(1)
    
    async def start(self):
        """Inicia o servidor do dashboard"""
        if self._running:
            return
        
        self.app = self.create_app()
        self._running = True
        
        # Iniciar loop de atualizações
        self._update_task = asyncio.create_task(self._update_loop())
        
        # Iniciar servidor
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"Dashboard de métricas iniciado em http://{self.host}:{self.port}")
    
    async def stop(self):
        """Para o servidor do dashboard"""
        self._running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        # Fechar todas as conexões WebSocket
        for ws in self.websockets:
            if not ws.closed:
                await ws.close()
        
        self.websockets.clear()
        print("Dashboard de métricas parado")

# Instância global do dashboard
_dashboard: Optional[MetricsDashboard] = None

def get_dashboard(host: str = "localhost", port: int = 8080) -> MetricsDashboard:
    """Obtém a instância global do dashboard"""
    global _dashboard
    if _dashboard is None:
        _dashboard = MetricsDashboard(host, port)
    return _dashboard

async def start_dashboard(host: str = "localhost", port: int = 8080):
    """Inicia o dashboard de métricas"""
    if not AIOHTTP_AVAILABLE:
        print("aiohttp não está disponível. Dashboard não pode ser iniciado.")
        return
    
    dashboard = get_dashboard(host, port)
    await dashboard.start()

async def stop_dashboard():
    """Para o dashboard de métricas"""
    global _dashboard
    if _dashboard:
        await _dashboard.stop()