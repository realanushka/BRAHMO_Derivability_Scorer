/**
 * Controls component — Threshold slider, Algorithm selector, Rescore button.
 */
export default function Controls({ threshold, algorithm, onThresholdChange, onAlgorithmChange, onRescore, loading }) {
  const algorithms = [
    { value: 'hybrid', label: 'Hybrid', desc: '0.7×Heuristic + 0.3×TF-IDF' },
    { value: 'heuristic', label: 'Heuristic', desc: 'spaCy NER + Regex rules' },
    { value: 'tfidf', label: 'TF-IDF', desc: 'Cosine similarity to corpus' },
  ];

  return (
    <div className="glass-card px-8 py-5">
      <div className="flex flex-wrap items-end gap-8">
        {/* Threshold Slider */}
        <div className="flex-1 min-w-[250px]">
          <label className="block text-sm font-semibold text-white/70 mb-2">
            Derivability Threshold
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="0.40"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
              className="input-range flex-1"
              id="threshold-slider"
            />
            <span className="text-2xl font-bold text-indigo-400 tabular-nums w-16 text-right">
              {threshold.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between text-xs text-white/30 mt-1 px-1">
            <span>0.40 (Aggressive)</span>
            <span>0.70 (Default)</span>
            <span>0.95 (Conservative)</span>
          </div>
        </div>

        {/* Algorithm Selector */}
        <div className="min-w-[200px]">
          <label className="block text-sm font-semibold text-white/70 mb-2">
            Algorithm
          </label>
          <div className="flex gap-2">
            {algorithms.map((alg) => (
              <button
                key={alg.value}
                onClick={() => onAlgorithmChange(alg.value)}
                title={alg.desc}
                id={`algo-${alg.value}`}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  algorithm === alg.value
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                    : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
                }`}
              >
                {alg.label}
              </button>
            ))}
          </div>
        </div>

        {/* Rescore Button */}
        <button
          onClick={onRescore}
          disabled={loading}
          id="rescore-button"
          className="btn-primary flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Scoring...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
              </svg>
              Rescore All
            </>
          )}
        </button>
      </div>
    </div>
  );
}
