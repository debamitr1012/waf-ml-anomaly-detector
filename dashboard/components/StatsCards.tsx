'use client';

import { Statistics } from '@/types';
import { Activity, AlertTriangle, Clock, TrendingUp } from 'lucide-react';

interface StatsCardsProps {
  stats: Statistics | null;
}

export default function StatsCards({ stats }: StatsCardsProps) {
  if (!stats) return null;

  const cards = [
    {
      title: 'Total Requests',
      value: stats.analyzer.total_analyzed.toLocaleString(),
      icon: Activity,
      color: 'blue',
      bgColor: 'bg-blue-500',
    },
    {
      title: 'Anomalies Detected',
      value: stats.analyzer.anomalies_detected.toLocaleString(),
      icon: AlertTriangle,
      color: 'red',
      bgColor: 'bg-red-500',
    },
    {
      title: 'Avg Latency',
      value: `${stats.analyzer.avg_latency_ms.toFixed(1)}ms`,
      icon: Clock,
      color: 'green',
      bgColor: 'bg-green-500',
    },
    {
      title: 'Detection Rate',
      value: `${stats.metrics.detection_rate_percent.toFixed(2)}%`,
      icon: TrendingUp,
      color: 'purple',
      bgColor: 'bg-purple-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      {cards.map((card) => {
        const Icon = card.icon;
        
        return (
          <div key={card.title} className="bg-white rounded-lg shadow-md p-6 card-hover animate-fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <div className={`${card.bgColor} p-3 rounded-lg`}>
                <Icon size={24} className="text-white" />
              </div>
            </div>
            <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
            <p className="text-3xl font-bold text-gray-900">{card.value}</p>
          </div>
        );
      })}
    </div>
  );
}
