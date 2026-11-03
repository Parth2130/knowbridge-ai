// Document Management Controller for KnowBridge AI

let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDocuments();

  const fileInput = document.getElementById('fileUploadInput');
  const dropzone = document.getElementById('uploadDropzone');
  const uploadForm = document.getElementById('uploadDocumentForm');
  const searchInput = document.getElementById('docSearchInput');
  const typeFilter = document.getElementById('docTypeFilter');
  const projectFilter = document.getElementById('docProjectFilter');

  if (searchInput) searchInput.addEventListener('input', () => loadDocuments());
  if (typeFilter) typeFilter.addEventListener('change', () => loadDocuments());
  if (projectFilter) projectFilter.addEventListener('change', () => loadDocuments());

  // Drag and Drop
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', handleUploadSubmit);
  }
});

function handleFileSelection(file) {
  const allowed = ['pdf', 'docx', 'txt'];
  const ext = file.name.split('.').pop().toLowerCase();
  
  if (!allowed.includes(ext)) {
    showToast('Invalid file format. Please upload a PDF, DOCX, or TXT file.', 'error');
    return;
  }

  if (file.size > 16 * 1024 * 1024) {
    showToast('File size exceeds the 16 MB maximum limit.', 'error');
    return;
  }

  selectedFile = file;
  const fileNameDisplay = document.getElementById('selectedFileName');
  const fileMetaDisplay = document.getElementById('selectedFileMeta');
  const selectedFileInfo = document.getElementById('selectedFileInfo');

  if (fileNameDisplay) fileNameDisplay.innerText = file.name;
  if (fileMetaDisplay) {
    const sizeKB = (file.size / 1024).toFixed(1);
    fileMetaDisplay.innerText = `${ext.toUpperCase()} • ${sizeKB} KB`;
  }
  if (selectedFileInfo) selectedFileInfo.classList.remove('d-none');
}

