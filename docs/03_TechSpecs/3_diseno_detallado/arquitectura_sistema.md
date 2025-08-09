# Diseño Detallado - Arquitectura del Sistema DevHub

## 1. Vista de Arquitectura General

### 1.1 Arquitectura de Alto Nivel
```
DevHub System Architecture (3-Tier + Agent Layer):

┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  CLI Interface        │  Web Dashboard MVP    │  Future: IDE    │
│  (devhub_cli.py)     │  (Next.js/React)     │  Plugins        │
│                      │                       │                 │
│  • Project creation  │  • Real-time metrics  │  • Context      │
│  • Structure valid.  │  • Agent monitoring   │    integration  │
│  • Blueprint eval.   │  • Document status    │  • IntelliSense │
│  • Agent execution   │  • Visual reports     │  • Debugging    │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  BlueprintAgent      │  DevAgent            │  QAAgent         │
│                      │                      │                  │
│  • Blueprint         │  • Task execution    │  • Quality       │
│    custodianship     │  • Status updates    │    validation    │
│  • Change processing │  • Backlog progress  │  • Test          │
│  • Version control   │  • Auto-proposals    │    execution     │
│                      │                      │  • Acceptance    │
│                      │                      │    criteria      │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│          DAS Enforcer              │      PMS Core               │
│       (das/enforcer.py)            │   (pms/pms_core.py)         │
│                                    │                             │
│  • Permission validation           │  • Memory persistence       │
│  • Agent orchestration             │  • Integrity validation     │
│  • Access control enforcement      │  • Atomic transactions      │
│  • Audit logging                   │  • SHA-1 checksums         │
│  • Filesystem protection           │  • Rollback capability      │
│  • Multi-agent coordination        │  • Schema validation        │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  Document Storage    │  Configuration     │  Audit & Logging   │
│                      │                    │                     │
│  • Blueprint (YAML)  │  • Agent configs   │  • Operation logs   │
│  • Project Charter   │  • Memory index    │  • Access attempts  │
│  • TechSpecs         │  • Templates       │  • Error tracking   │
│  • Backlog phases    │  • Weights/Rules   │  • Performance     │
│  • Project status    │  • Schemas         │    metrics          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Principios Arquitectónicos

#### Separation of Concerns
- **Presentation**: UI/UX sin lógica de negocio
- **Agent**: Lógica específica de dominio por agente
- **Service**: Orquestación y enforcement de reglas
- **Data**: Persistencia y integridad únicamente

#### Dependency Inversion
```python
# Correcto: Service layer no depende de detalles de implementación
class DASEnforcer:
    def __init__(self, pms_interface: PMSInterface):
        self.pms = pms_interface  # Abstraction, not implementation

# Incorrecto: Dependencia directa de implementación concreta
class DASEnforcer:
    def __init__(self):
        self.pms = PMSCore()  # Tight coupling
```

#### Single Responsibility
- **PMS**: Solo persistencia y integridad
- **DAS**: Solo orquestación y permisos
- **Agents**: Solo lógica específica del dominio

## 2. Patrones de Diseño Implementados

### 2.1 Strategy Pattern (Agent Execution)
```python
class AgentStrategy(ABC):
    """Strategy pattern para diferentes tipos de agentes"""
    
    @abstractmethod
    def execute_task(self, task: Task) -> ExecutionResult:
        pass
    
    @abstractmethod
    def validate_permissions(self, operation: str) -> bool:
        pass

class BlueprintAgentStrategy(AgentStrategy):
    """Estrategia específica para BlueprintAgent"""
    
    def execute_task(self, task: Task) -> ExecutionResult:
        if task.type == "blueprint.update":
            return self._update_blueprint(task)
        elif task.type == "blueprint.evaluate":
            return self._evaluate_blueprint(task)
        else:
            raise UnsupportedTaskError(f"Task {task.type} not supported")

class DevAgentStrategy(AgentStrategy):
    """Estrategia específica para DevAgent"""
    
    def execute_task(self, task: Task) -> ExecutionResult:
        if task.type == "backlog.update":
            return self._update_backlog(task)
        elif task.type == "task.complete":
            return self._complete_task(task)
        else:
            raise UnsupportedTaskError(f"Task {task.type} not supported")
