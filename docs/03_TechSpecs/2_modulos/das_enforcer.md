# TS-DAS: DevAgent System Enforcer

## 1. Descripción del Módulo

### Información General
- **Nombre**: DAS Enforcer (DevAgent System)
- **ID**: TS-DAS-001
- **Responsabilidades**: Orquestación de múltiples agentes con enforcement automático de permisos y validación de acceso
- **Relación con otros módulos**: Capa intermedia entre agentes y PMS Core, proporciona APIs `agent_load` y `agent_save`

### Interfaces Principales
```python
class DASEnforcer:
    def agent_load(agent_name: str, scope: str) -> dict
    def agent_save(agent_name: str, scope: str, data: dict) -> bool
    def validate_agent_config(agent_name: str) -> dict
    def validate_file_access(agent_name: str, file_path: str, operation: str) -> bool
    def log_access_attempt(agent_name: str, scope: str, operation: str, success: bool) -> None
```

## 2. Diseño Detallado

### Arquitectura Interna
```
DAS Enforcer Architecture:
┌─────────────────────────────────────────┐
│ Agent API Layer (agent_load/save)       │
├─────────────────────────────────────────┤
│ Permission Validation Layer             │
├─────────────────────────────────────────┤  
│ Filesystem Protection Layer             │
├─────────────────────────────────────────┤
│ Audit & Logging Layer                   │
├─────────────────────────────────────────┤
│ PMS Core Integration                     │
└─────────────────────────────────────────┘
```

### Componentes Principales

#### 2.1 DASEnforcer Core Class
```python
class DASEnforcer:
    """Sistema de enforcement con validación automática de permisos"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.agent_configs = {}
        self.protected_paths = {}
        self.audit_log = []
        self.pms_core = PMSCore(project_root)
        
        self._load_agent_configurations()
        self._init_protected_paths()
        self._init_audit_logger()
    
    def _load_agent_configurations(self) -> None:
        """Carga configuraciones YAML de todos los agentes"""
        agents_dir = self.project_root / 'das' / 'agent_templates'
        
        for agent_file in agents_dir.glob('*.yaml'):
            with open(agent_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                agent_name = config.get('agente', {}).get('nombre')
                if agent_name:
                    self.agent_configs[agent_name] = config
    
    def _init_protected_paths(self) -> None:
        """Inicializa mapeo de scopes a paths del filesystem protegidos"""
        self.protected_paths = {
            'blueprint': [
                'docs/02_blueprint/**/*',
                'docs/blueprint.yaml'
            ],
            'project_charter': [
                'docs/01_ProjectCharter/**/*'
            ],
            'backlog_f1': [
                'docs/05_backlog/backlog_f1.yaml'
            ],
            'backlog_f2': [
                'docs/05_backlog/backlog_f2.yaml'
            ],
            'project_status': [
                'memory/project_status.md'
            ],
            'blueprint_changes': [
                'docs/blueprint_changes.csv'
            ]
        }
```

