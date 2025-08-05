# DevHub Specs

## Arquitectura DevHub

La arquitectura de DevHub se basa en una estructura modular que permite la creación y gestión de proyectos de IA de manera eficiente. Los componentes principales son:

- **PMS** (Persistent Memory System) - Sistema de memoria persistente
- **DAS** (DevAgent System) - Sistema de agentes autónomos  
- **UI** (User Interface) - Interface de usuario

## Estructura Base DevHub

```
DevHub/                          # Repositorio DevHub central
├── CLAUDE.md                    # Configuración Claude Code
├── README.md                    # Documentación principal
├── devhub_cli.py               # CLI para creación de proyectos
├── pms/                        # Sistema PMS central
│   ├── pms_core.py            # 
│   └── memory_templates/             # Templates de los archivos de memoria
│       ├── memory_index.yaml  # Template para el Índice de memoria
│       └── project_status.md   # Template para el estado del proyecto y registro de tareas ejecutadas
├── das/                        # Sistema DAS central
│   ├── enforcer.py            # 
│   └── agent_templates/                # Templates de system prompts de los agentes
│       ├── DevAgent.yaml      # Template DevAgent
│       ├── BluePrintAgent.yaml # Template BluePrintAgent
│       └── AiProjectManager.yaml # Template AiProjectManager
└── docs/                       # Documentación DevHub
    └── DevHub.md              # Este archivo
```

## Estructura de archivos inicial de los Proyectos en desarrollo

Cada proyecto creado con DevHub sigue una estructura estándar que permite la fácil gestión y escalabilidad. La estructura inicial de un proyecto es la siguiente:
```
project_name/
├── README.md                   # Documentación del proyecto
├── pms_core.py                # PMS configurado para proyecto local
├── enforcer.py                # DAS enforcer configurado localmente
├── agents/                    # Agentes del proyecto
│   ├── DevAgent.yaml          # DevAgent configurado para proyecto
│   ├── BluePrintAgent.yaml    # BluePrintAgent configurado
│   └── AiProjectManager.yaml  # AiProjectManager configurado
├── docs/                      # Documentación del proyecto
│   ├── ProjectCharter.md      # Visión y alcance del proyecto
│   ├── roadmap.md            # Roadmap de implementación
│   ├── blueprint.md          # Especificación técnica detallada
│   ├── blueprint_changes.csv # Propuestas de cambios al blueprint
│   └── backlog/              # Sistema de backlogs por fases
│       ├── backlog.md        # Documentación del sistema backlog
│       ├── backlog_f1.yaml   # Backlog Fase 1
│       ├── backlog_f2.yaml   # Backlog Fase 2
│       └── backlog_fN.yaml   # Backlog Fase N
├── memory/                    # Sistema de memoria persistente
│   ├── memory_index.yaml     # Configuración de rutas del proyecto
│   └── project_status.md     # Estado actual del proyecto
```

## Características del Sistema

### Independencia de Proyectos
- Cada proyecto tiene su propio `pms_core.py` configurado localmente
- Cada proyecto tiene su propio `enforcer.py` con restricciones específicas
- Los agentes están configurados exclusivamente para el contexto del proyecto

### Sistema de Backlogs Multi-Fase
- `backlog_f1.yaml`, `backlog_f2.yaml`, etc. para gestión por fases
- `backlog.md` documenta las tareas y objetivos de cada sprint
- DevAgent puede trabajar con cualquier fase según el estado del proyecto

### Templates
- Los templates de memoria y agentes son configurables y reutilizables
- `memory_templates/` contiene los templates de memoria
- `agent_templates/` contiene los system prompts de los agentes

### Memoria Persistente con Persisten Memory System PMS
- El sistema de memoria persistente (pms) se ha creado para mejorar la confiabilidad, la credibilidad y la capcidad de los agentes.
- Las especificaciones del sistema de memoria persistente se encuentran en `pms\pms.md`

## Sistema de Agentes con DevAgent System (DAS)
- El sistema DAS permite la orquestación de múltiples agentes para tareas específicas del proyecto.
- Limita el acceso a archivos y recursos según permisos definidos.
- El sistema DAS se especifica en `das/das.md`

## Agentes del Sistema

### DevAgent
- Ejecuta tareas de desarrollo siguiendo blueprint y backlog
- Actualiza estado del proyecto automáticamente
- Propone cambios al blueprint cuando es necesario

### BluePrintAgent
Neceitamos mantener blueprint.md como fuente de verdad del proyecto, por lo que se requiere un sistema de seguridad para evitar modificaciones no autorizadas.
- Único autorizado para modificar `blueprint.md`
- Procesa propuestas de `blueprint_changes.csv`
- Mantiene versionado y changelog del blueprint

### AiProjectManager
- Gestiona la visión general del proyecto

## Enforcement y Seguridad

- Cada proyecto tiene su propio sistema de permisos especificado en `das/das.md`
- Los agentes solo pueden acceder a archivos autorizados
- Violaciones de permisos son registradas y bloqueadas automáticamente
- Sistema de auditoría completo para todas las operaciones

## Escalabilidad

Esta estructura permite:
- ✅ Proyectos completamente independientes
- ✅ Replicación fácil de configuraciones exitosas
- ✅ Gestión de múltiples fases de desarrollo
- ✅ Integración con sistemas CI/CD
- ✅ Colaboración entre múltiples desarrolladores

---

*Este documento define la estructura estándar para todos los proyectos DevHub. Cualquier modificación debe ser documentada y comunicada al equipo de desarrollo.*