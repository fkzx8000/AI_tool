from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='viewer', index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id', use_alter=True, name='fk_user_team_id'), nullable=True)
    average_code_score = db.Column(db.Float, default=0.0)
    projects = db.relationship('Project', secondary='project_team_members', back_populates='team_members')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cto_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rnds = db.relationship('User', foreign_keys=[User.team_id], backref='team', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    tl_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cto_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    team_members = db.relationship('User', secondary='project_team_members', back_populates='projects')
    tasks = db.relationship('Task', backref='project', lazy=True)

project_team_members = db.Table('project_team_members',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='open', index=True)
    opened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assignee = db.relationship('User', backref=db.backref('assigned_tasks', lazy=True))

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user = db.relationship('User', backref='ratings')

#BSPMS2429-163
class PerformanceReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    code_snippet = db.Column(db.Text, nullable=False)
    report = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('performance_reports', lazy=True))
    team = db.relationship('Team', backref=db.backref('performance_reports', lazy=True))


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship('Project', backref=db.backref('logs', lazy=True))
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class MarketingProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    objectives = db.Column(db.Text, nullable=False)
    google_drive_link = db.Column(db.String(255))  # Add this line
    campaigns = db.relationship('Campaign', backref='marketing_project', lazy=True)

    # Define the relationship to the Client model
    client = db.relationship('Client', back_populates='marketing_projects_list', overlaps="marketing_projects_list")
    creator = db.relationship('User', backref='created_marketing_projects')


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='feedbacks')

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    potential = db.Column(db.Boolean, default=False)
    marketing_projects_list = db.relationship('MarketingProject', back_populates='client', overlaps="client")


class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    marketing_project_id = db.Column(db.Integer, db.ForeignKey('marketing_project.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    marketing_project_id = db.Column(db.Integer, db.ForeignKey('marketing_project.id'), nullable=False)
    target_audience = db.Column(db.String(255), nullable=False)
    channels = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=True)  # תקציב הקמפיין
    actual_expenses = db.Column(db.Float, nullable=True)  # הוצאות בפועל
    expected_expenses = db.Column(db.Float, nullable=True)  # הוצאות צפויות
    feedbacks = db.relationship('Feedback', backref='campaign', lazy=True)  # קשר למשוב
    comments = db.relationship('Comment', backref='campaign', lazy=True)  # קשר להערות

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='comments')
