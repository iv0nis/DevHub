# Project Charter de mvp-wizard

## 1. Propósito

Permitir a Product Owners generar en 6 pasos los artefactos clave de su proyecto (Charter, Roadmap, Blueprint) y mostrar la estructura final de forma simple y rápida.

## 2. Contexto

Crear un wizard que capture información básica del proyecto y genere automáticamente los documentos de planificación usando PMS-Core.

## 3. Objetivo

Demostrar un flujo funcional de 6 pasos que genere 3 artefactos (Charter, Roadmap, Blueprint) y muestre la estructura final del proyecto.

## 4. Visión

Un prototipo simple que muestre el flujo completo de creación de documentos de proyecto.

## 5. Alcance conceptual

* **In-Scope**:

  * Flujo guiado en 6 pasos: Nombre → Briefing → Charter → Roadmap → Blueprint → Estructura
  * Componentes básicos: Stepper con navegación anterior/siguiente
  * Formularios simples para capturar inputs
  * Previews básicos de documentos generados
  * Estado en memoria simple para datos entre pasos
  * Integración directa con pms-core
* **Out-of-Scope**:

  * Persistencia en base de datos
  * Autenticación de usuarios
  * Colaboración multi-usuario
  * UI avanzado y animaciones
  * Validaciones complejas
  * Tests automatizados
  * CI/CD automático
