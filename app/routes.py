import json
import sys
import os
import random
from flask import Flask, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify
from flask_wtf import Form
from .models import User, Supplier, Dashboard, Listing, Catalogue, Purchase, Order, Platform, ListingPlatform
from .forms import addListingForm, editListingForm, addCatalogueForm, editCatalogueForm, \
removeCatalogueForm, removeListingForm, addSupplierForm, editSupplierForm, removeSupplierForm, \
addPurchaseForm, editPurchaseForm, removePurchaseForm, addOrderForm, editOrderForm, removeOrderForm, CatalogueExcelForm, \
addPlatformForm, editPlatformForm, removePlatformForm
from . import vendor_permission, db
from .functions import get_safe_redirect, updateDashboardListings, updateDashboardOrders, updateDashboardPurchasesSum, secureRedirect
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user
import flask_excel
from flask import request as flask_request


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
################ -------------------------- Dashboard -------------------- ################
@routes.route('/', methods=['GET'])
@routes.route('/home', methods=['GET'])
@login_required
@vendor_permission.require()
def index():
    try:
        deleteform = removeListingForm()
        delete_purchase = removePurchaseForm(action_redirect=url_for('routes.index'))
        delete_order =  removeOrderForm(action_redirect=url_for('routes.index'))

        add_platform =  addPlatformForm(action_redirect=url_for('routes.index'), dashboard_id=current_user.dashboard.id)
        edit_platform =  editPlatformForm(action_redirect=url_for('routes.index'))
        delete_platform =  removePlatformForm(action_redirect=url_for('routes.index'))

        return render_template('index.html', dashboard=current_user.dashboard, deleteform=deleteform, delete_purchase=delete_purchase, delete_order=delete_order, add_platform=add_platform, edit_platform=edit_platform, delete_platform=delete_platform)
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        # flash('Unknown error unable to view product', 'danger')
        return 'system error', 500

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
            # update event will done after success = True, so incase error in that event set success to False 
            success = None

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
@routes.route('/listings', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def listings():    
    try:
        user_dashboard_listings_q = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            User.id == current_user.id,
            Dashboard.id == current_user.dashboard.id
        )
    # total_pages + 1 (becuase range not take last number while i need it to display the last page)
        pagination = makePagination(
                request.args.get('page', 1),
                user_dashboard_listings_q,
                lambda total_pages: [url_for('routes.listings', page=page_index) for page_index in range(1, total_pages+1)]
        )
        user_dashboard_listings = pagination['data']

        return render_template('listings.html', listings=user_dashboard_listings, pagination_btns=pagination['pagination_btns'])
    except Exception as e:
        flash('Unknown error Unable to view Listings', 'danger')
        return redirect(url_for('routes.index'))

@routes.route('/listings/<int:listing_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def view_listing(listing_id):
    success = True
    message = ''
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
            Dashboard.id == current_user.dashboard.id
        ).one_or_none()
        if not target_listing:
            message = 'The listing specified with id: {} could not be found. It may be removed or deleted.'.format(listing_id)
            success = False            
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        message = 'Unknown error Unable to view Listing'
        success = False
    finally:
        if success == True:
            return render_template('listing.html', listing=target_listing, deleteform=deleteform, delete_purchase=delete_purchase,delete_order=delete_order)
        else:
            flash(message, 'danger')
            return redirect(url_for('routes.index'))


