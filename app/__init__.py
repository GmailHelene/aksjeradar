from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.index'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importer og registrer blueprints
    from app.routes.main import main as main_blueprint
    from app.routes.portfolio import portfolio as portfolio_blueprint
    from app.routes.analysis import analysis as analysis_blueprint
    from app.routes.stocks import stocks as stocks_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(portfolio_blueprint)
    app.register_blueprint(analysis_blueprint)
    app.register_blueprint(stocks_blueprint)

    with app.app_context():
        db.create_all()

    return app

# For enkel import i run.py:
app = create_app()
