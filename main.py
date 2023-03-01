from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, logout_user, current_user, login_required
from flask_mail import Mail, Message
from pathlib import Path
import os
import openai
from sqlalchemy.orm.exc import UnmappedInstanceError
from route_functions import register_user, login
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
import re

path = Path(r"C:\Users\stapi\PycharmProjects\life_scale\instance\living.db")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('LIFE_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///living.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get("MY_EMAIL")
app.config['MAIL_PASSWORD'] = os.environ.get("MY_EMAIL_APP_PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MY_EMAIL")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

admin = os.environ.get("admin")

openai.api_key = os.environ.get("OPEN_AI_LIFE_KEY")


def generate(content: str) -> str:
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=f"Python code for printing this: '{content}'",
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response


# with app.app_context():
#     key = Fernet.generate_key()

key = os.environ.get("F_KEY")

fernet = Fernet(key)


def encrypt_data(data):
    return fernet.encrypt(data.encode())


def decrypt_data(data):
    return fernet.decrypt(data).decode()


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    birth_date = db.Column(db.String(12), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, nullable=False)
    connections = db.relationship('Connection', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    finances = db.relationship('Finances', backref='user', lazy=True)
    bucket_list = db.relationship('Bucketlist', backref='user', lazy=True)


class Connection(db.Model):
    __tablename__ = 'life connections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    relationship_to_user = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.String(12), nullable=False)
    relationship_thoughts = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Goal(db.Model):
    __tablename__ = "life goals"
    id = db.Column(db.Integer, primary_key=True)
    life_goal_title = db.Column(db.String(100), nullable=True)
    chosen_goal = db.Column(db.Text, unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Finances(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_title = db.Column(db.String(100), nullable=True)
    financial_goal = db.Column(db.String(500), nullable=True)
    target_amount = db.Column(db.Float, nullable=True)
    formatted_amount = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Bucketlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bucket_list_item_title = db.Column(db.String(100), nullable=True)
    bucket_list_item = db.Column(db.String(500), nullable=True)
    item_cost = db.Column(db.Float, nullable=True)
    formatted_cost = db.Column(db.String(50), nullable=True)
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
        country_currency = request.form.get("country")
        token = s.dumps(email, salt="email-verification")
        msg = Message("Verify Your Email", recipients=[email])
        msg.body = f"Click the link to verify your email: {url_for('verify_email', token=token, _external=True)}"
        mail.send(msg)
        registered_user = register_user(username=name,
                                        email=email,
                                        password=password,
                                        date_of_birth=date_of_birth,
                                        money=country_currency,
                                        verification=False,
                                        db=db,
                                        user=User, goal=Goal, finances=Finances)
        return registered_user
    return render_template('register.html')


@app.route("/registration/success")
def registration_success():
    return render_template("registration_success.html")


@app.route("/verify-email/<token>")
def verify_email(token):
    try:
        # Validate the token and mark the user as verified
        email = s.loads(token, salt="email-verification", max_age=3600)
        user = User.query.filter_by(email=email).first()
        user.verified = True
        db.session.commit()
        success_message = "Email verification successful."
        return render_template("email-verification.html", response=success_message)
    except SignatureExpired:
        expired_link_message = "The verification link has expired. Please try again."
        return render_template("email-verification.html", response=expired_link_message)
    except BadSignature:
        invalid_link_message = "The verification link is invalid. Please check your email and try again."
        return render_template("email-verification.html", response=invalid_link_message)


@app.route("/login", methods=["GET", "POST"])
def implements_login():
    if request.method == "POST":
        user_name = request.form.get("entryUsername").lower()
        user_password = request.form.get("entryPassword")
        log_in = login(name=user_name, entered_password=user_password, user=User)
        return log_in
    return render_template("login.html")


@app.route("/life-goals", methods=["GET", "POST"])
@login_required
def add_life_goal():
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('add_life_goal'))

        selected_title = request.form.get("life-goals")
        goal_check = Goal.query.filter_by(user_id=current_user.id).all()
        if selected_title == 'selection':
            flash("Please select one of the options.")
            return redirect(url_for('add_life_goal'))
        for goal_title in goal_check:
            if goal_title.life_goal_title == selected_title:
                flash("Goal exists, You can only edit or delete this goal.")
                return redirect(url_for('goals'))

        your_life_goal = request.form.get("lifeGoalFormControlTextarea")
        your_life_goal = encrypt_data(your_life_goal)
        life_goal = Goal(life_goal_title=selected_title,
                         chosen_goal=your_life_goal,
                         user_id=current_user.id)
        db.session.add(life_goal)
        db.session.commit()
        return redirect(url_for('goals'))
    return render_template("add-life-goals.html", comp_func=generate)


@app.route("/life-goals/edit/<int:life_goal_id>", methods=["GET", "POST"])
@login_required
def life_goal_edit(life_goal_id):
    goal_edit = Goal.query.get(life_goal_id)
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('life_goal_edit'))
        the_edit = request.form.get("editLifeGoalFormControlTextarea")
        the_edit = encrypt_data(the_edit)
        goal_edit.chosen_goal = the_edit
        db.session.commit()
        return redirect(url_for('goals'))
    return render_template("life-goals-edit.html", life_edit=goal_edit, d_func=decrypt_data)


@app.route("/life-goals/ai-edit/<int:life_goal_id>", methods=["GET", "POST"])
@login_required
def life_goal_ai_enhance(life_goal_id):
    goal_edit = Goal.query.get(life_goal_id)
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('life_goal_ai_enhance'))
        the_edit = request.form.get("aiEditLifeGoalFormControlTextarea")
        the_edit = encrypt_data(the_edit)
        goal_edit.chosen_goal = the_edit
        db.session.commit()
        return redirect(url_for('goals'))

    return render_template("life-goals-ai-edit.html", life_ai_edit=goal_edit, d_func=decrypt_data, enhancer=generate)


@app.route("/life-goals/delete/<int:life_goal_id>", methods=["GET", "POST"])
@login_required
def delete_life_goal(life_goal_id):
    if current_user.is_authenticated and current_user.is_authenticated:
        item_to_delete = Goal.query.get(life_goal_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for("goals"))


@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    user_goals = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template("life-goals.html", user_goals=user_goals, d_func=decrypt_data)


@app.route("/add_connections", methods=["GET", "POST"])
@login_required
def add_connections():
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('add_connections'))
        person_name = request.form.get("entryName")
        person_name = encrypt_data(person_name)
        relationship_to_person = request.form.get("entryRelate")
        relationship_to_person = encrypt_data(relationship_to_person)
        person_date_of_birth = request.form.get("entryDate")
        what_you_think_about_person = request.form.get("relationshipFormControlTextarea")
        if not person_name or not relationship_to_person or not person_date_of_birth or not what_you_think_about_person:
            flash("Please make sure that you have filled in the entire form.")
            return redirect(url_for('add_connections'))
        what_you_think_about_person = encrypt_data(what_you_think_about_person)
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
@login_required
def connections_edit(connect_id):
    connection_goal_edit = Connection.query.get(connect_id)
    if current_user.is_authenticated and request.method == "POST":
        connection_name = request.form.get("editEntryName")
        relationship = request.form.get("editEntryRelate")
        date_of_birth = request.form.get("editEntryDate")
        thoughts = request.form.get("relationshipFormControlTextareaEdit")
        if connection_name:
            connection_name = encrypt_data(connection_name)
            connection_goal_edit.name = connection_name
        if relationship:
            relationship = encrypt_data(relationship)
            connection_goal_edit.relationship_to_user = relationship
        if date_of_birth:
            connection_goal_edit.birth_date = date_of_birth
        if thoughts:
            thoughts = encrypt_data(thoughts)
            connection_goal_edit.relationship_thoughts = thoughts
        db.session.commit()
        return redirect(url_for('connections'))
    return render_template("edit-connections.html", connect=connection_goal_edit, d_func=decrypt_data)


