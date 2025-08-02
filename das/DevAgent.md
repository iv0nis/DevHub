● 8 Pasos de DevAgent Adaptados a PMS v1.2.1

  1. Cargar configuración del sistema

  # Lee memory/memory_index.yaml (no .md)
  config = pms_core.load(scope="memory_index")

  2. Leer estado actual del proyecto

  # Lee memory/project_status.md para contexto y métricas
  status = pms_core.load(scope="project_status")
  # Obtiene: fase_actual, ultima_tarea_id, métricas

  3. Leer documentos estratégicos

  # Si existen, lee documentos de contexto (opcional en PMS v1.2.1)
  if config.paths.get("charter"): charter = pms_core.load(scope="charter")
  if config.paths.get("roadmap"): roadmap = pms_core.load(scope="roadmap")

  4. Cargar blueprint único

  # Lee docs/blueprint.md (único archivo, no por fases)
  blueprint = pms_core.load(scope="blueprint")
  # Contiene todas las fases con formato: Fase N → Épica N.X → US-N.X.Y

  5. Seleccionar siguiente tarea del backlog

  # Lee backlog de la fase actual
  fase_actual = status["current_state"]["fase_actual"]  # Ej: 1
  backlog = pms_core.load(scope=f"backlog_f{fase_actual}")

  # Busca siguiente tarea (estado P = in-progress o siguiente C = pending)
  siguiente_tarea = find_next_task(backlog)

  # Si no hay más tareas en la fase:
  if not siguiente_tarea:
      pregunta_usuario("¿Pasar a fase {fase_actual+1} o revisar manualmente?")

  6. Ejecutar la tarea

  # Implementa la lógica específica de la tarea
  resultado = ejecutar_tarea_desarrollo(siguiente_tarea)

  7. Registrar resultado en el sistema

  # Actualiza backlog con resultado
  siguiente_tarea["estado"] = "C" if resultado.exitoso else "F"
  if not resultado.exitoso:
      siguiente_tarea["motivo_fallo"] = resultado.motivo

  # Guarda backlog actualizado
  pms_core.save(scope=f"backlog_f{fase_actual}", payload=backlog, mode="update_dual")

  # Actualiza project_status.md (orden cronológico presente→pasado)
  nuevo_status = update_project_status(status, siguiente_tarea, resultado)
  pms_core.save(scope="project_status", payload=nuevo_status, mode="update_dual")

  # Si necesita cambio en blueprint, propone via CSV
  if resultado.requiere_cambio_blueprint:
      propuesta = crear_propuesta_cambio(resultado.descripcion_cambio)
      pms_core.save(scope="blueprint_changes", payload=propuesta, mode="update_single")

  8. Continuar ciclo

  # Vuelve al paso 5 para buscar siguiente tarea
  return loop_siguiente_tarea()

  Diferencias clave con la versión original:
  - Usa API pms_core.load()/save() en lugar de acceso directo a archivos
  - memory_index.yaml en lugar de .md
  - Blueprint único con todas las fases vs blueprint_f(x).md
  - Sistema de propuestas via blueprint_changes.csv
  - Rollback atómico con mode="update_dual" para cambios críticos