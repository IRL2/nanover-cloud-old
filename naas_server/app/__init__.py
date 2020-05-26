from flask import Flask
import werkzeug
import logging
app = Flask(__name__)

handler = logging.FileHandler('/home/ubuntu/flask.log')  # errors logged to this file
handler.setLevel(logging.INFO)  # only log errors and above
app.logger.addHandler(handler)  # attach the handler to the app's logger

from app import routes
