import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { PieChart } from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function CategoryChart({ categorias }) {
  if (!categorias || categorias.length === 0) {
    return (
      <div className="glass-card chart-section animate-fade-in">
        <div className="section-header">
          <h2 className="section-title">
            <PieChart size={20} color="#38bdf8" />
            <span>Gastos por Categoria</span>
          </h2>
        </div>
        <div className="empty-state">
          <PieChart size={48} opacity={0.3} />
          <p>Nenhum gasto categorizado no período atual.</p>
        </div>
      </div>
    );
  }

  const labels = categorias.map((item) => item.categoria);
  const dataValues = categorias.map((item) => item.valor);

  const backgroundColors = [
    '#38bdf8', '#818cf8', '#c084fc', '#f43f5e', '#facc15',
    '#10b981', '#fb7185', '#34d399', '#60a5fa', '#a855f7'
  ];

  const data = {
    labels,
    datasets: [
      {
        data: dataValues,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderColor: '#0b101d',
        borderWidth: 2,
        hoverOffset: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#e2e8f0',
          font: {
            family: "'Inter', sans-serif",
            size: 12,
            weight: '600'
          },
          padding: 16,
          usePointStyle: true,
          pointStyle: 'circle'
        },
      },
      tooltip: {
        backgroundColor: '#111d3b',
        titleFont: { family: "'Outfit', sans-serif", size: 14 },
        bodyFont: { family: "'Inter', sans-serif", size: 13 },
        padding: 12,
        borderColor: 'rgba(56, 189, 248, 0.3)',
        borderWidth: 1,
        callbacks: {
          label: function (context) {
            let label = context.label || '';
            if (label) label += ': ';
            if (context.parsed !== null) {
              label += new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
              }).format(context.parsed);
            }
            return label;
          }
        }
      },
    },
    cutout: '65%',
  };

  return (
    <div className="glass-card chart-section animate-fade-in">
      <div className="section-header">
        <h2 className="section-title">
          <PieChart size={20} color="#38bdf8" />
          <span>Gastos por Categoria</span>
        </h2>
      </div>
      <div className="chart-wrapper">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
}
