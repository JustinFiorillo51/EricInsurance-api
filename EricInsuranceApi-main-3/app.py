from flask import Flask
import logging
import traceback
from api.auth import auth_bp
from api.dashboard import dashboard_bp
from api.groups import groups_bp
from api.commons import commons_bp
from api.family_members import family_members_bp
from api.admin_users import admin_user_bp
from api.admin_rates import admin_rates_bp
from api.admin_rates_lookup import admin_rates_lookup_bp
from api.admin_groups import admin_groups_bp
from api.admin_document_template import admin_document_template_bp
from api.document_mergence import document_mergence_bp
from api.participants import participants_bp
from api.coverage_history import coverage_history_bp
from api.ppo_network_history import ppo_network_history_bp
from api.reports_billing import reports_billing_bp
from config import Config

def setup_logger(app):
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # file_handler = RotatingFileHandler('app.log', maxBytes=1000000, backupCount=5)
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.LOG_LEVEL) 
    console_handler.setFormatter(formatter)

    app.logger.setLevel(Config.LOG_LEVEL)
    # app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    def logerr(e):
        app.logger.error(f'An error has occurred: {str(e)}\n{traceback.format_exc()}')

    app.logerr = logerr


def setup_db(app):
    pass


def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    app.register_blueprint(participants_bp, url_prefix='/api/participants')
    app.register_blueprint(commons_bp, url_prefix='/api/commons')
    app.register_blueprint(family_members_bp, url_prefix='/api/family_members')
    app.register_blueprint(coverage_history_bp, url_prefix='/api/coverage_history')
    app.register_blueprint(ppo_network_history_bp, url_prefix='/api/ppo_network_history')

    app.register_blueprint(reports_billing_bp, url_prefix='/api/reports/billing')


    app.register_blueprint(admin_user_bp, url_prefix='/api/admin/user')
    app.register_blueprint(admin_rates_bp, url_prefix='/api/admin/rates')
    app.register_blueprint(admin_rates_lookup_bp, url_prefix='/api/admin/rates_lookup')
    app.register_blueprint(admin_groups_bp, url_prefix='/api/admin/groups')
    app.register_blueprint(admin_document_template_bp, url_prefix='/api/admin/document_template')
    app.register_blueprint(document_mergence_bp, url_prefix='/api/document_mergence')
    

    setup_logger(app)
    setup_db(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)