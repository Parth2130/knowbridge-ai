// Human Review & Approvals Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadApprovals();

  const projectSelect = document.getElementById('approvalProjectFilter');
  if (projectSelect) projectSelect.addEventListener('change', () => loadApprovals());
});

async function loadApprovals() {
  const container = document.getElementById('pendingApprovalsContainer');
  const historyContainer = document.getElementById('approvalHistoryContainer');
  if (!container) return;

  const project_id = document.getElementById('approvalProjectFilter')?.value || '';
  const params = new URLSearchParams();
  if (project_id) params.append('project_id', project_id);

  try {
    const res = await fetch(`/api/approvals?${params.toString()}`);
    const data = await res.json();
    const pending = data.pending_items || [];
    const history = data.recent_approvals || [];

    // Pending Items
    if (pending.length === 0) {
      container.innerHTML = `
        <div class="empty-state py-5 bg-white rounded border">
          <div class="empty-state-icon">
            <i data-lucide="shield-check"></i>
          </div>
          <h4>No Items Pending Human Review</h4>
          <p class="text-muted">All AI-extracted deliverables, decisions, and risks have been verified.</p>
        </div>
      `;
    } else {
      container.innerHTML = pending.map(item => `
        <div class="p-3 mb-3 rounded border bg-white shadow-sm">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-primary text-uppercase">${item.type}</span>
              <span class="badge badge-ai">AI-GENERATED (${Math.round((item.confidence || 0.85) * 100)}% CONFIDENCE)</span>
            </div>
            <button class="btn btn-sm btn-kb-outline py-0 px-2" onclick="viewEvidence('${item.type}', ${item.id})">
              <i data-lucide="file-search" style="width:13px;"></i> View Source Evidence
            </button>
          </div>
          <h5 class="fw-bold text-dark mb-1">${item.description || item.title}</h5>
          ${item.reason ? `<div class="small text-muted mb-2">Rationale: ${item.reason}</div>` : ''}
          ${item.suggested_action ? `<div class="small text-muted mb-2">Action: ${item.suggested_action}</div>` : ''}
          <div class="d-flex align-items-center justify-content-between pt-2 border-top mt-2">
            <span class="text-muted small">Project: <b>${item.project_name || 'Project'}</b></span>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-kb-success" onclick="processApproval('${item.type}', ${item.id}, 'Approve')">
                <i data-lucide="check"></i> Approve
              </button>
              <button class="btn btn-sm btn-kb-danger" onclick="promptReject('${item.type}', ${item.id})">
                <i data-lucide="x"></i> Reject
              </button>
            </div>
          </div>
        </div>
      `).join('');
    }

    // History
    if (historyContainer) {
      if (history.length === 0) {
        historyContainer.innerHTML = '<p class="text-muted small text-center py-3">No review actions recorded yet.</p>';
      } else {
        historyContainer.innerHTML = history.map(h => `
          <div class="p-2 mb-2 rounded border bg-light small d-flex justify-content-between align-items-center">
            <div>
              <span class="badge bg-${h.action === 'Approve' ? 'success' : 'danger'} me-1">${h.action}d</span>
              <b>${h.reviewer_name}</b> verified ${h.entity_type} #${h.entity_id}
              <div class="text-muted mt-1 fst-italic">"${h.comments || 'No comment'}"</div>
            </div>
            <div class="text-muted">${h.created_at}</div>
          </div>
        `).join('');
      }
    }

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading approvals:', err);
    showToast('Failed to load approvals: ' + err.message, 'error');
  }
}

async function processApproval(entityType, entityId, action, comments = '') {
  try {
    const res = await fetch(`/api/approvals/${entityId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: entityType, action, comments })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Item successfully marked as ${action}d.`, 'success');
      loadApprovals();
    } else {
      showToast(data.error || 'Failed to update item status.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

function promptReject(entityType, entityId) {
  const reason = prompt('Please enter rejection feedback or reason (optional):', 'Incorrect extraction from document.');
  if (reason !== null) {
    processApproval(entityType, entityId, 'Reject', reason);
  }
}
