# MVP-Wizard - Arquitectura y Documentación

## 1. Propósito del MVP

Crear un **sandbox funcional** para desarrollar el sistema UI de DevHub (actualmente inexistente) y validar la integración entre sus 3 pilares fundamentales:

- **PMS** (Persistent Memory System) - Sistema de memoria persistente
- **DAS** (DevAgent System) - Sistema de agentes autónomos  
- **UI** (User Interface) - Interface de usuario

El MVP implementa un wizard de 6 pasos que genera artefactos PMS y simula el flujo completo que tendrá DevHub, sirviendo como prototipo para validar la integración de los 3 pilares.

## 2. Arquitectura MVP (Actual)

### 2.1 Frontend
- **Next.js 14** con App Router
- **6-step wizard** con navegación anterior/siguiente
- **TypeScript + Tailwind** para componentes
- **Zustand** para state management entre pasos

### 2.2 Backend
- **DAS via navegador** (simulación temporal de DevAgent System)
- **API routes** `/api/pms/` para bridge Python-Node.js
- **Integración directa** con `pms_core.py`

### 2.3 Storage
- **PMS-Core real** (`pms_core.py`)
- **Sistema de archivos** memory/, docs/, backlog/
- **Rollback atómico** y SHA-1 validation

## 3. Arquitectura DevHub (Futuro)

### 3.1 Frontend
- **Same wizard interface** (sin cambios)
- **Mismos 6 pasos** y navegación
- **Same state management**

### 3.2 Backend
- **DAS integrado** (DevAgent System interno, no navegador)
- **Same API routes** estructura
- **Same PMS-Core** integration

### 3.3 Storage
- **Same PMS-Core** sin cambios
- **Same file system** structure

## 4. Evolutividad MVP → DevHub

**Ventaja clave**: El MVP permite **evolución sin breaking changes** de los 3 pilares

1. **UI**: Reutilización 100% - frontend validado y funcional
2. **PMS**: Reutilización 100% - sistema ya integrado y probado  
3. **DAS**: Solo reemplazar implementación (navegador → DevAgent System interno)

## 5. Flujo de 6 Pasos

1. **Paso 1**: Nombre proyecto + inicializar
2. **Paso 2**: Briefing y contexto
3. **Paso 3**: Charter preview generado
4. **Paso 4**: Roadmap preview generado
5. **Paso 5**: Blueprint preview generado
6. **Paso 6**: Estructura final + activar DevAgent

**Nota**: DevAgent genera backlog **después** del Step 6

## 6. Proto-backlog de Implementación

1. **Init repo** → `feature/mvp-wizard` rama
2. **Setup Next.js** `/app` con stepper básico
3. **Integrar PMS-Core** llamadas directas
4. **Implementar pasos**:
   * Paso1: Nombre + iniciar
   * Paso2: Briefing
   * Paso3: Charter preview
   * Paso4: Roadmap preview
   * Paso5: Blueprint preview
   * Paso6: Estructura + finalizar
5. **Deploy MVP** en Vercel/Netlify

## 7. Contexto para DevAgents

Este documento sirve para contextualizar a otros DevAgents sobre:

- **Por qué existe el MVP**: Validar flujo antes de implementar agentes internos
- **Qué reutilizar**: Frontend completo + PMS-Core + API structure
- **Qué cambiar**: Solo la implementación de agentes (navegador → interno)
- **Timeline**: MVP funcional → Migration gradual → DevHub completo

