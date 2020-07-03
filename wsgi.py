#this file would opens a wsgi gate and start the app in production mode

from doggiewalk import app as application

if __name__ == "__main__":
    application.run()
