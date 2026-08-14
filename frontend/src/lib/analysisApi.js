import api from './api';

// ─── Job Triggers ──────────────────────────────────────────────────────────

export const triggerSummarize = (documentId) =>
  api.post('/api/v1/analysis/summarize', { document_id: documentId });

export const triggerQuiz = (documentId) =>
  api.post('/api/v1/analysis/quiz', { document_id: documentId });

export const triggerFormulaRevision = (documentId) =>
  api.post('/api/v1/analysis/formula-revision', { document_id: documentId });

export const triggerStudyUnitSummary = (documentIds) =>
  api.post('/api/v1/analysis/study_unit-summary', { document_ids: documentIds });

export const triggerComparison = (documentIds) =>
  api.post('/api/v1/analysis/compare', { document_ids: documentIds });

// ─── Job Status ─────────────────────────────────────────────────────────────

export const getAnalysisStatus = (analysisId) =>
  api.get(`/api/v1/analysis/${analysisId}`);

export const getAnalysisDownloadUrls = (analysisId) =>
  api.get(`/api/v1/analysis/${analysisId}/download`);

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Fetches a JSON artifact from a presigned S3 URL.
 * The URL must already be obtained from getAnalysisDownloadUrls.
 */
export const fetchArtifactJson = async (url) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch artifact: ${res.statusText}`);
  return res.json();
};

/**
 * Fetches a Markdown artifact from a presigned S3 URL.
 */
export const fetchArtifactMarkdown = async (url) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch artifact: ${res.statusText}`);
  return res.text();
};

/**
 * Poll until job is COMPLETED or FAILED. Calls onUpdate on each poll.
 * Returns final job data.
 */
export const pollAnalysisJob = (analysisId, onUpdate, intervalMs = 3000) => {
  const interval = setInterval(async () => {
    try {
      const res = await getAnalysisStatus(analysisId);
      const job = res.data.data;
      onUpdate(job);
      if (job.status === 'COMPLETED' || job.status === 'FAILED') {
        clearInterval(interval);
      }
    } catch (err) {
      console.error('Polling error:', err);
      clearInterval(interval);
    }
  }, intervalMs);
  return interval; // return so caller can clear if unmounted
};