# create new listing
@routes.route('/listings/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_listing():
    form = addListingForm()
    platforms_ids = []
    try:
        user_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
        form.catalogue_id.choices = [(catalogue.id, catalogue.product_name) for catalogue in user_catalogues]
        form.platforms.choices = [(platform.id, platform.name) for platform in current_user.dashboard.platforms]
    except:
        flash('unable to display add listing form due to isssue in catalogues', 'danger')
        return redirect(url_for('routes.index'))

    if request.method == 'POST':
        success = None
        try:
            if form.validate_on_submit():
                # confirm selected platforms owns by user
                valid_platforms = True
                current_dashboard_id = current_user.dashboard.id
                for platform_id in form.platforms.data:
                    target_platform = Platform.query.filter_by(id=platform_id, dashboard_id=current_dashboard_id).one_or_none()
                    if target_platform:
                        platforms_ids.append(target_platform.id)
                    else:
                        valid_platforms = False

                if valid_platforms:
                    user_dashboard = current_user.dashboard
                    new_listing = Listing(dashboard_id=user_dashboard.id, catalogue_id=form.catalogue_id.data)
                    new_listing.insert()
                    # add the listing platforms
                    for platform_id in platforms_ids:
                        new_listing_platform = ListingPlatform(listing_id=new_listing.id, platform_id=platform_id)
                        new_listing_platform.insert()

                    # set the number of total listings after adding action
                    updateDashboardListings(user_dashboard)
                    success = True
                else:
                    flash('Unable to add listing invalid platforms', 'danger')
                    success = False
            else:
                success = False
                
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown Error unable to create new Listing', 'danger')
            success = None
            raise e

 
        finally:
            if success == True:
                flash('Successfully Created New Listing', 'success')
                return redirect(url_for('routes.listings'))
            elif success == None:
                return redirect(url_for('routes.listings'))
            else:
                return render_template('crud/add_listing.html', form=form)

    else:
        # GET Requests
        try:
            return render_template('crud/add_listing.html', form=form)
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            return redirect(url_for('routes.index'))

@routes.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_listing(listing_id):
    
    # route setup
    form = None
    target_listing = None
    platforms_ids = []
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
            Dashboard.id == current_user.dashboard.id
        ).one_or_none()
        
        if target_listing is not None:
            listing_platforms = [listing_platform.platform.id for listing_platform in target_listing.platforms]
            form = editListingForm(
                catalogue_id=target_listing.catalogue_id,
                platforms=listing_platforms
            )
            user_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
            form.catalogue_id.choices = [(catalogue.id, catalogue.product_name) for catalogue in user_catalogues]
            form.platforms.choices = [(platform.id, platform.name) for platform in current_user.dashboard.platforms]
        else:
            flash('Unable to display Edit listing form, target listing maybe removed', 'danger')
            return redirect(url_for('routes.listings'))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('unable to display edit listing form due to issue in data collection', 'danger')
        return redirect(url_for('routes.listings'))
    
    # Post Requests
    success = True
    error_message = ''
    if request.method == 'POST':
        try:
            selected_catalogue = Catalogue.query.filter_by(id=form.catalogue_id.data, user_id=current_user.id).one_or_none()
            
            # confirm selected platforms owns by user
            valid_platforms = True
            current_dashboard_id = current_user.dashboard.id
            for platform_id in form.platforms.data:
                target_platform = Platform.query.filter_by(id=platform_id, dashboard_id=current_dashboard_id).one_or_none()
                if target_platform:
                    platforms_ids.append(target_platform.id)
                else:
                    valid_platforms = False

            current_listing_platforms = [listing_platform.platform.id for listing_platform in target_listing.platforms]
            
            if form and form.validate_on_submit() and selected_catalogue and valid_platforms:

                # update only what needed reduce db request
                if target_listing.catalogue_id != form.catalogue_id.data:
                    
                    # back catalogue as it was before moved listing
                    listing_purchases_quantity = sum([int(p.quantity) for p in target_listing.purchases])
                    listing_orders_quantity = sum([int(o.quantity) for o in target_listing.orders])
                    original_quantity = int(target_listing.catalogue.quantity) + listing_orders_quantity
                    original_quantity = original_quantity - listing_purchases_quantity
                    original_quantity = original_quantity if original_quantity >= 0 else 0
                    

                    # new catalogue qauntity after current listing's purchases (without work with dates)
                    new_quantity = int(selected_catalogue.quantity) + listing_purchases_quantity

                    #return str(new_quantity > listing_orders_quantity)
                    # check if new catalogue after added purchases to it accept the number of orders or not
                    if new_quantity >= listing_orders_quantity:
                        # new catalogue quantity after current listing's order
                        new_quantity = new_quantity - listing_orders_quantity


                        target_listing.catalogue_id = form.catalogue_id.data
                        target_listing.catalogue.quantity = original_quantity
                        selected_catalogue.quantity = new_quantity


                        # update platforms
                        for old_platform in target_listing.platforms:
                            if old_platform.platform.id not in platforms_ids:
                                old_platform.delete()
                            
                        for platform_id in platforms_ids:
                            if platform_id not in current_listing_platforms:
                                new_listing_platform = ListingPlatform(listing_id=target_listing.id,platform_id=platform_id)
                                new_listing_platform.insert()

                        target_listing.catalogue.update()
                        target_listing.update()
                        # listing sync with new catalogue done on catalogue after update
                        selected_catalogue.update()
                        target_listing.sync_listing()
                    else:
                        flash("Unable to edit the list, the new catalogue quantity does not accept the listing's orders, please add purchase to this listing, or edit the new catalogue quantity before editing.", "warning")
                        success = False
                else:
                    # update platforms
                    for old_platform in target_listing.platforms:
                        if old_platform.platform.id not in platforms_ids:
                            old_platform.delete()
                        
                    for platform_id in platforms_ids:
                        if platform_id not in current_listing_platforms:
                            new_listing_platform = ListingPlatform(listing_id=target_listing.id,platform_id=platform_id)
                            new_listing_platform.insert()

                    #target_listing.update()
            else:
                success = False
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            success = None

        finally:
            if success == True:
                flash('successfully edited the listing', 'success')
                return redirect(url_for('routes.view_listing', listing_id=listing_id))
            elif success == False:
                return render_template('crud/edit_listing.html',form=form, listing_id=listing_id)
            else:
                flash('Unknown error, Unable to edit listing', 'danger')
                return redirect(url_for('routes.listings'))

    else:
        # GET requests
        return render_template('crud/edit_listing.html', form=form, listing_id=listing_id)

