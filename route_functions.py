from flask import url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
import os


def create_admin_user(user, db, password):
    hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=4)
    admin = user(username=os.environ.get("ADMIN_NAME").lower(), email=os.environ.get("ADMIN_EMAIL").lower(),
                 password=hashed_password,
                 birth_date="1987-11-11", country_name="South Africa", currency_symbol="R", verified=True, is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print("Admin Account created!!!")


def register_user(username, email, password, date_of_birth, user, goal, finances, money, state, verification, db):
    hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=4)
    new_user = user(username=username,
                    email=email,
                    password=hashed_password,
                    birth_date=date_of_birth,
                    country_name=state,
                    currency_symbol=money,
                    verified=verification)
    db.session.add(new_user)
    db.session.commit()
    registered_user = user.query.filter_by(username=username).first()
    if registered_user:
        new_user_goals = goal(user_id=registered_user.id)
        new_user_finances = finances(user_id=registered_user.id)
        db.session.add(new_user_goals)
        db.session.add(new_user_finances)
        db.session.commit()
        return redirect(url_for('registration_success'))


def login(name, entered_password, user):
    main_user = user.query.filter_by(email=name).first()
    if not main_user:
        flash("The email or password is incorrect.")
        return redirect(url_for('implements_login'))
    elif main_user and main_user.verified != 1:
        flash("You need to verify your account before logging in.")
        return redirect(url_for('implements_login'))
    elif main_user:
        main_user_password = check_password_hash(pwhash=main_user.password, password=entered_password)
        if not main_user_password:
            flash("The username or password is incorrect.")
            return redirect(url_for('implements_login'))
        elif main_user_password and main_user.verified == 1:
            login_user(user=main_user)
            print(main_user.id)
            return redirect(url_for('home'))
