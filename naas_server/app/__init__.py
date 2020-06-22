from flask import Flask
import os
import logging

app = Flask(__name__,
            static_url_path='',
            static_folder='ui/build',
            template_folder='ui/build')

log_dir = '/home/ubuntu'
if os.path.isdir(log_dir):
    handler = logging.FileHandler('{}/flask.log'.format(log_dir))  # errors logged to this file
    handler.setLevel(logging.INFO)  # only log errors and above
    app.logger.addHandler(handler)  # attach the handler to the app's logger

from app import routes
