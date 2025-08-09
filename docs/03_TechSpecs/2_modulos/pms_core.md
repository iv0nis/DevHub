# TS-PMS: Persistent Memory System Core

## 1. Descripción del Módulo

### Información General
- **Nombre**: PMS Core (Persistent Memory System)
- **ID**: TS-PMS-001
- **Responsabilidades**: Sistema de memoria persistente confiable con validación de integridad y rollback atómico
- **Relación con otros módulos**: Provee capa de persistencia para DAS Enforcer y todos los agentes

### Interfaces Principales
```python
class PMSCore:
    def load(scope: str, project_path: str = None) -> dict
    def save(scope: str, data: dict, project_path: str = None) -> bool  
    def rollback(scope: str, version: str, project_path: str = None) -> bool
    def validate_integrity(scope: str, project_path: str = None) -> bool
    def get_version_history(scope: str, project_path: str = None) -> list
```

## 2. Diseño Detallado

### Arquitectura Interna
```
PMS Core Architecture:
┌─────────────────────────────────────────┐
│ PMS API Layer (pms_core.py)             │
├─────────────────────────────────────────┤
│ Validation Layer (SHA-1, Schema)        │
├─────────────────────────────────────────┤  
│ Transaction Layer (Atomic Operations)   │
├─────────────────────────────────────────┤
│ Storage Layer (Filesystem + Git)        │
└─────────────────────────────────────────┘
```

### Componentes Principales

#### 2.1 PMSCore Class
```python
class PMSCore:
    """Sistema de memoria persistente con integridad garantizada"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.memory_index_path = self.project_root / 'memory' / 'memory_index.yaml'
        self.temp_dir = self.project_root / '.pms_temp'
        self._load_memory_index()
    
    def _load_memory_index(self) -> None:
        """Carga configuración de paths y metadatos"""
        with open(self.memory_index_path, 'r', encoding='utf-8') as f:
            self.memory_index = yaml.safe_load(f)
    
    def _get_file_path(self, scope: str) -> Path:
        """Resuelve scope a path físico del archivo"""
        if scope not in self.memory_index.get('scopes', {}):
            raise ValueError(f"Scope '{scope}' no definido en memory_index.yaml")
        return self.project_root / self.memory_index['scopes'][scope]
```

#### 2.2 Validation Layer
```python
class IntegrityValidator:
    """Validación SHA-1 y schemas YAML"""
    
    @staticmethod
    def calculate_sha1(file_path: Path) -> str:
        """Calcula hash SHA-1 de archivo"""
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()
    
    @staticmethod
    def validate_yaml_schema(data: dict, schema_name: str) -> bool:
        """Valida estructura YAML contra schema esperado"""
        # Implementación con pydantic o jsonschema
        pass
    
    def validate_file_integrity(self, scope: str) -> tuple[bool, str]:
        """Valida integridad completa de archivo"""
        file_path = self._get_file_path(scope)
        
        if not file_path.exists():
            return False, f"Archivo {file_path} no existe"
        
        # Validar SHA-1 si está configurado
        expected_hash = self.memory_index['scopes'][scope].get('sha1_hash')
        if expected_hash:
            current_hash = self.calculate_sha1(file_path)
            if current_hash != expected_hash:
                return False, f"SHA-1 mismatch: esperado {expected_hash}, actual {current_hash}"
        
        return True, "Integridad validada"
```

#### 2.3 Transaction Layer
```python
class TransactionManager:
    """Operaciones atómicas con rollback automático"""
    
    def __init__(self, pms_core: PMSCore):
        self.pms = pms_core
        self.transaction_log = []
    
    def begin_transaction(self, scope: str) -> str:
        """Inicia transacción y crea backup"""
        transaction_id = f"txn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        file_path = self.pms._get_file_path(scope)
        backup_path = self.pms.temp_dir / f"{transaction_id}_{scope}.backup"
        
        # Crear backup antes de modificación
        shutil.copy2(file_path, backup_path)
        
        self.transaction_log.append({
            'id': transaction_id,
            'scope': scope,
            'backup_path': backup_path,
            'timestamp': datetime.now(),
            'status': 'active'
        })
        
        return transaction_id
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """Confirma transacción y limpia backup"""
        transaction = self._get_transaction(transaction_id)
        if not transaction:
            return False
        
        # Validar integridad post-modificación
        is_valid, error = self.pms.validate_file_integrity(transaction['scope'])
        if not is_valid:
            # Auto-rollback si falla validación
            self.rollback_transaction(transaction_id)
            raise IntegrityError(f"Commit fallido: {error}")
        
        # Limpiar backup y marcar como committed
        transaction['backup_path'].unlink()
        transaction['status'] = 'committed'
        return True
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """Revierte cambios usando backup"""
        transaction = self._get_transaction(transaction_id)
        if not transaction:
            return False
        
        file_path = self.pms._get_file_path(transaction['scope'])
        backup_path = transaction['backup_path']
        
        # Restaurar desde backup
        shutil.copy2(backup_path, file_path)
        backup_path.unlink()
        
        transaction['status'] = 'rolled_back'
        return True
```

## 3. Modelo de Datos

