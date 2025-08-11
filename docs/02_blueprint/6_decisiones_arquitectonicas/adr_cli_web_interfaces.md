# ADR-003: CLI/Web como Interfaces Principales

**Estado:** Aceptado  
**Fecha:** 2025-08-09

## Contexto
El Charter especifica que **integración profunda con IDEs externos** está **Out-of-Scope**. Esto requiere definir las interfaces principales para interactuar con DevHub.

## Decisión
Priorizar **CLI + Web Dashboard** como interfaces primarias:
- CLI para operaciones de desarrollo y automatización
- Web dashboard para monitoreo y visualización
- APIs simples para integraciones básicas (sin deep IDE integration)

## Rationale
1. **Alineación Charter**: Cumple restricción "No integración profunda IDEs"
2. **Universalidad**: CLI funciona en cualquier terminal/IDE
3. **Flexibilidad**: Web accessible desde cualquier browser
4. **Simplicidad**: No desarrollo de plugins específicos por IDE
5. **Mantenibilidad**: Menos superficie de testing y soporte

## Implementación

### CLI (devhub_cli.py)
```bash
# Operaciones principales
devhub create-project <name>           # Crear nuevo proyecto
devhub validate-structure             # Validar integridad
devhub sync-documents                # Sincronizar artefactos
devhub evaluate-blueprint            # Evaluar completitud
devhub agent-run <agent> <task>      # Ejecutar agente específico
```

### Web Dashboard (Next.js)
- **Project Overview**: Estado general del proyecto
- **Blueprint Status**: Completitud y gaps identificados
- **Agent Activity**: Log de acciones de agentes
- **Document Sync**: Estado de sincronización entre artefactos
- **Metrics Dashboard**: KPIs de desarrollo

### APIs Básicas (No Deep Integration)
```python
# Interfaces simples para herramientas externas
GET /api/project/status              # Estado actual
GET /api/blueprint/completeness      # Porcentaje completitud
POST /api/agents/run                 # Trigger agente
GET /api/documents/sync-status       # Estado sincronización
```

## Consecuencias

**Positivas:**
+ Compatibilidad universal (cualquier editor/IDE)
+ Desarrollo y mantenimiento simplificado
+ Testing más sencillo (menos interfaces)
+ Documentación concentrada
+ Flexibilidad para integraciones futuras

**Negativas:**
- No features avanzadas de IDE (autocomplete, debugging)
- Context switching entre herramientas
- Menor productividad vs deep integration
- Curva de aprendizaje de CLI

## Alternativas Evaluadas
- **Plugins IDE específicos**: Descartado por restricción Charter (Out-of-Scope)
- **Solo Web**: Descartada por limitaciones en automatización
- **Solo CLI**: Descartada por falta de visualización para stakeholders