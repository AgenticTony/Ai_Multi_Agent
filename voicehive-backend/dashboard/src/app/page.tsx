'use client'

import { useState, useEffect } from 'react'
import { Activity, Phone, Users, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import DashboardCard from '@/components/DashboardCard'
import DashboardChart from '@/components/DashboardChart'
import Navbar from '@/components/Navbar'

interface DashboardMetrics {
  totalCalls: number
  activeCalls: number
  successRate: number
  avgDuration: number
  systemHealth: 'healthy' | 'warning' | 'error'
  alerts: number
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalCalls: 0,
    activeCalls: 0,
    successRate: 0,
    avgDuration: 0,
    systemHealth: 'healthy',
    alerts: 0
  })

  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading dashboard data
    const loadDashboardData = async () => {
      try {
        // In a real implementation, this would fetch from your API
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        setMetrics({
          totalCalls: 1247,
          activeCalls: 8,
          successRate: 94.2,
          avgDuration: 4.3,
          systemHealth: 'healthy',
          alerts: 2
        })
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const getHealthStatus = (health: string) => {
    switch (health) {
      case 'healthy':
        return { color: 'text-green-600', icon: CheckCircle, label: 'Healthy' }
      case 'warning':
        return { color: 'text-yellow-600', icon: AlertTriangle, label: 'Warning' }
      case 'error':
        return { color: 'text-red-600', icon: AlertTriangle, label: 'Error' }
      default:
        return { color: 'text-gray-600', icon: Activity, label: 'Unknown' }
    }
  }

  const healthStatus = getHealthStatus(metrics.systemHealth)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Real-time monitoring and analytics for VoiceHive</p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <DashboardCard
            title="Total Calls"
            value={metrics.totalCalls.toLocaleString()}
            icon={Phone}
            trend="+12%"
            trendDirection="up"
          />
          <DashboardCard
            title="Active Calls"
            value={metrics.activeCalls.toString()}
            icon={Activity}
            trend="Live"
            trendDirection="neutral"
          />
          <DashboardCard
            title="Success Rate"
            value={`${metrics.successRate}%`}
            icon={TrendingUp}
            trend="+2.1%"
            trendDirection="up"
          />
          <DashboardCard
            title="Avg Duration"
            value={`${metrics.avgDuration}m`}
            icon={Users}
            trend="-0.3m"
            trendDirection="down"
          />
        </div>

        {/* System Health & Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* System Health */}
          <div className="card">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">System Health</h3>
              <div className={`flex items-center ${healthStatus.color}`}>
                <healthStatus.icon className="h-5 w-5 mr-2" />
                <span className="font-medium">{healthStatus.label}</span>
              </div>
            </div>
            <div className="mt-4">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">API Response Time</span>
                  <span className="text-sm font-medium text-green-600">45ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Memory Usage</span>
                  <span className="text-sm font-medium text-yellow-600">72%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Active Alerts</span>
                  <span className="text-sm font-medium text-red-600">{metrics.alerts}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Call Volume Chart */}
          <div className="lg:col-span-2 card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Call Volume (24h)</h3>
            <DashboardChart 
              data={[
                { name: '00:00', value: 12 },
                { name: '02:00', value: 8 },
                { name: '04:00', value: 5 },
                { name: '06:00', value: 15 },
                { name: '08:00', value: 32 },
                { name: '10:00', value: 45 },
                { name: '12:00', value: 38 },
                { name: '14:00', value: 42 },
                { name: '16:00', value: 35 },
                { name: '18:00', value: 28 },
                { name: '20:00', value: 22 },
                { name: '22:00', value: 18 },
              ]}
              type="line"
              color="#3b82f6"
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {[
              { time: '2 minutes ago', event: 'Call completed successfully', status: 'success' },
              { time: '5 minutes ago', event: 'New appointment scheduled', status: 'info' },
              { time: '8 minutes ago', event: 'System health check passed', status: 'success' },
              { time: '12 minutes ago', event: 'High memory usage detected', status: 'warning' },
              { time: '15 minutes ago', event: 'Call failed - network timeout', status: 'error' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-3 ${
                    activity.status === 'success' ? 'bg-green-500' :
                    activity.status === 'warning' ? 'bg-yellow-500' :
                    activity.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                  }`}></div>
                  <span className="text-sm text-gray-900">{activity.event}</span>
                </div>
                <span className="text-xs text-gray-500">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
