'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import DashboardChart from '@/components/DashboardChart';

interface AnalyticsData {
  callVolume: { date: string; calls: number }[];
  successRate: { date: string; rate: number }[];
  avgDuration: { date: string; duration: number }[];
  sentimentTrends: { date: string; positive: number; neutral: number; negative: number }[];
  hourlyDistribution: { hour: number; calls: number }[];
  topCallers: { phone: string; calls: number; totalDuration: number }[];
  agentPerformance: { agent: string; calls: number; avgDuration: number; successRate: number }[];
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      
      // Mock analytics data - in production this would come from your API
      const mockData: AnalyticsData = {
        callVolume: [
          { date: '2025-01-01', calls: 45 },
          { date: '2025-01-02', calls: 52 },
          { date: '2025-01-03', calls: 38 },
          { date: '2025-01-04', calls: 61 },
          { date: '2025-01-05', calls: 49 },
          { date: '2025-01-06', calls: 67 },
          { date: '2025-01-07', calls: 55 }
        ],
        successRate: [
          { date: '2025-01-01', rate: 92.5 },
          { date: '2025-01-02', rate: 94.2 },
          { date: '2025-01-03', rate: 89.1 },
          { date: '2025-01-04', rate: 96.7 },
          { date: '2025-01-05', rate: 91.8 },
          { date: '2025-01-06', rate: 95.5 },
          { date: '2025-01-07', rate: 93.6 }
        ],
        avgDuration: [
          { date: '2025-01-01', duration: 185 },
          { date: '2025-01-02', duration: 192 },
          { date: '2025-01-03', duration: 178 },
          { date: '2025-01-04', duration: 205 },
          { date: '2025-01-05', duration: 188 },
          { date: '2025-01-06', duration: 198 },
          { date: '2025-01-07', duration: 182 }
        ],
        sentimentTrends: [
          { date: '2025-01-01', positive: 65, neutral: 25, negative: 10 },
          { date: '2025-01-02', positive: 70, neutral: 22, negative: 8 },
          { date: '2025-01-03', positive: 62, neutral: 28, negative: 10 },
          { date: '2025-01-04', positive: 75, neutral: 20, negative: 5 },
          { date: '2025-01-05', positive: 68, neutral: 24, negative: 8 },
          { date: '2025-01-06', positive: 72, neutral: 21, negative: 7 },
          { date: '2025-01-07', positive: 69, neutral: 23, negative: 8 }
        ],
        hourlyDistribution: [
          { hour: 9, calls: 12 },
          { hour: 10, calls: 18 },
          { hour: 11, calls: 25 },
          { hour: 12, calls: 22 },
          { hour: 13, calls: 15 },
          { hour: 14, calls: 28 },
          { hour: 15, calls: 32 },
          { hour: 16, calls: 29 },
          { hour: 17, calls: 20 }
        ],
        topCallers: [
          { phone: '+1-555-0123', calls: 8, totalDuration: 1560 },
          { phone: '+1-555-0456', calls: 6, totalDuration: 1200 },
          { phone: '+1-555-0789', calls: 5, totalDuration: 980 },
          { phone: '+1-555-0321', calls: 4, totalDuration: 840 },
          { phone: '+1-555-0654', calls: 4, totalDuration: 720 }
        ],
        agentPerformance: [
          { agent: 'Roxy', calls: 367, avgDuration: 192, successRate: 94.2 }
        ]
      };

