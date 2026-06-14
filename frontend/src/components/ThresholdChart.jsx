/**
 * ThresholdChart — Chart.js graphs showing threshold vs savings, precision, recall.
 */
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function ThresholdChart({ thresholdData, currentThreshold }) {
  if (!thresholdData?.data_points?.length) return null;

  const points = thresholdData.data_points;
  const labels = points.map((p) => p.threshold.toFixed(2));

  const data = {
    labels,
    datasets: [
      {
        label: 'Token Savings %',
        data: points.map((p) => p.savings_percentage),
        borderColor: '#6366F1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 7,
        yAxisID: 'y',
      },
      {
        label: 'Precision',
        data: points.map((p) => p.precision * 100),
        borderColor: '#10B981',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 7,
        borderDash: [5, 5],
        yAxisID: 'y',
      },
      {
        label: 'Recall',
        data: points.map((p) => p.recall * 100),
        borderColor: '#F59E0B',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 7,
        borderDash: [10, 5],
        yAxisID: 'y',
      },
      {
        label: 'False Positives',
        data: points.map((p) => p.false_positive_count),
        borderColor: '#EF4444',
        backgroundColor: 'transparent',
        tension: 0.2,
        pointRadius: 5,
        pointHoverRadius: 8,
        pointStyle: 'triangle',
        yAxisID: 'y1',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'rgba(255,255,255,0.7)',
          font: { family: 'Inter', size: 12 },
          padding: 16,
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#fff',
        bodyColor: 'rgba(255,255,255,0.8)',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 12,
        titleFont: { family: 'Inter', size: 13, weight: '600' },
        bodyFont: { family: 'Inter', size: 12 },
        cornerRadius: 12,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Threshold',
          color: 'rgba(255,255,255,0.5)',
          font: { family: 'Inter', size: 12, weight: '600' },
        },
        ticks: { color: 'rgba(255,255,255,0.4)', font: { family: 'Inter' } },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        type: 'linear',
        position: 'left',
        title: {
          display: true,
          text: 'Percentage (%)',
          color: 'rgba(255,255,255,0.5)',
          font: { family: 'Inter', size: 12, weight: '600' },
        },
        ticks: { color: 'rgba(255,255,255,0.4)', font: { family: 'Inter' } },
        grid: { color: 'rgba(255,255,255,0.05)' },
        min: 0,
        max: 100,
      },
      y1: {
        type: 'linear',
        position: 'right',
        title: {
          display: true,
          text: 'False Positives',
          color: 'rgba(239,68,68,0.7)',
          font: { family: 'Inter', size: 12, weight: '600' },
        },
        ticks: { color: 'rgba(239,68,68,0.5)', font: { family: 'Inter' }, stepSize: 1 },
        grid: { display: false },
        min: 0,
      },
    },
  };

  return (
    <div className="glass-card p-6" id="threshold-chart">
      <h2 className="text-lg font-bold text-white/90 mb-1">Threshold Impact Analysis</h2>
      <p className="text-sm text-white/40 mb-5">
        How changing the threshold affects savings, accuracy, and safety.
        Current threshold: <span className="text-indigo-400 font-semibold">{currentThreshold?.toFixed(2)}</span>
        {thresholdData.optimal_threshold && (
          <> | Optimal: <span className="text-emerald-400 font-semibold">{thresholdData.optimal_threshold.toFixed(2)}</span></>
        )}
      </p>
      <div className="h-[350px]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
