// Global Application Helpers for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons if available
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Mobile sidebar toggle
  const mobileToggle = document.getElementById('mobileSidebarToggle');
  const sidebar = document.querySelector('.app-sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }
});

// Toast notification function
function showToast(message, type = 'info') {
  let container = document.getElementById('kb-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'kb-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `kb-toast ${type}`;
  
  let iconName = 'info';
  if (type === 'success') iconName = 'check-circle';
  if (type === 'error') iconName = 'alert-triangle';
  if (type === 'warning') iconName = 'alert-circle';

  toast.innerHTML = `
    <i data-lucide="${iconName}"></i>
    <div style="flex:1;">${message}</div>
    <button type="button" style="background:none;border:none;cursor:pointer;color:#718096;" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(toast);

  if (window.lucide) {
    window.lucide.createIcons({ root: toast });
  }

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Reusable Evidence Modal
async function viewEvidence(entityType, entityId) {
  const modalEl = document.getElementById('evidenceModal');
  if (!modalEl) return;

  const titleEl = document.getElementById('evidenceModalTitle');
  const bodyEl = document.getElementById('evidenceModalBody');
  const docNameEl = document.getElementById('evidenceDocName');
  const pageNumEl = document.getElementById('evidencePageNum');
  const quoteEl = document.getElementById('evidenceQuote');
  const statusEl = document.getElementById('evidenceStatus');

  bodyEl.innerHTML = `
    <div class="text-center py-4">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="text-muted mt-2">Retrieving supporting document source citation...</p>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  try {
    const res = await fetch(`/api/evidence/entity/${entityType}/${entityId}`);
    const data = await res.json();

    if (data.available && data.evidence) {
      const ev = data.evidence;
      titleEl.innerText = `Supporting Evidence for ${entityType.toUpperCase()}`;
      bodyEl.innerHTML = `
        <div class="mb-3">
          <label class="form-label text-muted">Related Extracted ${entityType.toUpperCase()}</label>
          <div class="fw-bold text-dark p-2 rounded" style="background-color:#F4F8FC;border:1px solid #DFE9F2;">
            ${ev.entity_description || 'Extracted Item'}
          </div>
        </div>
        <div class="d-flex align-items-center gap-2 mb-3">
          <span class="evidence-meta-tag"><i data-lucide="file-text" style="width:14px;"></i> ${ev.document_name}</span>
          <span class="evidence-meta-tag"><i data-lucide="bookmark" style="width:14px;"></i> Page ${ev.page_number || '1'}</span>
          <span class="evidence-meta-tag"><i data-lucide="shield-check" style="width:14px;"></i> Confidence: ${Math.round((ev.confidence_score || 0.9) * 100)}%</span>
        </div>
        <label class="form-label text-muted">Original Source Citation (Exact Extracted Text)</label>
        <div class="evidence-highlight-box">
          "${ev.original_text}"
        </div>
        <div class="text-end text-muted small mt-2">
          Citation reference: ${ev.extraction_reference || 'Verified by KnowBridge NLP Engine'}
        </div>
      `;
    } else {
      titleEl.innerText = `Supporting Evidence`;
      bodyEl.innerHTML = `
        <div class="empty-state py-3">
          <div class="empty-state-icon" style="background:#FEE2E2;color:#EF4444;">
            <i data-lucide="alert-circle"></i>
          </div>
          <h4>Evidence Unavailable</h4>
          <p class="text-muted">No explicit source document citation was linked to this item. It may have been manually authored or verified outside document extraction.</p>
        </div>
      `;
    }

    if (window.lucide) {
      window.lucide.createIcons({ root: bodyEl });
    }
  } catch (err) {
    bodyEl.innerHTML = `<div class="alert alert-danger">Failed to load evidence details: ${err.message}</div>`;
  }
}