```

### 2.2 Command Pattern (Agent Operations)
```python
class AgentCommand(ABC):
    """Command pattern para operaciones de agentes"""
    
    def __init__(self, agent_name: str, enforcer: DASEnforcer):
        self.agent_name = agent_name
        self.enforcer = enforcer
        self.timestamp = datetime.now()
    
    @abstractmethod
    def execute(self) -> CommandResult:
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        pass

class LoadCommand(AgentCommand):
    """Comando para operaciones de carga"""
    
    def __init__(self, agent_name: str, scope: str, enforcer: DASEnforcer):
        super().__init__(agent_name, enforcer)
        self.scope = scope
    
    def execute(self) -> CommandResult:
        # Validar permisos
        is_allowed, reason = self.enforcer.validate_read_permission(
            self.agent_name, self.scope
        )
        
        if not is_allowed:
            raise PermissionError(reason)
        
        # Ejecutar operación
        data = self.enforcer.pms.load(self.scope)
        
        # Log operación
        self.enforcer.audit_logger.log_access_attempt(
            self.agent_name, self.scope, "read", True
        )
        
        return CommandResult(success=True, data=data)
    
    def undo(self) -> bool:
        # Load operations no requieren undo
        return True

class SaveCommand(AgentCommand):
    """Comando para operaciones de guardado"""
    
    def __init__(self, agent_name: str, scope: str, data: dict, enforcer: DASEnforcer):
        super().__init__(agent_name, enforcer)
        self.scope = scope
        self.data = data
        self.backup_data = None
    
    def execute(self) -> CommandResult:
        # Validar permisos
        is_allowed, reason = self.enforcer.validate_write_permission(
            self.agent_name, self.scope
        )
        
        if not is_allowed:
            raise PermissionError(reason)
        
        # Crear backup antes de modificar
        try:
            self.backup_data = self.enforcer.pms.load(self.scope)
        except Exception:
            self.backup_data = None
        
        # Ejecutar operación con transacción
        transaction_id = self.enforcer.pms.begin_transaction(self.scope)
        
        try:
            success = self.enforcer.pms.save(self.scope, self.data)
            self.enforcer.pms.commit_transaction(transaction_id)
            
            # Log éxito
            self.enforcer.audit_logger.log_access_attempt(
                self.agent_name, self.scope, "write", True
            )
            
            return CommandResult(success=True, data=self.data)
            
        except Exception as e:
            # Auto-rollback en caso de error
            self.enforcer.pms.rollback_transaction(transaction_id)
            
            # Log fallo
            self.enforcer.audit_logger.log_access_attempt(
                self.agent_name, self.scope, "write", False, str(e)
            )
            
            raise
    
    def undo(self) -> bool:
        """Restaura estado anterior"""
        if self.backup_data is not None:
            return self.enforcer.pms.save(self.scope, self.backup_data)
        return True
