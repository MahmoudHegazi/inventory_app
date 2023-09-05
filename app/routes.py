import json
import sys
import os
import random
import decimal
import flask_excel
from flask import Flask, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify, abort, current_app
from flask_wtf import Form
from .models import User, Supplier, Dashboard, Listing, Catalogue, Purchase, Order, Platform, ListingPlatform, WarehouseLocations, LocationBins, \
CatalogueLocations, CatalogueLocationsBins, Category, UserMeta
from .forms import addListingForm, editListingForm, addCatalogueForm, editCatalogueForm, \
removeCatalogueForm, removeListingForm, addSupplierForm, editSupplierForm, removeSupplierForm, \
addPurchaseForm, editPurchaseForm, removePurchaseForm, addOrderForm, editOrderForm, removeOrderForm, CatalogueExcelForm, \
removeCataloguesForm, removeListingsForm, removeAllCataloguesForm, addPlatformForm, editPlatformForm, removePlatformForm, \
addLocationForm, editLocationForm, removeLocationForm, addBinForm, editBinForm, removeBinForm, AddMultipleListingForm, \
addCategoryForm, editCategoryForm, removeCategoryForm, importCategoriesAPIForm, importOffersAPIForm, SetupBestbuyForm
from . import vendor_permission, db
from .functions import get_safe_redirect, updateDashboardListings, updateDashboardOrders, updateDashboardPurchasesSum, secureRedirect, get_charts, \
bestbuy_ready
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user
from flask import request as flask_request
from sqlalchemy import or_, and_

routes = Blueprint('routes', __name__, template_folder='templates', static_folder='static')


def makePagination(page=1, query_obj=None, callback=(), limit_parm=10):
    import math
    try:
        # save integer limit , so can passed direct from query paramter and auto handle incase invalid query paramter set (no code in endpoint)
        str_limit = str(limit_parm).strip()
        limit = int(str_limit) if str_limit and str_limit.isnumeric() else 10
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
        print('System Error makePagination: {}'.format(sys.exc_info()))
        flash('System Error Unable to display Pagination data, please report this problem to us error: 1001', 'danger')
        return {'data': [], 'pagination_btns': []}


