from flask import url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user


def register_user(username, email, password, date_of_birth, user, db):
    hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=4)
    new_user = user(username=username, email=email, password=hashed_password, birth_date=date_of_birth)
    db.session.add(new_user)
    db.session.commit()
    registered_user = user.query.filter_by(username=username).first()
    if registered_user:
        flash("You're registered.")
        return redirect(url_for('implements_login'))
    # return "User {} was successfully registered.".format(username)


def login(name, entered_password, user):
    main_user = user.query.filter_by(username=name).first()
    if not main_user:
        flash("The username or password is incorrect.")
        return redirect(url_for('implements_login'))
    elif main_user:
        print(main_user.password)
        print(entered_password)
        main_user_password = check_password_hash(pwhash=main_user.password, password=entered_password)
        print(main_user_password)
        if not main_user_password:
            flash("The username or password is incorrect.")
            return redirect(url_for('implements_login'))
        elif main_user_password:
            print("user_logged in.")
            login_user(user=main_user)
            return redirect(url_for('home'))


def add_connection(connect_name, relationship, date_of_birth, thoughts_on_relationships, connection, db, id_no):
    new_connection = connection(name=connect_name,
                                relationship_to_user=relationship,
                                birth_date=date_of_birth,
                                relationship_thoughts=thoughts_on_relationships, user_id=id_no)
    db.session.add(new_connection)
    db.session.commit()
    return redirect(url_for('connections'))


