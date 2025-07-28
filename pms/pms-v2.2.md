# Persistent Memory System (PMS) v2.2

## Especificación Técnica - Arquitectura para Agentes

---

## 1. Requisitos del Proyecto

Para que un proyecto sea compatible con PMS v2.2, debe cumplir los siguientes requisitos obligatorios:

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

---

## 2. Archivos de Configuración del Sistema

### 2.1 `memory/memory_index.yaml` - Índice Maestro

Configuración central del sistema con rutas y orden de lectura:

```yaml
paths:
  status: "./project_status.md"
  blueprint: "../docs/blueprint.md"
  backlog_dir: "../docs/backlog/"
config:
  rollback_dual: true        # transacciones atómicas
  sha_validation: true       # verificación de integridad
  metrics_tracking: true     # seguimiento automático
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

---

## 3. Arquitectura Multi-Agente

### 3.1 BluePrintAgent - Gestor Exclusivo de Blueprint

**Rol único:**
- Único agente autorizado para modificar `docs/blueprint.md`
- Control exclusivo de estructura del blueprint
- Control exclusivo de versionado del blueprint
- Control exclusivo de changelog del blueprint

**Responsabilidades específicas:**
- Mantener formato obligatorio `Fase N → Épica N.X → US-N.X.Y`
- Gestionar versionado SHA-1 del blueprint
- Gestionar changelog automático
- Validar formato antes de guardar
- Actualizar `memory/project_status.md`

**Integración con PMS:**
- Lee `docs/project_charter.md`
- Lee `docs/roadmap.md` 
- Lee `memory/memory_index.yaml`
- Produce `docs/blueprint.md` con formato estricto PMS v2.2
- Usa flujo `read_only` → `update_single`
- Registra cambios en `memory/project_status.md`

**Contenido del blueprint:**
- Fases numeradas consecutivamente
- Épicas con formato N.X por fase
- User Stories con formato US-N.X.Y por épica
- Headers YAML obligatorios (version, changelog, sha1_hash)

### 3.2 Contratos del Sistema

#### API pms-core (Funciones universales)
- `load(paths, scope)` → Carga archivos en memoria según scope del agente
- `save(scope, data, flow_type)` → Guarda con flujo adaptativo + rollback
- `metrics()` → Expone métricas estándar (burndown, health)

#### Tipos de Flujo (Cualquier agente puede usar)
- **read_only**: Solo lectura, sin modificaciones
- **update_single**: Escribe un archivo con validaciones básicas  
- **update_dual**: Rollback dual atómico para cambios críticos

#### Control de Concurrencia
- Uso de archivos `.lock` para operaciones atómicas
- Patrón `.tmp` → `rename()` para atomicidad
- Validación SHA-1 opcional para detectar cambios externos

---

## 4. Flujo de Trabajo Unificado

### 4.1 CARGAR CONFIGURACIÓN
- Leer `memory/memory_index.yaml` → obtener rutas y configuración

### 4.2 EVALUAR ESTADO ACTUAL + MÉTRICAS
- Leer `memory/project_status.md` → detectar `fase_actual` y métricas
- **Burndown check**: ¿estamos en ritmo según `velocidad_sprint`?
- **Health check**: ¿hay demasiadas tareas bloqueadas?

### 4.3 CARGAR CONTEXTO ESTRATÉGICO
- Leer documentos según `read_order`
- Validar hash del blueprint (siempre habilitado)

### 4.4 SELECCIONAR TAREA
- Identificar siguiente tarea con `estado ≠ C`
- **Priorizar por criticidad**: high → medium → low

### 4.5 FLUJO DE EJECUCIÓN

```
┌─ TODAS LAS OPERACIONES ───────────────┐
│ • Ejecutar tarea                      │
│ • Crear archivos .tmp                 │
│ • Validar consistencia               │
│ • Rollback dual atómico              │
│ • Commit git                          │
└───────────────────────────────────────┘

