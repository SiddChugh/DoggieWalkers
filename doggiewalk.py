# Basic Flask Functionality should be added to this file
import os
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms import *
from passlib.hash import sha256_crypt # Used for password encryption
from flask.ext.via import Via
from functools import wraps
from sqlalchemy.dialects.postgresql import JSON
from models import db, User, mail, Event, Review, Dm, Dog
import psycopg2
from flask.ext.mail import Mail, Message
from flask_socketio import SocketIO, send, emit
from io import BytesIO
from shutil import copyfile
import logging
import psycopg2
import datetime
import time
import base64
import os
import re
import uuid
import shutil

POSTGRES = {
    'user': 'vagrant',
    'pw': 'vagrant',
    'db': 'projectdb',
    'host': 'localhost',
    'port': '5432',
}

app = Flask(__name__)
#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.secret_key='cmpt470'

app.config['VIA_ROUTES_MODULE'] = 'routes'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cmpt470doggiewalk@gmail.com'
app.config['MAIL_PASSWORD'] = 'doggiewalk'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
via = Via()
via.init_app(app)

db.init_app(app)
app.app_context().push()
db.create_all()
mail.init_app(app)

socketio = SocketIO(app)
@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    send(msg, broadcast = True)
    #emit(msg)

def makeImageDirectories(user_id):
    # Check if user image directories are made
    directory1 = 'static/images/user/' + user_id + '/profile'
    directory2 = 'static/images/user/' + user_id + '/dog'
    directory3 = 'static/images/user/' + user_id + '/general'
    if not os.path.exists(directory1):
        os.makedirs(directory1)
    if not os.path.exists(directory2):
        os.makedirs(directory2)
    if not os.path.exists(directory3):
        os.makedirs(directory3)

    # Set default profile picture
    list = os.listdir(directory1 + '/') # dir is your directory path
    number_files = len(list)

    if number_files < 1:
        default_path = 'static/images/thumb/user.png'

        # Remove current picture (including folder)
        shutil.rmtree(directory1)
        os.makedirs(directory1)

        copyfile(default_path, directory1 + '/profile.jpg')

