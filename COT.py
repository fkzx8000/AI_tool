from flask import Flask
from models import db, User, Team, Project, Task, Notification, Message, Log, MarketingProject, Campaign, Client, Presentation, Feedback, Comment
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_users():
    roles = ['admin', 'CTO', 'TL', 'R&D', 'marketing', 'viewer']
    users = []

    for role in roles:
        for i in range(1, 4):  # Create 3 users for each role
            username = f'{role.lower()}{i}'
            password = generate_password_hash('123', method='pbkdf2:sha256')
            user = User(username=username, password=password, role=role)
            users.append(user)

    db.session.add_all(users)
    db.session.commit()
    print("Users created successfully.")

def create_teams_and_projects():
    # Fetch users with specific roles
    cto_users = User.query.filter_by(role='CTO').all()
    tl_users = User.query.filter_by(role='TL').all()
    rnd_users = User.query.filter_by(role='R&D').all()

    # Create teams and assign team leaders
    teams = []
    for i, cto in enumerate(cto_users, start=1):
        team = Team(name=f'Team {i}', cto_id=cto.id)
        leader = tl_users[i % len(tl_users)]
        team.leader_id = leader.id  # Assign TL as team leader
        teams.append(team)
        leader.team_id = team.id
        db.session.add(leader)

    db.session.add_all(teams)
    db.session.commit()

    # Create projects
    projects = []
    for i, team in enumerate(teams):
        project = Project(name=f'Project {i + 1}', description='Sample project', tl_id=team.leader_id, cto_id=team.cto_id)
        projects.append(project)

    db.session.add_all(projects)
    db.session.commit()

    # Assign R&D members to projects
    for project in projects:
        if rnd_users:  # Ensure there are R&D users available
            rnd_user = rnd_users.pop(0)
            project.team_members.append(rnd_user)
            db.session.add(project)

    db.session.commit()

    print("Teams and projects created and assigned successfully.")

def create_marketing_projects_and_campaigns():
    marketing_users = User.query.filter_by(role='marketing').all()

    # Create clients
    clients = [
        Client(name="Client A", potential=True),
        Client(name="Client B", potential=False),
        Client(name="Client C", potential=True)
    ]
    db.session.add_all(clients)
    db.session.commit()

    # Create marketing projects
    marketing_projects = []
    for i, marketing_user in enumerate(marketing_users, start=1):
        client = clients[i % len(clients)]
        project = MarketingProject(
            name=f'Marketing Project {i}',
            creator_id=marketing_user.id,
            client_id=client.id,
            created_date=datetime.now(timezone.utc),
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            objectives='Increase brand awareness',
            google_drive_link='http://example.com/drive'
        )
        marketing_projects.append(project)

    db.session.add_all(marketing_projects)
    db.session.commit()

    # Create campaigns for marketing projects
    for i, project in enumerate(marketing_projects):
        campaign = Campaign(
            name=f'Campaign {i + 1}',
            marketing_project_id=project.id,
            target_audience='18-25 year olds',
            channels='Social Media',
            link='http://example.com/campaign',
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            budget=random.uniform(10000, 50000),  # תקציב אקראי לדוגמה
            actual_expenses=random.uniform(5000, 20000),  # הוצאות בפועל אקראיות לדוגמה
            expected_expenses=random.uniform(15000, 40000)  # הוצאות צפויות אקראיות לדוגמה
        )
        db.session.add(campaign)

    db.session.commit()

    print("Marketing projects and campaigns created successfully.")

# Create sample tasks and notifications
def create_tasks_and_notifications():
    projects = Project.query.all()

    # Create tasks
    for project in projects:
        for i in range(3):  # Create 3 tasks per project
            task = Task(name=f'Task {i + 1} for {project.name}', description='Sample task', project_id=project.id, status='open')
            db.session.add(task)

        # Create sample messages
        if project.team_members:  # Ensure there is at least one team member
            message = Message(sender_id=project.tl_id, receiver_id=project.team_members[0].id, message=f'Welcome to {project.name}!')
            db.session.add(message)

    db.session.commit()
    print("Tasks and notifications created successfully.")

def create_sample_presentations():
    presentations = [
        Presentation(title="Presentation A", link="http://example.com/presentationA", marketing_project_id=1),
        Presentation(title="Presentation B", link="http://example.com/presentationB", marketing_project_id=2),
        Presentation(title="Presentation C", link="http://example.com/presentationC", marketing_project_id=3),
    ]
    db.session.add_all(presentations)
    db.session.commit()
    print("Sample presentations created successfully.")

def create_sample_clients():
    clients = [
        Client(name="John Doe", potential=True, mobile_number="123-456-7890", email="john@example.com",
               address="123 Main St", company="Example Corp", payment_method="Credit Card", notes="High interest"),
        Client(name="Jane Smith", potential=False, mobile_number="098-765-4321", email="jane@example.com",
               address="456 Elm St", company="Tech Solutions", payment_method="PayPal", notes="Reliable"),
        Client(name="Bob Johnson", potential=True, mobile_number="555-123-4567", email="bob@example.com",
               address="789 Pine St", payment_method="Wire Transfer", notes="Negotiating terms"),
    ]
    db.session.add_all(clients)
    db.session.commit()
    print("Sample clients created successfully.")

# Add random logs
def create_logs():
    projects = Project.query.all()
    log_messages = [
        "Project kick-off meeting held.",
        "Requirements gathering completed.",
        "First sprint planning executed.",
        "Code review session conducted.",
        "Bug fixing in progress.",
        "Client feedback received.",
        "Deployment to staging environment.",
        "Final project presentation prepared."
    ]

    for project in projects:
        for _ in range(random.randint(3, 6)):  # Create between 3 and 6 log entries per project
            log_message = random.choice(log_messages)
            log = Log(project_id=project.id, user_id=project.tl_id, message=log_message)
            db.session.add(log)

    db.session.commit()
    print("Logs created successfully.")

def create_feedback():
    campaigns = Campaign.query.all()
    users = User.query.all()

    for campaign in campaigns:
        for _ in range(random.randint(1, 3)):  # Create between 1 and 3 feedback entries per campaign
            user = random.choice(users)
            feedback = Feedback(
                campaign_id=campaign.id,
                user_id=user.id,
                content=f"Feedback from {user.username} on campaign {campaign.name}."
            )
            db.session.add(feedback)

    db.session.commit()
    print("Feedback entries created successfully.")

def create_comments():
    campaigns = Campaign.query.all()
    users = User.query.all()

    for campaign in campaigns:
        for _ in range(random.randint(1, 3)):  # Create between 1 and 3 comments per campaign
            user = random.choice(users)
            comment = Comment(
                campaign_id=campaign.id,
                user_id=user.id,
                content=f"Comment from {user.username} on campaign {campaign.name}."
            )
            db.session.add(comment)

    db.session.commit()
    print("Comment entries created successfully.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all tables are created
        create_users()
        create_teams_and_projects()
        create_marketing_projects_and_campaigns()
        create_tasks_and_notifications()
        create_sample_presentations()
        create_sample_clients()
        create_logs()
        create_feedback()
        create_comments()