# sperate secure app routes  (All Cruds, Add, View, Edit, Delete)
################ -------------------------- Dashboard -------------------- ################
@routes.route('/', methods=['GET'])
@routes.route('/home', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def index():
    try:
        charts_data = get_charts(db, current_user,
            charts_ids=[
                'top_ordered_products',
                'most_purchased_products', 
                'top_purchases_suppliers', 'orders_yearly_performance',
            ]
        )
        return render_template('index.html', dashboard=current_user.dashboard, charts_data=charts_data)
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        # flash('Unknown error unable to view product', 'danger')
        abort(500)
        return 'system error', 500

def populate_add_multiple_form(form, platform, dashboard_id, min_entries=None, max_entries=None):
    try:
        # this function called twice on in get route to inital the form and set min, max entires and process, and fill choices, other call will be only for fill choices as already form inital and should have the entries filled with user inputs
        need_process = False

        user_platforms = platform.query.filter_by(dashboard_id=dashboard_id).all()
        platform_choices = [(platform_obj.id, platform_obj.name) for platform_obj in user_platforms]

        # process will update min and max entries, which will used to create the needed number of inputs for fieldList, then you can access the entries and set it's choices 
        if min_entries is not None:
            form.catalogue_ids.min_entries = min_entries
            form.platforms_selects.min_entries = min_entries
            need_process = True
        
        if max_entries is not None:
            form.catalogue_ids.max_entries = max_entries
            form.platforms_selects.max_entries = max_entries
            need_process = True

        if need_process == True:
            form.process()

        for select_field in form.platforms_selects.entries:
            select_field.choices.extend(platform_choices)
        
    except Exception as e:
        print("error in populate_add_multiple_form")
        raise e

################ -------------------------- Catalogue -------------------- ################
@routes.route('/catalogues', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def catalogues():
    try:
        pagination = makePagination(
            request.args.get('page', 1),
            Catalogue.query.filter_by(user_id=current_user.id),
            lambda total_pages: [url_for('routes.catalogues', page=page_index) for page_index in range(1, total_pages+1)],
            limit_parm=session.get('limit', 10)
        )
        catalogues_excel = CatalogueExcelForm()
        delete_catalogues = removeCataloguesForm()
        delete_all_catalogues = removeAllCataloguesForm()
        add_multiple_listings = AddMultipleListingForm()
        #return str(delete_catalogues.hidden_tag())+str(delete_catalogues.catalogues_ids)
        user_catalogues = pagination['data']
        populate_add_multiple_form(add_multiple_listings, Platform, current_user.dashboard.id, min_entries=len(user_catalogues), max_entries=len(user_catalogues))

        return render_template('catalogues.html', catalogues=user_catalogues,  catalogues_excel=catalogues_excel, pagination_btns=pagination['pagination_btns'], delete_catalogues=delete_catalogues, delete_all_catalogues=delete_all_catalogues, add_multiple_listings=add_multiple_listings)
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('unable to display catalogues page', 'danger')
        raise e
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
        print('System Error: {}'.format(sys.exc_info()))
        flash('unable to display catalogues page', 'danger')
        return redirect(url_for('routes.catalogues'))

@routes.route('/catalogues/add', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_catalogue():
    form = addCatalogueForm()
    locations_choices = []
    # locations_bins_data is json object string sent to javascript client side to handle bin
    locations_bins_data = []
    allowed_bins_ids = []
    try:
        current_locations = WarehouseLocations.query.filter_by(dashboard_id=current_user.dashboard.id).all()
        for location in current_locations:
            current_location_obj = {'location': location.id, 'bins': [bin.id for bin in location.bins]}
            locations_choices.append((location.id, location.name))
            for bin in location.bins:
                allowed_bins_ids.append((bin.id, '{}: {}'.format(location.name, bin.name)))

            locations_bins_data.append(current_location_obj)

        categories = [(cat.code, '{}:{}'.format(cat.code, cat.label)) for cat in Category.query.filter_by(dashboard_id=current_user.dashboard.id).all()]
        form = addCatalogueForm()
        form.warehouse_locations.choices = locations_choices
        form.locations_bins.choices = allowed_bins_ids
        form.category_code.choices = categories
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('unable to process your request', 'danger')
        return redirect(url_for('routes.catalogues'))

    if request.method == 'POST':
        success = None
        try:
            if form.validate_on_submit():
                selected_category = Category.query.filter_by(code=form.category_code.data, dashboard_id=current_user.dashboard.id).first()
                if selected_category:
                    # using sqlalchemy.orm.collections.instrumentedlist append technique to insert all relations one time if catalogue inserted, and in child locations as well so if error happend before inser which last thing all actions will ignored (1 commit for all)
                    new_catalogue = Catalogue(user_id=current_user.id, sku=form.sku.data, product_name=form.product_name.data, product_description=form.product_description.data, brand=form.brand.data, category_code=selected_category.code, price=form.price.data, sale_price=form.sale_price.data, quantity=form.quantity.data, product_model=form.product_model.data, condition=form.condition.data, upc=form.upc.data)
                    for warehouse_location_id in form.warehouse_locations.data:
                        valid_location = WarehouseLocations.query.filter_by(dashboard_id=current_user.dashboard.id, id=warehouse_location_id).one_or_none()
                        if valid_location is not None:
                            new_catalogue_location = CatalogueLocations(location_id=valid_location.id)
                            for bin_id in form.locations_bins.data:
                                valid_bin = LocationBins.query.filter_by(id=bin_id).one_or_none()
                                if valid_bin is not None:
                                    new_location_bin = CatalogueLocationsBins(bin_id=valid_bin.id)
                                    new_catalogue_location.bins.append(new_location_bin)
                            new_catalogue.locations.append(new_catalogue_location)
                    new_catalogue.insert()
                    success = True
                    flash('Successfully Created New Catalogue', 'success')
                else:
                    success = False
                    flash('Invalid Category', 'danger')
            else:
                success = False
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown Error unable to create new Catalogue', 'danger')
            raise e
        
        finally:
            if success == True:
                return redirect(url_for('routes.catalogues'))
            elif success == None:
                return redirect(url_for('routes.catalogues'))
            else:
                return render_template('crud/add_catalogue.html', form=form, locations_bins_data=locations_bins_data)
    else:
        # GET Requests
        try:
            # get dashboard locations and bins data (advanced) (display locations with null bins to fill the warehouse location select options)
            return render_template('crud/add_catalogue.html', form=form, locations_bins_data=locations_bins_data)
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash('unable to display Add new Catalogue page', 'danger')
            return redirect(url_for('routes.catalogues'))

@routes.route('/catalogue/<int:catalogue_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def edit_catalogue(catalogue_id):
    form = None
    target_catalogue = None
    # setup route data and checking
    try:
        locations_choices = []
        locations_bins_data = []
        allowed_bins_ids = []
        allowed_locations_ids = []
        allowed_locations_bins_ids = []
        selected_locs_ids = []
        selected_bins_ids = []
        current_locations = WarehouseLocations.query.filter_by(dashboard_id=current_user.dashboard.id).all()
        target_catalogue = Catalogue.query.filter_by(id=catalogue_id, user_id=current_user.id).one_or_none()
        if target_catalogue is not None:
            for location in current_locations:
                current_location_obj = {'location': location.id, 'bins': [bin.id for bin in location.bins]}
                locations_choices.append((location.id, location.name))
                allowed_locations_ids.append(location.id)
                for bin in location.bins:
                    allowed_bins_ids.append((bin.id, '{}: {}'.format(location.name, bin.name)))
                    allowed_locations_bins_ids.append(bin.id)
                locations_bins_data.append(current_location_obj)

            for cat_loc in target_catalogue.locations:
                selected_locs_ids.append(cat_loc.location_id)
                for loc_bin in cat_loc.bins:
                    selected_bins_ids.append(loc_bin.bin_id)
            
            categories = [(cat.code, '{}:{}'.format(cat.code, cat.label)) for cat in Category.query.filter_by(dashboard_id=current_user.dashboard.id).all()]

            form = editCatalogueForm(
                sku = target_catalogue.sku,
                product_name = target_catalogue.product_name,
                product_description = target_catalogue.product_description,
                brand = target_catalogue.brand,
                category_code = target_catalogue.category_code,
                quantity = target_catalogue.quantity,
                product_model = target_catalogue.product_model,
                condition = target_catalogue.condition,
                upc = target_catalogue.upc,
                price = target_catalogue.price,
                sale_price = target_catalogue.sale_price,
                warehouse_locations=selected_locs_ids,
                locations_bins=selected_bins_ids # sample as write hello world
                )
            form.warehouse_locations.choices = locations_choices
            form.locations_bins.choices = allowed_bins_ids
            form.category_code.choices = categories

        else:
            flash('Unable to find the selected catalogue, it maybe deleted', 'danger')
            return redirect(url_for('routes.catalogues'))
         
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
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

                if target_catalogue.category_code != form.category_code.data:
                    # code should always be valid by wtforms, incase invalid it will ignored without notifcation
                    target_category = Category.query.filter_by(code=form.category_code.data, dashboard_id=current_user.dashboard.id).first()
                    if target_category:
                        target_catalogue.category_code = target_category.code

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

                # location updates missing
                # CatalogueLocationsBins.query.filter(location_id==cuurent_catalogue_location.location_id,bin_id=current_bin_in)
                user_warehouse_locations_ids = form.warehouse_locations.data
                user_locations_bin_ids = form.locations_bins.data

                # loop of user catalogue locations (handle delete old not used)
                for old_selected_loc_id in selected_locs_ids:
                    # check if old loc id exist in the new array sent after sumbit form else delete it
                    if old_selected_loc_id in user_warehouse_locations_ids:
                        # if user selected same location id, need check if bins of current location in loop still used or user remove it after submit form
                        not_changed_location = CatalogueLocations.query.filter_by(location_id=old_selected_loc_id, catalogue_id=target_catalogue.id).one_or_none()
                        if not_changed_location:                            
                            for old_bin in not_changed_location.bins:
                                # if current user old bin id in the sent list from form conitnue else delete this old bin as user not selected it anymore
                                if old_bin.bin_id in user_locations_bin_ids:
                                    continue
                                else:
                                    old_bin.delete()
                        else:
                            continue
                    else:
                        # delete location if it was old location of catalogue but not sent in the new array
                        removed_loc = CatalogueLocations.query.filter_by(location_id=old_selected_loc_id, catalogue_id=target_catalogue.id).one_or_none()
                        if removed_loc:
                            removed_loc.delete()
               

                # handle new inserts

                # insert all new locations from locations ids list sent from user

                for user_loc_id in user_warehouse_locations_ids:
                    
                    location_exist = CatalogueLocations.query.filter_by(location_id=user_loc_id, catalogue_id=target_catalogue.id).one_or_none()
                    if location_exist is not None:
                        continue
                    else:
                        # user added new loc                        
                        new_inserted_catalogue_loc = CatalogueLocations(location_id=user_loc_id)                        
                        target_catalogue.locations.append(new_inserted_catalogue_loc)
                # after add all transit catalogue locations update catalogue.locations once also handle if exist
                target_catalogue.update()
                
                # handle all new bins inserts (as before it I added all can locations always must found location when query it to append new bin)
                all_catalogue_locations_ids = [catalogue_loc.id for catalogue_loc in target_catalogue.locations]
                                
                for user_bin_id in user_locations_bin_ids:                    
                    # this solve the very hard problem as technquie I used must secured professional and detected as I sent to js all avail bins ids ignoring their parnt locations so must in insert validate and detect the location of the selected bin
                    # this query says is there CatalogueLocationsBins recored that bin id same as bin_id sent from user form, and also its location id for location owned by target catalogue locations (the previous step make sure new locations inserted in beging to target_catalogue before insert bins so new selected location valid must be found)
                    bin_exist = CatalogueLocationsBins.query.filter(CatalogueLocationsBins.bin_id==user_bin_id, CatalogueLocationsBins.location_id.in_(all_catalogue_locations_ids)).first()
                    if bin_exist is not None:
                        # if bin already exist not continue
                        continue
                    else:
                        # here user selected new bin that need to be inserted
                        
                        target_bin = LocationBins.query.filter_by(id=user_bin_id).one_or_none()
                        
                        # get and validate submited bin and confirm its parent dashboardid same as user dashboard_id
                        if target_bin is not None and target_bin.warehouse_location.dashboard_id == current_user.dashboard.id:
                            catalogue_location = CatalogueLocations.query.filter_by(catalogue_id=target_catalogue.id, location_id=target_bin.warehouse_location.id).one_or_none()
                            if catalogue_location is not None and (catalogue_location.warehouse_location.dashboard_id == current_user.dashboard.id):
                                new_bin = CatalogueLocationsBins(bin_id=target_bin.id)                                
                                catalogue_location.bins.append(new_bin)
                                
                                catalogue_location.update()

                flash('Successfully updated catalogue data', 'success')
                success = True
            else:
                # invalid wtforms form sumited in finally this will return render_template to display errors
                success = False
        
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            # update event will done after success = True, so incase error in that event set success to False 
            success = None
            raise e
        

        finally:
            if success == True:                
                # success 
                return redirect(url_for('routes.view_catalogue', catalogue_id=catalogue_id))
            elif success == False:
                # not success due to wtforms render template to display errors
                # very important ntoe locations_bins_data is data sent to js
                return render_template('crud/edit_catalogue.html', form=form, catalogue_id=catalogue_id, locations_bins_data=locations_bins_data)
            else:
                # not success system error, log error and redirect to main page
                flash('Unknown eror, unable to edit catalogue', 'danger')
                return redirect(url_for('routes.catalogues'))


    else:
        # GET Requests
        try:
            return render_template('crud/edit_catalogue.html', form=form, catalogue_id=catalogue_id, locations_bins_data=locations_bins_data)
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
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

                # update dashboard numbers
                updateDashboardListings(current_user.dashboard)
                updateDashboardOrders(db, Order, Listing, current_user.dashboard)
                updateDashboardPurchasesSum(db, Purchase, Listing, current_user.dashboard)
                flash('Successfully deleted Catalogue ID: {}'.format(catalogue_id), 'success')
            else:
                flash('Unable to delete Catalogue, ID: {}'.format(catalogue_id), 'danger')
        else:
            flash('Catalogue not found it maybe deleted, ID: {}'.format(catalogue_id))
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete catalogue', 'danger')
    finally:
        return redirect(url_for('routes.catalogues'))


@routes.route('/catalogues/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_catalogues():
    try:
        form = removeCataloguesForm()
        deleted_ids = []

        if form.validate_on_submit():
            user_catalogues_ids = [str(user_catalogue.id) for user_catalogue in current_user.catalogues]

            selected_catalogues = []
            catalogues_ids_str = str(form.catalogues_ids.data).strip()
            if catalogues_ids_str:
                selected_catalogues = catalogues_ids_str.split(',')

            for selected_catalogue_id in selected_catalogues:
                if selected_catalogue_id in user_catalogues_ids:
                    selected_catalogue = Catalogue.query.filter_by(id=selected_catalogue_id, user_id=current_user.id).one_or_none()
                    if selected_catalogue:
                        deleted_ids.append(selected_catalogue.id)
                        selected_catalogue.delete()
            if len(deleted_ids) > 0:
                updateDashboardListings(current_user.dashboard)
                updateDashboardOrders(db, Order, Listing, current_user.dashboard)
                updateDashboardPurchasesSum(db, Purchase, Listing, current_user.dashboard)
                flash('Successfully deleted Catalogues', 'success')
            else:
                flash('No Changes Detected', 'success')
        else:
            flash('Unable to delete Catalogues', 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete catalogues', 'danger')

    finally:
        return redirect(url_for('routes.catalogues'))


@routes.route('/catalogues/delete_all', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_all_catalogues():
    deleted = 0
    try:
        form = removeAllCataloguesForm()
        
        if form.validate_on_submit():
            system_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
            for selected_catalogue in system_catalogues:
                selected_catalogue.delete()
                deleted +=1

            if deleted > 0:
                updateDashboardListings(current_user.dashboard)
                updateDashboardOrders(db, Order, Listing, current_user.dashboard)
                updateDashboardPurchasesSum(db, Purchase, Listing, current_user.dashboard)
                flash('Successfully deleted Catalogues', 'success')
            else:
                flash('No Changes Detected', 'success')
        else:
            flash('Unable to delete Catalogues', 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete catalogues', 'danger')

    finally:
        return redirect(url_for('routes.catalogues'))


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
                lambda total_pages: [url_for('routes.listings', page=page_index) for page_index in range(1, total_pages+1)],
                limit_parm=session.get('limit', 10)
        )
        user_dashboard_listings = pagination['data']

        delete_listings = removeListingsForm()
        import_offers = importOffersAPIForm()
        setup_bestbuy = SetupBestbuyForm()
        bestbuy_installed = bestbuy_ready()
        return render_template('listings.html', listings=user_dashboard_listings, pagination_btns=pagination['pagination_btns'], delete_listings=delete_listings, import_offers=import_offers, setup_bestbuy=setup_bestbuy,bestbuy_installed=bestbuy_installed)
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
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
                    new_listing = Listing(dashboard_id=user_dashboard.id, catalogue_id=form.catalogue_id.data, active=form.active.data, discount_start_date=form.discount_start_date.data, discount_end_date=form.discount_end_date.data, unit_discount_price=form.unit_discount_price.data, unit_origin_price=form.unit_origin_price.data, quantity_threshold=form.quantity_threshold.data, currency_iso_code=form.currency_iso_code.data, shop_sku=form.shop_sku.data, offer_id=form.offer_id.data, reference=form.reference.data, reference_type=form.reference_type.data)
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
            print('System Error: {}'.format(sys.exc_info()))
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
@vendor_permission.require(http_exception=403)
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
                platforms=listing_platforms,
                active=target_listing.active,
                discount_start_date=target_listing.discount_start_date,
                discount_end_date=target_listing.discount_end_date,
                unit_discount_price=target_listing.unit_discount_price,
                unit_origin_price=target_listing.unit_origin_price,
                quantity_threshold=target_listing.quantity_threshold,
                currency_iso_code=target_listing.currency_iso_code,
                shop_sku=target_listing.shop_sku,
                offer_id=target_listing.offer_id,
                reference=target_listing.reference,
                reference_type=target_listing.reference_type
            )
            user_catalogues = Catalogue.query.filter_by(user_id=current_user.id).all()
            form.catalogue_id.choices = [(catalogue.id, catalogue.product_name) for catalogue in user_catalogues]
            form.platforms.choices = [(platform.id, platform.name) for platform in current_user.dashboard.platforms]
        else:
            flash('Unable to display Edit listing form, target listing maybe removed', 'danger')
            return redirect(url_for('routes.listings'))
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
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

                        if target_listing.active != form.active.data:
                            target_listing.active = form.active.data

                        if target_listing.discount_start_date != form.discount_start_date.data:
                            target_listing.discount_start_date = form.discount_start_date.data

                        if target_listing.discount_end_date != form.discount_end_date.data:
                            target_listing.discount_end_date = form.discount_end_date.data

                        if target_listing.unit_discount_price != form.unit_discount_price.data:
                            target_listing.unit_discount_price = form.unit_discount_price.data

                        if target_listing.unit_origin_price != form.unit_origin_price.data:
                            target_listing.unit_origin_price = form.unit_origin_price.data

                        if target_listing.quantity_threshold != form.quantity_threshold.data:
                            target_listing.quantity_threshold = form.quantity_threshold.data

                        if target_listing.currency_iso_code != form.currency_iso_code.data:
                            target_listing.currency_iso_code = form.currency_iso_code.data

                        if target_listing.shop_sku != form.shop_sku.data:
                            target_listing.shop_sku = form.shop_sku.data

                        if target_listing.offer_id != form.offer_id.data:
                            target_listing.offer_id = form.offer_id.data

                        if target_listing.reference != form.reference.data:
                            target_listing.reference = form.reference.data

                        if target_listing.reference_type != form.reference_type.data:
                            target_listing.reference_type = form.reference_type.data
                        
                        target_listing.catalogue.update()
                        target_listing.update()
                        # listing sync with new catalogue done on catalogue after update (catalogue.update, and sync_listing do same event)
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

                    if target_listing.active != form.active.data:
                        target_listing.active = form.active.data

                    if target_listing.discount_start_date != form.discount_start_date.data:
                        target_listing.discount_start_date = form.discount_start_date.data

                    if target_listing.discount_end_date != form.discount_end_date.data:
                        target_listing.discount_end_date = form.discount_end_date.data

                    if target_listing.unit_discount_price != form.unit_discount_price.data:
                        target_listing.unit_discount_price = form.unit_discount_price.data

                    if target_listing.unit_origin_price != form.unit_origin_price.data:
                        target_listing.unit_origin_price = form.unit_origin_price.data

                    if target_listing.quantity_threshold != form.quantity_threshold.data:
                        target_listing.quantity_threshold = form.quantity_threshold.data

                    if target_listing.currency_iso_code != form.currency_iso_code.data:
                        target_listing.currency_iso_code = form.currency_iso_code.data

                    if target_listing.shop_sku != form.shop_sku.data:
                        target_listing.shop_sku = form.shop_sku.data

                    if target_listing.offer_id != form.offer_id.data:
                        target_listing.offer_id = form.offer_id.data

                    if target_listing.reference != form.reference.data:
                        target_listing.reference = form.reference.data

                    if target_listing.reference_type != form.reference_type.data:
                        target_listing.reference_type = form.reference_type.data

                    target_listing.update()
            else:
                success = False
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
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
                updateDashboardOrders(db, Order, Listing, user_dashboard)
                updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard)
                flash('Successfully deleted Listing ID: {}'.format(listing_id), 'success')
            else:
                flash('Unable to delete Listing, ID: {}'.format(listing_id), 'danger')
        else:
            flash('Listing not found it maybe deleted, ID: {}'.format(listing_id))
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete Listing', 'danger')
    finally:
        return redirect(url_for('routes.listings'))
    

# need after_delete
@routes.route('/listings/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_listings():
    try:
        user_dashboard = current_user.dashboard
        form = removeListingsForm()
        user_listings = db.session.query(
            Listing
        ).join(
            Dashboard, Listing.dashboard_id==Dashboard.id
        ).join(
            User, Dashboard.id==User.dashboard_id
        ).filter(
            User.id == current_user.id,
            Dashboard.id == user_dashboard.id
        ).all()
        
        if form.validate_on_submit():

            user_listings_ids = [str(user_listing.id) for user_listing in user_listings]

            deleted_listings = []
            selected_listings = []
            listings_ids_str = str(form.listings_ids.data).strip()
            if listings_ids_str:
                selected_listings = listings_ids_str.split(',')

            for listing_id in selected_listings:
                if listing_id in user_listings_ids:
                    target_listing = Listing.query.filter_by(id=listing_id, dashboard_id=current_user.dashboard_id).one_or_none()
                    if target_listing:
                        orders_total = sum([order.quantity for order in target_listing.orders])
                        purchases_total = sum([purchase.quantity for purchase in target_listing.purchases])
                        
                        catalogue_quantity = int(target_listing.catalogue.quantity)
                        catalogue_quantity += orders_total
                        catalogue_quantity -= purchases_total
                        catalogue_quantity = catalogue_quantity if catalogue_quantity >= 0  else 0
    
                        target_listing.catalogue.quantity = catalogue_quantity
                        target_listing.delete()                        
                        target_listing.catalogue.update()

                        deleted_listings.append(listing_id)

            # update number of listings one time  after all delete actions
            updateDashboardListings(user_dashboard)
            updateDashboardOrders(db, Order, Listing, user_dashboard)
            updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard)
            flash('Successfully deleted Listings', 'success')
        else:
            flash('Unable to delete Listings', 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete Listing', 'danger')

    finally:
        return redirect(url_for('routes.listings'))

# ! this route called from catalogues page
@routes.route('/listings/multiple_add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def multiple_listing_add():
    try:
        total_created_listings = 0
        form = AddMultipleListingForm()
        # fill choices only
        populate_add_multiple_form(form, Platform, current_user.dashboard.id)
        if form.validate_on_submit():
            catalogue_ids_data = form.catalogue_ids.data
            platforms_selects_data = form.platforms_selects.data

            if len(catalogue_ids_data) == len(platforms_selects_data):
                for i in range(len(catalogue_ids_data)):
                    catalogue_id = catalogue_ids_data[i]
                    platform_ids_list = platforms_selects_data[i]
                    if catalogue_id is not None:
                        current_catalogue = Catalogue.query.filter_by(id=catalogue_id, user_id=current_user.id).one_or_none()
                        if current_catalogue is not None:
                            # current_user.dashboard.id may small heavy repted query but make sure get value on time when insert
                            new_listing = Listing(dashboard_id=current_user.dashboard.id, catalogue_id=current_catalogue.id)
                            # create platforms using append
                            for platform_id in platform_ids_list:
                                # sometimes platform id will be 0 if no platform selected (coerce used always int)
                                if platform_id != 0:
                                    valid_platform = Platform.query.filter_by(dashboard_id=current_user.dashboard.id, id=platform_id).one_or_none()
                                    if valid_platform is not None:
                                        new_platform = ListingPlatform(listing_id=None, platform_id=valid_platform.id)
                                        new_listing.platforms.append(new_platform)
                            
                            new_listing.insert()
                            total_created_listings += 1
                    else:
                        # this error if something happend in Javascript and not filled the catalogue_id input so it must notice by user to report (this developing error)
                        flash("one of catalogues is invalid, unable to create listing for it", "danger")
                
                # set the number of total listings after adding action
                updateDashboardListings(current_user.dashboard)
                flash("Successfully created {} listings".format(total_created_listings))
            else:
                # (protect mylogic from fieldList when it delete one of select feilds if user not select value)
                print("Error in multiple_listing_add catalogues_ids data not equal to platforms_data, one of inputs missing")
                flash("System Error while processing your request, Please report this issue.", 'danger')

        else:
            print('error from multiple_listing_add {}'.format(form.errors))
            flash("Error while processing your request, can not add multiple listing right now.", "danger")
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to add multiple listing', 'danger')
    
    finally:
        return redirect(url_for('routes.catalogues'))


################ -------------------------- Listing Purchases (this purchases based on selected listing from any supplier) -------------------- ################
@routes.route('/listings/<int:listing_id>/purchases/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
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
            print('System Error: {}'.format(sys.exc_info()))
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
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
            print('System Error: {}'.format(sys.exc_info()))
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
                if target_catalogue_quantity >= 0:
                    target_catalogue_quantity = target_catalogue_quantity if target_catalogue_quantity >= 0 else 0
                    target_purchase.listing.catalogue.quantity = target_catalogue_quantity

                    target_purchase.delete()
                    target_purchase.listing.catalogue.update()
                    
                    # update sum of dashboard's purchases
                    updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard)
                    flash('Successfully removed purchase with ID: {}'.format(purchase_id), 'success')
                else:
                    flash('can not remove purchase, note you need to delete one or more orders that created after the deleted purchase, based on it upcoming qunaity', 'danger')
            else:
                # security wtform
                flash('Unable to delete purchase with ID: {} , invalid Data'.format(purchase_id), 'danger')
        else:
            flash('Unable to delete purchase with ID: {} , it not found or delete'.format(purchase_id), 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
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
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
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
                            customer_lastname=form.customer_lastname.data,
                            tax=form.tax.data,
                            shipping=form.shipping.data,
                            shipping_tax=form.shipping_tax.data,
                            commission=form.commission.data,
                            total_cost=form.total_cost.data
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
            print('System Error: {}'.format(sys.exc_info()))
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
@vendor_permission.require(http_exception=403)
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
            customer_lastname=target_order.customer_lastname,
            tax=target_order.tax,
            shipping=target_order.shipping,
            shipping_tax=target_order.shipping_tax,
            commission=target_order.commission,
            total_cost=target_order.total_cost
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
        print('System Error: {}'.format(sys.exc_info()))
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

                            if target_order.tax != form.tax.data:
                                target_order.tax = form.tax.data

                            if target_order.shipping != form.shipping.data:
                                target_order.shipping = form.shipping.data

                            if target_order.shipping_tax != form.shipping_tax.data:
                                target_order.shipping_tax = form.shipping_tax.data

                            if target_order.commission != form.commission.data:
                                target_order.commission = form.commission.data

                            # for more control on previous and new total_cost value, and keep the logic of user can optional set total cost handle total cost here
                            if target_order.total_cost != form.total_cost.data:  
                                target_order.total_cost = form.total_cost.data
                            else:
                                target_order.total_cost = decimal.Decimal(target_order.listing.price) + decimal.Decimal(target_order.tax) + decimal.Decimal(target_order.shipping) + decimal.Decimal(target_order.shipping_tax) + decimal.Decimal(target_order.commission)

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
                        # this variable to calculate total_cost action change as it run in case of total_cost changed or incase shipping, tax, etc changed
                        total_cost_actions = 0
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

                        if target_order.tax != form.tax.data:
                            target_order.tax = form.tax.data
                            actions += 1
                            total_cost_actions += 1

                        if target_order.shipping != form.shipping.data:
                            target_order.shipping = form.shipping.data
                            actions += 1
                            total_cost_actions += 1

                        if target_order.shipping_tax != form.shipping_tax.data:
                            target_order.shipping_tax = form.shipping_tax.data
                            actions += 1
                            total_cost_actions += 1

                        if target_order.commission != form.commission.data:
                            target_order.commission = form.commission.data
                            actions += 1
                            total_cost_actions += 1

                        if target_order.total_cost != form.total_cost.data:
                            # set total cost manual by user
                            target_order.total_cost = form.total_cost.data
                            actions += 1
                        else:
                            if total_cost_actions > 0:
                                # dynamic calcuate total_cost
                                target_order.total_cost = decimal.Decimal(target_order.listing.price) + decimal.Decimal(target_order.tax) + decimal.Decimal(target_order.shipping) + decimal.Decimal(target_order.shipping_tax) + decimal.Decimal(target_order.commission)
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
                            flash('No changes detected', 'success')

                else:
                    flash('Unable to edit order invalid listing provided', 'danger')
                    success = None
            else:
                # wtforms error (render_template)
                success = False
            
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error delete_order: {}'.format(sys.exc_info()))
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
        print('System Error orders: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to display suppliers page', 'danger')
        success = False
    finally:
        if success == True:
            return render_template('suppliers.html', suppliers=suppliers, addform=addform, editform=editform, deleteform=deleteform)
        else:
            return redirect(url_for('routes.index'))


@routes.route('/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to add supplier', 'danger')
        success = False
    
    finally:
        if success == True:
            flash('Successfully created new supplier', 'success')

        return redirect(url_for('routes.suppliers'))


@routes.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete supplier', 'danger')
    finally:
        return redirect(url_for('routes.suppliers'))


################ -------------------------- Supplier Purchases (this purchases based on selected supplier) -------------------- ################
@routes.route('/suppliers/<int:supplier_id>/purchases/<int:purchase_id>', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
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
        print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
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
            print('System Error: {}'.format(sys.exc_info()))
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
@vendor_permission.require(http_exception=403)
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
            print('System Error: {}'.format(sys.exc_info()))
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
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to edit purchase with id: {}'.format(purchase_id), 'danger') 
    finally:
        return redirect(url_for('routes.view_supplier', supplier_id=supplier_id))


#########################################################  Setup  ############################################################
@routes.route('/setup', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def setup():
    try:
        add_platform =  addPlatformForm()
        edit_platform =  editPlatformForm()
        delete_platform =  removePlatformForm()

        add_location =  addLocationForm()
        edit_location =  editLocationForm()
        delete_location =  removeLocationForm()

        add_bin = addBinForm()
        edit_bin = editBinForm()
        delete_bin = removeBinForm()
        

        add_category = addCategoryForm()
        edit_category = editCategoryForm()
        delete_category = removeCategoryForm()

        import_categories = importCategoriesAPIForm()

        setup_bestbuy = SetupBestbuyForm()
    
        # check if user have bestbuy_metas created for remanaing and max per request for current user  (note if global app config numbers changed next time user will try import data will require to setup again the api and auto update the global config number only if required update)
        bestbuy_installed = bestbuy_ready()
        return render_template('setup.html', dashboard=current_user.dashboard, add_platform=add_platform, edit_platform=edit_platform, delete_platform=delete_platform, add_location=add_location, edit_location=edit_location, delete_location=delete_location, add_bin=add_bin, edit_bin=edit_bin, delete_bin=delete_bin, add_category=add_category, edit_category=edit_category, delete_category=delete_category, import_categories=import_categories, setup_bestbuy=setup_bestbuy, bestbuy_installed=bestbuy_installed)
    except Exception as e:
        print("Error in setup page Error: {}".format(sys.exc_info()))
        flash('Unknown error Unable to setup page', 'danger')
        return redirect(url_for('routes.index'))

###########################  Setup platforms  ##############################
@routes.route('/platforms/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_platform():
    try:
        form = addPlatformForm()
        if form.validate_on_submit():
            platform_exist = Platform.query.filter_by(dashboard_id=current_user.dashboard.id, name=form.name_add.data).first()
            if not platform_exist:
                new_platform = Platform(dashboard_id=current_user.dashboard.id, name=form.name_add.data)
                new_platform.insert()
                flash('Successfully Created New Platform', 'success')
            else:
                flash('Can not add platform, platform with same name [{}] already exist'.format(form.name_add.data), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not create platform Please restart page and try again", "danger")
                    continue
                if field == 'name_add':
                    field = 'name'
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown Error unable to create new Platform', 'danger')
    finally:       
        return redirect(url_for('routes.setup'))

@routes.route('/platforms/<int:platform_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def edit_platform(platform_id):
    success = True
    actions = 0
    try:
        form = editPlatformForm()
        if form.validate_on_submit():
            target_platform = Platform.query.filter_by(id=platform_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_platform is not None:
                if target_platform.name != form.name_edit.data:
                    platform_name_exist = Platform.query.filter_by(dashboard_id=current_user.dashboard.id, name=form.name_edit.data).first()
                    if not platform_name_exist:
                        target_platform.name = form.name_edit.data
                        target_platform.update()
                        flash('Successfully edit platform ID:({})'.format(platform_id), 'success')
                    else:
                        flash('Can not edit platform, platform with same name [{}] already exist'.format(form.name_edit.data), 'danger')
                else:
                    flash('No changes Detected.', 'success')
            else:
                flash('platform with ID: ({}) not found or deleted'.format(platform_id), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not edit platform Please restart page and try again", "danger")
                    continue

                if field == 'name_edit':
                    field = 'name'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to edit platform', 'danger')
        success = False
    finally:
        return redirect(url_for('routes.setup'))

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
            flash('Platform not found it maybe deleted, ID: {}'.format(platform_id), 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete platform', 'danger')
    finally:
        return redirect(url_for('routes.setup'))

###########################  Setup Locations  ##############################
@routes.route('/locations/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_location():
    try:
        form = addLocationForm()
        if form.validate_on_submit():
            exist_location = WarehouseLocations.query.filter_by(name=form.location_name_add.data, dashboard_id=current_user.dashboard_id).first()
            if not exist_location:
                new_location = WarehouseLocations(dashboard_id=current_user.dashboard_id, name=form.location_name_add.data)
                new_location.insert()
                flash('Successfully Created New Location', 'success')
            else:
                flash('Can not add location, location with same name [{}] already exist'.format(form.location_name_add.data), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not create location Please restart page and try again", "danger")
                    continue
                if field == 'location_name_add':
                    field = 'name'
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown Error unable to create new Location', 'danger')
    finally:       
        return redirect(url_for('routes.setup'))

@routes.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def edit_location(location_id):
    success = True
    actions = 0
    try:
        form = editLocationForm()
        if form.validate_on_submit():
            target_location = WarehouseLocations.query.filter_by(id=location_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_location is not None:
                if target_location.name != form.location_name_edit.data:
                    exist_location_name = WarehouseLocations.query.filter_by(name=form.location_name_edit.data, dashboard_id=current_user.dashboard.id).first()
                    if not exist_location_name:
                        target_location.name = form.location_name_edit.data
                        target_location.update()
                        flash('Successfully edit location ID:({})'.format(location_id), 'success')
                    else:
                        flash('Can not edit location, location with same name [{}] already exist'.format(form.location_name_edit.data), 'danger')
                else:
                    flash('No changes Detected.', 'success')
            else:
                flash('Location with ID: ({}) not found or deleted'.format(location_id), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not edit location Please restart page and try again", "danger")
                    continue

                if field == 'location_name_edit':
                    field = 'name'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to edit location', 'danger')
        success = False
    finally:
        return redirect(url_for('routes.setup'))

@routes.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_location(location_id):
    try:
        form = removeLocationForm()
        target_location = WarehouseLocations.query.filter_by(id=location_id, dashboard_id=current_user.dashboard.id).one_or_none()
        if target_location is not None:
            if form.validate_on_submit():
                target_location.delete()
                flash('Successfully deleted Location ID: {}'.format(location_id), 'success')
            else:
                flash('Unable to delete Location, ID: {}'.format(location_id), 'danger')
        else:
            flash('Location not found it maybe deleted, ID: {}'.format(location_id), 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete location', 'danger')
    finally:
        return redirect(url_for('routes.setup'))



###########################  Warehouse Locations Bins  ##############################
@routes.route('/locations/<string:location_id>/bins/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_bin(location_id):
    try:
        form = addBinForm()
        if form.validate_on_submit():
            target_location = WarehouseLocations.query.filter_by(dashboard_id=current_user.dashboard.id, id=location_id).one_or_none()
            if target_location is not None:
                # bin name can not duplicated in same location eg, bin1 in location x if duplicated so delete this or add additionl info eg: roof1, first point incase of this name can full descriptive of bin roof 1, spot1 etc instead of spot1
                exist_bin = LocationBins.query.filter_by(name=form.bin_name_add.data, location_id=target_location.id).first()
                if not exist_bin:
                    new_bin = LocationBins(name=form.bin_name_add.data, location_id=target_location.id)
                    new_bin.insert()
                    flash('Successfully Created New Bin', 'success')
                else:
                    flash('Can not add bin, bin with same name [{}] already exist in this warehouse location'.format(form.bin_name_add.data), 'danger')
            else:
                flash('Can not add bin, Location not found it maybe deleted, Location ID: {}'.format(location_id), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not create bin Please restart page and try again", "danger")
                    continue
                if field == 'bin_name_add':
                    field = 'name'
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown Error unable to create new Bin', 'danger')
    finally:       
        return redirect(url_for('routes.setup'))

@routes.route('/locations/<string:location_id>/bins/<string:bin_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def edit_bin(location_id, bin_id):
    success = True
    actions = 0
    try:
        form = editBinForm()
        if form.validate_on_submit():
            target_location = WarehouseLocations.query.filter_by(id=location_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_location is not None:
                target_bin = LocationBins.query.filter_by(id=bin_id, location_id=target_location.id).one_or_none()
                if target_bin is not None:
                    if target_bin.name != form.bin_name_edit.data:
                        exist_bin_name = LocationBins.query.filter_by(name=form.bin_name_edit.data, location_id=target_location.id).first()
                        if not exist_bin_name:
                            target_bin.name = form.bin_name_edit.data
                            target_bin.update()
                            flash('Successfully edit bin', 'success')
                        else:
                            flash('Can not edit bin, bin with same name [{}] already exist'.format(form.bin_name_edit.data), 'danger')
                    else:
                        flash('No changes Detected.', 'success')
                else:
                    flash('can not edit bin, Bin with ID: ({}) not found or deleted'.format(bin_id), 'danger')
            else:
                flash('can not edit bin, Location with ID: ({}) not found or deleted'.format(location_id), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not edit bin Please restart page and try again", "danger")
                    continue

                if field == 'bin_name_edit':
                    field = 'name'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
            success = False
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to edit bin', 'danger')
        success = False
    finally:
        return redirect(url_for('routes.setup'))
    

@routes.route('/locations/<string:location_id>/bins/<string:bin_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_bin(location_id, bin_id):
    try:
        form = removeBinForm()
        if form.validate_on_submit():
            # there are cascade rule in sqlalchemy, and db can not found bin while its location deleted (!!! this high secuirty point)
            target_location = WarehouseLocations.query.filter_by(id=location_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_location is not None:
                target_bin = LocationBins.query.filter_by(id=bin_id, location_id=target_location.id).one_or_none()
                if target_bin is not None:
                    target_bin.delete()
                    flash('Successfully deleted Bin', 'success')
                else:
                    flash('Unable to delete Bin with ID: {}, bin not found it maybe deleted'.format(bin_id), 'danger')
            else:
                flash('Unable to delete Bin, Location with ID: {}, not Found or deleted'.format(location_id), 'danger')
        else:
            flash('Unable to delete Bin, ID: {}'.format(bin_id), 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete bin', 'danger')
    finally:
        return redirect(url_for('routes.setup'))

###########################  Categories  ##############################
@routes.route('/categories/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_category():
    try:
        form = addCategoryForm()
        if form.validate_on_submit():
            # category code and label are uniques for the dashboard (eg you can not have to categories with same title in invetory sidebar and random some here and some here)
            exist_category = db.session.query(Category).filter(and_(Category.dashboard_id==current_user.dashboard_id), or_(Category.code==form.code.data, Category.label==form.label.data)).first()
            if not exist_category:
                new_category = Category(dashboard_id=current_user.dashboard_id, code=form.code.data, label=form.label.data, level=form.level.data, parent_code=form.parent_code.data)
                new_category.insert()
                flash('Successfully Created New Category', 'success')
            else:
                flash('Can not add Category, Category with same code [{}] or label [{}] already exist'.format(form.code.data, form.label.data), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not create category Please restart page and try again", "danger")
                    continue
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown Error unable to create new Category', 'danger')
    finally:
        return redirect(url_for('routes.setup'))

@routes.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def edit_category(category_id):
    actions = 0
    unique_success = True
    unqiues_message = []
    try:
        form = editCategoryForm()
        if form.validate_on_submit():
            target_category = Category.query.filter_by(id=category_id, dashboard_id=current_user.dashboard.id).one_or_none()
            if target_category is not None:
                
                # confirm new code not exist in system only when code updated
                if target_category.code != form.code_edit.data:
                    exist_category_code = Category.query.filter_by(code=form.code_edit.data, dashboard_id=current_user.dashboard.id).first()

                    if not exist_category_code:
                        target_category.code = form.code_edit.data
                        actions += 1
                    else:
                        unique_success = False
                        unqiues_message.append('Category with same code [{}] already exist'.format(form.code_edit.data))
                
                # confirm new label not exist in system only when label updated
                if target_category.label != form.label_edit.data:
                    exist_category_label = Category.query.filter_by(label=form.label_edit.data, dashboard_id=current_user.dashboard.id).first()

                    if not exist_category_label:
                        target_category.label = form.label_edit.data
                        actions += 1
                    else:
                        unique_success = False
                        unqiues_message.append('Category with same label [{}] already exist'.format(form.label_edit.data))

                if target_category.level != form.level_edit.data:
                        target_category.level = form.level_edit.data
                        actions += 1

                if target_category.parent_code != form.parent_code_edit.data:
                        target_category.parent_code = form.parent_code_edit.data
                        actions += 1

                if unique_success == True:
                    if actions > 0:
                        target_category.update()
                        flash('Successfully edit category ID:({})'.format(category_id), 'success')
                    else:
                        flash('No changes Detected.', 'success')
                else:
                    flash('Can not edit Category, {}'.format(','.join(unqiues_message)), 'danger')        
            else:
                flash('Category with ID: ({}) not found or deleted'.format(category_id), 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not edit category Please restart page and try again", "danger")
                    continue

                if field == 'code_edit':
                    field = 'code'
                if field == 'label_edit':
                    field = 'label'
                if field == 'level_edit':
                    field = 'level'
                if field == 'parent_code_edit':
                    field = 'parent_code'

                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to edit category', 'danger')
    finally:
        return redirect(url_for('routes.setup'))

@routes.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_category(category_id):
    try:
        form = removeCategoryForm()
        target_category = Category.query.filter_by(id=category_id, dashboard_id=current_user.dashboard.id).one_or_none()
        if target_category is not None:
            if form.validate_on_submit():
                target_category.delete()
                flash('Successfully deleted Category ID: {}'.format(category_id), 'success')
            else:
                flash('Unable to delete Category, ID: {}'.format(category_id), 'danger')
        else:
            flash('Category not found it maybe deleted, ID: {}'.format(category_id), 'danger')
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('Unknown error unable to delete category', 'danger')
    finally:
        return redirect(url_for('routes.setup'))


"""
@routes.errorhandler(403)
def method_not_allowed(e):
    #session['redirected_from'] = request.url
    return redirect(url_for('auth.logout'))
"""

