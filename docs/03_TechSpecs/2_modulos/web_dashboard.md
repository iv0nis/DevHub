# TechSpecs - Web Dashboard

## 1. Introducción

### Propósito
Especificar la implementación técnica del Web Dashboard UI, interfaz web que proporciona visualización en tiempo real del estado del proyecto, métricas de agentes, y control de operaciones del sistema DevHub.

### Alcance
- Implementación del frontend web con Next.js y componentes React
- Integración con PMS Core para visualización de datos en tiempo real
- Dashboard de métricas y KPIs del proyecto
- Panel de control para operaciones de agentes
- Sistema de notificaciones y alertas

### Referencias
- **Blueprint**: docs/02_blueprint.yaml (componentes.web_dashboard_ui)
- **Charter**: docs/01_ProjectCharter.yaml
- **HLD Components**: Pilar UI en arquitectura de 3 pilares (PMS + DAS + UI)
- **User Stories**: US relacionadas con interfaz de usuario y visualización
- **ADRs**: ADR-002 CLI + Web interfaces

### Contexto
- **Propósito**: Resolver la necesidad de interfaz visual para monitoreo y control del sistema DevHub
- **Alcance incluido**: [Dashboard components, Real-time metrics, Agent control panel, Notification system, Responsive UI]
- **Alcance excluido**: [Agent implementation, PMS operations, File system direct access, Authentication system]
- **Suposiciones**: [Node.js disponible, PMS Core operativo, Puerto 3000 disponible, Navegador moderno]
- **Restricciones**:
  - **Técnicas**: [Next.js 13+, React 18+, TypeScript, Tailwind CSS]
  - **Regulatorias**: [Solo lectura de datos críticos via API]
  - **Temporales**: [Actualizaciones UI < 2 segundos, Load time < 3 segundos]

## 2. Descripción del Módulo

### Información General
- **Nombre**: Web Dashboard UI
- **Responsabilidades**: Visualización de estado del proyecto, control de agentes, mostrar métricas en tiempo real, interfaz de usuario
- **Relación con otros módulos**: Consume datos via PMS Core, muestra estado de DAS Enforcer, interfaz para control de agentes

### Diagramas
- **Componentes**: docs/03_TechSpecs/3_diseno_detallado/componentes_web_dashboard.png
- **Flujo de datos**: docs/03_TechSpecs/3_diseno_detallado/flujo_datos_dashboard.png

## 3. Diseño Detallado

### Componentes y Estructura

### Estructura del Proyecto Web
```
web-dashboard/
├── package.json
├── next.config.js
├── tailwind.config.js
├── src/
│   ├── pages/
│   │   ├── index.tsx           # Dashboard principal
│   │   ├── blueprint/
│   │   │   └── index.tsx       # Blueprint status
│   │   ├── agents/
│   │   │   └── index.tsx       # Agent activity
│   │   └── api/
│   │       ├── project/
│   │       │   └── status.ts   # Project status API
│   │       ├── blueprint/
│   │       │   └── completeness.ts
│   │       └── agents/
│   │           └── activity.ts
│   ├── components/
│   │   ├── ui/                 # Componentes base
│   │   ├── charts/             # Chart components  
│   │   ├── layout/             # Layout components
│   │   └── features/           # Feature components
│   ├── hooks/                  # Custom React hooks
│   ├── services/               # API services
│   ├── types/                  # TypeScript types
│   └── utils/                  # Utilities
└── public/
    ├── favicon.ico
    └── logo.png
```

## 3. Componentes Principales

### 3.1 Dashboard Principal
```typescript
// src/pages/index.tsx
import React from 'react'
import { useQuery } from 'react-query'
import { ProjectOverview } from '@/components/features/ProjectOverview'
import { BlueprintStatus } from '@/components/features/BlueprintStatus'
import { AgentActivity } from '@/components/features/AgentActivity'
import { DocumentSync } from '@/components/features/DocumentSync'

export default function Dashboard() {
  const { data: projectStatus, isLoading } = useQuery(
    'project-status',
    () => fetchProjectStatus(),
    { refetchInterval: 30000 } // Refetch every 30s
  )

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">
            DevHub Dashboard - {projectStatus?.project_name}
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProjectOverview status={projectStatus} />
          <BlueprintStatus />
          <AgentActivity />
          <DocumentSync />
        </div>
      </main>
    </div>
  )
}

// Fetch function
async function fetchProjectStatus(): Promise<ProjectStatus> {
  const response = await fetch('/api/project/status')
  if (!response.ok) {
    throw new Error('Failed to fetch project status')
  }
  return response.json()
}
```

