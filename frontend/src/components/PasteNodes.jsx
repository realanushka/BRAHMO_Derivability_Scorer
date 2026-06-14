/**
 * PasteNodes component — Paste raw node text (CSV or SQL) directly into a box
 * and save it to Supabase, or delete those same nodes by pasting again.
 *
 * Save: the pasted text is parsed and stored in Supabase (unscored). Each save
 * is tagged with a batch id. Duplicate ids are auto-renamed so no node is
 * ever dropped. Click "Rescore All" afterwards to score the new nodes.
 *
 * Delete by Text: paste the SAME text again and click Delete. Its nodes are
 * matched (by content) against previously uploaded/pasted nodes and only those
 * matches are deleted. The original seed nodes are never affected.
 */
import { useState } from 'react';
import { pasteNodes, deleteNodesByText } from '../api/client';

const PLACEHOLDER = `Paste nodes here — CSV or SQL. Examples:

CSV (first line is the header):
id,org_id,type,title,content,expected_derivability,department
PX-1,supra,FACT,What is BMI,"Body Mass Index is weight in kg divided by height in metres squared.",DERIVABLE,medicine

SQL:
INSERT INTO knowledge_nodes (id, org_id, type, title, content) VALUES
('PX-2','supra','FACT','What is Sepsis','Sepsis is a life-threatening response to infection.');`;

export default function PasteNodes({ onChanged }) {
  const [text, setText] = useState('');
  const [format, setFormat] = useState('auto'); // 'auto' | 'csv' | 'sql'
  const [busy, setBusy] = useState(false);
  const [delBusy, setDelBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [delResult, setDelResult] = useState(null);
  const [error, setError] = useState(null);

  const fmtParam = format === 'auto' ? null : format;

  const reset = () => {
    setResult(null);
    setDelResult(null);
    setError(null);
  };

  const handleSave = async () => {
    if (!text.trim()) return;
    setBusy(true);
    reset();
    try {
      const res = await pasteNodes(text, fmtParam);
      setResult(res);
      if (onChanged) onChanged(); // refresh the node table
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!text.trim()) return;
    const ok = window.confirm(
      'Delete the nodes in this pasted text?\n\n' +
        'Only nodes you uploaded/pasted are matched (by content). ' +
        'Your original seed nodes are NOT affected.'
    );
    if (!ok) return;

    setDelBusy(true);
    reset();
    try {
      const res = await deleteNodesByText(text, fmtParam);
      setDelResult(res);
      if (onChanged) onChanged(); // refresh the node table
    } catch (err) {
      setError(err.message);
    } finally {
      setDelBusy(false);
    }
  };

  return (
    <div className="glass-card px-8 py-5">
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-semibold text-white/70">
          Paste Nodes <span className="text-white/40 font-normal">(CSV or SQL text)</span>
        </label>

        {/* Format selector */}
        <div className="flex gap-1">
          {['auto', 'csv', 'sql'].map((f) => (
            <button
              key={f}
              onClick={() => setFormat(f)}
              id={`paste-format-${f}`}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                format === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white/5 text-white/50 hover:bg-white/10'
              }`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={PLACEHOLDER}
        rows={7}
        id="paste-textarea"
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/80 placeholder-white/25 font-mono leading-relaxed focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/40 resize-y"
      />

      <div className="flex flex-wrap items-center gap-3 mt-3">
        <button
          onClick={handleSave}
          disabled={!text.trim() || busy}
          id="paste-save-button"
          className="btn-primary flex items-center gap-2 whitespace-nowrap"
        >
          {busy ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving...
            </>
          ) : (
            'Save to Database'
          )}
        </button>

        <button
          onClick={handleDelete}
          disabled={!text.trim() || delBusy}
          id="paste-delete-button"
          title="Paste the same nodes and click — their matching nodes are deleted. Seed nodes are safe."
          className="px-5 py-2.5 bg-red-600/80 hover:bg-red-600 text-white font-semibold rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {delBusy ? 'Deleting...' : 'Delete by Text'}
        </button>

        {text.trim() && (
          <button
            onClick={() => { setText(''); reset(); }}
            className="px-4 py-2.5 text-sm text-white/50 hover:text-white/80 transition-colors"
          >
            Clear
          </button>
        )}

        {/* Result / status area */}
        <div className="flex-1 min-w-[260px] text-sm">
          {error && <div className="text-red-400">⚠️ {error}</div>}

          {result && (
            <div className="space-y-1">
              <div className="text-emerald-400 font-semibold">
                ✓ Inserted {result.inserted_count} of {result.parsed_count} parsed node(s)
                <span className="text-white/40 font-normal"> · {result.format.toUpperCase()}</span>
              </div>
              {result.renamed.length > 0 && (
                <div className="text-amber-400">
                  {result.renamed.length} id(s) renamed to avoid duplicates:{' '}
                  {result.renamed.slice(0, 5).map((r) => `${r.original_id}→${r.new_id}`).join(', ')}
                  {result.renamed.length > 5 ? ', …' : ''}
                </div>
              )}
              {result.warnings.length > 0 && (
                <div className="text-white/40">{result.warnings.length} warning(s): {result.warnings[0]}</div>
              )}
              <div className="text-white/50">Now click <span className="text-indigo-400 font-medium">Rescore All</span> to score the new nodes.</div>
            </div>
          )}

          {delResult && (
            <div className={delResult.deleted_count > 0 ? 'text-emerald-400 font-semibold' : 'text-white/50'}>
              {delResult.deleted_count > 0 ? '✓ ' : 'ℹ️ '}{delResult.message}
            </div>
          )}

          {!error && !result && !delResult && (
            <div className="text-white/40">
              Paste nodes and click <span className="text-white/60">Save to Database</span>. To remove them,
              paste the same nodes and click <span className="text-white/60">Delete by Text</span>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
