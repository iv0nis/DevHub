import React from 'react'
import { useQuery } from 'react-query'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { CompletenessReport } from '@/types'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, Legend } from 'recharts'

export function BlueprintStatus() {
  const { data: completeness, isLoading, error } = useQuery(
    'blueprint-completeness',
    () => fetchBlueprintCompleteness(),
    { 
      refetchInterval: 60000, // Refetch every minute
      retry: 2
    }
  )

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Blueprint Status</h2>
        </CardHeader>
        <CardContent>
          <LoadingSpinner className="py-8" />
        </CardContent>
      </Card>
    )
  }

  if (error || !completeness) {
    return (
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Blueprint Status</h2>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-red-600 text-sm">
              {error instanceof Error ? error.message : 'Failed to load blueprint status'}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const overallScore = Math.round(completeness.score * 100)
  const isReady = overallScore >= 80

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Blueprint Status</h2>
          <div className="flex items-center space-x-3">
            <div className={`text-3xl font-bold ${isReady ? 'text-green-600' : 'text-yellow-600'}`}>
              {overallScore}%
            </div>
            <Badge color={isReady ? 'green' : 'yellow'}>
              {isReady ? 'Ready for TechSpecs' : 'In Development'}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Breakdown Chart */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Component Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart 
                data={Object.entries(completeness.breakdown).map(([key, value]) => ({
                  name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                  completeness: Math.round(value * 100),
                  weight: Math.round((completeness.weights?.[key] || 0.1) * 100)
                }))}
              >
                <XAxis dataKey="name" tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="completeness" fill="#3b82f6" name="Completeness %" />
                <Bar dataKey="weight" fill="#e5e7eb" name="Weight %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Next Milestone */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Next Milestone</span>
              <span className="text-sm font-semibold text-blue-600">
                {completeness.next_milestone}
              </span>
            </div>
          </div>

          {/* Recommendations */}
          {!isReady && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">Recommendations:</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                {Object.entries(completeness.breakdown)
                  .filter(([_, value]) => value < 0.5)
                  .map(([key, _]) => (
                    <li key={key}>
                      • Focus on {key.replace(/_/g, ' ').toLowerCase()}
                    </li>
                  ))}
              </ul>
            </div>
          )}

          {/* Last Evaluated */}
          <div className="text-xs text-gray-500 border-t pt-2">
            Last evaluated: {new Date(completeness.last_evaluated).toLocaleString()}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

async function fetchBlueprintCompleteness(): Promise<CompletenessReport> {
  const response = await fetch('/api/blueprint/completeness')
  if (!response.ok) {
    throw new Error(`Failed to fetch blueprint completeness: ${response.statusText}`)
  }
  return response.json()
}