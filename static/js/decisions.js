// Decision Tracking Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadDecisions();

  const searchInput = document.getElementById('decisionSearchInput');
  const projectFilter = document.getElementById('decisionProjectFilter');
  const statusFilter = document.getElementById('decisionStatusFilter');
  const decisionForm = document.getElementById('decisionForm');

  if (searchInput) searchInput.addEventListener('input', () => loadDecisions());
  if (projectFilter) projectFilter.addEventListener('change', () => loadDecisions());
  if (statusFilter) statusFilter.addEventListener('change', () => loadDecisions());

  if (decisionForm) {
    decisionForm.addEventListener('submit', handleDecisionSubmit);
  }
});

async function loadDecisions() {
  const container = document.getElementById('decisionsTimelineContainer');
  if (!container) return;

  const search = document.getElementById('decisionSearchInput')?.value || '';
  const project_id = document.getElementById('decisionProjectFilter')?.value || '';
  const status = document.getElementById('decisionStatusFilter')?.value || '';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (project_id) params.append('project_id', project_id);
  if (status) params.append('status', status);

  try {
    const res = await fetch(`/api/decisions?${params.toString()}`);
    const data = await res.json();
    const decisions = data.decisions || [];

    if (decisions.length === 0) {
      container.innerHTML = `
        <div class="empty-state py-5 bg-white rounded border">
          <div class="empty-state-icon">
            <i data-lucide="git-commit"></i>
          </div>
          <h4>No Architectural Decisions Found</h4>
          <p class="text-muted">Extract decisions from documents or log an architectural decision record (ADR).</p>
          <button class="btn-kb-primary" data-bs-toggle="modal" data-bs-target="#decisionModal" onclick="resetDecisionForm()">
            <i data-lucide="plus"></i> Record Decision
          </button>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = `
      <div class="timeline-track">
        ${decisions.map(d => `
          <div class="timeline-node">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="badge bg-light text-primary border">${d.project_name || 'Project'}</span>
                <div class="d-flex align-items-center gap-2">
                  <span class="badge badge-ai" style="font-size:0.7rem;">${d.verification_status}</span>
                  <span class="badge badge-status badge-${(d.status || 'approved').toLowerCase()}">${d.status}</span>
                </div>
              </div>
              <h5 class="fw-bold text-dark mb-2">${d.title}</h5>
              <p class="text-muted small mb-2">${d.description}</p>
              ${d.reason ? `
                <div class="p-2 rounded mb-3" style="background:#F4F8FC;border-left:3px solid #2475E8;font-size:0.83rem;">
                  <b>Rationale:</b> ${d.reason}
                </div>
              ` : ''}
              <div class="d-flex align-items-center justify-content-between border-top pt-2 mt-2">
                <span class="text-muted small"><i data-lucide="calendar" style="width:13px;"></i> Date: ${d.decision_date || 'Recorded'}</span>
                <div class="d-flex gap-2">
                  <button class="btn btn-sm btn-kb-outline" onclick="viewEvidence('decision', ${d.id})">
                    <i data-lucide="file-search" style="width:13px;"></i> View Evidence
                  </button>
                  <button class="btn btn-sm btn-outline-primary" onclick="editDecision(${JSON.stringify(d).replace(/"/g, '&quot;')})">
                    <i data-lucide="edit-2" style="width:13px;"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" onclick="deleteDecision(${d.id})">
                    <i data-lucide="trash-2" style="width:13px;"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading decisions:', err);
    showToast('Failed to load decisions: ' + err.message, 'error');
  }
}

function resetDecisionForm() {
  const form = document.getElementById('decisionForm');
  if (form) form.reset();
  document.getElementById('decisionId').value = '';
  document.getElementById('decisionModalTitle').innerText = 'Record New Decision';
}

function editDecision(d) {
  document.getElementById('decisionId').value = d.id;
  document.getElementById('decisionProject').value = d.project_id;
  document.getElementById('decisionTitle').value = d.title;
  document.getElementById('decisionDescription').value = d.description;
  document.getElementById('decisionReason').value = d.reason || '';
  document.getElementById('decisionDate').value = d.decision_date || '';
  document.getElementById('decisionStatus').value = d.status;
  document.getElementById('decisionModalTitle').innerText = 'Edit Decision Record';

  const modalEl = document.getElementById('decisionModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleDecisionSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('decisionId').value;
  const project_id = document.getElementById('decisionProject').value;
  const title = document.getElementById('decisionTitle').value.trim();
  const description = document.getElementById('decisionDescription').value.trim();
  const reason = document.getElementById('decisionReason').value.trim();
  const decision_date = document.getElementById('decisionDate').value.trim();
  const status = document.getElementById('decisionStatus').value;

  const payload = { project_id, title, description, reason, decision_date, status };
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/decisions/${id}` : '/api/decisions';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(id ? 'Decision updated successfully.' : 'Decision recorded successfully.', 'success');
      const modalEl = document.getElementById('decisionModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadDecisions();
    } else {
      showToast(data.error || 'Failed to save decision.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

async function deleteDecision(id) {
  if (!confirm('Are you sure you want to delete this decision?')) return;
  try {
    const res = await fetch(`/api/decisions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Decision removed.', 'success');
      loadDecisions();
    } else {
      showToast(data.error || 'Failed to delete decision.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}
