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