      setTimeout(() => {
        setAnalyticsData(mockData);
        setLoading(false);
      }, 1000);
    };

    fetchAnalytics();
  }, [timeRange]);

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatHour = (hour: number) => {
    return `${hour}:00`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="ml-4 text-gray-600">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Usage Analytics</h1>
            <p className="mt-2 text-gray-600">Comprehensive insights into call patterns and performance</p>
          </div>
          
          <div>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500">Total Calls</div>
            <div className="text-3xl font-bold text-gray-900">
              {analyticsData?.callVolume.reduce((sum, day) => sum + day.calls, 0)}
            </div>
            <div className="text-sm text-green-600 mt-1">+12% from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500">Avg Success Rate</div>
            <div className="text-3xl font-bold text-green-600">
              {analyticsData ? Math.round((analyticsData.successRate.reduce((sum, day) => sum + day.rate, 0) / analyticsData.successRate.length) * 10) / 10 : 0}%
            </div>
            <div className="text-sm text-green-600 mt-1">+2.1% from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500">Avg Call Duration</div>
            <div className="text-3xl font-bold text-blue-600">
              {formatDuration(
                Math.round(
                  analyticsData ? (analyticsData.avgDuration.reduce((sum, day) => sum + day.duration, 0) / analyticsData.avgDuration.length) : 0
                )
              )}
            </div>
            <div className="text-sm text-blue-600 mt-1">-5s from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500">Customer Satisfaction</div>
            <div className="text-3xl font-bold text-purple-600">4.8/5</div>
            <div className="text-sm text-green-600 mt-1">+0.2 from last period</div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Call Volume Chart */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Call Volume Trend</h3>
            <DashboardChart
              data={analyticsData?.callVolume.map(item => ({ name: item.date, value: item.calls })) || []}
              type="line"
              color="#3B82F6"
            />
          </div>

          {/* Success Rate Chart */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Success Rate Trend</h3>
            <DashboardChart
              data={analyticsData?.successRate.map(item => ({ name: item.date, value: item.rate })) || []}
              type="line"
              color="#10B981"
            />
          </div>

          {/* Average Duration Chart */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Call Duration</h3>
            <DashboardChart
              data={analyticsData?.avgDuration.map(item => ({ name: item.date, value: item.duration })) || []}
              type="bar"
              color="#8B5CF6"
            />
          </div>

          {/* Hourly Distribution */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Hourly Call Distribution</h3>
            <DashboardChart
              data={analyticsData?.hourlyDistribution.map(item => ({ name: formatHour(item.hour), value: item.calls })) || []}
              type="bar"
              color="#F59E0B"
            />
          </div>
        </div>

        {/* Sentiment Analysis */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Analysis Trends</h3>
          <div className="h-64">
            {/* This would be a stacked area chart in a real implementation */}
            <div className="grid grid-cols-7 gap-2 h-full">
              {analyticsData?.sentimentTrends.map((day, index) => (
                <div key={index} className="flex flex-col justify-end">
                  <div className="text-xs text-gray-500 mb-1 text-center">
                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="flex flex-col h-32 bg-gray-100 rounded">
                    <div 
                      className="bg-green-500 rounded-t"
                      style={{ height: `${day.positive}%` }}
                      title={`Positive: ${day.positive}%`}
                    ></div>
                    <div 
                      className="bg-yellow-500"
                      style={{ height: `${day.neutral}%` }}
                      title={`Neutral: ${day.neutral}%`}
                    ></div>
                    <div 
                      className="bg-red-500 rounded-b"
                      style={{ height: `${day.negative}%` }}
                      title={`Negative: ${day.negative}%`}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-center mt-4 space-x-6">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
                <span className="text-sm text-gray-600">Positive</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded mr-2"></div>
                <span className="text-sm text-gray-600">Neutral</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
                <span className="text-sm text-gray-600">Negative</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Callers */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Callers</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Phone</th>
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Calls</th>
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Total Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {analyticsData?.topCallers.map((caller, index) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-2 text-sm text-gray-900">{caller.phone}</td>
                      <td className="py-2 text-sm text-gray-600">{caller.calls}</td>
                      <td className="py-2 text-sm text-gray-600">{formatDuration(caller.totalDuration)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Agent Performance */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Agent</th>
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Calls</th>
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Avg Duration</th>
                    <th className="text-left py-2 text-sm font-medium text-gray-500">Success Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {analyticsData?.agentPerformance.map((agent, index) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-2 text-sm text-gray-900">{agent.agent}</td>
                      <td className="py-2 text-sm text-gray-600">{agent.calls}</td>
                      <td className="py-2 text-sm text-gray-600">{formatDuration(agent.avgDuration)}</td>
                      <td className="py-2 text-sm text-green-600 font-medium">{agent.successRate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
