def test_task_crud_and_dependency_blocking(auth_client, sample_project):
    # 1. Create task A (Prerequisite)
    res_a = auth_client.post('/api/tasks', json={
        'project_id': sample_project,
        'description': 'Database schema migration',
        'responsible_person': 'Alex Chen',
        'status': 'Pending'
    })
    assert res_a.status_code == 201
    task_a_id = res_a.get_json()['task']['id']

    # 2. Create task B (Dependent)
    res_b = auth_client.post('/api/tasks', json={
        'project_id': sample_project,
        'description': 'API Gateway route cutover',
        'responsible_person': 'Sarah Jenkins',
        'status': 'Pending'
    })
    assert res_b.status_code == 201
    task_b_id = res_b.get_json()['task']['id']

    # 3. Create blocking dependency: A blocks B
    dep_res = auth_client.post('/api/risks/dependencies', json={
        'project_id': sample_project,
        'prerequisite_task_id': task_a_id,
        'dependent_task_id': task_b_id,
        'description': 'Schema migration required before route cutover.',
        'is_blocking': True
    })
    assert dep_res.status_code == 201

    # 4. Attempt to complete Task B while Task A is still Pending -> should be blocked!
    fail_res = auth_client.put(f'/api/tasks/{task_b_id}', json={'status': 'Completed'})
    assert fail_res.status_code == 400
    assert 'Blocked by prerequisite task' in fail_res.get_json()['error']

    # 5. Complete Task A first
    ok_a = auth_client.put(f'/api/tasks/{task_a_id}', json={'status': 'Completed'})
    assert ok_a.status_code == 200

    # 6. Now Task B can be completed
    ok_b = auth_client.put(f'/api/tasks/{task_b_id}', json={'status': 'Completed'})
    assert ok_b.status_code == 200
    assert ok_b.get_json()['task']['status'] == 'Completed'

def test_decision_crud(auth_client, sample_project):
    res = auth_client.post('/api/decisions', json={
        'project_id': sample_project,
        'title': 'Adopted PostgreSQL Citus Sharding',
        'description': 'Horizontally sharded database across multi-AZ clusters.',
        'reason': 'Handles 50k write transactions per second.',
        'decision_date': '2026-11-02',
        'status': 'Approved'
    })
    assert res.status_code == 201
    dec_id = res.get_json()['decision']['id']

    # Edit
    edit_res = auth_client.put(f'/api/decisions/{dec_id}', json={
        'title': 'Adopted PostgreSQL Citus Sharding (Confirmed)'
    })
    assert edit_res.status_code == 200
    assert 'Confirmed' in edit_res.get_json()['decision']['title']

    # Delete
    del_res = auth_client.delete(f'/api/decisions/{dec_id}')
    assert del_res.status_code == 200
