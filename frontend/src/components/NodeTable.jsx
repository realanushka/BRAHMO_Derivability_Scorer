/**
 * NodeTable — Sortable table displaying all 30 knowledge nodes with scores.
 */
import { useState, useMemo } from 'react';

function ClassBadge({ classification }) {
  const map = {
    DERIVABLE: 'badge-derivable',
    PARTIALLY_DERIVABLE: 'badge-partial',
    NON_DERIVABLE: 'badge-non-derivable',
    UNKNOWN: 'badge-unknown',
  };
  const labels = {
    DERIVABLE: '🔴 DERIVABLE',
    PARTIALLY_DERIVABLE: '🟡 PARTIAL',
    NON_DERIVABLE: '🟢 NON_DERIV',
    UNKNOWN: '⚪ UNKNOWN',
  };
  return (
    <span className={map[classification] || map.UNKNOWN}>
      {labels[classification] || classification}
    </span>
  );
}

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7 ? 'bg-red-500' : score >= 0.4 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
        <div className={`score-bar ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono font-semibold text-white/80 w-12 text-right">
        {score.toFixed(2)}
      </span>
    </div>
  );
}

export default function NodeTable({ nodes, onNodeClick, threshold }) {
  const [sortField, setSortField] = useState('id');
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sortedNodes = useMemo(() => {
    if (!nodes) return [];
    return [...nodes].sort((a, b) => {
      let av = a[sortField] ?? '';
      let bv = b[sortField] ?? '';
      if (typeof av === 'number' && typeof bv === 'number') {
        return sortDir === 'asc' ? av - bv : bv - av;
      }
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
  }, [nodes, sortField, sortDir]);

  const getValidationStatus = (node) => {
    if (!node.expected_derivability || node.derivability_class === 'UNKNOWN') return '—';
    const scored = node.derivability_class;
    const expected = node.expected_derivability;
    if (scored === expected) return '✅';
    if (expected === 'DERIVABLE' && scored !== 'DERIVABLE') return '⚠️ FN';
    if (expected !== 'DERIVABLE' && scored === 'DERIVABLE') return '🔴 FP';
    if (expected === 'PARTIALLY_DERIVABLE') return '⚠️';
    return '⚠️';
  };

  const getAction = (cls) => {
    if (cls === 'DERIVABLE') return 'EXCLUDE';
    if (cls === 'PARTIALLY_DERIVABLE') return 'DELTA';
    if (cls === 'NON_DERIVABLE') return 'FULL';
    return '—';
  };

  const getTokensSaved = (node) => {
    const full = node.tokens_full || 0;
    const delta = node.tokens_delta || 0;
    if (node.derivability_class === 'DERIVABLE') return full;
    if (node.derivability_class === 'PARTIALLY_DERIVABLE') return full - delta;
    return 0;
  };

  const columns = [
    { key: 'id', label: 'Node ID', width: 'w-20' },
    { key: 'title', label: 'Title', width: 'w-48' },
    { key: 'derivability_score', label: 'Score', width: 'w-36' },
    { key: 'derivability_class', label: 'Class', width: 'w-32' },
    { key: 'scoring_reason', label: 'Reason', width: 'w-64' },
    { key: 'action', label: 'Action', width: 'w-20' },
    { key: 'tokens_saved', label: 'Saved', width: 'w-16' },
    { key: 'expected_derivability', label: 'Expected', width: 'w-28' },
    { key: 'validation', label: 'Valid', width: 'w-16' },
  ];

  return (
    <div className="glass-card overflow-hidden" id="node-table">
      <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-lg font-bold text-white/90">Scoring Detail — Per Node</h2>
        <span className="text-sm text-white/40">{sortedNodes.length} nodes</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.key !== 'action' && col.key !== 'validation' && col.key !== 'tokens_saved' && handleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-white/50 uppercase tracking-wider cursor-pointer hover:text-white/80 transition-colors ${col.width}`}
                >
                  {col.label}
                  {sortField === col.key && (
                    <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedNodes.map((node) => (
              <tr
                key={node.id}
                onClick={() => onNodeClick(node)}
                className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors group"
                id={`node-row-${node.id}`}
              >
                <td className="px-4 py-3 font-mono text-xs text-indigo-400 font-semibold">
                  {node.id}
                </td>
                <td className="px-4 py-3 text-white/80 font-medium truncate max-w-[200px]" title={node.title}>
                  {node.title}
                </td>
                <td className="px-4 py-3">
                  <ScoreBar score={node.derivability_score ?? 0.5} />
                </td>
                <td className="px-4 py-3">
                  <ClassBadge classification={node.derivability_class || 'UNKNOWN'} />
                </td>
                <td className="px-4 py-3 text-xs text-white/50 truncate max-w-[280px]" title={node.scoring_reason}>
                  {node.scoring_reason || '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-bold ${
                    node.derivability_class === 'DERIVABLE' ? 'text-red-400' :
                    node.derivability_class === 'PARTIALLY_DERIVABLE' ? 'text-amber-400' :
                    'text-emerald-400'
                  }`}>
                    {getAction(node.derivability_class)}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs font-mono text-white/60">
                  {getTokensSaved(node)}
                </td>
                <td className="px-4 py-3">
                  {node.expected_derivability && (
                    <span className="text-xs text-white/40">{node.expected_derivability.replace('_', ' ').slice(0, 12)}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {getValidationStatus(node)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
