import io

def test_ai_knowledge_extraction(auth_client, sample_project):
    doc_text = """CLOUD PLATFORM HANDOVER
Outgoing Architect: Sarah Jenkins
Incoming Architect: Alex Chen

1. Architectural Decisions
Decision: We decided to deploy RabbitMQ for internal queuing because offline simulation required no AWS billing overhead.
Decision: Selected PostgreSQL 16 with Citus extension for database sharding due to ACID requirements.

2. Deliverables and Action Items
• Task: Complete database replication latency stress test before payment gateway migration. Assigned to: Alex Chen. Due by: 2026-11-20. Status: In Progress.
• Task: Rotate staging database master encryption keys. Assigned to: Sarah Jenkins. Due by: 2026-11-15. Status: Completed.
• Task: Verify unowned background queue worker scripts. Assigned to: Unassigned. Status: Pending.

3. Operational Risks
• Risk: Redis session cache does not have automated failover configured in Frankfurt EU region.
• Risk: Critical background worker queue lacks secondary maintainer.

4. Dependencies
Database integration must be completed before payment gateway migration.
"""
    # 1. Upload document
    data = {
        'project_id': str(sample_project),
        'file': (io.BytesIO(doc_text.encode('utf-8')), 'handover_spec.txt')
    }
    upload_res = auth_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert upload_res.status_code == 201
    doc_id = upload_res.get_json()['document']['id']

    # 2. Run AI Knowledge Extraction
    analysis_res = auth_client.post(f'/api/analysis/{doc_id}')
    assert analysis_res.status_code == 200
    res_data = analysis_res.get_json()

    assert res_data['tasks_count'] >= 2
    assert res_data['decisions_count'] >= 2
    assert res_data['risks_count'] >= 1
    assert 'summary' in res_data

    # 3. Verify Tasks created in database
    tasks_res = auth_client.get(f'/api/tasks?project_id={sample_project}')
    assert tasks_res.status_code == 200
    tasks = tasks_res.get_json()['tasks']
    assert any('database replication latency' in t['description'].lower() for t in tasks)

    # 4. Verify Decisions created in database
    dec_res = auth_client.get(f'/api/decisions?project_id={sample_project}')
    assert dec_res.status_code == 200
    decisions = dec_res.get_json()['decisions']
    assert any('rabbitmq' in d['title'].lower() for d in decisions)

    # 5. Verify Evidence Linking
    first_dec = decisions[0]
    ev_res = auth_client.get(f"/api/evidence/entity/decision/{first_dec['id']}")
    assert ev_res.status_code == 200
    assert ev_res.get_json()['available'] is True
    assert ev_res.get_json()['evidence']['document_name'] == 'handover_spec.txt'

    # 6. Re-analysis should update without duplicating records
    re_analysis = auth_client.post(f'/api/analysis/{doc_id}')
    assert re_analysis.status_code == 200
    tasks_after = auth_client.get(f'/api/tasks?project_id={sample_project}').get_json()['tasks']
    assert len(tasks_after) == len(tasks)
