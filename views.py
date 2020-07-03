# -*- coding: UTF-8 -*-
from flask import request, render_template, redirect, url_for, session, flash, Flask, abort, send_file
from flask.views import View, MethodView
from flask_sqlalchemy import *
from wtforms import *
from wtforms.fields.html5 import DateField
from functools import wraps
from passlib.hash import sha256_crypt # Used for password encryption
from models import *
from flask.ext.mail import Mail, Message
from geopy.geocoders import Nominatim
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
from smtplib import SMTPException


# Used to get urls for image uploads
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
# Check if user is logged in
def is_logged_in(f):
    # From Python wraps library
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Home Page
# Page Not Found will show up if this is not defined
def index():
    return render_template('home.html')

@is_logged_in
def dashboard():
    events = Event.query.all()
    return render_template('dashboard.html', events=events)

# User Registration Form Class (Registration uses wtforms library)
class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=5, max=50), validators.DataRequired()])
    date_of_birth = DateField('Date Of Birth ', [validators.DataRequired()])

    city = SelectField('City', choices = [('Burnaby', 'Burnaby'),('White Rock', 'White Rock'),('Ladner', 'Ladner'),('Delta', 'Delta'),('Richmond', 'Richmond'),('Langley', 'Langley'), ('Coquitlam', 'Coquitlam'), ('Port Coquitlam', 'Port Coquitlam'), ('Port Moody', 'Port Moody'), ('Maple Ridge', 'Maple Ridge'), ('Surrey', 'Surrey'), ('Vancouver', 'Vancouver'), ('North Vancouver', 'North Vancouver'), ('West Vancouver', 'West Vancouver')])

    willing_to_walk = SelectField('Are you willing to walk dogs?', choices=[('Yes','Yes'), ('No','No')])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_pass', message='Passwords do not match.')
    ])
    confirm_pass = PasswordField('Confirm Password')

def validateDOB(DOB):
    strDOB= str(DOB)
    newDOB= strDOB.split('-')
    
    if (newDOB[0] < '1900'):
        DOB= DOB.replace(year=1900)
    return DOB  

class RegisterAPI(MethodView):
    def post(self):
        form = RegisterForm(request.form)
        email_input = form.email.data
        user = User.query.filter_by(email=email_input).first()
        error = None

        # Check if account already exists with entered email
        if user is not None:
            error = 'An account already exists with that email.'

        form.date_of_birth.data=validateDOB(form.date_of_birth.data)    
        if form.validate() and error is None:
            citystr = str(form.city.data)
            walk = str(form.willing_to_walk.data)

            geolocator = Nominatim(user_agent='DoggieWalk')
            location = geolocator.geocode(citystr)
            latitude = location.latitude
            longitude = location.longitude

            # # Add new user
            newuser = User(email=form.email.data,
                            password=sha256_crypt.hash(form.password.data),
                            first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            date_of_birth=form.date_of_birth.data,
                            city= citystr,
                            willing_to_walk=walk,
                            latitude=latitude,
                            longitude=longitude
                            )
            db.session.add(newuser)
            db.session.commit()

            # Send a welcome email message to new user
            try:
                msg = Message('Welcome Email', sender = 'cmpt470doggiewalk@gmail.com', recipients = str(newuser.email).split())
                msg.body = "Welcome to Doggie Walk! Congrats on being a new member!"
                mail.send(msg)
                flash('Welcome E-mail sent successfully', 'success')
            except SMTPException, e:
                print e
            flash ('Your user registration is complete and can now log in!', 'success')
            return redirect(url_for('index'))
        else:
            return render_template('register.html', form=RegisterForm(request.form), error=error)
    def get(self):
        return render_template('register.html', form=RegisterForm(request.form))

