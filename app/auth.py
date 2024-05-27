import sys
import os
import datetime
import cryptocode
from flask import Blueprint, session, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, current_user
from .models import User, Role, UserRoles, Dashboard, Inventory
from .forms import SignupForm, LoginForm, addNewUserForm
from . import login_manager, bcrypt, app, db, VendorReadAction, vendor_needs
from markupsafe import escape
from datetime import datetime, timedelta
from flask_principal import Identity, AnonymousIdentity, \
     identity_changed, identity_loaded, RoleNeed, UserNeed, Permission

auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

@login_manager.user_loader
def load_user(email):
    user = User.query.filter_by(email=(email)).one_or_none()
    return user

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for user_role in current_user.roles:
            identity.provides.add(RoleNeed(user_role.role.name))

            for role_permission in user_role.role.permissions:
                current_permission = role_permission.permission.permission.value
                if current_permission in vendor_needs:
                    identity.provides.add(vendor_needs[current_permission](str(role_permission.permission.id)))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        success_login = False
        try:
            if form.validate_on_submit():
                user = User.query.filter_by(uname=form.username.data).one_or_none()
                if user is not None and bcrypt.check_password_hash(user.upass, form.pwd.data):
                    if user.approved:
                        flash('Welcome: {}'.format(escape(user.name)), 'success')
                        success_login = True
                    else:
                        flash('The status of your registration request is still pending, please wait for the administrator to approve your request.', 'danger')
                else:
                    flash('Please check your login details and try again.', 'danger')
            else:
                flash('Please check your login details and try again.', 'danger')

        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unable to login right now, please try again later.', 'danger')
            success_login = False

        finally:
            # Final Actions (3) Redirect Home, Redirect With FLahs, Render Template with form errors (True, None, False) False not mentioned as it default
            if success_login == True:
                login_user(user, remember=(True if form.remember.data else False))
                            # Tell Flask-Principal the identity changed
                identity_changed.send(current_app._get_current_object(),
                                      identity=Identity(user.id))
                                  
                return redirect(url_for('routes.index'))

            else:
                return redirect(url_for('auth.login'))

        
    return render_template('login.html', form=form)


@auth.route('/signup', methods=['GET'])
def signup():
    signup_form = SignupForm()
    return render_template('signup.html', form=signup_form)


@auth.route('/signup', methods=['POST'])
def submit_signup():
    valid_form = False
    is_private = False
    try:
        # check if vendor role found else create it
        vendor_role = Role.query.filter_by(name='vendor').one_or_none()
        if vendor_role is None:
            vendor_role = Role(name='vendor')
            vendor_role.insert()

        form = SignupForm()
        if form.validate_on_submit():
            valid_inventory = False

            is_private = True if form.is_private.data == True else False
            # dynamic get right inv also tricky
            inventory = Inventory.query.filter_by(code=form.inventory_code.data, active=True, private=is_private).one_or_none()
            #return str(is_private)
            if inventory:
                if inventory.total_requests() <= inventory.max_pending:
                    # if there pass not empty
                    if inventory.join_pass:
                        # if user enter pass
                        if form.join_password.data:
                            salat = inventory.salat if inventory.salat else ""
                            decoded = cryptocode.decrypt(inventory.join_pass, salat)

                            # if encrypted not False and equal to join
                            if decoded and form.join_password.data == decoded:
                                valid_inventory = True
                    else:
                        # if join pass empty and user enter no pass or it public must be string
                        if inventory.join_pass == '' and inventory.join_pass == form.join_password.data:
                            valid_inventory = True
    
                    if valid_inventory:
                        user_exist = User.query.filter_by(uname=form.username.data).one_or_none()
                        email_exist = User.query.filter_by(email=form.email.data).one_or_none()
                        if user_exist is None and email_exist is None:
                            user_dashboard = Dashboard()
                            user_dashboard.insert()
                            new_user = User(name=form.name.data, uname=form.username.data, upass=bcrypt.generate_password_hash(form.pwd.data), email=form.email.data, dashboard_id=user_dashboard.id, inventory_id=inventory.id, approved=False)
                            new_user.insert()
                            # create new vendor default role for the user (can create temp role and delete when accept so access small page save even if login)
                            new_user_role = UserRoles(user_id=new_user.id, role_id=vendor_role.id)
                            new_user_role.insert()
                            flash('Successfully Created New User, Please Login', 'success')
                            valid_form = True
                        else:
                            if user_exist is not None:
                                form.username.errors.append('Username is taken, please try something else.')
                            
                            if email_exist is not None:
                                form.email.errors.append('Email is taken, please try something else.')
                            
                            valid_form = False
                    else:
                        # tricky message also for inactive act like not exist so protect signup and requesrs
                        form.inventory_code.errors.append('Inventory not found.')
                        valid_form = False
                else:
                    # tricky message also for inactive act like not exist so protect signup and requesrs
                    form.inventory_code.errors.append('Inventory cannot accept new onhold users, please ask your admin to approve or deny old users requests which will prevent Inventory from receiving further registration requests, and then try to sign up again.t.')
                    valid_form = False
            else:
                form.inventory_code.errors.append('Inventory not found.')
                valid_form = False
        else:
            valid_form = False
        
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unable to create new users right now, please try again later.', 'danger')
        valid_form = None

    finally:
        if valid_form == True:
            return redirect(url_for('auth.login'))
        elif valid_form == None:
            return redirect(url_for('auth.signup'))
        else:
            # pass is_private to jinja2 if true will execute script that click on private button so both ux and prevent user unlogical error like he changed his mind was submit wrong private and when redirect he stayed and continue on public but the issue form.is_private not updated, script will update it then and sync
            return render_template('signup.html', form=form, is_private=is_private)


@auth.route('/logout', methods=['GET'])
def logout():

    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    
    # clear old session messages
    session.pop('import_orders_report', None)

    return redirect(url_for('auth.login'))
