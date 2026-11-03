// AI Knowledge Extraction Controller for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const docIdParam = urlParams.get('doc_id');
  const projIdParam = urlParams.get('project_id');

  const projectSelect = document.getElementById('analysisProjectSelect');
  const docSelect = document.getElementById('analysisDocSelect');
  const analyzeDocBtn = document.getElementById('runDocAnalysisBtn');
  const analyzeBatchBtn = document.getElementById('runBatchAnalysisBtn');

  if (projectSelect) {
    if (projIdParam) projectSelect.value = projIdParam;
    projectSelect.addEventListener('change', () => {
      loadProjectDocumentsForSelect(projectSelect.value);
      loadExistingProjectAnalysis(projectSelect.value);
    });

    // Initial load
    if (projectSelect.value) {
      loadProjectDocumentsForSelect(projectSelect.value, docIdParam);
      loadExistingProjectAnalysis(projectSelect.value);
    }
  }

  if (analyzeDocBtn) {
    analyzeDocBtn.addEventListener('click', () => {
      const docId = docSelect ? docSelect.value : null;
      if (!docId) {
        showToast('Please select a document to analyze.', 'warning');
        return;
      }
      runDocumentAnalysis(docId);
    });
  }

  if (analyzeBatchBtn) {
    analyzeBatchBtn.addEventListener('click', () => {
      const projId = projectSelect ? projectSelect.value : null;
      if (!projId) {
        showToast('Please select a project to batch analyze.', 'warning');
        return;
      }
      runBatchAnalysis(projId);
    });
  }
});

async function loadProjectDocumentsForSelect(projectId, preselectedDocId = null) {
  const docSelect = document.getElementById('analysisDocSelect');
  if (!docSelect) return;

  if (!projectId) {
    docSelect.innerHTML = '<option value="">-- Select Project First --</option>';
    return;
  }

  try {
    const res = await fetch(`/api/documents?project_id=${projectId}`);
    const data = await res.json();
    const docs = data.documents || [];

    if (docs.length === 0) {
      docSelect.innerHTML = '<option value="">No documents in this project</option>';
      return;
    }

    docSelect.innerHTML = docs.map(d => `
      <option value="${d.id}" ${preselectedDocId && preselectedDocId == d.id ? 'selected' : ''}>
        ${d.original_filename} (${d.file_type} • ${d.processing_status})
      </option>
    `).join('');

    // If a document was preselected in URL query, run analysis automatically or load preview
    if (preselectedDocId) {
      runDocumentAnalysis(preselectedDocId);
    }
  } catch (err) {
    console.error('Failed to load project docs:', err);
  }
}

async function runDocumentAnalysis(docId) {
  const statusEl = document.getElementById('analysisStatusIndicator');
  const resultsEl = document.getElementById('analysisResultsContainer');
  const analyzeBtn = document.getElementById('runDocAnalysisBtn');

  if (statusEl) {
    statusEl.classList.remove('d-none');
    statusEl.innerHTML = `
      <div class="alert alert-info d-flex align-items-center gap-3">
        <div class="spinner-border text-primary" role="status"></div>
        <div>
          <div class="fw-bold">Running KnowBridge AI Knowledge Extraction Engine...</div>
          <div class="small">Extracting decisions, mapping deliverables, analyzing dependencies, and auditing operational risks.</div>
        </div>
      </div>
    `;
  }
  if (analyzeBtn) analyzeBtn.disabled = true;

  try {
    const res = await fetch(`/api/analysis/${docId}`, { method: 'POST' });
    const data = await res.json();

    if (res.ok) {
      showToast('Knowledge extraction completed successfully!', 'success');
      if (statusEl) {
        statusEl.innerHTML = `
          <div class="alert alert-success d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center gap-2">
              <i data-lucide="check-circle" class="text-success"></i>
              <div>
                <span class="fw-bold">Analysis Succeeded</span> — ${data.tasks_count} tasks, ${data.decisions_count} decisions, ${data.risks_count} risks identified.
                <div class="small text-muted">Engine: ${data.analysis.engine_mode}</div>
              </div>
            </div>
            <a href="/reports" class="btn-kb-primary btn-sm">Generate Handover Report →</a>
          </div>
        `;
      }
      renderAnalysisResults(data.analysis);
    } else {
      showToast(data.error || 'AI Analysis failed.', 'error');
      if (statusEl) {
        statusEl.innerHTML = `<div class="alert alert-danger">${data.error || 'Failed to extract knowledge from document.'}</div>`;
      }
    }
  } catch (err) {
    showToast('Analysis error: ' + err.message, 'error');
    if (statusEl) statusEl.innerHTML = `<div class="alert alert-danger">Network error: ${err.message}</div>`;
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (window.lucide) window.lucide.createIcons();
  }
}

