# Persistent Memory System (PMS) v1.2.1

## Especificación Técnica - Arquitectura para Agentes

### Índice
1. [Requisitos del Proyecto](#1-requisitos-del-proyecto)
2. [Archivos de Configuración del Sistema](#2-archivos-de-configuración-del-sistema)
3. [API PMS-Core](#3-api-pms-core)
4. [Principios Técnicos](#4-principios-técnicos)
5. [Particionado de Blueprint](#5-particionado-de-blueprint-proyectos-6-meses)
6. [Health Indicators y Alerts](#6-health-indicators-y-alerts)
7. [Beneficios del Sistema](#7-beneficios-del-sistema)
8. [Checklist PMS-Core](#8-checklist-pms-core)
9. [Glosario](#9-glosario)

---

## 1. Requisitos del Proyecto

Para que un proyecto sea compatible con PMS, debe cumplir los siguientes requisitos obligatorios:

### 1.1 Estructura de Carpetas Obligatoria

```
project-root/
├── memory/
│   ├── memory_index.yaml        # OBLIGATORIO - Configuración central
│   ├── project_status.md        # OBLIGATORIO - Estado actual + métricas
│   └── temp/                    # OBLIGATORIO - Directorio para rollback
│
├── docs/
│   ├── project_charter.md       # RECOMENDADO - Visión del proyecto
│   ├── roadmap.md              # RECOMENDADO - Planificación temporal
│   ├── blueprint.md            # OBLIGATORIO - Estructura específica requerida
│   └── backlog/                # OBLIGATORIO - Backlogs por fase
│       └── backlog_f{n}.yaml  # Generados automáticamente por agentes
```

### 1.2 Requisitos de Formato del Blueprint

El archivo `docs/blueprint.md` DEBE seguir esta estructura exacta:

```markdown
---
version: [número]                # OBLIGATORIO - Control de versiones
changelog: [lista]              # RECOMENDADO - Historial de cambios  
sha1_hash: "[hash]"            # OBLIGATORIO - Validación de integridad
---

# Blueprint del Proyecto

## Fase [N] — [Título de la Fase]
### Épica [N.X] – [Nombre de la Épica]
- US-[N.X.Y]: Como [rol], [descripción de la necesidad]
- US-[N.X.Z]: Como [rol], [descripción de la necesidad]

## Fase [N+1] — [Siguiente Fase]
[...estructura similar...]
```

**Convenciones obligatorias:**
- Fases numeradas consecutivamente: `Fase 1`, `Fase 2`, `Fase 3`...
- Épicas con formato `N.X`: `1.1`, `1.2`, `2.1`, `2.2`...
- User Stories con formato `US-N.X.Y`: `US-1.1.1`, `US-1.2.1`...

**Campos opcionales:**
- `last_modified` (ISO-8601): Marca temporal actualizada automáticamente por PMS-Core

---

## 2. Archivos de Configuración del Sistema

### 2.1 `memory/memory_index.yaml` - Índice Maestro

Configuración central del sistema con rutas y orden de lectura:

```yaml
paths:
  status: "./project_status.md"
  blueprint: "../docs/blueprint.md"
  blueprint_changes: "../docs/blueprint_changes.csv"
  backlog_dir: "../docs/backlog/"
config:
  rollback_dual: true        # transacciones atómicas
  sha_validation: true       # verificación de integridad
  metrics_tracking: true     # seguimiento automático
  expected_hash: ""          # hash SHA-1 esperado del blueprint
```

**Template completo:** `/templates/memory_index.yaml`

### 2.2 `memory/project_status.md` - Estado + Métricas

Estado actual del proyecto con métricas integradas y log cronológico:

```yaml
current_state:
  fase_actual: 1
  ultima_tarea_id: "T-1.2.3b"
  metricas:
    total_tareas: 15
    completadas: 8
    velocidad_sprint: 4.2
    porcentaje_completado: 53.3
```

```markdown
## Registro de Cambios
### 2025-07-25 14:30 - Sprint 2 completado
- Tareas completadas: T-1.2.1a, T-1.2.2b
- Métricas: Velocidad actual 4.2
```

**Template completo:** `/templates/project_status.md`

### 2.3 `docs/blueprint.md` - Blueprint Evolutivo

Fuente de verdad estratégica con fases, épicas y user stories:

```markdown
---
version: 1.2
last_modified: 2025-07-28T14:30:00Z  # ISO-8601, actualizado automáticamente por PMS-Core
changelog:
  - "Ejemplo: Añadida épica de seguridad"
  - "Ejemplo: Refinada épica base"
sha1_hash: "a94f2b8c3e7d1f9e2a5b6c8d4e9f1a2b3c7d8e9f"
---

# Blueprint del Proyecto

## Fase 1 — Configuración inicial
### Épica 1.1 – Entorno de desarrollo
- US-1.1.1: Como dev, quiero configurar el repo Git
- US-1.1.2: Como dev, necesito instalar dependencias

### Épica 1.2 – Estructura base
- US-1.2.1: Como PM, quiero directorios principales
- US-1.2.2: Como PM, deseo documentación inicial
```

**Template completo:** `/templates/blueprint.md`

### 2.4 `docs/backlog/backlog_f1.yaml` - Backlog con Criticidad

Tareas operativas por fase con estados y criticidad:

```yaml
fase: 1
sprint: 2
historias:
  US-1.2.1:
    estado: P          # P = In-Progress
    tareas:
      - id: T-1.2.1a
        desc: "Crear estructura de directorios"
        estado: C
        criticidad: medium
        
      - id: T-1.2.1b
        desc: "Configurar paths"
        estado: P
        criticidad: low
        subtasks:
          - id: ST-1
            desc: "Crear formulario"
            estado: C
```

**Template completo:** `/templates/backlog_f1.yaml`

### 2.5 `docs/blueprint_changes.csv` - Propuestas de Cambio

Sistema colaborativo para proponer modificaciones al blueprint:

```csv
id,author,timestamp,description,status
1,DevAgent,2025-07-28T14:22Z,"Añadir US-1.3.1 para configuración CI/CD",proposed
2,QAAgent,2025-07-28T15:10Z,"Modificar criterios aceptación US-2.1.1",reviewed
3,PMAgent,2025-07-28T16:05Z,"Nueva épica 3.3 - Monitoreo sistema",approved
```

**Estados del flujo:**
- `proposed`: Propuesta inicial por cualquier agente
- `reviewed`: Validada técnicamente por BluePrintAgent
- `approved`: Aprobada por humano (PO/PM)
- `merged`: Fusionada al blueprint por BluePrintAgent

**Template completo:** `/templates/blueprint_changes.csv`

---

## 3. API PMS-Core

### 3.1 Funciones Principales

```python
# Cargar datos por scope
data = pms_core.load(scope="blueprint")
data = pms_core.load(scope="backlog_f1") 
data = pms_core.load(scope="project_status")

# Guardar con rollback
pms_core.save(scope="blueprint", payload=data, mode="update_dual")
pms_core.save(scope="project_status", payload=metrics, mode="update_single")

# Métricas automáticas
metrics = pms_core.metrics()
```

### 3.2 Contratos del Sistema

#### API pms-core (Funciones universales)
- `load(scope)` → Carga archivos en memoria según scope
- `save(scope, payload, mode)` → Guarda con flujo adaptativo + rollback
- `metrics()` → Expone métricas estándar (burndown, health)

#### Tipos de Flujo
- **read_only**: Solo lectura, sin modificaciones
- **update_single**: Escribe un archivo con validaciones básicas  
- **update_dual**: Rollback dual atómico para cambios críticos

#### Control de Concurrencia
- Uso de archivos `.lock` para operaciones atómicas
- Patrón `.tmp` → `rename()` para atomicidad (archivos temporales en `memory/temp/`)
- Validación SHA-1 opcional para detectar cambios externos

---


## 4. Principios Técnicos

> **"Robustez por defecto, simplicidad en la interfaz, visibilidad siempre"**

### 4.1 Robustez por Defecto
- **Rollback dual atómico** - Transacciones que garantizan consistencia de datos
- **Validación SHA-1** - Detección automática de cambios externos al blueprint
- **Sistema de locks** - Prevención de corrupción por operaciones concurrentes

### 4.2 Simplicidad en la Interfaz
- **Templates estandarizados** - Formatos predefinidos para todos los archivos
- **Estados unificados** - Solo 4 estados posibles (C/P/B/F)
- **Configuración centralizada** - Un solo archivo de índice maestro

### 4.3 Visibilidad Siempre
- **Métricas automáticas** - Burndown y health tracking sin configuración
- **Log cronológico** - Trazabilidad completa de decisiones y cambios
- **Separación clara** - Documentos humanos vs operativos de agentes

### 4.4 Arquitectura Agnóstica
- **Framework neutral** - No asume roles específicos de agentes
- **Configuración flexible** - Cada agente define qué lee/escribe según responsabilidades
- **Contratos claros** - API consistente independiente del tipo de agente

---

## 5. Particionado de Blueprint (Proyectos >6 meses)

### 5.1 Estructura Opcional
```
docs/
├── blueprint.md          # Índice general + roadmap
├── backlog/             # Backlogs operativos por fase
│   └── backlog_f{n}.yaml
├── phases/
│   ├── phase_1.md       # Detalle fase 1
│   ├── phase_2.md       # Detalle fase 2
│   └── phase_N.md
```

### 5.2 `docs/blueprint.md` (Índice)
```markdown
# Blueprint del Proyecto - Índice General

## Roadmap de Fases
- **Fase 1**: Configuración inicial → [Ver detalle](phases/phase_1.md)
- **Fase 2**: Módulo núcleo → [Ver detalle](phases/phase_2.md)
- **Fase 3**: Integración → [Ver detalle](phases/phase_3.md)

## Métricas Globales
- Duración estimada: 6 meses
- Total de épicas: 12
- Total user stories estimadas: 48
```

### 5.3 `docs/phases/phase_1.md` (Detalle)
```markdown
---
phase: 1
version: 1.1
parent_blueprint: "../blueprint.md"
---

# Fase 1 - Configuración Inicial

## Épica 1.1 – Entorno de desarrollo
[contenido detallado...]

## Épica 1.2 – Estructura base
[contenido detallado...]
```

---

## 6. Health Indicators y Alerts

### 6.1 Métricas de Salud Automáticas

```yaml
# En project_status.md
health_alerts:
  - type: "high_blocked_ratio"
    threshold: 20    # % tareas bloqueadas
    current: 13.3
    status: "ok"
    
  - type: "low_velocity"  
    threshold: 3.0   # tareas/sprint mínimo
    current: 4.2
    status: "ok"
    
  - type: "sprint_overrun"
    threshold: 1.2   # 20% sobrepaso del sprint
    current: 1.0
    status: "ok"
```

### 6.2 Auto-Alertas del Sistema
- **Red**: >30% tareas bloqueadas o velocidad <50% objetivo
- **Yellow**: 15-30% bloqueadas o velocidad 50-80% objetivo  
- **Green**: <15% bloqueadas y velocidad >80% objetivo

---

## 7. Beneficios del Sistema

### 7.1 **Beneficios Clave**
- **Operación robusta**: Sistema unificado con rollback atómico
- **Flexibilidad**: Blueprint evolutivo con control de cambios
- **Escalabilidad**: Particionado opcional para proyectos grandes
- **Confiabilidad**: Sistema robusto de validaciones y rollback
- **Observabilidad**: Métricas de burndown y health tracking integradas

### 7.2 **Nuevas Capacidades**
- **Burndown automático**: Visualización de progreso sin overhead
- **Health monitoring**: Detección temprana de problemas  
- **Escalabilidad robusta**: Particionado opcional para proyectos grandes
- **Evolutividad**: Blueprint puede cambiar sin romper el sistema
- **Observabilidad**: Métricas y alertas integradas


---

## 8. Checklist PMS-Core

### 8.1 Preparación del Proyecto
- [ ] Crear estructura de carpetas obligatoria (`memory/`, `docs/`, `docs/backlog/`)
- [ ] Crear directorio `memory/temp/` para rollback
- [ ] Configurar `.gitignore` para ignorar archivos temporales (`.lock`, `temp/`, `*.tmp`)

### 8.2 Configuración Inicial
- [ ] Crear `memory/memory_index.yaml` basado en template
- [ ] Crear `memory/project_status.md` con estado inicial
- [ ] Crear `docs/blueprint.md` con formato obligatorio
- [ ] Crear `docs/blueprint_changes.csv` con headers

### 8.3 Validación de Requisitos
- [ ] Verificar formato de headers YAML en blueprint
- [ ] Verificar numeración correcta de fases (`Fase 1`, `Fase 2`...)
- [ ] Verificar formato de épicas (`1.1`, `1.2`, `2.1`...)
- [ ] Verificar formato de user stories (`US-1.1.1`, `US-1.2.1`...)

### 8.4 Pruebas del Sistema PMS
- [ ] Ejecutar ciclo completo: `pms_core.load(scope="blueprint")` → modificación → `save(scope="blueprint", payload=data, mode="update_dual")`
- [ ] Verificar generación automática de métricas
- [ ] Validar integridad de archivos tras operaciones
- [ ] Probar rollback dual con archivos temporales

---

## 9. Glosario

### Términos de Arquitectura
- **Orchestration Layer**: Capa 1 que define el flow de agentes, orden y dependencias (CrewAI, LangGraph, etc.)
- **Agent Service**: Capa 2 con lógica de dominio específica de cada agente (BluePrintAgent, DevAgent, etc.)
- **PMS-Core**: Capa 3 que proporciona persistencia, rollback dual, validación SHA-1 e integridad de datos
- **Storage Layer**: Capa 4 con drivers de almacenamiento (filesystem, DB, Git, S3, etc.)

### Términos de Flujo
- **Flow**: Orquestación de agentes que define qué agente ejecuta cuándo, sin tocar archivos directamente
- **Scope**: Identificador de recurso en PMS-Core (`"blueprint"`, `"backlog_f1"`, `"project_status"`)
- **Mode**: Tipo de operación de guardado (`"read_only"`, `"update_single"`, `"update_dual"`)

### Términos de Datos
- **Blueprint**: Documento estratégico con fases, épicas y user stories; solo modificable por BluePrintAgent
- **Backlog**: Documentos operativos por fase con tareas ejecutables y estados
- **Memory Index**: Archivo maestro `memory_index.yaml` que define rutas y configuración del sistema

---

## Changelog

### v1.2.1 - 2025-07-28
- **Plantillas alineadas con spec**: añadido `blueprint_changes`, `expected_hash`; retirado `read_order`
- **Documentado `last_modified`** como campo opcional (ISO-8601, actualizado automáticamente por PMS-Core)
- **Separación Flow vs PMS**: contenido de orquestación movido a `../agents/agents.md`
- **Estructura limpia**: PMS enfocado exclusivamente en persistencia

---

**Estado**: ✅ Especificación técnica completa • Implementación validada