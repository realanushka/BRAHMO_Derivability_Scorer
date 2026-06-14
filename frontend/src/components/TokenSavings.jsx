/**
 * TokenSavings — Detailed savings projections at various scales.
 */
export default function TokenSavings({ savings }) {
  if (!savings) return null;

  const rows = [
    {
      label: 'Per Session',
      value: savings.session_savings_dollars,
      format: 'currency',
      icon: '🎯',
      desc: 'Single engineer, one session',
    },
    {
      label: 'Daily (50 eng)',
      value: savings.daily_savings_50_engineers,
      format: 'currency',
      icon: '📅',
      desc: '50 engineers × 10 sessions',
    },
    {
      label: 'Annual (50 eng)',
      value: savings.annual_savings_50_engineers,
      format: 'currency',
      icon: '📊',
      desc: '250 working days',
    },
    {
      label: 'Daily (500 eng)',
      value: savings.daily_savings_500_engineers,
      format: 'currency',
      icon: '🏢',
      desc: '500 engineers × 10 sessions',
    },
    {
      label: 'Annual (500 eng)',
      value: savings.annual_savings_500_engineers,
      format: 'currency',
      icon: '🚀',
      desc: 'Full scale projection',
      highlight: true,
    },
  ];

  return (
    <div className="glass-card p-6" id="token-savings">
      <h2 className="text-lg font-bold text-white/90 mb-1">Token Savings — Cost Impact</h2>
      <p className="text-sm text-white/40 mb-5">
        Saving <span className="text-indigo-400 font-semibold">{savings.saved_tokens?.toLocaleString()}</span> of{' '}
        <span className="text-white/60">{savings.total_tokens?.toLocaleString()}</span> tokens
        = <span className="text-emerald-400 font-semibold">{savings.savings_percentage}%</span> reduction
      </p>

      {/* Progress bar */}
      <div className="w-full h-4 bg-white/10 rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-700"
          style={{ width: `${Math.min(savings.savings_percentage, 100)}%` }}
        />
      </div>

      {/* Savings Table */}
      <div className="space-y-2">
        {rows.map((row) => (
          <div
            key={row.label}
            className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
              row.highlight
                ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30'
                : 'bg-white/5 hover:bg-white/10'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">{row.icon}</span>
              <div>
                <div className="text-sm font-semibold text-white/80">{row.label}</div>
                <div className="text-xs text-white/30">{row.desc}</div>
              </div>
            </div>
            <div className={`text-lg font-bold tabular-nums ${row.highlight ? 'text-indigo-400' : 'text-white/70'}`}>
              ${row.value?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        ))}
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-2 gap-3 mt-5">
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center">
          <div className="text-xs text-red-400/70 mb-1">Derivable Tokens Saved</div>
          <div className="text-xl font-bold text-red-400">{savings.derivable_tokens?.toLocaleString() || 0}</div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-center">
          <div className="text-xs text-amber-400/70 mb-1">Partial (Delta) Savings</div>
          <div className="text-xl font-bold text-amber-400">{savings.partial_tokens_saved?.toLocaleString() || 0}</div>
        </div>
      </div>
    </div>
  );
}
