from flask import Flask
from flask_cors import CORS
import datetime
import logging
from . import api


def create_app():
    app = Flask(__name__,
                static_url_path='',
                static_folder='../ui/build',
                template_folder='../ui/build')

    gunicorn_logger = logging.getLogger('gunicorn.error')
    if gunicorn_logger:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    CORS(app, resources={r'/api/*': {"origins": ["http://localhost:3000", "http://localhost"]}})
    app.config['CORS_HEADERS'] = 'Content-Type'

    api.init(app)

    return app
