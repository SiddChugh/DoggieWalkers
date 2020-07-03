from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from flask.ext.mail import Mail, Message

db = SQLAlchemy()
mail = Mail()


class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True, unique=True)
	email = db.Column(db.String(100), unique=True, nullable=False)
	password = db.Column(db.String(100), nullable=False)
	first_name = db.Column(db.String(100), nullable=False)
	last_name = db.Column(db.String(100), nullable=False)
	date_of_birth = db.Column(db.DateTime(), nullable=False)
	city = db.Column(db.String(100))
	events = db.relationship("Event")
	willing_to_walk = db.Column(db.String(3))
	latitude =db.Column(db.Float)
	longitude =db.Column(db.Float)
	def __repr__(self):
		return  '%s %s %s %s %s %s %s %s %s %s' %(self.id, self.email, self.password, self.first_name, self.last_name, self.date_of_birth, self.city, self.willing_to_walk, self.latitude, self.longitude)

class Dog(db.Model):
	__tablename__ = 'dogs'
	id = db.Column(db.Integer, primary_key=True, unique=True)
	name = db.Column(db.String(50), nullable=False)
	age = db.Column(db.Integer, unique=False, nullable=False)
	breed = db.Column(db.String(50))
	owner = db.Column(db.String(50), db.ForeignKey(User.email))
	ownerObj = db.relationship("User",  backref=db.backref("dogs", cascade="all, delete-orphan"), lazy = True, foreign_keys=[owner])
	dateAdded = db.Column(db.TIMESTAMP)
	#def __init__(self, *args):
	#    super().__init__(*args)
	def __repr__(self):
		return  '%s %s %s %s %s %s' %(self.id, self.name, self.age, self.breed, self.owner, self.dateAdded)

def updatedAtDefault(context):
	return context.get_current_parameters()['createdAt']

class Event(db.Model):
	__tablename__ = 'events'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(50), nullable=False)
	body = db.Column(db.Text(), nullable=False)
	author = db.Column(db.String(50), db.ForeignKey('users.email'))
	createdAt = db.Column(db.TIMESTAMP, default=datetime.utcnow)
	updatedAt = db.Column(db.DateTime(), default=updatedAtDefault)
	city = db.Column(db.String(50))
	latitude =db.Column(db.Float)
	longitude =db.Column(db.Float)
	def __repr__(self):
		return  '%s %s %s %s ' %(self.id, self.title, self.author, self.createdAt)

class Dm(db.Model):
	__tablename__ = 'dm'
	id = db.Column(db.Integer, primary_key=True)
	message = db.Column(db.Text(), unique=False, nullable=False)
	sender = db.Column(db.String(100), db.ForeignKey('users.email'))
	receiver = db.Column(db.String(100), db.ForeignKey('users.email'))
	dateTime = db.Column(db.TIMESTAMP, default=datetime.utcnow)
	def __repr__(self):
		return  '%s %s %s %s %s' %(self.id, self.body, self.sender, self.receiver, self.sentDateTime)

class Review(db.Model):
	__tablename__ = 'reviews'
	id = db.Column(db.Integer, primary_key=True)
	rating = db.Column(db.Integer)
	title = db.Column(db.String(50), nullable=False)
	comment = db.Column(db.Text)
	authorid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	receiverid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	author = db.relationship("User",  backref=db.backref("authors", cascade="all, delete-orphan"), lazy = True, foreign_keys=[authorid])
	receiver = db.relationship("User", backref=db.backref("reviewees", cascade="all, delete-orphan"), lazy = True, foreign_keys=[receiverid])
	createdAt = db.Column(db.DateTime, default=datetime.utcnow)
	updatedAt = db.Column(db.DateTime, default=updatedAtDefault)
	def __repr__(self):
		return  '%s %s %s %s' %(self.id, self.title, self.rating, self.reviewerid)
