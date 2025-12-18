'use client';

import { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { AnalysisResult } from '@/types';
import { format } from 'date-fns';

Chart.register(...registerables);

interface AnomalyChartProps {
  alerts: AnalysisResult[];
}

export default function AnomalyChart({ alerts }: AnomalyChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // Prepare data from last 20 alerts
    const labels = alerts.slice(0, 20).reverse().map((_, i) => format(new Date(), 'HH:mm:ss'));
    const data = alerts.slice(0, 20).reverse().map(a => a.anomaly_score * 100);

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Anomaly Score',
          data,
          borderColor: 'rgb(220, 53, 69)',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
          },
          title: {
            display: true,
            text: 'Real-time Anomaly Detection Timeline',
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Anomaly Score (%)',
            },
          },
          x: {
            title: {
              display: true,
              text: 'Time',
            },
          },
        },
      },
    };

    // Destroy existing chart
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    // Create new chart
    chartRef.current = new Chart(ctx, config);

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [alerts]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="h-64">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}
