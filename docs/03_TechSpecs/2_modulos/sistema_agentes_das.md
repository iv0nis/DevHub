# TechSpecs - Sistema Agentes DAS

## 1. Introducción

### Propósito
Especificar la implementación técnica del Sistema de Agentes DAS (DevAgent System) que permite la orquestación de múltiples agentes especializados para tareas específicas del proyecto con enforcement técnico de permisos.

### Alcance
- Implementación del enforcer de permisos DAS 
- Validación automática de scopes de acceso
- Integración con PMS Core para operaciones seguras
- Sistema de caching de configuraciones de agentes
- Logging y auditoría de violaciones de permisos

### Referencias
- **Blueprint**: docs/02_blueprint.yaml (componentes.sistema_agentes_das)
- **Charter**: docs/01_ProjectCharter.yaml  
- **HLD Components**: Arquitectura de 3 pilares (PMS + DAS + UI)
- **User Stories**: US relacionadas con seguridad y enforcement
- **ADRs**: Decisiones de arquitectura local filesystem

### Contexto
- **Propósito**: Resolver el control de acceso granular entre agentes y recursos del proyecto
- **Alcance incluido**: [Permission validation, Agent config loading, PMS operation wrapping, Audit logging]
- **Alcance excluido**: [Agent orchestration workflow, Inter-agent communication, UI components]
- **Suposiciones**: [Agentes tienen configuración YAML válida, PMS Core está operativo, Filesystem es accesible]
- **Restricciones**:
  - **Técnicas**: [Python 3.8+, PyYAML dependency, POSIX/Windows file locking]
  - **Regulatorias**: [Debe mantener audit trail de accesos]
  - **Temporales**: [Validación de permisos debe ser < 100ms]

## 2. Descripción del Módulo

### Información General
- **Nombre**: DAS Enforcer
- **Responsabilidades**: Validar permisos de agentes, envolver operaciones PMS, mantener cache de configuraciones, logging de violaciones
- **Relación con otros módulos**: Intermedio entre agentes y PMS Core, consumido por todos los agentes del sistema

### Diagramas
- **Clases**: docs/03_TechSpecs/3_diseno_detallado/clase_das_enforcer.png
- **Secuencia**: docs/03_TechSpecs/3_diseno_detallado/secuencia_permission_check.png

## 3. Diseño Detallado

### Clases y Objetos

DASEnforcer:
  attributes:
    - agents_dir: Path
    - project_root: Path
    - permissions_cache: Dict[str, Dict]
    - protected_paths: Dict[str, List[str]]
  methods:
    - load_agent_permissions:
        purpose: Cargar y cachear configuración de permisos de un agente
        inputs: agent_id (str)
        outputs: Dict con read_scopes, write_scopes, enforcement settings
    - validate_agent_permissions:
        purpose: Validar si agente tiene permisos para operación en scope
        inputs: agent_id (str), operation (Literal['load', 'save']), scope (str)
        outputs: bool (True si permitido)
    - safe_pms_call:
        purpose: Wrapper seguro para operaciones PMS Core con validation
        inputs: agent_id, operation, scope, payload, mode
        outputs: Result from PMS operation
  responsibilities:
    - Mantener cache de configuraciones de agentes
    - Validar permisos antes de operaciones PMS
    - Logging de violaciones para auditoría

### Interfaces y Contratos

Agent Permission API:
  type: Python function interface
  inputs: agent_id (str), scope (str), optional payload
  outputs: Parsed data from PMS or PermissionError
  protocol: Function calls dentro del proceso
  authentication: YAML config file validation

Safe PMS Wrapper:
  type: Internal wrapper interface
  inputs: Standard PMS parameters with agent validation
  outputs: PMS operation results with security envelope
  protocol: Direct function calls
  authentication: Agent ID + scope permission matrix

### Algoritmos y Pseudocódigo

Permission Validation Algorithm:
  description: Validar permisos de agente para operación específica
  steps:
    - step: 1
      action: Load agent config from YAML (with caching)
    - step: 2
      action: Extract read_scopes/write_scopes based on operation type
    - step: 3  
      action: Check if requested scope matches any allowed pattern (wildcard support)
    - step: 4
      action: Log violation and raise PermissionError if denied
  complexity: O(n) where n is number of allowed scope patterns

