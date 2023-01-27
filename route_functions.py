from flask import url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user


def register_user(username, email, password, date_of_birth, user, goal, finances, db):
    hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=4)
    new_user = user(username=username, email=email, password=hashed_password, birth_date=date_of_birth)
    db.session.add(new_user)
    db.session.commit()
    registered_user = user.query.filter_by(username=username).first()
    print(registered_user.id)
    if registered_user:
        new_user_goals = goal(user_id=registered_user.id)
        new_user_finances = finances(user_id=registered_user.id)
        db.session.add(new_user_goals)
        db.session.add(new_user_finances)
        db.session.commit()
        flash("You're registered.")
        return redirect(url_for('implements_login'))
    # return "User {} was successfully registered.".format(username)


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


def add_purpose(driving_purpose, db, id_no, goal):
    purpose_edit = goal.query.get(id_no)
    purpose_edit.purpose = driving_purpose
    db.session.commit()
    return redirect(url_for('goals'))


def add_spirituality(the_spirit, db, id_no, goal):
    spirit_edit = goal.query.get(id_no)
    spirit_edit.spiritual = the_spirit
    db.session.commit()
    return redirect(url_for('goals'))


def add_mental(the_mind, db, id_no, goal):
    mental_edit = goal.query.get(id_no)
    mental_edit.mental = the_mind
    db.session.commit()
    return redirect(url_for('goals'))


def add_physical(the_body, db, id_no, goal):
    body_edit = goal.query.get(id_no)
    body_edit.physical_health = the_body
    db.session.commit()
    return redirect(url_for('goals'))
