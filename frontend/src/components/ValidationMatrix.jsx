/**
 * ValidationMatrix — Confusion matrix, precision, recall, F1, false positive alerts.
 */
export default function ValidationMatrix({ matrix }) {
  if (!matrix) return null;

  const cm = matrix.confusion_matrix || {};
  const tp = cm.true_positives ?? 0;
  const fp = cm.false_positives ?? 0;
  const tn = cm.true_negatives ?? 0;
  const fn = cm.false_negatives ?? 0;

  const MetricGauge = ({ label, value, color, target }) => {
    const pct = Math.round(value * 100);
    return (
      <div className="text-center">
        <div className="relative w-20 h-20 mx-auto mb-2">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
            <circle
              cx="18" cy="18" r="15" fill="none"
              stroke={color} strokeWidth="3"
              strokeDasharray={`${pct * 0.942} 100`}
              strokeLinecap="round"
              className="transition-all duration-1000"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-white">
            {pct}%
          </span>
        </div>
        <div className="text-sm font-semibold text-white/80">{label}</div>
        {target && <div className="text-xs text-white/30">Target: ≥{target}%</div>}
      </div>
    );
  };

  return (
    <div className="glass-card p-6" id="validation-matrix">
      <h2 className="text-lg font-bold text-white/90 mb-5">Validation Matrix — Scorer Accuracy</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Grid */}
        <div>
          <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-3">Confusion Matrix</h3>
          <div className="grid grid-cols-3 gap-1 text-center text-sm">
            {/* Header row */}
            <div className="p-2" />
            <div className="p-2 text-xs text-white/50 font-semibold">Actually Derivable</div>
            <div className="p-2 text-xs text-white/50 font-semibold">Actually Non-Derivable</div>

            {/* Scored Derivable row */}
            <div className="p-2 text-xs text-white/50 font-semibold text-right">Scored DERIVABLE</div>
            <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-3">
              <div className="text-2xl font-bold text-emerald-400">{tp}</div>
              <div className="text-xs text-emerald-400/70">True Positive</div>
            </div>
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3">
              <div className="text-2xl font-bold text-red-400">{fp}</div>
              <div className="text-xs text-red-400/70">FALSE POSITIVE</div>
            </div>

            {/* Scored Non-Derivable row */}
            <div className="p-2 text-xs text-white/50 font-semibold text-right">Scored NON_DERIV</div>
            <div className="bg-amber-500/20 border border-amber-500/30 rounded-lg p-3">
              <div className="text-2xl font-bold text-amber-400">{fn}</div>
              <div className="text-xs text-amber-400/70">False Negative</div>
            </div>
            <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-3">
              <div className="text-2xl font-bold text-emerald-400">{tn}</div>
              <div className="text-xs text-emerald-400/70">True Negative</div>
            </div>
          </div>
        </div>

        {/* Metric Gauges */}
        <div>
          <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-3">Performance Metrics</h3>
          <div className="flex justify-around items-start">
            <MetricGauge label="Precision" value={matrix.precision} color="#10B981" target={85} />
            <MetricGauge label="Recall" value={matrix.recall} color="#6366F1" target={70} />
            <MetricGauge label="F1 Score" value={matrix.f1_score} color="#F59E0B" />
          </div>
        </div>
      </div>

      {/* False Positive Alerts */}
      {matrix.false_positive_nodes?.length > 0 && (
        <div className="mt-5 bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <h4 className="text-sm font-bold text-red-400 mb-2">
            🔴 FALSE POSITIVES ({matrix.false_positive_nodes.length}) — Critical: Investigate!
          </h4>
          <p className="text-xs text-red-300/70">
            These nodes were scored DERIVABLE but are actually NOT derivable.
            Org-specific knowledge would be excluded!
          </p>
          <div className="flex gap-2 mt-2">
            {matrix.false_positive_nodes.map((id) => (
              <span key={id} className="badge-derivable">{id}</span>
            ))}
          </div>
        </div>
      )}

      {matrix.false_negative_nodes?.length > 0 && (
        <div className="mt-3 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
          <h4 className="text-sm font-bold text-amber-400 mb-2">
            ⚠️ False Negatives ({matrix.false_negative_nodes.length}) — Acceptable: Wasted tokens
          </h4>
          <div className="flex gap-2 mt-2">
            {matrix.false_negative_nodes.map((id) => (
              <span key={id} className="badge-partial">{id}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