class LoginAPI(MethodView):
    email = None
    @staticmethod
    def setEmail(email_input):
        LoginAPI.email = email_input

    @staticmethod
    def getEmail():
        return LoginAPI.email

    def post(self):
        # Get form fields for login Page
        email_input = request.form['email']
        password_candidate = request.form['password']
        LoginAPI.setEmail(email_input)
        # Get user by email
        user = User.query.filter_by(email=email_input).first()
        if user is not None:
            password = user.password
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Password valid (uses session library from Flask)
                session['logged_in'] = True
                session['email'] = email_input
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['user_id'] = user.id

                makeImageDirectories(str(user.id))

                flash('You are now logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password entered'
                return render_template('login.html', error=error)
        else:
            error = 'No account is associated with that email'
            return render_template('login.html', error=error)

    def get(self):
        return render_template('login.html')


# Logout page
@is_logged_in
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


# About page
def about():
    return render_template('about.html')

# Terms and Conditions page
def terms():
    return render_template('terms.html')

# Privacy Policy page
def privacy():
    return render_template('privacy.html')

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


class ContactUsForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=200)], default="admin@doggiwalk.ca")
    email = StringField('Email', [validators.Length(min=1, max=30)])
    message = TextAreaField('Message', [validators.Length(min=10)])


# Contact Us page
class ContactUsAPI(MethodView):
    def get(self):
        return render_template('contactUs.html', form=ContactUsForm(request.form))
    def post(self):
        form = ContactUsForm(request.form)
        if form.validate():
            name = form.name.data
            email = form.email.data
            message = form.message.data

            flash('Administrator has been notified', 'success')
            return redirect(url_for('index'))
        else:
            # todo error details
            flash('The form was incorrectly filled out', 'danger')
            return ContactUsAPI.get(self)
    def delete(self, id=None):
        return 'DELETE contacts page'

class UserProfileAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id):
        user_info = User.query.get_or_404(id)
        user_email = user_info.email
        
        dog_info = Dog.query.filter_by(owner=user_email).all()
        event_info = Event.query.filter_by(author=user_email).all()

        userProfImgLink = '/static/images/user/' + str(user_info.id) + '/profile/profile.jpg'

        conn_string = "host='localhost' dbname='projectdb' user='vagrant' password='vagrant'"
        cur = psycopg2.connect(conn_string)
        cursor = cur.cursor()
        cursor.execute("SELECT avg(rating) FROM reviews WHERE reviews.receiverid = " + str(id))
        data = cursor.fetchone()
        url= request.url.split('/')
        user_images = 'static/images/user/' + str(url[-2]) + '/general'
        image_names = os.listdir(user_images)

        if data[0] is None:
            myStars = 0
            hasHalfStar = False
        else:
            myStars = int(data[0])
            rounded = round(data[0] * 2) / 2 # round to nearest .5
            hasHalfStar = ((rounded * 2) % 2) == 1 # true if it ends in .5
        cursor.close()

        # Display message if no results found
        if user_info is not None:
            return render_template('user_profile.html', user_info=user_info, dogs=dog_info, events=event_info, stars=myStars, half=hasHalfStar, userProfImgLink=userProfImgLink, image_names=image_names, user_id=url[-2])

# User Registration Form Class (Registration uses wtforms library)
class UserInfoForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50), validators.DataRequired()])
    email = StringField('Email', [validators.Length(min=5, max=50), validators.DataRequired()])
    date_of_birth = DateField('Date Of Birth ', [validators.DataRequired()])

    city = SelectField('City', choices = [('Burnaby', 'Burnaby'), ('White Rock', 'White Rock'),('Ladner', 'Ladner'),('Delta', 'Delta'),('Richmond', 'Richmond'),('Langley', 'Langley'),('Coquitlam', 'Coquitlam'), ('Port Coquitlam', 'Port Coquitlam'), ('Port Moody', 'Port Moody'), ('Maple Ridge', 'Maple Ridge'), ('Surrey', 'Surrey'), ('Vancouver', 'Vancouver'), ('North Vancouver', 'North Vancouver'), ('West Vancouver', 'West Vancouver')])

    willing_to_walk = SelectField('Are you willing to walk dogs?', choices=[('Yes','Yes'), ('No','No')])

