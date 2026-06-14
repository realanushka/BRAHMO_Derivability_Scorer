/**
 * App.jsx — Main application component for BRAHMO Derivability Scorer.
 *
 * Manages global state, API calls, and renders all dashboard sections:
 * Header, Controls, StatsCards, NodeTable, NodeModal, ValidationMatrix,
 * ThresholdChart, and TokenSavings.
 */
import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Controls from './components/Controls';
import UploadNodes from './components/UploadNodes';
import PasteNodes from './components/PasteNodes';
import TestPlayground from './components/TestPlayground';
import StatsCards from './components/StatsCards';
import NodeTable from './components/NodeTable';
import NodeModal from './components/NodeModal';
import ValidationMatrix from './components/ValidationMatrix';
import ThresholdChart from './components/ThresholdChart';
import TokenSavings from './components/TokenSavings';
import {
  fetchNodes,
  scoreAll,
  fetchMetrics,
  fetchValidationMatrix,
  fetchTokenSavings,
  fetchThresholdAnalysis,
} from './api/client';

export default function App() {
  // --- Global State ---
  const [nodes, setNodes] = useState([]);
  const [threshold, setThreshold] = useState(0.70);
  const [algorithm, setAlgorithm] = useState('hybrid');
  const [metrics, setMetrics] = useState(null);
  const [savings, setSavings] = useState(null);
  const [validationMatrix, setValidationMatrix] = useState(null);
  const [thresholdData, setThresholdData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'playground'

  // --- Load all data ---
  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [nodesRes, metricsRes, savingsRes, matrixRes, threshRes] = await Promise.all([
        fetchNodes(),
        fetchMetrics(threshold),
        fetchTokenSavings(threshold),
        fetchValidationMatrix(threshold),
        fetchThresholdAnalysis(),
      ]);
      setNodes(nodesRes.nodes || []);
      setMetrics(metricsRes);
      setSavings(savingsRes);
      setValidationMatrix(matrixRes);
      setThresholdData(threshRes);
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err.message);
    } finally {
      setInitialLoad(false);
    }
  }, [threshold]);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, [loadData]);

  // --- Rescore All ---
  const handleRescore = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await scoreAll(algorithm, threshold);
      // Refresh all data after scoring
      await loadData();
    } catch (err) {
      console.error('Scoring error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- Threshold Change ---
  const handleThresholdChange = (value) => {
    setThreshold(value);
  };

  // --- Modal ---
  const handleNodeClick = (node) => setSelectedNode(node);
  const handleCloseModal = () => setSelectedNode(null);

  // --- Error Banner ---
  if (error && initialLoad) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="glass-card p-10 max-w-lg text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-white mb-3">Cannot Connect to Backend</h2>
          <p className="text-white/60 mb-4 text-sm">{error}</p>
          <div className="bg-white/5 rounded-xl p-4 text-left text-sm text-white/50 space-y-1">
            <p>Make sure the backend is running:</p>
            <code className="block text-indigo-400 mt-2">cd backend</code>
            <code className="block text-indigo-400">uvicorn app.main:app --reload</code>
          </div>
          <button onClick={loadData} className="btn-primary mt-6">Retry Connection</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      {/* Header */}
      <Header />

      {/* Tab bar */}
      <div className="flex gap-2">
        {[
          { id: 'dashboard', label: '📊 Dashboard' },
          { id: 'playground', label: '🧪 Test Playground' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
              activeTab === tab.id
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Banner (non-blocking) */}
      {error && !initialLoad && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-3 text-sm text-red-400 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button>
        </div>
      )}

      {activeTab === 'playground' ? (
        /* ── Test Playground tab ── */
        <TestPlayground />
      ) : (
        /* ── Dashboard tab ── */
        <>
          {/* Controls */}
          <Controls
            threshold={threshold}
            algorithm={algorithm}
            onThresholdChange={handleThresholdChange}
            onAlgorithmChange={setAlgorithm}
            onRescore={handleRescore}
            loading={loading}
          />

          {/* Upload Nodes (file) */}
          <UploadNodes onChanged={loadData} />

          {/* Paste Nodes (text) */}
          <PasteNodes onChanged={loadData} />

          {/* Stats Cards */}
          <StatsCards metrics={metrics} savings={savings} />

          {/* Node Table */}
          <NodeTable nodes={nodes} onNodeClick={handleNodeClick} threshold={threshold} />

          {/* Two-column layout for validation + savings */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <ValidationMatrix matrix={validationMatrix} />
            <TokenSavings savings={savings} />
          </div>

          {/* Threshold Chart (full width) */}
          <ThresholdChart thresholdData={thresholdData} currentThreshold={threshold} />

          {/* Node Detail Modal */}
          <NodeModal node={selectedNode} onClose={handleCloseModal} />
        </>
      )}
    </div>
  );
}
