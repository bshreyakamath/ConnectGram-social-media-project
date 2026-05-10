from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "your secret_key_here"

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, email TEXT, bio TEXT, followers INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS follows (follower_id INTEGER, followed_id INTEGER, UNIQUE(follower_id, followed_id))')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, caption TEXT, image_url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, post_id INTEGER, UNIQUE(user_id, post_id))')
    conn.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, post_id INTEGER, content TEXT, username TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()


@app.route('/')
@app.route('/login.html')
def show_login():
    return render_template('login.html')

@app.route('/account.html')
def show_signup():
    return render_template('account.html')

@app.route('/dashboard.html')
def show_dashboard():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('dashboard.html', user=user)

@app.route('/post.html')
def show_post():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    return render_template('post.html')

@app.route('/feed.html')
def show_feed():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, u.username, 
        (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count
        FROM posts p JOIN users u ON p.user_id = u.id 
        ORDER BY p.id DESC
    ''').fetchall()
    comments = conn.execute('SELECT * FROM comments ORDER BY timestamp ASC').fetchall()
    conn.close()
    return render_template('feed.html', posts=posts, comments=comments)

@app.route('/Follow pagee.html')
def show_follow():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    users = conn.execute('''
        SELECT u.*, 
        (SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = u.id) as is_following
        FROM users u WHERE u.id != ?
    ''', (session['user_id'], session['user_id'])).fetchall()
    conn.close()
    return render_template('Follow pagee.html', users=users)

@app.route('/Messaging page.html')
def show_messaging():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    users = conn.execute('SELECT id, username FROM users WHERE id != ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('Messaging page.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_login'))


@app.route('/signup', methods=['POST'])
def signup():
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password, email, bio) VALUES (?, ?, ?, ?)', 
                     (request.form['username'], request.form['password'], request.form['email'], request.form['bio']))
        conn.commit()
        return redirect(url_for('show_login'))
    except: return "Error: Username might already exist."
    finally: conn.close()

@app.route('/login', methods=['POST'])
def login():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                        (request.form['username'], request.form['password'])).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('show_dashboard'))
    return "Login Failed."

@app.route('/add_post', methods=['POST'])
def add_post():
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    conn.execute('INSERT INTO posts (user_id, caption, image_url) VALUES (?, ?, ?)', 
                 (session['user_id'], request.form['caption'], request.form['image_url']))
    conn.commit()
    conn.close()
    return redirect(url_for('show_feed'))


@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    existing = conn.execute('SELECT * FROM likes WHERE user_id = ? AND post_id = ?', (session['user_id'], post_id)).fetchone()
    if existing:
        conn.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (session['user_id'], post_id))
    else:
        conn.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (session['user_id'], post_id))
    conn.commit()
    conn.close()
    return redirect(url_for('show_feed'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: return redirect(url_for('show_login'))
    conn = get_db()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.execute('INSERT INTO comments (user_id, post_id, content, username) VALUES (?, ?, ?, ?)', 
                 (session['user_id'], post_id, request.form['content'], user['username']))
    conn.commit()
    conn.close()
    return redirect(url_for('show_feed'))

@app.route('/toggle_follow/<int:target_id>', methods=['POST'])
def toggle_follow(target_id):
    if 'user_id' not in session: return jsonify({"status": "error"}), 401
    conn = get_db()
    existing = conn.execute('SELECT * FROM follows WHERE follower_id = ? AND followed_id = ?', (session['user_id'], target_id)).fetchone()
    action = ""
    if existing:
        conn.execute('DELETE FROM follows WHERE follower_id = ? AND followed_id = ?', (session['user_id'], target_id))
        conn.execute('UPDATE users SET followers = MAX(0, followers - 1) WHERE id = ?', (target_id,))
        action = "unfollowed"
    else:
        conn.execute('INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)', (session['user_id'], target_id))
        conn.execute('UPDATE users SET followers = followers + 1 WHERE id = ?', (target_id,))
        action = "followed"
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "action": action})


@app.route('/send_message', methods=['POST'])
def handle_send_message():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)', 
                 (session['user_id'], data['receiver_id'], data['content']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/get_messages/<int:other_id>')
def get_messages(other_id):
    if 'user_id' not in session: return jsonify([]), 401
    conn = get_db()
    messages = conn.execute('''
        SELECT content, sender_id FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    ''', (session['user_id'], other_id, other_id, session['user_id'])).fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages])

if __name__ == '__main__':
    app.run(debug=True)