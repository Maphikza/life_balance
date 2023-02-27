from flask import url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user


def register_user(username, email, password, date_of_birth, user, goal, finances, money, verification, db):
    hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=4)
    new_user = user(username=username,
                    email=email,
                    password=hashed_password,
                    birth_date=date_of_birth,
                    country=money,
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
        flash("You're registered.")
        return redirect(url_for('implements_login'))


def login(name, entered_password, user):
    main_user = user.query.filter_by(username=name).first()
    if not main_user:
        flash("The username or password is incorrect.")
        return redirect(url_for('implements_login'))
    elif main_user:
        main_user_password = check_password_hash(pwhash=main_user.password, password=entered_password)
        if not main_user_password:
            flash("The username or password is incorrect.")
            return redirect(url_for('implements_login'))
        elif main_user_password:
            login_user(user=main_user)
            return redirect(url_for('home'))