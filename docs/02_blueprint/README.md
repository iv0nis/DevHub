# DevHub Blueprint - Estructura Modular

## Estructura Actualizada

```
docs/02_blueprint/
├── 1_arquitectura_logica/
│   └── arquitectura_devhub.md       # Arquitectura + Charter Mapping
├── 2_componentes/
│   ├── agentes_sistema.md
│   ├── caracteristicas_sistema.md
│   └── sistema_agentes_das.md
├── 3_flujos_datos_eventos/
│   ├── contratos_agentes.md
│   └── flujo_nueva_feature.md
├── 4_seguridad_enforcement/
│   └── enforcement_seguridad.md     # ACTUALIZADO: Enforcement técnico DevAgent
├── 5_operaciones/
│   ├── developer_tooling.md
│   └── escalabilidad.md
├── 6_decisiones_arquitectonicas/
│   ├── adr_arquitectura_local_filesystem.md
│   ├── adr_cli_web_interfaces.md    # NUEVO: ADR-003 
│   ├── adr_single_tenant_por_proyecto.md
│   ├── estructura_archivos_proyectos.md
│   ├── estructura_base_devhub.md
│   └── feature_workflow.md
├── 7_suposiciones_restricciones/
│   └── notas_documento.md
├── 8_governanza_documental/         # NUEVO: Sistema governanza
│   └── bus_eventos_documentales.md
├── 9_observabilidad/                # NUEVO: KPIs y métricas
│   └── metricas_kpis.md
└── README.md                        # Este archivo
```

## Sincronización Realizada

### ✅ Contenido Añadido desde blueprint.yaml

1. **ADR-003**: CLI/Web Interfaces (faltaba completamente)
2. **Governanza Documental**: Sistema de eventos y enforcement
3. **Observabilidad**: KPIs, métricas y alertas completo
4. **Charter Mapping**: Objetivos → Componentes técnicos
5. **Enforcement Actualizado**: Scopes DevAgent específicos

### ✅ Estructura Modular Preservada

- Información granular mantenida en archivos específicos
- Contratos Pydantic y schemas técnicos preservados
- Integration tests específicos mantenidos
- Flujos detallados por área conservados

## Estado de Sincronización

### 02_blueprint.yaml ↔ 02_blueprint/
- **Status**: ✅ **SINCRONIZADO**
- **Fecha sync**: 2025-08-10
- **Información faltante**: Ninguna crítica
- **Fuente canonical**: 02_blueprint.yaml (operativo) + 02_blueprint/ (desarrollo)

### Próximos Pasos Recomendados

1. **Implementar auto-sync**: Sistema automático blueprint.yaml ↔ estructura modular
2. **Validación consistency**: Script que compare ambas fuentes regularmente  
3. **Workflow development**: Editar en modular → regenerar YAML consolidado
4. **Agent integration**: Agentes leen YAML, humanos editan estructura modular

## Navegación Rápida

### Por Tipo de Información
- **Arquitectura**: [1_arquitectura_logica/](1_arquitectura_logica/)
- **Agentes DAS**: [2_componentes/sistema_agentes_das.md](2_componentes/sistema_agentes_das.md)
- **ADRs**: [6_decisiones_arquitectonicas/](6_decisiones_arquitectonicas/)
- **Enforcement**: [4_seguridad_enforcement/enforcement_seguridad.md](4_seguridad_enforcement/enforcement_seguridad.md)
- **Governanza**: [8_governanza_documental/bus_eventos_documentales.md](8_governanza_documental/bus_eventos_documentales.md)
- **Métricas**: [9_observabilidad/metricas_kpis.md](9_observabilidad/metricas_kpis.md)

### Por Agente
- **DevAgent**: [2_componentes/](2_componentes/) + [4_seguridad_enforcement/](4_seguridad_enforcement/)
- **BluePrintAgent**: [8_governanza_documental/](8_governanza_documental/) + [3_flujos_datos_eventos/](3_flujos_datos_eventos/)
- **AiProjectManager**: [9_observabilidad/](9_observabilidad/) + [5_operaciones/](5_operaciones/)

---

**Última actualización**: 2025-08-10 | **Estado**: Completamente sincronizado con blueprint.yaml v2.2