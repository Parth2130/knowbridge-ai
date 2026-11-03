import json

def test_register_user(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'Sarah Connor',
        'email': 'sarah@skynet.com',
        'organisation': 'Resistance Inc',
        'password': 'securepassword123',
        'confirm_password': 'securepassword123',
        'role': 'Project Manager'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['user']['email'] == 'sarah@skynet.com'
    assert 'password_hash' not in data['user']

def test_register_duplicate_email(client):
    payload = {
        'full_name': 'Sarah Connor',
        'email': 'sarah_dup@skynet.com',
        'organisation': 'Resistance Inc',
        'password': 'securepassword123',
        'confirm_password': 'securepassword123'
    }
    res1 = client.post('/api/auth/register', json=payload)
    assert res1.status_code == 201
    
    # Second attempt with same email
    res2 = client.post('/api/auth/register', json=payload)
    assert res2.status_code == 409
    assert 'already exists' in res2.get_json()['error']

def test_register_password_mismatch(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'Mismatch Test',
        'email': 'mismatch@test.com',
        'organisation': 'Org',
        'password': 'password123',
        'confirm_password': 'different_password'
    })
    assert res.status_code == 400
    assert 'do not match' in res.get_json()['error']

def test_login_success(client):
    # Register first
    client.post('/api/auth/register', json={
        'full_name': 'Login Tester',
        'email': 'login@test.com',
        'organisation': 'Login Corp',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    # Log in
    res = client.post('/api/auth/login', json={
        'email': 'login@test.com',
        'password': 'password123'
    })
    assert res.status_code == 200
    assert res.get_json()['user']['email'] == 'login@test.com'

def test_login_invalid_password(client):
    client.post('/api/auth/register', json={
        'full_name': 'Bad Password Tester',
        'email': 'badpass@test.com',
        'organisation': 'Org',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    res = client.post('/api/auth/login', json={
        'email': 'badpass@test.com',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401
    assert 'Invalid email address or password' in res.get_json()['error']

def test_unauthorized_access_protection(client):
    res = client.get('/api/projects')
    assert res.status_code == 401

    res_dash = client.get('/api/dashboard')
    assert res_dash.status_code == 401

def test_logout(auth_client):
    res = auth_client.post('/api/auth/logout')
    assert res.status_code == 200

    # Next call should be unauthorized
    res2 = auth_client.get('/api/projects')
    assert res2.status_code == 401