# need after_delete
@routes.route('/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_listing(listing_id):
    try:
        user_dashboard = current_user.dashboard
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
            Dashboard.id == user_dashboard.id
        ).one_or_none()
        if target_listing is not None:
            if form.validate_on_submit():
                orders_total = sum([order.quantity for order in target_listing.orders])
                purchases_total = sum([purchase.quantity for purchase in target_listing.purchases])
                
                catalogue_quantity = int(target_listing.catalogue.quantity)
                catalogue_quantity += orders_total
                catalogue_quantity -= purchases_total
                catalogue_quantity = catalogue_quantity if catalogue_quantity >= 0  else 0
                target_listing.catalogue.quantity = catalogue_quantity            
                
                target_listing.delete()
                target_listing.catalogue.update()
                
                # update number of listings after delete action
                updateDashboardListings(user_dashboard)
                flash('Successfully deleted Listing ID: {}'.format(listing_id), 'success')
            else:
                flash('Unable to delete Listing, ID: {}'.format(listing_id), 'danger')
        else:
            flash('Listing not found it maybe deleted, ID: {}'.format(listing_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete Listing', 'danger')
    finally:
        return redirect(url_for('routes.listings'))

################ -------------------------- Listing Purchases (this purchases based on selected listing from any supplier) -------------------- ################
@routes.route('/listings/<int:listing_id>/purchases/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def view_purchase_listing(listing_id, purchase_id):
    success = True
    target_purchase = None
    message = ''
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
            Dashboard.id == current_user.dashboard.id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            success = False
            message = 'unable to find selected purchase with id: ({}), it maybe deleted or you use invalid url'

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        message = 'Unknown error unable to display Purchase with id: {}'.format(purchase_id)
        success = False
    finally:
        if success == True:
            return render_template('purchase.html', purchase=target_purchase, listing_id=listing_id, deleteform=deleteform)
        else:
            flash(message, 'danger')
            return redirect(url_for('routes.view_listing', listing_id=listing_id))
            

@routes.route('/listings/<int:listing_id>/purchases/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_purchase_listing(listing_id):
    form = None
    target_listing = None
    dashboard_listings = []
    user_dashboard = None
    redirect_url = None
    try:
        user_dashboard = current_user.dashboard
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            Dashboard.id == user_dashboard.id,
            User.id == current_user.id            
        ).one_or_none()
        if target_listing is None:
            flash('Unable to find listing with id: ({})'.format(listing_id), 'danger')
            return redirect(url_for('routes.listings'))
        
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
            Dashboard.id == user_dashboard.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Purchase form', 'danger')
        return redirect(url_for('routes.view_listing', listing_id=listing_id))
    
    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                # handle redirect securly
                redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None

                # confirm listing id and supplier id are in user listings and suppliers (else user can create request for other user's suppliers)
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids:
                    new_purchase = Purchase(quantity=form.quantity.data, date=form.date.data, supplier_id=form.supplier_id.data, listing_id=form.listing_id.data)
                    # update sum of dashboard's purchases
                    new_purchase.insert()

                    new_purchase.listing.catalogue.quantity = int(new_purchase.listing.catalogue.quantity) + int(new_purchase.quantity)                                        
                    new_purchase.listing.catalogue.update()
                    updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard)
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
                flash('Successfully Created New Purchase for Supplier With ID:{}'.format(form.supplier_id.data))
                # handle diffrent redirect for better ux
                if not redirect_url:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))
                else:
                    return redirect(redirect_url)
            
            elif success == False:
                return render_template('crud/add_purchase_listing.html', form=form, listing_id=listing_id)
            else:
                if not redirect_url:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))
                else:
                    return redirect(redirect_url)
            
    else:
        return render_template('crud/add_purchase_listing.html', form=form, listing_id=listing_id)

