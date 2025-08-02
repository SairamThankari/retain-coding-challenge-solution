from flask import Flask, request, jsonify
import sqlite3
import json
import re
import hashlib
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database connection with proper error handling
def get_db_connection():
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        return None

# Input validation functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, ""

def validate_name(name):
    """Validate name format"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    return True, ""

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def require_json(f):
    """Decorator to ensure request contains valid JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        return f(*args, **kwargs)
    return decorated_function

# Error handling
class APIError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

@app.errorhandler(APIError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status_code

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# API Routes
@app.route('/')
def home():
    return jsonify({
        "message": "User Management System",
        "version": "1.0.0",
        "endpoints": {
            "GET /users": "Get all users",
            "GET /user/<id>": "Get specific user",
            "POST /users": "Create new user",
            "PUT /user/<id>": "Update user",
            "DELETE /user/<id>": "Delete user",
            "GET /search?name=<name>": "Search users by name",
            "POST /login": "User login"
        }
    })

@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users (excluding passwords)"""
    try:
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "created_at": user[3]
            })
        
        return jsonify({"users": user_list, "count": len(user_list)})
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise APIError("User not found", 404)
        
        return jsonify({
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "created_at": user[3]
        })
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/users', methods=['POST'])
@require_json
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['name', 'email', 'password']):
            raise APIError("Missing required fields: name, email, password")
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate inputs
        name_valid, name_error = validate_name(name)
        if not name_valid:
            raise APIError(name_error)
        
        if not validate_email(email):
            raise APIError("Invalid email format")
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            raise APIError(password_error)
        
        # Hash password
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise APIError("Email already exists", 409)
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, datetime.now().isoformat())
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        return jsonify({
            "message": "User created successfully",
            "user_id": user_id,
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/user/<int:user_id>', methods=['PUT'])
@require_json
def update_user(user_id):
    """Update user information"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided")
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        
        # Validate inputs if provided
        if name:
            name_valid, name_error = validate_name(name)
            if not name_valid:
                raise APIError(name_error)
        
        if email:
            if not validate_email(email):
                raise APIError("Invalid email format")
        
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise APIError("User not found", 404)
        
        # Check if email is already taken by another user
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
            if cursor.fetchone():
                raise APIError("Email already exists", 409)
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if name:
            update_fields.append("name = ?")
            params.append(name)
        
        if email:
            update_fields.append("email = ?")
            params.append(email)
        
        if not update_fields:
            raise APIError("No valid fields to update")
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({"message": "User updated successfully"})
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise APIError("User not found", 404)
        
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        return jsonify({"message": "User deleted successfully"})
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/search', methods=['GET'])
def search_users():
    """Search users by name"""
    try:
        name = request.args.get('name', '').strip()
        
        if not name:
            raise APIError("Please provide a name parameter to search")
        
        if len(name) < 2:
            raise APIError("Search term must be at least 2 characters long")
        
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, created_at FROM users WHERE name LIKE ? ORDER BY name",
            (f'%{name}%',)
        )
        users = cursor.fetchall()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "created_at": user[3]
            })
        
        return jsonify({
            "users": user_list,
            "count": len(user_list),
            "search_term": name
        })
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
@require_json
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['email', 'password']):
            raise APIError("Missing required fields: email, password")
        
        email = data['email'].strip().lower()
        password = data['password']
        
        if not validate_email(email):
            raise APIError("Invalid email format")
        
        if not password:
            raise APIError("Password is required")
        
        # Hash the provided password
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        if not conn:
            raise APIError("Database connection failed", 500)
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email FROM users WHERE email = ? AND password = ?",
            (email, hashed_password)
        )
        user = cursor.fetchone()
        
        if user:
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "user": {
                    "id": user[0],
                    "name": user[1],
                    "email": user[2]
                }
            })
        else:
            return jsonify({
                "status": "failed",
                "message": "Invalid email or password"
            }), 401
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        raise APIError("Database error occurred", 500)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5009, debug=debug_mode)