```

### 2.3 Observer Pattern (Event System)
```python
class EventPublisher:
    """Publisher para eventos del sistema"""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
    
    def subscribe(self, event_type: str, callback: Callable):
        """Registra callback para tipo de evento"""
        self._subscribers[event_type].append(callback)
    
    def publish(self, event: SystemEvent):
        """Publica evento a todos los subscribers"""
        for callback in self._subscribers[event.type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

class SystemEvent:
    """Evento base del sistema"""
    
    def __init__(self, event_type: str, source: str, data: dict = None):
        self.type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = datetime.now()
        self.id = str(uuid.uuid4())

# Event types definidos
class EventTypes:
    BLUEPRINT_UPDATED = "blueprint.updated"
    TASK_COMPLETED = "task.completed" 
    SYNC_REQUIRED = "sync.required"
    INTEGRITY_VIOLATION = "integrity.violation"
    PERMISSION_DENIED = "permission.denied"

# Ejemplo de uso
event_publisher = EventPublisher()

# Subscriber para sync automático
def handle_blueprint_update(event: SystemEvent):
    """Trigger sync cuando blueprint se actualiza"""
    sync_service = DocumentSyncService()
    sync_service.sync_blueprint_to_yaml()

event_publisher.subscribe(EventTypes.BLUEPRINT_UPDATED, handle_blueprint_update)

# Publisher desde DAS Enforcer
def agent_save(agent_name: str, scope: str, data: dict) -> bool:
    # ... lógica de guardado ...
    
    # Publicar evento
    if scope == "blueprint":
        event = SystemEvent(
            EventTypes.BLUEPRINT_UPDATED,
            source=agent_name,
            data={"scope": scope, "agent": agent_name}
        )
        event_publisher.publish(event)
    
    return True
```

### 2.4 Factory Pattern (Agent Creation)
```python
class AgentFactory:
    """Factory para creación de agentes"""
    
    _strategies = {
        'BlueprintAgent': BlueprintAgentStrategy,
        'DevAgent': DevAgentStrategy,
        'QAAgent': QAAgentStrategy,
        'AiProjectManager': ProjectManagerAgentStrategy
    }
    
    @classmethod
    def create_agent(cls, agent_name: str, config: dict, enforcer: DASEnforcer) -> AgentStrategy:
        """Crea instancia de agente basado en configuración"""
        
        if agent_name not in cls._strategies:
            raise ValueError(f"Unknown agent type: {agent_name}")
        
        strategy_class = cls._strategies[agent_name]
        
        # Validar configuración
        cls._validate_agent_config(agent_name, config)
        
        # Crear instancia con dependencias inyectadas
        return strategy_class(
            name=agent_name,
            config=config,
            enforcer=enforcer,
            event_publisher=event_publisher
        )
    
    @classmethod
    def register_agent_type(cls, agent_name: str, strategy_class: Type[AgentStrategy]):
        """Permite registro dinámico de nuevos tipos de agente"""
        cls._strategies[agent_name] = strategy_class
    
    @staticmethod
    def _validate_agent_config(agent_name: str, config: dict):
        """Valida configuración mínima del agente"""
        required_fields = ['agente.nombre', 'pms_scopes.read', 'pms_scopes.write']
        
        for field in required_fields:
            keys = field.split('.')
            current = config
            
            for key in keys:
                if key not in current:
                    raise ValueError(f"Missing required config field: {field}")
                current = current[key]
```

## 3. Comunicación Entre Componentes

### 3.1 API Contracts
```python
# Interface contracts entre componentes principales

class PMSInterface(ABC):
    """Contract para Persistent Memory System"""
    
    @abstractmethod
    def load(self, scope: str) -> dict:
        """Carga datos desde scope con validación de integridad"""
        pass
    
    @abstractmethod  
    def save(self, scope: str, data: dict) -> bool:
        """Guarda datos con transacción atómica"""
        pass
    
    @abstractmethod
    def rollback(self, scope: str, version: str) -> bool:
        """Revierte a versión anterior"""
        pass

class DASInterface(ABC):
    """Contract para DevAgent System"""
    
    @abstractmethod
    def agent_load(self, agent_name: str, scope: str) -> dict:
        """Load con enforcement de permisos automático"""
        pass
    
    @abstractmethod
    def agent_save(self, agent_name: str, scope: str, data: dict) -> bool:
        """Save con enforcement de permisos automático"""
        pass
    
    @abstractmethod
    def validate_agent_config(self, agent_name: str) -> dict:
        """Valida y retorna configuración de agente"""
        pass

class AgentInterface(ABC):
    """Contract base para todos los agentes"""
    
    @abstractmethod
    def execute_task(self, task: str, **kwargs) -> ExecutionResult:
        """Ejecuta tarea específica del agente"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Retorna lista de capacidades del agente"""
        pass
```

### 3.2 Message Flow Patterns

#### Synchronous Request-Response
```python
# CLI -> DAS -> PMS (Synchronous)
def cli_evaluate_blueprint(project_path: str) -> EvaluationReport:
    """Flujo sincrónico: CLI solicita evaluación"""
    
    # 1. CLI instantia evaluator
    evaluator = BlueprintEvaluator(project_path)
    
    # 2. Evaluator usa DAS para acceso controlado
    das = DASEnforcer(project_path)
    
    try:
        # 3. DAS valida permisos y delega a PMS
        blueprint_data = das.agent_load("system", "blueprint")
        charter_data = das.agent_load("system", "project_charter")
        
        # 4. Evaluator procesa datos
        score, breakdown = evaluator.evaluate(charter_data, blueprint_data)
        
        # 5. Retorna resultado sincrónico
        return EvaluationReport(
            score=score,
            breakdown=breakdown,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Blueprint evaluation failed: {e}")
        raise
```

#### Event-Driven Asynchronous
```python
# Agent -> Event Publisher -> Subscribers (Asynchronous)
class BlueprintAgent:
    def update_blueprint(self, changes: dict) -> bool:
        """Flujo asíncrono: Agent actualiza blueprint"""
        
        try:
            # 1. Agent actualiza blueprint via DAS
            success = self.das.agent_save("BlueprintAgent", "blueprint", changes)
            
            if success:
                # 2. Publica evento para procesamiento asíncrono
                event = SystemEvent(
                    EventTypes.BLUEPRINT_UPDATED,
                    source="BlueprintAgent",
                    data={
                        "changes": changes,
                        "version": changes.get("version"),
                        "scope": "blueprint"
                    }
                )
                
                self.event_publisher.publish(event)
                
            return success
            
        except Exception as e:
            logger.error(f"Blueprint update failed: {e}")
            return False

# Subscribers procesan evento asíncronamente
def sync_blueprint_to_modular(event: SystemEvent):
    """Subscriber: Sincroniza blueprint.yaml -> estructura modular"""
    sync_service = BlueprintSyncService()
    sync_service.sync_yaml_to_modular_structure()

def update_project_metrics(event: SystemEvent):
    """Subscriber: Actualiza métricas del proyecto"""
    metrics_service = ProjectMetricsService()
    metrics_service.update_blueprint_metrics(event.data)

def notify_stakeholders(event: SystemEvent):
    """Subscriber: Notifica cambios importantes"""
    notification_service = NotificationService()
    notification_service.send_blueprint_update_notification(event)
```

### 3.3 Error Propagation Strategy

#### Graceful Degradation Chain
```python
class ErrorPropagationHandler:
    """Maneja propagación de errores con degradación gradual"""
    
    def handle_pms_error(self, error: PMSError, operation: str) -> bool:
        """Maneja errores de PMS con fallbacks"""
        
        if isinstance(error, IntegrityError):
            # Error crítico: propagar inmediatamente
            logger.critical(f"Data integrity compromised: {error}")
            return False
            
        elif isinstance(error, ScopeNotFoundError):
            # Error recoverable: crear scope con defaults
            logger.warning(f"Scope not found, creating default: {error}")
            return self._create_default_scope(operation)
            
        elif isinstance(error, ParseError):
            # Error de formato: intentar reparación automática
            logger.warning(f"Parse error, attempting repair: {error}")
            return self._attempt_auto_repair(operation)
            
        else:
            # Error genérico: log y continuar con fallback
            logger.error(f"PMS operation failed: {error}")
            return self._use_fallback_data(operation)
    
    def handle_das_error(self, error: DASError, agent: str, operation: str) -> bool:
        """Maneja errores de DAS con enforcement degradado"""
        
        if isinstance(error, PermissionError):
            # Log violación pero no crash completo del sistema
            logger.warning(f"Permission denied for {agent}: {error}")
            self._record_security_incident(agent, operation, str(error))
            return False
            
        elif isinstance(error, AgentNotFoundError):
            # Cargar configuración default para agente
            logger.info(f"Agent config missing, using default: {agent}")
            return self._load_default_agent_config(agent)
            
        else:
            # DAS no disponible: modo bypass temporal con logging
            logger.error(f"DAS enforcement failed, using bypass mode: {error}")
            self._enable_bypass_mode(agent, operation)
            return True
```

## 4. Extensibilidad y Plugins

### 4.1 Plugin Architecture
```python
class PluginInterface(ABC):
    """Interface para plugins de extensión"""
    
    @abstractmethod
    def initialize(self, context: DevHubContext) -> bool:
        """Inicializa plugin con contexto del sistema"""
        pass
    
    @abstractmethod
    def get_supported_events(self) -> list[str]:
        """Retorna eventos que el plugin puede manejar"""
        pass
    
    @abstractmethod
    def handle_event(self, event: SystemEvent) -> PluginResult:
        """Procesa evento del sistema"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Limpieza cuando plugin se desactiva"""
        pass

class PluginManager:
    """Gestor de plugins del sistema"""
    
    def __init__(self, context: DevHubContext):
        self.context = context
        self.plugins = {}
        self.active_plugins = set()
    
    def register_plugin(self, name: str, plugin: PluginInterface) -> bool:
        """Registra nuevo plugin en el sistema"""
        
        try:
            # Validar plugin
            if not self._validate_plugin(plugin):
                return False
            
            # Inicializar plugin
            if plugin.initialize(self.context):
                self.plugins[name] = plugin
                
                # Subscribir a eventos
                for event_type in plugin.get_supported_events():
                    self.context.event_publisher.subscribe(
                        event_type,
                        lambda e: plugin.handle_event(e)
                    )
                
                self.active_plugins.add(name)
                logger.info(f"Plugin '{name}' registered successfully")
                return True
            else:
                logger.error(f"Plugin '{name}' initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Plugin registration failed for '{name}': {e}")
            return False

# Ejemplo: Plugin para integración con Slack
class SlackNotificationPlugin(PluginInterface):
    """Plugin para notificaciones Slack"""
    
    def initialize(self, context: DevHubContext) -> bool:
        self.slack_client = SlackClient(context.config.get('slack_token'))
        self.channel = context.config.get('slack_channel', '#devhub')
        return self.slack_client.test_connection()
    
    def get_supported_events(self) -> list[str]:
        return [
            EventTypes.BLUEPRINT_UPDATED,
            EventTypes.TASK_COMPLETED,
            EventTypes.INTEGRITY_VIOLATION
        ]
    
    def handle_event(self, event: SystemEvent) -> PluginResult:
        """Envía notificación a Slack basada en evento"""
        
        message = self._format_message(event)
        
        try:
            self.slack_client.send_message(self.channel, message)
            return PluginResult(success=True)
        except Exception as e:
            return PluginResult(success=False, error=str(e))
    
    def _format_message(self, event: SystemEvent) -> str:
        """Formatea mensaje para Slack"""
        
        if event.type == EventTypes.BLUEPRINT_UPDATED:
            return f"📐 Blueprint updated by {event.source}"
        elif event.type == EventTypes.TASK_COMPLETED:
            return f"✅ Task completed: {event.data.get('task_id')}"
        elif event.type == EventTypes.INTEGRITY_VIOLATION:
            return f"🚨 Data integrity issue detected in {event.data.get('scope')}"
        else:
            return f"📢 System event: {event.type}"
```

### 4.2 Extension Points
```python
# Extension points definidos en el sistema

class ExtensionPoints:
    """Registry de puntos de extensión disponibles"""
    
    # Agent lifecycle hooks
    AGENT_PRE_EXECUTE = "agent.pre_execute"
    AGENT_POST_EXECUTE = "agent.post_execute"
    AGENT_ERROR = "agent.error"
    
    # Data validation hooks
    PRE_SAVE_VALIDATION = "data.pre_save_validation"
    POST_SAVE_PROCESSING = "data.post_save_processing"
    INTEGRITY_CHECK = "data.integrity_check"
    
    # CLI command extensions
    CLI_COMMAND_EXTENSION = "cli.command_extension"
    CLI_OUTPUT_FORMATTER = "cli.output_formatter"
    
    # Web dashboard widgets
    DASHBOARD_WIDGET = "web.dashboard_widget"
    API_ENDPOINT_EXTENSION = "web.api_extension"

# Ejemplo: Extension para validación custom
class CustomValidationExtension(PluginInterface):
    """Extension para validaciones custom de datos"""
    
    def handle_event(self, event: SystemEvent) -> PluginResult:
        if event.type == ExtensionPoints.PRE_SAVE_VALIDATION:
            return self._validate_data(event.data)
        return PluginResult(success=True)
    
    def _validate_data(self, data: dict) -> PluginResult:
        """Validación custom de reglas de negocio"""
        
        # Ejemplo: Validar que blueprint tenga versión semantic
        if 'version' in data:
            version = data['version']
            if not self._is_semantic_version(version):
                return PluginResult(
                    success=False,
                    error=f"Version '{version}' is not semantic (x.y.z)"
                )
        
        return PluginResult(success=True)
```

## 5. Deployment Architecture

### 5.1 Deployment Models

#### Standalone Deployment
```yaml
# docker-compose.yml para deployment standalone
version: '3.8'

services:
  devhub-core:
    build:
      context: .
      dockerfile: Dockerfile.core
    volumes:
      - ./projects:/app/projects
      - ./config:/app/config
    environment:
      - DEVHUB_MODE=standalone
      - PYTHON_PATH=/usr/bin/python3
    ports:
      - "8080:8080"  # Web dashboard
    
  devhub-cli:
    build:
      context: .
      dockerfile: Dockerfile.cli
    volumes:
      - ./projects:/app/projects
    stdin_open: true
    tty: true
    profiles: ["cli"]

volumes:
  projects:
    driver: local
  config:
    driver: local
```

#### Development Environment
```bash
#!/bin/bash
# setup_dev_environment.sh

# DevHub development environment setup

echo "Setting up DevHub development environment..."

# 1. Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Node.js dependencies (para web dashboard)
cd web-dashboard
npm install
cd ..

# 3. Initialize development project
mkdir -p dev-project
cd dev-project
python ../devhub_cli.py create-project sample-project
cd sample-project

# 4. Validate setup
python ../../devhub_cli.py validate-structure
python ../../devhub_cli.py evaluate-blueprint

echo "✅ Development environment ready!"
echo "📁 Sample project: ./dev-project/sample-project"
echo "🚀 Start web dashboard: cd web-dashboard && npm run dev"
echo "🔧 CLI available: python devhub_cli.py --help"
```

### 5.2 Configuration Management

#### Environment-specific Configs
```python
# config/environments.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EnvironmentConfig:
    """Configuración específica por environment"""
    
    environment: str
    debug_mode: bool
    log_level: str
    
    # PMS settings
    pms_backup_retention_days: int
    pms_integrity_check_interval: int
    
    # DAS settings  
    das_audit_retention_days: int
    das_strict_mode: bool
    
    # Web dashboard settings
    web_dashboard_enabled: bool
    web_dashboard_port: int
    web_real_time_updates: bool
    
    # Performance settings
    max_memory_usage_mb: int
    max_concurrent_agents: int
    
    # Plugin settings
    plugins_enabled: bool
    plugins_directory: str

class ConfigManager:
    """Gestor de configuración multi-environment"""
    
    ENVIRONMENTS = {
        'development': EnvironmentConfig(
            environment='development',
            debug_mode=True,
            log_level='DEBUG',
            pms_backup_retention_days=7,
            pms_integrity_check_interval=300,  # 5 minutes
            das_audit_retention_days=30,
            das_strict_mode=False,  # More lenient in dev
            web_dashboard_enabled=True,
            web_dashboard_port=3000,
            web_real_time_updates=True,
            max_memory_usage_mb=1024,
            max_concurrent_agents=3,
            plugins_enabled=True,
            plugins_directory='plugins/'
        ),
        
        'production': EnvironmentConfig(
            environment='production',
            debug_mode=False,
            log_level='INFO',
            pms_backup_retention_days=90,
            pms_integrity_check_interval=3600,  # 1 hour
            das_audit_retention_days=365,
            das_strict_mode=True,  # Strict in production
            web_dashboard_enabled=True,
            web_dashboard_port=8080,
            web_real_time_updates=False,  # Less overhead
            max_memory_usage_mb=2048,
            max_concurrent_agents=10,
            plugins_enabled=False,  # Disabled for stability
            plugins_directory='/opt/devhub/plugins/'
        ),
        
        'testing': EnvironmentConfig(
            environment='testing',
            debug_mode=True,
            log_level='WARNING',
            pms_backup_retention_days=1,
            pms_integrity_check_interval=60,  # 1 minute
            das_audit_retention_days=7,
            das_strict_mode=True,  # Test strict mode
            web_dashboard_enabled=False,  # Not needed in tests
            web_dashboard_port=0,
            web_real_time_updates=False,
            max_memory_usage_mb=512,
            max_concurrent_agents=5,
            plugins_enabled=True,  # Test plugins
            plugins_directory='test_plugins/'
        )
    }
    
    @classmethod
    def get_config(cls, environment: str = None) -> EnvironmentConfig:
        """Obtiene configuración para environment específico"""
        
        if environment is None:
            environment = os.getenv('DEVHUB_ENV', 'development')
        
        if environment not in cls.ENVIRONMENTS:
            raise ValueError(f"Unknown environment: {environment}")
        
        return cls.ENVIRONMENTS[environment]
```

Esta arquitectura detallada proporciona una base sólida y extensible para DevHub, con separación clara de responsabilidades, patrones de diseño probados, y flexibilidad para crecimiento futuro.