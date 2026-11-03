// Knowledge Base Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadKnowledge();

  const searchInput = document.getElementById('kbSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      const cards = document.querySelectorAll('.kb-item-card');
      cards.forEach(c => {
        c.style.display = c.innerText.toLowerCase().includes(term) ? '' : 'none';
      });
    });
  }
});

async function loadKnowledge() {
  const container = document.getElementById('knowledgeCardsContainer');
  if (!container) return;

  try {
    const [decRes, taskRes, docRes] = await Promise.all([
      fetch('/api/decisions'),
      fetch('/api/tasks'),
      fetch('/api/documents')
    ]);

    const decData = await decRes.json();
    const taskData = await taskRes.json();
    const docData = await docRes.json();

    const decisions = decData.decisions || [];
    const tasks = taskData.tasks || [];
    const docs = docData.documents || [];

    if (decisions.length === 0 && tasks.length === 0) {
      container.innerHTML = `
        <div class="col-12">
          <div class="empty-state py-5 bg-white rounded border">
            <div class="empty-state-icon">
              <i data-lucide="book-open"></i>
            </div>
            <h4>Knowledge Base Is Empty</h4>
            <p class="text-muted">Analyze project documents to extract and index technical knowledge automatically.</p>
          </div>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = `
      <div class="col-12 mb-4">
        <div class="p-3 bg-white rounded border d-flex gap-4">
          <div><span class="text-muted small">Total Knowledge Points:</span> <b class="text-primary">${decisions.length + tasks.length}</b></div>
          <div><span class="text-muted small">Document Sources:</span> <b class="text-dark">${docs.length}</b></div>
          <div><span class="text-muted small">Verified Decisions:</span> <b class="text-success">${decisions.filter(d => d.status === 'Approved').length}</b></div>
        </div>
      </div>
      
      <!-- Architectural Decisions Section -->
      <div class="col-12 mb-3">
        <h5 class="fw-bold text-dark"><i data-lucide="git-commit" class="text-primary me-2"></i>Architectural & Technical Knowledge (${decisions.length})</h5>
      </div>
      ${decisions.map(d => `
        <div class="col-md-6 mb-3 kb-item-card">
          <div class="p-3 rounded border bg-white h-100 d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="badge bg-light text-primary border">${d.project_name || 'Project'}</span>
              <span class="badge badge-status badge-approved">${d.status}</span>
            </div>
            <h6 class="fw-bold text-dark mb-1">${d.title}</h6>
            <p class="text-muted small mb-2 flex-fill">${d.description}</p>
            ${d.reason ? `<div class="p-2 rounded bg-light border-start border-primary border-3 small mb-2"><b>Why:</b> ${d.reason}</div>` : ''}
            <div class="d-flex justify-content-between align-items-center border-top pt-2 mt-auto small">
              <span class="text-muted"><i data-lucide="calendar" style="width:12px;"></i> ${d.decision_date || 'N/A'}</span>
              <button class="btn btn-sm btn-kb-outline py-0 px-2" onclick="viewEvidence('decision', ${d.id})">
                <i data-lucide="file-search" style="width:12px;"></i> Evidence
              </button>
            </div>
          </div>
        </div>
      `).join('')}

      <!-- Operational Knowledge Deliverables -->
      <div class="col-12 mt-3 mb-3">
        <h5 class="fw-bold text-dark"><i data-lucide="check-square" class="text-success me-2"></i>Operational Procedures & Deliverables (${tasks.length})</h5>
      </div>
      ${tasks.map(t => `
        <div class="col-md-6 mb-3 kb-item-card">
          <div class="p-3 rounded border bg-white h-100 d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="badge bg-light text-secondary border">${t.project_name || 'Project'}</span>
              <span class="badge badge-status badge-${t.status.toLowerCase().replace(' ', '-')}">${t.status}</span>
            </div>
            <h6 class="fw-bold text-dark mb-1">${t.description}</h6>
            <div class="text-muted small mt-auto pt-2 border-top d-flex justify-content-between">
              <span>Owner: <b>${t.responsible_person}</b></span>
              <span>Deadline: <b>${t.deadline || 'N/A'}</b></span>
            </div>
          </div>
        </div>
      `).join('')}
    `;

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Failed to load knowledge:', err);
  }
}