class UserProfileEditAPI(MethodView):
    # Member variables
    edit_user_info = None
    form = None

    @staticmethod
    # @is_logged_in # Checks if logged in
    # Sets form fields to load current user info
    def setFields(id):
        # Initiate query to get user profile
        edit_user_info = User.query.filter_by(id=id).first()
        # Request user profile form
        form = UserInfoForm(request.form)
        
        # Populate exisitng user info
        form.first_name.data = edit_user_info.first_name
        form.last_name.data = edit_user_info.last_name
        form.email.data = edit_user_info.email
        form.date_of_birth.data=validateDOB(edit_user_info.date_of_birth)
        form.city.data = edit_user_info.city
        form.willing_to_walk.data = edit_user_info.willing_to_walk

        UserProfileEditAPI.form = form
        UserProfileEditAPI.edit_user_info = edit_user_info

    @is_logged_in # Checks if logged in
    def get(self, id):
        if User.query.get(id) is None:
            abort(404)
        if id is not session['user_id']:
            abort(405)
        UserProfileEditAPI.setFields(id)
        return render_template('user_info_edit.html', form=UserProfileEditAPI.form)

    @is_logged_in # Checks if logged in
    def post(self, id):
        if User.query.get(id) is None:
            abort(404)
        if id is not session['user_id']:
            abort(405)

        UserProfileEditAPI.setFields(id)
        # if UserProfileEditAPI.form.validate():
        # Set as class member variable
        edit_user_info = UserProfileEditAPI.edit_user_info

        edit_user_info.first_name = request.form['first_name']
        session['first_name'] = edit_user_info.first_name
        edit_user_info.last_name = request.form['last_name']
        session['last_name'] = edit_user_info.last_name
        edit_user_info.email = request.form['email']
        # Update session email
        session['email'] = edit_user_info.email
        edit_user_info.date_of_birth = request.form['date_of_birth']
        edit_user_info.city = str(request.form['city'])
        edit_user_info.willing_to_walk = str(request.form['willing_to_walk'])
        db.session.commit()

        flash('User Information Updated Successfully', 'success')
        return redirect(url_for('user_profile', id=edit_user_info.id))

# User Image uploads
class UploadImageAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        return render_template('uploadImage.html')

    @is_logged_in # Checks if logged in
    def post(self, id=None):
        # Check if file selected
        if 'images' not in request.files:
            flash('No image(s) selected for uploading. Please select an image and try again.', 'danger')
            return render_template('uploadImage.html')

        userImagePath = 'static/images/user/' + str(session['user_id']) + '/general'
        target = os.path.join(APP_ROOT, userImagePath)

        if not os.path.isdir(target):
            os.mkdir(target)

        for file in request.files.getlist("images"):
            # Get each images filename
            filename = file.filename

            # Define the destination path (folder where image will be)
            destination = "/".join([target, filename])
            # Saves file(s) in destination
            file.save(destination)

        flash('Image(s) uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))

# Dog Image uploads
class UploadDogImageAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        return render_template('uploadDogImage.html')

    @is_logged_in # Checks if logged in
    def post(self, id=None):
        # Check if file selected
        if 'images' not in request.files:
            flash('No image(s) selected for uploading. Please select an image and try again.', 'danger')
            return render_template('uploadDogImage.html')

        # Make dog image directory
        dogImagePath = 'static/images/user/' + str(session['user_id']) + '/dog/' + str(session['dog_id'])

        target = os.path.join(APP_ROOT, dogImagePath)

        if not os.path.isdir(target):
            os.mkdir(target)

        for file in request.files.getlist("images"):
            # Get each images filename
            filename = file.filename

            # Define the destination path (folder where image will be)
            destination = "/".join([target, filename])
            # Saves file(s) in destination
            file.save(destination)

        flash('Image(s) uploaded successfully!', 'success')
        return redirect(url_for('dog_profile', id=session['dog_id']))

class MyImagesAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        user_images = 'static/images/user/' + str(session['user_id']) + '/general'
        image_names = os.listdir(user_images)
        return render_template('myImages.html', image_names=image_names)

# Single User Image page
class MyImageAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, file):
        image_path = '/static/images/user/' + str(session['user_id']) + '/general/' + file
        return render_template('myImage.html', image_name=file, image_path=image_path)

    @is_logged_in # Checks if logged in
    def post(self, file):
        images_path = 'static/images/user/' + str(session['user_id']) + '/general/'
        # Profile Picture change
        if 'makeProfile' in request.form:
            current_path = images_path + file
            profile_folder = 'static/images/user/' + str(session['user_id']) + '/profile/'
            profile_path = profile_folder + "/profile.jpg"

            # Remove current picture (including folder)
            shutil.rmtree(profile_folder)
            os.makedirs(profile_folder)

            # Copy currently select image to profile folder
            copyfile(current_path, profile_path)

            flash('Profile Picture Updated!', 'success')
        # Delete Image
        else:
            os.remove(images_path + file)
            flash('Image deleted successfully!', 'success')

        image_names=os.listdir(images_path)
        return render_template('myImages.html', image_names=image_names)