Scope Matching Algorithm:
  description: Verificar si scope solicitado coincide con patrón permitido
  steps:
    - step: 1
      action: Exact match comparison (scope == allowed_pattern)
    - step: 2
      action: Wildcard matching for patterns ending with '*'
    - step: 3
      action: Return True if match found, False otherwise
  complexity: O(1) for exact match, O(m) for wildcard where m is pattern length

### Flujos Internos

Agent Load Flow:
  trigger: agent_load() function called by any agent
  steps:
    - Validate agent permissions for 'load' operation on scope
    - Log attempt and result
    - Call PMS Core load() if authorized
    - Return data or raise PermissionError
  output: Parsed data from target scope

Agent Save Flow:
  trigger: agent_save() function called by any agent  
  steps:
    - Validate agent permissions for 'save' operation on scope
    - Check payload is provided
    - Determine save mode from agent config
    - Call PMS Core save() if authorized
    - Log operation result
  output: Save confirmation or PermissionError

### Validaciones y Reglas de Negocio

rules:
  - rule_id: PERM_001
    description: Agent must have valid YAML config file in agents/ directory
    validation: File exists and parses as valid YAML with required fields
  - rule_id: PERM_002  
    description: Read operations require scope in read_scopes OR write_scopes
    validation: scope matches any pattern in combined allowed scopes list
  - rule_id: PERM_003
    description: Write operations require scope in write_scopes only
    validation: scope matches pattern in write_scopes list specifically
  - rule_id: PERM_004
    description: Wildcard scopes must use '*' suffix (e.g., "backlog_f*")
    validation: Pattern ends with '*' and prefix matches scope start

## 4. Datos

### Esquema de Base de Datos
N/A - Sistema usa filesystem para persistencia via PMS Core

### Modelos de Datos Internos

AgentPermissions:
  structure: 
    read_scopes: List[str]
    write_scopes: List[str] 
    mode: str
    enforcement_enabled: bool
    strict_mode: bool
    log_violations: bool
  lifecycle: Cargado on-demand, cacheado en memoria, invalidado on config change
  validation: Required fields check, valid scope pattern format

ProtectedPaths:
  structure: Dict[scope_pattern, List[file_glob_patterns]]
  lifecycle: Inicializado al startup, estático durante ejecución
  validation: Valid glob patterns, existing scope patterns

### Formatos de Intercambio

Agent Config YAML:
  type: YAML file format
  schema: |
    pms_scopes:
      read: [list of scope patterns]
      write: [list of scope patterns] 
      mode: string
    enforcement:
      enabled: boolean
      strict_mode: boolean
      log_violations: boolean
  example: |
    pms_scopes:
      read: ["blueprint", "backlog_f*"]
      write: ["backlog_f*", "project_status"]
      mode: "update_single"
    enforcement:
      enabled: true
      strict_mode: true
      log_violations: true

## 5. Integraciones

### APIs y Servicios

PMS Core Integration:
  type: Internal Python module import
  endpoints:
    - endpoint: pms_core.load()
      method: Function call
      purpose: Load data from scope with agent permission wrapper
      authentication: Agent ID validation
    - endpoint: pms_core.save()
      method: Function call
      purpose: Save data to scope with agent permission wrapper
      authentication: Agent ID + write permission validation
  format: Python objects (dict, str)

### Dependencias Externas

libraries:
  - name: PyYAML
    version: ">=6.0"
    purpose: Parse agent configuration YAML files
  - name: pathlib
    version: Python stdlib
    purpose: File path manipulation and validation
  - name: fnmatch  
    version: Python stdlib
    purpose: Glob pattern matching for protected paths
  - name: logging
    version: Python stdlib
    purpose: Audit trail and violation logging

## 6. Seguridad

### Controles de Acceso

access_controls:
  - level: Agent-based granular permissions
    permissions: read_scopes/write_scopes per agent configuration
    enforcement: Technical enforcement via DAS Enforcer validation

### Validación de Entradas

input_validation:
  - input_type: agent_id parameter
    validation_rules: Non-empty string, valid YAML config file exists
    sanitization: Path traversal prevention, filename validation
  - input_type: scope parameter
    validation_rules: Non-empty string, matches expected scope patterns
    sanitization: Special character filtering
  - input_type: payload parameter (for save operations)
    validation_rules: Required for save, proper data type expected by PMS
    sanitization: Delegated to PMS Core layer

### Encriptación y Hash

