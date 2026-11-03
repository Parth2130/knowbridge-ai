// Project Management Module for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadProjects();

  const searchInput = document.getElementById('searchProjectInput');
  const categoryFilter = document.getElementById('filterCategory');
  const statusFilter = document.getElementById('filterStatus');
  const projectForm = document.getElementById('projectForm');

  if (searchInput) searchInput.addEventListener('input', () => loadProjects());
  if (categoryFilter) categoryFilter.addEventListener('change', () => loadProjects());
  if (statusFilter) statusFilter.addEventListener('change', () => loadProjects());

  if (projectForm) {
    projectForm.addEventListener('submit', handleProjectSubmit);
  }
});

async function loadProjects() {
  const container = document.getElementById('projectsListContainer');
  if (!container) return;

  const search = document.getElementById('searchProjectInput')?.value || '';
  const category = document.getElementById('filterCategory')?.value || '';
  const status = document.getElementById('filterStatus')?.value || '';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (category) params.append('category', category);
  if (status) params.append('status', status);

  try {
    const res = await fetch(`/api/projects?${params.toString()}`);
    const data = await res.json();
    const projects = data.projects || [];

    if (projects.length === 0) {
      container.innerHTML = `
        <div class="col-12">
          <div class="empty-state py-5 bg-white rounded border">
            <div class="empty-state-icon">
              <i data-lucide="folder-search"></i>
            </div>
            <h4>No Projects Found</h4>
            <p class="text-muted">No projects match your current filters or search terms.</p>
            <button class="btn-kb-primary" data-bs-toggle="modal" data-bs-target="#projectModal" onclick="resetProjectForm()">
              <i data-lucide="plus"></i> Create New Project
            </button>
          </div>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = projects.map(p => `
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="dashboard-card h-100 d-flex flex-column mb-0">
          <div class="dashboard-card-header pb-2">
            <span class="badge bg-light text-primary border">${p.category}</span>
            <span class="badge badge-status badge-${p.status.toLowerCase().replace(' ', '-')}">${p.status}</span>
          </div>
          <div class="dashboard-card-body flex-fill d-flex flex-column pt-3">
            <h5 class="fw-bold mb-2 text-dark">${p.name}</h5>
            <p class="text-muted small mb-3 flex-fill">${p.description || 'No description provided.'}</p>
            
            <div class="p-2 rounded mb-3" style="background:#F4F8FC;font-size:0.82rem;">
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted">Outgoing Lead:</span>
                <span class="fw-semibold text-dark">${p.outgoing_member}</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">Incoming Lead:</span>
                <span class="fw-semibold text-primary">${p.incoming_member}</span>
              </div>
            </div>

            <div class="mb-3">
              <div class="d-flex justify-content-between text-muted small mb-1">
                <span>Handover Progress</span>
                <span class="fw-bold text-dark">${p.progress}%</span>
              </div>
              <div class="progress" style="height: 6px;">
                <div class="progress-bar" style="width:${p.progress}%; background-color:#2475E8;"></div>
              </div>
            </div>

            <div class="d-flex justify-content-between text-muted small border-top pt-2 mt-auto">
              <span><i data-lucide="file-text" style="width:13px;"></i> ${p.document_count} Docs</span>
              <span><i data-lucide="check-square" style="width:13px;"></i> ${p.task_count} Tasks</span>
              <span><i data-lucide="calendar" style="width:13px;"></i> Due: ${p.deadline || 'N/A'}</span>
            </div>
          </div>
          <div class="p-3 border-top bg-light d-flex justify-content-between align-items-center">
            <div class="d-flex gap-1">
              <button class="btn btn-sm btn-outline-secondary" onclick="editProject(${JSON.stringify(p).replace(/"/g, '&quot;')})">
                <i data-lucide="edit-2" style="width:14px;height:14px;"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteProject(${p.id}, '${p.name}')">
                <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
              </button>
            </div>
            <a href="/analysis?project_id=${p.id}" class="btn-kb-secondary btn-sm">
              <i data-lucide="cpu" style="width:14px;height:14px;"></i> Analyze
            </a>
          </div>
        </div>
      </div>
    `).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading projects:', err);
    showToast('Failed to load projects: ' + err.message, 'error');
  }
}

function resetProjectForm() {
  const form = document.getElementById('projectForm');
  if (form) form.reset();
  document.getElementById('projectId').value = '';
  document.getElementById('projectModalTitle').innerText = 'Create New Project';
}

function editProject(p) {
  document.getElementById('projectId').value = p.id;
  document.getElementById('projectName').value = p.name;
  document.getElementById('projectDesc').value = p.description || '';
  document.getElementById('projectCategory').value = p.category;
  document.getElementById('projectOutgoing').value = p.outgoing_member;
  document.getElementById('projectIncoming').value = p.incoming_member;
  document.getElementById('projectStartDate').value = p.start_date || '';
  document.getElementById('projectDeadline').value = p.deadline || '';
  document.getElementById('projectStatus').value = p.status;
  document.getElementById('projectModalTitle').innerText = 'Edit Project Details';

  const modalEl = document.getElementById('projectModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleProjectSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('projectId').value;
  const name = document.getElementById('projectName').value.trim();
  const description = document.getElementById('projectDesc').value.trim();
  const category = document.getElementById('projectCategory').value;
  const outgoing_member = document.getElementById('projectOutgoing').value.trim();
  const incoming_member = document.getElementById('projectIncoming').value.trim();
  const start_date = document.getElementById('projectStartDate').value;
  const deadline = document.getElementById('projectDeadline').value;
  const status = document.getElementById('projectStatus').value;

  const payload = {
    name, description, category, outgoing_member, incoming_member,
    start_date, deadline, status
  };

  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/projects/${id}` : '/api/projects';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(id ? 'Project updated successfully.' : 'Project created successfully.', 'success');
      const modalEl = document.getElementById('projectModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadProjects();
    } else {
      showToast(data.error || 'Failed to save project.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

async function deleteProject(id, name) {
  if (!confirm(`Are you sure you want to delete project "${name}"?\nAll associated documents, tasks, and reports will also be removed.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Project deleted successfully.', 'success');
      loadProjects();
    } else {
      showToast(data.error || 'Failed to delete project.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}
