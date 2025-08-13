import React from 'react'

interface ProgressBarProps {
  current: number
  total: number
  label?: string
  className?: string
}

export function ProgressBar({ 
  current, 
  total, 
  label,
  className = '' 
}: ProgressBarProps) {
  const percentage = total > 0 ? Math.min(100, (current / total) * 100) : 0
  
  return (
    <div className={`space-y-1 ${className}`}>
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {label}
        </div>
        <div className="text-sm font-medium text-gray-900">
          {Math.round(percentage)}%
        </div>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}