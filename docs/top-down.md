El flujo habitual es **top-down**:

```
Project Charter  →  Blueprint  →  Roadmap  →  Backlogs
                    ↑                ↑          ↑
                    └─ feedback ─────┴──────────┘
```

### 1. Blueprint vs. Roadmap

|                 | Blueprint                            | Roadmap                                                    |
| --------------- | ------------------------------------ | ---------------------------------------------------------- |
| **Pregunta**    | “¿Cómo lo construiremos?”            | “¿Cuándo y en qué orden lo entregaremos?”                  |
| **Insumos**     | Charter (propósito, alcance)         | Charter **+** Blueprint (componentes y dependencias)       |
| **Dependencia** | No necesita al roadmap para existir. | Necesita entender el blueprint para programar cada módulo. |

> **Por tanto, el roadmap “bebe” del blueprint**, no al revés. Cambios en la arquitectura (blueprint) pueden obligar a re-planificar el calendario (roadmap).

### 2. Backlogs

* **Derivan directamente del roadmap** (prioridad y fase) **y del blueprint** (detalle técnico de cada ítem).
* Actúan como “lista de trabajo viva” para DevAgent; conforme se aprende algo nuevo, pueden retroalimentar ambos documentos:

  * Una tarea revela una dependencia → se actualiza blueprint.
  * Se alarga una tarea crítica → se ajusta roadmap.

### 3. Ciclo de vida simplificado en DevHub

1. **Charter** define por qué y qué (estrategia).
2. **BluePrintAgent** genera/ajusta *blueprint.md*.
3. **AiProjectManager** crea/actualiza *roadmap.md* y los *backlog\_f*.yaml a partir del blueprint.
4. **DevAgent** ejecuta backlogs y reporta hallazgos que, si impactan diseño o plazos, disparan actualizaciones hacia arriba.

Así mantenemos coherencia: cada capa consume la información de la anterior y, cuando algo cambia, propaga ajustes hacia abajo o de vuelta hacia arriba según corresponda.

**Respuesta corta:**
No hace falta desechar la modularización; hay que **ajustar los contratos entre módulos** para que soporten el esquema jerárquico *top-down + retroalimentación*. Los bloques principales (Charter, Blueprint, Roadmap, Backlogs) siguen siendo válidos; lo que cambia es **cómo se invocan y cómo se pasan la información**.

---

## Qué hay que tocar y qué no

| Bloque        | Mantener                                               | Actualizar                                                                                                                                                             |
| ------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Charter**   | Formato y ownership (patrocinador + AiProjectManager). | Agregar un *section id* o *hash* para que los demás docs referencien su versión.                                                                                       |
| **Blueprint** | Sigue siendo “diseño arquitectónico”.                  | 1) Debe registrar de qué *Charter-id* proviene.<br>2) Expone una API de cambio (*BlueprintChangeEvent*) para que Roadmap/Backlogs lo consuman.                         |
| **Roadmap**   | Sigue planificando por releases / fases.               | 1) Debe leer cambios del Blueprint.<br>2) Publica *RoadmapChangeEvent* para regenerar backlogs afectados.                                                              |
| **Backlogs**  | Estructura YAML por fase.                              | 1) Escuchan RoadmapChangeEvent.<br>2) Emiten *RealityFeedbackEvent* con métricas (tiempo real, bloqueos) que pueden disparar ajustes en Roadmap y, a veces, Blueprint. |
| **Agentes**   | Roles básicos permanecen.                              | Añadir “canales de eventos” arriba/abajo y políticas de quién puede activar cambios en nivel superior.                                                                 |

---

## Refactor mínimo sugerido ( ≃ 1–2 días)

1. **Crear un bus de eventos ligero** (ej. carpeta `/events` con JSONs o colas in-memory)

   * `BlueprintChangeEvent`, `RoadmapChangeEvent`, `RealityFeedbackEvent`.

2. **Extender cada agente** con dos métodos:

   * `consume(eventType)` → actualiza su artefacto.
   * `produce(eventType)` → notifica al nivel adyacente.

3. **Versionado de documentos**

   * Añade `version` y `parentVersion` al front-matter de cada MD/YAML.

4. **Política de escalado de feedback**

   * Backlogs solo pueden proponer cambios al Roadmap;
   * Roadmap puede proponer cambios al Blueprint;
   * Blueprint no modifica Charter, pero genera *change-requests* que un humano aprueba.

---

## Qué NO tocar de la modularización

* **Separación física de archivos** (`/charter`, `/blueprint`, `/roadmap`, `/backlogs`)
  ya respeta el esquema jerárquico.

* **Responsabilidad de cada agente**
  (DevAgent ejecuta backlog; BlueprintAgent no se mete en fechas).

* **Templates y scaffolding**
  siguen útiles; solo añade los nuevos campos de versión/evento.

---

## Resultado esperado

* **Coherencia continua**: cualquier cambio abajo (ej. backlog se retrasa) sube como evento → Roadmap recalcula fechas →, si afecta capacidad, sube a Blueprint para reconsiderar diseño.
* **Trazabilidad**: cada documento declara de qué versión del padre nació.
* **Menos “big-bang” re-work**: ajustes finos y rápidos sin romper el todo.

> **Conclusión**: adapta la *interfaz* entre módulos, no la *estructura* interna. Con un bus de eventos y metadatos de versión tendrás el nuevo modelo jerárquico con retroalimentación, manteniendo la modularización que ya construiste.

