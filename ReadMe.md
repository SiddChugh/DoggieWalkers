This demo project is one of my academic projects where the main goal of this application is to create a platform where dog owners and dog enthusiasts can be brought together. Specifically, the service aims to bring people who don’t have the time or simply can’t walk their dogs for whatever reason, and those who have the time and desire but don’t
have a dog. The target audience for the application is separated into two profiles: dog owners and dog walker. The separation is not determined based on demographics, but rather on a particular circumstance: people who have dogs, however cannot walk them and people who have extra time and desire to walk dogs.

# Prerequisities
Vagrant <p>
Please download vagrant from *https://www.vagrantup.com/downloads.html*

# To start app:
vagrant up <p>
vagrant provision <p>
vagrant ssh <p>
cd project <p>
run **gunicorn --bind 0.0.0.0:5002 wsgi** <p>

# TroubleShoot:
Cannot connect to port 5002, port already in use <p>
run **fuser -k 5002/tcp > /dev/null 2>&1; exit 0** <p>


# Technologies used:
**Gunicorn** ‘Green Unicorn’ is a Python WSGI HTTP Server for UNIX. <p>
**Nginx** is an HTTP and reverse proxy server.


The url we use:
0.0.0.0:5002

