from flask import Flask, render_template, redirect, url_for, request, flash, session,jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Team, Project, Task, Rating, project_team_members, Log, Notification, Message, \
    MarketingProject, Client, Presentation, Campaign, Comment, Feedback, PerformanceReport
from collections import defaultdict
from datetime import datetime
import re
import openai



app = Flask(__name__)
openai.api_key = 'your open ai key'


def create_app():
    """
    Creates and configures the Flask application.

    - Configures the database and initializes the login manager.
    - Creates all database tables.

    :return: Configured Flask app.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'mysecret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    return app


app = create_app()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def set_default_language():
    if 'language' not in session:
        session['language'] = 'en'

@app.route('/set_language', methods=['POST'])
def set_language():
    selected_language = request.form.get('language')
    if selected_language in ['he', 'en']:
        session['language'] = selected_language
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    """
    Redirects authenticated users to their respective home pages based on their role.

    - Admin: Redirects to admin home page.
    - CTO: Redirects to CTO home page.
    - TL: Redirects to team leader home page.
    - R&D: Redirects to R&D home page.
    - Viewer: Redirects to viewer home page.
    - Not authenticated: Shows not logged in page.
    """
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_home'))
        elif current_user.role == 'CTO':
            return redirect(url_for('cto_home'))
        elif current_user.role == 'TL':
            return redirect(url_for('tl_home'))
        elif current_user.role == 'R&D':
            return redirect(url_for('rnd_home'))
        elif current_user.role == 'marketing':
            return redirect(url_for('marketing_home'))
        else:
            return redirect(url_for('viewer_home'))
    return render_template('not_logged_in.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.

    - If authenticated, redirects to home page.
    - If POST request, checks username and password, logs in user if valid.
    - Shows login page otherwise.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.

    - If authenticated, redirects to home page.
    - If POST request, registers new user with username and hashed password.
    - Shows registration page otherwise.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Add role selection in registration form

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """
    Logs out the current user and redirects to home page.
    """
    logout_user()
    return redirect(url_for('home'))




@app.route('/admin/home')
@login_required
def admin_home():
    """
    Admin home page displaying all users organized by role and teams.
    """
    if current_user.role != 'admin':
        return 'Access denied'

    users = User.query.all()
    teams = Team.query.all()

    # Organize users by role
    users_by_role = defaultdict(list)
    users_dict = {user.id: user for user in users}  # for quick lookup by id
    for user in users:
        users_by_role[user.role].append(user)

    return render_template('admin/home.html', users_by_role=users_by_role, teams=teams, users_dict=users_dict)



@app.route('/admin/set_role', methods=['GET', 'POST'])
@login_required
def set_role():
    """
    Allows admin to set user roles.

    - Only accessible by admin users.
    - GET: Shows form to set user roles.
    - POST: Updates user role based on form input.
    """
    if current_user.role != 'admin':
        return 'Access denied'

    if request.method == 'POST':
        user_id = request.form['user_id']
        new_role = request.form['role']
        user = User.query.get(user_id)
        if user:
            user.role = new_role
            db.session.commit()
            return render_template('admin/home.html')
        return 'User not found'

    users = User.query.all()
    return render_template('admin/set_role.html', users=users)


@app.route('/cto/home')
@login_required
def cto_home():
    """
    Shows the CTO home page with team leaders and their projects.
    """
    if current_user.role not in ['admin', 'CTO']:
        return 'Access denied'

    teams = Team.query.all()
    team_data = []
    for team in teams:
        leader = User.query.get(team.leader_id)
        if leader:
            projects = Project.query.filter_by(tl_id=leader.id).all()
            for project in projects:
                # Collect team members for each project
                project.team_members = User.query.join(project_team_members).filter(
                    project_team_members.c.project_id == project.id).all()

            # Collect team members and calculate their average scores
            team_members = User.query.filter_by(team_id=team.id).all()
            for member in team_members:
                ratings = Rating.query.filter_by(user_id=member.id).all()
                if ratings:
                    member.average_score = round(sum(rating.score for rating in ratings) / len(ratings), 2)
                else:
                    member.average_score = None

            team_info = {
                'name': team.name,
                'leader': leader,
                'projects': projects,
                'team_members': team_members
            }
            team_data.append(team_info)

    return render_template('cto/home.html', team_data=team_data)



@app.route('/cto/manage_roles', methods=['GET'])
@login_required
def manage_roles():
    """
    Manages roles of users for CTO.

    - Only accessible by CTO users.
    - Shows form to manage user roles.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    users = User.query.filter(User.role.in_(['viewer', 'R&D', 'TL'])).all()
    teams = Team.query.all()
    return render_template('cto/manage_roles.html', users=users, teams=teams)


@app.route('/cto/update_role', methods=['POST'])
@login_required
def update_role():
    """
    Updates role of a user.

    - Only accessible by CTO users.
    - Updates user role and optionally assigns to a team.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        flash('Access denied: You do not have permission to perform this action.', 'danger')
        return redirect(url_for('manage_roles'))

    user_id = request.form['user_id']
    new_role = request.form['new_role']
    team_id = request.form.get('team_id')
    user = User.query.get(user_id)

    if user:
        if user.role == 'TL' and user.team_id != team_id:
            oldTeam = Team.query.get(user.team_id)
            oldTeam.leader_id = None
            db.session.commit()
        if new_role == 'R&D':
            user.role = new_role
            user.team_id = team_id
            db.session.commit()
            flash('User role updated to R&D successfully.', 'success')
        elif new_role == 'TL':
            if team_id:
                existing_tl = User.query.filter_by(team_id=team_id, role='TL').first()
                if existing_tl:
                    flash('The team already has a TL. The user cannot be added as TL to this team.', 'danger')
                else:
                    user.role = new_role
                    user.team_id = team_id
                    team = Team.query.get(team_id)
                    team.leader_id = user.id
                    db.session.commit()
                    flash('User promoted to TL and added to team successfully.', 'success')
            else:
                user.role = new_role
                user.team_id = None
                db.session.commit()
                flash('User promoted to TL without team.', 'success')
        elif new_role == 'viewer':
            open_projects = Project.query.filter_by(tl_id=user.id).join(Task).filter(Task.status != 'completed').all()
            if open_projects:
                flash('The TL cannot be demoted to viewer because they have active projects with open tasks.', 'danger')
            else:
                user.role = new_role
                user.team_id = team_id
                db.session.commit()
                flash('User role updated to viewer successfully.', 'success')
        else:
            flash('Invalid role selected.', 'danger')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('manage_roles'))


@app.route('/cto/create_team', methods=['POST'])
@login_required
def create_team():
    """
    Creates a new team.

    - Only accessible by CTO users.
    - Creates a new team with a specified name.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    team_name = request.form['team_name']
    new_team = Team(name=team_name, cto_id=current_user.id)
    db.session.add(new_team)
    db.session.commit()
    flash('Team created successfully.', 'success')
    return redirect(url_for('manage_roles'))


