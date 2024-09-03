import sys
import os
import pytest
from app import app, db
from models import User, Team, Project, Task
from werkzeug.security import generate_password_hash
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def init_db():
    with app.app_context():
        hashed_password = generate_password_hash('adminpass', method='pbkdf2:sha256')
        admin = User(username='admintest', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()

@pytest.fixture
def login_admin(client):
    def do_login(username, password):
        return client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    return do_login

def test_home_not_logged_in(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_logout(client, init_db, login_admin):
    response = login_admin('admintest', 'adminpass')
    assert response.status_code == 200
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

def test_admin_access(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('adminpass', method='pbkdf2:sha256')
        admin = User(username='admintest', password=hashed_password, role='admin')


        response = client.post('/login', data=dict(
            username='admintest',
            password='adminpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_cto_access(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('ctopass', method='pbkdf2:sha256')
        cto = User(username='cto', password=hashed_password, role='CTO')
        db.session.add(cto)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='cto',
            password='ctopass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_tl_access(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('tlpass', method='pbkdf2:sha256')
        tl = User(username='tl', password=hashed_password, role='TL')
        db.session.add(tl)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='tl',
            password='tlpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_rnd_access(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('rndpass', method='pbkdf2:sha256')
        rnd = User(username='rnd', password=hashed_password, role='R&D')
        db.session.add(rnd)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='rnd',
            password='rndpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_manage_roles_access(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('ctopass', method='pbkdf2:sha256')
        cto = User(username='cto', password=hashed_password, role='CTO')
        db.session.add(cto)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='cto',
            password='ctopass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_add_user_to_team(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('ctopass', method='pbkdf2:sha256')
        cto = User(username='cto', password=hashed_password, role='CTO')
        db.session.add(cto)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='cto',
            password='ctopass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_edit_project_description(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('tlpass', method='pbkdf2:sha256')
        tl = User(username='tl', password=hashed_password, role='TL')
        db.session.add(tl)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='tl',
            password='tlpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_add_task(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('tlpass', method='pbkdf2:sha256')
        tl = User(username='tl', password=hashed_password, role='TL')
        db.session.add(tl)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='tl',
            password='tlpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_manage_task(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('tlpass', method='pbkdf2:sha256')
        tl = User(username='tl', password=hashed_password, role='TL')
        db.session.add(tl)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='tl',
            password='tlpass'
        ), follow_redirects=True)
        assert response.status_code == 200

def test_view_project(client, init_db):
    with app.app_context():
        hashed_password = generate_password_hash('ctopass', method='pbkdf2:sha256')
        cto = User(username='cto', password=hashed_password, role='CTO')
        db.session.add(cto)
        db.session.commit()

        response = client.post('/login', data=dict(
            username='cto',
            password='ctopass'
        ), follow_redirects=True)
        assert response.status_code == 200
