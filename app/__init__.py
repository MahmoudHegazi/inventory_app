import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed
from flask_admin import Admin, expose, BaseView
import flask_excel as excel
from flask_session import Session

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '/static/assets/uploads')      
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'hGjj6dq4fvnsyMBMpcXlh8-faN3EhMKRvYG1T-l5-YzHHtdFa4sqp9wJH0kwE0lIBmonkEY4mT1j3ZjyFQD1badAZukd5w62gVTQ1MgTLRa61kcNhcTGIj9cDh8chUVllIIY'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://mr204h:Ilda2011@localhost/inventory123?charset=utf8mb4'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dbmasteruser:Success2023!@ls-78a3019a69abb8942e164ba31b7f79d941a5b928.cm1krsomo3zh.ca-central-1.rds.amazonaws.com/inventory123?charset=utf8mb4'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['AUTH_ALLOWED_FILES'] = {'png', 'jpg', 'jpeg', 'gif'}
# configure backend-session
app.config['SESSION_PERMANENT'] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, '../flask_session')
#app.config['SESSION_FILE_DIR'] = '/home/ubuntu/inventory_app/flask_session'
#print(app.root_path)
# here setup global variables for remaning requests per user and max request
app.config['BESTBUY_RAMAINING'] = 100
app.config['BESTBUY_MAX'] = 100
# here global variable for our API default max (OURAPI_REQUESTS_LIMIT how many requests can sent by user, this is default number for all users, still can edit from db to speacfic user, OURAPI_KEYS_MAX-> how many keys can user have also this is default and can changed by db for speacfic user)
app.config['OURAPI_REQUESTS_LIMIT'] = 100
app.config['OURAPI_KEYS_MAX'] = 10

#app.config['SALAT'] = os.environ.get('SALAT')
db = SQLAlchemy(app)
# if not used remove (pass encryptor unseen and no info for it)
bcrypt = Bcrypt(app)
principals = Principal(app)

#admin = Admin(app, name='Inventory Admin')
# openssl 22.0.0, cryptography 41.0.3

# setup backend-session
flaskSession = Session(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

vendor_permission = Permission(RoleNeed('vendor'))
admin_permission = Permission(RoleNeed('admin'))

# setup excel to add flask_excel's methods, and other data to request
excel.init_excel(app)

# keep routes in diffrent file than app configuration
from .routes import routes
from .auth import auth
from .main import main
from .api import api
# from .admin import admin_routes
crud = app.register_blueprint(routes)
authincation = app.register_blueprint(auth)
systemActions = app.register_blueprint(main)
apiEndpoints = app.register_blueprint(api)


admin = Admin(app, name='Inventory', template_mode='bootstrap4')

from .admin_models import InventoryModelView, userModalView, roleModalView, userRolesModalView, userMetaModalView, dashboardModalView, listingModalView, cataloguedModalView, purchaseModalView, orderModalView, supplierModalView, backlink
from flask_admin.contrib.fileadmin import FileAdmin
admin.add_view(userModalView)
admin.add_view(roleModalView)
admin.add_view(userRolesModalView)
admin.add_view(userMetaModalView)
admin.add_view(dashboardModalView)
admin.add_view(listingModalView)
admin.add_view(cataloguedModalView)
admin.add_view(purchaseModalView)
admin.add_view(orderModalView)
admin.add_view(supplierModalView)

static_path = os.path.join(os.path.dirname(__file__), 'static')
admin.add_view(FileAdmin(static_path, '/static/', 'Files Manager'))
admin.add_link(backlink)

# display errors page for all app based on all given errors
""" (some times work with cookies and flask secuirty, user will see old cached page if click any message will get forbiden error as he not logged in, remove this will not get the error page and redirect to login)
@app.errorhandler(403)
def handle_forbidden(e):
    return render_template('errors/error_403.html') 
    # return render_template('errors/error_403.html')
"""
"""
@app.errorhandler(403)
def handle_forbidden(e):
    # forbidden here when some issue with session and flask login so it logged out so loghim out full and let logout redirect him to login page
    return redirect(url_for('auth.logout'))
"""

@app.errorhandler(404)
def handle_not_found(e):
    return render_template('errors/error_404.html')

@app.errorhandler(405)
def handle_method_not_allowed(e):
    return render_template('errors/error_405.html')
 
@app.errorhandler(500)
def handle_internal_server_error(e):
    return render_template('errors/error_500.html')
