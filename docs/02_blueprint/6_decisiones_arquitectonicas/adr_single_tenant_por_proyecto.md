# ADR-002: Single-Tenant por Proyecto

**Estado:** Aceptado  
**Fecha:** 2025-08-09

## Contexto
El Charter especifica que **multi-tenant entre organizaciones** está **Out-of-Scope**. Esto define la estrategia de aislamiento y gestión de proyectos en DevHub.

## Decisión
Implementar modelo **"Un proyecto = Una instancia DevHub"**:
- Cada proyecto tiene su propia instancia completa de DevHub
- Configuración independiente (pms_core.py, enforcer.py, agentes)
- Datos completamente aislados por proyecto
- No compartición de recursos entre proyectos

## Rationale
1. **Alineación Charter**: Cumple restricción "No multi-tenant"
2. **Seguridad**: Aislamiento completo entre proyectos
3. **Simplicidad**: No lógica compleja de multi-tenancy
4. **Personalización**: Configuración específica por proyecto
5. **Escalabilidad**: Proyectos crecen independientemente

## Implementación

### Estructura por Proyecto
```
DevHub_Framework/          # Templates y core
├── pms/templates/
├── das/agent_templates/
└── docs/doc_templates/

Project_Alpha/            # Instancia específica
├── pms_core.py          # Configurado para Alpha
├── enforcer.py          # Permisos específicos Alpha  
├── agents/              # System prompts Alpha
└── docs/               # Documentos Alpha

Project_Beta/            # Instancia independiente
├── pms_core.py         # Configurado para Beta
├── enforcer.py         # Permisos específicos Beta
└── ...
```

### Beneficios Técnicos
- **Configuración granular**: Cada proyecto puede tener reglas DAS específicas
- **Evolución independiente**: Un proyecto no afecta otros
- **Backup selectivo**: Respaldo por proyecto según criticidad
- **Debugging aislado**: Problemas no se propagan

## Consecuencias

**Positivas:**
+ Aislamiento completo de datos
+ Configuración personalizable por proyecto
+ Debugging y troubleshooting simplificado
+ Escalabilidad horizontal natural
+ Backup/restore granular

**Negativas:**
- Duplicación de configuraciones similares
- Mantenimiento múltiple de instancias
- No economías de escala en recursos
- Sincronización manual entre proyectos relacionados

## Alternativas Evaluadas
- **Multi-tenant compartido**: Descartado por restricción Charter (Out-of-Scope)
- **Instancia única global**: Descartada por complejidad de aislamiento
- **Microservicios por proyecto**: Descartada por overhead de infraestructura