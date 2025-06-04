'use client'

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'

interface DashboardCardProps {
  title: string
  value: string
  icon: LucideIcon
  trend?: string
  trendDirection?: 'up' | 'down' | 'neutral'
  className?: string
}

export default function DashboardCard({
  title,
  value,
  icon: Icon,
  trend,
  trendDirection = 'neutral',
  className = ''
}: DashboardCardProps) {
  const getTrendColor = () => {
    switch (trendDirection) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getTrendIcon = () => {
    switch (trendDirection) {
      case 'up':
        return TrendingUp
      case 'down':
        return TrendingDown
      default:
        return null
    }
  }

  const TrendIcon = getTrendIcon()

  return (
    <div className={`metric-card ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Icon className="h-6 w-6 text-primary-600" />
          </div>
        </div>
        {trend && (
          <div className={`flex items-center ${getTrendColor()}`}>
            {TrendIcon && <TrendIcon className="h-4 w-4 mr-1" />}
            <span className="text-sm font-medium">{trend}</span>
          </div>
        )}
      </div>
      
      <div className="mt-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      </div>
    </div>
  )
}
