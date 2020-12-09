import os

import bcrypt

import config

from dotenv import load_dotenv
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from playhouse.shortcuts import model_to_dict

from models import Difficulty, Riddles, Users, UsersRiddles, database, db_proxy

from peewee import fn


load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
if 'HEROKU' in os.environ:
    SECRET_KEY.encode('utf-8')


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.from_object(config.DevelopmentConfig())

login_manager = LoginManager()
login_manager.init_app(app)

MINIMAL_PASS_LENGTH = 8


@login_manager.user_loader
def load_user(user_id):
    return Users.get(user_id)


def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)


@app.before_request
def _db_connect():
    g.db = db_proxy
    g.db.connect()


@app.teardown_request
def _db_close(_):
    if not database.is_closed():
        g.db.close()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.j2'), 404


@app.errorhandler(401)
def page_unauthorized(e):
    return render_template('401.j2'), 401


app.register_error_handler(404, page_not_found)
app.register_error_handler(401, page_unauthorized)



@app.route('/index')
@app.route('/')
def index():
    return render_template("index.j2")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = Users.select(Users.username).where(fn.Lower(Users.username) == request.form['username'].lower())
        if user:
            flash('Username is already registered', "registered")
        elif len(request.form['password']) < MINIMAL_PASS_LENGTH:
            flash('Password must be at least 8 digits long')
        else:
            salt = bcrypt.gensalt(prefix=b'2b', rounds=10)
            unhashed_password = request.form['password'].encode('utf-8')
            hashed_password = bcrypt.hashpw(unhashed_password, salt)
            fields = {
                **request.form,
                'password': hashed_password
            }
            user = Users(**fields)
            user.save()
            login_user(user)
            return redirect(url_for('index'))
    return render_template("register.j2")


@app.route('/riddles/<int:riddle_id>', methods=["GET", "POST"])
@login_required
def riddle(riddle_id):
    query = UsersRiddles.select(UsersRiddles.riddle_id).where(UsersRiddles.user_id == current_user.user_id)
    solved = {riddle.riddle_id for riddle in query}
    for num in solved:
        if num == riddle_id:
            return redirect(url_for('correct', riddle_id=riddle_id))
    if request.method == "POST":
        riddle = Riddles.select().where(Riddles.riddle_id == riddle_id).get()
        answer = riddle.answer
        if answer != request.form['user_answer']:
            flash("Wrong answer. Try again.")
        else:
            UsersRiddles.create(riddle=riddle_id, user=current_user.user_id)
            current_user.points += 1
            current_user.save()
            return redirect(url_for('correct', riddle_id=riddle_id))
    riddle = Riddles.select().where(Riddles.riddle_id == riddle_id).join(Difficulty, attr='difficulty_id').get()
    riddle_dict = model_to_dict(riddle)
    return render_template("riddle.j2", **riddle_dict)


@app.route('/riddles/<int:riddle_id>/correct', methods=["GET", "POST"])
@login_required
def correct(riddle_id):
    return render_template("correct.j2", riddle_id=riddle_id, username=current_user.name)


@app.route('/riddles')
@login_required
def riddles():
    query = (Riddles
            .select(Riddles.riddle_id)
            .order_by(Riddles.riddle_id)
            .limit(100))
    riddles = [riddle.riddle_id for riddle in query]
    query = UsersRiddles.select(UsersRiddles.riddle_id).where(UsersRiddles.user_id == current_user.user_id)
    solved = {riddle.riddle_id for riddle in query}
    return render_template("riddles.j2", riddles=riddles, solved=solved)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form['username']:
        try:
            input_username = request.form['username'].lower()
            user = Users.select().where(
                fn.Lower(Users.username) == input_username
                ).get()
        except Users.DoesNotExist:
            flash('No such username found. Please try again')
        else:
            fields = model_to_dict(user)
            pw = request.form['password'].encode('utf-8')
            if bcrypt.checkpw(pw, fields['password'].encode('utf-8')):
                user = Users(**fields)
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('The password entered is incorrect')
    return render_template('login.j2')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
