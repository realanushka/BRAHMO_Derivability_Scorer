/**
 * UploadNodes component — Upload a .csv/.sql file of knowledge nodes, and
 * delete nodes by re-supplying the file they came from.
 *
 * Upload: the file is parsed and stored in Supabase (unscored). Each upload
 * is tagged with a batch id. Duplicate ids are auto-renamed so no node is
 * ever dropped.
 *
 * Delete by File: click the button, choose the SAME file again. Its nodes
 * are matched (by content) against the previously uploaded nodes and only
 * those matches are deleted. The original seed nodes are never affected.
 */
import { useRef, useState } from 'react';
import { uploadNodes, deleteNodesByFile } from '../api/client';

export default function UploadNodes({ onChanged }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [delBusy, setDelBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [delResult, setDelResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const deleteInputRef = useRef(null);

  const handleFile = (e) => {
    setFile(e.target.files[0] || null);
    setResult(null);
    setDelResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setDelResult(null);
    try {
      const res = await uploadNodes(file);
      setResult(res);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      if (onChanged) onChanged(); // refresh the node table
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  // Step 1: clicking the delete button opens a file picker
  const openDeletePicker = () => {
    setResult(null);
    setDelResult(null);
    setError(null);
    if (deleteInputRef.current) deleteInputRef.current.click();
  };

  // Step 2: once a file is chosen, confirm and delete its matching nodes
  const handleDeleteFile = async (e) => {
    const chosen = e.target.files[0];
    if (deleteInputRef.current) deleteInputRef.current.value = ''; // allow re-pick
    if (!chosen) return;

    const ok = window.confirm(
      `Delete the nodes that came from "${chosen.name}"?\n\n` +
        'Only nodes you uploaded are matched (by content). Your original seed nodes are NOT affected.'
    );
    if (!ok) return;

    setDelBusy(true);
    setError(null);
    setResult(null);
    setDelResult(null);
    try {
      const res = await deleteNodesByFile(chosen);
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
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <div>
          <label className="block text-sm font-semibold text-white/70 mb-2">
            Upload Nodes <span className="text-white/40 font-normal">(.csv or .sql)</span>
          </label>
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.sql"
              onChange={handleFile}
              id="upload-input"
              className="block text-sm text-white/60 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-white/10 file:text-white/80 file:font-medium hover:file:bg-white/20 file:cursor-pointer"
            />
            <button
              onClick={handleUpload}
              disabled={!file || busy}
              id="upload-button"
              className="btn-primary flex items-center gap-2 whitespace-nowrap"
            >
              {busy ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Uploading...
                </>
              ) : (
                'Upload'
              )}
            </button>

            {/* Delete by File: button opens a picker, then deletes matching nodes */}
            <input
              ref={deleteInputRef}
              type="file"
              accept=".csv,.sql"
              onChange={handleDeleteFile}
              className="hidden"
              id="delete-file-input"
            />
            <button
              onClick={openDeletePicker}
              disabled={delBusy}
              id="delete-by-file-button"
              title="Choose the file you uploaded — its matching nodes are deleted. Seed nodes are safe."
              className="px-5 py-2.5 bg-red-600/80 hover:bg-red-600 text-white font-semibold rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {delBusy ? 'Deleting...' : 'Delete by File'}
            </button>
          </div>
        </div>

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
              Uploaded nodes are stored unscored — click <span className="text-white/60">Rescore All</span> after uploading.
              To remove an upload, click <span className="text-white/60">Delete by File</span> and choose that same file.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
