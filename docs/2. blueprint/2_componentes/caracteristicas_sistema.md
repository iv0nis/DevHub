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