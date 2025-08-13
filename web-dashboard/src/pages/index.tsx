import React from 'react'
import { useQuery } from 'react-query'
import { ProjectOverview } from '@/components/features/ProjectOverview'
import { BlueprintStatus } from '@/components/features/BlueprintStatus'
import { AgentActivity } from '@/components/features/AgentActivity'
import { DocumentSync } from '@/components/features/DocumentSync'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { ProjectStatus } from '@/types'

export default function Dashboard() {
  const { data: projectStatus, isLoading, error } = useQuery(
    'project-status',
    () => fetchProjectStatus(),
    { 
      refetchInterval: 30000, // Refetch every 30s
      retry: 3
    }
  )

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <div className="mt-4 text-gray-600">Loading DevHub Dashboard...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-lg font-semibold">Error loading dashboard</div>
          <div className="mt-2 text-gray-600">
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">
              DevHub Dashboard
            </h1>
            <div className="text-sm text-gray-600">
              {projectStatus?.project_name && (
                <div className="font-medium">{projectStatus.project_name}</div>
              )}
              <div>Last sync: {new Date().toLocaleTimeString()}</div>
            </div>
          </div>
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

      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="text-center text-sm text-gray-500">
            DevHub Web Dashboard v1.0.0 - Real-time project monitoring
          </div>
        </div>
      </footer>
    </div>
  )
}

// API fetch function
async function fetchProjectStatus(): Promise<ProjectStatus> {
  const response = await fetch('/api/project/status')
  if (!response.ok) {
    throw new Error(`Failed to fetch project status: ${response.statusText}`)
  }
  return response.json()
}