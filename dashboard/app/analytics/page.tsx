'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiClient } from '@/lib/api-client';
import { Statistics } from '@/types';
import { Activity, TrendingUp, AlertTriangle, Clock } from 'lucide-react';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Statistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiClient.getStatistics();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  const analyzerStats = stats?.analyzer;
  const metricsStats = stats?.metrics;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Analytics & Insights</h1>

        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="text-purple-600" />
            Performance Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Avg Latency</div>
              <div className="text-2xl font-bold text-blue-600">
                {analyzerStats?.avg_latency_ms.toFixed(1)}ms
              </div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Throughput</div>
              <div className="text-2xl font-bold text-green-600">
                {metricsStats?.requests_per_minute.toFixed(1)} req/min
              </div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Detection Rate</div>
              <div className="text-2xl font-bold text-purple-600">
                {metricsStats?.detection_rate_percent.toFixed(2)}%
              </div>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">False Positives</div>
              <div className="text-2xl font-bold text-orange-600">
                {metricsStats?.false_positive_rate_percent.toFixed(2)}%
              </div>
            </div>
          </div>
        </div>

        {/* Attack Types Distribution */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="text-red-600" />
            Attack Types Distribution
          </h2>
          <div className="space-y-3">
            {metricsStats?.attack_types && Object.entries(metricsStats.attack_types).map(([type, count]) => {
              const total = Object.values(metricsStats.attack_types).reduce((a, b) => a + b, 0);
              const percentage = (count / total) * 100;
              
              return (
                <div key={type}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{type}</span>
                    <span className="text-sm text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Clock className="text-green-600" />
            System Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-l-4 border-green-500 pl-4">
              <div className="text-sm text-gray-600">Total Requests</div>
              <div className="text-2xl font-bold">{analyzerStats?.total_analyzed.toLocaleString()}</div>
            </div>
            <div className="border-l-4 border-red-500 pl-4">
              <div className="text-sm text-gray-600">Anomalies Detected</div>
              <div className="text-2xl font-bold">{analyzerStats?.anomalies_detected.toLocaleString()}</div>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <div className="text-sm text-gray-600">Uptime</div>
              <div className="text-2xl font-bold">
                {Math.floor((metricsStats?.uptime_seconds || 0) / 3600)}h
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