@app.route("/connections/ai-edit/<int:connect_id>", methods=["GET", "POST"])
@login_required
def connections_ai_enhance_edit(connect_id):
    connection_goal_edit = Connection.query.get(connect_id)
    if current_user.is_authenticated and request.method == "POST":
        connection_name = request.form.get("editEntryName")
        relationship = request.form.get("editEntryRelate")
        date_of_birth = request.form.get("editEntryDate")
        thoughts = request.form.get("relationshipFormControlTextareaEdit")
        if connection_name:
            connection_name = encrypt_data(connection_name)
            connection_goal_edit.name = connection_name
        if relationship:
            relationship = encrypt_data(relationship)
            connection_goal_edit.relationship_to_user = relationship
        if date_of_birth:
            connection_goal_edit.birth_date = date_of_birth
        if thoughts:
            thoughts = encrypt_data(thoughts)
            connection_goal_edit.relationship_thoughts = thoughts
        db.session.commit()
        return redirect(url_for('connections'))
    return render_template("connections-ai-enhance.html",
                           connect_ai_edit=connection_goal_edit,
                           d_func=decrypt_data,
                           enhancer=generate)


@app.route("/connections/delete/<int:connect_id>", methods=["GET", "POST"])
@login_required
def delete_connection(connect_id):
    if current_user.is_authenticated:
        item_to_delete = Connection.query.get(connect_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for("connections"))


