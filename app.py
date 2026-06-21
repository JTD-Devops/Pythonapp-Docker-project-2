from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import os
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

# Service URLs
AUTH_SERVICE = os.environ.get('AUTH_SERVICE', 'http://auth:5001')
BOOK_SERVICE = os.environ.get('BOOK_SERVICE', 'http://book:5002')
BORROW_SERVICE = os.environ.get('BORROW_SERVICE', 'http://borrow:5003')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = requests.post(
                f'{AUTH_SERVICE}/auth/login',
                json={'username': username, 'password': password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                session['user_id'] = data['user_id']
                session['username'] = data['username']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        except requests.exceptions.ConnectionError:
            flash('Authentication service unavailable', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        try:
            response = requests.post(
                f'{AUTH_SERVICE}/auth/signup',
                json={'username': username, 'email': email, 'password': password},
                timeout=10
            )
            
            if response.status_code == 201:
                flash('Account created! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(response.json().get('message', 'Signup failed'), 'danger')
        except requests.exceptions.ConnectionError:
            flash('Authentication service unavailable. Please try again.', 'danger')
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        books_response = requests.get(f'{BOOK_SERVICE}/books', timeout=10)
        books = books_response.json() if books_response.status_code == 200 else []
    except:
        books = []
    
    try:
        borrow_response = requests.get(f'{BORROW_SERVICE}/borrow/user/{session["user_id"]}', timeout=10)
        borrowed = borrow_response.json() if borrow_response.status_code == 200 else []
    except:
        borrowed = []
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         total_books=len(books),
                         borrowed_count=len(borrowed))

@app.route('/books')
def books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        response = requests.get(f'{BOOK_SERVICE}/books', timeout=10)
        books = response.json() if response.status_code == 200 else []
    except:
        books = []
        flash('Book service unavailable', 'warning')
    
    return render_template('books.html', books=books)

@app.route('/borrow', methods=['POST'])
def borrow_book():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    book_id = request.form.get('book_id')
    
    try:
        book_response = requests.put(
            f'{BOOK_SERVICE}/books/{book_id}/borrow',
            json={'user_id': session['user_id']},
            timeout=10
        )
        
        if book_response.status_code != 200:
            flash('Book not available for borrowing', 'danger')
            return redirect(url_for('books'))
        
        borrow_response = requests.post(
            f'{BORROW_SERVICE}/borrow',
            json={'user_id': session['user_id'], 'book_id': book_id},
            timeout=10
        )
        
        flash('Book borrowed successfully!', 'success')
    except requests.exceptions.ConnectionError:
        flash('Service unavailable', 'danger')
    
    return redirect(url_for('borrowed'))

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        book_response = requests.put(f'{BOOK_SERVICE}/books/{book_id}/return', timeout=10)
        
        if book_response.status_code != 200:
            flash('Error returning book', 'danger')
            return redirect(url_for('borrowed'))
        
        borrow_response = requests.post(
            f'{BORROW_SERVICE}/borrow/return',
            json={'user_id': session['user_id'], 'book_id': book_id},
            timeout=10
        )
        
        flash('Book returned successfully!', 'success')
    except requests.exceptions.ConnectionError:
        flash('Service unavailable', 'danger')
    
    return redirect(url_for('borrowed'))

@app.route('/borrowed')
def borrowed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    borrowed_books = []
    try:
        borrow_response = requests.get(f'{BORROW_SERVICE}/borrow/user/{session["user_id"]}', timeout=10)
        borrowed_records = borrow_response.json() if borrow_response.status_code == 200 else []
        
        for record in borrowed_records:
            book_response = requests.get(f'{BOOK_SERVICE}/books/{record["book_id"]}', timeout=10)
            if book_response.status_code == 200:
                book_data = book_response.json()
                book_data['borrowed_at'] = record['borrowed_at']
                book_data['due_date'] = record['due_date']
                borrowed_books.append(book_data)
    except:
        flash('Service unavailable', 'warning')
    
    return render_template('borrowed.html', borrowed_books=borrowed_books)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
