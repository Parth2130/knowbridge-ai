def test_create_project(auth_client):
    res = auth_client.post('/api/projects', json={
        'name': 'Payments Microservices Handover',
        'description': 'Transition of payment services',
        'category': 'Engineering',
        'outgoing_member': 'Sarah Jenkins',
        'incoming_member': 'Alex Chen',
        'start_date': '2026-11-01',
        'deadline': '2026-12-01',
        'status': 'Active'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['project']['name'] == 'Payments Microservices Handover'
    assert data['project']['outgoing_member'] == 'Sarah Jenkins'

def test_list_and_filter_projects(auth_client, sample_project):
    res = auth_client.get('/api/projects')
    assert res.status_code == 200
    projects = res.get_json()['projects']
    assert len(projects) >= 1

    # Filter by category
    res_filtered = auth_client.get('/api/projects?category=Engineering')
    assert res_filtered.status_code == 200
    assert len(res_filtered.get_json()['projects']) >= 1

    # Search by keyword
    res_search = auth_client.get('/api/projects?search=Cloud')
    assert res_search.status_code == 200
    assert len(res_search.get_json()['projects']) >= 1

def test_update_project(auth_client, sample_project):
    res = auth_client.put(f'/api/projects/{sample_project}', json={
        'name': 'Updated Cloud Migration Title',
        'status': 'Completed'
    })
    assert res.status_code == 200
    assert res.get_json()['project']['name'] == 'Updated Cloud Migration Title'
    assert res.get_json()['project']['status'] == 'Completed'

def test_delete_project(auth_client, sample_project):
    res = auth_client.delete(f'/api/projects/{sample_project}')
    assert res.status_code == 200

    # Ensure deleted
    res_get = auth_client.get(f'/api/projects/{sample_project}')
    assert res_get.status_code == 404
