from flask.ext.via.routers.default import Functional, Pluggable
from views import *

routes = [
	Functional('/', index),
	Functional('/about/', about),
	Functional('/terms/', terms),
	Functional('/privacy/', privacy),
	Pluggable('/login/', LoginAPI, 'login'),
	Pluggable('/register/', RegisterAPI, 'register'),
	Functional ('/dashboard', dashboard),

	Functional ('/dog_walkers', dog_walkers),
	Functional ('/dog_owners', dog_owners),

	Functional('/logout/', logout),
	
	Pluggable('/search/', search, 'search'),
	Pluggable('/contactUs/', ContactUsAPI, 'contact_us'),

	# Direct Messaging
	Pluggable('/sendMessage/', SendMessageAPI, 'send_message'),
	Pluggable('/Inbox',  InboxAPI, 'inbox'),
	Pluggable('/sentMessages',  SentAPI, 'sent'),
	Pluggable('/deleteMessage/<int:id>/',  DeleteMessageAPI, 'delete_message'),

	# Image Upload and Gallery (for Users and Dogs)
	Pluggable('/uploadImage', UploadImageAPI, 'upload_image'),
	Pluggable('/uploadDogImage', UploadDogImageAPI, 'upload_dog_image'),
	Pluggable('/myImages', MyImagesAPI, 'my_images'),
	Pluggable('/myImage/<string:file>', MyImageAPI, 'my_image'),
	Pluggable('/myImage/<string:file>', MyImageAPI, 'my_image_profile'),
	Pluggable('/myImage/<string:file>/delete', MyImageAPI, 'my_image_delete'),

	# User Profile
	Pluggable('/user_profile/<int:id>/', UserProfileAPI, 'user_profile'),
	Pluggable('/user_profile/<int:id>/edit/', UserProfileEditAPI, 'user_profile_edit'),

	Pluggable('/users/<int:id>/reviews/', ReviewAPI, 'reviews_list'),
	Pluggable('/users/<int:id>/reviews/new/', AddReviewAPI, 'reviews_new'),
	Pluggable('/users/<int:id>/reviews/<int:review_id>/', ReviewAPI, 'reviews'),
	Pluggable('/users/<int:id>/reviews/<int:review_id>/edit/', ReviewAPI, 'reviews_edit'),

	Pluggable('/events/', EventAPI, 'events_list'),
	Pluggable('/events/new/', EventAPI, 'events_new'),
	Pluggable('/events/<int:id>/', EventAPI, 'events'),
	Pluggable('/events/<int:id>/edit/', EditEventAPI, 'events_edit'),
	Pluggable ('/events/<int:id>/remove', remove, 'remove'),

	Pluggable('/dogs/', DogsAPI, 'dogs_all'),
	Pluggable('/dogs/add/', AddDogAPI, 'dogs_add'),
	Pluggable('/dogs/<int:id>/', DogProfileAPI, 'dog_profile'),
	Pluggable('/dogs/<int:id>/edit/', DogProfileEditAPI, 'dogs_edit'),
	Pluggable('/myDogImage/<string:file>', MyDogImageAPI, 'my_dog_image'),
	Pluggable('/myDogImage/<string:file>', MyDogImageAPI, 'my_dog_image_profile'),
	Pluggable('/myDogImage/<string:file>/delete', MyDogImageAPI, 'my_dog_image_delete'),

	Pluggable('/posts/', ContentAPI, 'posts_list'),
	Pluggable('/posts/new/', ContentAPI, 'posts_new'),
	Pluggable('/posts/<int:id>/', ContentAPI, 'posts'),
	Pluggable('/posts/<int:id>/edit/', ContentEdit, 'posts_edit'),

	Pluggable('/conversations/', ContentAPI, 'conversations_list'),
	Pluggable('/conversations/new/', ContentAPI, 'conversations_new'),
	Pluggable('/conversations/<int:id>/', ContentAPI, 'conversations'),
	Pluggable('/conversations/<int:id>/edit/', ContentEdit, 'conversations_edit'),
	Pluggable('/conversations/<int:id>/reply/', ContentEdit, 'conversations_reply'),
	Pluggable('/conversations/<int:id>/trash/', ContentEdit, 'conversations_trash'),
	Pluggable('/conversations/<int:id>/untrash/', ContentEdit, 'conversations_untrash'),

]
