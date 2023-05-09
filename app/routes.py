import json
import sys
import os
import random
from flask import Flask, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify
from flask_wtf import Form
from .models import User, Supplier, Dashboard, Listing, Catalogue, Purchase, Order
from .forms import addDashboardForm, editDashboardForm, removeDashboardForm, addListingForm, editListingForm, addCatalogueForm, editCatalogueForm, \
removeDashboardForm, removeCatalogueForm, removeListingForm, addSupplierForm, editSupplierForm, removeSupplierForm, \
addPurchaseForm, editPurchaseForm, removePurchaseForm, addOrderForm, editOrderForm, removeOrderForm, CatalogueExcelForm, defaultDashboardForm
from . import vendor_permission, db
from .functions import get_safe_redirect
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user
import flask_excel


routes = Blueprint('routes', __name__, template_folder='templates', static_folder='static')


def makePagination(page=1, query_obj=None, callback=()):
    import math
    try:
        limit = 10
        offset = 0
        # limit == 0 means no need data
        if limit < 1:
            return {'data': [], 'pagination_btns': []}
        
        total_items = len(query_obj.all())
        total_pages = math.ceil(total_items/limit)
        # handle none integer query parameter without exception for all routes dynamic
        try:
            page = int(page)
        except:
            page = 1
        
        # make sure page is always more than 0 (handle invaid query parameter given)
        page = 1 if page < 1 else page
        
        # page 1, means start from row index 0, page 2 means start from row index 5 (user need see content start from 0 or previous page end until current page end: page-1  1->(0-1), 2->(1, 2), 3->(2, 3) this how in simple display)
        requested_offset = int((page-1) * limit)


        # if requested offset 0*5 or 100*5 is less than last allowed offset for example 16, set offset as requested else offset =0 (becuase max offset decrsed 1 from it so it <= )
        offset = requested_offset if requested_offset < total_items else 0
        # call the lambda function given and pass to it the total_pages so it dynamic create diffrent urls with valid given params from endpoint (so endpoint call decide the url of btns and benfit of all actions in same function)
        pagination_btns = list(callback(total_pages))
        data = query_obj.limit(limit).offset(offset).all()

        return {'data': data, 'pagination_btns': pagination_btns}
    except Exception as e:
        print('System Error makePagination: {} , info: {}'.format(e, sys.exc_info()))
        flash('System Error Unable to display Pagination data, please report this problem to us error: 1001', 'danger')
        return {'data': [], 'pagination_btns': []}


