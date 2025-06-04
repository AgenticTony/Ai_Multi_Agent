'use client'

import { useState, useEffect } from 'react'
import { Settings, Save, RefreshCw, Shield, Bell, Palette, Database, Globe } from 'lucide-react'
import Navbar from '@/components/Navbar'

interface SettingsData {
  general: {
    companyName: string
    timezone: string
    language: string
    dateFormat: string
  }
  notifications: {
    emailNotifications: boolean
    smsNotifications: boolean
    pushNotifications: boolean
    callAlerts: boolean
    systemAlerts: boolean
  }
  security: {
    twoFactorAuth: boolean
    sessionTimeout: number
    passwordExpiry: number
    ipWhitelist: string
  }
  api: {
    rateLimit: number
    webhookUrl: string
    apiKey: string
    enableLogging: boolean
  }
  appearance: {
    theme: 'light' | 'dark' | 'auto'
    primaryColor: string
    compactMode: boolean
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData>({
    general: {
      companyName: 'VoiceHive Corp',
      timezone: 'UTC',
      language: 'en',
      dateFormat: 'MM/DD/YYYY'
    },
    notifications: {
      emailNotifications: true,
      smsNotifications: false,
      pushNotifications: true,
      callAlerts: true,
      systemAlerts: true
    },
    security: {
      twoFactorAuth: true,
      sessionTimeout: 30,
      passwordExpiry: 90,
      ipWhitelist: ''
    },
    api: {
      rateLimit: 1000,
      webhookUrl: '',
      apiKey: 'vh_live_••••••••••••••••',
      enableLogging: true
    },
    appearance: {
      theme: 'light',
      primaryColor: '#3B82F6',
      compactMode: false
    }
  })

  const [activeTab, setActiveTab] = useState('general')
  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  const handleSave = async () => {
    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } finally {
      setIsLoading(false)
    }
  }

  const updateSetting = (section: keyof SettingsData, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }))
  }

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'api', label: 'API', icon: Database },
    { id: 'appearance', label: 'Appearance', icon: Palette }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Settings className="h-8 w-8 mr-3 text-primary-600" />
                Settings
              </h1>
              <p className="mt-2 text-gray-600">Manage your VoiceHive configuration and preferences</p>
            </div>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className={`btn-primary flex items-center ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : 'Save Changes'}
            </button>
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
              <div className="card">
                {/* General Settings */}
                {activeTab === 'general' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-6">General Settings</h3>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Name
                        </label>
                        <input
                          type="text"
                          value={settings.general.companyName}
                          onChange={(e) => updateSetting('general', 'companyName', e.target.value)}
                          className="input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Timezone
                        </label>
                        <select
                          value={settings.general.timezone}
                          onChange={(e) => updateSetting('general', 'timezone', e.target.value)}
                          className="input"
                        >
                          <option value="UTC">UTC</option>
                          <option value="America/New_York">Eastern Time</option>
                          <option value="America/Chicago">Central Time</option>
                          <option value="America/Denver">Mountain Time</option>
                          <option value="America/Los_Angeles">Pacific Time</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Language
                        </label>
                        <select
                          value={settings.general.language}
                          onChange={(e) => updateSetting('general', 'language', e.target.value)}
                          className="input"
                        >
                          <option value="en">English</option>
                          <option value="es">Spanish</option>
                          <option value="fr">French</option>
                          <option value="de">German</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* Notification Settings */}
                {activeTab === 'notifications' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-6">Notification Preferences</h3>
                    <div className="space-y-6">
                      {Object.entries(settings.notifications).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 capitalize">
                              {key.replace(/([A-Z])/g, ' $1').trim()}
                            </h4>
                            <p className="text-sm text-gray-500">
                              {key === 'emailNotifications' && 'Receive notifications via email'}
                              {key === 'smsNotifications' && 'Receive notifications via SMS'}
                              {key === 'pushNotifications' && 'Receive browser push notifications'}
                              {key === 'callAlerts' && 'Get alerted about call events'}
                              {key === 'systemAlerts' && 'Receive system status alerts'}
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={value}
                              onChange={(e) => updateSetting('notifications', key, e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Security Settings */}
                {activeTab === 'security' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-6">Security Settings</h3>
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
                          <p className="text-sm text-gray-500">Add an extra layer of security to your account</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.security.twoFactorAuth}
                            onChange={(e) => updateSetting('security', 'twoFactorAuth', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Session Timeout (minutes)
                        </label>
                        <input
                          type="number"
                          value={settings.security.sessionTimeout}
                          onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                          className="input"
                          min="5"
                          max="480"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Password Expiry (days)
                        </label>
                        <input
                          type="number"
                          value={settings.security.passwordExpiry}
                          onChange={(e) => updateSetting('security', 'passwordExpiry', parseInt(e.target.value))}
                          className="input"
                          min="30"
                          max="365"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* API Settings */}
                {activeTab === 'api' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-6">API Configuration</h3>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Rate Limit (requests per hour)
                        </label>
                        <input
                          type="number"
                          value={settings.api.rateLimit}
                          onChange={(e) => updateSetting('api', 'rateLimit', parseInt(e.target.value))}
                          className="input"
                          min="100"
                          max="10000"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Webhook URL
                        </label>
                        <input
                          type="url"
                          value={settings.api.webhookUrl}
                          onChange={(e) => updateSetting('api', 'webhookUrl', e.target.value)}
                          className="input"
                          placeholder="https://your-domain.com/webhook"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          API Key
                        </label>
                        <div className="flex space-x-2">
                          <input
                            type="text"
                            value={settings.api.apiKey}
                            readOnly
                            className="input flex-1 bg-gray-50"
                          />
                          <button className="btn-secondary">Regenerate</button>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">Enable API Logging</h4>
                          <p className="text-sm text-gray-500">Log all API requests for debugging</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.api.enableLogging}
                            onChange={(e) => updateSetting('api', 'enableLogging', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Appearance Settings */}
                {activeTab === 'appearance' && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-6">Appearance</h3>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Theme
                        </label>
                        <select
                          value={settings.appearance.theme}
                          onChange={(e) => updateSetting('appearance', 'theme', e.target.value)}
                          className="input"
                        >
                          <option value="light">Light</option>
                          <option value="dark">Dark</option>
                          <option value="auto">Auto (System)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Primary Color
                        </label>
                        <div className="flex space-x-2">
                          <input
                            type="color"
                            value={settings.appearance.primaryColor}
                            onChange={(e) => updateSetting('appearance', 'primaryColor', e.target.value)}
                            className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                          />
                          <input
                            type="text"
                            value={settings.appearance.primaryColor}
                            onChange={(e) => updateSetting('appearance', 'primaryColor', e.target.value)}
                            className="input flex-1"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">Compact Mode</h4>
                          <p className="text-sm text-gray-500">Use a more compact layout</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.appearance.compactMode}
                            onChange={(e) => updateSetting('appearance', 'compactMode', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
