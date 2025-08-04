# Roadmap del MVP Wizard

Roadmap simplificado basado en proto-backlog, enfocado en MVP funcional sin over-engineering.

---

## Fase 1: Init repo
- **US1.1**: Crear rama `feature/mvp-wizard`
- **US1.2**: Setup Next.js básico con TypeScript y Tailwind

## Fase 2: Setup Next.js con stepper básico
- **US2.1**: Crear estructura `src/app/step/[step]`
- **US2.2**: Implementar navegación Anterior/Siguiente
- **US2.3**: Progress bar visual 1-6

## Fase 3: Integrar PMS-Core
- **US3.1**: Crear API routes básicas `/api/pms/`
- **US3.2**: Bridge directo Python-Node.js
- **US3.3**: Test integración con `pms_core.py`

## Fase 4: Implementar pasos
- **US4.1**: Step 1: Formulario nombre proyecto
- **US4.2**: Step 2: Briefing básico
- **US4.3**: Step 3: Preview Charter generado
- **US4.4**: Step 4: Preview Roadmap generado
- **US4.5**: Step 5: Preview Blueprint generado  
- **US4.6**: Step 6: Mostrar estructura final

## Fase 5: Deploy MVP
- **US5.1**: Deploy manual a Vercel/Netlify
- **US5.2**: Verificar funcionamiento en producción

---

*Roadmap minimalista alineado con proto-backlog - Sin tests, CI/CD, ni validaciones complejas*