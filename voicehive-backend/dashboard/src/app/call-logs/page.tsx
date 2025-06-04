'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';

interface CallLog {
  id: string;
  timestamp: string;
  duration: number;
  status: 'completed' | 'failed' | 'in-progress';
  caller: string;
  agent: string;
  summary: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export default function CallLogsPage() {
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Simulate API call to fetch call logs
    const fetchCallLogs = async () => {
      setLoading(true);
      // Mock data - in production this would come from your API
      const mockLogs: CallLog[] = [
        {
          id: 'call-001',
          timestamp: '2025-01-06T15:30:00Z',
          duration: 245,
          status: 'completed',
          caller: '+1-555-0123',
          agent: 'Roxy',
          summary: 'Customer inquiry about appointment scheduling',
          sentiment: 'positive'
        },
        {
          id: 'call-002',
          timestamp: '2025-01-06T15:25:00Z',
          duration: 180,
          status: 'completed',
          caller: '+1-555-0456',
          agent: 'Roxy',
          summary: 'Lead qualification for dental services',
          sentiment: 'neutral'
        },
        {
          id: 'call-003',
          timestamp: '2025-01-06T15:20:00Z',
          duration: 0,
          status: 'failed',
          caller: '+1-555-0789',
          agent: 'Roxy',
          summary: 'Call failed to connect',
          sentiment: 'negative'
        },
        {
          id: 'call-004',
          timestamp: '2025-01-06T15:15:00Z',
          duration: 320,
          status: 'completed',
          caller: '+1-555-0321',
          agent: 'Roxy',
          summary: 'Appointment confirmation and rescheduling',
          sentiment: 'positive'
        },
        {
          id: 'call-005',
          timestamp: '2025-01-06T15:10:00Z',
          duration: 150,
          status: 'in-progress',
          caller: '+1-555-0654',
          agent: 'Roxy',
          summary: 'Currently handling customer support inquiry',
          sentiment: 'neutral'
        }
      ];
      
      setTimeout(() => {
        setCallLogs(mockLogs);
        setLoading(false);
      }, 1000);
    };

    fetchCallLogs();
  }, []);

  const filteredLogs = callLogs.filter(log => {
    const matchesFilter = filter === 'all' || log.status === filter;
    const matchesSearch = log.caller.includes(searchTerm) || 
                         log.summary.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'in-progress': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600';
      case 'negative': return 'text-red-600';
      case 'neutral': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Call Logs</h1>
          <p className="mt-2 text-gray-600">View and analyze all voice interactions</p>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search by phone number or summary..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Calls</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="in-progress">In Progress</option>
              </select>
            </div>
          </div>
        </div>

        {/* Call Logs Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading call logs...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Call ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Caller
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Summary
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sentiment
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {log.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatTimestamp(log.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.caller}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {log.status === 'failed' ? 'N/A' : formatDuration(log.duration)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.agent}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {log.summary}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${getSentimentColor(log.sentiment)}`}>
                          {log.sentiment}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredLogs.length === 0 && (
                <div className="p-8 text-center text-gray-500">
                  No call logs found matching your criteria.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Total Calls</div>
            <div className="text-2xl font-bold text-gray-900">{callLogs.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Completed</div>
            <div className="text-2xl font-bold text-green-600">
              {callLogs.filter(log => log.status === 'completed').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Failed</div>
            <div className="text-2xl font-bold text-red-600">
              {callLogs.filter(log => log.status === 'failed').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Avg Duration</div>
            <div className="text-2xl font-bold text-blue-600">
              {formatDuration(
                Math.round(
                  callLogs
                    .filter(log => log.status === 'completed')
                    .reduce((sum, log) => sum + log.duration, 0) /
                  callLogs.filter(log => log.status === 'completed').length || 0
                )
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
