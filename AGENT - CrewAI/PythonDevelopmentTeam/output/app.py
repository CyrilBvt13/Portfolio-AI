from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators, BooleanField
import tinydb

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
tiny_db = tinydb.TinyDB('users.json')
user_table = tinydb.table('users')
login_manager = LoginManager()
login_manager.init_app(app)

class User:
    def __init__(self, username, email, password_hash):
        self.id = None
        self.username = username
        self.email = email
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    user_data = user_table.get(tinydb.where('id') == int(user_id))
    if user_data:
        return User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=user_data['password_hash']
        )
    return None

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_data = user_table.get(tinydb.where('username') == form.username.data)
        if user_data and check_password_hash(user_data['password_hash'], form.password.data):
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash']
            )
            login_user(user)
            return redirect(url_for('profile', user_id=user.id))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)