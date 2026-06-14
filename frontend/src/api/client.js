/**
 * API Client for BRAHMO Derivability Scorer backend.
 * All endpoints prefixed with /api (proxied to FastAPI via Vite).
 */

const BASE_URL = '/api';

async function request(url, options = {}) {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function deleteNodesByFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  // NOTE: do NOT set Content-Type — the browser sets the multipart boundary.
  const response = await fetch(`${BASE_URL}/nodes/delete-by-file`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function pasteNodes(text, format = null) {
  return request('/paste-nodes', {
    method: 'POST',
    body: JSON.stringify({ text, format }),
  });
}

export async function deleteNodesByText(text, format = null) {
  return request('/nodes/delete-by-text', {
    method: 'POST',
    body: JSON.stringify({ text, format }),
  });
}

export async function fetchNodes(orgId = 'supra') {
  return request(`/nodes?org_id=${orgId}`);
}

export async function scoreAll(algorithm = 'hybrid', threshold = 0.7, orgId = 'supra') {
  return request('/score-all', {
    method: 'POST',
    body: JSON.stringify({ algorithm, threshold, org_id: orgId }),
  });
}

export async function uploadNodes(file) {
  const formData = new FormData();
  formData.append('file', file);
  // NOTE: do NOT set Content-Type — the browser sets the multipart boundary.
  const response = await fetch(`${BASE_URL}/upload-nodes`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function scoreNode(nodeId, algorithm = 'hybrid', threshold = 0.7) {
  return request('/score-node', {
    method: 'POST',
    body: JSON.stringify({ node_id: nodeId, algorithm, threshold }),
  });
}

/**
 * Score raw ad-hoc content WITHOUT saving to the database (the "surprise test").
 * Because no node_id is sent, the backend scores and returns the result only.
 */
export async function scoreContent({ content, title = '', nodeType = 'FACT', algorithm = 'hybrid', threshold = 0.7 }) {
  return request('/score-node', {
    method: 'POST',
    body: JSON.stringify({ content, title, node_type: nodeType, algorithm, threshold }),
  });
}

export async function fetchMetrics(threshold = 0.7, orgId = 'supra') {
  return request(`/metrics?org_id=${orgId}&threshold=${threshold}`);
}

export async function fetchValidationMatrix(threshold = 0.7, orgId = 'supra') {
  return request(`/validation-matrix?org_id=${orgId}&threshold=${threshold}`);
}

export async function fetchTokenSavings(threshold = 0.7, orgId = 'supra') {
  return request(`/token-savings?org_id=${orgId}&threshold=${threshold}`);
}

export async function fetchThresholdAnalysis(orgId = 'supra') {
  return request(`/threshold-analysis?org_id=${orgId}`);
}
