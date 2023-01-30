from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, logout_user, current_user
from pathlib import Path
import os
from route_functions import register_user, login, add_purpose, add_spirituality, add_mental, \
    add_physical

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
    life_goal_title = db.Column(db.String(100), unique=True, nullable=True)
    chosen_goal = db.Column(db.Text, unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Finances(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_title = db.Column(db.String(100), unique=True, nullable=True)
    financial_goal = db.Column(db.String(500), nullable=True)
    target_amount = db.Column(db.Float, nullable=True)
    formatted_amount = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Bucketlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bucket_list_item_title = db.Column(db.String(100), unique=True, nullable=True)
    bucket_list_item = db.Column(db.String(500), nullable=True)
    item_cost = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Checking if the database exists and if it does not exist we create it.
if path.exists():
    pass
else:
    with app.app_context():
        db.create_all()
        print("The database has been created.")


def format_number(num):
    if num >= 1000000:
        return '{:,.1f}M'.format(num / 1000000)
    elif num >= 1000:
        return '{:,.1f}K'.format(num / 1000)
    else:
        return '{:,.1f}'.format(num)


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


@app.route("/life-goals", methods=["GET", "POST"])
def add_life_goal():
    if request.method == "POST":
        selected_title = request.form.get("life-goals")
        your_life_goal = request.form.get("lifeGoalFormControlTextarea")
        life_goal = Goal(life_goal_title=selected_title,
                         chosen_goal=your_life_goal,
                         user_id=current_user.id)
        db.session.add(life_goal)
        db.session.commit()
        return redirect(url_for('goals'))
    return render_template("life-goals.html")


@app.route("/life-goals/edit/<int:life_goal_id>", methods=["GET", "POST"])
def life_goal_edit(life_goal_id):
    goal_edit = Goal.query.get(life_goal_id)
    if request.method == "POST":
        the_edit = request.form.get("editLifeGoalFormControlTextarea")
        goal_edit.chosen_goal = the_edit
        db.session.commit()
        return redirect(url_for('goals'))
    return render_template("life-goals-edit.html", life_edit=goal_edit)


@app.route("/goals", methods=["GET", "POST"])
def goals():
    user_goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template("goals.html", user_goals=user_goals)


@app.route("/add_connections", methods=["GET", "POST"])
def add_connections():
    if request.method == "POST":
        person_name = request.form.get("entryName")
        relationship_to_person = request.form.get("entryRelate")
        person_date_of_birth = request.form.get("entryDate")
        what_you_think_about_person = request.form.get("relationshipFormControlTextarea")
        your_connection = Connection(name=person_name,
                                     relationship_to_user=relationship_to_person,
                                     birth_date=person_date_of_birth,
                                     relationship_thoughts=what_you_think_about_person,
                                     user_id=current_user.id)
        db.session.add(your_connection)
        db.session.commit()
        return redirect(url_for('connections'))
    return render_template('add_connection.html')


@app.route("/connections/edit/<int:connect_id>", methods=["GET", "POST"])
def connections_edit(connect_id):
    connection_goal_edit = Connection.query.get(connect_id)
    if request.method == "POST":
        connection_name = request.form.get("editEntryName")
        relationship = request.form.get("editEntryRelate")
        date_of_birth = request.form.get("editEntryDate")
        thoughts = request.form.get("relationshipFormControlTextareaEdit")
        if connection_name:
            connection_goal_edit.name = connection_name
        if relationship:
            connection_goal_edit.relationship_to_user = relationship
        if date_of_birth:
            connection_goal_edit.birth_date = date_of_birth
        if thoughts:
            connection_goal_edit.relationship_thoughts = thoughts
        db.session.commit()
        return redirect(url_for('connections'))
    return render_template("edit-connections.html")


@app.route("/connections", methods=["GET", "POST"])
def connections():
    user_connections = Connection.query.filter_by(user_id=current_user.id)
    return render_template("connections.html", user_connections=user_connections)


@app.route("/add-finance", methods=["GET", "POST"])
def add_finance_goals():
    if request.method == "POST":
        title = request.form.get("finance-goals")
        amount = request.form.get("quantity").replace(" ", "")
        amount_formatted = format_number(float(amount))
        plan = request.form.get("financeFormControlTextarea")
        financial_goal = Finances(goal_title=title,
                                  target_amount=amount,
                                  formatted_amount=amount_formatted,
                                  financial_goal=plan,
                                  user_id=current_user.id)
        db.session.add(financial_goal)
        db.session.commit()
        return redirect(url_for('finance'))
    return render_template("all_finance.html")


@app.route("/finance/edit/<int:goal_id>", methods=["GET", "POST"])
def finance_edit(goal_id):
    finance_goal_edit = Finances.query.get(goal_id)
    if request.method == "POST":
        goal_edit = request.form.get("financeFormControlTextarea-edit")
        print(goal_edit)
        amount = request.form.get("quantity_edit").strip()
        if goal_edit:
            finance_goal_edit.financial_goal = goal_edit
        if amount:
            finance_goal_edit.target_amount = amount
        db.session.commit()
        return redirect(url_for("finance"))
    return render_template("finances_edit.html", finance_goal=finance_goal_edit)


@app.route("/finance", methods=["GET", "POST"])
def finance():
    user_finances = Finances.query.filter_by(user_id=current_user.id)
    return render_template("finance.html", user_finances=user_finances, func=format_number)


@app.route("/purpose", methods=["GET", "POST"])
def implements_add_purpose():
    if request.method == "POST":
        your_purpose = request.form.get("purposeFormControlTextarea")
        your_goal = add_purpose(driving_purpose=your_purpose, db=db, id_no=current_user.id, goal=Goal)
        return your_goal
    return render_template("life-goals.html")


@app.route("/spirit", methods=["GET", "POST"])
def implements_add_spirituality():
    if request.method == "POST":
        your_spirit = request.form.get("spiritFormControlTextarea")
        your_goal = add_spirituality(the_spirit=your_spirit, db=db, id_no=current_user.id, goal=Goal)
        return your_goal
    return render_template("spirit.html")


@app.route("/mind", methods=["GET", "POST"])
def implements_mental():
    if request.method == "POST":
        your_mind = request.form.get("mindFormControlTextarea")
        your_goal = add_mental(the_mind=your_mind, db=db, id_no=current_user.id, goal=Goal)
        return your_goal
    return render_template("life-goals-edit.html")


@app.route("/body", methods=["GET", "POST"])
def implements_physical():
    if request.method == "POST":
        your_body = request.form.get("bodyFormControlTextarea")
        your_goal = add_physical(the_body=your_body, db=db, id_no=current_user.id, goal=Goal)
        return your_goal
    return render_template("edit-connections.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('implements_login'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
