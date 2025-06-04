'use client'

import { useState, useEffect } from 'react'
import { Bell, CheckCircle, AlertTriangle, Info, X, Clock } from 'lucide-react'
import Navbar from '@/components/Navbar'

interface Notification {
  id: string
  type: 'success' | 'warning' | 'info' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  actionRequired?: boolean
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [filter, setFilter] = useState<'all' | 'unread' | 'success' | 'warning' | 'error'>('all')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading notifications
    const loadNotifications = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        setNotifications([
          {
            id: '1',
            type: 'success',
            title: 'Call Completed Successfully',
            message: 'Call with customer +1-555-0123 completed successfully. Duration: 4m 32s',
            timestamp: '2 minutes ago',
            read: false
          },
          {
            id: '2',
            type: 'warning',
            title: 'High Memory Usage Detected',
            message: 'System memory usage has reached 85%. Consider scaling resources.',
            timestamp: '5 minutes ago',
            read: false,
            actionRequired: true
          },
          {
            id: '3',
            type: 'info',
            title: 'New Appointment Scheduled',
            message: 'Appointment scheduled for tomorrow at 2:00 PM with John Smith.',
            timestamp: '8 minutes ago',
            read: true
          },
          {
            id: '4',
            type: 'error',
            title: 'Call Failed - Network Timeout',
            message: 'Call to +1-555-0456 failed due to network timeout. Retry recommended.',
            timestamp: '12 minutes ago',
            read: false,
            actionRequired: true
          },
          {
            id: '5',
            type: 'success',
            title: 'System Health Check Passed',
            message: 'All system components are functioning normally.',
            timestamp: '15 minutes ago',
            read: true
          }
        ])
      } catch (error) {
        console.error('Failed to load notifications:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadNotifications()
  }, [])

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      default:
        return <Info className="h-5 w-5 text-blue-500" />
    }
  }

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    )
  }

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    )
  }

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
  }

  const filteredNotifications = notifications.filter(notif => {
    if (filter === 'all') return true
    if (filter === 'unread') return !notif.read
    return notif.type === filter
  })

  const unreadCount = notifications.filter(n => !n.read).length

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
                <Bell className="h-8 w-8 mr-3 text-primary-600" />
                Notifications
                {unreadCount > 0 && (
                  <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    {unreadCount} unread
                  </span>
                )}
              </h1>
              <p className="mt-2 text-gray-600">Stay updated with system alerts and important information</p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="btn-secondary"
              >
                Mark All as Read
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="px-4 sm:px-0 mb-6">
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'All' },
              { key: 'unread', label: 'Unread' },
              { key: 'success', label: 'Success' },
              { key: 'warning', label: 'Warning' },
              { key: 'error', label: 'Error' }
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key as any)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === key
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Notifications List */}
        <div className="px-4 sm:px-0">
          {filteredNotifications.length === 0 ? (
            <div className="card text-center py-12">
              <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications</h3>
              <p className="text-gray-600">
                {filter === 'unread' ? 'All caught up! No unread notifications.' : 'No notifications match your current filter.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`card transition-all hover:shadow-md ${
                    !notification.read ? 'border-l-4 border-l-primary-500 bg-primary-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="flex-shrink-0 mt-1">
                        {getIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className={`text-sm font-medium ${!notification.read ? 'text-gray-900' : 'text-gray-700'}`}>
                            {notification.title}
                          </h3>
                          {notification.actionRequired && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                              Action Required
                            </span>
                          )}
                          {!notification.read && (
                            <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center text-xs text-gray-500">
                          <Clock className="h-3 w-3 mr-1" />
                          {notification.timestamp}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      {!notification.read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        >
                          Mark as read
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