@app.route("/connections", methods=["GET", "POST"])
@login_required
def connections():
    user_connections = Connection.query.filter_by(user_id=current_user.id)
    return render_template("connections.html", user_connections=user_connections, d_func=decrypt_data)


@app.route("/add-finance", methods=["GET", "POST"])
@login_required
def add_finance_goals():
    value_list = ["Emergency Funds", "Life Insurance", "Medical Insurance",
                  "Disability Cover", "Income Insurance", "Retirement Fund"]
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('add_finance_goals'))
        title = request.form.get("finance-goals")
        amount = request.form.get("quantity").replace(" ", "")
        amount = re.sub(r'(?!\.)\D', '', amount)
        if amount:
            try:
                float(amount)
            except ValueError:
                flash("You can only enter positive digits e.g 5 instead of 'five'.")
                return redirect(url_for('add_finance_goals'))
        amount_formatted = format_number(float(amount))
        amount_formatted = encrypt_data(amount_formatted)
        plan = request.form.get("financeFormControlTextarea")
        plan = encrypt_data(plan)
        goal_check = Finances.query.filter_by(user_id=current_user.id).all()
        if title == 'selection' or title not in value_list:
            flash("Please select one of the valid options.")
            return redirect(url_for('add_finance_goals'))
        for goal_title in goal_check:
            if goal_title.goal_title == title:
                flash("Goal exists, You can only edit or delete this goal.")
                return redirect(url_for('finance'))
        financial_goal = Finances(goal_title=title,
                                  target_amount=amount,
                                  formatted_amount=amount_formatted,
                                  financial_goal=plan,
                                  user_id=current_user.id)
        db.session.add(financial_goal)
        db.session.commit()
        return redirect(url_for('finance'))
    return render_template("add-finance.html")


@app.route("/finance/edit/<int:goal_id>", methods=["GET", "POST"])
@login_required
def finance_edit(goal_id):
    finance_goal_edit = Finances.query.get(goal_id)
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('finance_edit', goal_id=finance_goal_edit.id))
        goal_edit = request.form.get("financeFormControlTextarea-edit")
        amount = request.form.get("quantity_edit").replace(" ", "")
        if goal_edit:
            goal_edit = encrypt_data(goal_edit)
            finance_goal_edit.financial_goal = goal_edit
        if amount:
            try:
                float(amount)
            except ValueError:
                flash("You can only enter positive digits e.g 5 instead of 'five'.")
                return redirect(url_for('finance_edit', goal_id=finance_goal_edit.id))
            finance_goal_edit.target_amount = amount
            formatted_amount = format_number(float(amount))
            formatted_amount = encrypt_data(formatted_amount)
            finance_goal_edit.formatted_amount = formatted_amount

        db.session.commit()
        return redirect(url_for("finance"))
    return render_template("finances_edit.html", finance_goal=finance_goal_edit, d_func=decrypt_data)


@app.route("/finance/ai-edit/<int:goal_id>", methods=["GET", "POST"])
@login_required
def finance_edit_ai_enhance(goal_id):
    finance_ai_goal_edit = Finances.query.get(goal_id)
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('finance_edit_ai_enhance', goal_id=finance_ai_goal_edit.id))
        goal_edit = request.form.get("aiFinanceFormControlTextarea-edit")
        amount = request.form.get("quantity_edit").replace(" ", "")
        if goal_edit:
            goal_edit = encrypt_data(goal_edit)
            finance_ai_goal_edit.financial_goal = goal_edit
        if amount:
            try:
                float(amount)
            except ValueError:
                flash("You can only enter positive digits e.g 5 instead of 'five'.")
                return redirect(url_for('finance_edit_ai_enhance', goal_id=finance_ai_goal_edit.id))
            finance_ai_goal_edit.target_amount = amount
            formatted_amount = format_number(float(amount))
            formatted_amount = encrypt_data(formatted_amount)
            finance_ai_goal_edit.formatted_amount = formatted_amount

        db.session.commit()
        return redirect(url_for("finance"))
    return render_template("finance-goals-ai-edit.html",
                           finance_goal=finance_ai_goal_edit,
                           d_func=decrypt_data,
                           enhancer=generate)