async function runBatchAnalysis(projectId) {
  const statusEl = document.getElementById('analysisStatusIndicator');
  const analyzeBtn = document.getElementById('runBatchAnalysisBtn');

  if (statusEl) {
    statusEl.classList.remove('d-none');
    statusEl.innerHTML = `
      <div class="alert alert-info d-flex align-items-center gap-3">
        <div class="spinner-border text-primary" role="status"></div>
        <div>
          <div class="fw-bold">Running Batch AI Project Analysis...</div>
          <div class="small">Aggregating cross-document knowledge, validating cross-team dependencies, and structuring full project handover.</div>
        </div>
      </div>
    `;
  }
  if (analyzeBtn) analyzeBtn.disabled = true;

  try {
    const res = await fetch(`/api/analysis/project/${projectId}`, { method: 'POST' });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, 'success');
      if (statusEl) {
        statusEl.innerHTML = `
          <div class="alert alert-success d-flex align-items-center justify-content-between">
            <div><i data-lucide="check-circle" class="text-success me-2"></i><b>Batch Analysis Complete!</b> All documents synthesized.</div>
            <a href="/reports" class="btn-kb-primary btn-sm">Generate Handover Report →</a>
          </div>
        `;
      }
      renderAnalysisResults(data.analysis);
    } else {
      showToast(data.error || 'Batch analysis failed.', 'error');
    }
  } catch (err) {
    showToast('Batch analysis error: ' + err.message, 'error');
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (window.lucide) window.lucide.createIcons();
  }
}

async function loadExistingProjectAnalysis(projectId) {
  if (!projectId) return;
  try {
    const res = await fetch(`/api/analysis/${projectId}`);
    if (res.ok) {
      const data = await res.json();
      if (data.tasks && data.tasks.length > 0) {
        renderAnalysisResults({
          engine_mode: 'Database Persisted AI Knowledge Base',
          executive_summary: `Live aggregated knowledge repository for project "${data.project.name}".`,
          key_highlights: [
            `${data.tasks.length} total tasks identified across project files.`,
            `${data.decisions.length} architectural and strategic decisions registered.`,
            `${data.risks.length} operational or security risks actively tracked.`
          ],
          handover_readiness: data.project.status === 'Completed' ? 'High - Completed' : 'Under Active Handover',
          decisions: data.decisions,
          tasks: data.tasks,
          responsibilities: data.responsibilities,
          deadlines: data.deadlines,
          risks: data.risks,
          dependencies: data.dependencies,
          missing_information: data.missing_information
        });
      }
    }
  } catch (err) {
    console.error('Failed to load project analysis:', err);
  }
}

