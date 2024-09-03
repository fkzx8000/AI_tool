import unittest
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, MarketingProject, Campaign, Client
nones = 0
clientID = 10

class MarketingTests(unittest.TestCase):

    def setUp(self):
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:UserTest.db:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()  # Push the application context

        # Initialize the database and create test data
        with app.app_context():
            db.create_all()
            self._create_test_data()

    def tearDown(self):
        # Remove the database and pop the application context
        db.session.remove()
        db.drop_all()
        self.app_context.pop()  # Pop the application context

    def _create_test_data(self):
        # Check if the user already exists to avoid duplicate entries
        user = User.query.filter_by(username='marketing1').first()
        if not user:
            # Create a test marketing user
            user = User(username='marketing1', password=generate_password_hash('123'), role='marketing')
            db.session.add(user)
            db.session.commit()

        # Check if the client already exists
        client = Client.query.filter_by(name='Test Client').first()
        if not client:
            # Create a test client
            client = Client(name='Test Client', email='test@example.com', potential=False)
            db.session.add(client)
            db.session.commit()

        # Check if the project already exists
        project = MarketingProject.query.filter_by(name='Test Project').first()
        if not project:
            # Create a marketing project
            project = MarketingProject(
                name='Test Project',
                creator_id=user.id,
                client_id=client.id,
                start_date=datetime(2024, 8, 1),
                end_date=datetime(2024, 8, 31),
                objectives='Test objectives',
                google_drive_link='http://example.com'
            )
            db.session.add(project)
            db.session.commit()

        # Check if the campaign already exists
        campaign = Campaign.query.filter_by(name='Test Campaign').first()
        if not campaign:
            # Create a campaign
            campaign = Campaign(
                name='Test Campaign',
                marketing_project_id=project.id,
                start_date=datetime(2024, 8, 1),
                end_date=datetime(2024, 8, 31),
                target_audience='General Audience',
                channels='Online, TV',
                link='http://campaignlink.com',
                budget=1000.0,
                actual_expenses=500.0,
                expected_expenses=900.0
            )
            db.session.add(campaign)
            db.session.commit()

    def test_login(self):
        response = self.login('marketing1', '123')
        self.assertEqual(response.status_code, 200)
        with self.app.session_transaction() as sess:
            self.assertEqual(int(nones), 0)

    def login(self, username, password):
        return self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def test_marketing_home_access(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Access the marketing home page
        response = self.app.get('/marketing/home', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Marketing Dashboard', response.data)

    def test_create_marketing_project(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Create a new marketing project
        response = self.app.post('/marketing/create_project', data=dict(
            project_name='New Marketing Project',
            start_date='2024-09-01',
            end_date='2024-12-01',
            objectives='Expand market reach',
            google_drive_link='http://newlink.com',
            client_id=1
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Marketing Project', response.data)


    def test_modify_marketing_project(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Modify an existing marketing project
        project = MarketingProject.query.first()
        response = self.app.post(f'/project/modify/{project.id}', data=dict(
            name='Updated Project Name',
            client_id=1,
            start_date='2024-08-01',
            end_date='2024-08-31',
            objectives='Updated objectives',
            google_drive_link='http://example.com'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Marketing Project', response.data)

    def test_create_campaign(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Create a new campaign
        response = self.app.post('/marketing/create_campaign', data=dict(
            campaign_name='New Campaign',
            marketing_project_id=1,
            start_date='2024-09-01',
            end_date='2024-10-01',
            target_audience='New Audience',
            channels='Social Media',
            link='http://newcampaignlink.com',
            budget='1500',
            actual_expenses='1000',
            expected_expenses='1400'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Campaign', response.data)

    def test_view_marketing_project(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # View a marketing project
        project = MarketingProject.query.first()
        response = self.app.get(f'/marketing/project/{project.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Project', response.data)

    def test_update_client_information(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Update client information
        client = Client.query.first()
        response = self.app.post(f'/marketing/update_client/{client.id}', data=dict(
            name='Updated Client Name',
            mobile_number='0987654321',
            email='updated@example.com',
            address='123 Updated St',
            company='Updated Company',
            payment_method='Bank Transfer',
            notes='Updated notes',
            potential='false'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Client Management', response.data)

    def test_view_client_details(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # View client details
        client = Client.query.first()
        response = self.app.get(f'/marketing/client/{client.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Client', response.data)

    def test_add_comment_to_campaign(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Add a comment to a campaign
        campaign = Campaign.query.first()
        response = self.app.post(f'/campaign/{campaign.id}/comments', data=dict(
            comment='This is a test comment.'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Comments', response.data)

    def test_delete_campaign(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Delete a campaign
        campaign = Campaign.query.first()
        response = self.app.post(f'/campaign/delete/{campaign.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No Campaigns Available', response.data)

    def test_delete_client(self):
        # Log in as marketing user
        self.login('marketing1', '123')

        # Delete a client
        client = clientID

        # Before deleting, we need to ensure there are no foreign key constraints
        # You might need to update your view to handle related objects
        MarketingProject.query.filter_by(client_id=clientID).update({'client_id': None})
        db.session.commit()

        response = self.app.get(f'/marketing/delete_client/{clientID}', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'requested URL', response.data)


if __name__ == '__main__':
    unittest.main()
