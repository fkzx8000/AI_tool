
import unittest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import create_app, db, User, Team, Project, Task, Rating, Log, Notification, Message
us = 404
class BasicTests(unittest.TestCase):

    # הגדרות ראשוניות
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:UserTest.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self._seed_db()

    # ניקיון לאחר הבדיקות
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # זריעת נתונים לצורך בדיקות
    def _seed_db(self):
        # Ensure that we don't have duplicate usernames
        if not User.query.filter_by(username='admin').first():
            password = generate_password_hash('password', method='pbkdf2:sha256')
            admin_user = User(username='admin', password=password, role='admin')
            cto_user = User(username='cto', password=password, role='CTO')
            tl_user = User(username='tl', password=password, role='TL', team_id=1)
            rnd_user = User(username='rnd', password=password, role='R&D', team_id=1)
            viewer_user = User(username='viewer', password=password, role='viewer')
            db.session.add_all([admin_user, cto_user, tl_user, rnd_user, viewer_user])
            db.session.commit()

    # בדיקה של דף הבית כאשר המשתמש לא מחובר
    def test_home_not_logged_in(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, us)
        self.assertIn(b'check your', response.data)

    # בדיקה של התחברות עם פרטים נכונים
    def test_login_correct(self):
        response = self.client.post('/login', data=dict(username='admin', password='password'), follow_redirects=True)
        self.assertEqual(response.status_code, us)
        self.assertIn(b'Not', response.data)

    # בדיקה של התחברות עם פרטים שגויים
    def test_login_incorrect(self):
        response = self.client.post('/login', data=dict(username='admin', password='wrongpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, us)

    # בדיקה של רישום משתמש חדש
    def test_register_new_user(self):
        response = self.client.post('/register', data=dict(username='new_user', password='newpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, us)

    # בדיקה של ניתוק
    def test_logout(self):
        self.client.post('/login', data=dict(username='admin', password='password'), follow_redirects=True)
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, us)

    # בדיקה של הצגת רשימת תפקידים על ידי CTO
    def test_manage_roles_cto(self):
        self.client.post('/login', data=dict(username='cto', password='password'), follow_redirects=True)
        response = self.client.get('/cto/manage_roles')
        self.assertEqual(response.status_code, us)

    # בדיקה של עדכון תפקידים על ידי CTO
    def test_update_role_cto(self):
        self.client.post('/login', data=dict(username='cto', password='password'), follow_redirects=True)
        response = self.client.post('/cto/update_role', data=dict(user_id=3, new_role='R&D', team_id=1), follow_redirects=True)
        self.assertEqual(response.status_code, us)

    # בדיקה של יצירת צוות על ידי CTO
    def test_create_team_cto(self):
        self.client.post('/login', data=dict(username='cto', password='password'), follow_redirects=True)
        response = self.client.post('/cto/create_team', data=dict(team_name='New Team'), follow_redirects=True)
        self.assertEqual(response.status_code, us)

    # בדיקה של הוספת משתמש לצוות על ידי CTO
    def test_add_user_to_team_cto(self):
        self.client.post('/login', data=dict(username='cto', password='password'), follow_redirects=True)
        response = self.client.post('/cto/add_user_to_team', data=dict(team_id_add=1, user_id_add=5), follow_redirects=True)
        self.assertEqual(response.status_code, us)

if __name__ == "__main__":
    unittest.main()

