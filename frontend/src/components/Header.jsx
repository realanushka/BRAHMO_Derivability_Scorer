/**
 * Header component — BRAHMO Derivability Scorer branding.
 */
export default function Header() {
  return (
    <header className="glass-card px-8 py-5 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Logo / Icon */}
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
        </div>
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              BRAHMO
            </span>{' '}
            <span className="text-white/90">Derivability Scorer</span>
          </h1>
          <p className="text-sm text-white/40 mt-0.5">Token Savings Engine — Zero LLM at Query Time</p>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2 text-sm text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow" />
          System Active
        </span>
        <span className="text-xs text-white/30 border-l border-white/10 pl-3">v1.0.0</span>
      </div>
    </header>
  );
}
