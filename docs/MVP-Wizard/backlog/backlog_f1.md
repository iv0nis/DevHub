# MVP Wizard - Backlog F1

**Fase:** 1  
**Sprint:** 1  
**Estado:** En progreso

## Historias de Usuario

### US-1.1.1: Setup proyecto Next.js
- **Estado:** ✅ Completado
- **Tareas:**
  - T-1.1.1a: Crear proyecto Next.js con TypeScript → ✅ Completado
  - T-1.1.1b: Configurar Tailwind + ESLint → ✅ Completado
  - T-1.1.1c: Instalar dependencias y probar servidor → ✅ Completado

### US-1.2.1: Estructura stepper básico
- **Estado:** 🔄 En progreso
- **Tareas:**
  - T-1.2.1a: Crear carpetas src/app/step/[id] → 📋 Pendiente
  - T-1.2.1b: Instalar Zustand para estado global → 📋 Pendiente
  - T-1.2.1c: Crear componentes base (Stepper, Navigation) → 📋 Pendiente

### US-1.2.2: Rutas dinámicas /step/1-6
- **Estado:** 📋 Pendiente
- **Tareas:**
  - T-1.2.2a: Configurar rutas step/[id]/page.tsx → 📋 Pendiente
  - T-1.2.2b: Implementar navegación entre pasos → 📋 Pendiente
  - T-1.2.2c: Crear layout común StepLayout → 📋 Pendiente

### US-1.3.1: API PMS-Core integration
- **Estado:** 📋 Pendiente
- **Tareas:**
  - T-1.3.1a: Crear Next.js API routes → 📋 Pendiente
  - T-1.3.1b: Bridge Python pms_core.py → 📋 Pendiente
  - T-1.3.1c: Endpoints para cada paso del wizard → 📋 Pendiente

### US-1.4.1: UI pasos wizard
- **Estado:** 📋 Pendiente
- **Tareas:**
  - T-1.4.1a: Step 1: Formulario nombre proyecto → 📋 Pendiente
  - T-1.4.1b: Step 2: Briefing form → 📋 Pendiente
  - T-1.4.1c: Steps 3-5: Previews (Charter, Roadmap, Blueprint) → 📋 Pendiente
  - T-1.4.1d: Step 6: Estructura + finalización → 📋 Pendiente

### US-1.5.1: CI/CD & Deploy
- **Estado:** 📋 Pendiente
- **Tareas:**
  - T-1.5.1a: GitHub Actions setup → 📋 Pendiente
  - T-1.5.1b: Configurar Vercel deployment → 📋 Pendiente

## Estructura objetivo

```
src/
├── app/
│   ├── step/
│   │   └── [id]/
│   │       └── page.tsx    # Rutas dinámicas /step/1...6
│   └── components/
│       └── Stepper.tsx     # Navegación visual
└── lib/
    └── store.ts            # Estado global (Zustand)
```

## Rutas del wizard

- `/step/1` → Nombre proyecto + iniciar
- `/step/2` → Briefing form
- `/step/3` → Charter preview
- `/step/4` → Roadmap preview
- `/step/5` → Blueprint preview
- `/step/6` → Estructura + finalizar  