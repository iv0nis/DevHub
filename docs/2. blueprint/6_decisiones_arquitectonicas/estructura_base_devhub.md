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