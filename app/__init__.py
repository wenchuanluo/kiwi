# app/__init__.py
from flask import Flask
from app.db import db
from app.route.user_bp import user_bp  
from app.route.security_bp import security_bp 
from app.route.portfolio_bp import portfolio_bp


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    # register extensions
    db.init_app(app)

    # register blueprints
    app.register_blueprint(user_bp)   
    app.register_blueprint(security_bp)   
    app.register_blueprint(portfolio_bp)


    return app