@app.route('/cto/add_user_to_team', methods=['POST'])
@login_required
def add_user_to_team():
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    team_id = request.form['team_id_add']
    user_id = request.form['user_id_add']
    team = Team.query.get(team_id)
    user = User.query.get(user_id)

    if team and user:
        if user.team_id and user.team_id != team_id:
            flash(f'The user is already a member of another team: {user.team.name}.', 'danger')
        else:
            if user.role == 'TL':
                existing_tl = User.query.filter_by(team_id=team_id, role='TL').first()
                if existing_tl:
                    flash('The team already has a TL.', 'danger')
                else:
                    # Remove TL from the previous team
                    old_team = Team.query.filter_by(leader_id=user.id).first()
                    if old_team:
                        old_team.leader_id = None

                    user.team_id = team_id
                    team.leader_id = user.id
                    db.session.commit()
                    flash('User added to team successfully as TL.', 'success')
            else:
                user.team_id = team_id
                db.session.commit()
                flash('User added to team successfully.', 'success')
    else:
        flash('Team or user not found.', 'danger')

    return redirect(url_for('manage_roles'))



@app.route('/cto/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    """
    Manages projects for CTO.

    - Only accessible by CTO users.
    - GET: Shows form to manage projects.
    - POST: Creates a new project based on form input.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        tl_id = request.form['tl_id']
        new_project = Project(name=name, description=description, tl_id=tl_id, cto_id=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('manage_projects'))

    tls = User.query.filter_by(role='TL').all()
    projects = Project.query.all()
    projects_without_tl = Project.query.filter_by(tl_id=None).all()
    return render_template('cto/manage_projects.html', tls=tls, projects=projects, projects_without_tl=projects_without_tl)



@app.route('/cto/view_project/<int:project_id>', methods=['GET'])
@login_required
def view_project(project_id):
    """
    Views a project in detail.

    - Only accessible by CTO users.
    - Shows detailed information about a specific project.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    open_tasks = Task.query.filter_by(project_id=project_id, status='open').order_by(Task.opened_at).all()
    closed_tasks = Task.query.filter_by(project_id=project_id, status='closed').order_by(Task.opened_at).all()
    team_leader = User.query.get(project.tl_id)
    team_members = project.team_members
    total_score = 0
    num_ratings = 0
    for member in team_members:
        ratings = Rating.query.filter_by(user_id=member.id).all()
        member.average_code_score = sum(rating.score for rating in ratings) / len(ratings) if ratings else None
        total_score += sum(rating.score for rating in ratings)
        num_ratings += len(ratings)
    average_score = total_score / num_ratings if num_ratings > 0 else 0

    return render_template('cto/view_project_modal.html', project=project, open_tasks=open_tasks,
                           closed_tasks=closed_tasks, team_leader=team_leader, team_members=team_members,
                           average_score=average_score)



@app.route('/cto/remove_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def remove_project(project_id):
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        # Remove TL from the project and update team leader's team ID
        if project.tl_id:
            team_leader = User.query.get(project.tl_id)
            if team_leader:
                team_leader.team_id = None
                project.team_members.clear()  # Remove all team members from the project
                db.session.commit()

        project.tl_id = None
        db.session.commit()

        flash('Team Leader and all team members removed from the project successfully.', 'success')
        return redirect(url_for('manage_projects'))

    return render_template('cto/confirm_remove_tl.html', project=project)




@app.route('/cto/assign_tl', methods=['POST'])
@login_required
def assign_tl():
    """
    Assigns a team leader to a project.

    - Only accessible by CTO users.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('manage_projects'))

    project_id = request.form.get('project_id')
    tl_id = request.form.get('tl_id')

    if not project_id or not tl_id:
        flash('Project ID and Team Leader ID are required.', 'danger')
        return redirect(url_for('manage_projects'))

    project = Project.query.get_or_404(project_id)
    team_leader = User.query.get_or_404(tl_id)

    if team_leader.role != 'TL':
        flash('Selected user is not a Team Leader.', 'danger')
        return redirect(url_for('manage_projects'))

    # Unassign the current team leader from the project
    if project.tl_id:
        old_team_leader = User.query.get(project.tl_id)
        if old_team_leader:
            old_team_leader.team_id = None
            if old_team_leader in project.team_members:
                project.team_members.remove(old_team_leader)

    # Assign the new team leader to the project and add them as a team member
    project.tl_id = tl_id
    team_leader.team_id = project.id
    if team_leader not in project.team_members:
        project.team_members.append(team_leader)

    db.session.commit()

    # הוספת לוג לשינוי ראש הצוות בפרויקט
    add_log(project.id, current_user.id,
            f'Team Leader "{team_leader.username}" assigned to project "{project.name}" by {current_user.username}.')

    flash(f'Team Leader {team_leader.username} assigned to project {project.name}.', 'success')
    return redirect(url_for('manage_projects'))


