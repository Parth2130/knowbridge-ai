def test_report_generation_and_pdf_download(auth_client, sample_project):
    # Add a task and a decision first
    auth_client.post('/api/tasks', json={
        'project_id': sample_project,
        'description': 'Final cluster security audit',
        'responsible_person': 'Alex Chen',
        'status': 'In Progress'
    })
    auth_client.post('/api/decisions', json={
        'project_id': sample_project,
        'title': 'Deploy with ArgoCD',
        'description': 'GitOps continuous deployment'
    })

    # 1. Generate Report
    gen_res = auth_client.post('/api/reports', json={
        'project_id': sample_project,
        'title': 'Official Handover Report — Test Cloud'
    })
    assert gen_res.status_code == 201
    rep = gen_res.get_json()['report']
    rep_id = rep['id']
    assert rep['current_version'] == 1
    assert '1_project_title' in rep['content']
    assert '16_approval_status' in rep['content']

    # 2. Update Report -> Should increment version to 2
    update_res = auth_client.put(f'/api/reports/{rep_id}', json={
        'summary': 'Updated executive summary for handover.',
        'change_summary': 'Clarified cluster cutover instructions.'
    })
    assert update_res.status_code == 200
    assert update_res.get_json()['report']['current_version'] == 2

    # 3. Download PDF (ReportLab)
    dl_res = auth_client.get(f'/api/reports/{rep_id}/download')
    assert dl_res.status_code == 200
    assert dl_res.content_type == 'application/pdf'
    assert dl_res.data.startswith(b'%PDF-')  # Valid PDF header

def test_human_approval_workflow(auth_client, sample_project):
    # Create AI-generated task
    task_res = auth_client.post('/api/tasks', json={
        'project_id': sample_project,
        'description': 'Unverified AI extracted task',
        'status': 'Pending'
    })
    task_id = task_res.get_json()['task']['id']

    # Approve item
    app_res = auth_client.post(f'/api/approvals/{task_id}', json={
        'entity_type': 'task',
        'action': 'Approve',
        'comments': 'Verified against system specifications.'
    })
    assert app_res.status_code == 200
    assert app_res.get_json()['approval']['action'] == 'Approve'

def test_acknowledgement_workflow(auth_client, sample_project):
    # Generate report
    gen_res = auth_client.post('/api/reports', json={'project_id': sample_project})
    rep_id = gen_res.get_json()['report']['id']

    # Submit acknowledgement
    ack_res = auth_client.post('/api/acknowledgements', json={
        'report_id': rep_id,
        'comments': 'Formally acknowledged and accepted by incoming staff.'
    })
    assert ack_res.status_code == 200
    data = ack_res.get_json()
    assert data['acknowledgement']['status'] == 'Acknowledged'