security_measures:
  - data_type: Agent permissions cache
    protection: Memory-only storage, cleared on process exit
    algorithm: None (ephemeral data)
  - data_type: Violation logs
    protection: Standard logging framework protections
    algorithm: Timestamp + structured logging format

## 7. Errores y Manejo de Excepciones

### Tipos de Errores

error_types:
  - error_code: PERM_DENIED
    description: Agent lacks required permissions for operation
    category: Authorization error
    recovery_strategy: Check agent config, request permission elevation, or use different scope
  - error_code: AGENT_NOT_FOUND
    description: Agent configuration file not found or invalid
    category: Configuration error
    recovery_strategy: Create valid agent config file or verify agent_id parameter
  - error_code: PMS_INTEGRATION_FAILED  
    description: Unable to import or call PMS Core functions
    category: Integration error
    recovery_strategy: Verify PMS Core installation and Python path configuration

### Logging y Alertas

logging:
  - level: WARNING
    events: Permission violations, config loading errors
    format: "PERMISSION_VIOLATION: {agent_id} tried {operation} on '{scope}' - {message}"
  - level: INFO
    events: Successful permission validations (if debug enabled)
    format: "PERMISSION_GRANTED: {agent_id} {operation} {scope}"

alerts:
  - condition: Multiple permission violations from same agent within time window
    severity: HIGH
    notification: Log warning with rate limiting detection
  - condition: Agent config file missing or corrupted
    severity: MEDIUM  
    notification: Detailed error message with fix suggestions

## 8. Pruebas Previstas

### Casos de Prueba Unitarios

unit_tests:
  - test_case: test_valid_agent_permission_load
    description: Agent with read permission can load from allowed scope
    inputs: DevAgent, "load", "blueprint" 
    expected_output: Successful data load from PMS
    assertions: No PermissionError raised, data returned
  - test_case: test_denied_agent_permission_save
    description: Agent without write permission cannot save to scope
    inputs: ReadOnlyAgent, "save", "blueprint", test_payload
    expected_output: PermissionError raised
    assertions: Exception contains agent_id and scope, no PMS save called
  - test_case: test_wildcard_scope_matching
    description: Wildcard scope "backlog_f*" matches "backlog_f1", "backlog_f2"
    inputs: DevAgent, "load", "backlog_f1"
    expected_output: Permission granted for wildcard match
    assertions: _scope_matches returns True for pattern matching

### Datos de Prueba  

test_data:
  - dataset: Valid agent configurations
    purpose: Test permission loading and validation
    size: 5 agent config files with various permission combinations
  - dataset: Invalid agent configurations
    purpose: Test error handling for malformed configs  
    size: 3 invalid YAML files with missing required fields
  - dataset: Protected path test cases
    purpose: Test file path to scope mapping validation
    size: 10 file paths covering different scope patterns

### Mocks y Stubs

mocks:
  - component: PMS Core module
    purpose: Test DAS Enforcer without requiring full PMS installation
    behavior: Return success/failure based on test scenario requirements
  - component: YAML config files
    purpose: Test different agent permission configurations
    behavior: Provide controlled test data for various permission scenarios

## 9. Rendimiento

### Límites de Carga

performance_limits:
  - metric: Permission validation latency
    limit: < 100ms per validation
    measurement: Time from agent_load/save call to PMS operation
  - metric: Config cache hit rate  
    limit: > 95% for repeated agent operations
    measurement: Cache hits vs misses during operation
  - metric: Memory usage for permissions cache
    limit: < 10MB for 100 agent configurations
    measurement: Memory profiling of permissions_cache dict

### Optimizaciones

optimizations:
  - technique: Agent configuration caching
    target: Reduce YAML file I/O operations
    expected_improvement: 90%+ reduction in config load time for repeated access
  - technique: Compiled regex patterns for scope matching
    target: Faster wildcard scope validation
    expected_improvement: 50% improvement in scope matching performance
  - technique: Lazy loading of protected paths
    target: Reduce startup time
    expected_improvement: 30% faster enforcer initialization

### Métricas de Aceptación

acceptance_criteria:
  - metric: Permission validation time
    threshold: < 50ms per validation
    measurement_period: During normal operation load
  - metric: Zero false positives
    threshold: 100% accuracy in permission decisions
    measurement_period: Comprehensive test suite execution
  - metric: Complete audit trail
    threshold: All permission attempts logged
    measurement_period: Full operational day

## 10. Anexos

