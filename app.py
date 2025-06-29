from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Use env var or fallback

# MySQL configuration from environment variables
db_config = {
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', ''),
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'database': os.environ.get('MYSQLDATABASE', 'heart_tracker'),
    'port': os.environ.get('MYSQLPORT', 3306)
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        flash(f'Database connection error: {str(err)}', 'error')
        return None

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('tracker'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        roll_number = request.form['roll_number']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('login'))
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE roll_number = %s', (roll_number,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('tracker'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        roll_number = request.form['roll_number']
        class_name = request.form['class']
        phone_number = request.form['phone_number']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))
        
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('signup'))
        
        try:
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (name, password, roll_number, class_name, phone_number)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, hashed_password, roll_number, class_name, phone_number))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {str(err)}', 'error')
            cursor.close()
            conn.close()
    
    return render_template('signup.html')

@app.route('/tracker', methods=['GET', 'POST'])
def tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('login'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Fetch user details and submission status
    cursor.execute('SELECT name, roll_number, class_name, phone_number, is_submitted FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        conn.close()
        session.pop('user_id', None)
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Fetch user's selections
    cursor.execute('SELECT disease, symptom, priority FROM selections WHERE user_id = %s', (session['user_id'],))
    selections = {f"{row['disease']}::{row['symptom']}": row['priority'] for row in cursor.fetchall()}
    
    if request.method == 'POST' and not user['is_submitted']:
        # Clear existing selections for the user
        cursor.execute('DELETE FROM selections WHERE user_id = %s', (session['user_id'],))
        
        # Save new selections with user details
        for key, priority in request.form.items():
            if key.startswith('priority_') and priority != '--':
                disease, symptom = key.replace('priority_', '').split('::')
                cursor.execute('''
                    INSERT INTO selections (user_id, name, roll_number, class_name, phone_number, disease, symptom, priority)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (session['user_id'], user['name'], user['roll_number'], user['class_name'], user['phone_number'], disease, symptom, int(priority)))
        
        # Mark user as submitted
        cursor.execute('UPDATE users SET is_submitted = TRUE WHERE id = %s', (session['user_id'],))
        conn.commit()
        flash('Selections saved successfully! You can no longer modify your choices.', 'success')
    
    cursor.close()
    conn.close()
    
    return render_template('tracker.html', selections=selections, is_submitted=user['is_submitted'])

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
