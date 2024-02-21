from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import re
from main import app, db
from models import User, Task

@app.route('/')
def home():
    try:
        if current_user.name:
            return redirect(url_for('tasks'))
    except:
        return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

        if not email_regex.match(email):
            flash("Enter a valid email address.")
            return redirect(url_for('login'))
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('login'))

        if not user:
            flash("The email does not exist.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Incorrect password.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect('tasks')
    
    try:
        if current_user.name:
            return redirect(url_for('tasks'))
    except:
        return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        
        email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

        if len(name) < 3:
            flash("Name must be at least 3 characters.")
            return redirect(url_for('register'))
        elif not email_regex.match(email):
            flash("Enter a valid email address.")
            return redirect(url_for('register'))
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('register'))
        
        hash_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=email,
            name=name,
            password=hash_password,
            plan=0,
            task_counter=0
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for('tasks'))
    
    try:
        if current_user.name:
            return redirect(url_for('tasks'))
    except:
        return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/tasks', methods=["GET", "POST"])
@login_required
def tasks():
    name = current_user.name
    plan = current_user.plan
    tasks = db.session.execute(db.select(Task).where(Task.user_id == current_user.id))
    tasks = tasks.scalars()
    return render_template('tasks.html', name=name, tasks=tasks, plan=plan)

@app.route('/tasks/add', methods=["GET", "POST"])
@login_required
def add_task():
    if current_user.plan == 1 or current_user.task_counter < 20:
        new_task = Task(
            content=request.form.get('content'),
            user_id=current_user.id
        )
        current_user.task_counter += 1

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for('tasks'))
    else:
        flash("You reached task limit for your plan. Buy premium or go away.")
        return redirect(url_for('tasks'))

@app.route('/tasks/delete/<id>', methods=["GET", "POST"])
@login_required
def delete_task(id):
    task = db.session.execute(db.select(Task).where(Task.id == id))
    task = task.scalar()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/password', methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        new_password = request.form.get('password')

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('password'))

        hash_password = generate_password_hash(
            new_password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        current_user.password = hash_password
        db.session.commit()
        return redirect(url_for('tasks'))

    return render_template('password.html', name=current_user.name, plan=current_user.plan)

@app.route('/statistics')
@login_required
def statistics():
    
        tasks = db.session.execute(db.select(Task).where(Task.user_id == current_user.id))
        tasks = tasks.scalars()
        tasks_number = 0
        if current_user.plan == 0:
            limit=20
        else:
            limit=-1
        for task in tasks:
            tasks_number += 1
        all_tasks = db.session.execute(db.select(Task))
        all_tasks = all_tasks.scalars()
        all_tasks_counter = 0
        for task in all_tasks:
            all_tasks_counter += 1
        limit = all_tasks_counter
        return render_template('statistics.html', tasks=tasks_number, name=current_user.name, limit=limit, plan=current_user.plan)

@app.route('/premium', methods=["GET", "POST"])
@login_required
def premium():
    if current_user.plan == 1:
        flash('You already have premium plan. Thank you!')
        return redirect(url_for('tasks'))
    if request.method == "POST":
        current_user.plan = 1
        db.session.commit()
        flash('Thank you for buying premium!')
        return redirect(url_for('tasks'))

    return render_template('premium.html', name=current_user.name, plan=current_user.plan)

@app.route('/forward/<id>', methods=["GET", "POST"])
@login_required
def forward(id):
    if request.method == "POST":
        try:
            email = request.form.get('email')
            task = db.session.execute(db.select(Task).where(Task.id == id))
            task = task.scalar()
            user_to_forward = db.session.execute(db.select(User).where(User.email == email))
            user_to_forward.scalar()
            task.user_id = user_to_forward.id
            db.session.commit()
            flash('Task forwarded successfully')
            return redirect(url_for('tasks'))
        except:
            flask('Something went wrong')
            return redirect(url_for('tasks'))

    return render_template('forward.html', name=current_user.name, plan=current_user.plan, id=id)


if __name__ == "__main__":
    app.run(debug=True)
