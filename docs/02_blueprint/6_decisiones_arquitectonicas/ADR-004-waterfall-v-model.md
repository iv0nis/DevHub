# ADR-004: Adopción de Waterfall/V-Model

**Estado:** Aprobado  
**Fecha:** 2025-08-11

## Contexto
DevHub requiere trazabilidad completa desde requisitos hasta implementación, diseño robusto antes de codificar, y alineación con estándares de la industria (ISO/IEC/IEEE 42010, arc42) para proyectos de agentes autónomos.

El flujo de trabajo en DevHub implementa una metodología de desarrollo secuencial que prioriza la documentación de la visión y requisitos en el Project Charter, seguida del diseño de alto nivel (HLD) en Blueprint, el diseño de bajo nivel (LLD) en TechSpecs y finalmente la implementación. Esta aproximación metodológica se alinea con prácticas consolidadas en la industria del software, especialmente en organizaciones que requieren un diseño robusto antes de iniciar el desarrollo.

## Decisión
Adoptar metodología Waterfall/V-Model secuencial:
**Charter → Blueprint (HLD) → TechSpecs (LLD) → Roadmap → Backlogs → Implementación**

## Metodologías de la Industria Aplicables

### Waterfall / V-Model
En entornos altamente regulados o proyectos de gran escala (telecomunicaciones, automoción, sector bancario), se implementa el modelo en cascada con las siguientes fases:

1. **Requisitos** - Definición y análisis de necesidades
2. **Diseño** - High-Level Design (HLD) + Low-Level Design (LLD)
3. **Implementación** - Desarrollo del código
4. **Pruebas** - Validación y verificación
5. **Mantenimiento** - Soporte y evolución

El Blueprint de DevHub actúa como el HLD principal, mientras que el LLD se desarrolla específicamente en TechSpecs (Technical Specifications). El V-Model complementa esta estructura añadiendo pruebas específicas asociadas a cada fase de diseño.

### Big Design Up Front (BDUF)
En proyectos donde la reducción de riesgos es prioritaria, se desarrolla un diseño comprehensivo antes de la implementación. En este contexto, el Blueprint funciona como el artefacto principal del diseño inicial.

### Documentación de Arquitectura según Estándares ISO/IEC/IEEE 42010 y arc42
Las mejores prácticas de arquitectura de software recomiendan la creación de un **Software Architecture Document** (SAD) que incluye:

- Descripción de stakeholders
- Requisitos de calidad  
- Visión arquitectónica de alto nivel
- Componentes principales
- Flujos de datos
- Decisiones arquitectónicas

El estándar **arc42** proporciona una estructura de 12 secciones que se corresponde estrechamente con el template de Blueprint implementado en DevHub.

## Template de Blueprint: Correspondencia con Estándares de la Industria

El template `blueprint_template.md` de DevHub incorpora los siguientes elementos, alineados con las mejores prácticas de documentación arquitectónica:

1. **Metadatos** - Versión, fecha y hash de control
2. **Stack tecnológico** - Tecnologías y patrones arquitectónicos
3. **Componentes principales** - Propósito, responsabilidades e interfaces
4. **Flujos de datos** - Contratos y comunicación entre componentes
5. **Seguridad** - Análisis de amenazas y medidas de protección
6. **Operaciones** - Despliegue, escalabilidad y observabilidad
7. **Decisiones clave** - Rationale y consecuencias
8. **Documentación de soporte** - Suposiciones, restricciones, glosario y referencias

Esta estructura corresponde al 100% con los requerimientos de los Software Architecture Documents (SAD) utilizados en la industria.

## Proceso de Implementación en DevHub

### 1. Charter / Visión y Requisitos
Documento de alto nivel que establece stakeholders, objetivos de negocio, alcance del proyecto y criterios de éxito.

### 2. Blueprint (High-Level Design)
Utilización completa del template de Blueprint para definir todos los aspectos relevantes para arquitectos y líderes técnicos antes del desarrollo del código.

### 3. TechSpecs (Low-Level Design)
A partir del Blueprint, se generan uno o varios documentos de Technical Specifications (TechSpecs) para cada componente crítico, incluyendo:

- Diagramas de clases
- Pseudocódigo
- Firmas de API
- Manejo de errores
- Especificaciones detalladas

### 4. Roadmap / Backlog
Con los TechSpecs (LLD) validados, cada módulo y detalle técnico se traduce en épicas e historias de usuario, completamente estimadas y priorizadas.

### 5. Implementación y Pruebas
El equipo de desarrollo utiliza los TechSpecs (LLD) y el backlog como base para la codificación, pruebas y despliegue del sistema.

## Consecuencias

**Positivas:**
+ Trazabilidad completa desde requisitos hasta implementación
+ Reducción de riesgos mediante diseño anticipado  
+ Garantías de calidad a través de documentación estructurada
+ Alineación con estándares de la industria del software
+ Facilidad de mantenimiento y evolución del sistema
+ Documentación arquitectónica robusta (SAD/arc42)
+ Control de calidad mediante revisiones por fase

**Negativas:**
- Menor flexibilidad para cambios tardíos
- Mayor documentación upfront requerida  
- Proceso menos adaptativo que metodologías ágiles

## Alternativas Evaluadas
- **Agile puro**: Descartado por falta de trazabilidad documental requerida
- **Híbrido Dual-Track**: Descartado por complejidad de coordinación agentes
- **BDUF (Big Design Up Front)**: Muy similar, pero menos estructurado que V-Model

## Conclusión
La metodología Waterfall/V-Model implementada en DevHub representa una práctica estándar en la industria del software, especialmente efectiva cuando se requieren garantías de calidad y trazabilidad completa. El template de Blueprint constituye exactamente el artefacto de High-Level Design utilizado en proyectos de gran escala, complementado posteriormente con TechSpecs (LLD) y backlog para completar el ciclo de desarrollo.

Esta estructura metodológica proporciona un proceso sólido, claro y alineado con las mejores prácticas de la ingeniería de software.

