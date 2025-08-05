# MVP-Wizard - DevHub UI Development & Integration Test

## Objetivo Central

El MVP-Wizard es un **sandbox funcional** para desarrollar el sistema UI de DevHub y validar la integración entre sus 3 pilares fundamentales:

- **PMS** (Persistent Memory System) - Sistema de memoria persistente
- **Agentes** (DevAgent, BluePrintAgent, etc.) - Sistema de agentes autónomos  
- **UI** (User Interface) - Interface de usuario

## ¿Qué es?

Un wizard de 6 pasos que permite a Product Owners generar artifacts clave de proyecto (Charter, Roadmap, Blueprint) simulando el flujo completo que tendrá DevHub en producción.

## ¿Por qué un MVP?

- **Desarrollar UI**: DevHub actualmente no tiene sistema UI - el MVP nos permite construirlo
- **Validar integración**: Probar que PMS + Agentes + UI funcionen juntos antes del DevHub completo
- **Arquitectura evolutiva**: El frontend del MVP se reutilizará 100% en DevHub

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## Documentación

- **[mvp-wizard.md](docs/mvp-wizard.md)** - Arquitectura completa y especificaciones técnicas
- **[Project Charter](docs/projectCharter.md)** - Visión y alcance del MVP
- **[Roadmap](docs/roadmap.md)** - Fases de implementación
- **[DevAgent.yaml](../das/agents/DevAgent.yaml)** - Instrucciones del agente de desarrollo

## Arquitectura

```
mvp-wizard/
├── src/app/step/[step]/     # 6-step wizard interface
├── pms_core.py              # PMS integration
├── memory/                  # Project state storage  
├── docs/                    # Generated artifacts
└── templates/               # PMS templates
```

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
