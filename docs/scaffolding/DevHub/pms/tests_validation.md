# PMS-Core - Tests de Validación v1.2.1

## Criterios de Aceptación

### 1. API Core Functions

#### 1.1 `pms_core.load(scope)`
**Entrada**: scope string (`"blueprint"`, `"backlog_f1"`, `"project_status"`)  
**Salida**: objeto parsed (dict/object) o excepción

| Test Case | Scope | Fixtures | Resultado Esperado |
|-----------|-------|----------|-------------------|
| `test_load_blueprint_valid` | `"blueprint"` | `docs/blueprint.md` válido | Dict con `version`, `changelog`, `sha1_hash`, contenido |
| `test_load_blueprint_missing` | `"blueprint"` | Archivo no existe | `FileNotFoundError` |
| `test_load_blueprint_corrupted` | `"blueprint"` | YAML header malformado | `ValidationError` |
| `test_load_backlog_valid` | `"backlog_f1"` | `docs/backlog/backlog_f1.yaml` válido | Dict con `fase`, `sprint`, `historias` |
| `test_load_project_status` | `"project_status"` | `memory/project_status.md` válido | Dict con `current_state`, `metricas` |
| `test_load_invalid_scope` | `"invalid_scope"` | - | `ValueError("Unknown scope")` |

#### 1.2 `pms_core.save(scope, payload, mode)`
**Entrada**: scope, data dict, mode (`"update_single"`, `"update_dual"`)  
**Salida**: success boolean o excepción

| Test Case | Scope | Mode | Fixtures | Resultado Esperado |
|-----------|-------|------|----------|-------------------|
| `test_save_blueprint_update_dual` | `"blueprint"` | `"update_dual"` | Data válida | Archivo actualizado + SHA-1 recalculado + `last_modified` auto-fill |
| `test_save_blueprint_concurrent` | `"blueprint"` | `"update_dual"` | 2 procesos simultáneos | Segundo proceso espera lock, ambos exitosos |
| `test_save_project_status_single` | `"project_status"` | `"update_single"` | Métricas actualizadas | Archivo actualizado directamente |
| `test_save_rollback_failure` | `"blueprint"` | `"update_dual"` | Falla durante write | Rollback automático, archivo original intacto |

### 2. SHA-1 Validation

#### 2.1 Cálculo y Verificación
**Fixtures**: `docs/blueprint.md` con contenido conocido

| Test Case | Escenario | Entrada | Resultado Esperado |
|-----------|-----------|---------|-------------------|
| `test_sha1_calculation` | Contenido fijo | Blueprint estático | SHA-1 específico (ej: `"a94f2b8c..."`) |
| `test_sha1_validation_match` | Hash coincide | `expected_hash` = hash real | `load()` exitoso |
| `test_sha1_validation_mismatch` | Hash no coincide | `expected_hash` ≠ hash real | `IntegrityError` |
| `test_sha1_update_on_save` | Modificación blueprint | `save(mode="update_dual")` | Nuevo SHA-1 en header + `memory_index.yaml` |

#### 2.2 Casos Límite
| Test Case | Escenario | Resultado Esperado |
|-----------|-----------|-------------------|
| `test_sha1_empty_file` | Archivo vacío | SHA-1 de string vacío |
| `test_sha1_unicode_content` | Contenido UTF-8/emojis | SHA-1 correcto con encoding |
| `test_sha1_large_file` | Blueprint >1MB | SHA-1 calculado sin memory issues |

### 3. Rollback Dual Atómico

#### 3.1 Flujo Normal
**Setup**: Directorio `memory/temp/` existe, permisos correctos

| Test Case | Escenario | Pasos | Resultado Esperado |
|-----------|-----------|-------|-------------------|
| `test_rollback_dual_success` | Save exitoso | 1) Create `.tmp` 2) Write data 3) Validate 4) `rename()` | Archivo final correcto, no `.tmp` residual |
| `test_rollback_dual_failure_write` | Error en write | 1) Create `.tmp` 2) **Falla write** | Archivo original intacto, `.tmp` limpiado |
| `test_rollback_dual_failure_validate` | Error en validación | 1) Write `.tmp` 2) **Falla validation** | Archivo original intacto, `.tmp` limpiado |

#### 3.2 Concurrencia
| Test Case | Escenario | Resultado Esperado |
|-----------|-----------|-------------------|
| `test_concurrent_save_lock` | 2 procesos `save()` simultáneos | Segundo espera lock, ambos exitosos secuencialmente |
| `test_lock_timeout` | Lock bloqueado >30s | `TimeoutError` en segundo proceso |
| `test_stale_lock_cleanup` | Lock file huérfano | Auto-cleanup si proceso muerto |

