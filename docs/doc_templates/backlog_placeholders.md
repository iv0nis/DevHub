### Tier list de *placeholders* para un **template de backlog**

| Tier                                               | Placeholder | Propósito (1 línea)                                   |
| -------------------------------------------------- | ----------- | ----------------------------------------------------- |
| **Esenciales** (mínimos para que DevAgent ejecute) |             |                                                       |
| E1                                                 | `id`        | Identificador único (p. ej. `US-1.2.3`).              |
| E2                                                 | `title`     | Resumen corto de la historia.                         |
| E3                                                 | `phase`     | Fase / release a la que pertenece (`F1`, `F2`…).      |
| E4                                                 | `status`    | `todo · in-progress · done · blocked`.                |
| E5                                                 | `priority`  | `P0-P3` o `critical-low`; guía de orden de ejecución. |

| Tier                                         | Placeholder           | Propósito                                       |
| -------------------------------------------- | --------------------- | ----------------------------------------------- |
| **Básicos** (recomendados para trazabilidad) |                       |                                                 |
| B1                                           | `description`         | Qué se necesita y por qué (máx. 3-4 líneas).    |
| B2                                           | `acceptance_criteria` | Lista bullets “done when…”.                     |
| B3                                           | `owner`               | Humano o agente responsable.                    |
| B4                                           | `story_points`        | Tamaño relativo (1-13) o `estimate_h` en horas. |
| B5                                           | `dependencies`        | Array de `id` que deben completarse antes.      |
| B6                                           | `created_at`          | ISO-8601; lo rellena el sistema.                |
| B7                                           | `updated_at`          | ISO-8601; refresca en cada cambio.              |

| Tier                                   | Placeholder  | Propósito                                       |
| -------------------------------------- | ------------ | ----------------------------------------------- |
| **Extendidos** (solo si aportan valor) |              |                                                 |
| X1                                     | `labels`     | Etiquetas libres: `security`, `UI`, `refactor`… |
| X2                                     | `risk_level` | `low · medium · high`; para alertas.            |
| X3                                     | `due_date`   | Fecha límite contractual, si existe.            |
| X4                                     | `blocked_by` | Motivo textual cuando `status = blocked`.       |
| X5                                     | `reviewer`   | Quién debe aprobar el PR o merge.               |
| X6                                     | `links`      | URLs a diseños, mock-ups, ADR, etc.             |
| X7                                     | `notes`      | Campo libre para comentarios de progreso.       |

> **Uso sugerido**
>
> * **Plantilla Base (`backlog_fN.yaml`)** = E + B.
> * Activa los **extendidos** solo en proyectos con auditoría, SLA estrictos o complejidad alta.