@routes.route('/listings/<int:listing_id>/purchases/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_purchase_listing(listing_id, purchase_id):
    form = None
    target_purchase = None
    dashboard_listings = []
    redirect_url = None
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
            Dashboard.id == current_user.dashboard.id,
            User.id == current_user.id
        ).one_or_none()

        if target_purchase is None:
            flash('Unable to find Purchase with id: ({})'.format(purchase_id), 'danger')
            return redirect(url_for('routes.view_listing', listing_id=listing_id))
        
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
            Dashboard.id == current_user.dashboard.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]
        form.supplier_id.choices = [(supplier.id, supplier.name) for supplier in current_user.suppliers]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Purchase form', 'danger')
        return redirect(url_for('routes.view_listing', listing_id=listing_id))
    
    if request.method == 'POST':
        redirect_url = None
        success = True
        quantity_changed = False
        try:
            if form.validate_on_submit():
                # handle redirect securly
                redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None
                selected_listing = Listing.query.filter_by(id=form.listing_id.data).one_or_none()
                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                if valid_ids and selected_listing:

                    if target_purchase.listing.catalogue.id != selected_listing.catalogue.id:
                        #return 'here listing change to diffrent catalogue'

                        original_quantity = int(target_purchase.listing.catalogue.quantity) - int(target_purchase.quantity)
                        original_quantity = original_quantity if original_quantity >= 0 else 0
                        new_quantity = int(selected_listing.catalogue.quantity) + int(form.quantity.data)

                        if target_purchase.supplier_id != form.supplier_id.data:
                            target_purchase.supplier_id = form.supplier_id.data                          
    
                        if target_purchase.date != form.date.data:
                            target_purchase.date = form.date.data

                        if target_purchase.quantity != form.quantity.data:
                            target_purchase.quantity = form.quantity.data
                            quantity_changed = True
                            
                        if target_purchase.listing_id != form.listing_id.data:
                            target_purchase.listing_id = form.listing_id.data


                        target_purchase.listing.catalogue.quantity = original_quantity
                        selected_listing.catalogue.quantity = new_quantity

                        target_purchase.update()

                        selected_listing.catalogue.update()
                        target_purchase.listing.catalogue.update()

                    else:
                            
                        if target_purchase.supplier_id != form.supplier_id.data:
                            target_purchase.supplier_id = form.supplier_id.data
    
                        if target_purchase.quantity != form.quantity.data:
                            original_quantity = int(target_purchase.listing.catalogue.quantity) - int(target_purchase.quantity)
                            original_quantity = original_quantity if original_quantity >= 0 else 0
                            new_quantity = original_quantity + int(form.quantity.data)
                            target_purchase.quantity = form.quantity.data
                            selected_listing.catalogue.quantity = new_quantity
                            quantity_changed = True
                            
                        if target_purchase.listing_id != form.listing_id.data:
                            target_purchase.listing_id = form.listing_id.data
                            # here listing id changed qauantity effect

                        if target_purchase.date != form.date.data:
                            target_purchase.date = form.date.data

                        target_purchase.update()

                        if quantity_changed:
                            selected_listing.catalogue.update()
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
                if redirect_url is None:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))
                else:
                    return redirect(redirect_url)
                
            elif success == False:
                return render_template('crud/edit_purchase_listing.html', form=form, listing_id=listing_id, purchase_id=purchase_id)
            else:
                if redirect_url is None:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))
                else:
                    return redirect(redirect_url)
    else:
        return render_template('crud/edit_purchase_listing.html', form=form, listing_id=listing_id, purchase_id=purchase_id)

