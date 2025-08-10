# DevHub - Gestión de Backlogs

## Índice de Fases

### Fase 0: Consolidación Documental P1
**Estado**: Pendiente  
**Objetivo**: Resolver fragmentación documental integrando archivos sueltos a secciones canónicas  
**Archivo**: [`backlog_f0.yaml`](05_backlog/backlog_f0.yaml)

**Gap crítico identificado**: Workflow paso 4 "TechSpec (módulo)" sin agente responsable definido.

**Tareas principales**:
- ⏳ **P1-DEVAGENT-001**: Expandir DevAgent (responsabilidades en `das/das.md` + capabilities en `agents/DevAgent.yaml`)
- ⏳ **P1-DEVAGENT-002**: Eliminar archivo redundante `DevAgent_BP_to_TS_Expansion.md`
- ⏳ **P1-VALIDACION-003**: Validar completitud workflow Blueprint→TechSpecs

**Resultado esperado**: DevAgent formalmente responsable de Blueprint→TechSpecs con capabilities técnicas.

---

### Fase 1: Implementación Core Components
**Estado**: Planificado  
**Objetivo**: Desarrollar componentes fundamentales PMS, DAS, CLI y Web Dashboard  
**Archivo**: [`backlog_f1.yaml`](05_backlog/backlog_f1.yaml)

**Componentes principales**:
- **PMS Core**: Sistema de memoria persistente con validación SHA-1
- **DAS Enforcer**: Sistema de orquestación de agentes con enforcement
- **CLI DevHub**: Interfaz command-line para operaciones principales
- **Web Dashboard MVP**: Interfaz básica de monitoreo

**Total tareas**: 13 (3 P0, 3 P1, 5 P2, 2 P3)  
**Sprints estimados**: 3 sprints

---

## Metodología de Gestión

### Estructura de Archivos
```
docs/05_backlog/
    backlog_f0.yaml    # Fase 0: Consolidación documental
    backlog_f1.yaml    # Fase 1: Core components
    backlog_fN.yaml    # Fases futuras
```

### Convenciones de Identificadores
- **Fase 0**: `P1-DEVAGENT-001`, `P1-VALIDACION-004` (Consolidación P1)
- **Fase 1**: `TS-PMS-001`, `TS-DAS-001`, `TS-CLI-001` (TechSpecs mapping)

### Estados de Tareas
- `todo`: Pendiente de inicio
- `in-progress`: En desarrollo
- `done`: Completada exitosamente  
- `blocked`: Bloqueada por dependencia

### Prioridades
- **P0**: Crítico - Componentes fundamentales
- **P1**: Alto - Funcionalidad importante
- **P2**: Medio - Mejoras y extensiones
- **P3**: Bajo - Optimizaciones y configuración

## Progreso General

### Fase 0 (Consolidación Documental)
- **Progreso**: 0% (0/3 tareas completadas)
- **Estado**: Pendiente
- **Próximo**: Expandir DevAgent responsibilities y capabilities

### Fase 1 (Core Components)  
- **Progreso**: 0% (0/13 tareas iniciadas)
- **Estado**: Planificado
- **Inicio estimado**: Tras completar Fase 0

## Referencias

### Documentación Relacionada
- **TechSpecs**: [`docs/03_TechSpecs/`](03_TechSpecs/) - Especificaciones técnicas detalladas
- **Blueprint**: [`docs/blueprint.yaml`](blueprint.yaml) - Arquitectura general del sistema
- **Templates**: [`docs/doc_templates/backlog_fN.yaml`](doc_templates/backlog_fN.yaml) - Template para nuevas fases

### Workflow de Desarrollo
1. **Charter** – Define qué y por qué (estrategia)
2. **Blueprint** – Define cómo (arquitectura) 
3. **TechSpecs** – Define implementación detallada
4. **Roadmap** – Define cuándo (planificación temporal)
5. **Backlog** – Define tareas específicas (ejecución)

---

**Última actualización**: 2025-08-10  
**Responsable**: BlueprintAgent (Fase 0), DevAgent (Fase 1+)  
**Metodología**: Waterfall/V-Model con documentación exhaustiva