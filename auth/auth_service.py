from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
import time

app = Flask(__name__)

# Database connection config
DB_CONFIG = {
    'host': 'database',
    'user': 'novels_user',
    'password': 'novels_pass',
    'database': 'novels_db',
    'port': 3306
}

def get_db_connection():
    """Get MySQL connection with retry"""
    max_retries = 20
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"⚠️ DB connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database initialized!")

@app.route('/health', methods=['GET'])
def health():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({'status': 'healthy'}), 200
        return jsonify({'status': 'unhealthy'}), 500
    except:
        return jsonify({'status': 'unhealthy'}), 500

@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 500
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 500
        
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password_hash FROM users WHERE username = %s',
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            return jsonify({
                'success': True,
                'user_id': user[0],
                'username': user[1],
                'message': 'Login successful'
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({'service': 'Auth Service', 'status': 'running'})

if __name__ == '__main__':
    print("⏳ Waiting for database...")
    # Wait for MySQL to be ready
    time.sleep(30)
    init_db()
    print("🚀 Auth Service running on port 5001...")
    app.run(debug=False, host='0.0.0.0', port=5001)
