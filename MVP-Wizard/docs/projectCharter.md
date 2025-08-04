# Project Charter de MVP-Wizard

## 1. Propósito

Crear un sandbox funcional para desarrollar el sistema UI de DevHub y validar la integración entre sus 3 pilares fundamentales: PMS, DAS y UI.

## 2. Contexto

DevHub requiere un sistema UI que actualmente no existe. El MVP-Wizard permite desarrollar este pilar UI mientras se prueba la integración con PMS (Persistent Memory System) y DAS (DevAgent System).

## 3. Objetivo

Implementar un wizard de 6 pasos que genere artefactos PMS y simule el flujo completo de DevHub, validando que los 3 pilares funcionen integrados antes de construir el sistema completo.

## 4. Visión

Un prototipo funcional que sirva como base para el desarrollo del pilar UI de DevHub, con arquitectura evolutiva que permita reutilización 100% en el sistema final.

## 5. Alcance conceptual

* **In-Scope**:

  * Desarrollo del pilar UI: Interface wizard de 6 pasos funcional
  * Validación de integración: PMS + DAS + UI trabajando juntos
  * Flujo completo: Nombre → Briefing → Charter → Roadmap → Blueprint → Estructura
  * Componentes base: Stepper, navegación, formularios simples
  * Simulación DAS: Agentes GPT via navegador (temporal)
  * Integración PMS: Bridge Python-Node.js con pms_core.py
* **Out-of-Scope**:

  * Persistencia en base de datos
  * Autenticación de usuarios
  * Colaboración multi-usuario
  * UI avanzado y animaciones
  * Validaciones complejas
  * Tests automatizados
  * CI/CD automático
