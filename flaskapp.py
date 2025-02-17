import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure database and table exist with filename column
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              username TEXT NOT NULL, 
              password TEXT NOT NULL, 
              firstname TEXT NOT NULL, 
              lastname TEXT NOT NULL, 
              email TEXT NOT NULL, 
              address TEXT,
              word_count INTEGER,
              filename TEXT)''')
conn.commit()
conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    address = request.form['address']

    # Handle file upload
    if 'file' not in request.files:
        return "No file uploaded"
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file type. Only .txt files are allowed."

    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"File saved as: {filename}")  # Debugging line

    # Count words in the uploaded file
    with open(file_path, 'r') as f:
        content = f.read()
        word_count = len(content.split())

    # Insert user data and the filename into the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, firstname, lastname, email, address, word_count, filename) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (username, password, firstname, lastname, email, address, word_count, filename))
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))

@app.route('/profile/<username>')
def profile(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        return render_template('profile.html', user=user)
    else:
        return "User not found."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            return redirect(url_for('profile', username=username))
        else:
            return render_template('login.html', error_message="Invalid username or password. Please try again.")

    return render_template('login.html')

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"Attempting to download: {filepath}")

    if not os.path.exists(filepath):
        return f"File not found: {filepath}", 404

    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
