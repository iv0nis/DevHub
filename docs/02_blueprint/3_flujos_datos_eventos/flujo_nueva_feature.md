# Flujo de Nueva Feature - DevHub

## Overview
Flujo controlado y trazable de 7 pasos para insertar nuevas funcionalidades, garantizando integridad documental y arquitectónica mediante sincronización modular.

## Flujo de Datos y Eventos

### 1. Idea → Validación (Charter/alcance)
```
Input: Feature request del usuario
├── Validación contra objectives (Charter)
├── Evaluación de scope (In/Out-of-Scope)
└── Output: Feature validada | Feature rechazada
```

**Contratos de Datos:**
- Input: `{feature_description, business_value, technical_requirements}`
- Output: `{validation_result, impact_assessment, approval_status}`

### 2. Propuesta → blueprint_changes.csv → Review
```
Feature validada
├── DevAgent crea propuesta en blueprint_changes.csv
├── BlueprintAgent evalúa completitud actual (≥80%?)
├── Si < 80%: Solicita completar blueprint primero
└── Si ≥ 80%: Procesa cambios en blueprint
```

**Contratos de Datos:**
- Input: `blueprint_changes.csv` con format:
  ```csv
  section,change_type,description,rationale,impact
  components,add,new_component_x,enables_feature_y,medium
  ```
- Output: `blueprint.yaml` actualizado

### 3. Blueprint (módulo) → Sync → Integridad
```
Blueprint actualizado
├── Actualización modular en docs/02_blueprint/
├── Regeneración blueprint.yaml desde estructura modular  
├── Validación SHA-1 para integridad
└── CI verifica sintaxis YAML + alineación
```

**Eventos Técnicos:**
- `blueprint.updated` → Trigger regeneración YAML
- `integrity.validated` → SHA-1 hash updated
- `ci.validation.passed` → Ready for next step

### 4. TechSpec (módulo) → ADR si hay decisión clave
```
Blueprint ≥ 80% + feature especificada
├── Generación Technical Specifications
├── Si decisión crítica → crear ADR
└── Sincronización con blueprint
```

**Contratos de Datos:**
- Input: `blueprint.yaml` section relevant to feature
- Output: `docs/03_techspecs/{feature_name}.md`
- Trigger ADR: Si `impact=high` en blueprint_changes

### 5. Roadmap (módulo) → Sync
```
TechSpecs validados
├── Actualización roadmap con nueva épica
├── Sincronización timeline + dependencies
└── Validación capacidad del equipo
```

**Pipeline de Sincronización:**
- Blueprint → TechSpecs → Roadmap → Backlog
- Cada paso valida consistencia con anterior

### 6. Backlog (módulo) → Sync
```
Épica definida en roadmap
├── Descomposición en user stories + tasks
├── Asignación a fase backlog_f{N}.yaml
└── Priorización + estimación detallada
```

**Formato de Datos:**
```yaml
# backlog_f{N}.yaml
tasks:
  - id: TASK-001
    feature: nueva_feature
    type: development
    priority: high
    estimation: 5
    dependencies: []
    acceptance_criteria: [...]
```

### 7. Status (update)
```
Artefactos sincronizados
├── Actualización project_status.md
├── Log cambios + timestamp
└── Notificación stakeholders
```

## Contratos entre Componentes

### PMS ↔ DAS
- **load/save operations** con enforcement de permisos
- **rollback automático** si violación de integridad
- **event logging** para auditoría

### Agentes ↔ Filesystem
- **Scope-based access** via DAS enforcer
- **SHA-1 validation** para cada read/write
- **Atomic transactions** via PMS

### UI ↔ Backend
- **REST APIs** para estado de proyecto
- **WebSocket events** para notificaciones real-time
- **Export formats** para reporting

## Policies de Datos

### Integridad Documental
- **Single source of truth**: project_status.md
- **Propagación automática** de cambios
- **Validation schemas** YAML estrictos

### Control de Acceso
- **Agent permissions** definidos en YAML
- **Filesystem mapping** protege rutas críticas
- **Audit logging** de todas las operaciones

### Sincronización
- **Timestamp-based** conflict resolution
- **Dependency validation** entre artefactos
- **Rollback capability** en caso de inconsistencias

## Eventos del Sistema

### Eventos de Negocio
- `feature.requested` → Inicia workflow
- `feature.approved` → Procede a blueprint
- `blueprint.ready` → Procede a techspecs
- `development.completed` → Update status

### Eventos Técnicos  
- `document.modified` → Trigger sync
- `integrity.violated` → Trigger rollback
- `permission.denied` → Log violation
- `sync.completed` → Update timestamps

## Métricas y Observabilidad

### KPIs de Flujo
- **Time to backlog**: Idea → Task executable
- **Blueprint completeness**: % vs Charter
- **Sync success rate**: Consistencia documental
- **Agent efficiency**: Tasks/hour por agente

### Alertas Automáticas
- Blueprint completeness < 80%
- Documentos desincronizados > 24h
- Violaciones de permisos repetidas
- CI validation failures

Este flujo garantiza trazabilidad completa, control de calidad y sincronización automática en todo el pipeline de desarrollo de DevHub.