# This function will helps us add dummy data to our database
def dummy_db_data():
    # Deleting all existing users will cause ids to change
    safe_add_user(User(email="mchaudhr@sfu.ca",
            password=sha256_crypt.hash("123456"),
            first_name="Fahd",
            last_name="Chaudhry",
            date_of_birth="01/02/1999",
            city = 'Burnaby',
            willing_to_walk = "Yes",
            latitude='49.269914',
            longitude='-122.954904'))

    safe_add_user(User(email="schugh@sfu.ca",
            password=sha256_crypt.hash("123456"),
            first_name="Siddharth",
            last_name="Chugh",
            date_of_birth="01/02/1999",
            city = 'West Vancouver',
            willing_to_walk = "No",
            latitude='49.328625',
            longitude='-123.160198'))

    safe_add_user(User(email="user1@sfu.ca",
            password=sha256_crypt.hash("123456"),
            first_name="User",
            last_name="One",
            date_of_birth="01/02/1999",
            city = 'Vancouver',
            willing_to_walk = "Yes",
            latitude='49.26967',
            longitude='-123.07725'))

    safe_add_user(User(email="user2@sfu.ca",
            password=sha256_crypt.hash("123456"),
            first_name="User",
            last_name="Two",
            date_of_birth="01/02/1999",
            city = 'Vancouver',
            willing_to_walk = "Yes",
            latitude='49.26866',
            longitude='-123.07865'))

    safe_add_user(User(email="user3@sfu.ca",
            password=sha256_crypt.hash("123456"),
            first_name="User",
            last_name="Three",
            date_of_birth="01/02/1999",
            city = 'Vancouver',
            willing_to_walk = "Yes",
            latitude='49.26773',
            longitude='-123.07707'))
    
    userA = User.query.filter_by(email="mchaudhr@sfu.ca").first()
    userB = User.query.filter_by(email="schugh@sfu.ca").first()
    user1 = User.query.filter_by(email="user1@sfu.ca").first()
    user2 = User.query.filter_by(email="user2@sfu.ca").first()
    user3 = User.query.filter_by(email="user3@sfu.ca").first()
    
    # Dummy data for dog1 for fahd
    safe_add_dog(Dog(name="Rover",
                age=7,
                breed="German Shepherd",
                owner="mchaudhr@sfu.ca"
                ))

    # Dummy data for dog2 for Fahd
    safe_add_dog(Dog(name="Coco",
                age=4,
                breed="German Shepherd",
                owner="mchaudhr@sfu.ca"
                ))
    safe_add_dog(Dog(name="Lily",
                age=4,
                breed="Golden Retriever",
                owner=userB.email
                ))
    safe_add_dog(Dog(name="Rusty",
                age=2,
                breed="Corgi",
                owner="user1@sfu.ca"
                ))

    safe_add_dog(Dog(name="Petunia",
                age=8,
                breed="Chihuahua",
                owner="user1@sfu.ca"
                ))
    safe_add_dog(Dog(name="Buster",
                age=3,
                breed="Pit bull",
                owner="user2@sfu.ca"
                ))
    safe_add_dog(Dog(name="Dorsen",
                age=1,
                breed="Samoyed",
                owner="user3@sfu.ca"
                ))
    safe_add_dog(Dog(name="Rex",
                age=2,
                breed="Dalmatian",
                owner="user3@sfu.ca"
                ))

    safe_add_review(Review(
                rating=5,
                title="Love 'em",
                comment='''Simply amazing. He is
                a genius at walking dogs. I have 101 beautiful dalmatians, and
                he was able to walk them all at once. I swear their coats are
                shinier than ever. Amazing worker.
                ''',
                authorid=userB.id,
                receiverid=userA.id
                ))
    safe_add_review(Review(
                rating=3,
                title="Meh",
                authorid=user1.id,
                receiverid=userA.id
                ))
    safe_add_review(Review(
                rating=3,
                title="Meh meh",
                comment="asdfasdf",
                authorid=user2.id,
                receiverid=userB.id
                ))
    safe_add_review(Review(
                rating=5,
                title="Great",
                comment="I think they're great",
                authorid=userB.id,
                receiverid=user1.id
                ))
    safe_add_review(Review(
                rating=4,
                title="Not bad",
                comment="Not bad at all",
                authorid=user3.id,
                receiverid=user1.id
                ))
    delete_all(Event)
    event1 = Event(
                title="Walked Fahd's dog",
                body="walked coco",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=user1.email)
    event2 = Event(
                title="Walked Fahd's dog",
                body="walked rover",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=user2.email)
    event3 = Event(
                title="Met user 2",
                body="we talked about dog walking",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=user3.email)
    event4 = Event(
                title="Met user 3",
                body="we talked about dogs",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=userB.email)
    event5 = Event(
                title="Met user 1",
                body="We decided on a dog walking schedule.",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=userA.email)
    event6 = Event(
                title="Took Rover to the vet",
                body="I was worried!",
                city="Vancouver",
                latitude="49.2608724",
                longitude="-123.1139529",
                author=userA.email)
    db.session.add(event1)
    db.session.add(event2)
    db.session.add(event3)
    db.session.add(event4)
    db.session.add(event5)
    db.session.add(event6)
    db.session.commit()

def initialize_admin_user():
    admin_email = 'admin@example.test'
    user = User.query.filter_by(email=admin_email).first()
    if user is None:
        admin = User(email=admin_email,
                password=sha256_crypt.hash('password'),
                first_name='Admin',
                last_name='User',
                date_of_birth="01/02/1999",
                city = 'West Vancouver',
                willing_to_walk = "No",
                latitude='49.328625',
                longitude='-123.160198'
                )
        db.session.add(admin)
        db.session.commit()

	user_info = User.query.filter_by(email=admin_email).first()
	makeImageDirectories(str(user_info.id))

# safe_add_X checks if obj with model X exists in db before adding
def safe_add_user(user):
    db_user = User.query.filter_by(email=user.email).first()
    if db_user is None:
		db.session.add(user)
		db.session.commit()
		makeImageDirectories(str(User.query.filter_by(email=user.email).first().id))

# assumes owner will not have multiple dogs with same name
def safe_add_dog(dog):
    db_dog = Dog.query.filter_by(name=dog.name, owner=dog.owner).first()
    if db_dog is None:
        db.session.add(dog)
        db.session.commit()

# assumes person will not have multiple reviews with same title on same person
def safe_add_review(review):
    db_review = Review.query.filter_by(authorid=review.authorid, receiverid=review.receiverid, title=review.title).first()
    if db_review is None:
        db.session.add(review)
        db.session.commit()

def delete_all_users():
    delete_all(User)

def delete_all(model):
    for item in model.query.all():
        db.session.delete(item)
    db.session.commit()

dummy_db_data()
initialize_admin_user()



if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    port = int(os.environ.get('PORT', 5002))

    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://DB_USER:PASSWORD@HOST/DATABASE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    db.init_app(app)
    socketio.run(app,host='0.0.0.0', port=port, debug=True )
    #app.run(host='0.0.0.0', port=port, debug=True)
