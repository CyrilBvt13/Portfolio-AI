from flask import Flask
from flask_bcrypt import Bcrypt
from marshmallow import Schema, fields, ValidationError
from functools import wraps
import jwt
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from os import getenv

app = Flask(__name__)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(80))

app.config['SECRET_KEY'] = getenv('JWT_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')

limiter = Limiter(app, key_func=get_remote_address)

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

class UserSchema(Schema):
    username = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)

def validate_user(data):
    try:
        return UserSchema().load(data)  # This will raise a ValidationError if data is invalid
    except ValidationError as err:
        return err.messages, False
    return {}, True

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.get(data['public_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    validation_errors, is_valid = validate_user(data)
    if not is_valid:
        return jsonify(validation_errors), 400

    hashed_password = hash_password(data['password'])
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'})

@app.route('/login', methods=['POST'])
@limiter.limit("10/minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401

    access_token = jwt.encode({'user_id': user.id}, app.config['SECRET_KEY'])
    return jsonify(access_token=access_token)

@app.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({
        'public_id': current_user.public_id,
        'username': current_user.username
    })

if __name__ == '__main__':
    app.run()