# Single Dog Image page
class MyDogImageAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, file):
        dog_info = Dog.query.get(session['dog_id'])
        user_info = User.query.filter_by(email=dog_info.owner).first()

        image_path = '/static/images/user/' + str(user_info.id) + '/dog/' + str(dog_info.id) + '/' + file
        return render_template('myDogImage.html', image_name=file, image_path=image_path, dog_info=dog_info)

    @is_logged_in # Checks if logged in
    def post(self, file):
        images_path = 'static/images/user/' + str(session['user_id']) + '/dog/' + str(session['dog_id']) + '/'

        # Profile Picture change
        if 'makeProfile' in request.form:
            current_path = images_path + file
            profile_folder = 'static/images/user/' + str(session['user_id']) + '/profile/'
            profile_path = profile_folder + "/profile.jpg"

            # Remove current picture (including folder)
            shutil.rmtree(profile_folder)
            os.makedirs(profile_folder)

            # Copy currently select image to profile folder
            copyfile(current_path, profile_path)

            flash('Profile Picture Updated!', 'success')
            return redirect(url_for('dog_profile', id=session['dog_id']))
        # Delete Image
        else:
            os.remove(images_path + file)
            flash('Image deleted successfully!', 'success')
            return redirect(url_for('dog_profile', id=session['dog_id']))

# Send Message Form
class SendMessageForm(Form):
    receiver = SelectField(u'Send To', coerce=int)
    message = TextAreaField('Message', [validators.required()])
# DM - Send a Message
class SendMessageAPI(MethodView):
    # Member variables
    userList = None
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        userList = User.query.filter(User.first_name != 'Admin').order_by('first_name').all()
        form = SendMessageForm(request.form)

        # Show all users in database (excluding Admin)
        # Current format for select field: User Email - first_name last_name
        form.receiver.choices = [(u.id, u.email + ' - ' + u.first_name + ' ' + u.last_name) for u in User.query.filter(User.first_name != 'Admin').order_by('first_name').all()]

        # Pass in values to member variable (will be used in the post request)
        SendMessageAPI.userList = userList

        return render_template('sendMessage.html', form=form)

    @is_logged_in # Checks if logged in
    def post(self, id=None):
        form = SendMessageForm(request.form)
        userList = SendMessageAPI.userList
        form.receiver.choices = [(u.id, u.email) for u in userList]

        receiverEmail = User.query.get(form.receiver.data).email

        if form.validate():
            newMessage = Dm(message = form.message.data,
                            sender = session['email'],
                            receiver = receiverEmail)
            db.session.add(newMessage)
            db.session.commit()

            # # Sends email notification to user that they received a new message
            try:
                msg = Message('Doggie Walk: New Message', sender = 'cmpt470doggiewalk@gmail.com', recipients = str(receiverEmail).split())
                msg.body = "A message from another user has been received on your Doggie Walk profile!"
                mail.send(msg)
            except SMTPException, e:
                print e
            flash('Message sent successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please ensure all fields are filled in appropriately.', 'danger')
            form = SendMessageForm(request.form)
            return render_template('sendMessage.html', form=form)

# DM - Received Messages
class InboxAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self):
        allMessages = Dm.query.filter_by(receiver=session['email']).all()
        return render_template('inbox.html', allMessages = allMessages)