@app.route('/cto/delete_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def delete_project(project_id):
    """
    Deletes a project.

    - Only accessible by CTO users.
    - GET: Shows confirmation form to delete project.
    - POST: Deletes the project.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        db.session.delete(project)
        db.session.commit()

        # הוספת לוג למחיקת הפרויקט
        add_log(project_id, current_user.id, f'Project "{project.name}" deleted by {current_user.username}.')

        flash('Project deleted successfully.', 'success')
        return redirect(url_for('manage_projects'))

    return render_template('cto/confirm_delete_project.html', project=project)


@app.route('/cto/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    """
    Adds a new project.

    - Only accessible by CTO users.
    - GET: Shows form to add a new project.
    - POST: Creates a new project based on form input.
    """
    if current_user.role != 'CTO' and current_user.role != 'admin':
        return 'Access denied'

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        tl_id = request.form['tl_id']
        new_project = Project(name=name, description=description, tl_id=tl_id, cto_id=current_user.id)
        db.session.add(new_project)
        db.session.commit()

        # הוספת לוג לפרויקט החדש
        add_log(new_project.id, current_user.id, f'Project "{name}" created by {current_user.username}.')

        return redirect(url_for('cto_home'))

    tls = User.query.filter_by(role='TL').all()
    return render_template('cto/add_project.html', tls=tls)


@app.route('/tl/home')
@login_required
def tl_home():
    """
    Shows the team leader home page with team and project information.

    - Only accessible by admin, CTO, and TL users.
    """
    if current_user.role not in ['admin', 'CTO', 'TL']:
        return 'Access denied'

    projects = Project.query.filter_by(tl_id=current_user.id).all()
    team = Team.query.get(current_user.team_id)
    team_name = team.name if team else 'Team Leader Home'
    team_members = User.query.filter_by(team_id=current_user.team_id).all()
    team_tasks = Task.query.join(Project).filter(Project.tl_id == current_user.id).all()
    total_score = 0
    total_ratings = 0
    for member in team_members:
        member.projects = Project.query.join(project_team_members).join(User).filter(
            project_team_members.c.user_id == member.id).all()
        ratings = Rating.query.filter_by(user_id=member.id).all()
        if ratings:
            member.average_code_score = round(sum(rating.score for rating in ratings) / len(ratings), 2)
            total_score += sum(rating.score for rating in ratings)
            total_ratings += len(ratings)
    team_average_score = round(total_score / total_ratings, 2) if total_ratings > 0 else None

    return render_template('tl/home.html', projects=projects, team_members=team_members, team_tasks=team_tasks, team_name=team_name, team_average_score=team_average_score)

@app.route('/add_user_to_project/<int:project_id>/<int:user_id>', methods=['POST'])
@login_required
def add_user_to_project(project_id, user_id):
    """
    Add a user to a project.
    """

    if current_user.role != 'TL' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    user = User.query.get_or_404(user_id)

    if user not in project.team_members:
        project.team_members.append(user)
        db.session.commit()

        # הוספת לוג להוספת המשתמש למשימה
        add_log(project.id, current_user.id, f'User "{user.username}" added to project "{project.name}" by {current_user.username}.')

        flash(f'{user.username} has been added to {project.name}.', 'success')
    else:
        flash(f'{user.username} is already a member of {project.name}.', 'info')

    return redirect(url_for('tl_home'))


@app.route('/remove_user_from_project/<int:project_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_user_from_project(project_id, user_id):
    """
    Remove a user from a project.
    """
    if current_user.role != 'TL' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    user = User.query.get_or_404(user_id)

    if user in project.team_members:
        project.team_members.remove(user)
        db.session.commit()

        # הוספת לוג להסרת המשתמש מהמשימה
        add_log(project.id, current_user.id, f'User "{user.username}" removed from project "{project.name}" by {current_user.username}.')

        flash(f'{user.username} has been removed from {project.name}.', 'success')
    else:
        flash(f'{user.username} is not a member of {project.name}.', 'info')

    return redirect(url_for('tl_home'))


@app.route('/project/<int:project_id>/add_task', methods=['GET', 'POST'])
@login_required
def add_task(project_id):
    """
    Adds a new task to a project.

    - Only accessible by TL users.
    - GET: Shows form to add a new task.
    - POST: Creates a new task based on form input.
    """
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        assignee_id = request.form['assignee_id']
        assignee = User.query.get(assignee_id) if assignee_id else None
        new_task = Task(name=name, description=description, project_id=project.id,
                        assignee_id=assignee.id if assignee else None, status='open')
        db.session.add(new_task)
        db.session.commit()

        # הוספת לוג להוספת המשימה
        add_log(project.id, current_user.id, f'Task "{name}" added to project "{project.name}" by {current_user.username}.')

        notify_team_members(project.id, f'Task "{name}" added to project "{project.name}" by {current_user.username}.')
        flash('Task added successfully!', 'success')
        if assignee != None:
            return redirect(url_for('manage_project', project_id=project.id))
        return redirect(url_for('tl_home'))

    team_members = project.team_members
    return render_template('tl/add_task.html', project=project, team_members=team_members)

# התלבטות בין הלמעלה ללמטה
@app.route('/add_task_to_user/<int:project_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_task_to_user(project_id, user_id):
    """
    Adds a new task to a specific user in a specific project.
    """
    if current_user.role != 'TL' and current_user.role != 'admin':
        return 'Access denied'

    user = User.query.get_or_404(user_id)
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_task = Task(name=name, description=description, project_id=project.id, assignee_id=user.id)
        db.session.add(new_task)
        db.session.commit()
        flash(f'Task "{name}" added to {user.username} in project "{project.name}".', 'success')
        return redirect(url_for('tl_home'))

    return render_template('add_task_to_user.html', project=project, user=user)


@app.route('/project/<int:project_id>/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(project_id, task_id):
    """
    Edits an existing task.

    - Only accessible by TL users.
    - GET: Shows form to edit the task.
    - POST: Updates the task based on form input.
    """
    project = Project.query.get_or_404(project_id)
    task = Task.query.get_or_404(task_id)

    if (current_user.role != 'TL' and current_user.role != 'admin') or project.tl_id != current_user.id:
        return 'Access denied'

    if request.method == 'POST':
        old_status = task.status  # שמירת הסטטוס הקודם
        task.name = request.form['name']
        task.description = request.form['description']
        task.status = request.form['status']
        assignee_id = request.form.get('assignee_id')
        task.assignee_id = assignee_id if assignee_id else None
        db.session.commit()

        # הוספת לוג לעדכון המשימה
        add_log(project.id, current_user.id, f'Task "{task.name}" updated by {current_user.username}. Status changed from "{old_status}" to "{task.status}".')

        notify_team_members(project.id, f'Task "{task.name}" updated by {current_user.username}.')
        flash('Task updated successfully!', 'success')
        return redirect(url_for('edit_task', project_id=project.id, task_id=task.id))  # Redirect back to edit page

    team_members = project.team_members
    return render_template('tl/edit_task.html', project=project, task=task, team_members=team_members)



@app.route('/tl/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def manage_task(task_id):
    """
    Manages a task and adds subtasks.

    - Only accessible by admin, CTO, and TL users.
    - GET: Shows task details and form to add subtasks.
    - POST: Adds a subtask based on form input.
    """
    if current_user.role not in ['admin', 'CTO', 'TL']:
        return 'Access denied'

    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)
    if project.tl_id != current_user.id:
        return 'Access denied'

    if request.method == 'POST':
        subtask_name = request.form['subtask_name']
        subtask_description = request.form['subtask_description']
        assignee_id = request.form['assignee_id']
        new_subtask = Task(name=subtask_name, description=subtask_description, project_id=project.id,
                           assignee_id=assignee_id, status='open', parent_id=task.id)
        db.session.add(new_subtask)
        db.session.commit()

        # הוספת לוג להוספת תת-המשימה
        add_log(project.id, current_user.id,
                f'Sub-task "{subtask_name}" added to task "{task.name}" by {current_user.username}.')

        flash('Sub-task added successfully.', 'success')
        notify_team_members(project.id,
                            f'New sub-task "{subtask_name}" added to task "{task.name}" by {current_user.username}.')
        return redirect(url_for('manage_task', task_id=task_id))

    team_members = User.query.filter_by(team_id=current_user.team_id, role='R&D').all()
    return render_template('tl/manage_task.html', task=task, team_members=team_members)

@app.route('/task/<int:task_id>/claim', methods=['POST'])
@login_required
def claim_task(task_id):
    """
    Allows a user to claim an open task.

    - Only accessible by R&D users.
    """

    if current_user.role != 'R&D' and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('task_queue'))

    task = Task.query.get_or_404(task_id)
    if task.assignee_id is not None:
        flash('Task already claimed by another user.', 'danger')
    else:
        task.assignee_id = current_user.id
        db.session.commit()
        flash(f'Task "{task.name}" claimed successfully!', 'success')

    return redirect(url_for('task_queue'))



@app.route('/tl/manage_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def manage_project(project_id):
    """
    Manages a project and adds team members.

    - Only accessible by TL users.
    - GET: Shows project details and form to add team members.
    - POST: Adds team members to the project based on form input.
    """

    if current_user.role != 'TL' and current_user.role != 'admin':
        return 'Access denied'

    project = Project.query.get_or_404(project_id)
    team_members = User.query.filter_by(team_id=current_user.team_id, role='R&D').all()

    if request.method == 'POST':
        member_id = request.form.get('member_id')
        if member_id:
            member = User.query.get(member_id)
            if member and member not in project.team_members:
                project.team_members.append(member)

                # הוספת לוג להוספת חבר צוות לפרויקט
                add_log(project.id, current_user.id, f'{member.username} added to project "{project.name}" by {current_user.username}.')

                db.session.commit()
                flash(f'{member.username} has been added to {project.name}.', 'success')
            else:
                flash('Member is already part of the project or invalid member.', 'danger')

    tasks = Task.query.filter_by(project_id=project.id).all()
    return render_template('tl/manage_project.html', project=project, team_members=team_members, tasks=tasks)


@app.route('/project/<int:project_id>/logs')
@login_required
def project_logs(project_id):
    """
    Views the logs of a project.

    - Only accessible by TL, CTO, and admin users.
    - Shows log entries for a specific project.
    """
    project = Project.query.get_or_404(project_id)

    # Admin and CTO can see all logs
    if current_user.role in ['admin', 'CTO']:
        logs = Log.query.filter_by(project_id=project_id).order_by(Log.timestamp.desc()).all()

    # TL can see only the logs related to their team
    elif current_user.role == 'TL':
        if project.tl_id != current_user.id:
            flash('Access denied: You do not have permission to view these logs.', 'danger')
            return redirect(url_for('home'))
        logs = Log.query.filter_by(project_id=project_id).order_by(Log.timestamp.desc()).all()

    # R&D can see only the logs related to their team
    elif current_user.role == 'R&D':
        if project.team_members.filter_by(id=current_user.id).first() is None:
            flash('Access denied: You do not have permission to view these logs.', 'danger')
            return redirect(url_for('home'))
        logs = Log.query.join(Project).filter(
            Project.id == project_id,
            Project.team_members.any(User.id == current_user.id)
        ).order_by(Log.timestamp.desc()).all()

    else:
        flash('Access denied: You do not have permission to view these logs.', 'danger')
        return redirect(url_for('home'))

    return render_template('project_logs.html', project=project, logs=logs)



@app.route('/rnd/home')
@login_required
def rnd_home():
    """
    Shows the R&D home page with assigned tasks and team information.

    - Only accessible by admin, CTO, TL, and R&D users.
    """
    if current_user.role not in ['admin', 'CTO', 'TL', 'R&D']:
        return 'Access denied'

    projects = Project.query.join(project_team_members).filter(project_team_members.c.user_id == current_user.id).all()
    team_members = User.query.filter_by(team_id=current_user.team_id, role='R&D').all()
    tasks = Task.query.filter_by(assignee_id=current_user.id).all()

    return render_template('rnd/home.html', projects=projects, team_members=team_members, tasks=tasks)


@app.route('/rnd/task_queue')
@login_required
def task_queue():
    """
    Shows the queue of open tasks for R&D members.

    - Only accessible by R&D users.
    """

    if current_user.role != 'R&D' and current_user.role != 'admin':
        return 'Access denied'

    # Get project IDs for projects the user is a member of
    user_project_ids = [project.id for project in current_user.projects]

    # Filter open tasks by projects the user is associated with
    open_tasks = Task.query.filter(Task.status == 'open', Task.assignee_id.is_(None), Task.project_id.in_(user_project_ids)).order_by(Task.opened_at).all()

    return render_template('rnd/task_queue.html', open_tasks=open_tasks)



@app.route('/rnd/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task_status(task_id):
    """
    Toggles the status of a task between open and closed.

    - Only accessible by the assigned R&D member.
    """
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id:
        return 'Access denied'

    old_status = task.status  # שמירת הסטטוס הקודם
    task.status = 'closed' if task.status == 'open' else 'open'
    task.closed_at = datetime.utcnow() if task.status == 'closed' else None
    db.session.commit()

    # הוספת לוג לשינוי סטטוס המשימה
    add_log(task.project_id, current_user.id, f'Task "{task.name}" status changed from "{old_status}" to "{task.status}" by {current_user.username}.')

    notify_team_members(task.project_id, f'Task "{task.name}" status changed to {task.status} by {current_user.username}.')
    flash(f'Task "{task.name}" status updated to {task.status}.', 'success')

    return redirect(url_for('rnd_home'))


@app.route('/rnd/return_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def return_task(task_id):
    """
    Returns a task to the task queue with a reason.

    - Only accessible by the assigned R&D member.
    - GET: Shows form to return the task.
    - POST: Returns the task with a specified reason.
    """
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id:
        return 'Access denied'

    if request.method == 'POST':
        reason = request.form['reason']
        task.assignee_id = None
        db.session.commit()

        # הוספת לוג להחזרת המשימה
        add_log(task.project_id, current_user.id, f'Task "{task.name}" returned by {current_user.username}. Reason: {reason}')

        notify_team_members(task.project_id, f'Task "{task.name}" returned by {current_user.username}. Reason: {reason}')
        flash(f'Task "{task.name}" returned successfully.', 'success')
        return redirect(url_for('rnd_home'))

    return render_template('rnd/return_task.html', task=task)


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    """
    Handles the chat functionality.

    - Accessible by all authenticated users.
    - GET: Shows chat interface.
    - POST: Sends a new chat message.
    """
    team_members = User.query.filter_by(team_id=current_user.team_id).all()
    other_users = User.query.filter(User.team_id != current_user.team_id).all()

    if request.method == 'POST':
        receiver_id = request.form['receiver_id']
        message_text = request.form['message']
        message = Message(sender_id=current_user.id, receiver_id=receiver_id, message=message_text)
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('chat'))

    return render_template('chat.html', team_members=team_members, other_users=other_users)



@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat_with_user(user_id):
    """
    Handles private chat between two users.

    - Accessible by all authenticated users.
    - GET: Shows chat interface with specific user.
    - POST: Sends a new chat message or clears chat history.
    """
    user = User.query.get_or_404(user_id)

    if user_id == current_user.id:
        flash("You cannot chat with yourself.", "danger")
        return redirect(url_for('chat'))

    if request.method == 'POST':
        if 'message' in request.form:
            message_text = request.form['message']
            if message_text.strip():
                message = Message(sender_id=current_user.id, receiver_id=user_id, message=message_text.strip())
                db.session.add(message)
                db.session.commit()
                flash('Message sent successfully!', 'success')
        elif 'clear_chat' in request.form:
            Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
            ).delete()
            db.session.commit()
            flash('Chat cleared successfully!', 'success')
        return redirect(url_for('chat_with_user', user_id=user_id))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    return render_template('chat_with_user.html', messages=messages, user=user)

@app.route('/switch_role/<role>')
@login_required
def switch_role(role):
    if current_user.role == 'admin':
        if role in ['admin', 'TL', 'CTO', 'R&D']:
            session['selected_role'] = role
            flash(f'נבחר תפקיד: {role}', 'success')
        else:
            flash('תפקיד לא תקין.', 'danger')
    return redirect(url_for('home'))



@app.route('/my_project_logs', methods=['GET'])
@login_required
def my_project_logs():
    """
    מציג את כל הלוגים של הפרויקטים שקשורים למשתמש הנוכחי בהתאם לתפקידו.
    """
    if current_user.role == 'admin' or current_user.role == 'CTO':
        # Admin ו-CTO רואים את כל הלוגים
        logs = Log.query.order_by(Log.timestamp.desc()).all()
    elif current_user.role == 'TL':
        # TL רואה את הלוגים של הצוות שלו
        logs = Log.query.join(Project).join(project_team_members).filter(
            Project.tl_id == current_user.id
        ).order_by(Log.timestamp.desc()).all()
    elif current_user.role == 'R&D':
        # R&D רואה את הלוגים של הצוות שלו
        logs = Log.query.join(Project).join(project_team_members).filter(
            Project.team_members.any(User.team_id == current_user.team_id)
        ).order_by(Log.timestamp.desc()).all()
    else:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    return render_template('my_project_logs.html', logs=logs)




@app.route('/chat/mark_as_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """
    Marks a notification as read.

    - Accessible by all authenticated users.
    """
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return 'Access denied'
    notification.read = True
    db.session.commit()
    return redirect(url_for('notifications'))


#BSPMS2429-160
def get_gpt_feedback_and_score(code, subject,testHelp = 0):
    """
    Uses OpenAI GPT to provide feedback on the code in English, including a score,
    and then detailed feedback and proposed code changes if necessary.
    Additionally, it creates a performance report and saves it to the database.

    :param code: The code to review as a string.
    :param subject: The subject for feedback (e.g., 'Security', 'Consistency', 'General').
    :return: A tuple containing the feedback in English, the score, and the updated code.
    """
    prompt = f"You are an expert Python developer specializing in {subject}. Please review the following code and provide: \n1. A score between 1 and 10 based on {subject}. \n2. A score between 1 and 10 based on PEP8 compliance. \n3. A brief explanation of the scores. \n4. Any necessary changes to the code, with explanations. Please provide the score first, followed by the feedback.\n\n{code}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    feedback = response.choices[0].message['content']
    score = extract_score(feedback)
    updated_code = extract_code(feedback)

    # Create and save the report associated with the current user and their team
    if testHelp == 1:
        return feedback, 8, updated_code

    if current_user.is_authenticated:
        new_report = PerformanceReport(
            user_id=current_user.id,
            team_id=current_user.team_id,
            code_snippet=code,
            report=feedback
        )
        db.session.add(new_report)
        db.session.commit()

    return feedback, score, updated_code


def extract_score(content):
    """
    Extracts the PEP8 score from the first line in the content that contains 'PEP8'.
    The score is expected to be a number between 1 and 10.

    :param content: The string content returned by the AI.
    :return: The extracted score as an integer, or None if no valid score is found.
    """
    lines = content.splitlines()

    for line in lines:
        if 'PEP8' in line.upper():
            match = re.search(r'((\d{1,2})(?:/10)?)$', line)
            if match:
                try:
                    score = int(match.group(1))
                except ValueError:
                    score = int(match.group(1).split('/')[0])
                if 1 <= score <= 10:
                    return score

    return None

def extract_code(content):
    """
    Extracts code from the content returned by the AI.
    :param content: The string content returned by the AI.
    :return: The suggested code if found, otherwise None.
    """
    code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return None


@app.route('/rate_security', methods=['GET', 'POST'])
@login_required
def rate_security():
    if request.method == 'POST':
        code_input = request.form['code_input']
        feedback, score, updated_code = get_gpt_feedback_and_score(code_input, 'Security')

        if score is not None and current_user.is_authenticated:
            new_rating = Rating(user_id=current_user.id, subject='Security', score=score)
            db.session.add(new_rating)
            db.session.commit()
            return render_template('rnd/rate_security.html', score=score, feedback=feedback, updated_code=updated_code)

    return render_template('rnd/rate_security.html')

@app.route('/rate_consistency', methods=['GET', 'POST'])
@login_required
def rate_consistency():
    if request.method == 'POST':
        code_input = request.form['code_input']
        feedback, score, updated_code = get_gpt_feedback_and_score(code_input, 'Consistency')

        if score is not None and current_user.is_authenticated:
            new_rating = Rating(user_id=current_user.id, subject='Consistency', score=score)
            db.session.add(new_rating)
            db.session.commit()
            team_id = current_user.team_id
            team_ratings = Rating.query.join(User).filter(User.team_id == team_id,
                                                          Rating.subject == 'Consistency').all()
            team_average = sum(r.score for r in team_ratings) / len(team_ratings) if team_ratings else None
            return render_template('rnd/rate_consistency.html', score=score, feedback=feedback,
                                   team_average=team_average, updated_code=updated_code)

    return render_template('rnd/rate_consistency.html')


@app.route('/rate_code', methods=['GET', 'POST'])
@login_required
def rate_code():
    if request.method == 'POST':
        code_input = request.form['code_input']
        feedback, score, updated_code = get_gpt_feedback_and_score(code_input, 'General')

        if score is not None and current_user.is_authenticated:
            # Save the score in the database
            new_rating = Rating(user_id=current_user.id, subject='General', score=score)
            db.session.add(new_rating)
            db.session.commit()

            # Calculate the user's average score for general code quality
            user_ratings = Rating.query.filter_by(user_id=current_user.id, subject='General').all()
            user_average = sum(r.score for r in user_ratings) / len(user_ratings) if user_ratings else None

            # Render the template with the score, feedback, user average, and updated code
            return render_template('rnd/rate_code.html', score=score, feedback=feedback, user_average=user_average, updated_code=updated_code)

    # If the request is GET or there's no score, render the form
    return render_template('rnd/rate_code.html')


def add_log(project_id, user_id, message):
    """
    Adds a log entry for a project.

    :param project_id: ID of the project.
    :param user_id: ID of the user making the log entry.
    :param message: Log message.
    """
    log = Log(project_id=project_id, user_id=user_id, message=message)
    db.session.add(log)
    db.session.commit()


def notify_team_members(project_id, message):
    """
    Sends a notification to all team members of a project.

    :param project_id: ID of the project.
    :param message: Notification message.
    """
    project = Project.query.get(project_id)
    team_members = project.team_members
    for member in team_members:
        notification = Notification(user_id=member.id, message=message)
        db.session.add(notification)
    db.session.commit()

@app.route('/project/<int:project_id>/details', methods=['GET'])
@login_required
def project_details(project_id):
    """
    Returns the HTML for the project details.

    - Only accessible by authorized users.
    """
    project = Project.query.get_or_404(project_id)
    return render_template('project_details.html', project=project)




@app.route('/project/<int:project_id>/edit_description', methods=['GET', 'POST'])
@login_required
def edit_project_description(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        old_description = project.description  # שמירת התיאור הישן
        project.description = request.form['description']
        db.session.commit()

        # הוספת לוג לשינוי תיאור הפרויקט
        add_log(project.id, current_user.id, f'Project description updated by {current_user.username}. Old description: "{old_description}", New description: "{project.description}".')

        flash('Project description updated successfully.', 'success')
        return redirect(url_for('manage_project', project_id=project.id))
    return render_template('edit_project_description.html', project=project)




@app.route('/marketing/home')
@login_required
def marketing_home():
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    marketing_projects = MarketingProject.query.all()
    campaigns = Campaign.query.all()
    leads = Client.query.all()
    presentations = Presentation.query.all()

    return render_template(
        'marketing/home.html',
        marketing_projects=marketing_projects,
        campaigns=campaigns,
        leads=leads,
        presentations=presentations
    )


@app.route('/project/modify/<int:project_id>', methods=['GET', 'POST'])
@login_required
def modify_project(project_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('marketing_home'))

    # Fetch the project to edit
    project = MarketingProject.query.get_or_404(project_id)
    clients = Client.query.all()  # Fetch clients to select from

    if request.method == 'POST':
        # Update project details
        project.name = request.form.get('name')
        project.client_id = request.form.get('client_id')
        project.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        project.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        project.objectives = request.form.get('objectives')
        project.google_drive_link = request.form.get('google_drive_link')

        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('marketing_project_details', project_id=project_id))

    return render_template('marketing/edit_project.html', project=project, clients=clients)


@app.route('/marketing/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_marketing_project(project_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    project = MarketingProject.query.get_or_404(project_id)

    if request.method == 'POST':
        # Handle feedback submission
        feedback_content = request.form['feedback_content']
        campaign_id = request.form['campaign_id']
        feedback = Feedback(
            campaign_id=campaign_id,
            user_id=current_user.id,
            content=feedback_content
        )
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('view_marketing_project', project_id=project.id))

    return render_template('marketing/view_marketing_project.html', project=project)


@app.route('/marketing/clients')
@login_required
def marketing_clients():
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    potential_clients = Client.query.filter_by(potential=True).all()
    existing_clients = Client.query.filter_by(potential=False).all()

    return render_template('marketing/clients.html', potential_clients=potential_clients, existing_clients=existing_clients)

@app.route('/marketing/create_project', methods=['GET', 'POST'])
@login_required
def create_marketing_project():
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    clients = Client.query.all()  # Fetch clients to select from in the form
    marketing_projects = MarketingProject.query.all()  # Fetch existing marketing projects for campaign creation

    if request.method == 'POST' and 'project_name' in request.form:
        # Handle Marketing Project Creation
        name = request.form.get('project_name')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        objectives = request.form.get('objectives')
        google_drive_link = request.form.get('google_drive_link')
        client_id = request.form.get('client_id')  # Client selection

        # Convert date strings to datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format for project.', 'danger')
            return redirect(url_for('create_marketing_project'))

        # Create a new MarketingProject object
        new_project = MarketingProject(
            name=name,
            creator_id=current_user.id,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            objectives=objectives,
            google_drive_link=google_drive_link
        )

        db.session.add(new_project)
        db.session.commit()

        flash('Marketing project created successfully!', 'success')
        return redirect(url_for('marketing_home'))

    return render_template('marketing/create_project.html', clients=clients, marketing_projects=marketing_projects)


@app.route('/marketing/create_campaign', methods=['POST'])
@login_required
def create_campaign():
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    if request.method == 'POST' and 'campaign_name' in request.form:
        # Handle Campaign Creation
        name = request.form.get('campaign_name')
        marketing_project_id = request.form.get('marketing_project_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        target_audience = request.form.get('target_audience')
        channels = request.form.get('channels')
        link = request.form.get('link')
        budget = float(request.form.get('budget', 0))  # Convert to float with default 0
        actual_expenses = float(request.form.get('actual_expenses', 0))
        expected_expenses = float(request.form.get('expected_expenses', 0))

        # Convert date strings to datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format for campaign.', 'danger')
            return redirect(url_for('create_marketing_project'))

        # Create a new Campaign object
        new_campaign = Campaign(
            name=name,
            marketing_project_id=marketing_project_id,
            start_date=start_date,
            end_date=end_date,
            target_audience=target_audience,
            channels=channels,
            link=link,
            budget=budget,
            actual_expenses=actual_expenses,
            expected_expenses=expected_expenses
        )

        db.session.add(new_campaign)
        db.session.commit()

        flash('Campaign created successfully!', 'success')
        return redirect(url_for('marketing_home'))


@app.route('/marketing/project_details/<int:project_id>', methods=['GET'])
@login_required
def marketing_project_details(project_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    project = MarketingProject.query.get_or_404(project_id)
    campaigns = Campaign.query.filter_by(marketing_project_id=project.id).all()

    return render_template('marketing/project_details.html', project=project, campaigns=campaigns)


@app.route('/campaign/<int:campaign_id>/comments', methods=['GET', 'POST'])
@login_required
def campaign_comments(campaign_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    campaign = Campaign.query.get_or_404(campaign_id)
    comments = Comment.query.filter_by(campaign_id=campaign.id).all()

    if request.method == 'POST':
        comment_content = request.form.get('comment')
        if comment_content:
            new_comment = Comment(
                campaign_id=campaign.id,
                user_id=current_user.id,
                content=comment_content
            )
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
        return redirect(url_for('campaign_comments', campaign_id=campaign_id))

    return render_template('marketing/campaign_comments.html', campaign=campaign, comments=comments)




@app.route('/campaign/delete/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    # Check if the user has the necessary permissions to delete
    if current_user.role != 'marketing' and current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('marketing_home'))

    # Find the campaign by ID
    campaign = Campaign.query.get_or_404(campaign_id)

    # Delete the campaign
    db.session.delete(campaign)
    db.session.commit()

    flash('Campaign deleted successfully!', 'success')
    return redirect(url_for('marketing_project_details', project_id=campaign.marketing_project_id))

@app.route('/marketing/client/<int:client_id>', methods=['GET'])
@login_required
def view_client(client_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    client = Client.query.get_or_404(client_id)
    return render_template('marketing/client_detail.html', client=client)

@app.route('/marketing/update_client/<int:client_id>', methods=['POST'])
@login_required
def update_client(client_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    client = Client.query.get_or_404(client_id)
    client.name = request.form.get('name')
    client.mobile_number = request.form.get('mobile_number')
    client.email = request.form.get('email')
    client.address = request.form.get('address')
    client.company = request.form.get('company')
    client.payment_method = request.form.get('payment_method')
    client.notes = request.form.get('notes')
    client.potential = request.form.get('potential') == 'true'
    db.session.commit()

    flash('Client details updated successfully!', 'success')
    return redirect(url_for('view_client', client_id=client_id))

@app.route('/marketing/delete_client/<int:client_id>', methods=['GET'])
@login_required
def delete_client(client_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()

    flash('Client deleted successfully!', 'success')
    return redirect(url_for('marketing_clients'))

@app.route('/add_client', methods=['POST'])
@login_required
def add_client():
    name = request.form.get('name')
    mobile_number = request.form.get('mobile_number')
    email = request.form.get('email')
    address = request.form.get('address')
    company = request.form.get('company')
    payment_method = request.form.get('payment_method')
    notes = request.form.get('notes')
    potential = request.form.get('potential') == '1'

    new_client = Client(
        name=name,
        mobile_number=mobile_number,
        email=email,
        address=address,
        company=company,
        payment_method=payment_method,
        notes=notes,
        potential=potential
    )

    db.session.add(new_client)
    db.session.commit()

    flash('Client added successfully!', 'success')
    return redirect(url_for('client_management'))  # Redirect to the client management page

@app.route('/client_management')
@login_required
def client_management():
    # Fetch clients based on their potential status
    potential_clients = Client.query.filter_by(potential=True).all()
    existing_clients = Client.query.filter_by(potential=False).all()

    return render_template(
        'marketing/clients.html',
        potential_clients=potential_clients,
        existing_clients=existing_clients
    )


@app.route('/marketing/campaign/<int:campaign_id>', methods=['GET'])
@login_required
def view_campaign(campaign_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    campaign = Campaign.query.get_or_404(campaign_id)

    return render_template('marketing/view_campaign.html', campaign=campaign)


@app.route('/marketing/campaign/edit/<int:campaign_id>', methods=['POST'])
@login_required
def edit_campaign(campaign_id):
    if current_user.role != 'marketing' and current_user.role != 'admin':
        return 'Access denied'

    campaign = Campaign.query.get_or_404(campaign_id)

    # Update campaign details
    campaign.name = request.form.get('campaign_name')
    campaign.start_date = datetime.strptime(request.form.get('campaign_start_date'), '%Y-%m-%d')
    campaign.end_date = datetime.strptime(request.form.get('campaign_end_date'), '%Y-%m-%d')
    campaign.target_audience = request.form.get('target_audience')
    campaign.channels = request.form.get('channels')
    campaign.budget = float(request.form.get('budget'))
    campaign.actual_expenses = float(request.form.get('actual_expenses'))
    campaign.expected_expenses = float(request.form.get('expected_expenses'))

    db.session.commit()
    flash('Campaign updated successfully!', 'success')
    return redirect(url_for('view_campaign', campaign_id=campaign.id))

# viewer <---- משתמשים מסוג

@app.route('/viewer/home', methods=['GET', 'POST'])
@login_required
def viewer_home():
    if current_user.role != 'viewer':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    team_members = User.query.filter(User.role == 'admin').all()
    messages = []
    selected_user = None

    if 'receiver_id' in request.args:
        receiver_id = request.args.get('receiver_id', type=int)
        selected_user = User.query.get(receiver_id)

        if selected_user:
            messages = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == selected_user.id)) |
                ((Message.sender_id == selected_user.id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.timestamp.desc()).all()  # מיון בסדר יורד

    return render_template('viewer/home.html', team_members=team_members, messages=messages, selected_user=selected_user)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """
    שליחת הודעה למשתמש נבחר דרך AJAX.
    """
    receiver_id = request.form['receiver_id']
    message_text = request.form['message']

    receiver = User.query.get(receiver_id)
    if receiver:
        message = Message(sender_id=current_user.id, receiver_id=receiver_id, message=message_text)
        db.session.add(message)
        db.session.commit()

        # עדכון ההודעות לאחר שליחה
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver.id)) |
            ((Message.sender_id == receiver.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp).all()

        messages_html = ''.join([
            f'<li class="list-group-item{" text-right" if message.sender_id == current_user.id else ""}">'
            f'<strong>{message.sender.username}:</strong> {message.message}'
            f'</li>' for message in messages
        ])

        return jsonify({'messages': messages_html, 'receiver_name': receiver.username})
    else:
        return jsonify({'error': 'Receiver not found'}), 404

@app.route('/load_messages', methods=['GET'])
@login_required
def load_messages():
    receiver_id = request.args.get('receiver_id', type=int)
    order = request.args.get('order', default='asc', type=str)
    receiver = User.query.get(receiver_id)

    if receiver:
        if order == 'asc':
            messages = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver.id)) |
                ((Message.sender_id == receiver.id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.timestamp.asc()).all()  # מיון בסדר עולה
        else:
            messages = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver.id)) |
                ((Message.sender_id == receiver.id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.timestamp.desc()).all()  # מיון בסדר יורד

        messages_html = ''.join([
            f'<li class="list-group-item{" text-right" if message.sender_id == current_user.id else ""}">'
            f'<strong>{message.sender.username}:</strong> {message.message}'
            f'</li>' for message in messages
        ])

        return jsonify({'messages': messages_html, 'receiver_name': receiver.username})
    else:
        return jsonify({'error': 'Receiver not found'}), 404

# Report
def get_gpt_performance_report(code):
    """
    Uses OpenAI GPT to provide a performance report for the code, including suggestions for optimization,
    and detailed feedback on potential performance bottlenecks.

    :param code: The code to review as a string.
    :return: A string containing the performance report.
    """
    prompt = f"You are an expert in optimizing Python code for performance. Please analyze the following code and provide: \n1. Identification of any performance bottlenecks. \n2. Suggestions for optimization. \n3. A brief explanation of why the optimizations are important.\n\n{code}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    performance_report = response.choices[0].message['content']
    return performance_report


@app.route('/rate_performance', methods=['GET', 'POST'])
@login_required
def rate_performance():
    """
    Route for rating and getting feedback on the performance of code.

    - Accessible by authenticated users.
    - GET: Shows form to input code.
    - POST: Processes the code, rates its performance, and provides feedback.
    """
    if request.method == 'POST':
        code_input = request.form['code_input']
        performance_report = get_gpt_performance_report(code_input)

        # Create and save the report associated with the current user and their team
        new_report = PerformanceReport(
            user_id=current_user.id,
            team_id=current_user.team_id,
            code_snippet=code_input,
            report=performance_report
        )
        db.session.add(new_report)
        db.session.commit()

        return render_template('performance_report.html', performance_report=performance_report)

    return render_template('rate_performance.html')

@app.route('/performance_reports')
@login_required
def performance_reports():
    """
    Displays performance reports based on user role.
    - R&D: Can see only their own reports.
    - TL: Can see reports of all team members.
    - CTO and admin: Can see all reports.
    """
    if current_user.role == 'R&D':
        reports = PerformanceReport.query.filter_by(user_id=current_user.id).all()
    elif current_user.role == 'TL':
        reports = PerformanceReport.query.filter_by(team_id=current_user.team_id).all()
    elif current_user.role in ['CTO', 'admin']:
        reports = PerformanceReport.query.all()
    else:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    return render_template('view_performance_reports.html', reports=reports)



if __name__ == '__main__':
    app.run(debug=True)

