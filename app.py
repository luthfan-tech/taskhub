import sqlite3
from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_developer_key_luthfan"
DB_NAME = "task_manager.db"

# ==============================================================================
# DATABASE SETUP
# ==============================================================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Users Table (Secure Password Hashing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Tasks Table linked to Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

# ==============================================================================
# FRONTEND UI (Tailwind CSS, Dashboard, Filters, and Modals)
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950 text-slate-100">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Luthfan's Task Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="h-full flex flex-col font-sans">

    <nav class="border-b border-slate-800 bg-slate-900 px-6 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-3">
            <span class="text-2xl">⚡</span>
            <span class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">Task Hub CLI-Web v1.0</span>
        </div>
        {% if logged_in %}
        <div class="flex items-center space-x-4">
            <span class="text-slate-400">Welcome, <strong class="text-emerald-400">{{ username }}</strong></span>
            <a href="/logout" class="px-3 py-1.5 text-xs font-semibold rounded bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800 transition">Log Out</a>
        </div>
        {% endif %}
    </nav>

    <main class="flex-grow p-6 max-w-6xl w-full mx-auto">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, msg in messages %}
              <div class="mb-4 p-4 rounded text-sm {% if category == 'error' %} bg-rose-950 text-rose-300 border border-rose-800 {% else %} bg-emerald-950 text-emerald-300 border border-emerald-800 {% endif %}">
                  {{ msg }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if not logged_in %}
        <div class="max-w-md mx-auto mt-16 bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
            <h2 class="text-2xl font-bold mb-6 text-center text-slate-100">Access Portal</h2>
            
            <form action="/auth" method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Username</label>
                    <input type="text" name="username" required class="w-full bg-slate-950 border border-slate-800 rounded px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Password</label>
                    <input type="password" name="password" required class="w-full bg-slate-950 border border-slate-800 rounded px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
                </div>
                <div class="grid grid-cols-2 gap-4 pt-4">
                    <button type="submit" name="action" value="login" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 rounded transition">Log In</button>
                    <button type="submit" name="action" value="register" class="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2 rounded border border-slate-700 transition">Register</button>
                </div>
            </form>
        </div>

        {% else %}
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 h-fit">
                <h3 class="text-lg font-bold mb-4 text-emerald-400">⚡ Add New Task</h3>
                <form action="/add" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Task Title</label>
                        <input type="text" name="task_name" required placeholder="What needs doing?" class="w-full bg-slate-950 border border-slate-800 rounded px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Priority</label>
                        <select name="priority" class="w-full bg-slate-950 border border-slate-800 rounded px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
                            <option value="Low">🟢 Low</option>
                            <option value="Medium" selected>🟡 Medium</option>
                            <option value="High">🔴 High</option>
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 rounded transition">Create Task</button>
                </form>
            </div>

            <div class="md:col-span-2 space-y-4">
                
                <div class="flex space-x-2 bg-slate-900 p-2 rounded-lg border border-slate-800 w-fit">
                    <a href="/" class="px-4 py-1.5 rounded text-sm transition {% if current_filter == 'All' %} bg-emerald-600 text-white {% else %} text-slate-400 hover:text-slate-100 {% endif %}">All</a>
                    <a href="/?filter=Pending" class="px-4 py-1.5 rounded text-sm transition {% if current_filter == 'Pending' %} bg-emerald-600 text-white {% else %} text-slate-400 hover:text-slate-100 {% endif %}">Pending</a>
                    <a href="/?filter=Completed" class="px-4 py-1.5 rounded text-sm transition {% if current_filter == 'Completed' %} bg-emerald-600 text-white {% else %} text-slate-400 hover:text-slate-100 {% endif %}">Completed</a>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    {% if not tasks %}
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
                        No tasks found. Get started by adding one!
                    </div>
                    {% endif %}
                    
                    {% for task in tasks %}
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between hover:border-slate-700 transition">
                        <div class="flex items-center space-x-4">
                            <form action="/complete/{{ task[0] }}" method="POST">
                                <button type="submit" class="w-6 h-6 rounded-full border-2 border-slate-700 flex items-center justify-center hover:border-emerald-500 transition {% if task[3] == 'Completed' %} bg-emerald-500 border-emerald-500 text-white {% endif %}">
                                    {% if task[3] == 'Completed' %}✓{% endif %}
                                </button>
                            </form>
                            <div>
                                <h4 class="font-semibold text-slate-100 {% if task[3] == 'Completed' %} line-through text-slate-500 {% endif %}">{{ task[1] }}</h4>
                                <span class="inline-block text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 mt-1 rounded {% if task[2] == 'High' %} bg-rose-950 text-rose-300 {% elif task[2] == 'Medium' %} bg-amber-950 text-amber-300 {% else %} bg-slate-800 text-slate-300 {% endif %}">
                                    {{ task[2] }} Priority
                                </span>
                            </div>
                        </div>
                        
                        <form action="/delete/{{ task[0] }}" method="POST">
                            <button type="submit" class="text-slate-500 hover:text-rose-400 text-sm font-semibold transition">Delete</button>
                        </form>
                    </div>
                    {% endfor %}
                </div>

            </div>
        </div>
        {% endif %}
    </main>

</body>
</html>
"""

# ==============================================================================
# ROUTING & CONTROLLER LOGIC
# ==============================================================================
@app.route('/')
def index():
    logged_in = 'user_id' in session
    tasks = []
    current_filter = request.args.get('filter', 'All')
    
    if logged_in:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if current_filter == 'All':
                cursor.execute("SELECT id, task_name, priority, status FROM tasks WHERE user_id = ?", (session['user_id'],))
            else:
                cursor.execute("SELECT id, task_name, priority, status FROM tasks WHERE user_id = ? AND status = ?", (session['user_id'], current_filter))
            tasks = cursor.fetchall()
            
    return render_template_string(
        HTML_TEMPLATE, 
        logged_in=logged_in, 
        username=session.get('username', ''), 
        tasks=tasks,
        current_filter=current_filter
    )

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form['username'].strip().lower()
    password = request.form['password']
    action = request.form['action']
    
    if not username or not password:
        flash("Fields cannot be empty!", "error")
        return redirect(url_for('index'))
        
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        if action == 'register':
            try:
                hashed_pw = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
                conn.commit()
                flash("Registration successful! You can now log in.", "success")
            except sqlite3.IntegrityError:
                flash("Username is already taken!", "error")
                
        elif action == 'login':
            cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['username'] = username
                flash("Logged in successfully!", "success")
            else:
                flash("Invalid login credentials!", "error")
                
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    task_name = request.form['task_name'].strip()
    priority = request.form['priority']
    
    if task_name:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (user_id, task_name, priority) VALUES (?, ?, ?)", 
                           (session['user_id'], task_name, priority))
            conn.commit()
            flash("Task added!", "success")
            
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Verify ownership first
        cursor.execute("SELECT status FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
        task = cursor.fetchone()
        if task:
            new_status = 'Pending' if task[0] == 'Completed' else 'Completed'
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            conn.commit()
            
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
        conn.commit()
        flash("Task deleted.", "success")
        
    return redirect(url_for('index'))

# ==============================================================================
# ENTRYPOINT
# ==============================================================================
if __name__ == '__main__':
    init_db()
    print("\n🚀 Full-Stack App initialized successfully!")
    print("👉 Open http://127.0.0.1:5000 in your browser to test it.")
    app.run(debug=True, port=5000)