*Nota: Todas las tareas usan rollback atómico dual*
```

### 4.6 ACTUALIZAR MÉTRICAS AUTOMÁTICAMENTE
- Recalcular contadores por estado
- Actualizar `velocidad_sprint` si completó sprint
- Detectar health alerts (ej: >20% bloqueadas)

---

## 5. Principios Técnicos

> **"Robustez por defecto, simplicidad en la interfaz, visibilidad siempre"**

### 5.1 Robustez por Defecto
- **Rollback dual atómico** - Transacciones que garantizan consistencia de datos
- **Validación SHA-1** - Detección automática de cambios externos al blueprint
- **Sistema de locks** - Prevención de corrupción por operaciones concurrentes

### 5.2 Simplicidad en la Interfaz
- **Templates estandarizados** - Formatos predefinidos para todos los archivos
- **Estados unificados** - Solo 4 estados posibles (C/P/B/F)
- **Configuración centralizada** - Un solo archivo de índice maestro

### 5.3 Visibilidad Siempre
- **Métricas automáticas** - Burndown y health tracking sin configuración
- **Log cronológico** - Trazabilidad completa de decisiones y cambios
- **Separación clara** - Documentos humanos vs operativos de agentes

### 5.4 Arquitectura Agnóstica
- **Framework neutral** - No asume roles específicos de agentes
- **Configuración flexible** - Cada agente define qué lee/escribe según responsabilidades
- **Contratos claros** - API consistente independiente del tipo de agente

---

## 6. Particionado de Blueprint (Proyectos >6 meses)

### 6.1 Estructura Opcional
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

### 6.2 `docs/blueprint.md` (Índice)
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

### 6.3 `docs/phases/phase_1.md` (Detalle)
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

## 7. Health Indicators y Alerts

### 7.1 Métricas de Salud Automáticas

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

### 7.2 Auto-Alertas del Sistema
- **Red**: >30% tareas bloqueadas o velocidad <50% objetivo
- **Yellow**: 15-30% bloqueadas o velocidad 50-80% objetivo  
- **Green**: <15% bloqueadas y velocidad >80% objetivo

---

## 8. Beneficios del Sistema

### 8.1 **Beneficios Clave**
- **Operación robusta**: Sistema unificado con rollback atómico
- **Flexibilidad**: Blueprint evolutivo con control de cambios
- **Escalabilidad**: Particionado opcional para proyectos grandes
- **Confiabilidad**: Sistema robusto de validaciones y rollback
- **Observabilidad**: Métricas de burndown y health tracking integradas

### 8.2 **Nuevas Capacidades**
- **Burndown automático**: Visualización de progreso sin overhead
- **Health monitoring**: Detección temprana de problemas  
- **Escalabilidad robusta**: Particionado opcional para proyectos grandes
- **Evolutividad**: Blueprint puede cambiar sin romper el sistema
- **Observabilidad**: Métricas y alertas integradas


---

## 9. Checklist de Implementación

### 9.1 Preparación del Proyecto
- [ ] Crear estructura de carpetas obligatoria (`memory/`, `docs/`, `docs/backlog/`)
- [ ] Crear directorio `memory/temp/` para rollback
- [ ] Configurar `.gitignore` para ignorar archivos temporales

### 9.2 Configuración Inicial
- [ ] Crear `memory/memory_index.yaml` basado en template
- [ ] Crear `memory/project_status.md` con estado inicial
- [ ] Crear `docs/blueprint.md` con formato obligatorio

### 9.3 Validación de Requisitos
- [ ] Verificar formato de headers YAML en blueprint
- [ ] Verificar numeración correcta de fases (`Fase 1`, `Fase 2`...)
- [ ] Verificar formato de épicas (`1.1`, `1.2`, `2.1`...)
- [ ] Verificar formato de user stories (`US-1.1.1`, `US-1.2.1`...)

### 9.4 Configuración de Agentes
- [ ] Configurar system prompt del DevAgent con lectura PMS
- [ ] Configurar validación SHA-1 del blueprint
- [ ] Probar flujo de rollback dual con archivos temporales

### 9.5 Pruebas del Sistema
- [ ] Ejecutar ciclo completo: lectura → modificación → rollback
- [ ] Verificar generación automática de métricas
- [ ] Validar integridad de archivos tras operaciones

---

**Estado**: ✅ Especificación técnica completa • Implementación validada