@routes.route('/listings/<int:listing_id>/purchases/<int:purchase_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_purchase_listing(listing_id, purchase_id):
    try:
        user_dashboard = current_user.dashboard
        form = removePurchaseForm()
        redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None
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
            Dashboard.id == user_dashboard.id,
            User.id == current_user.id
        ).one_or_none()
        
        if target_purchase is not None:
            if form.validate_on_submit():

                current_quantity = int(target_purchase.listing.catalogue.quantity)
                purchase_quantity = int(target_purchase.quantity)
                                
                target_catalogue_quantity = current_quantity - purchase_quantity
                # if target_catalogue_quantity < 0:
                #     flash('Note, you need to delete one or more orders that created after the deleted purchase, based on it upcoming qunaity', 'danger')
                target_catalogue_quantity = target_catalogue_quantity if target_catalogue_quantity >= 0 else 0
                target_purchase.listing.catalogue.quantity = target_catalogue_quantity

                target_purchase.delete()
                target_purchase.listing.catalogue.update()
                
                # update sum of dashboard's purchases
                updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard)
                flash('Successfully removed purchase with ID: {}'.format(purchase_id), 'success')
            else:
                # security wtform
                flash('Unable to delete purchase with ID: {} , invalid Data'.format(purchase_id), 'danger')
        else:
            flash('Unable to delete purchase with ID: {} , it not found or delete'.format(purchase_id), 'danger')
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit purchase with id: {}'.format(purchase_id), 'danger')
        raise e

    finally:
        if redirect_url:
            return redirect(redirect_url)
        else:
            return redirect(url_for('routes.view_listing', listing_id=listing_id))


################ -------------------------- Listings Orders -------------------- ################
@routes.route('/listings/<int:listing_id>/orders/<int:order_id>', methods=['GET'])
@login_required
@vendor_permission.require()
def view_order(listing_id, order_id):    
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
            Dashboard.id == current_user.dashboard.id,
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
            return render_template('order.html', order=target_order, listing_id=listing_id, deleteform=deleteform)
        else:
            return redirect(url_for('routes.view_listing', listing_id=listing_id))
        

@routes.route('/listings/<int:listing_id>/orders/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_order(listing_id):
    form = None
    target_listing = None
    dashboard_listings = []
    user_dashboard = None
    redirect_url = None
    try:
        user_dashboard = current_user.dashboard
        target_listing = db.session.query(
            Listing
        ).join(
            Dashboard
        ).join(
            User
        ).filter(
            Listing.id == listing_id,
            Dashboard.id == user_dashboard.id,
            User.id == current_user.id            
        ).one_or_none()
        if target_listing is None:
            flash('Unable to find listing with id: ({})'.format(listing_id), 'danger')
            return redirect(url_for('routes.listings'))
        
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
            Dashboard.id == user_dashboard.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Order form', 'danger')
        return redirect(url_for('routes.view_listing', listing_id=listing_id))

    if request.method == 'POST':
        success = True
        try:
            if form.validate_on_submit():
                redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None 
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
                        #manual
                        new_quantity = int(catalogue_quantity - order_quantity)
                        new_quantity = new_quantity if new_quantity >= 0 else 0
                        selected_listing.catalogue.quantity = new_quantity
                        selected_listing.catalogue.update()

                        # update dashboard orders count
                        updateDashboardOrders(db, Order, Listing, user_dashboard)
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
                if redirect_url is not None:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))
            elif success == False:
                return render_template('crud/add_order.html', form=form, listing_id=listing_id, redirect_url=redirect_url)
            else:
                if redirect_url is not None:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))

    else:
        return render_template('crud/add_order.html', form=form, listing_id=listing_id)