#### 2.2 Permission Validation Layer
```python
class PermissionValidator:
    """Validación granular de permisos por agente y scope"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
    
    def validate_read_permission(self, agent_name: str, scope: str) -> tuple[bool, str]:
        """Valida si agente puede leer scope específico"""
        agent_config = self.enforcer.agent_configs.get(agent_name)
        if not agent_config:
            return False, f"Agente '{agent_name}' no configurado"
        
        pms_scopes = agent_config.get('pms_scopes', {})
        read_scopes = pms_scopes.get('read', [])
        
        # Soporte para wildcards (backlog_f*)
        if scope in read_scopes:
            return True, "Permiso directo concedido"
        
        # Validar wildcards
        for allowed_scope in read_scopes:
            if allowed_scope.endswith('*'):
                base_scope = allowed_scope[:-1]
                if scope.startswith(base_scope):
                    return True, f"Permiso wildcard '{allowed_scope}' coincide"
        
        return False, f"Agente '{agent_name}' no tiene permiso read para '{scope}'"
    
    def validate_write_permission(self, agent_name: str, scope: str) -> tuple[bool, str]:
        """Valida si agente puede escribir scope específico"""
        agent_config = self.enforcer.agent_configs.get(agent_name)
        if not agent_config:
            return False, f"Agente '{agent_name}' no configurado"
        
        pms_scopes = agent_config.get('pms_scopes', {})
        write_scopes = pms_scopes.get('write', [])
        
        # Validación similar a read con wildcards
        if scope in write_scopes:
            return True, "Permiso write directo concedido"
        
        for allowed_scope in write_scopes:
            if allowed_scope.endswith('*'):
                base_scope = allowed_scope[:-1]
                if scope.startswith(base_scope):
                    return True, f"Permiso write wildcard '{allowed_scope}' coincide"
        
        return False, f"Agente '{agent_name}' no tiene permiso write para '{scope}'"
    
    def get_agent_permissions(self, agent_name: str) -> dict:
        """Retorna configuración completa de permisos para agente"""
        agent_config = self.enforcer.agent_configs.get(agent_name, {})
        pms_scopes = agent_config.get('pms_scopes', {})
        enforcement = agent_config.get('enforcement', {})
        
        return {
            'read_scopes': pms_scopes.get('read', []),
            'write_scopes': pms_scopes.get('write', []),
            'mode': pms_scopes.get('mode', 'update_single'),
            'enforcement_enabled': enforcement.get('enabled', False),
            'strict_mode': enforcement.get('strict_mode', False),
            'log_violations': enforcement.get('log_violations', True)
        }
```

#### 2.3 Filesystem Protection Layer
```python
class FilesystemProtector:
    """Protección a nivel de filesystem usando patterns de paths"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
    
    def validate_file_access(self, agent_name: str, file_path: str, operation: str) -> tuple[bool, str]:
        """Valida acceso a path específico del filesystem"""
        file_path = Path(file_path)
        
        # Determinar scope basado en path
        scope = self._path_to_scope(file_path)
        if not scope:
            return False, f"Path '{file_path}' no mapeado a ningún scope protegido"
        
        # Validar permisos del agente para el scope
        if operation.lower() == 'read':
            return self.enforcer.permission_validator.validate_read_permission(agent_name, scope)
        elif operation.lower() == 'write':
            return self.enforcer.permission_validator.validate_write_permission(agent_name, scope)
        else:
            return False, f"Operación '{operation}' no reconocida"
    
    def _path_to_scope(self, file_path: Path) -> str | None:
        """Mapea path de archivo a scope correspondiente"""
        file_path_str = str(file_path)
        
        for scope, path_patterns in self.enforcer.protected_paths.items():
            for pattern in path_patterns:
                # Soporte básico para wildcards (**)
                if '**' in pattern:
                    base_pattern = pattern.replace('/**/*', '')
                    if file_path_str.startswith(base_pattern):
                        return scope
                elif file_path_str == pattern:
                    return scope
        
        return None
    
    def is_protected_path(self, file_path: str) -> bool:
        """Verifica si path está bajo protección DAS"""
        return self._path_to_scope(Path(file_path)) is not None
```

#### 2.4 Audit & Logging Layer
```python
class AuditLogger:
    """Sistema de auditoría completo para compliance y debugging"""
    
    def __init__(self, enforcer: DASEnforcer):
        self.enforcer = enforcer
        self.log_file = enforcer.project_root / 'memory' / 'das_audit.log'
        self.session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def log_access_attempt(self, agent_name: str, scope: str, operation: str, 
                          success: bool, details: str = "") -> None:
        """Log completo de intento de acceso"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'agent_name': agent_name,
            'scope': scope,
            'operation': operation,
            'success': success,
            'details': details,
            'stack_trace': traceback.format_stack() if not success else None
        }
        
        # Append al log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{json.dumps(log_entry)}\n")
        
        # Mantener en memoria para queries rápidas
        self.enforcer.audit_log.append(log_entry)
        
        # Limpiar log en memoria si crece mucho
        if len(self.enforcer.audit_log) > 1000:
            self.enforcer.audit_log = self.enforcer.audit_log[-500:]
    
    def get_violation_summary(self) -> dict:
        """Resumen de violaciones para alertas"""
        violations = [entry for entry in self.enforcer.audit_log if not entry['success']]
        
        return {
            'total_violations': len(violations),
            'agents_with_violations': list(set(v['agent_name'] for v in violations)),
            'most_violated_scopes': self._count_violations_by_scope(violations),
            'recent_violations': violations[-10:] if violations else []
        }
    
    def _count_violations_by_scope(self, violations: list) -> dict:
        """Cuenta violaciones por scope para identificar problemas"""
        from collections import Counter
        scope_counts = Counter(v['scope'] for v in violations)
        return dict(scope_counts.most_common(5))
```

