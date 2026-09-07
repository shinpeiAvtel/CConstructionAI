const documentIdInput = document.getElementById('document-id');
const loadButton = document.getElementById('load-button');
const downloadButton = document.getElementById('download-button');
const statusRegion = document.getElementById('status-region');

const summaryFields = {
  document: document.getElementById('document-value'),
  filename: document.getElementById('filename-value'),
  vendor: document.getElementById('vendor-value'),
  project: document.getElementById('project-value'),
  quoteNumber: document.getElementById('quote-number-value'),
  verification: document.getElementById('verification-value'),
  analysis: document.getElementById('analysis-value'),
  analysisVerification: document.getElementById('analysis-verification-value'),
  items: document.getElementById('items-value'),
  recommendations: document.getElementById('recommendations-value'),
};

const DEFAULT_TEXT = '—';
let currentDocumentId = null;
let isLoading = false;
let isDownloading = false;

function setStatus(message, type = 'info') {
  statusRegion.textContent = message;
  statusRegion.className = `status-region ${type}`;
}

function displayValue(element, value) {
  const normalized = (value === null || value === undefined || value === '') ? DEFAULT_TEXT : String(value);
  element.textContent = normalized;
}

function updateDownloadButtonState() {
  const hasDocumentId = documentIdInput.value.trim() !== '';
  const isValidDocument = currentDocumentId !== null && Number.isInteger(currentDocumentId) && currentDocumentId > 0;

  downloadButton.disabled = !hasDocumentId || !isValidDocument || isLoading || isDownloading;
  downloadButton.setAttribute('aria-disabled', String(downloadButton.disabled));
  downloadButton.setAttribute('aria-busy', String(isLoading || isDownloading));
  loadButton.setAttribute('aria-busy', String(isLoading));
  statusRegion.setAttribute('aria-busy', String(isLoading || isDownloading));
}

function resetSummary() {
  Object.values(summaryFields).forEach((element) => {
    element.textContent = DEFAULT_TEXT;
  });
}

async function loadDocument() {
  const rawValue = documentIdInput.value.trim();

  if (!rawValue) {
    setStatus('Document ID is required.', 'error');
    currentDocumentId = null;
    resetSummary();
    updateDownloadButtonState();
    return;
  }

  const documentId = Number(rawValue);
  if (!Number.isInteger(documentId) || documentId <= 0) {
    setStatus('Please enter a valid Document ID.', 'error');
    currentDocumentId = null;
    resetSummary();
    updateDownloadButtonState();
    return;
  }

  isLoading = true;
  loadButton.disabled = true;
  loadButton.textContent = 'Loading...';
  setStatus('Loading document...', 'info');
  updateDownloadButtonState();

  try {
    const response = await fetch(`/estimate-documents/${documentId}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      throw new Error('Document not found');
    }

    const result = await response.json();
    currentDocumentId = documentId;

    const source = result || {};
    displayValue(summaryFields.document, source.id ?? documentId);
    displayValue(summaryFields.filename, source.source_filename);
    displayValue(summaryFields.vendor, source.vendor_name);
    displayValue(summaryFields.project, source.project_code);
    displayValue(summaryFields.quoteNumber, source.quote_number);
    displayValue(summaryFields.verification, source.verification_status);
    displayValue(summaryFields.analysis, 'Available');
    displayValue(summaryFields.analysisVerification, source.verification_status ?? '—');
    displayValue(summaryFields.items, '—');
    displayValue(summaryFields.recommendations, '—');

    setStatus('Document loaded successfully.', 'info');
    updateDownloadButtonState();
  } catch (error) {
    currentDocumentId = null;
    resetSummary();
    setStatus('Document not found', 'error');
    updateDownloadButtonState();
  } finally {
    isLoading = false;
    loadButton.disabled = false;
    loadButton.textContent = 'Load Document';
    updateDownloadButtonState();
  }
}

async function downloadAnalysisExcel() {
  if (!documentIdInput.value.trim()) {
    setStatus('Document ID is required.', 'error');
    return;
  }

  const documentId = Number(documentIdInput.value.trim());
  if (!Number.isInteger(documentId) || documentId <= 0) {
    setStatus('Please enter a valid Document ID.', 'error');
    return;
  }

  if (!currentDocumentId || currentDocumentId !== documentId) {
    setStatus('Unable to download analysis', 'error');
    return;
  }

  isDownloading = true;
  downloadButton.disabled = true;
  downloadButton.textContent = 'Preparing Excel...';
  setStatus('Preparing Excel...', 'info');

  try {
    const url = `/documents/${documentId}/analysis/export/excel`;
    const response = await fetch(url, { method: 'GET' });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = `ESTIMATE_ANALYSIS_${documentId}.xlsx`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);

    setStatus('Analysis Excel download started.', 'info');
  } catch (error) {
    setStatus('Unable to download analysis', 'error');
  } finally {
    isDownloading = false;
    downloadButton.textContent = 'Download Analysis Excel';
    updateDownloadButtonState();
  }
}

loadButton.addEventListener('click', (event) => {
  event.preventDefault();
  loadDocument();
});

documentIdInput.addEventListener('input', () => {
  const rawValue = documentIdInput.value.trim();
  if (!rawValue) {
    currentDocumentId = null;
    resetSummary();
  }
  setStatus('');
  updateDownloadButtonState();
});

downloadButton.addEventListener('click', (event) => {
  event.preventDefault();
  downloadAnalysisExcel();
});

resetSummary();
setStatus('Enter a Document ID to load the estimate analysis.', 'info');
updateDownloadButtonState();
