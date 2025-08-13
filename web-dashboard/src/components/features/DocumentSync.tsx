import React from 'react'
import { useQuery } from 'react-query'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

interface SyncInfo {
  is_synchronized: boolean
  last_sync: string
  pending_syncs: string[]
  sync_errors: string[]
  documents: {
    name: string
    status: 'synced' | 'pending' | 'error'
    last_modified: string
  }[]
}

export function DocumentSync() {
  const { data: syncInfo, isLoading, error } = useQuery(
    'document-sync',
    () => fetchDocumentSync(),
    { 
      refetchInterval: 15000, // Check sync status every 15s
      retry: 1
    }
  )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Document Sync</h2>
          {syncInfo && (
            <Badge color={syncInfo.is_synchronized ? 'green' : 'yellow'}>
              {syncInfo.is_synchronized ? 'Synchronized' : 'Sync Pending'}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading && <LoadingSpinner className="py-8" />}

        {error && (
          <div className="text-center py-8">
            <div className="text-red-600 text-sm">
              {error instanceof Error ? error.message : 'Failed to load sync status'}
            </div>
          </div>
        )}

        {syncInfo && (
          <div className="space-y-4">
            {/* Sync Status Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">Last Sync</div>
                <div className="text-sm font-medium">
                  {formatRelativeTime(syncInfo.last_sync)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Status</div>
                <div className="text-sm font-medium">
                  {syncInfo.pending_syncs.length > 0 
                    ? `${syncInfo.pending_syncs.length} pending`
                    : 'Up to date'
                  }
                </div>
              </div>
            </div>

            {/* Document List */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">Documents</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {syncInfo.documents.map((doc, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border border-gray-100 rounded">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{doc.name}</div>
                      <div className="text-xs text-gray-500">
                        Modified: {formatRelativeTime(doc.last_modified)}
                      </div>
                    </div>
                    <Badge size="sm" color={getDocStatusColor(doc.status)}>
                      {doc.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* Sync Errors */}
            {syncInfo.sync_errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <div className="text-sm font-medium text-red-800 mb-2">Sync Errors:</div>
                <ul className="text-sm text-red-700 space-y-1">
                  {syncInfo.sync_errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Pending Syncs */}
            {syncInfo.pending_syncs.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="text-sm font-medium text-yellow-800 mb-2">
                  Pending Syncs ({syncInfo.pending_syncs.length}):
                </div>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {syncInfo.pending_syncs.slice(0, 3).map((pending, index) => (
                    <li key={index}>• {pending}</li>
                  ))}
                  {syncInfo.pending_syncs.length > 3 && (
                    <li>• ... and {syncInfo.pending_syncs.length - 3} more</li>
                  )}
                </ul>
              </div>
            )}

            {/* Manual Sync Button */}
            <div className="border-t pt-4">
              <button
                onClick={handleManualSync}
                disabled={isLoading}
                className="w-full px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Force Sync Now
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getDocStatusColor(status: string): 'green' | 'yellow' | 'red' {
  switch (status) {
    case 'synced': return 'green'
    case 'pending': return 'yellow'
    case 'error': return 'red'
    default: return 'gray' as 'green' // fallback
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

async function fetchDocumentSync(): Promise<SyncInfo> {
  const response = await fetch('/api/documents/sync')
  if (!response.ok) {
    throw new Error(`Failed to fetch sync status: ${response.statusText}`)
  }
  return response.json()
}

async function handleManualSync() {
  try {
    const response = await fetch('/api/documents/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to trigger sync')
    }
    
    // Show success message (could use toast notification)
    console.log('Sync triggered successfully')
  } catch (error) {
    console.error('Failed to trigger sync:', error)
    // Show error message (could use toast notification)
  }
}