## 3. APIs y Contratos

### Agent API Specification
```python
def agent_load(agent_name: str, scope: str) -> dict:
    """
    API principal para que agentes carguen datos con enforcement automático
    
    Args:
        agent_name: Nombre del agente (debe coincidir con archivo YAML)
        scope: Scope de datos a cargar (ej: 'blueprint', 'backlog_f1')
    
    Returns:
        dict: Datos del scope solicitado
        
    Raises:
        PermissionError: Si agente no tiene permisos read para el scope
        ScopeNotFoundError: Si scope no existe
        
    Side Effects:
        - Log de acceso en audit trail
        - Validación automática de integridad SHA-1
        - Update de métricas de acceso
    
    Example:
        >>> data = agent_load("DevAgent", "backlog_f1")
        >>> print(data['tasks'][0]['id'])
        'TASK-001'
    """

def agent_save(agent_name: str, scope: str, data: dict) -> bool:
    """
    API principal para que agentes guarden datos con enforcement automático
    
    Args:
        agent_name: Nombre del agente 
        scope: Scope donde guardar datos
        data: Datos a persistir
        
    Returns:
        bool: True si guardado exitoso
        
    Raises:
        PermissionError: Si agente no tiene permisos write para el scope
        ValidationError: Si datos no cumplen schema del scope
        
    Side Effects:
        - Transacción atómica con backup automático
        - Update de SHA-1 hash en memory_index
        - Trigger de eventos de sincronización
        - Log completo en audit trail
        
    Example:
        >>> task_data = {"id": "TASK-002", "status": "completed"}
        >>> success = agent_save("DevAgent", "backlog_f1", task_data)
        >>> assert success == True
    """

def validate_agent_config(agent_name: str) -> dict:
    """
    Valida configuración de agente y retorna permisos efectivos
    
    Returns:
        dict: Configuración de permisos, enforcement settings, y status
        
    Example:
        >>> config = validate_agent_config("BlueprintAgent")
        >>> assert "blueprint" in config['write_scopes']
        >>> assert config['enforcement_enabled'] == True
    """
```

## 4. Configuración de Agentes

### Agent Configuration Schema
```yaml
# das/agent_templates/AgentName.yaml
agente:
  nombre: "AgentName"
  proposito: "Descripción del propósito del agente"
  rol: "Rol específico en el ecosystem"
  personalidad: "Tono y estilo de comunicación"

# DAS Permissions Configuration  
pms_scopes:
  read: ["scope1", "scope2", "backlog_f*"]  # Wildcards soportadas
  write: ["scope1", "blueprint_changes"]
  mode: "update_single"  # update_single|update_dual

enforcement:
  enabled: true
  strict_mode: true      # Falla inmediatamente en violación
  log_violations: true   # Log todos los intentos

# Opcional: Configuración específica del agente
conocimiento_base:
  domain_info: "Información específica del dominio"
  tools: ["tool1", "tool2"]
```

### Predefined Agent Configurations

#### BlueprintAgent Configuration
```yaml
agente:
  nombre: "BlueprintAgent"
  proposito: "Custodio único del blueprint"

pms_scopes:
  read: ["blueprint", "project_charter", "project_status"]
  write: ["blueprint"]
  mode: "update_single"

enforcement:
  enabled: true
  strict_mode: true
  log_violations: true
```

#### DevAgent Configuration  
```yaml
agente:
  nombre: "DevAgent"
  proposito: "Ejecutor de tareas de desarrollo"

pms_scopes:
  read: ["backlog_f*", "blueprint", "project_status"]
  write: ["backlog_f*", "project_status", "blueprint_changes"]
  mode: "update_single"

enforcement:
  enabled: true
  strict_mode: true
  log_violations: true
```

