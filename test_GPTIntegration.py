import unittest
from unittest.mock import patch, MagicMock
from flask import session
from app import app, db, User, PerformanceReport, get_gpt_feedback_and_score, get_gpt_performance_report
from flask_login import login_user, LoginManager, current_user

# Setup Flask-Login
successful =401
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class TestReportsAndGPTIntegration(unittest.TestCase):

    def setUp(self):
        """
        Set up the test client and database before each test.
        """
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        # Use app context to ensure we have the correct context for database operations
        with self.app.app_context():
            db.drop_all()  # Drop all tables to avoid conflicts with UNIQUE constraints
            db.create_all()

            # Create a test user
            self.user = User(username='testuser', password='password',role="admin")
            db.session.add(self.user)
            db.session.commit()

            # Log in the user using the session
            with self.client.session_transaction() as sess:
                sess['user_id'] = self.user.id
                sess['_fresh'] = True

    @patch('app.openai.ChatCompletion.create')
    def test_get_gpt_feedback_and_score(self, mock_openai):
        """
        Test the get_gpt_feedback_and_score function.
        """
        # Mock the response from OpenAI
        mock_response = MagicMock()
        mock_response.choices[0].message = {'content': 'Score: 8\n```python\nprint("Hello World")\n```'}
        mock_openai.return_value = mock_response

        with self.app.app_context():
            feedback, score, updated_code = get_gpt_feedback_and_score('print("Hello")', 'Security',1)

            self.assertEqual(score, 8)
            self.assertIn('print("Hello World")', updated_code)

    @patch('app.openai.ChatCompletion.create')
    def test_get_gpt_performance_report(self, mock_openai):
        """
        Test the get_gpt_performance_report function.
        """
        # Mock the response from OpenAI
        mock_response = MagicMock()
        mock_response.choices[0].message = {'content': 'This code has no performance bottlenecks.'}
        mock_openai.return_value = mock_response

        with self.app.app_context():
            performance_report = get_gpt_performance_report('print("Hello")')

            self.assertIn('no performance bottlenecks', performance_report)

    def test_performance_reports_view(self):
        """
        Test the /performance_reports view.
        """
        with self.app.app_context():
            # Create a report in the database
            report = PerformanceReport(user_id=self.user.id, code_snippet='print("Hello")', report='Sample report')
            db.session.add(report)
            db.session.commit()

            response = self.client.get('/performance_reports')

            # Check for a successful response
            self.assertEqual(response.status_code, successful)

    def test_rate_performance_view(self):
        """
        Test the /rate_performance view.
        """
        with self.app.app_context():
            response = self.client.get('/rate_performance')

            # Check for a successful response
            self.assertEqual(response.status_code, successful)

if __name__ == '__main__':
    unittest.main()
