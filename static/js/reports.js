// Handover Report Controller for KnowBridge AI

let activeReportId = null;

document.addEventListener('DOMContentLoaded', () => {
  loadReports();

  const generateBtn = document.getElementById('generateReportBtn');
  const projectSelect = document.getElementById('reportProjectFilter');
  const editReportForm = document.getElementById('editReportForm');
  const acknowledgeBtn = document.getElementById('acknowledgeReportBtn');

  if (projectSelect) projectSelect.addEventListener('change', () => loadReports());

  if (generateBtn) {
    generateBtn.addEventListener('click', handleGenerateReport);
  }

  if (editReportForm) {
    editReportForm.addEventListener('submit', handleReportEdit);
  }

  if (acknowledgeBtn) {
    acknowledgeBtn.addEventListener('click', handleAcknowledge);
  }

  // Check URL query param for previewing specific report
  const urlParams = new URLSearchParams(window.location.search);
  const viewId = urlParams.get('view');
  if (viewId) {
    previewReport(viewId);
  }
});

async function loadReports() {
  const container = document.getElementById('reportsListContainer');
  if (!container) return;

  const project_id = document.getElementById('reportProjectFilter')?.value || '';
  const params = new URLSearchParams();
  if (project_id) params.append('project_id', project_id);

  try {
    const res = await fetch(`/api/reports?${params.toString()}`);
    const data = await res.json();
    const reports = data.reports || [];

    if (reports.length === 0) {
      container.innerHTML = `
        <div class="empty-state py-5 bg-white rounded border">
          <div class="empty-state-icon">
            <i data-lucide="file-text"></i>
          </div>
          <h4>No Handover Reports Generated Yet</h4>
          <p class="text-muted">Generate a 16-section intelligent handover report combining live database knowledge.</p>
          <button class="btn-kb-primary" onclick="openGenerateModal()">
            <i data-lucide="plus"></i> Generate Handover Report
          </button>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = reports.map(r => `
      <div class="dashboard-card mb-3">
        <div class="dashboard-card-header">
          <div>
            <div class="d-flex align-items-center gap-2 mb-1">
              <h5 class="fw-bold mb-0 text-dark">${r.title}</h5>
              <span class="badge badge-status badge-${r.status === 'Acknowledged' ? 'active' : 'pending'}">${r.status}</span>
              <span class="badge bg-light text-primary border">Version ${r.current_version} (${r.version_count} revisions)</span>
            </div>
            <div class="text-muted small">Project: <b>${r.project_name}</b> • Generated: ${r.created_at}</div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <button class="btn btn-sm btn-kb-outline" onclick="previewReport(${r.id})">
              <i data-lucide="eye"></i> Preview
            </button>
            <a href="/api/reports/${r.id}/download" class="btn btn-sm btn-kb-primary">
              <i data-lucide="download"></i> Download PDF
            </a>
            <button class="btn btn-sm btn-outline-secondary" onclick="openVersionHistory(${r.id})">
              <i data-lucide="history"></i> History
            </button>
          </div>
        </div>
        <div class="dashboard-card-body">
          <p class="text-muted small mb-3">${r.summary || 'Official knowledge handover documentation.'}</p>
          <div class="d-flex align-items-center justify-content-between p-2 rounded" style="background:#F4F8FC;font-size:0.85rem;">
            <span>Outgoing: <b>${r.outgoing_member}</b></span>
            <span>→</span>
            <span>Incoming: <b class="text-primary">${r.incoming_member}</b></span>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-primary py-0 px-2" onclick="openEditModal(${r.id}, '${escapeHtml(r.summary || '')}')">
                <i data-lucide="edit-3" style="width:12px;"></i> Edit Summary
              </button>
              ${r.status !== 'Acknowledged' ? `
                <button class="btn btn-sm btn-kb-success py-0 px-2" onclick="promptAcknowledge(${r.id})">
                  <i data-lucide="check-circle" style="width:12px;"></i> Acknowledge
                </button>
              ` : '<span class="text-success small fw-semibold"><i data-lucide="check-check" style="width:13px;"></i> Formally Acknowledged</span>'}
            </div>
          </div>
        </div>
      </div>
    `).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading reports:', err);
    showToast('Failed to load reports: ' + err.message, 'error');
  }
}

function openGenerateModal() {
  const modalEl = document.getElementById('generateReportModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleGenerateReport(e) {
  e.preventDefault();
  const projectId = document.getElementById('genReportProject').value;
  const title = document.getElementById('genReportTitle').value.trim();

  if (!projectId) {
    showToast('Please select a project.', 'warning');
    return;
  }

  const btn = document.getElementById('generateReportSubmitBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Compiling 16 Sections...';

  try {
    const res = await fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, title })
    });
    const data = await res.json();

    if (res.ok) {
      showToast('Handover report generated successfully!', 'success');
      const modalEl = document.getElementById('generateReportModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadReports();
      previewReport(data.report.id);
    } else {
      showToast(data.error || 'Failed to generate report.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="zap"></i> Generate Report';
  }
}

async function previewReport(reportId) {
  activeReportId = reportId;
  const modalEl = document.getElementById('previewReportModal');
  const titleEl = document.getElementById('previewReportTitle');
  const bodyEl = document.getElementById('previewReportBody');
  const dlLink = document.getElementById('previewDownloadPdfBtn');

  if (dlLink) dlLink.href = `/api/reports/${reportId}/download`;

  bodyEl.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="text-muted mt-2">Loading complete 16-section handover report...</p>
    </div>
  `;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  try {
    const res = await fetch(`/api/reports/${reportId}`);
    const data = await res.json();
    const r = data.report;
    const c = r.content || {};

    titleEl.innerText = r.title;

    bodyEl.innerHTML = `
      <div class="report-paper">
        <div class="d-flex justify-content-between align-items-start border-bottom pb-3 mb-4">
          <div>
            <h2 class="text-primary fw-bold mb-1">KNOWBRIDGE AI</h2>
            <div class="text-muted small">Enterprise Knowledge Handover Document • Team Code Crushers</div>
          </div>
          <div class="text-end">
            <span class="badge badge-status badge-approved">Version ${r.current_version} (${r.status})</span>
            <div class="text-muted small mt-1">Generated: ${r.created_at}</div>
          </div>
        </div>

        <!-- 1 - 4: Metadata Overview Table -->
        <table class="table table-bordered mb-4" style="background:#F8FBFE;font-size:0.88rem;">
          <tr>
            <td width="20%" class="fw-bold text-muted">1. Project Title:</td>
            <td width="30%" class="fw-bold text-dark">${c['1_project_title'] || r.project_name}</td>
            <td width="20%" class="fw-bold text-muted">Category:</td>
            <td width="30%">${c.category || 'Engineering'}</td>
          </tr>
          <tr>
            <td class="fw-bold text-muted">3. Outgoing Member:</td>
            <td class="fw-bold text-dark">${c['3_outgoing_member'] || r.outgoing_member}</td>
            <td class="fw-bold text-muted">4. Incoming Member:</td>
            <td class="fw-bold text-primary">${c['4_incoming_member'] || r.incoming_member}</td>
          </tr>
          <tr>
            <td class="fw-bold text-muted">Project Timeline:</td>
            <td colspan="3">${c.start_date || 'N/A'} through ${c.deadline || 'N/A'}</td>
          </tr>
        </table>

        <!-- 5. Executive Summary -->
        <div class="report-section-title">5. Project Summary & Handover Scope</div>
        <p class="text-dark" style="line-height:1.6;">${c['5_project_summary'] || r.summary}</p>

        <!-- 6. Completed Tasks -->
        <div class="report-section-title">6. Completed Tasks</div>
        ${renderTaskList(c['6_completed_tasks'])}

        <!-- 7. Pending Deliverables -->
        <div class="report-section-title">7. Pending & In-Progress Deliverables</div>
        ${renderTaskList(c['7_pending_tasks'])}

        <!-- 8. Important Decisions -->
        <div class="report-section-title">8. Architectural & Strategic Decisions</div>
        ${renderDecisionsList(c['8_important_decisions'])}

        <!-- 9. Task Responsibilities -->
        <div class="report-section-title">9. Task Responsibilities & Contact Mapping</div>
        ${renderResponsibilities(c['9_task_responsibilities'])}

        <!-- 10. Critical Deadlines -->
        <div class="report-section-title">10. Milestone Deadlines</div>
        ${renderDeadlines(c['10_deadlines'])}

        <!-- 11. Identified Risks -->
        <div class="report-section-title">11. Identified Project Risks</div>
        ${renderRisks(c['11_identified_risks'])}

        <!-- 12. Dependencies -->
        <div class="report-section-title">12. Task Dependencies & Blockers</div>
        ${renderDependencies(c['12_dependencies'])}

        <!-- 13. Supporting Evidence -->
        <div class="report-section-title">13. Supporting Evidence & Source Citations</div>
        ${renderEvidenceList(c['13_supporting_evidence'])}

        <!-- 14. Missing Information -->
        <div class="report-section-title">14. Missing Information & Documentation Gaps</div>
        ${renderMissing(c['14_missing_information'])}

        <!-- 15. Next Action Plan -->
        <div class="report-section-title">15. Next Action Plan (30-60-90 Day Transition)</div>
        ${renderActionPlan(c['15_next_action_plan'])}

        <!-- 16. Approval Status & Digital Signature -->
        <div class="report-section-title">16. Approval & Verification Status</div>
        <div class="p-3 rounded border bg-light">
          <div class="d-flex justify-content-between mb-2">
            <span>Status: <b>${c['16_approval_status']?.status || 'Verified'}</b></span>
            <span>Reviewer: <b>${c['16_approval_status']?.reviewer || 'Alex Chen'}</b></span>
          </div>
          <div class="text-muted small">Notes: ${c['16_approval_status']?.comments || 'All tasks and architectural decisions approved.'}</div>
        </div>
      </div>
    `;

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    bodyEl.innerHTML = `<div class="alert alert-danger">Failed to load report preview: ${err.message}</div>`;
  }
}

function renderTaskList(tasks) {
  if (!tasks || tasks.length === 0) return '<p class="text-muted small">None recorded.</p>';
  return `
    <ul class="list-group mb-3">
      ${tasks.map(t => `
        <li class="list-group-item d-flex justify-content-between align-items-center py-2">
          <span>${t.description}</span>
          <span class="badge badge-status badge-${t.status.toLowerCase().replace(' ', '-')}">${t.status} (Owner: ${t.responsible_person})</span>
        </li>
      `).join('')}
    </ul>
  `;
}

function renderDecisionsList(decisions) {
  if (!decisions || decisions.length === 0) return '<p class="text-muted small">No architectural decisions recorded.</p>';
  return `
    <table class="table table-sm table-bordered mb-3" style="font-size:0.85rem;">
      <thead class="table-light">
        <tr><th>Title</th><th>Rationale</th><th>Date</th></tr>
      </thead>
      <tbody>
        ${decisions.map(d => `
          <tr>
            <td class="fw-bold">${d.title}</td>
            <td>${d.reason || d.description}</td>
            <td>${d.decision_date || 'N/A'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderResponsibilities(resp) {
  if (!resp || Object.keys(resp).length === 0) return '<p class="text-muted small">No responsibilities mapped.</p>';
  return Object.keys(resp).map(owner => `
    <div class="mb-2 p-2 rounded bg-light border small">
      <b>${owner}:</b>
      <ul class="mb-0 ps-3">
        ${resp[owner].map(item => `<li>${typeof item === 'object' ? item.task : item}</li>`).join('')}
      </ul>
    </div>
  `).join('');
}

function renderDeadlines(deadlines) {
  if (!deadlines || deadlines.length === 0) return '<p class="text-muted small">No deadlines scheduled.</p>';
  return `
    <table class="table table-sm table-bordered mb-3" style="font-size:0.85rem;">
      <thead class="table-light"><tr><th>Milestone</th><th>Deadline</th><th>Owner</th></tr></thead>
      <tbody>
        ${deadlines.map(dl => `
          <tr><td>${dl.item}</td><td class="fw-bold text-primary">${dl.deadline}</td><td>${dl.responsible}</td></tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderRisks(risks) {
  if (!risks || risks.length === 0) return '<p class="text-muted small">No active risks identified.</p>';
  return risks.map(r => `
    <div class="risk-card ${(r.severity || 'medium').toLowerCase()} p-2 mb-2 small">
      <div class="d-flex justify-content-between">
        <b>${r.description}</b>
        <span class="badge badge-status badge-high">${r.severity}</span>
      </div>
      <div class="text-muted mt-1">Suggested Action: ${r.suggested_action}</div>
    </div>
  `).join('');
}

function renderDependencies(deps) {
  if (!deps || deps.length === 0) return '<p class="text-muted small">No task dependencies identified.</p>';
  return deps.map(dp => `
    <div class="p-2 mb-1 rounded bg-light border small">
      <span class="badge bg-danger me-1">BLOCKER</span> ${dp.description || `${dp.prerequisite_task_desc || dp.prerequisite} must precede ${dp.dependent_task_desc || dp.dependent}`}
    </div>
  `).join('');
}

function renderEvidenceList(evidence) {
  if (!evidence || evidence.length === 0) return '<p class="text-muted small">Evidence unavailable or pending initial document analysis.</p>';
  return `
    <table class="table table-sm table-bordered mb-3" style="font-size:0.85rem;">
      <thead class="table-light"><tr><th>Entity</th><th>Document</th><th>Page</th><th>Original Quote</th></tr></thead>
      <tbody>
        ${evidence.map(ev => `
          <tr>
            <td class="fw-bold">${ev.item_name}</td>
            <td>${ev.document_name}</td>
            <td>Page ${ev.page_number || 1}</td>
            <td class="text-muted fst-italic">"${ev.quote}"</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderMissing(missing) {
  if (!missing || missing.length === 0) return '<p class="text-success small">No missing documentation gaps found.</p>';
  return missing.map(m => `<div class="text-danger small mb-1">• ${m}</div>`).join('');
}

function renderActionPlan(plan) {
  if (!plan || plan.length === 0) return '<p class="text-muted small">Action plan not specified.</p>';
  return plan.map(p => `
    <div class="p-2 mb-1 rounded bg-light border small">
      <b class="text-primary">${p.timeframe}:</b> ${p.action}
    </div>
  `).join('');
}

function openEditModal(reportId, currentSummary) {
  document.getElementById('editReportId').value = reportId;
  document.getElementById('editReportSummary').value = currentSummary;
  const modalEl = document.getElementById('editReportModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleReportEdit(e) {
  e.preventDefault();
  const reportId = document.getElementById('editReportId').value;
  const summary = document.getElementById('editReportSummary').value.trim();
  const change_summary = document.getElementById('editReportChangeSummary').value.trim();

  try {
    const res = await fetch(`/api/reports/${reportId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary, change_summary })
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Report updated and new version created!', 'success');
      const modalEl = document.getElementById('editReportModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadReports();
    } else {
      showToast(data.error || 'Failed to update report.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

async function openVersionHistory(reportId) {
  const modalEl = document.getElementById('versionHistoryModal');
  const listEl = document.getElementById('versionHistoryList');
  listEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  try {
    const res = await fetch(`/api/reports/${reportId}`);
    const data = await res.json();
    const versions = data.report.versions || [];

    if (versions.length === 0) {
      listEl.innerHTML = '<p class="text-muted text-center py-3">No previous revisions recorded.</p>';
      return;
    }

    listEl.innerHTML = versions.map(v => `
      <div class="p-3 mb-2 rounded border bg-white d-flex align-items-center justify-content-between">
        <div>
          <span class="badge bg-primary me-2">Version ${v.version_number}</span>
          <span class="fw-semibold text-dark">${v.change_summary}</span>
          <div class="text-muted small mt-1">Edited by <b>${v.modified_by_name}</b> on ${v.created_at}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    listEl.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

function promptAcknowledge(reportId) {
  document.getElementById('ackReportId').value = reportId;
  const modalEl = document.getElementById('acknowledgeModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleAcknowledge(e) {
  e.preventDefault();
  const reportId = document.getElementById('ackReportId').value;
  const comments = document.getElementById('ackComments').value.trim();

  try {
    const res = await fetch('/api/acknowledgements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_id: reportId, comments })
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Handover officially acknowledged and project transitioned!', 'success');
      const modalEl = document.getElementById('acknowledgeModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadReports();
    } else {
      showToast(data.error || 'Failed to record acknowledgement.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}