@app.route("/finance/delete/<int:goal_id>", methods=["GET", "POST"])
@login_required
def delete_finance_goal(goal_id):
    if current_user.is_authenticated:
        item_to_delete = Finances.query.get(goal_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for("finance"))


@app.route("/finance", methods=["GET", "POST"])
@login_required
def finance():
    user_finances = Finances.query.filter_by(user_id=current_user.id)
    return render_template("finance.html", user_finances=user_finances, func=format_number, d_func=decrypt_data)


@app.route("/add-bucketlist", methods=["GET", "POST"])
@login_required
def add_bucketlist_item():
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('add_bucketlist_item'))
        item_title = request.form.get("bucketListFormControlInput").title()
        cost = request.form.get("costFormControlInput").replace(" ", "")
        cost = re.sub(r'(?!\.)\D', '', cost)
        if cost:
            try:
                float(cost)
            except ValueError:
                flash("You can only enter positive digits e.g 5 instead of 'five'.")
                return redirect(url_for('add_bucketlist_item'))
        cost_formatted = format_number(float(cost))
        item_details = request.form.get("bucketListFormControlTextarea")
        item_details = encrypt_data(item_details)
        bucket_list_item = Bucketlist(bucket_list_item_title=item_title,
                                      bucket_list_item=item_details,
                                      item_cost=cost,
                                      formatted_cost=cost_formatted,
                                      user_id=current_user.id)
        db.session.add(bucket_list_item)
        db.session.commit()
        return redirect(url_for('bucket_list'))
    return render_template("add_bucketlist.html")


