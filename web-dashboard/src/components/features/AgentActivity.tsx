import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { ActivityEntry } from '@/types'

export function AgentActivity() {
  const [selectedAgent, setSelectedAgent] = useState<string>('all')
  
  const { data: activity, isLoading, error } = useQuery(
    ['agent-activity', selectedAgent],
    () => fetchAgentActivity(selectedAgent),
    { 
      refetchInterval: 10000, // Real-time updates every 10s
      refetchIntervalInBackground: false,
      retry: 1
    }
  )

  const agents = ['all', 'BluePrintAgent', 'DevAgent', 'QAAgent', 'AiProjectManager']

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Agent Activity</h2>
          
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        {isLoading && (
          <LoadingSpinner className="py-8" />
        )}

        {error && (
          <div className="text-center py-8">
            <div className="text-red-600 text-sm">
              {error instanceof Error ? error.message : 'Failed to load agent activity'}
            </div>
          </div>
        )}

        {activity && (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {activity.length > 0 ? activity.map((entry: ActivityEntry) => (
              <div key={entry.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                <div className="flex-shrink-0 mt-1">
                  <StatusIcon status={entry.status} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-medium text-sm text-gray-900">
                      {entry.agent_name}
                    </span>
                    <Badge size="sm" color={getStatusColor(entry.status)}>
                      {entry.status}
                    </Badge>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-1">
                    {entry.action}
                  </div>
                  
                  {entry.files_modified && entry.files_modified.length > 0 && (
                    <div className="text-xs text-gray-500 mb-1">
                      Modified: {entry.files_modified.join(', ')}
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-400">
                    {formatRelativeTime(entry.timestamp)}
                  </div>

                  {entry.details && (
                    <div className="text-xs text-gray-500 mt-1 italic">
                      {entry.details}
                    </div>
                  )}
                </div>
              </div>
            )) : (
              <div className="text-center text-gray-500 py-8">
                No recent activity found
                {selectedAgent !== 'all' && (
                  <div className="text-xs mt-1">
                    Try selecting "All Agents" to see more activity
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return (
        <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
          <div className="w-2 h-2 bg-green-500 rounded-full" />
        </div>
      )
    case 'running':
      return (
        <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        </div>
      )
    case 'failed':
      return (
        <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center">
          <div className="w-2 h-2 bg-red-500 rounded-full" />
        </div>
      )
    default:
      return (
        <div className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center">
          <div className="w-2 h-2 bg-gray-400 rounded-full" />
        </div>
      )
  }
}

function getStatusColor(status: string): 'green' | 'blue' | 'red' | 'gray' {
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

async function fetchAgentActivity(agentFilter: string): Promise<ActivityEntry[]> {
  const params = new URLSearchParams({
    agent: agentFilter,
    limit: '50'
  })
  
  const response = await fetch(`/api/agents/activity?${params}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch agent activity: ${response.statusText}`)
  }
  return response.json()
}