# DM - Sent Messages
class SentAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self):
        sentMessages = Dm.query.filter_by(sender=session['email']).all()
        return render_template('sentMessages.html', sentMessages = sentMessages)

# Delete Message
class DeleteMessageAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id):
        if (id is not None):
            message_id = Dm.query.get(id)
            db.session.delete(message_id)
            db.session.commit()

            flash('Message deleted successfully', 'success')
            allMessages = Dm.query.filter_by(receiver=session['email']).all()
            return render_template('inbox.html', allMessages = allMessages)
        else:
            flash('Error: Could not delete the selected message. Please contact an administrator.', 'danger')
            return render_template('contactUs.html', form=ContactUsForm(request.form))

class DogsAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self):
        # Gets all dogs added by the current user
        dog_info = Dog.query.all()
        # Display message if no results found
        if dog_info is not None:
            return render_template('all_dogs.html', dogs=dog_info)
        else:
            flash('Error: Could not retreive user details. Please contact an administrator.', 'danger')
            return render_template('contactUs.html', form=ContactUsForm(request.form))

class AddDogForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    age = IntegerField('Age (months)', [validators.required()])
    breed = StringField('Breed', [validators.Length(min=1, max=50)])

class AddDogAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        title = "Add Dog Profile"
        form = AddDogForm(request.form)
        return render_template('add_dog.html', form=form, title=title)

    @is_logged_in # Checks if logged in
    def post(self, id=None):
        form = AddDogForm(request.form)
        if form.validate():
            dog = Dog(name=request.form['name'], age=request.form['age'], breed=request.form['breed'], owner=session['email'])
            db.session.add(dog)
            db.session.commit()

            # Make dog image directory
            dogImagePath = 'static/images/user/' + str(session['user_id']) + '/dog/' + str(dog.id)
            target = os.path.join(APP_ROOT, dogImagePath)

            if not os.path.isdir(target):
                os.mkdir(target)

            flash('Your Dogs Profile Has Been Created Successfully', 'success')
            return render_template('dashboard.html')
        else:
            flash('Please ensure all fields are filled in appropriately.', 'danger')
            form = AddDogForm(request.form)
            return render_template('add_dog.html', form=form)

# Individual Dog Profile
class DogProfileAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id):
        # Gets dog by id
        dog_info = Dog.query.get(id)

        # Get user info (needed to display images for non owner user)
        user_info = User.query.filter_by(email=dog_info.owner).first()
        
        # Display message if no results found
        if dog_info is not None:
            # Create dogID session variable (used to make dog directories)
            session['dog_id'] = dog_info.id

            dog_images = 'static/images/user/' + str(user_info.id) + '/dog/' + str(dog_info.id)

            target = os.path.join(APP_ROOT, dog_images)

            # Make dog path if not made yet
            if not os.path.isdir(target):
                os.mkdir(target)

            image_names = os.listdir(dog_images)
            return render_template('dog_profile.html', dog=dog_info, image_names=image_names, user_info=user_info)
        else:
            flash('Error: Could not retreive the specific dog''s details. Please contact an administrator.', 'danger')
            return render_template('contactUs.html', form=ContactUsForm(request.form))

    @is_logged_in # Checks if logged in
    def post(self, id): # Delete Dog Profile
        if (id is not None):
            dog_id = Dog.query.get(id)
            db.session.delete(dog_id)
            db.session.commit()

            flash('Successfully deleted the selected Dog Profile.', 'success')
            return render_template('dashboard.html')
        else:
            flash('Error: Could not retreive the specific dog''s ID to delete. Please contact an administrator.', 'danger')
            return render_template('contactUs.html', form=ContactUsForm(request.form))


class DogProfileEditAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id): # Edit Dog Profile
        if (id is not None):
            # Initiate query to get dog info
            dog_info = Dog.query.filter_by(id=id).first()
            # Request user profile form
            form = AddDogForm(request.form)

            # Populate exisitng user info
            form.name.data = dog_info.name
            form.age.data = dog_info.age
            form.breed.data = dog_info.breed

            title = "Edit Dog Profile"
            return render_template('add_dog.html', form=form, title=title)
        else:
            flash('Error: Could not retreive the specific dog''s ID to edit. Please contact an administrator.', 'danger')
            return render_template('contactUs.html', form=ContactUsForm(request.form))

    @is_logged_in # Checks if logged in
    def post(self, id):
        if (id is not None):
            dog_info = Dog.query.filter_by(id=id).first()

            dog_info.name = request.form['name']
            dog_info.age = request.form['age']
            dog_info.breed = request.form['breed']
            db.session.commit()

            flash('Dog Profile Updated Successfully', 'success')
            return redirect(url_for('dog_profile', id=id))

class ContentAPI(MethodView):
    def get(self, id=None):
        model = self.model
        template_name = self.template_name
        if id is None:
            abort(404)
            #return list of resources
            #content_list = model.query.all()
            #return render_template(template_name + '_list.html')
        else:
            # return resource with id
            content = model.query.get(id)
            if (content is None):
                abort(404)
            return render_template(template_name + '.html')

    def put(self, id=None):
        # modify resource with id
        if id is not None:
            return 'put ' + str(id)

    def post(self):
        # create a new resource
        return 'post'

    def delete(self, id=None):
        # delete resource with id
        if id is not None:
            return 'delete ' + str(id)

class ReviewView():
    def __init__(self, basequery):
        self.rating = basequery.rating
        author = User.query.get(basequery.authorid)
        self.author = author.first_name + " " + author.last_name
        self.authorid = basequery.authorid
        self.title = basequery.title
        self.createdAt = basequery.createdAt
        self.updatedAt = basequery.updatedAt
        self.id = basequery.id
        self.comment = basequery.comment

class ReviewAPI(ContentAPI):
    template_name = "review"
    @is_logged_in # Checks if logged in
    def get(self, id=None, review_id=None):
        template_name = self.template_name
        if id is not None:
            # get user
            user = User.query.get_or_404(id)
            if review_id is None:
                reviews_result = Review.query.filter_by(receiverid=id)
                reviews = []
                for res in reviews_result:
                    review = ReviewView(res)
                    reviews.append(review)
                return render_template(template_name + '_list.html', reviews=reviews, user=user)
            else:
                review_res = Review.query.filter_by(id=review_id).first_or_404()
                review = ReviewView(review_res)
                if review.comment is None:
                    review.comment = ""
                return render_template(template_name + '.html', review=review)
        abort(404)

class reviewForm(Form):
    rating = SelectField(label='Rating', choices=[(i,u"⭐" * i) for i in range(1,6)])
    title = StringField('Title', [validators.Length(min=5, max=50)])
    body = TextAreaField('Body', [])

class AddReviewAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id):
        form = reviewForm(request.form)
        receiver = User.query.get_or_404(id)
        return render_template('add_review.html', form=form, name=receiver.first_name + " " + receiver.last_name)

    @is_logged_in # Checks if logged in
    def post(self, id):
        form = reviewForm(request.form)
        receiver = User.query.get_or_404(id)
        if form.title.validate(form) and form.body.validate(form):
            newreview = Review(
                        rating=form.rating.data,
                        title=form.title.data,
                        comment=form.body.data,
                        authorid=session['user_id'],
                        receiverid=id
                        )
            db.session.add(newreview)
            db.session.commit()

            newMessage = Dm(message = 'you have recieved a new review!',
                            sender = session['email'],
                            receiver = receiver.email)
            db.session.add(newMessage)
            db.session.commit()

            flash('Review Created Successfully', 'success')
            return redirect(url_for('reviews_list', id=id))
        else:
            return render_template('add_review.html', form=form, name=receiver.first_name + " " + receiver.last_name)

