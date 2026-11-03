// Project Timeline Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  loadTimeline();

  const projectFilter = document.getElementById('timelineProjectFilter');
  if (projectFilter) {
    projectFilter.addEventListener('change', () => loadTimeline());
  }
});

async function loadTimeline() {
  const container = document.getElementById('timelineTrackContainer');
  if (!container) return;

  const project_id = document.getElementById('timelineProjectFilter')?.value || '';
  const params = new URLSearchParams();
  if (project_id) params.append('project_id', project_id);

  try {
    const res = await fetch(`/api/timeline?${params.toString()}`);
    const data = await res.json();
    const activities = data.activities || [];

    if (activities.length === 0) {
      container.innerHTML = `
        <div class="empty-state py-5 bg-white rounded border">
          <div class="empty-state-icon">
            <i data-lucide="calendar"></i>
          </div>
          <h4>No Timeline Events Recorded</h4>
          <p class="text-muted">Create projects, upload documentation, or run AI analyses to see events appear in the chronological timeline.</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    container.innerHTML = `
      <div class="timeline-track">
        ${activities.map(a => {
          let nodeClass = '';
          if (a.activity_type.includes('Completed') || a.activity_type.includes('Approved') || a.activity_type.includes('Acknowledged')) {
            nodeClass = 'success';
          } else if (a.activity_type.includes('Risk') || a.activity_type.includes('Updated')) {
            nodeClass = 'warning';
          }

          return `
            <div class="timeline-node ${nodeClass}">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="d-flex align-items-center justify-content-between mb-1">
                  <span class="badge bg-light text-primary border">${a.project_name || 'Project Activity'}</span>
                  <span class="text-muted small">${a.created_at}</span>
                </div>
                <h6 class="fw-bold text-dark mb-1">${a.activity_type}</h6>
                <p class="text-muted small mb-0">${a.description}</p>
                <div class="text-muted mt-2" style="font-size:0.75rem;">
                  <i data-lucide="user" style="width:12px;"></i> Initiated by <b>${a.user_name || 'System Engine'}</b>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Error loading timeline:', err);
    showToast('Failed to load timeline: ' + err.message, 'error');
  }
}