@routes.route('/listings/<int:listing_id>/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_order(listing_id, order_id):
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
            Dashboard.id == current_user.dashboard.id,
            User.id == current_user.id
        ).one_or_none()

        if target_order is None:
            flash('Unable to find Order with id: ({})'.format(order_id), 'danger')
            return redirect(url_for('routes.view_listing', listing_id=listing_id))
        
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
            Dashboard.id == current_user.dashboard.id
        ).all()
        form.listing_id.choices = [(listing.id, '{} - ({})'.format(listing.product_name, listing.sku) ) for listing in dashboard_listings]

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display Add Order form', 'danger')
        return redirect(url_for('routes.view_listing', listing_id=listing_id))
    
    if request.method == 'POST':
        success = True
        actions = 0
        quantity_changed = False
        current_order_quantity = 0
        try:            
            if form.validate_on_submit():
                redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None

                valid_ids = int(form.listing_id.data) in [listing.id for listing in dashboard_listings]
                selected_listing = Listing.query.filter_by(id=form.listing_id.data).one_or_none()


                if valid_ids and selected_listing:
                    # here listing id changed, and this new listing for a diffrent catalogue (note usally every catalogue have 1 listing)
                    if target_order.listing.catalogue.id != selected_listing.catalogue.id:
                                            
                        new_order_quantity0 = int(form.quantity.data)
                        new_catalogue_quantity0 = int(selected_listing.catalogue.quantity)
                        order_quantity0 = int(target_order.quantity)                        
                        catalogue_quantity0 = int(target_order.listing.catalogue.quantity)
                        orginal_quantity0 = catalogue_quantity0 + order_quantity0

                        new_quantity0 = new_catalogue_quantity0 - new_order_quantity0
                        new_quantity0 = new_quantity0 if new_quantity0 >= 0 else new_quantity0

                        # check if new catalogue quanity accept this order quanaity
                        if new_catalogue_quantity0 >= new_order_quantity0:
    
                            if target_order.quantity != form.quantity.data:
                                target_order.quantity = form.quantity.data
        
                            if target_order.date != form.date.data:
                                target_order.date = form.date.data
        
                            if target_order.customer_firstname != form.customer_firstname.data:
                                target_order.customer_firstname = form.customer_firstname.data
        
                            if target_order.customer_lastname != form.customer_lastname.data:
                                target_order.customer_lastname = form.customer_lastname.data
    
                            
                            if target_order.listing_id != form.listing_id.data:
                                target_order.listing_id = form.listing_id.data



                            target_order.listing.catalogue.quantity = orginal_quantity0
                            selected_listing.catalogue.quantity = new_quantity0

                            target_order.update()
                            target_order.listing.catalogue.update()
                            selected_listing.catalogue.update()
                            flash('Successfully Updated The order', 'success')
                        else:
                            flash('Unable to add edit, the order quantity is greater than the new catalog quantity', 'warning')
                            success = False
                    else:
                        # order's listing not changed                    
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
                        
                        if target_order.listing_id != form.listing_id.data:
                            target_order.listing_id = form.listing_id.data
                            actions += 1

                        if actions > 0:
                            
                            if quantity_changed:
                                # this check can block the whole update action incase it fails
                                order_quantity = int(form.quantity.data)
                                catalogue_quantity = int(selected_listing.catalogue.quantity)
    
                                
                                # (the edit action made here, else can check if new order bigger than so substract less than then add but this 1 step) first back the cataloug quanity as it was before this order added then check the new requested quantity (not direct - as this edit)
                                original_catalogue_quantity = int(catalogue_quantity + current_order_quantity)                                                    
                                if original_catalogue_quantity >= order_quantity:
                                    new_quantity = int(original_catalogue_quantity - order_quantity)                                    
                                    target_order.update()
                                    selected_listing.catalogue.quantity = new_quantity                          
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
            
        except Exception as e:
            print('System Error: {} , info: {}'.format(e, sys.exc_info()))
            flash('Unknown error unable to display Edit Order form', 'danger')

        finally:
            if success == False:
                return render_template('crud/edit_order.html', form=form, listing_id=listing_id, order_id=order_id, redirect_url=redirect_url)
            else:
                if redirect_url is not None:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('routes.view_listing', listing_id=listing_id))

    else:
        return render_template('crud/edit_order.html', form=form, listing_id=listing_id, order_id=order_id)
        



