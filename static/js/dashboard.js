// Main Dashboard Controller for KnowBridge AI

let taskChartInstance = null;
let docChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();

  // Project search filter
  const searchInput = document.getElementById('projectSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      const projectItems = document.querySelectorAll('.project-progress-item');
      projectItems.forEach(item => {
        const text = item.innerText.toLowerCase();
        item.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
});

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard');
    if (!res.ok) {
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      throw new Error('Failed to load dashboard data');
    }
    const data = await res.json();

    // 1. Update metric cards
    document.getElementById('metricProjects').innerText = data.metrics.total_projects || 0;
    document.getElementById('metricDocs').innerText = data.metrics.documents_analysed || 0;
    document.getElementById('metricPendingTasks').innerText = data.metrics.pending_tasks || 0;
    document.getElementById('metricCompletedTasks').innerText = data.metrics.completed_tasks || 0;
    document.getElementById('metricReports').innerText = data.metrics.handover_reports || 0;
    document.getElementById('metricApprovals').innerText = data.metrics.pending_approvals || 0;

    // 2. Render Project Progress
    renderProjectProgress(data.project_progress || []);

    // 3. Render Recent Activities
    renderRecentActivities(data.recent_activities || []);

    // 4. Render Latest Handover Report
    renderLatestReport(data.latest_report);

    // 5. Render Top Pending Tasks
    renderPendingTasks(data.pending_tasks_list || []);

    // 6. Render Charts (Chart.js)
    renderCharts(data.charts);

    if (window.lucide) {
      window.lucide.createIcons();
    }
  } catch (err) {
    console.error('Error loading dashboard:', err);
    showToast('Failed to load dashboard metrics: ' + err.message, 'error');
  }
}

function renderProjectProgress(projects) {
  const container = document.getElementById('projectProgressContainer');
  if (!container) return;

  if (projects.length === 0) {
    container.innerHTML = `
      <div class="empty-state py-3">
        <i data-lucide="folder-plus" class="text-muted" style="width:36px;height:36px;"></i>
        <h5 class="mt-2 text-dark">No Active Projects</h5>
        <p class="text-muted small">Create your first knowledge handover project to get started.</p>
        <a href="/projects" class="btn-kb-primary btn-sm"><i data-lucide="plus"></i> Create Project</a>
      </div>
    `;
    return;
  }

  container.innerHTML = projects.map(p => `
    <div class="project-progress-item p-3 mb-2 rounded" style="background:#F8FBFE;border:1px solid #DFE9F2;">
      <div class="d-flex align-items-center justify-content-between mb-1">
        <span class="fw-bold text-dark">${p.name}</span>
        <span class="badge badge-status badge-${p.status.toLowerCase().replace(' ', '-')}">${p.status}</span>
      </div>
      <div class="d-flex align-items-center justify-content-between text-muted small mb-2">
        <span>Handover: <b>${p.outgoing_member}</b> → <b>${p.incoming_member}</b></span>
        <span>${p.completed_task_count}/${p.task_count} Tasks (${p.progress}%)</span>
      </div>
      <div class="progress" style="height: 6px; background:#DFE9F2;">
        <div class="progress-bar bg-primary" role="progressbar" style="width: ${p.progress}%; background-color:#2475E8 !important;"></div>
      </div>
      <div class="d-flex justify-content-between align-items-center mt-2 small">
        <span class="text-muted"><i data-lucide="file" style="width:13px;"></i> ${p.document_count} Documents</span>
        <a href="/analysis?project_id=${p.id}" class="text-primary fw-semibold">View AI Handover →</a>
      </div>
    </div>
  `).join('');
}

