from leek.leek_api.routes.api_v1 import api_v1_blueprint
from leek.leek_api.routes.manage import manage_bp
from leek.leek_api.routes.users import users_bp
from leek.leek_api.routes.applications import applications_bp
from leek.leek_api.routes.events import events_bp
from leek.leek_api.routes.search import search_bp


def register_blueprints(app):
    # Register blueprints
    app.register_blueprint(api_v1_blueprint)
    app.register_blueprint(manage_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(search_bp)