@routes.route('/listings/<int:listing_id>/orders/<int:order_id>/delete', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_order(listing_id, order_id):
    redirect_url = None
    try:
        user_dashboard = current_user.dashboard
        form = removeOrderForm()
        redirect_url = secureRedirect(form.action_redirect.data) if form.action_redirect and form.action_redirect.data else None
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
            Dashboard.id == user_dashboard.id,
            User.id == current_user.id
        ).one_or_none()

        if target_order is not None:
            if form.validate_on_submit():

                current_quantity = int(target_order.listing.catalogue.quantity)
                order_quantity = int(target_order.quantity)
                target_order.listing.catalogue.quantity = current_quantity + order_quantity
                target_order.listing.catalogue.update()
                target_order.delete()

                # update dashboard orders count
                updateDashboardOrders(db, Order, Listing, user_dashboard)
                flash('Successfully removed order with ID: {}'.format(order_id), 'success')
            else:
                # security wtform
                flash('Unable to delete order with ID: {} , invalid Data'.format(order_id), 'danger')
        else:
            flash('Unable to delete order with ID: {} , it not found or delete'.format(order_id), 'danger')
    except Exception as e:
        print('System Error delete_order: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit order with id: {}'.format(order_id), 'danger')

    finally:
        if redirect_url is not None:
            return redirect(redirect_url)
        else:
            return redirect(url_for('routes.view_listing', listing_id=listing_id))



