from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, logout_user, current_user
from pathlib import Path
import os
from route_functions import register_user, login, add_connection, add_purpose

path = Path(r"C:\Users\stapi\PycharmProjects\life_scale\instance\living.db")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('LIFE_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///living.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    birth_date = db.Column(db.String(12), nullable=False)
    connections = db.relationship('Connection', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    finances = db.relationship('Finances', backref='user', lazy=True)
    bucket_list = db.relationship('Bucketlist', backref='user', lazy=True)


class Connection(db.Model):
    __tablename__ = 'life connections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    relationship_to_user = db.Column(db.String(120), nullable=False)
    birth_date = db.Column(db.String(12), nullable=False)
    relationship_thoughts = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Goal(db.Model):
    __tablename__ = "life goals"
    id = db.Column(db.Integer, primary_key=True)
    purpose = db.Column(db.Text, nullable=True)
    spiritual = db.Column(db.Text, nullable=True)
    mental = db.Column(db.Text, nullable=True)
    physical_health = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Finances(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emergency_funds = db.Column(db.String(120), nullable=True)
    life_insurance = db.Column(db.String(120), nullable=True)
    medical_insurance = db.Column(db.String(120), nullable=True)
    disability_insurance = db.Column(db.String(120), nullable=True)
    income_insurance = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Bucketlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bucket_list_item = db.Column(db.String(120), nullable=False)
    item_cost = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Checking if the database exists and if it does not exist we create it.
if path.exists():
    pass
else:
    with app.app_context():
        db.create_all()
        print("The database has been created.")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/registration", methods=["GET", "POST"])
def implement_registration():
    if request.method == "POST":
        name = request.form.get("entryUsername").lower()
        email = request.form.get("entryEmail").lower()
        password = request.form.get("entryPassword")
        date_of_birth = request.form.get("entryDate")
        print(f"name: {name}, email: {email}, password: {password}, birth date: {date_of_birth}")
        registered_user = register_user(username=name,
                                        email=email,
                                        password=password,
                                        date_of_birth=date_of_birth,
                                        db=db,
                                        user=User, goal=Goal, finances=Finances)
        return registered_user
    return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def implements_login():
    if request.method == "POST":
        user_name = request.form.get("entryUsername").lower()
        user_password = request.form.get("entryPassword")
        print(f"name: {user_name}, password: {user_password}")
        log_in = login(name=user_name, entered_password=user_password, user=User)
        return log_in
    return render_template("login.html")


@app.route("/add_connections", methods=["GET", "POST"])
def implements_add_connections():
    if request.method == "POST":
        person_name = request.form.get("entryName")
        relationship_to_person = request.form.get("entryRelate")
        person_date_of_birth = request.form.get("entryDate")
        what_you_think_about_person = request.form.get("relationshipFormControlTextarea")
        your_connection = add_connection(connect_name=person_name,
                                         relationship=relationship_to_person,
                                         date_of_birth=person_date_of_birth,
                                         thoughts_on_relationships=what_you_think_about_person,
                                         db=db,
                                         connection=Connection, id_no=current_user.id)
        return your_connection
    return render_template('add_connection.html')


@app.route("/goals", methods=["GET", "POST"])
def implements_add_purpose():
    if request.method == "POST":
        your_purpose = request.form.get("purposeFormControlTextarea")
        your_goal = add_purpose(driving_purpose=your_purpose, db=db, id_no=current_user.id, goal=Goal)
        return your_goal
    return render_template("goals.html")


@app.route("/connections", methods=["GET", "POST"])
def connections():
    user_connections = Connection.query.filter_by(id=current_user.id)
    return render_template("connections.html", user_connections=user_connections)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('implements_login'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
