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