### 4. Auto-fill `last_modified`

#### 4.1 Timestamp Management
| Test Case | Input | Resultado Esperado |
|-----------|-------|-------------------|
| `test_last_modified_autofill` | Blueprint sin `last_modified` | Campo añadido con timestamp ISO-8601 actual |
| `test_last_modified_update` | Blueprint con `last_modified` viejo | Campo actualizado a timestamp actual |
| `test_last_modified_format` | - | Formato exacto: `2025-07-28T14:30:00Z` |

#### 4.2 Timezone Handling
| Test Case | Escenario | Resultado Esperado |
|-----------|-----------|-------------------|
| `test_timezone_utc` | Sistema en cualquier TZ | `last_modified` siempre en UTC (Z suffix) |
| `test_timestamp_precision` | - | Precisión de segundos (no microsegundos) |

### 5. File System Integration

#### 5.1 Path Resolution
**Setup**: Directorio DevHub con estructura estándar

| Test Case | Scope | Path Esperado | Validación |
|-----------|-------|---------------|-----------|
| `test_path_resolution_blueprint` | `"blueprint"` | `../docs/blueprint.md` (relativo a `memory/`) | Archivo encontrado |
| `test_path_resolution_backlog` | `"backlog_f2"` | `../docs/backlog/backlog_f2.yaml` | Archivo encontrado |
| `test_path_absolute_fallback` | Cualquier scope | Path absoluto si relativo falla | Archivo encontrado |

#### 5.2 Error Handling
| Test Case | Escenario | Resultado Esperado |
|-----------|-----------|-------------------|
| `test_permission_denied` | Sin permisos write | `PermissionError` con mensaje claro |
| `test_disk_full` | Disco lleno durante write | `IOError` + rollback automático |
| `test_directory_missing` | `memory/temp/` no existe | Auto-creación de directorio |

### 6. Integration Tests

#### 6.1 End-to-End Workflow
**Fixture**: Proyecto DevHub completo con templates poblados

```python
def test_e2e_blueprint_modification():
    # 1. Load blueprint
    blueprint = pms_core.load("blueprint")
    original_hash = blueprint['sha1_hash']
    
    # 2. Modify content
    blueprint['phases'][0]['epics'].append({
        'id': '1.4',
        'title': 'Nueva épica test',
        'user_stories': ['US-1.4.1: Como test, quiero...']
    })
    
    # 3. Save with dual rollback
    result = pms_core.save("blueprint", blueprint, mode="update_dual")
    
    # 4. Verify persistence
    reloaded = pms_core.load("blueprint")
    assert reloaded['sha1_hash'] != original_hash
    assert 'Nueva épica test' in str(reloaded)
    assert reloaded['last_modified'] > original_timestamp
```

#### 6.2 Multi-Agent Simulation
```python
def test_concurrent_agents():
    # DevAgent modifica backlog
    # BluePrintAgent modifica blueprint  
    # PMAgent lee project_status
    # Todos simultáneamente sin corrupción
```

### 7. Performance Tests

| Test Case | Escenario | Baseline Esperado |
|-----------|-----------|-------------------|
| `test_load_performance` | Blueprint 100KB | < 50ms |
| `test_save_performance` | Blueprint 100KB | < 200ms (incluye SHA-1) |
| `test_concurrent_load` | 10 loads simultáneos | < 100ms cada uno |

---

## Test Data Fixtures

### `fixtures/blueprint_valid.md`
```markdown
---
version: 1.0
changelog: ["Initial version"]
sha1_hash: "da39a3ee5e6b4b0d3255bfef95601890afd80709"
---
# Blueprint Test
## Fase 1 — Test
### Épica 1.1 – Test Epic
- US-1.1.1: Como test, quiero validar el sistema
```

### `fixtures/memory_index_valid.yaml`
```yaml
paths:
  status: "./project_status.md"
  blueprint: "../docs/blueprint.md"
  blueprint_changes: "../docs/blueprint_changes.csv"
  backlog_dir: "../docs/backlog/"
config:
  rollback_dual: true
  sha_validation: true
  metrics_tracking: true
  expected_hash: "da39a3ee5e6b4b0d3255bfef95601890afd80709"
```

### `fixtures/backlog_f1_valid.yaml`
```yaml
fase: 1
sprint: 1
historias:
  US-1.1.1:
    estado: P
    tareas:
      - id: T-1.1.1a
        desc: "Test task"
        estado: C
        criticidad: medium
```

---

**Total**: 35+ test cases cubriendo funcionalidad core, casos límite y integración.  
**Coverage objetivo**: >95% de líneas de código en `pms_core`.