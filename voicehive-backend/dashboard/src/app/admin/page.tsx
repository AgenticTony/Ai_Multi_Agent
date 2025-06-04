'use client'

import { useState, useEffect } from 'react'
import { Shield, Users, Database, Activity, Server, AlertTriangle, CheckCircle, Clock, Trash2, Edit, Plus } from 'lucide-react'
import Navbar from '@/components/Navbar'

interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'user' | 'viewer'
  status: 'active' | 'inactive' | 'suspended'
  lastLogin: string
  createdAt: string
}

interface SystemInfo {
  version: string
  uptime: string
  memoryUsage: number
  cpuUsage: number
  diskUsage: number
  activeConnections: number
  totalRequests: number
  errorRate: number
}

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([])
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    version: '2.1.0',
    uptime: '15 days, 4 hours',
    memoryUsage: 68,
    cpuUsage: 23,
    diskUsage: 45,
    activeConnections: 127,
    totalRequests: 45892,
    errorRate: 0.02
  })
  const [activeTab, setActiveTab] = useState('users')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading admin data
    const loadAdminData = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        setUsers([
          {
            id: '1',
            name: 'John Admin',
            email: 'john@voicehive.com',
            role: 'admin',
            status: 'active',
            lastLogin: '2 hours ago',
            createdAt: '2024-01-15'
          },
          {
            id: '2',
            name: 'Sarah Manager',
            email: 'sarah@voicehive.com',
            role: 'user',
            status: 'active',
            lastLogin: '1 day ago',
            createdAt: '2024-02-20'
          },
          {
            id: '3',
            name: 'Mike Viewer',
            email: 'mike@voicehive.com',
            role: 'viewer',
            status: 'inactive',
            lastLogin: '1 week ago',
            createdAt: '2024-03-10'
          },
          {
            id: '4',
            name: 'Lisa Support',
            email: 'lisa@voicehive.com',
            role: 'user',
            status: 'suspended',
            lastLogin: '3 days ago',
            createdAt: '2024-01-30'
          }
        ])
      } catch (error) {
        console.error('Failed to load admin data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadAdminData()
  }, [])

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800'
      case 'user':
        return 'bg-blue-100 text-blue-800'
      case 'viewer':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800'
      case 'suspended':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getUsageColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-red-500'
    if (percentage >= 60) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const tabs = [
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'system', label: 'System Info', icon: Server },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'logs', label: 'System Logs', icon: Activity }
  ]

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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Shield className="h-8 w-8 mr-3 text-primary-600" />
                Admin Panel
              </h1>
              <p className="mt-2 text-gray-600">System administration and user management</p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                System Healthy
              </span>
            </div>
          </div>
        </div>

        <div className="px-4 sm:px-0">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar */}
            <div className="lg:w-64">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-500'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {tab.label}
                    </button>
                  )
                })}
              </nav>
            </div>

            {/* Content */}
            <div className="flex-1">
              {/* User Management */}
              {activeTab === 'users' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">User Management</h3>
                    <button className="btn-primary flex items-center">
                      <Plus className="h-4 w-4 mr-2" />
                      Add User
                    </button>
                  </div>
                  
                  <div className="card overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              User
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Role
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Last Login
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {users.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{user.name}</div>
                                  <div className="text-sm text-gray-500">{user.email}</div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getRoleColor(user.role)}`}>
                                  {user.role}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(user.status)}`}>
                                  {user.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {user.lastLogin}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <div className="flex space-x-2">
                                  <button className="text-primary-600 hover:text-primary-900">
                                    <Edit className="h-4 w-4" />
                                  </button>
                                  <button className="text-red-600 hover:text-red-900">
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* System Info */}
              {activeTab === 'system' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">System Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="card">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <Server className="h-8 w-8 text-blue-500" />
                        </div>
                        <div className="ml-4">
                          <h4 className="text-sm font-medium text-gray-900">Version</h4>
                          <p className="text-2xl font-bold text-gray-900">{systemInfo.version}</p>
                        </div>
                      </div>
                    </div>

                    <div className="card">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <Clock className="h-8 w-8 text-green-500" />
                        </div>
                        <div className="ml-4">
                          <h4 className="text-sm font-medium text-gray-900">Uptime</h4>
                          <p className="text-lg font-bold text-gray-900">{systemInfo.uptime}</p>
                        </div>
                      </div>
                    </div>

                    <div className="card">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <Activity className="h-8 w-8 text-purple-500" />
                        </div>
                        <div className="ml-4">
                          <h4 className="text-sm font-medium text-gray-900">Active Connections</h4>
                          <p className="text-2xl font-bold text-gray-900">{systemInfo.activeConnections}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h4 className="text-lg font-medium text-gray-900 mb-6">Resource Usage</h4>
                    <div className="space-y-6">
                      <div>
                        <div className="flex justify-between text-sm font-medium text-gray-900 mb-2">
                          <span>Memory Usage</span>
                          <span>{systemInfo.memoryUsage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${getUsageColor(systemInfo.memoryUsage)}`}
                            style={{ width: `${systemInfo.memoryUsage}%` }}
                          ></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm font-medium text-gray-900 mb-2">
                          <span>CPU Usage</span>
                          <span>{systemInfo.cpuUsage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${getUsageColor(systemInfo.cpuUsage)}`}
                            style={{ width: `${systemInfo.cpuUsage}%` }}
                          ></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm font-medium text-gray-900 mb-2">
                          <span>Disk Usage</span>
                          <span>{systemInfo.diskUsage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${getUsageColor(systemInfo.diskUsage)}`}
                            style={{ width: `${systemInfo.diskUsage}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Database */}
              {activeTab === 'database' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">Database Management</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="card">
                      <h4 className="text-lg font-medium text-gray-900 mb-4">Database Statistics</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Total Records</span>
                          <span className="text-sm font-medium">1,247,892</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Database Size</span>
                          <span className="text-sm font-medium">2.4 GB</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Last Backup</span>
                          <span className="text-sm font-medium">2 hours ago</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Connection Pool</span>
                          <span className="text-sm font-medium">15/50</span>
                        </div>
                      </div>
                    </div>

                    <div className="card">
                      <h4 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h4>
                      <div className="space-y-3">
                        <button className="w-full btn-secondary text-left">
                          Create Backup
                        </button>
                        <button className="w-full btn-secondary text-left">
                          Optimize Tables
                        </button>
                        <button className="w-full btn-secondary text-left">
                          View Query Log
                        </button>
                        <button className="w-full btn-secondary text-left text-red-600">
                          Clear Cache
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* System Logs */}
              {activeTab === 'logs' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">System Logs</h3>
                  
                  <div className="card">
                    <div className="space-y-4">
                      {[
                        { time: '2024-01-06 17:14:32', level: 'INFO', message: 'User john@voicehive.com logged in successfully' },
                        { time: '2024-01-06 17:12:15', level: 'WARN', message: 'High memory usage detected: 85%' },
                        { time: '2024-01-06 17:10:45', level: 'INFO', message: 'Database backup completed successfully' },
                        { time: '2024-01-06 17:08:22', level: 'ERROR', message: 'Failed to connect to external API: timeout' },
                        { time: '2024-01-06 17:05:10', level: 'INFO', message: 'System health check passed' },
                        { time: '2024-01-06 17:02:33', level: 'INFO', message: 'Call processing completed: ID 12847' },
                        { time: '2024-01-06 17:00:15', level: 'WARN', message: 'Rate limit approaching for API key: vh_live_****' }
                      ].map((log, index) => (
                        <div key={index} className="flex items-start space-x-3 py-2 border-b border-gray-100 last:border-b-0">
                          <span className="text-xs text-gray-500 font-mono w-32 flex-shrink-0">
                            {log.time}
                          </span>
                          <span className={`text-xs font-medium px-2 py-1 rounded flex-shrink-0 ${
                            log.level === 'ERROR' ? 'bg-red-100 text-red-800' :
                            log.level === 'WARN' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {log.level}
                          </span>
                          <span className="text-sm text-gray-900 flex-1">
                            {log.message}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <button className="btn-secondary">
                        Load More Logs
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
