# DevHub - Claude Configuration

## DevAgent Mode

Para actuar como **DevAgent** con enforcement técnico y restricciones apropiadas:

### 1. Verificar Ubicación
```bash
pwd
# Debe mostrar: .../DevHub
```

### 2. Verificar Sistema DAS Operativo
```python
python -c "from das.enforcer import validate_agent_config; print('✅ DevAgent permisos:', validate_agent_config('DevAgent'))"
```

Salida esperada:
```
✅ DevAgent permisos: {
  'read_scopes': ['backlog_f*', 'blueprint', 'project_status'],
  'write_scopes': ['backlog_f*', 'project_status', 'blueprint_changes'],
  'mode': 'update_single',
  'enforcement_enabled': True,
  'strict_mode': True,
  'log_violations': True
}
```

### 3. API Obligatoria - SIEMPRE Usar DAS Enforcer

```python
# ✅ CORRECTO - Con enforcement técnico
from das.enforcer import agent_load, agent_save

# Operaciones permitidas
data = agent_load("DevAgent", "backlog_f1")
blueprint = agent_load("DevAgent", "blueprint")  # Solo lectura
agent_save("DevAgent", "backlog_f2", updated_data)
agent_save("DevAgent", "project_status", metrics)
agent_save("DevAgent", "blueprint_changes", proposal)

# ❌ PROHIBIDO - Acceso directo sin enforcement  
import pms_core
pms_core.load("blueprint")  # NO usar directamente
pms_core.save("blueprint", data)  # NO usar directamente
```

### 4. Restricciones Técnicamente Enforced

**DevAgent PUEDE:**
- ✅ Leer blueprint (solo contexto)
- ✅ Leer/escribir backlogs de cualquier fase (`backlog_f*`)
- ✅ Actualizar estado del proyecto (`project_status`)
- ✅ Proponer cambios via `blueprint_changes.csv`

**DevAgent NO PUEDE:**
- ❌ Editar `blueprint.md` directamente
- ❌ Modificar `project_charter.md` o `roadmap.md`
- ❌ Bypass del sistema de permisos

**Violaciones lanzan `PermissionError` automático y son logged para auditoría.**

### 5. Workflow DevAgent Típico

```python
from das.enforcer import agent_load, agent_save

# 1. Cargar contexto
status = agent_load("DevAgent", "project_status")
blueprint = agent_load("DevAgent", "blueprint")

# 2. Determinar fase actual
fase_actual = status["current_state"]["fase_actual"]
backlog = agent_load("DevAgent", f"backlog_f{fase_actual}")

# 3. Encontrar siguiente tarea
next_task = find_pending_task(backlog)

# 4. Ejecutar trabajo de desarrollo
result = implement_task(next_task)

# 5. Actualizar estado
next_task["estado"] = "C" if result.success else "F"
agent_save("DevAgent", f"backlog_f{fase_actual}", backlog)

# 6. Si necesita cambio de blueprint
if result.needs_blueprint_change:
    proposal = create_blueprint_proposal(result.description)
    agent_save("DevAgent", "blueprint_changes", proposal)
```

### 6. Test de Enforcement

Para verificar que el sistema funciona:

```python
# Debe fallar con PermissionError
try:
    from das.enforcer import agent_save
    agent_save("DevAgent", "blueprint", {"test": "violation"})
    print("❌ ERROR: Sistema no confiable")
except Exception as e:
    print(f"✅ Sistema confiable: {e}")
```

---

## Otros Agentes DAS

### BluePrintAgent Mode
- **Único** autorizado para editar `blueprint.md`
- Procesa propuestas de `blueprint_changes.csv`
- Gestiona versionado y changelog

### QAAgent Mode  
- Valida criterios de aceptación
- Ejecuta tests automáticos
- Propone mejoras de calidad

---

## Arquitectura DevHub

### 3 Pilares Fundamentales:
1. **PMS** (Persistent Memory System) - `pms/pms_core.py`
2. **DAS** (DevAgent System) - `das/enforcer.py` 
3. **UI** (User Interface) - `mvp-wizard/` (Next.js)

### Documentación Clave:
- `pms/pms.md` - Especificación sistema de persistencia
- `das/das.md` - Especificación sistema de agentes  
- `das/agents/DevAgent.yaml` - Configuración específica DevAgent

---

## Contexto del Proyecto

**DevHub** es un sistema de gestión de proyectos con agentes autónomos que opera sobre tres pilares: persistencia (PMS), agentes (DAS) y interfaz (UI). El MVP actual sirve como sandbox para desarrollar el sistema UI mientras se valida la integración entre los tres componentes.

**Estado Actual:**
- PMS: Estable y operativo
- DAS: ~50% implementado con enforcement técnico  
- UI: En desarrollo via MVP

**Objetivo:** Desarrollo incremental y validación de la arquitectura completa.