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

## Modo Agente Específico (Cuando se Invoca)

Cuando el usuario solicite actuar como otro agente específico (BluePrintAgent, QAAgent, etc.):

### 1. Cargar System Prompt del Agente
```bash
# Leer configuración desde memory_index.yaml
python -c "
import yaml
with open('memory/memory_index.yaml') as f:
    idx = yaml.safe_load(f)

# Mapeo de nombres comunes a claves del índice
agent_mappings = {
    'blueprintagent': 'blueprint_agent',
    'devagent': 'dev_agent', 
    'qaagent': 'qa_agent',
    'aiprojectmanager': 'ai_project_manager'
}

requested_agent = '{agent_name}'.lower()
agent_key = agent_mappings.get(requested_agent, requested_agent)

if agent_key in idx['agents']:
    agent_path = idx['agents'][agent_key]
    with open(agent_path) as f:
        agent_config = yaml.safe_load(f)
    print(f'✅ Configuración cargada para: {agent_key}')
    print(f'Archivo: {agent_path}')
else:
    print(f'❌ Agente no encontrado: {agent_key}')
    print(f'Agentes disponibles: {list(idx[\"agents\"].keys())}')
"
```

### 2. Verificar Sistema DAS Operativo
```python
python -c "from das.enforcer import validate_agent_config; print('✅ {AgentName} permisos:', validate_agent_config('{AgentName}'))"
```

### 3. API Obligatoria - SIEMPRE Usar DAS Enforcer
```python
# ✅ CORRECTO - Con enforcement técnico específico del agente
from das.enforcer import agent_load, agent_save

# Usar el nombre del agente específico
data = agent_load("{AgentName}", "scope_permitido")
agent_save("{AgentName}", "scope_permitido", updated_data)

# ❌ PROHIBIDO - Acceso directo sin enforcement  
import pms_core
pms_core.load("scope")  # NO usar directamente
```

### 4. Workflow Genérico para Cualquier Agente
```python
from das.enforcer import agent_load, agent_save

# 1. Validar permisos del agente antes de proceder
try:
    permissions = validate_agent_config("{AgentName}")
    print(f"Permisos validados para {AgentName}")
except Exception as e:
    print(f"Error de configuración: {e}")
    return

# 2. Leer configuración y contexto según permisos
if "project_status" in permissions['read_scopes']:
    status = agent_load("{AgentName}", "project_status")

if "blueprint" in permissions['read_scopes']:
    blueprint = agent_load("{AgentName}", "blueprint")

# 3. Ejecutar workflow específico del agente
# (Aquí va la lógica específica según el tipo de agente)

# 4. Guardar resultados según permisos de escritura
for scope in permissions['write_scopes']:
    if updated_data_for_scope:
        agent_save("{AgentName}", scope, updated_data_for_scope)
```

### 5. Placeholders a Reemplazar
Cuando actúes como agente específico, reemplaza estos placeholders:
- `{agent_name}` → nombre en minúsculas (ej: "blueprintagent")
- `{AgentName}` → nombre normalizado (ej: "BluePrintAgent") 
- `{agent_key}` → clave en memory_index.yaml (ej: "blueprint_agent")

---

## Referencia Rápida de Agentes

### BluePrintAgent
- **Único** autorizado para editar `blueprint.md`
- Procesa propuestas de `blueprint_changes.csv`
- Gestiona versionado y changelog

### QAAgent  
- Valida criterios de aceptación
- Ejecuta tests automáticos
- Propone mejoras de calidad

### AiProjectManager
- Gestiona visión general del proyecto
- Coordina flujo entre documentos
- Solo lectura de Blueprint y Backlogs

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