async function loadDocuments() {
  const tableBody = document.getElementById('documentsTableBody');
  if (!tableBody) return;

  const search = document.getElementById('docSearchInput')?.value || '';
  const file_type = document.getElementById('docTypeFilter')?.value || '';
  const project_id = document.getElementById('docProjectFilter')?.value || '';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (file_type) params.append('file_type', file_type);
  if (project_id) params.append('project_id', project_id);

  try {
    const res = await fetch(`/api/documents?${params.toString()}`);
    const data = await res.json();
    const docs = data.documents || [];

    if (docs.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-5">
            <div class="empty-state">
              <div class="empty-state-icon">
                <i data-lucide="file-x"></i>
              </div>
              <h4>No Documents Found</h4>
              <p class="text-muted">Upload project documents (PDF, DOCX, TXT) to begin AI knowledge extraction.</p>
              <button class="btn-kb-primary" data-bs-toggle="modal" data-bs-target="#uploadDocModal">
                <i data-lucide="upload-cloud"></i> Upload First Document
              </button>
            </div>
          </td>
        </tr>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    tableBody.innerHTML = docs.map(d => {
      let statusBadge = '<span class="badge badge-status badge-active">Analysed</span>';
      if (d.processing_status === 'Extracted') {
        statusBadge = '<span class="badge badge-status badge-pending">Extracted</span>';
      } else if (d.processing_status === 'Uploaded') {
        statusBadge = '<span class="badge badge-status badge-review">Uploaded</span>';
      } else if (d.processing_status === 'Failed') {
        statusBadge = '<span class="badge badge-status badge-blocked">Failed</span>';
      }

      let typeBadgeColor = 'primary';
      if (d.file_type === 'PDF') typeBadgeColor = 'danger';
      if (d.file_type === 'DOCX') typeBadgeColor = 'primary';
      if (d.file_type === 'TXT') typeBadgeColor = 'secondary';

      return `
        <tr>
          <td>
            <div class="d-flex align-items-center gap-2">
              <i data-lucide="file-text" class="text-${typeBadgeColor}" style="width:20px;height:20px;"></i>
              <div>
                <div class="fw-bold text-dark">${d.original_filename}</div>
                <div class="text-muted small">${d.page_count} page(s) • ${d.file_size_formatted}</div>
              </div>
            </div>
          </td>
          <td><span class="badge bg-${typeBadgeColor} bg-opacity-10 text-${typeBadgeColor} border border-${typeBadgeColor} border-opacity-25">${d.file_type}</span></td>
          <td class="fw-semibold text-dark">${d.project_name || 'Unassigned'}</td>
          <td class="text-muted small">${d.uploaded_at}</td>
          <td>${statusBadge}</td>
          <td class="text-end">
            <div class="d-flex align-items-center justify-content-end gap-1">
              <button class="btn btn-sm btn-outline-primary" title="View Extracted Content" onclick="viewDocument(${d.id})">
                <i data-lucide="eye" style="width:14px;height:14px;"></i>
              </button>
              <a href="/api/documents/${d.id}/download" class="btn btn-sm btn-outline-secondary" title="Download Document">
                <i data-lucide="download" style="width:14px;height:14px;"></i>
              </a>
              <a href="/analysis?doc_id=${d.id}" class="btn btn-sm btn-kb-secondary" title="Run AI Knowledge Extraction">
                <i data-lucide="zap" style="width:14px;height:14px;"></i> Analyze
              </a>
              <button class="btn btn-sm btn-outline-danger" title="Delete Document" onclick="deleteDocument(${d.id}, '${d.original_filename}')">
                <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading documents:', err);
    showToast('Failed to load documents: ' + err.message, 'error');
  }
}

async function handleUploadSubmit(e) {
  e.preventDefault();
  if (!selectedFile) {
    showToast('Please select or drop a file to upload.', 'error');
    return;
  }

  const projectId = document.getElementById('uploadProjectId').value;
  if (!projectId) {
    showToast('Please select the project to which this document belongs.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('project_id', projectId);

  const submitBtn = document.getElementById('uploadSubmitBtn');
  const progressContainer = document.getElementById('uploadProgressBarContainer');
  const progressBar = document.getElementById('uploadProgressBar');

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Extracting Text...';
  if (progressContainer) progressContainer.classList.remove('d-none');
  if (progressBar) progressBar.style.width = '60%';

  try {
    const res = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (res.ok) {
      if (progressBar) progressBar.style.width = '100%';
      showToast('Document uploaded and text extracted successfully!', 'success');
      
      setTimeout(() => {
        const modalEl = document.getElementById('uploadDocModal');
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();

        selectedFile = null;
        document.getElementById('uploadDocumentForm').reset();
        document.getElementById('selectedFileInfo').classList.add('d-none');
        if (progressContainer) progressContainer.classList.add('d-none');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="upload"></i> Upload & Extract';
        loadDocuments();
      }, 500);
    } else {
      showToast(data.error || 'Failed to upload document.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="upload"></i> Upload & Extract';
      if (progressContainer) progressContainer.classList.add('d-none');
    }
  } catch (err) {
    showToast('Upload error: ' + err.message, 'error');
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i data-lucide="upload"></i> Upload & Extract';
    if (progressContainer) progressContainer.classList.add('d-none');
  }
}

async function viewDocument(docId) {
  const modalEl = document.getElementById('viewDocModal');
  const titleEl = document.getElementById('viewDocTitle');
  const bodyEl = document.getElementById('viewDocBody');
  const metaEl = document.getElementById('viewDocMeta');

  bodyEl.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="text-muted mt-2">Loading extracted text content...</p>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  try {
    const res = await fetch(`/api/documents/${docId}`);
    const data = await res.json();
    const doc = data.document;

    titleEl.innerText = doc.original_filename;
    metaEl.innerHTML = `
      <span class="badge bg-primary">${doc.file_type}</span>
      <span class="text-muted small">Uploaded: ${doc.uploaded_at}</span>
      <span class="text-muted small">• ${doc.page_count} page(s) • ${doc.file_size_formatted}</span>
    `;

    if (doc.pages && doc.pages.length > 0) {
      bodyEl.innerHTML = doc.pages.map(p => `
        <div class="card mb-3 border">
          <div class="card-header bg-light py-2 d-flex justify-content-between align-items-center">
            <span class="fw-bold small text-primary"><i data-lucide="file-text" style="width:14px;"></i> Page ${p.page_number} (${p.section_title})</span>
            <span class="text-muted small">${(p.text || '').length} characters</span>
          </div>
          <div class="card-body p-3">
            <pre style="white-space: pre-wrap; font-family: inherit; font-size: 0.88rem; color: #243449; margin-bottom: 0;">${escapeHtml(p.text || 'No text extracted on this page.')}</pre>
          </div>
        </div>
      `).join('');
    } else {
      bodyEl.innerHTML = `
        <div class="p-3 bg-light rounded text-muted">
          ${escapeHtml(doc.full_preview || 'No text content available.')}
        </div>
      `;
    }

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    bodyEl.innerHTML = `<div class="alert alert-danger">Failed to load document preview: ${err.message}</div>`;
  }
}

async function deleteDocument(id, filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

  try {
    const res = await fetch(`/api/documents/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Document deleted.', 'success');
      loadDocuments();
    } else {
      showToast(data.error || 'Failed to delete document.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}
