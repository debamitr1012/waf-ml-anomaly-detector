'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import StatsCards from '@/components/StatsCards';
import AnomalyChart from '@/components/AnomalyChart';
import AttackDistributionChart from '@/components/AttackDistributionChart';
import AlertsTable from '@/components/AlertsTable';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiClient } from '@/lib/api-client';
import { Statistics, AnalysisResult } from '@/types';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Statistics | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<AnalysisResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication (simple check - implement proper auth in production)
  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('authenticated');
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [router]);

  // WebSocket connection for real-time updates
  const { isConnected } = useWebSocket({
    onAnalysis: (data: AnalysisResult) => {
      if (data.is_anomaly) {
        setRecentAlerts((prev) => [data, ...prev].slice(0, 20));
      }
    },
    onStatsUpdate: (data: Statistics) => {
      setStats(data);
    },
  });

  // Fetch initial statistics and alerts
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, alertsData] = await Promise.all([
          apiClient.getStatistics(),
          apiClient.getRecentAlerts(50)
        ]);
        setStats(statsData);
        setRecentAlerts(alertsData.alerts);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">System Dashboard</h1>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        {/* Statistics Cards */}
        <StatsCards stats={stats} />

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <AnomalyChart alerts={recentAlerts} />
          </div>
          <div>
            <AttackDistributionChart stats={stats} />
          </div>
        </div>

        {/* Recent Alerts */}
        <AlertsTable alerts={recentAlerts} />
      </main>
    </div>
  );
}
