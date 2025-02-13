from flask import Flask, request, jsonify, session
import tinydb

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for sessions
db = tinydb.TinyDB('users.json')
users_table = db.table('users')

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_jwt_cookies

### User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all([data['email'], data['password']]):
        return {"message": "Email and password are required"}, 400
    user = User.query.filter_by(email=data['email']).first()
    if user:
        return {"message": "User already exists"}, 409
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return {"message": "User created successfully"}, 201

### Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not all([data['email'], data['password']]):
        return {"message": "Email and password are required"}, 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return {"message": "Invalid credentials"}, 401
    access_token = create_access_token(identity=user.id)
    return {"access_token": access_token}, 200

### Logout
@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    unset_jwt_cookies(response)
    return {"message": "Logged out successfully"}, 200

### Profile Update
@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not all([data['first_name'], data['last_name']]):
        return {"message": "First name and last name are required"}, 400
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return {"message": "User not found"}, 404
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    db.session.commit()
    return {"message": "Profile updated successfully"}, 200

### Error Handling
@app.errorhandler(401)
def handle_unauthorized(e):
    return {"message": "Unauthorized", "error": str(e)}, 401

@app.errorhandler(500)
def handle_internal_error(e):
    db.session.rollback()
    return {"message": "Internal server error", "error": str(e)}, 500