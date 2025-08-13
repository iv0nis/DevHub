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