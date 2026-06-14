/**
 * StatsCards — 6 statistics cards showing node counts and token savings.
 */
export default function StatsCards({ metrics, savings }) {
  const cards = [
    {
      label: 'Total Nodes',
      value: metrics?.total_nodes ?? 0,
      icon: '📊',
      color: 'from-slate-500 to-slate-600',
      textColor: 'text-white',
    },
    {
      label: 'Derivable',
      value: metrics?.derivable_count ?? 0,
      icon: '🔴',
      color: 'from-red-500/20 to-red-600/20',
      textColor: 'text-red-400',
      subtitle: 'EXCLUDED',
    },
    {
      label: 'Partial',
      value: metrics?.partial_count ?? 0,
      icon: '🟡',
      color: 'from-amber-500/20 to-amber-600/20',
      textColor: 'text-amber-400',
      subtitle: 'DELTA ONLY',
    },
    {
      label: 'Non-Derivable',
      value: metrics?.non_derivable_count ?? 0,
      icon: '🟢',
      color: 'from-emerald-500/20 to-emerald-600/20',
      textColor: 'text-emerald-400',
      subtitle: 'FULL CONTENT',
    },
    {
      label: 'Tokens Saved',
      value: savings?.saved_tokens ?? 0,
      icon: '💰',
      color: 'from-indigo-500/20 to-purple-500/20',
      textColor: 'text-indigo-400',
      subtitle: `${savings?.savings_percentage ?? 0}% savings`,
      format: 'number',
    },
    {
      label: 'Annual Savings',
      value: savings?.annual_savings_500_engineers ?? 0,
      icon: '📈',
      color: 'from-pink-500/20 to-rose-500/20',
      textColor: 'text-pink-400',
      subtitle: '500 engineers',
      format: 'currency',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="glass-card-hover p-5 group" id={`stat-${card.label.toLowerCase().replace(/\s/g, '-')}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-lg">{card.icon}</span>
            {card.subtitle && (
              <span className={`text-[10px] font-bold uppercase tracking-wider ${card.textColor} opacity-70`}>
                {card.subtitle}
              </span>
            )}
          </div>
          <div className={`stat-number ${card.textColor}`}>
            {card.format === 'currency'
              ? `$${card.value.toLocaleString('en-US', { minimumFractionDigits: 0 })}`
              : card.format === 'number'
              ? card.value.toLocaleString()
              : card.value}
          </div>
          <div className="text-sm text-white/40 mt-1 font-medium">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
