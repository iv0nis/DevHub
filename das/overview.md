# Agents System - Overview

## ¿Qué son los Agents?

Los **Agents** son servicios especializados que ejecutan tareas específicas del proyecto de forma autónoma, coordinados por un sistema de orquestación y usando PMS-Core como capa de persistencia unificada.

## Arquitectura de 3 Capas

```
┌──────────────────────────────┐
│  1. Orchestration Layer      │  ← CrewAI, LangGraph, custom
│     - Define flow y orden    │
│     - Maneja dependencias    │
└─────────────▲────────────────┘
              │ Comandos/Eventos
┌─────────────┴────────────────┐
│  2. Agent Services           │  ← BluePrintAgent, DevAgent, QAAgent
│     - Lógica de dominio      │
│     - Especialización        │
└─────────────▲────────────────┘
              │ pms_core.load/save()
┌─────────────┴────────────────┐
│  3. PMS-Core Library         │  ← Persistencia y rollback
└──────────────────────────────┘
```

## Agents Disponibles

| Agent | Responsabilidad | Scope Principal |
|-------|----------------|----------------|
| **BluePrintAgent** | Gestión del blueprint estratégico | `blueprint`, `blueprint_changes` |
| **DevAgent** | Ejecución de tareas de desarrollo | `backlog_f*`, `project_status` |
| **QAAgent** | Validación y testing | `backlog_f*`, métricas de calidad |

## Beneficios Clave

### **🔄 Separación de Responsabilidades**
- **Orchestration:** Define CUÁNDO y EN QUÉ ORDEN
- **Agents:** Define QUÉ hacer y CÓMO
- **PMS-Core:** Maneja DÓNDE y garantiza integridad

### **🛡️ Robustez**
- **No acceso directo a archivos** - Todo vía PMS-Core API
- **Rollback automático** para cambios críticos
- **Validación SHA-1** para detectar cambios externos

### **📈 Escalabilidad**
- **Agents agnósticos** - No dependen de frameworks específicos
- **Configuración flexible** - Cada agent define sus scopes
- **Orquestación intercambiable** - CrewAI, LangGraph, o custom

### **👁️ Observabilidad**
- **Eventos del sistema** - Trazabilidad completa
- **Métricas automáticas** - Health monitoring
- **Log cronológico** - Historia de decisiones

## Principio Fundamental

> **Los agents NUNCA acceden a archivos directamente. Siempre usan la API PMS-Core.**

```python
# ❌ INCORRECTO
with open("docs/blueprint.md") as f:
    blueprint = f.read()

# ✅ CORRECTO  
blueprint = pms_core.load(scope="blueprint")
```

## Flujo de Trabajo Típico

1. **Orchestrator** inicia el ciclo
2. **PMS-Core** carga el estado actual
3. **Agent específico** ejecuta su tarea
4. **PMS-Core** guarda cambios con rollback
5. **Sistema** actualiza métricas automáticamente

## Documentación Detallada

- **[agents.md](./agents.md)** - Especificación técnica completa
- **[pms.md](../pms/pms.md)** - API PMS-Core y persistencia
- **Configuración individual:** `BluePrintAgent.yaml`, `DevAgent.yaml`, `QAAgent.yaml`

---

**Estado**: ✅ Sistema operativo • Documentación completa • Ready for production