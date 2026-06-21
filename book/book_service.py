from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import time
import sys

app = Flask(__name__)

# MySQL Database configuration
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'mysql+pymysql://novels_user:novels_pass@database:3306/novels_db'
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

# Novel Model
class Novel(db.Model):
    __tablename__ = 'novels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(100))
    published_year = db.Column(db.String(10))
    image_url = db.Column(db.String(500))
    is_borrowed = db.Column(db.Boolean, default=False)
    borrowed_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/books', methods=['GET'])
def get_books():
    try:
        books = Novel.query.all()
        return jsonify([{
            'id': b.id,
            'name': b.name,
            'author': b.author,
            'description': b.description[:200] + '...' if len(b.description) > 200 else b.description,
            'genre': b.genre,
            'published_year': b.published_year,
            'is_borrowed': b.is_borrowed,
            'borrowed_by': b.borrowed_by
        } for b in books])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = Novel.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        return jsonify({
            'id': book.id,
            'name': book.name,
            'author': book.author,
            'description': book.description,
            'genre': book.genre,
            'published_year': book.published_year,
            'is_borrowed': book.is_borrowed
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>/borrow', methods=['PUT'])
def borrow_book(book_id):
    try:
        book = Novel.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        data = request.json
        user_id = data.get('user_id')
        
        if book.is_borrowed:
            return jsonify({'error': 'Book already borrowed'}), 400
        
        book.is_borrowed = True
        book.borrowed_by = user_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book borrowed successfully',
            'book': {
                'id': book.id,
                'name': book.name,
                'author': book.author,
                'is_borrowed': book.is_borrowed,
                'borrowed_by': book.borrowed_by
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>/return', methods=['PUT'])
def return_book(book_id):
    try:
        book = Novel.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        if not book.is_borrowed:
            return jsonify({'error': 'Book is not borrowed'}), 400
        
        book.is_borrowed = False
        book.borrowed_by = None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book returned successfully',
            'book': {
                'id': book.id,
                'name': book.name,
                'author': book.author,
                'is_borrowed': book.is_borrowed
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy'}), 500

if __name__ == '__main__':
    print("⏳ Waiting for database to be ready...")
    
    max_retries = 15
    connected = False
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Connection attempt {attempt + 1}/{max_retries}...")
            with app.app_context():
                db.create_all()
                db.session.execute('SELECT 1')
            print("✅ Database connected successfully!")
            connected = True
            break
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    print("🚀 Book Service running on port 5002...")
    app.run(debug=False, host='0.0.0.0', port=5002)
