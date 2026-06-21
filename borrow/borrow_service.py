from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
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

# Borrowed Novel Model
class BorrowedNovel(db.Model):
    __tablename__ = 'borrowed_novels'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    novel_id = db.Column(db.Integer, nullable=False)
    borrowed_at = db.Column(db.DateTime, server_default=db.func.now())
    returned_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='borrowed')
    due_date = db.Column(db.DateTime, nullable=True)

@app.route('/borrow', methods=['POST'])
def borrow_book():
    try:
        data = request.json
        user_id = data.get('user_id')
        book_id = data.get('book_id')
        
        if not user_id or not book_id:
            return jsonify({'error': 'user_id and book_id are required'}), 400
        
        existing = BorrowedNovel.query.filter_by(
            user_id=user_id,
            novel_id=book_id,
            status='borrowed'
        ).first()
        
        if existing:
            return jsonify({'error': 'Book already borrowed'}), 400
        
        borrowed = BorrowedNovel(
            user_id=user_id,
            novel_id=book_id,
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(borrowed)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book borrowed successfully',
            'borrowed_id': borrowed.id,
            'due_date': borrowed.due_date.isoformat() if borrowed.due_date else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/borrow/return', methods=['POST'])
def return_book():
    try:
        data = request.json
        user_id = data.get('user_id')
        book_id = data.get('book_id')
        
        if not user_id or not book_id:
            return jsonify({'error': 'user_id and book_id are required'}), 400
        
        borrowed = BorrowedNovel.query.filter_by(
            user_id=user_id,
            novel_id=book_id,
            status='borrowed'
        ).first()
        
        if not borrowed:
            return jsonify({'error': 'Book not borrowed'}), 404
        
        borrowed.status = 'returned'
        borrowed.returned_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Book returned successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/borrow/user/<int:user_id>', methods=['GET'])
def get_user_borrowed(user_id):
    try:
        borrowed = BorrowedNovel.query.filter_by(
            user_id=user_id,
            status='borrowed'
        ).all()
        
        return jsonify([{
            'id': b.id,
            'book_id': b.novel_id,
            'borrowed_at': b.borrowed_at.isoformat() if b.borrowed_at else None,
            'due_date': b.due_date.isoformat() if b.due_date else None
        } for b in borrowed])
    except Exception as e:
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
    
    print("🚀 Borrow Service running on port 5003...")
    app.run(debug=False, host='0.0.0.0', port=5003)
