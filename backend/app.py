import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

# have founded an error in getting login and sign up files in templates

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production

# Database configuration
DATABASE = 'database/database.db'  # Adjusted path to your user_data folder

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # This allows accessing columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        db.commit()

init_db()

@app.route('/')
def home():
    return redirect(url_for('/templates/login.html'))

@app.route('/templates/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('/templates/login.html'))
    return render_template('/templates/signup.html')

@app.route('/templates/signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)  # New (correct)
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
            db.commit()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('/templates/login.html'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
            return redirect(url_for('/templates/signup.html'))
    return render_template('/templates/signup.html')

@app.route('/templates/dashboard.html')
def dashboard():
    if 'user_id' in session:
        return f"Welcome, {session['username']}! This is your dashboard."
    else:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)