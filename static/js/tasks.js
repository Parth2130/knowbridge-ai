// Task Management Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadTasks();

  const searchInput = document.getElementById('taskSearchInput');
  const statusFilter = document.getElementById('taskStatusFilter');
  const projectFilter = document.getElementById('taskProjectFilter');
  const priorityFilter = document.getElementById('taskPriorityFilter');
  const taskForm = document.getElementById('taskForm');

  if (searchInput) searchInput.addEventListener('input', () => loadTasks());
  if (statusFilter) statusFilter.addEventListener('change', () => loadTasks());
  if (projectFilter) projectFilter.addEventListener('change', () => loadTasks());
  if (priorityFilter) priorityFilter.addEventListener('change', () => loadTasks());

  if (taskForm) {
    taskForm.addEventListener('submit', handleTaskSubmit);
  }
});

async function loadTasks() {
  const container = document.getElementById('tasksListContainer');
  const overdueContainer = document.getElementById('overdueTasksContainer');
  if (!container) return;

  const search = document.getElementById('taskSearchInput')?.value || '';
  const status = document.getElementById('taskStatusFilter')?.value || '';
  const project_id = document.getElementById('taskProjectFilter')?.value || '';
  const priority = document.getElementById('taskPriorityFilter')?.value || '';

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (status) params.append('status', status);
  if (project_id) params.append('project_id', project_id);
  if (priority) params.append('priority', priority);

  try {
    const res = await fetch(`/api/tasks?${params.toString()}`);
    const data = await res.json();
    const tasks = data.tasks || [];
    const overdue = data.overdue_tasks || [];

    // Overdue tasks card alert
    if (overdueContainer) {
      if (overdue.length > 0) {
        overdueContainer.classList.remove('d-none');
        document.getElementById('overdueTasksList').innerHTML = overdue.map(t => `
          <div class="d-flex align-items-center justify-content-between p-2 mb-1 rounded bg-white border border-danger">
            <span class="text-danger fw-semibold small">${t.description}</span>
            <span class="badge bg-danger">Overdue: ${t.deadline}</span>
          </div>
        `).join('');
      } else {
        overdueContainer.classList.add('d-none');
      }
    }

    if (tasks.length === 0) {
      container.innerHTML = `
        <div class="empty-state py-5 bg-white rounded border">
          <div class="empty-state-icon">
            <i data-lucide="check-circle-2"></i>
          </div>
          <h4>No Tasks Found</h4>
          <p class="text-muted">No pending or completed tasks match your criteria.</p>
          <button class="btn-kb-primary" data-bs-toggle="modal" data-bs-target="#taskModal" onclick="resetTaskForm()">
            <i data-lucide="plus"></i> Add New Task
          </button>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = tasks.map(t => {
      let priorityBadge = 'bg-secondary';
      if (t.priority === 'High') priorityBadge = 'bg-danger';
      if (t.priority === 'Medium') priorityBadge = 'bg-warning text-dark';
      if (t.priority === 'Low') priorityBadge = 'bg-info text-dark';

      let isCompleted = t.status === 'Completed';

      return `
        <div class="p-3 mb-2 rounded border bg-white d-flex align-items-center justify-content-between flex-wrap gap-2">
          <div style="flex:1; min-width: 260px;">
            <div class="d-flex align-items-center gap-2 mb-1">
              <span class="badge ${priorityBadge}">${t.priority}</span>
              <span class="fw-bold ${isCompleted ? 'text-decoration-line-through text-muted' : 'text-dark'}">${t.description}</span>
              <span class="badge badge-ai" style="font-size:0.7rem;">${t.verification_status}</span>
            </div>
            <div class="text-muted small">
              Project: <b>${t.project_name || 'Project'}</b> • Owner: <b class="text-dark">${t.responsible_person}</b> • Due: <b>${t.deadline || 'N/A'}</b>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <select class="form-select form-select-sm" style="width:130px;" onchange="updateTaskStatus(${t.id}, this.value)">
              <option value="Pending" ${t.status === 'Pending' ? 'selected' : ''}>Pending</option>
              <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
              <option value="Completed" ${t.status === 'Completed' ? 'selected' : ''}>Completed</option>
              <option value="Blocked" ${t.status === 'Blocked' ? 'selected' : ''}>Blocked</option>
            </select>
            <button class="btn btn-sm btn-outline-secondary" title="View Source Evidence" onclick="viewEvidence('task', ${t.id})">
              <i data-lucide="file-search" style="width:14px;height:14px;"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary" title="Edit Task" onclick="editTask(${JSON.stringify(t).replace(/"/g, '&quot;')})">
              <i data-lucide="edit-2" style="width:14px;height:14px;"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" title="Delete Task" onclick="deleteTask(${t.id})">
              <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading tasks:', err);
    showToast('Failed to load tasks: ' + err.message, 'error');
  }
}

function resetTaskForm() {
  const form = document.getElementById('taskForm');
  if (form) form.reset();
  document.getElementById('taskId').value = '';
  document.getElementById('taskModalTitle').innerText = 'Add New Task';
}

function editTask(t) {
  document.getElementById('taskId').value = t.id;
  document.getElementById('taskProject').value = t.project_id;
  document.getElementById('taskDescription').value = t.description;
  document.getElementById('taskOwner').value = t.responsible_person || '';
  document.getElementById('taskDeadline').value = t.deadline || '';
  document.getElementById('taskPriority').value = t.priority;
  document.getElementById('taskStatus').value = t.status;
  document.getElementById('taskModalTitle').innerText = 'Edit Task Details';

  const modalEl = document.getElementById('taskModal');
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

async function handleTaskSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('taskId').value;
  const project_id = document.getElementById('taskProject').value;
  const description = document.getElementById('taskDescription').value.trim();
  const responsible_person = document.getElementById('taskOwner').value.trim();
  const deadline = document.getElementById('taskDeadline').value.trim();
  const priority = document.getElementById('taskPriority').value;
  const status = document.getElementById('taskStatus').value;

  const payload = { project_id, description, responsible_person, deadline, priority, status };
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/tasks/${id}` : '/api/tasks';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(id ? 'Task updated successfully.' : 'Task added successfully.', 'success');
      const modalEl = document.getElementById('taskModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      loadTasks();
    } else {
      showToast(data.error || 'Failed to save task.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}

async function updateTaskStatus(taskId, newStatus) {
  try {
    const res = await fetch(`/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();

    if (res.ok) {
      showToast(`Task marked as ${newStatus}.`, 'success');
      loadTasks();
    } else {
      showToast(data.error || 'Failed to update status.', 'error');
      loadTasks(); // Reset dropdown
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
    loadTasks();
  }
}

async function deleteTask(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Task deleted successfully.', 'success');
      loadTasks();
    } else {
      showToast(data.error || 'Failed to delete task.', 'error');
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  }
}