@app.route("/bucket-list/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_bucket_list_item(item_id):
    bucket_list_edit = Bucketlist.query.get(item_id)
    if current_user.is_authenticated and request.method == "POST":
        state = request.form.get("status")
        if state and state == "False":
            flash("Please enable Javascript in your browser settings.")
            return redirect(url_for('edit_bucket_list_item', item_id=bucket_list_edit.id))
        title_edit = request.form.get("editBucketListFormControlInput").title()
        cost_edit = request.form.get("editCostFormControlInput").replace(" ", "")
        cost_edit = re.sub(r'(?!\.)\D', '', cost_edit)
        item_text_edit = request.form.get("editBucketListFormControlTextarea")
        if title_edit:
            bucket_list_edit.bucket_list_item_title = title_edit
        if cost_edit:
            try:
                float(cost_edit)
            except ValueError:
                flash("You can only enter positive digits e.g 5 instead of 'five'.")
                return redirect(url_for('edit_bucket_list_item', item_id=bucket_list_edit.id))
            bucket_list_edit.item_cost = cost_edit
            bucket_list_edit.formatted_cost = format_number(float(cost_edit))
        if item_text_edit:
            item_text_edit = encrypt_data(item_text_edit)
            bucket_list_edit.bucket_list_item = item_text_edit
        db.session.commit()
        return redirect(url_for("bucket_list"))
    return render_template("edit-bucket-list.html", user_bucket_list=bucket_list_edit, d_func=decrypt_data)


@app.route("/bucket-list/ai-edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def ai_edit_bucket_list_item(item_id):
    bucket_list_edit = Bucketlist.query.get(item_id)
    if current_user.is_authenticated and request.method == "POST":
        title_edit = request.form.get("aiEditBucketListFormControlInput")
        cost_edit = request.form.get("aiEditCostFormControlInput").replace(" ", "")
        cost_edit = re.sub(r'(?!\.)\D', '', cost_edit)
        item_text_edit = request.form.get("aiEditBucketListFormControlTextarea")
        if title_edit:
            bucket_list_edit.bucket_list_item_title = title_edit
        if cost_edit:
            bucket_list_edit.item_cost = cost_edit
            bucket_list_edit.formatted_cost = format_number(float(cost_edit))
        if item_text_edit:
            item_text_edit = encrypt_data(item_text_edit)
            bucket_list_edit.bucket_list_item = item_text_edit
        db.session.commit()
        return redirect(url_for("bucket_list"))
    return render_template("bucket-list-ai-edit.html",
                           user_bucket_list=bucket_list_edit,
                           d_func=decrypt_data, enhancer=generate)


@app.route("/bucket-list/delete/<int:item_id>", methods=["GET", "POST"])
@login_required
def delete_bucketlist_item(item_id):
    if current_user.is_authenticated:
        item_to_delete = Bucketlist.query.get(item_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for("bucket_list"))


@app.route("/bucket-list", methods=["GET", "POST"])
@login_required
def bucket_list():
    user_bucketlist = Bucketlist.query.filter_by(user_id=current_user.id)
    return render_template("bucket-list.html",
                           user_bucketlist=user_bucketlist,
                           d_func=decrypt_data)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def delete_user():
    """
    This function takes user id from admin form and systematically removes user data
    and finally deletes the user profile.
    :return: url_redirect
    """
    if current_user.id == 1:
        if request.method == "POST":
            user_to_remove = int(request.form.get("userID").replace(" ", ""))
            user_goals = Goal.query.filter_by(user_id=user_to_remove).all()
            user_connections = Connection.query.filter_by(user_id=user_to_remove)
            user_finances = Finances.query.filter_by(user_id=user_to_remove)
            user_bucketlist = Bucketlist.query.filter_by(user_id=current_user.id)
            for goal_item in user_goals:
                try:
                    item_to_delete = Goal.query.get(goal_item.id)
                    db.session.delete(item_to_delete)
                    db.session.commit()
                except (AttributeError, UnmappedInstanceError):
                    continue

            for relation in user_connections:
                try:
                    item_to_delete = Connection.query.get(relation.id)
                    db.session.delete(item_to_delete)
                    db.session.commit()
                except (AttributeError, UnmappedInstanceError):
                    continue

            for insurance in user_finances:
                try:
                    item_to_delete = Finances.query.get(insurance.id)
                    db.session.delete(item_to_delete)
                    db.session.commit()
                except (AttributeError, UnmappedInstanceError):
                    continue

            for bucket in user_bucketlist:
                try:
                    item_to_delete = Bucketlist.query.get(bucket.id)
                    db.session.delete(item_to_delete)
                    db.session.commit()
                except (AttributeError, UnmappedInstanceError):
                    continue
            site_user = User.query.get(user_to_remove)
            db.session.delete(site_user)
            db.session.commit()
            flash(f"User: {user_to_remove} is deleted")
            return redirect(url_for('home'))
    else:
        abort(401)
    return render_template("admin-delete.html")


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['emailEntry']).first()
        if user:
            token = s.dumps(user.email, salt='email-confirm')
            msg = Message('Password Reset Request', sender=os.environ.get("MY_EMAIL"), recipients=[user.email])
            link = url_for('reset_token', token=token, _external=True)
            msg.body = 'Your link is {}'.format(link)
            mail.send(msg)

            return '<h1>An email has been sent with instructions to reset your password.</h1>'
        else:
            flash(f'This account does not exist with us. However, you can register')
            return redirect(url_for('reset_request'))

    return render_template('reset_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    user = User.query.filter_by(email=email).first()
    if user:
        if request.method == 'POST':
            hashed_password = generate_password_hash(password=request.form['password'],
                                                     method='pbkdf2:sha256',
                                                     salt_length=4)
            user.password = hashed_password
            db.session.commit()
            return '<h1>Your password has been updated!</h1>'
        return render_template('reset_token.html')


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        if current_user.is_authenticated:
            email_address = current_user.email
        else:
            email_address = request.form.get("messageFormControlTextarea")

        email_subject = request.form.get("Subject")
        email_message = request.form.get("messageFormControlTextarea")
        msg = Message(f'{email_subject}', sender=os.environ.get("MY_EMAIL"), recipients=[os.environ.get("MY_EMAIL")])
        msg.body = f'Email from {email_address}\nMessage:\n {email_message}'
        mail.send(msg)

    return render_template("contact.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('implements_login'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