### Memory Index Schema
```yaml
# memory/memory_index.yaml
project_name: "DevHub"
version: "1.0"
created: "2025-08-09T12:00:00Z"
last_modified: "2025-08-09T12:00:00Z"

scopes:
  blueprint:
    path: "docs/blueprint.yaml"
    type: "yaml"
    sha1_hash: "f0eea832529e16b3d30dd2f34a60d2a8d06f01ec"
    schema: "blueprint_v2"
    
  project_status:
    path: "memory/project_status.md"
    type: "markdown"
    schema: "project_status_v1"
    
  backlog_f1:
    path: "docs/05_backlog/backlog_f1.yaml"
    type: "yaml" 
    schema: "backlog_v1"
    
  backlog_f2:
    path: "docs/05_backlog/backlog_f2.yaml"
    type: "yaml"
    schema: "backlog_v1"

schemas:
  blueprint_v2:
    required_sections: ["arquitectura", "componentes", "decisiones_arquitectonicas"]
    version_format: "semantic"
    
  project_status_v1:
    required_sections: ["current_state", "last_activity", "metrics"]
    
  backlog_v1:
    required_fields: ["tasks", "metadata"]
    task_schema: ["id", "status", "priority", "estimation"]
```

### Project Status Schema  
```yaml
# memory/project_status.md structure
current_state:
  fase_actual: 1
  blueprint_completeness: 0.70
  tasks_completed: 15
  tasks_pending: 8
  last_sync: "2025-08-09T11:48:00Z"

last_activity:
  agent: "BlueprintAgent"
  action: "blueprint.updated"
  timestamp: "2025-08-09T11:48:00Z"
  files_modified: ["docs/blueprint.yaml", "docs/blueprint_changes.csv"]
  
metrics:
  development_velocity: 3.2  # tasks/day
  blueprint_evolution: 0.13  # delta from previous version
  sync_reliability: 0.98     # successful syncs ratio
  
health:
  overall_status: "healthy"  # healthy|warning|critical
  critical_issues: []
  warnings: ["UI component not implemented"]
```

## 4. APIs y Contratos

### Core API Specification
```python
def load(scope: str, project_path: str = None) -> dict:
    """
    Carga datos desde scope especificado con validación de integridad
    
    Args:
        scope: Identificador de scope definido en memory_index.yaml
        project_path: Path opcional para proyectos externos
        
    Returns:
        dict: Datos parseados del archivo
        
    Raises:
        ScopeNotFoundError: Si scope no existe en memory_index
        IntegrityError: Si validación SHA-1 falla
        ParseError: Si estructura YAML/MD inválida
    """

def save(scope: str, data: dict, project_path: str = None) -> bool:
    """
    Guarda datos en scope con transacción atómica y backup automático
    
    Args:
        scope: Identificador de scope
        data: Datos a persistir (dict para YAML, str para Markdown)
        project_path: Path opcional
        
    Returns:
        bool: True si guardado exitoso
        
    Side Effects:
        - Actualiza SHA-1 hash en memory_index
        - Crea entry en transaction log
        - Actualiza timestamp en project_status
    """

def rollback(scope: str, version: str, project_path: str = None) -> bool:
    """
    Revierte scope a versión anterior usando backups
    
    Args:
        scope: Identificador de scope
        version: Version ID o timestamp
        
    Returns:
        bool: True si rollback exitoso
    """
```

## 5. Manejo de Errores

### Exception Hierarchy
```python
class PMSError(Exception):
    """Base exception para PMS operations"""
    pass

class ScopeNotFoundError(PMSError):
    """Scope no definido en memory_index"""
    pass

class IntegrityError(PMSError):
    """Falla validación SHA-1 o schema"""
    pass

class TransactionError(PMSError):
    """Error en operaciones transaccionales"""
    pass

class ParseError(PMSError):
    """Error parsing YAML/Markdown"""
    pass
```

### Error Handling Patterns
```python
def safe_load(scope: str) -> tuple[dict | None, str | None]:
    """Load with error handling - nunca lanza excepciones"""
    try:
        data = load(scope)
        return data, None
    except PMSError as e:
        return None, str(e)

def load_with_fallback(scope: str, fallback_data: dict) -> dict:
    """Load con fallback automático si falla"""
    data, error = safe_load(scope)
    return data if data is not None else fallback_data
```

## 6. Pruebas

### Unit Tests Coverage
- **Core operations**: load/save/rollback - 100% coverage
- **Integrity validation**: SHA-1, schema validation - 100% coverage  
- **Transaction management**: atomic operations, rollback - 100% coverage
- **Error handling**: Exception scenarios - 90% coverage

### Integration Tests
- **End-to-end**: PMS + DAS Enforcer workflow
- **Concurrency**: Multiple agents accessing same scope
- **Filesystem**: Permissions, disk full scenarios
- **Performance**: Large files, many concurrent operations

### Test Data Sets
```python
# tests/fixtures/pms_test_data.py
VALID_BLUEPRINT = {
    "version": "2.2",
    "project_name": "TestProject",
    "arquitectura": {...},
    "componentes": {...}
}

INVALID_BLUEPRINT = {
    "version": "invalid",  # Should trigger schema validation error
    "missing_required_sections": True
}

MEMORY_INDEX_FIXTURE = {
    "scopes": {
        "test_scope": {
            "path": "test_data/test_file.yaml",
            "type": "yaml",
            "schema": "test_v1"
        }
    }
}
```

## 7. Performance y Optimización

### Performance Requirements
- **Load time**: < 100ms para archivos < 1MB
- **Save time**: < 200ms incluyendo validation y backup
- **Memory usage**: < 50MB por instancia PMS
- **Concurrent ops**: Soporte para 5+ agentes simultáneos

### Optimizaciones Implementadas
- **Lazy loading**: Memory index cargado on-demand
- **File caching**: Cache SHA-1 hashes para evitar recálculo
- **Atomic writes**: Write to .tmp + rename para atomicidad
- **Lock management**: File locks para prevenir corruption

### Monitoring Hooks
```python
# Performance monitoring integrado
@performance_monitor
def load(scope: str) -> dict:
    start_time = time.time()
    # ... operación principal
    metrics.record_load_time(scope, time.time() - start_time)
    return result
```