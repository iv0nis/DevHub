# Contratos de Comunicación entre Agentes

## Overview
Define los contratos de datos y interfaces estándar para comunicación entre agentes en DevHub, garantizando interoperabilidad y consistencia.

## Arquitectura de Comunicación

### Patrón File-Based + Event-Driven
- **Persistencia**: Archivos YAML/MD como medium de intercambio
- **Coordinación**: DAS Enforcer orquesta acceso y permisos
- **Eventos**: Cambios en filesystem generan eventos de sincronización

## Contratos por Agente

### BlueprintAgent

#### Interfaces de Entrada
```yaml
# blueprint_changes.csv - Input format
section: str                    # Sección del blueprint a modificar
change_type: enum              # add|update|remove
description: str               # Descripción del cambio
rationale: str                 # Justificación técnica
impact: enum                   # low|medium|high
proposed_by: str               # ID del agente/usuario
timestamp: datetime            # Cuándo se propuso
```

#### Interfaces de Salida
```yaml
# blueprint.yaml - Output format
version: str                   # Versión del blueprint
last_modified: datetime        # Timestamp de última modificación
sha1_hash: str                # Hash de integridad
components:                   # Estructura completa de componentes
  charter_mapping: dict       # Mapeo Charter → Arquitectura
  agentes: dict              # Configuración de agentes
  sistemas: dict             # Especificaciones técnicas
```

### DevAgent

#### Interfaces de Entrada
```yaml
# backlog_f{N}.yaml - Tasks para ejecutar
tasks:
  - id: str                    # Identificador único de task
    feature: str               # Feature asociada
    type: enum                 # development|testing|documentation
    priority: enum             # high|medium|low
    estimation: int            # Story points o horas
    dependencies: list         # IDs de tasks dependientes
    acceptance_criteria: list  # Criterios específicos
    assigned_to: str          # DevAgent instance
    status: enum              # pending|in_progress|completed|blocked
```

#### Interfaces de Salida
```yaml
# project_status.md updates
current_state:
  fase_actual: int            # Fase de desarrollo actual
  tasks_completed: int        # Tasks finalizadas en fase
  tasks_pending: int          # Tasks restantes
  blockers: list             # Impedimentos identificados
  
last_activity:
  agent: str                  # Agente que ejecutó última acción
  action: str                # Tipo de acción realizada
  timestamp: datetime        # Cuándo ocurrió
  files_modified: list       # Archivos afectados
```

### AiProjectManager

#### Interfaces de Entrada
```yaml
# Lectura de múltiples fuentes
blueprint_status:
  completeness: float         # % de completitud vs Charter
  gaps: list                 # Áreas que requieren atención
  
backlog_status:
  phases: dict               # Estado por fase
  velocity: float            # Tasks/sprint promedio
  
project_metrics:
  timeline_health: enum      # on_track|at_risk|delayed
  quality_metrics: dict     # Métricas de calidad
```

#### Interfaces de Salida
```yaml
# Reportes y coordinación
project_dashboard:
  overall_health: enum       # healthy|warning|critical
  key_metrics: dict         # KPIs principales
  recommendations: list     # Acciones sugeridas
  next_priorities: list     # Próximas tareas críticas
  
stakeholder_updates:
  progress_summary: str      # Resumen ejecutivo
  completed_milestones: list # Hitos alcanzados
  upcoming_deliverables: list # Próximas entregas
  risks_and_mitigations: dict # Riesgos identificados
```

## Contratos de Sincronización

### PMS Core Operations
```python
# Operaciones estándar garantizadas
def load(scope: str) -> dict:
    """Carga datos con validación de integridad"""
    
def save(scope: str, data: dict) -> bool:
    """Guarda con transacción atómica"""
    
def rollback(scope: str, version: str) -> bool:
    """Rollback a versión anterior"""
```

### DAS Enforcer Validations
```python
# Validaciones automáticas
def validate_agent_permissions(agent: str, operation: str, scope: str) -> bool:
    """Valida permisos antes de operación"""
    
def log_access_attempt(agent: str, scope: str, success: bool) -> None:
    """Registra intentos de acceso para auditoría"""
    
def trigger_sync_event(scope: str, change_type: str) -> None:
    """Dispara eventos de sincronización"""
```

## Políticas de Comunicación

### Orden de Precedencia
1. **BlueprintAgent**: Autoridad única sobre blueprint.yaml
2. **DevAgent**: Ejecutor principal de tasks en backlog
3. **AiProjectManager**: Coordinador y reportes, solo lectura

### Resolución de Conflictos
- **Timestamp**: Cambio más reciente prevalece
- **Agent Priority**: BlueprintAgent > DevAgent > AiProjectManager
- **Manual Override**: Humano puede resolver conflictos explícitamente

### Estados de Sincronización
```yaml
sync_status:
  last_sync: datetime         # Última sincronización exitosa
  pending_changes: list       # Cambios pendientes de propagar
  conflicts: list            # Conflictos que requieren resolución
  integrity_check: bool       # Validación SHA-1 passed
```

## Eventos de Integración

### Pipeline de Eventos
```mermaid
blueprint_changes.csv → BlueprintAgent → blueprint.yaml → 
TriggerSync → DAS_Enforcer → UpdateStatus → 
NotifyAgents → project_status.md
```

### Event Schemas
```yaml
# Evento estándar
event:
  type: str                   # blueprint.updated, task.completed, etc.
  source_agent: str           # Agente que generó el evento
  target_agents: list         # Agentes que deben reaccionar
  payload: dict              # Datos del evento
  timestamp: datetime        # Cuándo ocurrió
  correlation_id: str        # Para trazabilidad
```

## Testing de Contratos

### Validation Schema
```python
# Esquemas Pydantic para validación automática
class BlueprintChange(BaseModel):
    section: str
    change_type: Literal['add', 'update', 'remove']
    description: str
    rationale: str
    impact: Literal['low', 'medium', 'high']

class TaskDefinition(BaseModel):
    id: str
    feature: str
    type: Literal['development', 'testing', 'documentation']
    priority: Literal['high', 'medium', 'low']
    acceptance_criteria: List[str]
```

### Integration Tests
- **Contract Compliance**: Todos los agentes respetan schemas
- **Sync Integrity**: Cambios se propagan correctamente
- **Permission Enforcement**: DAS bloquea operaciones no autorizadas
- **Data Consistency**: Estados sincronizados tras operaciones

Esta especificación garantiza comunicación confiable y consistente entre todos los agentes del sistema DevHub.