### 3.2 Project Overview Component
```typescript
// src/components/features/ProjectOverview.tsx
import React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ProgressBar } from '@/components/ui/ProgressBar'

interface ProjectOverviewProps {
  status: ProjectStatus
}

export function ProjectOverview({ status }: ProjectOverviewProps) {
  const healthColor = {
    healthy: 'green',
    warning: 'yellow', 
    critical: 'red'
  }[status.health.overall_status]

  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold">Project Overview</h2>
        <Badge color={healthColor}>
          {status.health.overall_status.toUpperCase()}
        </Badge>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Current Phase */}
          <div>
            <label className="text-sm font-medium text-gray-600">
              Current Phase
            </label>
            <div className="text-lg">Fase {status.current_state.fase_actual}</div>
          </div>

          {/* Task Progress */}
          <div>
            <label className="text-sm font-medium text-gray-600">
              Task Progress
            </label>
            <ProgressBar
              current={status.current_state.tasks_completed}
              total={status.current_state.tasks_completed + status.current_state.tasks_pending}
              label={`${status.current_state.tasks_completed} completed, ${status.current_state.tasks_pending} pending`}
            />
          </div>

          {/* Blueprint Completeness */}  
          <div>
            <label className="text-sm font-medium text-gray-600">
              Blueprint Completeness
            </label>
            <ProgressBar
              current={status.current_state.blueprint_completeness * 100}
              total={100}
              label={`${Math.round(status.current_state.blueprint_completeness * 100)}%`}
            />
          </div>

          {/* Last Activity */}
          <div>
            <label className="text-sm font-medium text-gray-600">
              Last Activity
            </label>
            <div className="text-sm">
              <span className="font-medium">{status.last_activity.agent}</span> 
              {' '}{status.last_activity.action}
              <div className="text-xs text-gray-500">
                {new Date(status.last_activity.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### 3.3 Blueprint Status Component
```typescript
// src/components/features/BlueprintStatus.tsx
import React from 'react'
import { useQuery } from 'react-query'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts'

