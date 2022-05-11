"""A simple flask web app"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import time, datetime
from logging.config import dictConfig

import flask_login
from flask import Flask, request, g
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect

from app import config
from app.auth import auth
from app.auth import auth
from app.cli import create_database
from app.context_processors import utility_text_processors
from app.db import db
from app.db.models import User
from app.error_handlers import error_handlers
from app.logging_config import log_con, LOGGING_CONFIG
from app.simple_pages import simple_pages
from app.transactions import songs
from app.transactions import transactions
from app.map import map
from app.db import database
from flask_cors import CORS
login_manager = flask_login.LoginManager()


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    if  os.environ.get("FLASK_ENV") == "production":
        app.config.from_object("app.config.ProductionConfig")
    elif os.environ.get("FLASK_ENV") == "development":
        app.config.from_object("app.config.DevelopmentConfig")
    elif os.environ.get("FLASK_ENV") == "testing":
        app.config.from_object("app.config.TestingConfig")

    # https://flask-login.readthedocs.io/en/latest/  <-login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    # Needed for CSRF protection of form submissions and WTF Forms
    # https://wtforms.readthedocs.io/en/3.0.x/
    csrf = CSRFProtect(app)
    # https://bootstrap-flask.readthedocs.io/en/stable/
    bootstrap = Bootstrap5(app)
    # these load functions with web interface
    app.register_blueprint(simple_pages)
    app.register_blueprint(auth)
    app.register_blueprint(database)
    # these load functionality without a web interface
    app.register_blueprint(log_con)
    app.register_blueprint(error_handlers)
    app.register_blueprint(songs)
    app.register_blueprint(map)
    app.context_processor(utility_text_processors)
    # add command function to cli commands
    app.cli.add_command(create_database)
    db.init_app(app)
    api_v1_cors_config = {
    "methods": ["OPTIONS", "GET", "POST"],
    }
    CORS(app, resources={"/api/*": api_v1_cors_config})
    # Run once at startup:
    return app


@login_manager.user_loader
def user_loader(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

def start_timer():
    g.start = time.time()

@log_con.after_app_request
def after_request_logging(response):
    if request.path == '/favicon.ico':
        return response
    elif request.path.startswith('/static'):
        return response
    elif request.path.startswith('/bootstrap'):
        return response
    #now = datetime.now()
    #duration = round(now - g.start, 2)
    #dt = datetime.fromtimestamp(now)
    #timestamp = rfc3339(dt, utc=True)

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    host = request.host.split(':', 1)[0]
    args = dict(request.args)
    request_id = request.headers.get('X-Request-ID')
    log_params = [
        ('method', request.method),
        ('path', request.path),
        ('status', response.status_code),
        #('duration', duration),
        #('time', timestamp),
        ('ip', ip),
        ('host', host),
        ('params', args)
    ]
    if request_id:
        log_params.append(('request_id', request_id))

    parts = []
    for name, value in log_params:
        part = name + ': ' + str(value) + ', '
        parts.append(part)
    line = " ".join(parts)
    log = logging.getLogger("request")
    log.info(line)
    return response

@log_con.before_app_first_request
def setup_logs():

    # set the name of the apps log folder to logs
    logdir = config.Config.LOG_DIR
    # make a directory if it doesn't exist
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logging.config.dictConfig(LOGGING_CONFIG)



LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },

    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file.handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'handler.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.myapp': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'myapp.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.request': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'request.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'errors.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.sqlalchemy': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'sqlalchemy.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.werkzeug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'werkzeug.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'file.handler.CSV_upload': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(config.Config.LOG_DIR,'CSV_upload.log'),
            'maxBytes': 10000000,
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default','file.handler'],
            'level': 'DEBUG',
            'propagate': True
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default','file.handler'],
            'level': 'DEBUG',
            'propagate': True
        },
        'werkzeug': {  # if __name__ == '__main__'
            'handlers': ['file.handler.werkzeug'],
            'level': 'DEBUG',
            'propagate': False
        },
        'sqlalchemy.engine': {  # if __name__ == '__main__'
            'handlers': ['file.handler.sqlalchemy'],
            'level': 'INFO',
            'propagate': False
        },
        'myApp': {  # if __name__ == '__main__'
            'handlers': ['file.handler.myapp'],
            'level': 'DEBUG',
            'propagate': False
        },
        'errors': {  # if __name__ == '__main__'
            'handlers': ['file.handler.errors'],
            'level': 'DEBUG',
            'propagate': False
        },
        'CSV_upload': {  # if __name__ == '__main__'
            'handlers': ['file.handler.CSV_upload'],
            'level': 'DEBUG',
            'propagate': False
        },
        'request': {  # if __name__ == '__main__'
            'handlers': ['file.handler.request'],
            'level': 'DEBUG',
            'propagate': False
        },

    }
}