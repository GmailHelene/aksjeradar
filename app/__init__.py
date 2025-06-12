from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate() 
login_manager = LoginManager()
login_manager.login_view = 'main.index'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importer alle modeller før db.create_all()
    from app.models import user, portfolio, stock

    from app.routes.main import main as main_blueprint
    from app.routes.portfolio import portfolio as portfolio_blueprint
    from app.routes.analysis import analysis as analysis_blueprint
    from app.routes.stocks import stocks

    app.register_blueprint(main_blueprint)
    app.register_blueprint(portfolio_blueprint, url_prefix='/portfolio')
    app.register_blueprint(analysis_blueprint, url_prefix='/analysis')
    app.register_blueprint(stocks)

    with app.app_context():
        db.create_all() 

    return app