function renderAnalysisResults(analysis) {
  const container = document.getElementById('analysisResultsContainer');
  if (!container) return;

  container.classList.remove('d-none');

  // Executive Summary Card
  document.getElementById('analysisExecSummary').innerText = analysis.executive_summary || 'No summary generated.';
  document.getElementById('analysisReadinessBadge').innerText = analysis.handover_readiness || 'Standard';

  // Key Highlights
  const highlightsList = document.getElementById('analysisHighlightsList');
  if (highlightsList) {
    const hl = analysis.key_highlights || [];
    highlightsList.innerHTML = hl.length > 0 ? hl.map(h => `<li class="mb-1 text-dark">${h}</li>`).join('') : '<li class="text-muted">No explicit highlights.</li>';
  }

  // 1. Decisions Card
  const decisionsContainer = document.getElementById('analysisDecisionsContainer');
  if (decisionsContainer) {
    const decs = analysis.decisions || [];
    if (decs.length === 0) {
      decisionsContainer.innerHTML = `<p class="text-muted small">No decisions identified in analyzed content.</p>`;
    } else {
      decisionsContainer.innerHTML = decs.map((d, idx) => `
        <div class="p-3 mb-2 rounded border bg-white">
          <div class="d-flex align-items-center justify-content-between mb-1">
            <span class="fw-bold text-dark"><i data-lucide="git-commit" class="text-primary me-1" style="width:16px;"></i> ${d.title}</span>
            <span class="badge badge-status badge-approved">${d.status || 'Approved'}</span>
          </div>
          <div class="text-muted small mb-2">${d.description || d.reason || ''}</div>
          <div class="d-flex align-items-center justify-content-between">
            <span class="text-muted" style="font-size:0.75rem;"><i data-lucide="calendar" style="width:12px;"></i> ${d.decision_date || 'Recorded'}</span>
            <button class="btn btn-sm btn-kb-outline py-0 px-2" style="font-size:0.75rem;" onclick="viewEvidence('decision', ${d.id || idx})">
              <i data-lucide="file-search" style="width:12px;"></i> View Source Evidence
            </button>
          </div>
        </div>
      `).join('');
    }
  }

  // 2. Tasks Card
  const tasksContainer = document.getElementById('analysisTasksContainer');
  if (tasksContainer) {
    const tasks = analysis.tasks || [];
    if (tasks.length === 0) {
      tasksContainer.innerHTML = `<p class="text-muted small">No tasks identified in analyzed content.</p>`;
    } else {
      tasksContainer.innerHTML = tasks.map((t, idx) => `
        <div class="p-3 mb-2 rounded border bg-white">
          <div class="d-flex align-items-center justify-content-between mb-1">
            <span class="fw-semibold text-dark">${t.description}</span>
            <span class="badge badge-status badge-${(t.status || 'pending').toLowerCase().replace(' ', '-')}">${t.status || 'Pending'}</span>
          </div>
          <div class="d-flex align-items-center justify-content-between text-muted small mt-2">
            <span>Owner: <b class="text-dark">${t.responsible_person || 'Unassigned'}</b> • Due: <b>${t.deadline || 'N/A'}</b></span>
            <button class="btn btn-sm btn-kb-outline py-0 px-2" style="font-size:0.75rem;" onclick="viewEvidence('task', ${t.id || idx})">
              <i data-lucide="file-search" style="width:12px;"></i> Evidence
            </button>
          </div>
        </div>
      `).join('');
    }
  }

  // 3. Risks Card
  const risksContainer = document.getElementById('analysisRisksContainer');
  if (risksContainer) {
    const risks = analysis.risks || [];
    if (risks.length === 0) {
      risksContainer.innerHTML = `<p class="text-muted small">No project risks detected.</p>`;
    } else {
      risksContainer.innerHTML = risks.map((r, idx) => `
        <div class="risk-card ${(r.severity || 'medium').toLowerCase()} p-3 mb-2">
          <div class="d-flex align-items-center justify-content-between mb-1">
            <span class="fw-bold text-dark"><i data-lucide="alert-triangle" class="text-danger me-1" style="width:14px;"></i> ${r.description}</span>
            <span class="badge badge-status badge-high">${r.severity || 'Medium'}</span>
          </div>
          <div class="text-muted small mb-1">Category: <b>${r.category || 'Technical'}</b></div>
          <div class="small text-secondary"><b>Recommended Action:</b> ${r.suggested_action || 'Review during handover.'}</div>
        </div>
      `).join('');
    }
  }

  // 4. Dependencies Card
  const depsContainer = document.getElementById('analysisDepsContainer');
  if (depsContainer) {
    const deps = analysis.dependencies || [];
    if (deps.length === 0) {
      depsContainer.innerHTML = `<p class="text-muted small">No task dependencies or blockers found.</p>`;
    } else {
      depsContainer.innerHTML = deps.map(dp => `
        <div class="p-3 mb-2 rounded border bg-light">
          <div class="d-flex align-items-center gap-2 mb-1">
            <span class="badge bg-danger">BLOCKER</span>
            <span class="fw-semibold text-dark">${dp.description || `${dp.prerequisite} must precede ${dp.dependent}`}</span>
          </div>
          <div class="text-muted small mt-1">Prerequisite required before dependent task can progress.</div>
        </div>
      `).join('');
    }
  }

  // 5. Missing Information
  const missingContainer = document.getElementById('analysisMissingContainer');
  if (missingContainer) {
    const missing = analysis.missing_information || [];
    if (missing.length === 0) {
      missingContainer.innerHTML = `<p class="text-success small mb-0"><i data-lucide="check" class="me-1"></i> Documentation is thorough and complete.</p>`;
    } else {
      missingContainer.innerHTML = missing.map(m => `
        <div class="d-flex align-items-center gap-2 p-2 mb-1 rounded" style="background:#FFFBEB;border:1px solid #FDE68A;font-size:0.85rem;color:#92400E;">
          <i data-lucide="help-circle" style="width:15px;flex-shrink:0;"></i>
          <span>${m}</span>
        </div>
      `).join('');
    }
  }

  if (window.lucide) window.lucide.createIcons();
}