################ -------------------------- All Default Dashboard Orders -------------------- ################
@routes.route('/orders', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def orders():
    try:
        request_page = request.args.get('page', 1)
        order_remove = removeOrderForm()

        orders_query = db.session.query(
            Order
        ).join(
            Listing
        ).filter(
            Listing.dashboard_id == current_user.dashboard.id,
        )
        pagination = makePagination(
            request_page,
            orders_query,
            lambda total_pages: [url_for('routes.orders', page=page_index) for page_index in range(1, total_pages+1)]
        )
            
        action_redirect = url_for('routes.orders', page=request_page)
        orders = pagination['data']
        return render_template('orders.html', orders=orders, pagination_btns=pagination['pagination_btns'], order_remove=order_remove, action_redirect=action_redirect)

    except Exception as e:
        print('System Error orders: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to display orders page', 'danger')
        return redirect(url_for('routes.index'))

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
    message = ''
    purchases = []
    try:
        deleteform = removeSupplierForm()
        delete_purchase_form = removePurchaseForm()
        supplier = Supplier.query.filter_by(id=supplier_id, user_id=current_user.id).one_or_none()        
        if supplier is not None:
            purchases = Purchase.query.filter_by(supplier_id=supplier.id).all()
        else:
            message = 'Unable to Find Supplier with id: {}, it maybe deleted.'.format(supplier_id)
            success = False

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        message = 'Unknown error unable to display suppliers page'        
        success = False
    finally:
        if success == True:
            return render_template('supplier.html', supplier=supplier, purchases=purchases,deleteform=deleteform,delete_purchase_form=delete_purchase_form)
        else:
            flash(message, 'danger')
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
                target_listing = db.session.query(Listing).join(Catalogue, Listing.catalogue_id==Catalogue.id).filter(Listing.id==form.listing_id.data, Catalogue.user_id==current_user.id).one_or_none()
                if target_listing:
                    # confirm listing id and supplier id are in user listings and suppliers (else user can create request for other user's suppliers)
                    valid_ids = int(form.listing_id.data) in [listing.id for listing in user_listings] and int(form.supplier_id.data) in [supplier.id for supplier in current_user.suppliers]
                    if valid_ids:
                        new_purchase = Purchase(quantity=form.quantity.data, date=form.date.data, supplier_id=form.supplier_id.data, listing_id=target_listing.id)
                        new_purchase.insert()
                        # update number of quantity of the catalogue (catalogue update it's listings when change)
                        new_purchase.listing.catalogue.quantity = int(new_purchase.listing.catalogue.quantity) + int(new_purchase.quantity)                                        
                        new_purchase.listing.catalogue.update()

                        # update sum of dashboard's purchases
                        updateDashboardPurchasesSum(db, Purchase, Listing, current_user.dashboard)
                    else:
                        # invalid listing or supplier id, secuirty
                        success = None
                        flash('Unable to add New Purchase make sure data is valid', 'danger')
                else:
                    flash('Unable to add New Purchase selected listing not found or deleted', 'danger')
                    success = None
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
                selected_listing = Listing.query.filter_by(id=form.listing_id.data).one_or_none()
                if valid_ids and selected_listing:

                    if target_purchase.listing.catalogue.id != selected_listing.catalogue.id:
                        #return 'here listing change to diffrent catalogue'

                        original_quantity = int(target_purchase.listing.catalogue.quantity) - int(target_purchase.quantity)
                        original_quantity = original_quantity if original_quantity >= 0 else 0
                        new_quantity = int(selected_listing.catalogue.quantity) + int(form.quantity.data)

                        if target_purchase.supplier_id != form.supplier_id.data:
                            target_purchase.supplier_id = form.supplier_id.data                          
    
                        if target_purchase.date != form.date.data:
                            target_purchase.date = form.date.data

                        if target_purchase.quantity != form.quantity.data:
                            target_purchase.quantity = form.quantity.data
                            quantity_changed = True
                            
                        if target_purchase.listing_id != form.listing_id.data:
                            target_purchase.listing_id = form.listing_id.data


                        target_purchase.listing.catalogue.quantity = original_quantity
                        selected_listing.catalogue.quantity = new_quantity

                        target_purchase.update()

                        selected_listing.catalogue.update()
                        target_purchase.listing.catalogue.update()

                    else:
                           
                        if target_purchase.supplier_id != form.supplier_id.data:
                            target_purchase.supplier_id = form.supplier_id.data

                        if target_purchase.quantity != form.quantity.data:
                            original_quantity = int(target_purchase.listing.catalogue.quantity) - int(target_purchase.quantity)
                            original_quantity = original_quantity if original_quantity >= 0 else 0
                            new_quantity = original_quantity + int(form.quantity.data)
                            target_purchase.quantity = form.quantity.data
                            selected_listing.catalogue.quantity = new_quantity
                            quantity_changed = True
                            
    
                        if target_purchase.date != form.date.data:
                            target_purchase.date = form.date.data

                        if target_purchase.listing_id != form.listing_id.data:
                            target_purchase.listing_id = form.listing_id.data

                        target_purchase.update()

                        if quantity_changed:
                            selected_listing.catalogue.update()

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

                current_quantity = int(target_purchase.listing.catalogue.quantity)
                purchase_quantity = int(target_purchase.quantity)

                target_catalogue_quantity = current_quantity - purchase_quantity
                target_catalogue_quantity = target_catalogue_quantity if target_catalogue_quantity >= 0 else 0
                target_purchase.listing.catalogue.quantity = target_catalogue_quantity

                target_purchase.delete()
                target_purchase.listing.catalogue.update()


                # update sum of dashboard's purchases
                updateDashboardPurchasesSum(db, Purchase, Listing, current_user.dashboard)
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


###########################  Dashboard platforms  ##############################
@routes.route('/platforms/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_platform():    
    try:
        form = addPlatformForm()
        if form.validate_on_submit():
            new_platform = Platform(dashboard_id=current_user.dashboard.id, name=form.name_add.data)
            new_platform.insert()
            flash('Successfully Created New Platform', 'success')
        else:
            print(form.errors.items())
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    continue
                if field == 'name_add':
                    field = 'name'
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown Error unable to create new Platform', 'danger')
    finally:       
        return redirect(url_for('routes.index'))

@routes.route('/platforms/<int:platform_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def edit_platform(platform_id):
    success = True
    actions = 0
    try:
        form = editPlatformForm()
        if form.validate_on_submit():
            target_platform = Platform.query.filter_by(id=platform_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_platform is not None:
                if target_platform.name != form.name_edit.data:
                    target_platform.name = form.name_edit.data
                    target_platform.update()
                    flash('Successfully edit platform ID:({})'.format(platform_id), 'success')
                else:
                    flash('No changes Detected.', 'success')
            else:
                flash('platform with ID: ({})  not found or deleted'.format(platform_id))
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    continue

                if field == 'name_edit':
                    field = 'name'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to edit platform', 'danger')
        success = False
    finally:
        return redirect(url_for('routes.index'))

@routes.route('/platforms/<int:platform_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_platform(platform_id):
    try:
        form = removePlatformForm()
        target_platform = Platform.query.filter_by(id=platform_id,dashboard_id=current_user.dashboard.id).one_or_none()
        if target_platform is not None:
            if form.validate_on_submit():
                target_platform.delete()
                flash('Successfully deleted Platform ID: {}'.format(platform_id), 'success')
            else:
                flash('Unable to delete platform, ID: {}'.format(platform_id), 'danger')
        else:
            flash('Platform not found it maybe deleted, ID: {}'.format(platform_id))
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error unable to delete platform', 'danger')
    finally:
        return redirect(url_for('routes.index'))
    

@routes.errorhandler(403)
def method_not_allowed(e):
    #session['redirected_from'] = request.url
    return redirect(url_for('auth.logout'))