function renderRecentActivities(activities) {
  const container = document.getElementById('recentActivitiesContainer');
  if (!container) return;

  if (activities.length === 0) {
    container.innerHTML = `<p class="text-muted small text-center py-3">No activity recorded yet.</p>`;
    return;
  }

  container.innerHTML = `
    <div class="timeline-track">
      ${activities.map(a => `
        <div class="timeline-node">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <div class="timeline-time">${a.created_at || 'Just now'} • <b>${a.user_name || 'System'}</b></div>
            <div class="timeline-title">${a.activity_type}</div>
            <div class="text-muted small mt-1">${a.description}</div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderLatestReport(report) {
  const container = document.getElementById('latestReportContainer');
  if (!container) return;

  if (!report) {
    container.innerHTML = `
      <div class="empty-state py-4">
        <i data-lucide="file-text" class="text-muted" style="width:36px;height:36px;"></i>
        <h5 class="mt-2 text-dark">No Reports Generated Yet</h5>
        <p class="text-muted small">Analyze documents and generate your project handover report.</p>
        <a href="/reports" class="btn-kb-secondary btn-sm"><i data-lucide="zap"></i> Generate Report</a>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="p-3 rounded" style="background:#FFFFFF;border:1px solid #DFE9F2;">
      <div class="d-flex align-items-center justify-content-between mb-2">
        <h5 class="fw-bold mb-0 text-dark">${report.title}</h5>
        <span class="badge badge-status badge-approved">v${report.current_version} (${report.status})</span>
      </div>
      <p class="text-muted small mb-3">${report.summary || 'Comprehensive transition report including architecture, deliverables, and operational guidelines.'}</p>
      <div class="d-flex align-items-center gap-2 mb-3">
        <span class="evidence-meta-tag"><i data-lucide="user" style="width:13px;"></i> Outgoing: ${report.outgoing_member}</span>
        <span class="evidence-meta-tag"><i data-lucide="user-check" style="width:13px;"></i> Incoming: ${report.incoming_member}</span>
      </div>
      <div class="d-flex gap-2">
        <a href="/api/reports/${report.id}/download" class="btn-kb-primary btn-sm flex-fill justify-content-center">
          <i data-lucide="download"></i> Download PDF
        </a>
        <a href="/reports?view=${report.id}" class="btn-kb-outline btn-sm">Preview</a>
      </div>
    </div>
  `;
}

function renderPendingTasks(tasks) {
  const container = document.getElementById('dashboardPendingTasksContainer');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = `<p class="text-muted small text-center py-3">All project tasks completed! 🎉</p>`;
    return;
  }

  container.innerHTML = tasks.map(t => `
    <div class="d-flex align-items-center justify-content-between p-2 mb-2 rounded" style="background:#F8FBFE;border:1px solid #DFE9F2;">
      <div style="flex:1;" class="me-2">
        <div class="fw-semibold text-dark small">${t.description}</div>
        <div class="text-muted" style="font-size:0.75rem;">Owner: <b>${t.responsible_person}</b> • Due: ${t.deadline || 'N/A'}</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <span class="badge badge-status badge-${t.status.toLowerCase().replace(' ', '-')}">${t.status}</span>
        <button class="btn btn-sm btn-outline-secondary p-1" title="View Evidence" onclick="viewEvidence('task', ${t.id})">
          <i data-lucide="file-search" style="width:14px;height:14px;"></i>
        </button>
      </div>
    </div>
  `).join('');
}

function renderCharts(charts) {
  if (!charts) return;

  // Task Status Doughnut Chart
  const taskCtx = document.getElementById('taskStatusChart');
  if (taskCtx && window.Chart) {
    if (taskChartInstance) taskChartInstance.destroy();

    const tData = charts.tasks || {};
    taskChartInstance = new Chart(taskCtx, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'In Progress', 'Pending', 'Blocked'],
        datasets: [{
          data: [
            tData['Completed'] || 0,
            tData['In Progress'] || 0,
            tData['Pending'] || 0,
            tData['Blocked'] || 0
          ],
          backgroundColor: ['#25A66A', '#2475E8', '#F59E0B', '#EF4444'],
          borderWidth: 2,
          borderColor: '#FFFFFF'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
        },
        cutout: '70%'
      }
    });
  }

  // Document Analysis Status Chart
  const docCtx = document.getElementById('docStatusChart');
  if (docCtx && window.Chart) {
    if (docChartInstance) docChartInstance.destroy();

    const dData = charts.documents || {};
    docChartInstance = new Chart(docCtx, {
      type: 'bar',
      data: {
        labels: ['Analysed', 'Extracted', 'Uploaded'],
        datasets: [{
          label: 'Documents',
          data: [dData['Analysed'] || 0, dData['Extracted'] || 0, dData['Uploaded'] || 0],
          backgroundColor: ['#2475E8', '#20A99A', '#DCEBFA'],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}