# sperate secure app routes  (All Cruds, Add, View, Edit, Delete)
################ -------------------------- Dashboards -------------------- ################
@routes.route('/', methods=['GET'])
@routes.route('/dashboards', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def index():
    default_form = defaultDashboardForm()
    # dynamic pagination anlysis (requires lazyloading for relation to work with query and set the offset and limit)
    pagination = makePagination(
        request.args.get('page', 1),
        current_user.dashboards,
        lambda total_pages: [url_for('routes.index', page=page_index) for page_index in range(1, total_pages+1)]
    )
    return render_template('index.html', dashboards=pagination['data'], pagination_btns=pagination['pagination_btns'], default_form=default_form)


@routes.route('/dashboards/<int:dashboard_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def view_dashboard(dashboard_id):
    dashboard = None
    deleteform = removeDashboardForm()
    try:
        dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to view product', 'danger')
    finally:
        if dashboard is not None:
            return render_template('dashboard.html', dashboard=dashboard, deleteform=deleteform)
        else:
            flash('Dashboard not found it maybe deleted', 'danger')
            return redirect(url_for('routes.index'))

# Create New Dashboard
@routes.route('/dashboards/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_dashboard():
    form = addDashboardForm()
    if request.method == 'POST':
        success = None
        try:
            if form.validate_on_submit():
                # check if no default dashboard make the new created default
                default = 0
                if not Dashboard.query.filter_by(default=1, user_id=current_user.id).first():
                    default = 1
                new_dashboard = Dashboard(
                    user_id = current_user.id,
                    title = form.title.data,
                    num_of_listings = form.num_of_listings.data,
                    num_of_orders = form.num_of_orders.data,
                    sum_of_monthly_purchases = form.sum_of_monthly_purchases.data,
                    default = default
                    )
                new_dashboard.insert()
                success = True
            else:
                success = False

        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            success = None
        finally:
            if success == True:
                flash('Successfully Created new Dashboard', 'success')
                if form.redirect.data:
                    safeurl = str(get_safe_redirect(form.redirect.data)).strip()
                    if safeurl:
                        return redirect(safeurl)
                return redirect(url_for('routes.index'))
            elif success == False:
                return render_template('crud/add_dashboard.html', form=form)
            else:
                flash('Unknown error unable to Add Dashboard', 'danger')
                return redirect(url_for('routes.index'))
    else:
        # set redirect url using flask wtforms and url_for in template (Add dashboard can done from dashboard view so redirect dynamic from which dashboard)
        if 'redirect' in request.args:
            # exist in same domain
            safeurl = str(get_safe_redirect(request.args['redirect'])).strip()
            if safeurl:
                form.redirect.data = safeurl
        return render_template('crud/add_dashboard.html', form=form)

@routes.route('/dashboards/<int:dashboard_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_dashboard(dashboard_id):
    if request.method == 'POST':
        success = None
        form = editDashboardForm()
        try:
            target_dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
            if target_dashboard is not None:
                if form.validate_on_submit():
                    target_dashboard.title = form.title.data
                    target_dashboard.num_of_listings = form.num_of_listings.data
                    target_dashboard.num_of_orders = form.num_of_orders.data
                    target_dashboard.sum_of_monthly_purchases = form.sum_of_monthly_purchases.data
                    target_dashboard.update()
                    success = True
                else:
                    success = False
            else:
                flash('Unable to find target dashboard.', 'danger')
                success = None

        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to Add Dashboard', 'danger')
            success = None
        finally:
            if success == True:
                flash('Successfully Edited Dashboard', 'success')
                return redirect(url_for('routes.index'))
            elif success == False:
                return render_template('crud/edit_dashboard.html', dashboard=target_dashboard, dashboard_id=dashboard_id, edit_dashboard_form=form)
            else:
                return redirect(url_for('routes.index'))
    else:
        # GET Requests
        success = True
        error_message = ''
        try:
            dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
            if dashboard is not None:
                form = editDashboardForm(
                    title=dashboard.title, num_of_listings=dashboard.num_of_listings,
                    num_of_orders=dashboard.num_of_orders, sum_of_monthly_purchases=dashboard.sum_of_monthly_purchases,
                    )
            else:
                error_message = 'Dashboard Not Found or deleted.'
                success = False

        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            error_message = 'Unknown Error, Unable to display Edit Dashboard Form.'
            success = False
        finally:
            if success == True:
                return render_template('crud/edit_dashboard.html', dashboard=dashboard, edit_dashboard_form=form)
            else:
                flash(error_message, 'danger')
                return redirect(url_for('routes.index'))


@routes.route('/dashboards/<int:dashboard_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_dashboard(dashboard_id):
    try:
        form = removeDashboardForm()
        dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
        if dashboard is not None:
            if form.validate_on_submit():
                dashboard.delete()
                flash('Successfully deleted Dashboard ID: {}'.format(dashboard_id), 'success')
            else:
                flash('Unable to delete dashboard ID: {}'.format(dashboard_id), 'danger')
        else:
            flash('Dashboard not found it maybe deleted ID: {}'.format(dashboard_id), 'danger')
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete dashboard ID: {}'.format(dashboard_id), 'danger')
    finally:
        return redirect(url_for('routes.index'))

################ -------------------------- Catalogue -------------------- ################
@routes.route('/catalogues', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def catalogues():
    try:
        pagination = makePagination(
            request.args.get('page', 1),
            Catalogue.query.filter_by(user_id=current_user.id),
            lambda total_pages: [url_for('routes.catalogues', page=page_index) for page_index in range(1, total_pages+1)]
        )
        catalogues_excel = CatalogueExcelForm()
        user_catalogues = pagination['data']
        return render_template('catalogues.html', catalogues=user_catalogues,  catalogues_excel=catalogues_excel, pagination_btns=pagination['pagination_btns'])
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('unable to display catalogues page', 'danger')
        return redirect(url_for('routes.index'))


@routes.route('/catalogue/<int:catalogue_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def view_catalogue(catalogue_id):
    try:
        deleteform = removeCatalogueForm()
        target_catalogue = Catalogue.query.filter_by(id=catalogue_id, user_id=current_user.id).one_or_none()
        if target_catalogue is not None:
            return render_template('catalogue.html', catalogue=target_catalogue, deleteform=deleteform)
        else:
            flash('Catalouge Not found or deleted', 'danger')
            return redirect(url_for('routes.catalogues'))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('unable to display catalogues page', 'danger')
        return redirect(url_for('routes.catalogues'))
 
@routes.route('/catalogues/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_catalogue():
    if request.method == 'POST':
        form = addCatalogueForm()
        success = None
        try:
            if form.validate_on_submit():
                new_catalogue = Catalogue(user_id=current_user.id, sku=form.sku.data, product_name=form.product_name.data, product_description=form.product_description.data, brand=form.brand.data, category=form.category.data, price=form.price.data, sale_price=form.sale_price.data, quantity=form.quantity.data, product_model=form.product_model.data, condition=form.condition.data, upc=form.upc.data, location=form.location.data)
                new_catalogue.insert()
                success = True
                flash('Successfully Created New Catalogue', 'success')
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown Error unable to create new Catalogue', 'danger')

        finally:
            if success == True:                
                return redirect(url_for('routes.catalogues'))
            elif success == None:
                return redirect(url_for('routes.catalogues'))
            else:
                return render_template('crud/add_catalogue.html', form=form)
    else:
        # GET Requests
        try:
            form = addCatalogueForm()
            return render_template('crud/add_catalogue.html', form=form)
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('unable to display Add new Catalogue page', 'danger')
            return redirect(url_for('routes.catalogues'))

@routes.route('/catalogue/<int:catalogue_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_catalogue(catalogue_id):
    form = None
    target_catalogue = None
    # setup route data and checking
    try:
        target_catalogue = Catalogue.query.filter_by(id=catalogue_id, user_id=current_user.id).one_or_none()
        if target_catalogue is not None:
            form = editCatalogueForm(
                sku = target_catalogue.sku,
                product_name = target_catalogue.product_name,
                product_description = target_catalogue.product_description,
                brand = target_catalogue.brand,
                category = target_catalogue.category,
                quantity = target_catalogue.quantity,
                product_model = target_catalogue.product_model,
                condition = target_catalogue.condition,
                upc = target_catalogue.upc,
                location = target_catalogue.location,
                price = target_catalogue.price,
                sale_price = target_catalogue.sale_price,
                )
        else:
            flash('Unable to find the selected catalogue, it maybe deleted', 'danger')
            return redirect(url_for('routes.catalogues'))
         
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Uknown error unable to Display catalogue edit form', 'danger')
        return redirect(url_for('routes.catalogues'))

    if request.method == 'POST':
        success = True
        try:
            if form and form.validate_on_submit():
                # update only what needed reduce db request and db actions
                if target_catalogue.sku != form.sku.data:
                    target_catalogue.sku = form.sku.data

                if target_catalogue.product_name != form.product_name.data:
                    target_catalogue.product_name = form.product_name.data

                if target_catalogue.product_description != form.product_description.data:
                    target_catalogue.product_description = form.product_description.data

                if target_catalogue.brand != form.brand.data:
                    target_catalogue.brand = form.brand.data

                if target_catalogue.category != form.category.data:
                    target_catalogue.category = form.category.data

                if target_catalogue.price != form.price.data:
                    target_catalogue.price = form.price.data

                if target_catalogue.sale_price != form.sale_price.data:
                    target_catalogue.sale_price = form.sale_price.data

                if target_catalogue.quantity != form.quantity.data:
                    target_catalogue.quantity = form.quantity.data

                if target_catalogue.product_model != form.product_model.data:
                    target_catalogue.product_model = form.product_model.data

                if target_catalogue.condition != form.condition.data:
                    target_catalogue.condition = form.condition.data

                if target_catalogue.upc != form.upc.data:
                    target_catalogue.upc = form.upc.data

                if target_catalogue.location != form.location.data:
                    target_catalogue.location = form.location.data

                target_catalogue.update()
                flash('Successfully updated catalogue data', 'success')
                success = True
            else:
                # invalid wtforms form sumited in finally this will return render_template to display errors
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        finally:
            if success == True:                
                # success 
                return redirect(url_for('routes.view_catalogue', catalogue_id=catalogue_id))
            elif success == False:
                # not success due to wtforms render template to display errors
                return render_template('crud/edit_catalogue.html', form=form, catalogue_id=catalogue_id)
            else:
                # not success system error, log error and redirect to main page
                flash('Unknown eror, unable to edit catalogue', 'danger')
                return redirect(url_for('routes.catalogues'))
    else:
        # GET Requests
        try:
            return render_template('crud/edit_catalogue.html', form=form, catalogue_id=catalogue_id)
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('unable to display Edit Catalogue page', 'danger')
            return redirect(url_for('routes.catalogues'))

@routes.route('/catalogues/<int:catalogue_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_catalogue(catalogue_id):
    try:
        form = removeCatalogueForm()
        target_Catalogue = Catalogue.query.filter_by(id=catalogue_id,user_id=current_user.id).one_or_none()
        if target_Catalogue is not None:
            if form.validate_on_submit():
                target_Catalogue.delete()
                flash('Successfully deleted Catalogue ID: {}'.format(catalogue_id), 'success')
            else:
                flash('Unable to delete Catalogue, ID: {}'.format(catalogue_id), 'danger')
        else:
            flash('Catalogue not found it maybe deleted, ID: {}'.format(catalogue_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete catalogue', 'danger')
    finally:
        return redirect(url_for('routes.catalogues', catalogue_id=catalogue_id))
    
################ -------------------------- Dashboard Listings -------------------- ################
@routes.route('/dashboards/<int:dashboard_id>/listings', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def listings(dashboard_id):
    user_dashboard_listings_q = db.session.query(
        Listing
    ).join(
        Dashboard
    ).join(
        User
    ).filter(
        User.id == current_user.id,
        Dashboard.id == dashboard_id
    )
    # total_pages + 1 (becuase range not take last number while i need it to display the last page)
    pagination = makePagination(
            request.args.get('page', 1),
            user_dashboard_listings_q,
            lambda total_pages: [url_for('routes.listings', dashboard_id=dashboard_id, page=page_index) for page_index in range(1, total_pages+1)]
    )
    user_dashboard_listings = pagination['data']

    return render_template('listings.html', listings=user_dashboard_listings, dashboard_id=dashboard_id, pagination_btns=pagination['pagination_btns'])

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def view_listing(dashboard_id, listing_id):
    success = True    
    try:
        deleteform = removeListingForm()
        delete_purchase = removePurchaseForm()
        delete_order =  removeOrderForm()
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).one_or_none()
        
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        success = False
    finally:
        if success == True:
            return render_template('listing.html', listing=target_listing, dashboard_id=dashboard_id, deleteform=deleteform, delete_purchase=delete_purchase,delete_order=delete_order)
        else:
            flash('Unknown error Unable to view Listing', 'danger')
            return redirect(url_for('routes.index'))


# create new listing
@routes.route('/dashboards/<int:dashboard_id>/listings/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_listing(dashboard_id):
    form = addListingForm()
    try:
        user_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
        form.catalogue_id.choices = [(catalogue.id, catalogue.product_name) for catalogue in user_catalogues]
    except:
        flash('unable to display add listing form due to isssue in catalogues', 'danger')
        return redirect(url_for('routes.index'))

    if request.method == 'POST':
        success = None
        try:
            target_dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
            if target_dashboard is not None:
                if form.validate_on_submit():
                    new_listing = Listing(dashboard_id=target_dashboard.id, catalogue_id=form.catalogue_id.data, platform=form.platform.data)
                    new_listing.insert()
                    success = True
                else:
                    success = False
            else:
                flash('Dashboard Not found or deleted', 'danger')
                success = None
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown Error unable to create new Listing', 'danger')

        finally:
            if success == True:
                flash('Successfully Created New Listing', 'success')
                return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
            elif success == None:
                return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
            else:
                return render_template('crud/add_listing.html', dashboard_id=dashboard_id, form=form)
    else:
        # GET Requests
        success = True
        try:
            target_dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
            if target_dashboard is None:
                flash('Dashboard Not Found or deleted', 'danger')
                success = False

        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            success = False
        finally:
            if success == True:
                return render_template('crud/add_listing.html', dashboard_id=dashboard_id, form=form)
            else:
                return redirect(url_for('routes.index'))

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_listing(dashboard_id, listing_id):
    # route setup
    form = None
    target_listing = None
    try:
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).one_or_none()
        
        if target_listing is not None:
            form = editListingForm(
                catalogue_id=target_listing.catalogue_id,
                platform=target_listing.platform
            )
            user_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
            form.catalogue_id.choices = [(catalogue.id, catalogue.product_name) for catalogue in user_catalogues]
        else:
            flash('Unable to display Edit listing form, target listing maybe removed', 'danger')
            return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('unable to display edit listing form due to issue in data collection', 'danger')
        return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
    
    # Post Requests
    success = True
    error_message = ''
    if request.method == 'POST':
        try:
            if form and form.validate_on_submit():
                # update only what needed reduce db request
                if target_listing.catalogue_id != form.catalogue_id.data:
                    target_listing.catalogue_id = form.catalogue_id.data

                if target_listing.platform != form.platform.data:
                    target_listing.platform = form.platform.data
                target_listing.update()
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            success = None
        finally:
            if success == True:
                flash('successfully edited the listing', 'success')
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
            elif success == False:
                return render_template('crud/edit_listing.html',form=form, dashboard_id=dashboard_id, listing_id=listing_id)
            else:
                flash('Unknown error, Unable to edit listing', 'danger')
                return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
    else:
        # GET requests
        return render_template('crud/edit_listing.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id)
    
@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_listing(dashboard_id, listing_id):
    try:
        form = removeListingForm()
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).one_or_none()
        if target_listing is not None:
            if form.validate_on_submit():
                target_listing.delete()
                flash('Successfully deleted Listing ID: {}'.format(listing_id), 'success')
            else:
                flash('Unable to delete Listing, ID: {}'.format(listing_id), 'danger')
        else:
            flash('Listing not found it maybe deleted, ID: {}'.format(listing_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete Listing', 'danger')
    finally:
        return redirect(url_for('routes.listings', dashboard_id=dashboard_id))

################ -------------------------- Listing Purchases (this purchases based on selected listing from any supplier) -------------------- ################
@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/purchases/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def view_purchase_listing(dashboard_id, listing_id, purchase_id):
    success = True
    target_purchase = None
    try:        
        deleteform = removePurchaseForm()
        # user dashboard, listing id to keep index stable and not generate invalid pages to the app (if dashboard, and listing id user can view his orders from invalid urls which not stable for indexing)
        target_purchase = db.session.query(
            Purchase
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            success = False
            flash('unable to find selected purchase with id: ({}), it maybe deleted or you use invalid url', 'danger')

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Purchase with id: {}'.format(purchase_id), 'danger')
        success = False
    finally:
        if success == True:
            return render_template('purchase.html', purchase=target_purchase, dashboard_id=dashboard_id, listing_id=listing_id, deleteform=deleteform)
        else:
            return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=dashboard_id))
            

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/purchases/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_purchase_listing(dashboard_id, listing_id):
    form = None
    target_listing = None
    dashboard_listings = []
    try:
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id            
        ).one_or_none()
        if target_listing is None:
            flash('Unable to find listing with id: ({})'.format(listing_id), 'danger')
            return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
        
        form = addPurchaseForm(listing_id=target_listing.id)
        # user using this route can only use the listing of selected dashboard so not allow another dashboard's listing to be submited some how using this route as it not provided
        dashboard_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Purchase form', 'danger')
        return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
    
    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                # confirm listing id and supplier id are in user listings and suppliers (else user can create request for other user's suppliers)
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids:
                    new_purchase = Purchase(quantity=form.quantity.data, date=form.date.data, supplier_id=form.supplier_id.data, listing_id=form.listing_id.data)
                    new_purchase.insert()
                else:
                    # invalid listing_id or supplier id, or listing_id not in selected dashboard, this should done from supplier which allow that secuirty
                    success = None
                    flash('Unable to add New Purchase make sure data is valid', 'danger')
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to Add Purchase', 'danger')
            success = None
        finally:
            if success == True:
                flash('Successfully Created New Purchase for Supplier With ID:'.format(form.supplier_id.data))
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
            elif success == False:
                return render_template('crud/add_purchase_listing.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id)
            else:
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
            
    else:
        return render_template('crud/add_purchase_listing.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id)

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/purchases/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_purchase_listing(dashboard_id, listing_id, purchase_id):
    form = None
    target_purchase = None
    dashboard_listings = []
    try:
        target_purchase = db.session.query(
            Purchase
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            flash('Unable to find Purchase with id: ({})'.format(purchase_id), 'danger')
            return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
        
        form = editPurchaseForm(listing_id=target_purchase.listing_id, supplier_id=target_purchase.supplier_id, quantity=target_purchase.quantity, date=target_purchase.date)
        # user using this route can only use the listing of selected dashboard so not allow another dashboard's listing to be submited some how using this route as it not provided
        dashboard_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Purchase form', 'danger')
        return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
    
    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids:
                    if target_purchase.listing_id != form.listing_id.data:
                        target_purchase.listing_id = form.listing_id.data

                    if target_purchase.supplier_id != form.supplier_id.data:
                        target_purchase.supplier_id = form.supplier_id.data

                    if target_purchase.quantity != form.quantity.data:
                        target_purchase.quantity = form.quantity.data

                    if target_purchase.date != form.date.data:
                        target_purchase.date = form.date.data

                    target_purchase.update()
                else:                    
                    flash('Unable to edit Purchases with ID:{}'.format(purchase_id), 'danger')
                    success = None
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to edit Purchase with id: {}'.format(purchase_id), 'danger')
            success = None
        finally:
            if success == True:
                flash('Successfully Edited Purchases With ID:{}'.format(purchase_id), 'success')
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
            elif success == False:
                return render_template('crud/edit_purchase_listing.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id, purchase_id=purchase_id)
            else:
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
    else:
        return render_template('crud/edit_purchase_listing.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id, purchase_id=purchase_id)

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/purchases/<int:purchase_id>/delete', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_purchase_listing(dashboard_id, listing_id, purchase_id):
    try:
        form = removePurchaseForm()
        # user can change url by mistake so this query prevent any invalid url not given by system (unlike supplier purchase which is global for any dashboard) (Supplier Purchase diffrent alot that listing purchase)
        target_purchase = db.session.query(
            Purchase
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()
        if target_purchase is not None:
            if form.validate_on_submit():
                target_purchase.delete()
                flash('Successfully removed purchase with ID: {}'.format(purchase_id), 'success')
            else:
                # security wtform
                flash('Unable to delete purchase with ID: {} , invalid Data'.format(purchase_id), 'danger')
        else:
            flash('Unable to delete purchase with ID: {} , it not found or delete'.format(purchase_id), 'danger')
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit purchase with id: {}'.format(purchase_id), 'danger')
    finally:
        return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))


################ -------------------------- Listings Orders -------------------- ################

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/orders/<int:order_id>', methods=['GET'])
@login_required
@vendor_permission.require()
def view_order(dashboard_id, listing_id, order_id):    
    success = True
    target_order = None
    try:        
        deleteform = removeOrderForm()
        # user dashboard, listing id to keep index stable and not generate invalid pages to the app (if dashboard, and listing id user can view his orders from invalid urls which not stable for indexing)
        target_order = db.session.query(
            Order
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Order.id == order_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()

        if target_order is None:
            success = False
            flash('unable to find selected order with id: ({}), it maybe deleted or you use invalid url', 'danger')

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Order with id: {}'.format(order_id), 'danger')
        success = False
    finally:
        if success == True:
            return render_template('order.html', order=target_order, dashboard_id=dashboard_id, listing_id=listing_id, deleteform=deleteform)
        else:
            return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=dashboard_id))
        

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/orders/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_order(dashboard_id, listing_id):
    form = None
    target_listing = None
    dashboard_listings = []
    try:
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id            
        ).one_or_none()
        if target_listing is None:
            flash('Unable to find listing with id: ({})'.format(listing_id), 'danger')
            return redirect(url_for('routes.listings', dashboard_id=dashboard_id))
        
        form = addOrderForm(listing_id=target_listing.id)
        # user using this route can only use the listing of selected dashboard so not allow another dashboard's listing to be submited some how using this route as it not provided
        dashboard_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Order form', 'danger')
        return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))

    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings]
                
                # note I allow user to change the listing in form thats why I query again  (the listing_id already vaildted in the if so it belongs to the user)
                selected_listing = Listing.query.filter_by(id=form.listing_id.data).one_or_none()                
                if valid_ids and selected_listing is not None:
                    # check the quanity first
                    order_quantity = int(form.quantity.data)
                    catalogue_quantity = int(selected_listing.catalogue.quantity)
                    if catalogue_quantity >= order_quantity:
                        new_order = Order(
                            listing_id=form.listing_id.data,
                            quantity=form.quantity.data,
                            date=form.date.data,
                            customer_firstname=form.customer_firstname.data,
                            customer_lastname=form.customer_lastname.data
                        )
                        new_order.insert()
                        selected_listing.catalogue.quantity = int(catalogue_quantity - order_quantity)
                        selected_listing.catalogue.update()
                        flash('Successfully Created New Order', 'success')
                    else:
                        flash('Unable to add order, the order quantity is greater than the available catalog quantity', 'warning')
                        success = False
                else:
                    # user provided new diffrent listing_id can be owned by other dashboard or other user
                    flash('Unable to add order invalid listing provided', 'danger')
                    success = None
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to create new Order', 'danger')        
            success = None
        finally:
            if success == True:
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
            elif success == False:
                return render_template('crud/add_order.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id)
            else:
                return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
    else:
        return render_template('crud/add_order.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id)

@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_order(dashboard_id, listing_id, order_id):
    form = None
    target_order = None
    dashboard_listings = []
    redirect_url = None
    try:
        # edit order is strict in all routes
        target_order = db.session.query(
            Order
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Order.id == order_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()

        if target_order is None:
            flash('Unable to find Order with id: ({})'.format(order_id), 'danger')
            return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
        
        form = editOrderForm(
            listing_id=target_order.listing_id,
            quantity=target_order.quantity,
            date=target_order.date,
            customer_firstname=target_order.customer_firstname,
            customer_lastname=target_order.customer_lastname
        )
        # user using this route can only use the listing of selected dashboard so not allow another dashboard's listing to be submited some how using this route as it not provided
        dashboard_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id,
            Dashboard.id == dashboard_id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Order form', 'danger')
        return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
    
    if request.method == 'POST':
        success = True
        actions = 0
        quantity_changed = False
        current_order_quantity = 0
        try:
            if form.validate_on_submit():
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings]
                selected_listing = Listing.query.filter_by(id=form.listing_id.data).one_or_none()
                if valid_ids and selected_listing:

                    if target_order.listing_id != form.listing_id.data:
                        target_order.listing_id = form.listing_id.data
                        actions += 1

                    if target_order.quantity != form.quantity.data:
                        current_order_quantity = target_order.quantity
                        target_order.quantity = form.quantity.data
                        actions += 1
                        quantity_changed = True

                    if target_order.date != form.date.data:
                        target_order.date = form.date.data
                        actions += 1

                    if target_order.customer_firstname != form.customer_firstname.data:
                        target_order.customer_firstname = form.customer_firstname.data
                        actions += 1

                    if target_order.customer_lastname != form.customer_lastname.data:
                        target_order.customer_lastname = form.customer_lastname.data
                        actions += 1
                    
                
                    if actions > 0:
                        
                        if quantity_changed:
                            # this check can block the whole update action incase it fails
                            order_quantity = int(form.quantity.data)
                            catalogue_quantity = int(selected_listing.catalogue.quantity)

                            
                            # (the edit action made here, else can check if new order bigger than so substract less than then add but this 1 step) first back the cataloug quanity as it was before this order added then check the new requested quantity (not direct - as this edit)
                            original_catalogue_quantity = int(catalogue_quantity + current_order_quantity)                                                    
                            if original_catalogue_quantity >= order_quantity:
                                # make the update action only if this check passed
                                target_order.update()
                                selected_listing.catalogue.quantity = int(original_catalogue_quantity - order_quantity)
                                selected_listing.catalogue.update()
                                flash('Successfully Updated The order', 'success')
                            else:
                                flash('Unable to add edit, the order quantity is greater than the available catalog quantity', 'warning')
                                success = False
                        else: 
                            # here quantity not changed so direct update others
                            target_order.update()
                            flash('Successfully Updated The order', 'success')
                    else:
                        # nothing changed user opened the edit page and click edit
                        flash('Successfully Updated The order', 'success')

                else:
                    flash('Unable to edit order invalid listing provided', 'danger')
                    success = None
            else:
                # wtforms error (render_template)
                success = False
            
            redirect_url = form.action_redirect.data if form.action_redirect.data else None
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to display Add Order form', 'danger')
        
        finally:
            if success == False:
                return render_template('crud/edit_order.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id, order_id=order_id)
            else:
                if redirect_url is not None:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))
        
    else:
        return render_template('crud/edit_order.html', form=form, dashboard_id=dashboard_id, listing_id=listing_id, order_id=order_id)
        



@routes.route('/dashboards/<int:dashboard_id>/listings/<int:listing_id>/orders/<int:order_id>/delete', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_order(dashboard_id, listing_id, order_id):
    redirect_url = None
    try:
        form = removeOrderForm()
        # user can change url by mistake so this query prevent any invalid url not given by system (unlike supplier purchase which is global for any dashboard) (Supplier Purchase diffrent alot that listing purchase)
        target_order = db.session.query(
            Order
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Order.id == order_id,
            Listing.id == listing_id,
            Dashboard.id == dashboard_id,
            User.id == current_user.id
        ).one_or_none()

        if target_order is not None:
            if form.validate_on_submit():
                current_quantity = int(target_order.listing.catalogue.quantity)
                order_quantity = int(target_order.quantity)
                target_order.listing.catalogue.quantity = order_quantity + order_quantity
                target_order.delete()
                flash('Successfully removed order with ID: {}'.format(order_id), 'success')
            else:
                # security wtform
                flash('Unable to delete order with ID: {} , invalid Data'.format(order_id), 'danger')
        else:
            flash('Unable to delete order with ID: {} , it not found or delete'.format(order_id), 'danger')
        
        redirect_url = form.action_redirect.data if form.action_redirect.data else None
    except Exception as e:
        print('System Error delete_order: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit order with id: {}'.format(order_id), 'danger')
    finally:
        if redirect_url is not None:
            return redirect(redirect_url)            
        else:
            return redirect(url_for('routes.view_listing', dashboard_id=dashboard_id, listing_id=listing_id))



################ -------------------------- All Default Dashboard Orders -------------------- ################
@routes.route('/orders', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def orders():
    try:
        request_page = request.args.get('page', 1)
        order_remove = removeOrderForm()
        default_dashboard = Dashboard.query.filter_by(default=True, user_id=current_user.id).first()
        if default_dashboard is not None:
            orders_query = db.session.query(
                Order
            ).join(
                Listing
            ).filter(
                Listing.dashboard_id == default_dashboard.id,
            )
            pagination = makePagination(
                request_page,
                orders_query,
                lambda total_pages: [url_for('routes.orders', page=page_index) for page_index in range(1, total_pages+1)]
            )
            
            action_redirect = url_for('routes.orders', page=request_page)
            orders = pagination['data']
            return render_template('orders.html', orders=orders, pagination_btns=pagination['pagination_btns'], order_remove=order_remove, action_redirect=action_redirect)
        else:
            flash("No default dashboard found, if you haven't created a dashboard you will need to create one and it will automatically be set as the default dashboard", 'warning')
            return redirect(url_for('routes.index'))
    except Exception as e:
        print('System Error orders: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display orders page', 'danger')
        return redirect(url_for('main.home'))

################ -------------------------- Suppliers -------------------- ################
@routes.route('/suppliers', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def suppliers():
    success = True
    try:
        addform = addSupplierForm()
        editform = editSupplierForm()
        deleteform = removeSupplierForm()
        suppliers = Supplier.query.filter_by(user_id=current_user.id).all()
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display suppliers page', 'danger')
        success = False
    finally:
        if success == True:
            return render_template('suppliers.html', suppliers=suppliers, addform=addform, editform=editform, deleteform=deleteform)
        else:
            return redirect(url_for('routes.index'))

@routes.route('/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
@vendor_permission.require()
def view_supplier(supplier_id):
    success = True
    try:
        deleteform = removeSupplierForm()
        delete_purchase_form = removePurchaseForm()
        supplier = Supplier.query.filter_by(id=supplier_id, user_id=current_user.id).one_or_none()
        purchases = Purchase.query.filter_by(supplier_id=supplier.id).all()
        if supplier is None:
            flash('Unable to Find Supplier with id: {}, it maybe deleted.'.format(supplier_id), 'danger')
            success = False
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display suppliers page', 'danger')
        success = False
    finally:
        if success == True:
            return render_template('supplier.html', supplier=supplier, purchases=purchases,deleteform=deleteform,delete_purchase_form=delete_purchase_form)
        else:
            return redirect(url_for('routes.suppliers'))

@routes.route('/suppliers/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_supplier():
    success = True
    try:
        form = addSupplierForm()
        if form.validate_on_submit():
            new_supplier = Supplier(name=form.name.data, user_id=current_user.id, phone=form.full_phone_add.data, address=form.address.data)
            new_supplier.insert()
        else:
            for field, errors in form.errors.items():
                if field == 'full_phone_add':
                    field = 'phone'
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to add supplier', 'danger')
        success = False
    
    finally:
        if success == True:
            flash('Successfully created new supplier', 'success')

        return redirect(url_for('routes.suppliers'))


@routes.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_supplier(supplier_id):
    success = True
    actions = 0
    try:
        form = editSupplierForm()
        if form.validate_on_submit():
            target_supplier = Supplier.query.filter_by(id=supplier_id, user_id=current_user.id).one_or_none()
            if target_supplier is not None:
                if target_supplier.name != form.name.data:
                    target_supplier.name = form.name.data
                    actions += 1

                if target_supplier.phone != form.full_phone_edit.data:
                    target_supplier.phone = form.full_phone_edit.data
                    actions += 1

                if target_supplier.address != form.address.data:
                    target_supplier.address = form.address.data
                    actions += 1
                
                if actions > 0:
                    target_supplier.update()
            else:
                success = False
                flash('supplier with ID: ({})  not found or deleted'.format(supplier_id))
        else:
            for field, errors in form.errors.items():
                if field == 'full_phone_edit':
                    field = 'phone'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit supplier', 'danger')
        success = False
    finally:
        if success == True:
            flash('Successfully edit supplier ID:({})'.format(supplier_id), 'success')
        return redirect(url_for('routes.suppliers'))
        
@routes.route('/suppliers/<int:supplier_id>/delete', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_supplier(supplier_id):
    try:
        form = removeSupplierForm()
        target_supplier = Supplier.query.filter_by(id=supplier_id,user_id=current_user.id).one_or_none()
        if target_supplier is not None:
            if form.validate_on_submit():
                target_supplier.delete()
                flash('Successfully deleted Supplier ID: {}'.format(supplier_id), 'success')
            else:
                flash('Unable to delete Supplier, ID: {}'.format(supplier_id), 'danger')
        else:
            flash('Cupplier not found it maybe deleted, ID: {}'.format(supplier_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete supplier', 'danger')
    finally:
        return redirect(url_for('routes.suppliers'))


################ -------------------------- Supplier Purchases (this purchases based on selected supplier) -------------------- ################
@routes.route('/suppliers/<int:supplier_id>/purchases/<int:purchase_id>', methods=['GET'])
@login_required
@vendor_permission.require()
def view_purchase_supplier(supplier_id, purchase_id):
    success = True
    target_purchase = None
    try:        
        deleteform = removePurchaseForm()
        # user dashboard, listing id to keep index stable and not generate invalid pages to the app (if dashboard, and listing id user can view his orders from invalid urls which not stable for indexing)
        target_purchase = db.session.query(
            Purchase
        ).join(
            Supplier
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            Supplier.id == supplier_id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            success = False
            flash('unable to find selected purchase with id: ({}), it maybe deleted or you use invalid url', 'danger')

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Purchase with id: {}'.format(purchase_id), 'danger')
        success = False
    finally:
        if success == True:
            
            return render_template('purchase.html', purchase=target_purchase, dashboard_id=target_purchase.listing.dashboard_id, listing_id=target_purchase.listing_id, deleteform=deleteform)
        else:
            return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
        

@routes.route('/suppliers/<int:supplier_id>/purchases/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_purchase_supplier(supplier_id):
    form = None
    target_supplier = None
    user_listings = []
    try:
        target_supplier = Supplier.query.filter_by(id=supplier_id, user_id=current_user.id).one_or_none()
        form = addPurchaseForm(supplier_id=target_supplier.id)
        user_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in user_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]
        if target_supplier is None:
            flash('Unable to find supplier with id: ({})'.format(supplier_id), 'danger')
            return redirect(url_for('routes.suppliers'))
        
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Purchase form', 'danger')
        return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))


    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                # confirm listing id and supplier id are in user listings and suppliers (else user can create request for other user's suppliers)
                valid_ids = int(form.listing_id.data) in [listing.id for listing in user_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids:
                    new_purchase = Purchase(quantity=form.quantity.data, date=form.date.data, supplier_id=form.supplier_id.data, listing_id=form.listing_id.data)
                    new_purchase.insert()
                else:
                    # invalid listing or supplier id, secuirty
                    success = None
                    flash('Unable to add New Purchase make sure data is valid', 'danger')
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to Add Purchase', 'danger')
            success = None
        finally:
            if success == True:
                flash('Successfully Created New Purchase for Supplier With ID:'.format(form.supplier_id.data))
                return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
            elif success == False:
                return render_template('crud/add_purchase_supplier.html', form=form, supplier_id=supplier_id)
            else:
                return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
    else:
        return render_template('crud/add_purchase_supplier.html', form=form, supplier_id=supplier_id)



@routes.route('/suppliers/<int:supplier_id>/purchases/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_purchase_supplier(supplier_id, purchase_id):
    form = None
    target_supplier = None
    target_purchase = None
    user_listings = []
    try:
        target_supplier = Supplier.query.filter_by(id=supplier_id, user_id=current_user.id).one_or_none()
        if target_supplier is None:
            flash('Unable to find supplier with id: ({})'.format(supplier_id), 'danger')
            return redirect(url_for('routes.suppliers'))
    
        target_purchase = db.session.query(
            Purchase
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            flash('Unable to find Purchase with id: ({})'.format(purchase_id), 'danger')
            return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
        
        form = editPurchaseForm(supplier_id=target_purchase.supplier_id, listing_id=target_purchase.listing_id, quantity=target_purchase.quantity, date=target_purchase.date)
        user_listings = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in user_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]
        
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Edit Purchase form', 'danger')
        return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
    
    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                valid_ids = int(form.listing_id.data) in [listing.id for listing in user_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids:
                    if target_purchase.listing_id != form.listing_id.data:
                        target_purchase.listing_id = form.listing_id.data

                    if target_purchase.supplier_id != form.supplier_id.data:
                        target_purchase.supplier_id = form.supplier_id.data

                    if target_purchase.quantity != form.quantity.data:
                        target_purchase.quantity = form.quantity.data

                    if target_purchase.date != form.date.data:
                        target_purchase.date = form.date.data

                    target_purchase.update()
                else:                    
                    flash('Unable to edit Purchases with ID:{}'.format(purchase_id), 'danger')
                    success = None
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to edit Purchase with id: {}'.format(purchase_id), 'danger')
            success = None
        finally:
            if success == True:
                flash('Successfully Edited Purchases With ID:{}'.format(purchase_id), 'success')
                return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
            elif success == False:
                return render_template('crud/edit_purchase_supplier.html', form=form, supplier_id=supplier_id, purchase_id=purchase_id)
            else:
                return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))
    else:
        return render_template('crud/edit_purchase_supplier.html', form=form, supplier_id=supplier_id, purchase_id=purchase_id)
    
@routes.route('/suppliers/<int:supplier_id>/purchases/<int:purchase_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_purchase_supplier(supplier_id, purchase_id):
    try:
        form = removePurchaseForm()
        target_purchase = db.session.query(
            Purchase
        ).join(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Purchase.id == purchase_id,
            User.id == current_user.id
        ).one_or_none()
        if target_purchase is not None:
            if form.validate_on_submit():
                target_purchase.delete()
                flash('Successfully removed purchase with ID: {}'.format(purchase_id), 'success')
            else:
                # security wtform
                flash('Unable to delete purchase with ID: {} , invalid Data'.format(purchase_id), 'danger')
        else:
            flash('Unable to delete purchase with ID: {} , it not found or delete'.format(purchase_id), 'danger')
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit purchase with id: {}'.format(purchase_id), 'danger') 
    finally:
        return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))

@routes.errorhandler(403)
def method_not_allowed(e):
    #session['redirected_from'] = request.url
    return redirect(url_for('auth.logout'))