## 5. Manejo de Errores

### Exception Hierarchy
```python
class DASError(Exception):
    """Base exception para DAS Enforcer operations"""
    pass

class PermissionError(DASError):
    """Agente no tiene permisos para operación solicitada"""
    def __init__(self, agent_name: str, scope: str, operation: str):
        self.agent_name = agent_name
        self.scope = scope
        self.operation = operation
        super().__init__(f"Permission denied: {agent_name} cannot {operation} {scope}")

class AgentNotFoundError(DASError):
    """Agente no configurado en el sistema"""
    pass

class EnforcementError(DASError):
    """Error general en enforcement de políticas"""
    pass
```

### Error Recovery Patterns
```python
def safe_agent_load(agent_name: str, scope: str) -> tuple[dict | None, str | None]:
    """Load con manejo graceful de errores"""
    try:
        return agent_load(agent_name, scope), None
    except DASError as e:
        return None, str(e)

def agent_load_with_fallback(agent_name: str, scope: str, fallback: dict) -> dict:
    """Load con fallback automático"""
    data, error = safe_agent_load(agent_name, scope)
    if data is not None:
        return data
    
    # Log error pero continuar con fallback
    logger.warning(f"agent_load failed for {agent_name}/{scope}: {error}")
    return fallback
```

## 6. Seguridad y Compliance

### Security Features
- **Principle of Least Privilege**: Agentes solo acceden a scopes estrictamente necesarios
- **Audit Trail Completo**: Log de todas las operaciones para compliance
- **Filesystem Protection**: Validación automática antes de cualquier I/O
- **Permission Inheritance**: Wildcards para grupos de scopes relacionados

### Compliance Capabilities
- **SOX Compliance**: Audit trail inmutable con timestamps
- **GDPR Compliance**: Log retention policies configurables
- **ISO 27001**: Access control y monitoring automático
- **Change Management**: Trazabilidad completa de modificaciones

### Security Hardening
```python
class SecurityHardening:
    """Medidas adicionales de security hardening"""
    
    @staticmethod
    def validate_agent_name(agent_name: str) -> bool:
        """Previene injection attacks via agent name"""
        import re
        return re.match(r'^[a-zA-Z0-9_]+$', agent_name) is not None
    
    @staticmethod  
    def sanitize_scope(scope: str) -> str:
        """Sanitiza scope para prevenir path traversal"""
        # Remove path traversal attempts
        scope = scope.replace('..', '').replace('/', '_')
        return scope
    
    def rate_limit_check(self, agent_name: str) -> bool:
        """Rate limiting para prevenir abuse"""
        # Implementar rate limiting básico
        pass
```

## 7. Performance y Monitoring

### Performance Optimization
- **Config Caching**: Agent configs cargadas una vez al startup
- **Permission Caching**: Cache de validaciones recientes para speed
- **Lazy Loading**: Audit logs cargados on-demand
- **Batch Operations**: Soporte para operaciones múltiples

### Monitoring Hooks
```python
class DASMonitoring:
    """Monitoring y métricas para DAS Enforcer"""
    
    def __init__(self):
        self.metrics = {
            'operations_count': 0,
            'permission_violations': 0,
            'average_response_time': 0.0,
            'agents_active': set()
        }
    
    def record_operation(self, agent_name: str, operation: str, duration: float, success: bool):
        """Registra métricas de operación"""
        self.metrics['operations_count'] += 1
        self.metrics['agents_active'].add(agent_name)
        
        if not success:
            self.metrics['permission_violations'] += 1
        
        # Update rolling average
        self._update_average_response_time(duration)
    
    def get_health_status(self) -> dict:
        """Health check para monitoring external"""
        violation_rate = self.metrics['permission_violations'] / max(self.metrics['operations_count'], 1)
        
        return {
            'status': 'healthy' if violation_rate < 0.05 else 'warning',
            'operations_per_minute': self._calculate_ops_per_minute(),
            'violation_rate': violation_rate,
            'active_agents': len(self.metrics['agents_active']),
            'average_response_ms': self.metrics['average_response_time'] * 1000
        }
```