export function BlueprintStatus() {
  const { data: completeness, isLoading } = useQuery(
    'blueprint-completeness',
    () => fetchBlueprintCompleteness(),
    { refetchInterval: 60000 }
  )

  if (isLoading) {
    return <Card><CardContent>Loading...</CardContent></Card>
  }

  const pieData = Object.entries(completeness?.breakdown || {}).map(([key, value]) => ({
    name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: Math.round(value * 100),
    weight: completeness?.weights?.[key] || 0
  }))

  const overallScore = Math.round(completeness?.score * 100)
  const isReady = overallScore >= 80

  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold">Blueprint Status</h2>
        <div className="flex items-center space-x-2">
          <div className={`text-2xl font-bold ${isReady ? 'text-green-600' : 'text-yellow-600'}`}>
            {overallScore}%
          </div>
          <Badge color={isReady ? 'green' : 'yellow'}>
            {isReady ? 'Ready for TechSpecs' : 'In Development'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Recommendations */}
        {!isReady && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-md">
            <h4 className="text-sm font-medium text-yellow-800">Recommendations:</h4>
            <ul className="text-sm text-yellow-700 mt-1 space-y-1">
              {pieData
                .filter(item => item.value < 50)
                .map(item => (
                  <li key={item.name}>• Focus on {item.name.toLowerCase()}</li>
                ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getColor(value: number): string {
  if (value >= 80) return '#10b981' // green
  if (value >= 50) return '#f59e0b' // yellow  
  return '#ef4444' // red
}
```

### 3.4 Agent Activity Component
```typescript
// src/components/features/AgentActivity.tsx
import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'

export function AgentActivity() {
  const [selectedAgent, setSelectedAgent] = useState<string>('all')
  
  const { data: activity, isLoading } = useQuery(
    ['agent-activity', selectedAgent],
    () => fetchAgentActivity(selectedAgent),
    { 
      refetchInterval: 10000, // Real-time updates
      refetchIntervalInBackground: false 
    }
  )

  const agents = ['all', 'BlueprintAgent', 'DevAgent', 'QAAgent']

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Agent Activity</h2>
          
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            {agents.map(agent => (
              <option key={agent} value={agent}>
                {agent === 'all' ? 'All Agents' : agent}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {activity?.map((entry: ActivityEntry) => (
            <div key={entry.id} className="flex items-start space-x-3 p-3 border rounded-md">
              <div className="flex-shrink-0 mt-1">
                {entry.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : entry.status === 'running' ? (
                  <Clock className="h-5 w-5 text-blue-500 animate-pulse" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-sm">{entry.agent_name}</span>
                  <Badge size="sm" color={getStatusColor(entry.status)}>
                    {entry.status}
                  </Badge>
                </div>
                
                <div className="text-sm text-gray-600 mt-1">
                  {entry.action}
                </div>
                
                {entry.files_modified && entry.files_modified.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    Modified: {entry.files_modified.join(', ')}
                  </div>
                )}
                
                <div className="text-xs text-gray-400 mt-1">
                  {formatRelativeTime(entry.timestamp)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {activity?.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No recent activity
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed': return 'green'
    case 'running': return 'blue'
    case 'failed': return 'red'
    default: return 'gray'
  }
}

function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}
```

## 4. API Routes Implementation

### 4.1 Project Status API
```typescript
// src/pages/api/project/status.ts
import { NextApiRequest, NextApiResponse } from 'next'
import { PythonShell } from 'python-shell'
import path from 'path'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const projectPath = req.query.path as string || process.cwd()
    
    // Ejecutar script Python para obtener status via PMS
    const pythonScript = path.join(process.cwd(), 'scripts', 'get_project_status.py')
    
    const results = await PythonShell.run(pythonScript, {
      args: [projectPath],
      mode: 'json'
    })

    const projectStatus = results[0] as ProjectStatus

    // Enrich con métricas adicionales
    const enrichedStatus = {
      ...projectStatus,
      health: await calculateProjectHealth(projectStatus),
      metrics: await getProjectMetrics(projectPath)
    }

    res.status(200).json(enrichedStatus)
    
  } catch (error) {
    console.error('Error fetching project status:', error)
    res.status(500).json({ 
      error: 'Failed to fetch project status',
      message: error.message 
    })
  }
}

async function calculateProjectHealth(status: ProjectStatus): Promise<HealthStatus> {
  const issues = []
  const warnings = []

  // Check blueprint completeness
  if (status.current_state.blueprint_completeness < 0.6) {
    issues.push('Blueprint completeness below 60%')
  } else if (status.current_state.blueprint_completeness < 0.8) {
    warnings.push('Blueprint completeness below 80%')
  }

  // Check pending tasks
  const totalTasks = status.current_state.tasks_completed + status.current_state.tasks_pending
  const completionRate = totalTasks > 0 ? status.current_state.tasks_completed / totalTasks : 1
  
  if (completionRate < 0.3) {
    issues.push('Low task completion rate')
  }

  // Determine overall status
  let overall_status: 'healthy' | 'warning' | 'critical'
  if (issues.length > 0) {
    overall_status = 'critical'
  } else if (warnings.length > 0) {
    overall_status = 'warning'
  } else {
    overall_status = 'healthy'
  }

  return {
    overall_status,
    critical_issues: issues,
    warnings
  }
}
```

### 4.2 Blueprint Completeness API
```typescript  
// src/pages/api/blueprint/completeness.ts
import { NextApiRequest, NextApiResponse } from 'next'
import { PythonShell } from 'python-shell'
import path from 'path'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const projectPath = req.query.path as string || process.cwd()
    
    // Ejecutar script de evaluación de blueprint
    const evaluationScript = path.join(process.cwd(), 'das', 'tools', 'evaluate_blueprint_completeness.py')
    
    const options = {
      mode: 'json' as const,
      pythonPath: 'python3',
      args: [
        '--charter', path.join(projectPath, 'docs/01_ProjectCharter'),
        '--blueprint', path.join(projectPath, 'docs/blueprint.yaml'),
        '--weights', path.join(projectPath, 'das/tools/weights.yml'),
        '--json-output' // Flag para output JSON
      ]
    }

    const results = await PythonShell.run(evaluationScript, options)
    const completenessData = results[0]

    // Add additional metadata
    const response = {
      ...completenessData,
      last_evaluated: new Date().toISOString(),
      ready_for_techspecs: completenessData.score >= 0.8,
      next_milestone: completenessData.score >= 0.8 ? 'TechSpecs Development' : 'Blueprint Completion'
    }

    res.status(200).json(response)
    
  } catch (error) {
    console.error('Error evaluating blueprint:', error)
    res.status(500).json({ 
      error: 'Failed to evaluate blueprint completeness',
      message: error.message 
    })
  }
}
```

### 4.3 Agent Activity API
```typescript
// src/pages/api/agents/activity.ts
import { NextApiRequest, NextApiResponse } from 'next'
import { readFileSync } from 'fs'
import { join } from 'path'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse  
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const projectPath = req.query.path as string || process.cwd()
    const agentFilter = req.query.agent as string || 'all'
    const limit = parseInt(req.query.limit as string) || 50

    // Leer audit log de DAS
    const auditLogPath = join(projectPath, 'memory', 'das_audit.log')
    
    let activities: ActivityEntry[] = []
    
    try {
      const logContent = readFileSync(auditLogPath, 'utf-8')
      const logLines = logContent.trim().split('\n')
      
      activities = logLines
        .filter(line => line.trim())
        .map(line => JSON.parse(line))
        .filter(entry => agentFilter === 'all' || entry.agent_name === agentFilter)
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, limit)
        .map(entry => ({
          id: `${entry.timestamp}-${entry.agent_name}`,
          agent_name: entry.agent_name,
          action: entry.operation === 'read' ? `Read ${entry.scope}` : `Write ${entry.scope}`,
          status: entry.success ? 'completed' : 'failed',
          success: entry.success,
          timestamp: entry.timestamp,
          files_modified: entry.success && entry.operation === 'write' ? [entry.scope] : [],
          details: entry.details
        }))
        
    } catch (fileError) {
      // Si no existe audit log, retornar array vacío
      console.warn('Audit log not found, returning empty activity')
    }

    res.status(200).json(activities)
    
  } catch (error) {
    console.error('Error fetching agent activity:', error)
    res.status(500).json({ 
      error: 'Failed to fetch agent activity',
      message: error.message 
    })
  }
}
```

## 5. Real-time Features

### 5.1 File System Monitoring
```typescript
// src/services/fileSystemMonitor.ts
import chokidar from 'chokidar'
import { EventEmitter } from 'events'

export class FileSystemMonitor extends EventEmitter {
  private watcher: chokidar.FSWatcher | null = null
  private projectPath: string

  constructor(projectPath: string) {
    super()
    this.projectPath = projectPath
  }

  start() {
    // Watch critical DevHub files
    const watchPaths = [
      `${this.projectPath}/docs/blueprint.yaml`,
      `${this.projectPath}/memory/project_status.md`,
      `${this.projectPath}/docs/05_backlog/*.yaml`,
      `${this.projectPath}/memory/das_audit.log`
    ]

    this.watcher = chokidar.watch(watchPaths, {
      ignored: /(^|[\/\\])\../, // ignore dotfiles
      persistent: true
    })

    this.watcher
      .on('change', (path) => {
        this.emit('file-changed', { path, type: 'changed' })
      })
      .on('add', (path) => {
        this.emit('file-changed', { path, type: 'added' })
      })

    console.log(`File system monitoring started for: ${this.projectPath}`)
  }

  stop() {
    if (this.watcher) {
      this.watcher.close()
      this.watcher = null
    }
  }
}
```

### 5.2 WebSocket Integration  
```typescript
// src/services/websocket.ts
import { Server } from 'socket.io'
import { FileSystemMonitor } from './fileSystemMonitor'

export function setupWebSocket(server: any) {
  const io = new Server(server, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  })

  io.on('connection', (socket) => {
    console.log('Client connected:', socket.id)
    
    const monitor = new FileSystemMonitor(process.cwd())
    
    monitor.on('file-changed', (event) => {
      // Emit file change events to connected clients
      socket.emit('project-updated', {
        type: 'file-change',
        data: event,
        timestamp: new Date().toISOString()
      })
    })

    monitor.start()

    socket.on('disconnect', () => {
      console.log('Client disconnected:', socket.id)
      monitor.stop()
    })
  })

  return io
}
```

## 6. Types y Interfaces

### 6.1 TypeScript Definitions
```typescript
// src/types/index.ts

export interface ProjectStatus {
  project_name: string
  version: string
  current_state: {
    fase_actual: number
    blueprint_completeness: number
    tasks_completed: number
    tasks_pending: number
    last_sync: string
  }
  last_activity: {
    agent: string
    action: string
    timestamp: string
    files_modified: string[]
  }
  metrics: ProjectMetrics
  health: HealthStatus
}

export interface ProjectMetrics {
  development_velocity: number
  blueprint_evolution: number
  sync_reliability: number
}

export interface HealthStatus {
  overall_status: 'healthy' | 'warning' | 'critical'
  critical_issues: string[]
  warnings: string[]
}

export interface CompletenessReport {
  score: number
  breakdown: Record<string, number>
  weights: Record<string, number>
  ready_for_techspecs: boolean
  last_evaluated: string
  next_milestone: string
}

export interface ActivityEntry {
  id: string
  agent_name: string
  action: string
  status: 'completed' | 'running' | 'failed'
  success: boolean
  timestamp: string
  files_modified: string[]
  details?: string
}

export interface SyncStatus {
  last_sync: string
  pending_syncs: string[]
  sync_errors: string[]
  is_synchronized: boolean
}
```

## 7. Deployment y Build

### 7.1 Package.json Configuration
```json
{
  "name": "devhub-web-dashboard",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-query": "^3.39.0",
    "recharts": "^2.8.0",
    "chokidar": "^3.5.3",
    "socket.io": "^4.7.0",
    "socket.io-client": "^4.7.0",
    "python-shell": "^5.0.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### 7.2 Next.js Configuration
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // API routes configuration
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
    responseLimit: '8mb',
  },

  // Custom webpack config for Python integration
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Server-side only packages
      config.externals.push('python-shell')
    }
    return config
  },

  // Environment variables
  env: {
    DEVHUB_PROJECT_PATH: process.env.DEVHUB_PROJECT_PATH || process.cwd(),
    PYTHON_PATH: process.env.PYTHON_PATH || 'python3'
  }
}

module.exports = nextConfig
```

## 8. Testing Strategy

### 8.1 Component Testing
```typescript
// src/components/__tests__/ProjectOverview.test.tsx
import { render, screen } from '@testing-library/react'
import { ProjectOverview } from '../features/ProjectOverview'

const mockProjectStatus = {
  project_name: 'Test Project',
  current_state: {
    fase_actual: 1,
    blueprint_completeness: 0.75,
    tasks_completed: 8,
    tasks_pending: 4
  },
  health: {
    overall_status: 'healthy' as const,
    critical_issues: [],
    warnings: []
  },
  last_activity: {
    agent: 'DevAgent',
    action: 'task.completed',
    timestamp: '2025-08-09T12:00:00Z',
    files_modified: []
  }
}

describe('ProjectOverview', () => {
  it('renders project status correctly', () => {
    render(<ProjectOverview status={mockProjectStatus} />)
    
    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('Fase 1')).toBeInTheDocument()
    expect(screen.getByText('8 completed, 4 pending')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('shows correct health status badge', () => {
    render(<ProjectOverview status={mockProjectStatus} />)
    
    const healthBadge = screen.getByText('HEALTHY')
    expect(healthBadge).toBeInTheDocument()
    expect(healthBadge).toHaveClass('bg-green')
  })
})
```

### 8.2 API Testing
```typescript
// src/pages/api/__tests__/project/status.test.ts
import { createMocks } from 'node-mocks-http'
import handler from '../../project/status'

describe('/api/project/status', () => {
  it('returns project status successfully', async () => {
    const { req, res } = createMocks({
      method: 'GET',
      query: { path: './test-project' }
    })

    await handler(req, res)

    expect(res._getStatusCode()).toBe(200)
    
    const data = JSON.parse(res._getData())
    expect(data).toHaveProperty('project_name')
    expect(data).toHaveProperty('current_state')
    expect(data).toHaveProperty('health')
  })

  it('handles invalid project path', async () => {
    const { req, res } = createMocks({
      method: 'GET',
      query: { path: './nonexistent-project' }
    })

    await handler(req, res)

    expect(res._getStatusCode()).toBe(500)
  })
})
```