import React from 'react'

interface BadgeProps {
  children: React.ReactNode
  color?: 'green' | 'yellow' | 'red' | 'blue' | 'gray'
  size?: 'sm' | 'md'
  className?: string
}

export function Badge({ 
  children, 
  color = 'gray', 
  size = 'md',
  className = '' 
}: BadgeProps) {
  const colorClasses = {
    green: 'badge-green',
    yellow: 'badge-yellow', 
    red: 'badge-red',
    blue: 'badge-blue',
    gray: 'badge-gray'
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5'
  }

  return (
    <span className={`badge ${colorClasses[color]} ${sizeClasses[size]} ${className}`}>
      {children}
    </span>
  )
}