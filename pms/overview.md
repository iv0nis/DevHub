# PMS Overview - Resumen Ejecutivo

## ¿Qué es PMS?

**Persistent Memory System (PMS)** es un sistema de persistencia y gestión de estado para proyectos con agentes AI. Proporciona estructura, integridad y trazabilidad sin imponer ningún framework de orquestación específico.

## Requisitos Obligatorios

### Estructura Mínima
```
project-root/
├── memory/
│   ├── memory_index.yaml        # Configuración central
│   ├── project_status.md        # Estado + métricas
│   └── temp/                    # Rollback atómico
├── docs/
│   ├── blueprint.md            # Fuente de verdad estratégica
│   ├── blueprint_changes.csv   # Propuestas de cambio collaborativas
│   └── backlog/                # Tareas operativas por fase
└── .gitignore                  # Ignora .lock, temp/, *.tmp
```

### Archivos Obligatorios
- `memory/memory_index.yaml`: Rutas y configuración del sistema
- `memory/project_status.md`: Estado actual con métricas integradas
- `docs/blueprint.md`: Blueprint con formato específico (fases → épicas → US)
- `docs/blueprint_changes.csv`: Sistema de propuestas collaborativas
- Al menos un `docs/backlog/backlog_f{n}.yaml` por fase

## API PMS-Core

### Funciones Principales
```python
# Cargar datos
data = pms_core.load(scope="blueprint")
data = pms_core.load(scope="backlog_f1") 
data = pms_core.load(scope="project_status")

# Guardar con rollback
pms_core.save(scope="blueprint", payload=data, mode="update_dual")
pms_core.save(scope="project_status", payload=metrics, mode="update_single")

# Métricas automáticas
metrics = pms_core.metrics()
```

### Modos de Operación
- `read_only`: Solo lectura, sin modificaciones
- `update_single`: Escribe un archivo con validaciones básicas
- `update_dual`: Rollback dual atómico para cambios críticos

## Control de Integridad

- **SHA-1 validation**: Detecta cambios externos al blueprint
- **Rollback dual**: Archivos `.tmp` + `rename()` atómico en `memory/temp/`
- **Concurrencia**: Archivos `.lock` para operaciones críticas

## Métricas Automáticas

El sistema calcula automáticamente:
- Porcentaje de completado por fase
- Velocidad de sprint (tareas/tiempo)
- Health alerts (ratio de tareas bloqueadas)
- Burndown tracking integrado

## Pasos de Arranque

1. **Crear estructura**: `mkdir -p project/{memory/temp,docs/backlog}`
2. **Copiar templates** desde `pms/templates/`
3. **Rellenar campos obligatorios** en cada archivo
4. **Configurar .gitignore** para archivos temporales
5. **Probar rollback**: Ejecutar ciclo `load → modify → save(update_dual)`

## Sistema de Propuestas Collaborativo

- **Flujo**: `proposed` → `reviewed` → `approved` → `merged`
- **Participantes**: Cualquier agente puede proponer, solo BluePrintAgent fusiona
- **Trazabilidad**: Cada cambio queda registrado con autor, timestamp y estado
- **Control humano**: Aprobación final siempre requiere revisión humana

## Beneficios Clave

✅ **Robustez**: Rollback atómico dual garantiza consistencia  
✅ **Flexibilidad**: Blueprint evolutivo con control de cambios  
✅ **Escalabilidad**: Particionado opcional para proyectos grandes  
✅ **Observabilidad**: Métricas de burndown y health integradas  
✅ **Framework-agnostic**: Compatible con CrewAI, LangGraph, custom orchestrators

---

Para detalles técnicos completos, consultar [`pms.md`](./pms.md).  
Para integración con agentes, consultar [`../agents/agents.md`](../agents/agents.md).