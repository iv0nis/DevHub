# PMS v2.2 - Overview

## Sistema de Memoria Persistente para Agentes LLM

PMS v2.2 proporciona memoria estructurada y persistente para agentes de IA, garantizando continuidad operativa y trazabilidad completa en proyectos de desarrollo.

## 🚀 Características Clave

- **Rollback atómico dual** - Transacciones seguras con consistencia garantizada
- **Métricas integradas** - Burndown automático y health tracking en tiempo real  
- **Blueprint evolutivo** - Control SHA-1 y versionado con changelog
- **Arquitectura multi-agente** - Separación clara entre documentos humanos y operativos
- **Escalabilidad robusta** - Particionado opcional para proyectos extensos

## 🧠 Tipos de Memoria

- **🧠 Trabajo** - Backlogs activos (`backlog/`)
- **⚡ Corto plazo** - Archivos temporales (`memory/temp/`)  
- **📚 Largo plazo** - Documentos estratégicos (`docs/`)
- **🎬 Episódica** - Log cronológico (`memory/project_status.md`)

## 📁 Estructura del Proyecto

```
project-root/
├── memory/
│   ├── memory_index.yaml     # Configuración central
│   ├── project_status.md     # Estado + métricas
│   └── temp/                 # Transacciones
├── docs/
│   ├── project_charter.md    # Visión (humano)
│   ├── roadmap.md           # Planificación (humano)  
│   └── blueprint.md         # Fases + épicas (humano)
└── backlog/
    └── backlog_fN.yaml      # Tareas operativas (agente)
```

## 🎯 Casos de Uso

- **Proyectos multi-fase** con equipos de agentes IA
- **Desarrollo con continuidad** - reanudar trabajo tras interrupciones
- **Trazabilidad completa** - auditoría de decisiones y progreso
- **Colaboración humano-agente** - separación clara de responsabilidades

## 🔧 Estados de Tareas

- `C` = Completed | `P` = In-Progress | `B` = Blocked | `F` = Failed

---

**PMS v2.2** - Memoria persistente para agentes LLM • *Robusto • Observable • Evolutivo*