'use client';

import { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { Statistics } from '@/types';

Chart.register(...registerables);

interface AttackDistributionChartProps {
  stats: Statistics | null;
}

export default function AttackDistributionChart({ stats }: AttackDistributionChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !stats?.metrics.attack_types) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const attackTypes = stats.metrics.attack_types;
    const labels = Object.keys(attackTypes);
    const data = Object.values(attackTypes);

    const colors = [
      'rgba(220, 53, 69, 0.8)',
      'rgba(255, 193, 7, 0.8)',
      'rgba(102, 126, 234, 0.8)',
      'rgba(40, 167, 69, 0.8)',
      'rgba(255, 99, 132, 0.8)',
    ];

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
          },
          title: {
            display: true,
            text: 'Attack Types Distribution',
          },
        },
      },
    };

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    chartRef.current = new Chart(ctx, config);

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [stats]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="h-64">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}