# Search page
class search(MethodView):
    def get(self):
        base_url= request.base_url
        len_baseh_url= len(request.base_url) + 8
        searchParam = request.url[len_baseh_url:]
        if len(searchParam) == 0:
             return render_template("home.html") # show no results

        #For getting users by either first or last name
        if (searchParam[0] == '+'):
            searchParam=searchParam[1:]

        splitSearchParam=searchParam.split('+')
        firstName=splitSearchParam[0]
        getUserByFirstName = User.query.filter(User.first_name.ilike(firstName)).all()
        getUserByLastName = User.query.filter(User.last_name.ilike(firstName)).all()


        if ('+' in searchParam):
            lastName=splitSearchParam[1]
            getUserByLastName = User.query.filter(User.last_name.ilike(lastName)).all()
            for i in getUserByFirstName:
                for j in getUserByLastName:
                    if ((i.id) == (j.id)):
                        getUserByLastName.remove(j)

        #for getting users by email
        getUserbyemail=None
        if ('%' in firstName):
            email= re.sub("%", "@", firstName)
            splitemail = email.split('@')
            splitemailNumbers = re.sub("1|2|3|4|5|6|7|8|9|0", "", splitemail[1])
            splitemail[0] += '@'
            splitemail[0] += (splitemailNumbers)
            getUserbyemail=User.query.filter(User.email.ilike(splitemail[0])).all()

        #for getting events and users by the city
        getEventbyCity=None
        getUserbyCity=None
        if ('+' in searchParam):
            city = searchParam.split('+')
            city = city[0]+' '+city[1]
        else:
            city=searchParam
  
        getEventbyCity = Event.query.filter(Event.city.ilike(city)).all()
        getUserbyCity = User.query.filter(User.city.ilike(city)).all()

        #for getting events by name
        if ('+' in searchParam):
            eventName = searchParam.split('+')
            finalEventName=''
            for  i in range(len(eventName)):
                finalEventName+=str(eventName[i])
                finalEventName+=' '
            finalEventName= finalEventName[:len(finalEventName)-1]
            getEventbyName = Event.query.filter(Event.title.ilike(finalEventName)).all()
        else:
            getEventbyName = Event.query.filter(Event.title.ilike(searchParam)).all()

        #for getting dog by breeds
        if ('+' in searchParam):
            breed = searchParam.split('+')
            breed = breed[0]+' '+breed[1]
        else:
            breed=searchParam
        getDogByBreed = Dog.query.filter(Dog.breed.ilike(breed)).all()
        if not getUserByFirstName:
            getUserByFirstName = None
        if not getUserByLastName:
            getUserByLastName = None
        if not getUserbyemail:
            getUserbyemail = None
        if not getEventbyCity:
            getEventbyCity = None
        if not getDogByBreed:
            getDogByBreed = None
        if not getEventbyName:
            getEventbyName = None
        if not getUserbyCity:
            getUserbyCity = None
        return render_template("search.html", firstName=getUserByFirstName, lastName=getUserByLastName, email=getUserbyemail, eventByCity=getEventbyCity, userByCity=getUserbyCity, eventByName=getEventbyName, dogByBreed=getDogByBreed)

    def post(self):
        return "<h1> Hello search </h1>"

class eventForm(Form):
    title = StringField('Title', [validators.Length(min=5, max=50)])
    body = TextAreaField('Body', [validators.Length(min=5)])
    city = SelectField('City', choices = [('Burnaby', 'Burnaby'), ('White Rock', 'White Rock'),('Ladner', 'Ladner'),('Delta', 'Delta'),('Richmond', 'Richmond'),('Langley', 'Langley'),('Vancouver', 'Vancouver'), ('North Vancouver', 'North Vancouver'), ('West Vancouver', 'West Vancouver'), ('Coquitlam', 'Coquitlam',), ('Port Coquitlam', 'Port Coquitlam'), ('Port Moody', 'Port Moody'), ('Surrey, Canada', 'Surrey')])

class EventAPI(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        if id is None:
            form = eventForm(request.form)
            return render_template('add_event.html', form=form)
        else:
            event= Event.query.get_or_404(id)
            return render_template('/events.html', event=event)

    @is_logged_in # Checks if logged in
    def post(self):
        form = eventForm(request.form)
        title = form.title.data
        body = form.body.data
        if form.title.validate(form) and form.body.validate(form):
            citystr = str(form.city.data)
            geolocator = Nominatim(user_agent='DoggieWalk')
            location = geolocator.geocode(citystr)
            latitude = location.latitude
            longitude = location.longitude
            postEvent = Event(title=title, body=body, author=session['email'], createdAt=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),city= citystr,
                            latitude=latitude,
                            longitude=longitude)
            db.session.add(postEvent)
            db.session.commit()

            flash('Event Created Successfully', 'success')
            return redirect(url_for('dashboard'))
        elif not(form.title.validate(form)):
            return render_template('add_event.html', form=form)
        elif not(form.body.validate(form)):
            return render_template('add_event.html', form=form)
        else:
            flash('Some unexpected error occured. Please contact the administrator', 'danger')
            return render_template('contactUs.html')

