/**
 * TestPlayground — a live "surprise test" sandbox.
 *
 * Paste or type any knowledge content, pick a type/algorithm/threshold, and
 * score it INSTANTLY. Nothing is saved to the database (the backend only
 * persists when a node_id is supplied; here we send raw content), so you can
 * experiment freely and see exactly how the scorer reacts and why.
 */
import { useState } from 'react';
import { scoreContent } from '../api/client';

const EXAMPLES = [
  {
    label: '🔴 Likely DERIVABLE',
    title: 'What is Hypertension',
    type: 'FACT',
    content:
      'Hypertension, also called high blood pressure, is a chronic condition where the blood pressure in the arteries is persistently elevated. Normal blood pressure is below 120/80 mmHg.',
  },
  {
    label: '🟢 Likely NON_DERIVABLE',
    title: 'Cardiac Unit Lead Decision',
    type: 'DECISION',
    content:
      'Supra Hospital decided in March 2024 that Dr. Mehta will lead the new cardiac care unit, after reviewing the 12 readmission cases recorded in the previous quarter.',
  },
  {
    label: '🟡 Likely PARTIAL',
    title: 'DVT Prophylaxis Protocol',
    type: 'FACT',
    content:
      'DVT prophylaxis for surgical patients includes early mobilization and anticoagulants such as enoxaparin. At Supra Hospital, the standard enoxaparin dose is fixed by the formulary committee.',
  },
  {
    label: '🛡️ CONSTRAINT (floor test)',
    title: 'Hand Hygiene Compliance',
    type: 'CONSTRAINT',
    content:
      'WHO 5-moment hand hygiene compliance is mandatory. Alcohol-based handrub at every bed. This sounds general, but the CONSTRAINT type caps the score at 0.50 so it is never excluded.',
  },
];

const NODE_TYPES = ['FACT', 'DECISION', 'CONSTRAINT', 'ANTI_PATTERN'];
const ALGORITHMS = ['hybrid', 'heuristic', 'tfidf'];

const CLASS_STYLES = {
  DERIVABLE: { text: 'text-red-400', bar: 'bg-red-500', label: '🔴 DERIVABLE — exclude entirely' },
  PARTIALLY_DERIVABLE: { text: 'text-amber-400', bar: 'bg-amber-500', label: '🟡 PARTIALLY DERIVABLE — send delta only' },
  NON_DERIVABLE: { text: 'text-emerald-400', bar: 'bg-emerald-500', label: '🟢 NON_DERIVABLE — keep full content' },
  UNKNOWN: { text: 'text-slate-400', bar: 'bg-slate-500', label: 'UNKNOWN' },
};

