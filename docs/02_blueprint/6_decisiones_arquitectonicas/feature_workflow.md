# Workflow de Features

## Flujo de 7 Pasos

1. **Idea → Validación (Charter/alcance)**
2. **Propuesta → `blueprint_changes.csv` → Review (BluePrintAgent + humano)**
3. **Blueprint (módulo) → Sync → Integridad (SHA/CI)**
4. **TechSpec (módulo) → ADR si hay decisión clave → Sync**
5. **Roadmap (módulo) → Sync**
6. **Backlog (módulo) → Sync**
7. **Status (update)**

## Puntos de Control

### Humanos
- Validación inicial contra charter
- Review de propuestas (calidad + estrategia)
- Supervisión de decisiones arquitectónicas críticas

### Técnicos
- SHA/CI enforcement automático
- DAS permissions por agente
- Auto-sync entre documentos

## Beneficios

- ✅ UX sin fricción (proceso encapsulado)
- ✅ Governance robusta (review dual)
- ✅ Integridad técnica (enforcement automático)
- ✅ Trazabilidad completa (idea → código)

## Ejemplo: Auto-Sync Tool

**Actual**: Paso 3 completado (módulo `5_operaciones/developer_tooling.md`)
**Pendiente**: Sync a `blueprint.yaml` → TechSpec → Roadmap → Backlog