class EditEventAPI(MethodView):
    editEventId = None

    @staticmethod
    @is_logged_in # Checks if logged in
    def setId(id_input):
        EditEventAPI.editEventId = id_input

    @is_logged_in # Checks if logged in
    def get(self, id=None):
        event= Event.query.get(id)
        form = eventForm(formdata=request.form, obj=event)
        EditEventAPI.setId(event.id)
        return render_template('add_event.html', form=form)

    @is_logged_in # Checks if logged in
    def post(self, id=None):
        form = eventForm(request.form)
        title = form.title.data
        body = form.body.data
        getEvent = Event.query.get(EditEventAPI.editEventId)
        getUser = User.query.filter_by(email=EditEventAPI.editEventId)
        if form.title.validate(form) and form.body.validate(form) and getEvent.author == LoginAPI.getEmail():
            eventCreatedAt=getEvent.createdAt
            db.session.delete(getEvent)
            db.session.commit()
            postEvent = Event(id=EditEventAPI.editEventId, title=title, body=body, author=LoginAPI.getEmail(), updatedAt=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), createdAt=eventCreatedAt)
            db.session.add(postEvent)
            db.session.commit()
            flash('Event Created Successfully', 'success')
            return redirect(url_for('dashboard'))
        elif not(form.title.validate(form)):
            return render_template('add_event.html', form=form)
        elif not(form.body.validate(form)):
            return render_template('add_event.html', form=form)
        elif not(getEvent.author == LoginAPI.getEmail()):
            flash('You can only edit your own events', 'danger')
            return redirect(url_for('dashboard'))
        else:
            flash('Some unexpected error occured. Please contact the administrator', 'danger')
            return render_template('contactUs.html')

class remove(MethodView):
    @is_logged_in # Checks if logged in
    def get(self, id=None):
        getEvent = Event.query.get(id)
        if getEvent.author == LoginAPI.getEmail():
            db.session.delete(getEvent)
            db.session.commit()
            return redirect(url_for('dashboard'))
        elif not(getEvent.author == LoginAPI.getEmail()):
            flash('You can only delete your own events', 'danger')
            return redirect(url_for('dashboard'))
        else:
            flash('Some unexpected error occured. Please contact the administrator', 'danger')
            return render_template('contactUs.html')

@is_logged_in # Checks if logged in
def dog_walkers():
    conn_string = "host='localhost' dbname='projectdb' user='vagrant' password='vagrant'"
    cur = psycopg2.connect(conn_string)
    cursor = cur.cursor()
    t = str('Yes').split()
    cursor.execute("SELECT email, first_name, last_name, id, city FROM Users WHERE willing_to_walk = %s", (t))
    data = cursor.fetchall()
    cursor.close()
    return render_template('dogwalkers.html', datas=data)

@is_logged_in # Checks if logged in
def dog_owners():
    conn_string = "host='localhost' dbname='projectdb' user='vagrant' password='vagrant'"
    cur = psycopg2.connect(conn_string)
    cursor = cur.cursor()
    t = str('Yes').split()
    cursor.execute("SELECT email, name, breed, Users.id, Dogs.id, city FROM Users, Dogs WHERE Users.email = Dogs.owner")
    data = cursor.fetchall()
    cursor.close()
    return render_template('dogowners.html', datas=data)

class ContentEdit(MethodView):
    def get(self, id):
        # return HTML form for editing resource
        return 'form for editing '+ str(id)

class ContentAPI(MethodView):
    def get(self, id):
        # return HTML form for editing resource
        return 'form for editing '+ str(id)
