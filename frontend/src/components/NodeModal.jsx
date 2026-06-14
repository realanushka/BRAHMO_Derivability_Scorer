/**
 * NodeModal — Detailed view of a single node's scoring breakdown.
 * Shows full content, delta content, score explanation, signals, and type floor.
 */
export default function NodeModal({ node, onClose }) {
  if (!node) return null;

  const score = node.derivability_score ?? 0.5;
  const cls = node.derivability_class || 'UNKNOWN';

  const colorMap = {
    DERIVABLE: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', bar: 'bg-red-500' },
    PARTIALLY_DERIVABLE: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', bar: 'bg-amber-500' },
    NON_DERIVABLE: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', bar: 'bg-emerald-500' },
    UNKNOWN: { bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-400', bar: 'bg-slate-500' },
  };
  const colors = colorMap[cls] || colorMap.UNKNOWN;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative glass-card max-w-3xl w-full max-h-[85vh] overflow-y-auto p-8 modal-content"
        onClick={(e) => e.stopPropagation()}
        id="node-modal"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-all"
          id="modal-close"
        >
          ✕
        </button>

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-sm font-mono text-indigo-400 font-bold">{node.id}</span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-md bg-white/10 text-white/60`}>
              {node.type}
            </span>
            {node.type_floor_applied && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30">
                ⚠️ FLOOR APPLIED
              </span>
            )}
          </div>
          <h2 className="text-xl font-bold text-white">{node.title}</h2>
        </div>

        {/* Score Display */}
        <div className={`${colors.bg} ${colors.border} border rounded-xl p-5 mb-6`}>
          <div className="flex items-center justify-between mb-3">
            <span className={`text-3xl font-extrabold ${colors.text}`}>
              {score.toFixed(4)}
            </span>
            <span className={`text-lg font-bold ${colors.text}`}>{cls.replace('_', ' ')}</span>
          </div>
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${colors.bar} transition-all duration-700`} style={{ width: `${score * 100}%` }} />
          </div>
          {node.expected_score_range && (
            <div className="mt-2 text-xs text-white/40">
              Expected range: {node.expected_score_range} | Expected class: {node.expected_derivability || '—'}
            </div>
          )}
        </div>

        {/* Content Section */}
        <div className="space-y-4 mb-6">
          <div>
            <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-2">Full Content</h3>
            <p className="text-sm text-white/80 bg-white/5 rounded-xl p-4 leading-relaxed border border-white/5">
              {node.content}
            </p>
            <span className="text-xs text-white/30 mt-1 block">{node.tokens_full || 0} tokens</span>
          </div>

          {node.non_derivable_portion && (
            <div>
              <h3 className="text-sm font-semibold text-amber-400/80 uppercase tracking-wider mb-2">
                Delta Content (Non-Derivable Portion)
              </h3>
              <p className="text-sm text-amber-300/90 bg-amber-500/10 rounded-xl p-4 leading-relaxed border border-amber-500/20">
                {node.non_derivable_portion}
              </p>
              <span className="text-xs text-white/30 mt-1 block">{node.tokens_delta || 0} tokens (saves {(node.tokens_full || 0) - (node.tokens_delta || 0)} tokens)</span>
            </div>
          )}
        </div>

        {/* Scoring Reason */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-2">Score Explanation</h3>
          <p className="text-sm text-white/70 bg-white/5 rounded-xl p-4 border border-white/5">
            {node.scoring_reason || 'No scoring reason available. Run scoring first.'}
          </p>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-white/5 rounded-xl p-3 border border-white/5">
            <span className="text-white/40 text-xs">Department</span>
            <div className="text-white/80 font-medium mt-1">{node.department || '—'}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 border border-white/5">
            <span className="text-white/40 text-xs">Importance</span>
            <div className="text-white/80 font-medium mt-1">{node.importance ?? '—'}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 border border-white/5">
            <span className="text-white/40 text-xs">Organization</span>
            <div className="text-white/80 font-medium mt-1">{node.org_id || '—'}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 border border-white/5">
            <span className="text-white/40 text-xs">Type Floor</span>
            <div className="text-white/80 font-medium mt-1">
              {node.type_floor_applied ? '✅ Applied' : '—'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