### Diagramas de Soporte

diagrams:
  - type: Component interaction diagram
    file: docs/03_TechSpecs/10_anexos/das_enforcer_interaction.png
    description: Shows DAS Enforcer as intermediary between agents and PMS Core
  - type: Permission validation flowchart
    file: docs/03_TechSpecs/10_anexos/permission_validation_flow.png  
    description: Decision tree for permission validation logic

### Ejemplos de Datos

data_examples:
  - scenario: DevAgent loading backlog data
    data: |
      agent_id: "DevAgent"
      operation: "load"
      scope: "backlog_f1"
      result: SUCCESS (scope matches "backlog_f*" in read_scopes)
  - scenario: Unauthorized agent attempting blueprint save
    data: |
      agent_id: "ReadOnlyAgent"  
      operation: "save"
      scope: "blueprint"
      result: PERMISSION_DENIED (scope not in write_scopes)

### ADRs Relacionados

adrs:
  - adr_id: ADR-001
    title: Arquitectura local filesystem
    decision: Use local filesystem with PMS for project persistence
    impact: DAS Enforcer must validate file path access patterns
  - adr_id: ADR-002
    title: Single tenant por proyecto
    decision: Each project instance isolated in directory structure  
    impact: Agent permissions scoped to project-specific directories

### Trazabilidad

traceability:
  blueprint_components:
    - sistema_agentes_das
    - seguridad_enforcement  
  backlog_tasks:
    - Implementation of permission validation system
    - Agent configuration management
  requirements:
    - REQ-SEC-001: Granular agent access control
    - REQ-SEC-002: Complete audit trail of operations
    - REQ-PERF-001: Sub-100ms permission validation

## 11. Integración PMS/DAS

### PMS Integration

pms_integration:
  memory_index_paths:
    status: "./memory/project_status.md" 
    blueprint: "./docs/02_blueprint.yaml"
    blueprint_changes: "./docs/blueprint_changes.csv"
    backlog_dir: "./docs/05_backlog/"
    techspecs: "./docs/03_TechSpecs.yaml"
  sha_validation:
    enabled: true
    expected_hash: "auto-calculated per operation"
  save_modes:
    default: "update_single"
    critical_resources:
      - scope: "blueprint"
        mode: "update_dual"  
      - scope: "techspecs"
        mode: "update_single"
  concurrency:
    locks: true
    tmp_write_pattern: true
  metrics:
    enabled: true
    expose: ["permission_checks", "violations", "cache_performance"]

### DAS Enforcement  

das_enforcement:
  enabled: true
  agents:
    - id: "DevAgent"
      pms_scopes:
        read: ["memory_index", "backlog_f*", "blueprint", "project_status", "techspecs"]
        write: ["backlog_f*", "project_status", "blueprint_changes", "techspecs"] 
      mode: "update_single"
    - id: "BluePrintAgent"
      pms_scopes:
        read: ["blueprint", "blueprint_changes", "project_status"]
        write: ["blueprint", "project_status"]
      mode: "update_dual"
  rules:
    - id: "no_direct_fs_access" 
      description: "Todos los agentes deben usar DAS Enforcer → PMS-Core para acceso a archivos."
    - id: "scope_wildcard_support"
      description: "Soporte para patterns tipo 'backlog_f*' para acceso a múltiples scopes relacionados."

### Blueprint Contract

blueprint_contract:
  format:
    module_id: "DAS-ENF-001"
    component: "sistema_agentes_das"
    version: "1.0"
  merge_flow_states: ["proposed", "reviewed", "approved", "merged"]
  sync_dependencies:
    blueprint_to_techspecs: "automated" 
    techspecs_to_backlog: "automated"
    validation_required: "permission_matrix_consistency"

## 12. Changelog y Versionado

changelog:
  - "v1.0.0: Implementación inicial DAS Enforcer con validation básica"
  - "v1.1.0: Agregado soporte para wildcard scopes y caching mejorado"

open_questions:
  - "¿Necesitamos rate limiting para prevenir ataques por fuerza bruta?"
  - "¿Implementar rotación automática de logs de auditoría?"

acceptance_criteria:
  - "Todos los agentes pueden cargar/guardar datos solo según sus permisos configurados"
  - "Sistema mantiene audit trail completo de todas las operaciones autorizadas/denegadas"
  - "Rendimiento de validación de permisos < 50ms en 95% de los casos"