export default function TestPlayground() {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [nodeType, setNodeType] = useState('FACT');
  const [algorithm, setAlgorithm] = useState('hybrid');
  const [threshold, setThreshold] = useState(0.7);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const loadExample = (ex) => {
    setContent(ex.content);
    setTitle(ex.title);
    setNodeType(ex.type);
    setResult(null);
    setError(null);
  };

  const handleScore = async () => {
    if (!content.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await scoreContent({ content, title, nodeType, algorithm, threshold });
      setResult(res.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const cls = result ? CLASS_STYLES[result.classification] || CLASS_STYLES.UNKNOWN : null;
  const score = result?.final_score ?? 0;

  return (
    <div className="space-y-5">
      {/* Intro */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-bold text-white/90 mb-1">🧪 Test Playground — Live Scorer</h2>
        <p className="text-sm text-white/50">
          Type or paste any content and score it instantly. <span className="text-white/70">Nothing is saved</span> —
          this is the live "surprise test." Watch the score, the classification, and the exact signals that fired.
        </p>
      </div>

      {/* Input + controls */}
      <div className="glass-card p-6 space-y-4">
        {/* Example chips */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-white/40 self-center mr-1">Quick examples:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              onClick={() => loadExample(ex)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-white/70 hover:bg-white/10 transition-all"
            >
              {ex.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-white/70 mb-2">Title (optional)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. What is Sepsis"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white/80 placeholder-white/25 focus:outline-none focus:border-indigo-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-white/70 mb-2">Node Type</label>
            <div className="flex gap-2 flex-wrap">
              {NODE_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setNodeType(t)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    nodeType === t ? 'bg-indigo-600 text-white' : 'bg-white/5 text-white/60 hover:bg-white/10'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-white/70 mb-2">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste or type the knowledge text to score…"
            rows={5}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/80 placeholder-white/25 leading-relaxed focus:outline-none focus:border-indigo-500/50 resize-y"
          />
        </div>

        <div className="flex flex-wrap items-end gap-6">
          <div>
            <label className="block text-sm font-semibold text-white/70 mb-2">Algorithm</label>
            <div className="flex gap-2">
              {ALGORITHMS.map((a) => (
                <button
                  key={a}
                  onClick={() => setAlgorithm(a)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    algorithm === a ? 'bg-indigo-600 text-white' : 'bg-white/5 text-white/60 hover:bg-white/10'
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-semibold text-white/70 mb-2">
              Threshold: <span className="text-indigo-400 font-bold">{threshold.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="0.40"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="input-range w-full"
            />
          </div>
          <button
            onClick={handleScore}
            disabled={!content.trim() || busy}
            className="btn-primary flex items-center gap-2 whitespace-nowrap"
          >
            {busy ? 'Scoring…' : '⚡ Score it'}
          </button>
        </div>

        {error && <div className="text-red-400 text-sm">⚠️ {error}</div>}
      </div>

      {/* Result */}
      {result && cls && (
        <div className="glass-card p-6 space-y-5">
          {/* Score headline */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-white/40 uppercase tracking-wider mb-1">Final Score</div>
              <div className={`text-5xl font-extrabold ${cls.text}`}>{score.toFixed(4)}</div>
            </div>
            <div className={`text-right ${cls.text}`}>
              <div className="text-lg font-bold">{cls.label}</div>
              {result.type_floor_applied && (
                <div className="text-xs text-amber-400 mt-1">⚠️ Type safety floor was applied</div>
              )}
            </div>
          </div>

          {/* Score bar */}
          <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${cls.bar} transition-all duration-700`} style={{ width: `${score * 100}%` }} />
          </div>

          {/* Sub-scores */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white/5 rounded-xl p-3 text-center">
              <div className="text-xs text-white/40 mb-1">Heuristic</div>
              <div className="text-xl font-bold text-white/80">{result.heuristic_score?.toFixed(3)}</div>
              <div className="text-[10px] text-white/30">× 0.7</div>
            </div>
            <div className="bg-white/5 rounded-xl p-3 text-center">
              <div className="text-xs text-white/40 mb-1">TF-IDF</div>
              <div className="text-xl font-bold text-white/80">{result.tfidf_score?.toFixed(3)}</div>
              <div className="text-[10px] text-white/30">× 0.3</div>
            </div>
            <div className="bg-white/5 rounded-xl p-3 text-center">
              <div className="text-xs text-white/40 mb-1">Raw (pre-floor)</div>
              <div className="text-xl font-bold text-white/80">{result.raw_score?.toFixed(3)}</div>
              <div className="text-[10px] text-white/30">before cap</div>
            </div>
          </div>

          {/* Scoring reason */}
          <div>
            <div className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-2">Why this score?</div>
            <p className="text-sm text-white/70 bg-white/5 rounded-xl p-4 border border-white/5">
              {result.scoring_reason}
            </p>
          </div>

          {/* Signals */}
          {result.signals?.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-2">
                Signals that fired ({result.signals.length})
              </div>
              <div className="space-y-2">
                {result.signals.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 bg-white/5 rounded-lg px-4 py-2">
                    <span
                      className={`text-sm font-bold font-mono w-14 text-right ${
                        s.weight >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {s.weight >= 0 ? '+' : ''}{s.weight.toFixed(2)}
                    </span>
                    <div className="flex-1">
                      <div className="text-sm text-white/80 font-medium">{s.name}</div>
                      <div className="text-xs text-white/40">{s.description}</div>
                      {s.matched_text && (
                        <div className="text-xs text-indigo-300/70 mt-0.5">matched: "{s.matched_text}"</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Delta (for partial) */}
          {result.non_derivable_portion && (
            <div>
              <div className="text-sm font-semibold text-amber-400/80 uppercase tracking-wider mb-2">
                Org-specific delta (kept for the AI)
              </div>
              <p className="text-sm text-amber-300/90 bg-amber-500/10 rounded-xl p-4 border border-amber-500/20">
                {result.non_derivable_portion}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
