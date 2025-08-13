import React from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { ProjectStatus } from '@/types'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts'

interface ProjectOverviewProps {
  status: ProjectStatus | undefined
}

export function ProjectOverview({ status }: ProjectOverviewProps) {
  if (!status) {
    return (
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Project Overview</h2>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            No project data available
          </div>
        </CardContent>
      </Card>
    )
  }

  const healthColor = {
    healthy: 'green',
    warning: 'yellow',
    critical: 'red'
  }[status.health.overall_status] as 'green' | 'yellow' | 'red'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Project Overview</h2>
          <Badge color={healthColor}>
            {status.health.overall_status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          {/* Current Phase */}
          <div>
            <label className="text-sm font-medium text-gray-600">
              Current Phase
            </label>
            <div className="text-2xl font-bold text-gray-900">
              Fase {status.current_state.fase_actual}
            </div>
          </div>

          {/* Task Progress */}
          <div>
            <ProgressBar
              current={status.current_state.tasks_completed}
              total={status.current_state.tasks_completed + status.current_state.tasks_pending}
              label={`Tasks: ${status.current_state.tasks_completed} completed, ${status.current_state.tasks_pending} pending`}
            />
          </div>

          {/* Metrics Visualization */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Task Progress Chart */}
            <div>
              <h3 className="text-lg font-medium mb-3">Task Progress</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Completed', value: status.current_state.tasks_completed, fill: '#10b981' },
                      { name: 'Pending', value: status.current_state.tasks_pending, fill: '#f59e0b' }
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#10b981" />
                    <Cell fill="#f59e0b" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Metrics Chart */}
            <div>
              <h3 className="text-lg font-medium mb-3">Key Metrics</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={[
                  { name: 'Velocity', value: status.metrics.development_velocity || 12.0 },
                  { name: 'Blueprint', value: (status.current_state.blueprint_completeness * 100) || 76.9 },
                  { name: 'Reliability', value: (status.metrics.sync_reliability * 100) || 95 },
                  { name: 'Coverage', value: (status.metrics.test_coverage * 100) || 80 }
                ]}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Last Activity */}
          <div>
            <label className="text-sm font-medium text-gray-600">
              Last Activity
            </label>
            <div className="mt-1">
              <div className="flex items-center space-x-2">
                <span className="font-medium text-blue-600">
                  {status.last_activity.agent}
                </span>
                <span className="text-gray-600">
                  {status.last_activity.action}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {new Date(status.last_activity.timestamp).toLocaleString()}
              </div>
              {status.last_activity.files_modified.length > 0 && (
                <div className="text-xs text-gray-500 mt-1">
                  Modified: {status.last_activity.files_modified.join(', ')}
                </div>
              )}
            </div>
          </div>

          {/* Health Issues */}
          {(status.health.critical_issues.length > 0 || status.health.warnings.length > 0) && (
            <div className="border-t pt-4">
              {status.health.critical_issues.length > 0 && (
                <div className="mb-3">
                  <div className="text-sm font-medium text-red-600">Critical Issues:</div>
                  <ul className="text-sm text-red-700 mt-1 space-y-1">
                    {status.health.critical_issues.map((issue, index) => (
                      <li key={index}>• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {status.health.warnings.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-yellow-600">Warnings:</div>
                  <ul className="text-sm text-yellow-700 mt-1 space-y-1">
                    {status.health.warnings.map((warning, index) => (
                      <li key={index}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}