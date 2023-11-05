import json
import sys
import os
import requests
import time
import math
from flask import Flask, app, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify, Request, Response, current_app
from .models import *
from .forms import CatalogueExcelForm, ExportDataForm, importCategoriesAPIForm, importOffersAPIForm, SetupBestbuyForm, importOrdersAPIForm,\
generateCatalogueBarcodeForm
from . import vendor_permission, admin_permission, db, excel
from .functions import get_mapped_catalogues_dicts, getTableColumns, getFilterBooleanClauseList, ExportSqlalchemyFilter,\
get_export_data, get_charts, get_excel_rows, get_sheet_row_locations, chunks, apikey_or_none, upload_catalogues, calc_chunks_result, \
bestbuy_ready, get_remaining_requests, get_requests_before_1minute, upload_orders, calc_orders_result, updateDashboardListings,\
updateDashboardOrders, import_orders, order_ids_chunks
from flask_login import login_required, current_user
import flask_excel
import pyexcel
from sqlalchemy import or_, and_, func , asc, desc, text
from datetime import datetime, timedelta
from barcode import EAN13, Code128
import barcode
from barcode.writer import SVGWriter
#from app import excel



main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

@main.route('/import_catalogues_excel', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def import_catalogues_excel():
    success = True
    message = ''
    try:
        catalogue_excel_form = CatalogueExcelForm()
        uploaded_skus = []
        duplicated_skus = []
        invalid_rows = []
        empty_rows = 0
        message = ''
        if catalogue_excel_form.validate_on_submit():
            # try import excel file with diffrent encodings 'utf-8', 'ISO-8859-1', 'latin', 'mac_cyrillic', 'latin1', 'latin2', 'cp1252', 'utf_16' can add more dynamic encodings methods to function
            imported_rows = get_excel_rows(request, 'excel_file')

            # remove empty rows
            excel_rows = []
            for row in imported_rows:
                row_string = ''.join(list(map(lambda item: str(item).strip(), row)))
                if row_string != '':
                    excel_rows.append(row)
                else:
                    empty_rows += 1

            
            mapped_catalogues = get_mapped_catalogues_dicts(excel_rows)


            if mapped_catalogues['success']:

                for row_index in range(len(mapped_catalogues['db_rows'])):

                    db_row = mapped_catalogues['db_rows'][row_index]
                    # get locations name list of current row to insert db warehouse locations if not exist in edit and insert
                    row_locations = get_sheet_row_locations(mapped_catalogues, row_index)
                    
                    # as both provided category_code and category_label in excel file create the category if not exist
                    categoryCode = db_row['category_code']
                    categoryLabel = db_row['category']
                    selected_category = Category.query.filter_by(code=categoryCode, dashboard_id=current_user.dashboard.id).first()
                    # as in final line will insert using **db_row so must have valid column names
                    del db_row['category_code']
                    del db_row['category']
                    if selected_category:
                        db_row['category_id'] = selected_category.id
                    else:
                        # to not end with duplicated label only create category if label and code not exist else leave it None and user update his category manual (as label should not duplicated) (only create new category if label not exist)
                        exist_label = Category.query.filter_by(dashboard_id=current_user.dashboard.id, label=categoryLabel).first()
                        if not exist_label:
                            selected_category = Category(dashboard_id=current_user.dashboard.id, code=categoryCode, label=categoryLabel, level=0, parent_code='')
                            selected_category.insert()
                            db_row['category_id'] = selected_category.id
                    #################################################

                    # condition
                    condition_name = db_row['condition']
                    del db_row['condition']
                    # note condition not allow duplicate for same condition
                    selected_condition = Condition.query.filter_by(dashboard_id=current_user.dashboard.id, name=condition_name).first()
                    if selected_condition:
                        db_row['condition_id'] = selected_condition.id
                    else:
                        new_condition = Condition(dashboard_id=current_user.dashboard.id, name=condition_name)
                        new_condition.insert()
                        db_row['condition_id'] = new_condition.id

                    row_info = "{}|{}".format(row_index+1, db_row['sku'])
                    if db_row['sku'] not in uploaded_skus:
                        try:
                       
                            catalogue_exist = Catalogue.query.filter_by(sku=db_row['sku'], user_id=current_user.id).first()                      
                            if catalogue_exist:

                                # check if new quantity fit current catalogue orders
                                total_orders = 0
                                for catalogue_listing in catalogue_exist.listings:
                                    for order in catalogue_listing.orders:
                                        total_orders += order.quantity

                                
                                valid_quantity = True
                                if db_row['quantity']<total_orders:
                                    flash("Ignored row: {}, the catalogue quantity can not updated, becuase the new quantity exported from excel is less that current catalogue's orders, try update quantity or edit orders of current catalogue".format(str(row_index+1)), "danger")
                                    valid_quantity = False
                                
                                
                                
                                # update only if new quantity is accept current orders of catalogue
                                if valid_quantity:
                                    # daynmic update existing catalogue data with new imported
                                    for key, value in db_row.items():
                                        setattr(catalogue_exist, key, value)
                                        catalogue_exist.update()
                                    
                                    uploaded_skus.append(db_row['sku'])
                                else:
                                    invalid_rows.append(row_info)

                                for sheet_location_name in row_locations:
                                    db_location = WarehouseLocations.query.filter_by(name=sheet_location_name, dashboard_id=current_user.dashboard.id).first()
                                    if not db_location:
                                        db_location = WarehouseLocations(name=sheet_location_name, dashboard_id=current_user.dashboard.id)
                                        db_location.insert()
                                    
                                    catalogue_loc= CatalogueLocations.query.filter_by(catalogue_id=catalogue_exist.id, location_id=db_location.id).first()
                                    if not catalogue_loc:
                                        catalogue_exist.locations.append(CatalogueLocations(location_id=db_location.id))
                                        catalogue_exist.update()
                            else:         
                                newCatalogue = Catalogue(user_id=current_user.id, **db_row)                      
                                

                                uploaded_skus.append(db_row['sku'])

                                # insert catalogue locations if not exist create locations
                                for sheet_location_name in row_locations:
                                    db_location = WarehouseLocations.query.filter_by(name=sheet_location_name, dashboard_id=current_user.dashboard.id).first()
                                    if not db_location:
                                        db_location = WarehouseLocations(name=sheet_location_name, dashboard_id=current_user.dashboard.id)                                        
                                        db_location.insert()
                                    newCatalogue.locations.append(CatalogueLocations(location_id=db_location.id))

                                newCatalogue.insert()
                                
                        except Exception as theerror:
                            # sometimes this error encoding is can not passed to print so ignore issues for it or ignore print it and enogh exc_info
                            # if error it broke the next rows rollback and continue
                            utf8_encoded_error = str(theerror).encode('utf-8', 'ignore')          
                            db.session.rollback()
                            invalid_rows.append(row_info)
                            print('System Error row ignored, import_catalogues_excel: {} , info: {}'.format(utf8_encoded_error, sys.exc_info()))
                            continue
                    else:
                        duplicated_skus.append(str(db_row['product_name']))
                        continue
                    
                # response message with report what data uploaded and what have issues and where issues
                total_ignored = len(duplicated_skus) + len(invalid_rows)
                total_uploaded = len(mapped_catalogues['db_rows']) - total_ignored
                message = 'Successfully Imported Catalogues From Excel File, Total uploaded: {}, Total Ignored: {}, Empty Rows: {}, Duplicateds: [{}], invalids: [{}]'.format(total_uploaded, total_ignored,empty_rows, ','.join(duplicated_skus), ','.join(invalid_rows))
            else:
                message = mapped_catalogues['message']
                success = False
        else:
            message = 'Unable to import excel data, please try again after fix errors:'
            for error in catalogue_excel_form.errors:
                message += ','.join(catalogue_excel_form.errors[error])
            success = False

    except Exception as e:
        # here big issues like db connection or invalid extensions
        print('System Error import_catalogues_excel: {} '.format(sys.exc_info()))
        message = 'Unable to import excel data please try again later'
        success = False
    finally:
        status = 'success' if success else 'danger'
        flash(message, status)
        return redirect(url_for('routes.catalogues'))




# export listing
@main.route('/export_listings', methods=['GET'])
@login_required
@vendor_permission.require()
def listing_export():
    try:
        selected_listings = Listing.query.filter_by(dashboard_id=current_user.dashboard.id).all()
        # this do 2 things, incase there are no data error may raised, also for performance as there no data no need call this heavy function
        if selected_listings:
            column_names = Listing.__table__.columns.keys()
            # column_names also used to exclude names for example you may not need id, so if not provided will not exported
            excel_response = flask_excel.make_response_from_query_sets(selected_listings, column_names, 'csv', file_name='inventory_listings')
            return excel_response
        else:
            flash('There is no data to be exported.', 'warning')
            return redirect(url_for('routes.index'))
    except Exception as e:
        # redirect used to display the flash message incase of error , becuase this GET request and it processed in the same rendered page (so flash can not displayed without refresh)
        print('System Error listing_export: {}'.format(sys.exc_info()))
        flash('Unknown error Your request could not be processed right now, please try again later.', 'danger')
        return redirect(url_for('routes.index'))

@main.route('/reports', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def reports():
    try:
        charts_data = get_charts(db, current_user,
            charts_ids=[
                'top_ordered_products','less_ordered_products',
                'most_purchased_products', 'less_purchased_products',
                'top_purchases_suppliers', 'less_purchases_suppliers',
                'suppliers_purchases', 'orders_yearly_performance',
                'purchases_yearly_performance',
            ]
        )
        export_form = ExportDataForm()  
        return render_template('reports.html', charts_data=charts_data, export_form=export_form)
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('unable to display reports page', 'danger')
        return redirect(url_for('routes.index'))


@main.route('/get_filter_columns', methods=['GET'])
@login_required
@vendor_permission.require()
def get_filter_columns():
    try:
        requested_table = request.args.get('table', '')
        # consts (usefor secuirty) getSqlalchemyColumnByName
        export_sqlalchemy_filter = ExportSqlalchemyFilter()
        # return all or only requested 
        data = export_sqlalchemy_filter.tables_data[requested_table] if requested_table in export_sqlalchemy_filter.tables_data else None
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print('System Error get_filter_columns: {}'.format(sys.exc_info()))
        flash('Unknown error Your request could not be processed right now, please try again later.', 'danger')
        return jsonify({'code': 500, 'message': 'system error'})


# full sqlalchemy dynamic export table data
@main.route('/reports/export', methods=['POST'])
@login_required
@vendor_permission.require()
def reports_export():
    message = ''
    success = True
    excel_response = None
    try:
        export_form = ExportDataForm()
        if export_form.validate_on_submit():
            columns = request.form.getlist('column[]')
            operators = request.form.getlist('operator[]')
            values = request.form.getlist('value[]')
            condition = export_form.condition.data
            table_name = export_form.table_name.data
            data_res = get_export_data(db, flask_excel, current_user.id, table_name, columns, operators, values, condition)
            if data_res and 'success' in data_res and 'excel_response' in data_res and data_res['success'] == True and data_res['excel_response']:
                excel_response = data_res['excel_response']
            else:
                message = data_res['message'] if data_res and 'message' in data_res and data_res['message'] else 'Uknonw error, unable to export your file right now.'
                success = False
        else:
            message = 'Invalid Data'
            success = False
    except Exception as e:
        print('System Error reports_export: {}'.format(sys.exc_info()))
        message = message if message != '' else 'Unknown Error Found While process your request'
        success = False

    finally:
        if success == True and excel_response:
            return excel_response
        else:
            flash(message, 'danger')
            return redirect(url_for('main.reports'))

# this search function works with js search component dynamic for all app searchs
@main.route('/search', methods=['GET', 'POST'])
@login_required
@vendor_permission.require()
def search():
    request_data = request.get_json()
    allowed_search_tables = ['catalogue', 'listing', 'order', 'listing_orders', 'listing_purchases']
    column = request_data['column'] if 'column' in request_data else None
    value = request_data['value'] if 'value' in request_data else None
    target_table = request_data['table'] if 'table' in request_data and request_data['table'] in allowed_search_tables else None
    parent_id = ''
    if 'parent_id' in request_data and request_data['parent_id'] and str(request_data['parent_id']).isnumeric():
        parent_id = request_data['parent_id']

    if column is not None and value is not None and target_table is not None:
        if target_table == 'catalogue':
            direct_search_columns = {
                'id': Catalogue.id,
                'sku': Catalogue.sku,
                'product_name': Catalogue.product_name,
                'price': Catalogue.price,
                'location': WarehouseLocations.name,
                'bin': LocationBins.name
            }
            if column in direct_search_columns:
                search_val = '%{}%'.format(value)
                sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                data = [data_obj.format() for data_obj in db.session.query(Catalogue).outerjoin(
                    CatalogueLocations, Catalogue.id == CatalogueLocations.catalogue_id
                ).outerjoin(
                    WarehouseLocations, CatalogueLocations.location_id == WarehouseLocations.id
                ).outerjoin(
                    CatalogueLocationsBins, CatalogueLocations.id == CatalogueLocationsBins.location_id
                ).outerjoin(
                    LocationBins, CatalogueLocationsBins.bin_id == LocationBins.id
                ).filter(
                    and_(Catalogue.user_id==current_user.id),
                    and_(sqlalchemy_expression)
                ).all()]
                for i in range(len(data)):
                    data[i]['view_catalogue'] = url_for('routes.view_catalogue', catalogue_id=data[i]['id'])
                    data[i]['edit_catalogue'] = url_for('routes.edit_catalogue', catalogue_id=data[i]['id'])
                    data[i]['product_image_url'] = url_for('static', filename='assets/images/{}'.format(data[i]['product_image']))

                return jsonify({'code': 200, 'succeess': True, 'column': column, 'value': value, 'data': data})
            else:
                return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request, unknown search column'})
            
        elif target_table == 'listing':
            direct_search_columns = {
                'id': Listing.id,                
                'sku': Listing.sku,
                'product_name': Listing.product_name,
                'price': Listing.price,
                'sale_price': Listing.sale_price,
                'quantity': Listing.quantity,
                'platform': Platform.name,
                'location': WarehouseLocations.name,
                'bin': LocationBins.name,
                'category': Category.label,
            }
            # eg: lower(listing.product_name) LIKE lower(:product_name_1)
            if column in direct_search_columns:
                search_val = '%{}%'.format(value)
                if value:
                    sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                else:
                    sqlalchemy_expression = or_(direct_search_columns[column] == None, direct_search_columns[column] == '')               
                
                data = [data_obj.format() for data_obj in db.session.query(Listing).join(
                    Catalogue, Listing.catalogue_id == Catalogue.id
                ).outerjoin(
                    Platform, Listing.platform_id == Platform.id
                ).outerjoin(
                    CatalogueLocations, Catalogue.id == CatalogueLocations.catalogue_id
                ).outerjoin(
                    WarehouseLocations, CatalogueLocations.location_id == WarehouseLocations.id
                ).outerjoin(
                    CatalogueLocationsBins, CatalogueLocations.id == CatalogueLocationsBins.location_id
                ).outerjoin(
                    LocationBins, CatalogueLocationsBins.bin_id == LocationBins.id
                ).outerjoin(
                    Category, Catalogue.category_id == Category.id
                ).filter(
                    and_(Catalogue.user_id==current_user.id),
                    and_(sqlalchemy_expression)
                ).all()]

                for i in range(len(data)):
                    data[i]['view_listing'] = url_for('routes.view_listing', listing_id=data[i]['id'])
                    data[i]['edit_listing'] = url_for('routes.edit_listing', listing_id=data[i]['id'])
                    data[i]['listing_image_url'] = url_for('static', filename='assets/images/{}'.format(data[i]['image']))
                return jsonify({'code': 200, 'succeess': True, 'data': data})
            else:
                return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request, unknown search column'})
        elif target_table == 'order':
            direct_search_columns = {
                'id': Order.id,
                'quantity': Order.quantity,
                'date': Order.date,
                'listing_id': Order.listing_id,
                'customer_firstname': Order.customer_firstname,
                'customer_lastname': Order.customer_lastname,
                'tax': Order.tax,
                'shipping': Order.shipping,
                'shipping_tax': Order.shipping_tax,
                'commission': Order.commission,
                'total_cost': Order.total_cost
            }

            if column in direct_search_columns:                
                search_val = '%{}%'.format(value)
                sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                data = [data_obj.format() for data_obj in db.session.query(Order).join(
                    Listing, Order.listing_id == Listing.id
                ).join(
                    Catalogue, Listing.catalogue_id == Catalogue.id
                ).filter(
                    and_(Catalogue.user_id==current_user.id),
                    and_(sqlalchemy_expression)
                )]
                for i in range(len(data)):
                    data[i]['view_order'] = url_for('routes.view_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    data[i]['edit_order'] = url_for('routes.edit_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    data[i]['delete_order'] = url_for('routes.delete_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    data[i]['order_image_url'] = url_for('static', filename='assets/images/default_order.png')

                return jsonify({'code': 200, 'succeess': True, 'data': data})
            else:
                return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request, unknown search column'})
        elif target_table == 'listing_orders':
            direct_search_columns = {
                'id': Order.id,
                'quantity': Order.quantity,
                'first_name': Order.customer_firstname,
                'last_name': Order.customer_lastname,
                'tax': Order.tax,
                'shipping': Order.shipping,
                'shipping_tax': Order.shipping_tax,
                'commission': Order.commission,
                'total_cost': Order.total_cost
            }
            if column in direct_search_columns:
                search_val = '%{}%'.format(value)
                sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                # parent_id must provided in this page and will not effect security as it after user_id
                data = [data_obj.format() for data_obj in db.session.query(Order).join(
                    Listing, Order.listing_id == Listing.id
                ).join(
                    Catalogue, Listing.catalogue_id == Catalogue.id
                ).filter(
                    and_(Catalogue.user_id==current_user.id),
                    and_(Order.listing_id==parent_id),
                    and_(sqlalchemy_expression)
                )]
                for i in range(len(data)):
                    data[i]['view_order'] = url_for('routes.view_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    data[i]['edit_order'] = url_for('routes.edit_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    data[i]['delete_order'] = url_for('routes.delete_order', listing_id=data[i]['listing_id'], order_id=data[i]['id'])
                    
                return jsonify({'code': 200, 'succeess': True, 'data': data})
            else:
                return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request, unknown search column'})
        elif target_table == 'listing_purchases':
            direct_search_columns = {
                'id': Purchase.id,
                'quantity': Purchase.quantity,
                'supplier_name': Supplier.name
            }
            if column in direct_search_columns:
                search_val = '%{}%'.format(value)
                sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                # this way force only display search for valid purchases that has catalogue, incase some data not has catalouge for any reason this will not diplsayed but user not need invalid data and it must not happend incase only db edit
                data = [data_obj.format() for data_obj in db.session.query(Purchase).join(
                    Listing, Purchase.listing_id == Listing.id
                ).join(
                    Catalogue, Listing.catalogue_id == Catalogue.id
                ).outerjoin(
                    Supplier, Purchase.supplier_id == Supplier.id
                ).filter(
                    and_(Catalogue.user_id==current_user.id),
                    and_(Purchase.listing_id==parent_id),
                    and_(sqlalchemy_expression)
                )]
                for i in range(len(data)):
                    data[i]['view_purchase_listing'] = url_for('routes.view_purchase_listing', listing_id=data[i]['listing_id'], purchase_id=data[i]['id'])
                    data[i]['edit_purchase_listing'] = url_for('routes.edit_purchase_listing', listing_id=data[i]['listing_id'], purchase_id=data[i]['id'])
                    data[i]['delete_purchase_listing'] = url_for('routes.delete_purchase_listing', listing_id=data[i]['listing_id'], purchase_id=data[i]['id'])
                return jsonify({'code': 200, 'succeess': True, 'data': data})
            else:
                return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request, unknown search column'})
        else:
            return jsonify({'code': 404, 'succeess': False, 'message': 'invalid search, unknown table'})
    else:
        return jsonify({'code': 400, 'succeess': False, 'message': 'invalid search request'})


# store limit in session with ajax
# this search function works with js search component dynamic for all app searchs
@main.route('/save_limit', methods=['POST'])
@login_required
@vendor_permission.require()
def savelimit():
    try:
        # confirm both side client and server number will set in session is valid integer
        limit = request.json.get('limit', 10)
        limit = limit if isinstance(limit, int) else 10
        session['limit'] = limit
        code = 200
    except Exception as e:
        print('System error in savelimit, info: {}'.format(sys.exc_info()))
        code = 500
    finally:
        return jsonify({'code': code})


# setup bestbuy api connection, not save token only set metas for max and remaning user requests
@main.route('/bestbuy_setup', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def setup_bestbuy():
    redirects = {'setup': url_for('routes.setup'), 'listings': url_for('routes.listings'), 'orders': url_for('routes.orders')}
    redirect_url = url_for('routes.setup')
    message = ''
    status = 'danger'
    # global values of meta can set in db or config or here direct
    remaining_requests = str(current_app.config.get('BESTBUY_RAMAINING'))
    request_max = str(current_app.config.get('BESTBUY_MAX'))
    try:
        #a750a16c-054e-407c-9825-3da7d4b2a9c1
        form = SetupBestbuyForm()        
        if form.redirect.data in redirects:
            redirect_url = redirects[form.redirect.data]
        
        if form.validate_on_submit():
            change_detected = False
            update_detected = False

            # create only not exist bestbuy required metas
            bestbuy_remaining_requests = UserMeta.query.filter_by(key='bestbuy_remaining_requests', user_id=current_user.id).first()
            if bestbuy_remaining_requests:
                # if global variable value changed update existing meta
                if bestbuy_remaining_requests.value != remaining_requests:
                    bestbuy_remaining_requests.value = remaining_requests
                    bestbuy_remaining_requests.update()
                    update_detected = True
            else:
                # if meta not exist with key bestbuy_remaining_requests create it with current global value for remaining_requests
                new_meta = UserMeta(key='bestbuy_remaining_requests', user_id=current_user.id, value=remaining_requests)
                current_user.meta.append(new_meta)
                change_detected = True

            bestbuy_request_max = UserMeta.query.filter_by(key='bestbuy_request_max', user_id=current_user.id).first()
            if bestbuy_request_max:
                # if global max changed update the metas
                if bestbuy_request_max.value != request_max:
                    bestbuy_request_max.value = request_max
                    bestbuy_request_max.update()
                    update_detected = True
            else:
                new_meta = UserMeta(key='bestbuy_request_max', user_id=current_user.id, value=request_max)
                current_user.meta.append(new_meta)
                change_detected = True

            if change_detected:
                current_user.update()
                updated_msg = 'and updated ' if update_detected else ''
                message = f'successfully setup bestbuy {updated_msg}API settings, you can now use bestbuy API to import data.'
            elif update_detected:
                message = 'successfully updated bestbuy API settings, you can now use bestbuy API to import data.'
            else:
                message = 'BestBuy API Already configured Before.'
                
            status = 'success'
        else:
            message = 'Unable to setup please try again'
            return redirect(redirect_url)
    except:
        print('System error in setup_bestbuy, info: {}'.format(sys.exc_info()))
        message = 'System error Unable to setup bestbuy API right now please try again later.'

    finally:
        flash(message, status)
        return redirect(redirect_url)

@main.route('/get_remaining_requests', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def get_remaining_requests_func():
    return str(get_remaining_requests())

# import categories using API (user securly provide API key)  (this main API endpoint for categories, so incase you first imported catalogues and it created the categories for you, any time you can back here to update the categories created (eg: to setup level and parent code, or incase in future label of category changed so this endpoint will handle the update also for you)) best practice if started with offers import, come here and import categories to have level and parent code if
@main.route('/import_categories_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def api_import_categories():
    total_imported = 0
    total_updated = 0
    total_notchanged = 0
    try:
        tomorrow_str = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)).strftime('%Y-%m-%d')
        #a750a16c-054e-407c-9825-3da7d4b2a9c1
        form = importCategoriesAPIForm()
        if form.validate_on_submit():
            bestbuy_instaled = bestbuy_ready()
            if bestbuy_instaled:
                # for better performance in categories as it not include time.sleep like chunks requests in offer, uses get_requests_before_1minute to reject request if made 1 request or more 5 seconds or less ago
                requests_within_1minute = get_requests_before_1minute()
                if requests_within_1minute[0] == 0:
                    user_remaining_requests = get_remaining_requests()
                    # secure apikey (regex validate apikey before request)
                    apikey = apikey_or_none(form.api_key.data)
                    req_url = 'https://marketplace.bestbuy.ca/api/hierarchies'
                    if apikey is not None:
                        if user_remaining_requests > 0:
                            headers = {'Authorization': apikey}
                            r = requests.get(req_url, headers=headers)
                            new_request_meta = UserMeta(key='bestbuy_request', user_id=current_user.id, value=r.status_code)
                            new_request_meta.insert()
                            if r.status_code == 200:
                                data = json.loads(r.content)
                                if 'hierarchies' in data:
                                    # start of valid import
                                    hierarchies = data['hierarchies']
                                    total_data = len(hierarchies)
                                    # limit of add_all is 50000 incase of data returned more than 50k split them
                                    for hierarchy in hierarchies:
                                        if 'code' in hierarchy and 'label' in hierarchy and 'level' in hierarchy and 'parent_code' in hierarchy:
                                            # import unique code and labels categories only, add_all was faster but no check
                                            category_exist = db.session.query(Category).filter(Category.dashboard_id==current_user.dashboard.id, Category.code==hierarchy['code']).first()
                                            if category_exist:
                                                require_update = False
                                                if category_exist.label != hierarchy['label']:
                                                    category_exist.label = hierarchy['label']
                                                    require_update = True

                                                if category_exist.level != hierarchy['level']:
                                                    category_exist.level = hierarchy['level']
                                                    require_update = True

                                                if category_exist.parent_code != hierarchy['parent_code']:
                                                    category_exist.parent_code = hierarchy['parent_code']
                                                    require_update = True

                                                if require_update:
                                                    category_exist.update()
                                                    total_updated += 1
                                                else:
                                                    total_notchanged += 1
                                            else:
                                                new_code = Category(dashboard_id=current_user.dashboard.id, code=hierarchy['code'], label=hierarchy['label'], level=hierarchy['level'], parent_code=hierarchy['parent_code'])
                                                new_code.insert()
                                                total_imported += 1
                                    flash('Succsefully imported {total_imported} of categories from total: {total_data} categories, Updated {total_updated} of categories from total: {total_data} categories, and not changed Categories: {not_changed}'.format(total_imported=total_imported,total_data=total_data,total_updated=total_updated,not_changed=total_notchanged), 'success')
                                else:
                                    flash('API Changed, Could not process your request right now', 'danger')
                            elif r.status_code == 401:
                                flash('Invalid API key, the API refused to authorize your request.', 'danger')
                            else:
                                flash('The API cannot process your request now, please try again later, if the problem is not resolved, please report to us.', 'danger')
                        else:
                            flash(f'You Can not make more requests right now, please wait for {tomorrow_str} and try again', 'warning')

                    else:
                        flash('Invalid API Key.', 'danger')
                else:
                    flash('Please wait {} seconds to import again'.format(requests_within_1minute[1]), 'danger')
            else:
                flash('Please update or configure bestbuy API settings first, by clicking on same import button clicked.', 'warning')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not import categories Please restart page and try again", "danger")
                    continue
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')   
    except Exception as e:
        flash('System Error, Could not process your request right now', 'danger')
        print('System error in api_import_categories, info: {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('routes.setup'))

# remaning listing info report
# import categories using API (user securly provide API key)
@main.route('/import_offers_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def api_offers_import():
    results = []
    try:
        tomorrow_str = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)).strftime('%Y-%m-%d')
        # a750a16c-054e-407c-9825-3da7d4b2a9c1
        form = importOffersAPIForm()
        if form.validate_on_submit():
            bestbuy_instaled = bestbuy_ready()
            bestbuy_request_max = UserMeta.query.filter_by(key='bestbuy_request_max', user_id=current_user.id).first()
            if bestbuy_instaled and bestbuy_request_max is not None:
                bestbuy_request_max = int(bestbuy_request_max.value)
                user_remaining_requests = get_remaining_requests()
                request_max = bestbuy_request_max if bestbuy_request_max <= 100 and bestbuy_request_max >= 0 else 100
                # secure apikey
                apikey = apikey_or_none(form.api_key.data)
                req_url = f'https://marketplace.bestbuy.ca/api/offers?max={request_max}'
                if apikey is not None:
                    # confirm user have remaning requests from db in the current time
                    if user_remaining_requests > 0:
                        headers = {'Authorization': apikey}
                        chunks_errors = []
                        successful = 0
                        # better send small test request, to confirm API key, and API comunication
                        r = requests.get(req_url, headers=headers)

                        new_request_meta = UserMeta(key='bestbuy_request', user_id=current_user.id, value=r.status_code)
                        new_request_meta.insert()
                        # 400/100 = 40, range(0,40)
                        # this is like status test request (API endpoint health check before start multiple requests, with time.sleep(10) per each, incase invalid api key user will wait alot if not tested)
                        if r.status_code == 200:                    
                            response_content = json.loads(r.content) if r and r.content else None                    
                            # get total count of requests
                            total_count = None
                            remaing_data = 0
                            try:
                                remaing_data = int(int(response_content['total_count']) - request_max) if int(response_content['total_count']) >= request_max else 0
                                total_count = math.ceil(remaing_data/request_max)
                            except:
                                print("API not sending total_count, or sending invalid int")
                                pass

                            # if total_count of required requests to imported less or equal to user_remaining_requests allow else make him send only requests with count of his reamning not block all
                            total_requests = total_count if total_count and user_remaining_requests >= total_count else user_remaining_requests
                            current_upload_result = upload_catalogues(json.loads(r.content)['offers'], current_user)
                            results.append(current_upload_result)

                            # static-dynamicly get user_remianing requests note nothing math or substrict done - to detect requests and that sure later incase in init file changed the remaning requests it still calcuate will and dynamic calcuate by dates of now requests vs the static number change by dev or admin bestbuy_remaining_requests (static-dynamic)
                            user_remaining_requests = get_remaining_requests()
                            if user_remaining_requests > 0:
                                # start loop to add cooldown sleep between requests and get all data
                                for i in range(0,total_requests):
                                    current_max = (i+2) * request_max
                                    # wait 5 seconds between each request
                                    time.sleep(5)
                                    try:
                                        # chunks remaning
                                        next_url = r.links.get('next').get('url') if r.links and r.links.get('next', None) and r.links.get('next').get('url', None) else None
                                        if next_url:
                                            r = requests.get(next_url, headers=headers)
                                            new_request_meta = UserMeta(key='bestbuy_request', user_id=current_user.id, value=r.status_code)
                                            new_request_meta.insert()

                                            if r.status_code == 200:
                                                if remaing_data > 0:
                                                    remaing_data = remaing_data - request_max if (remaing_data - request_max) > 0 else 0
                                                current_upload_result = upload_catalogues(json.loads(r.content)['offers'], current_user)
                                                results.append(current_upload_result)
                                                successful += 1

                                    except Exception as e:
                                        print("Error in one of chunks at api_offers_import: {}".format(sys.exc_info()))
                                        chunks_errors.append("Some Of data Could not be imported, Error occured in request number {}: start from {} to {}".format((i+2), current_max, (current_max-request_max)))

                            else:
                                chunks_errors.append("Could not import the Remaining {} data at the moment, you exceded the limit of requests, not all data imported".format(remaing_data))

                            updateDashboardListings(current_user.dashboard)                               
                            total_result = calc_chunks_result(results)
                            str_part1 = 'Succsefully imported {total_imported} of Catalogues from total: {total} Catalogues, Updated {total_updated} of catalogues from total: {total} catalogues, and {not_changed} not changed Catalogues'.format(total_imported=total_result['uploaded'],total=total_result['total'],total_updated=total_result['updated'],not_changed=total_result['not_changed'])
                            str_part2 = '--- AND imported {total_imported} of Listings from total: {total} Listings, Updated {total_updated} of listings from total: {total} listings,and created {new_categories} new Categories'.format(total_imported=total_result['luploaded'],total=total_result['total'],total_updated=total_result['lupdated'],not_changed=total_result['lnot_changed'], new_categories=total_result['new_categories'])
                            if len(chunks_errors) == 0:
                                flash('Succsefully Imported All Data, Import Report: {}{}'.format(str_part1, str_part2), 'success')
                            elif len(chunks_errors) > 0:
                                # one or more request blocked, but not all, inform user which requests have issue (API later automatic will handle when import data, but notify user with his stuiation)
                                flash('Succsefully Imported some of Data, one or more requests failed, Import Report: {}{}'.format(str_part1, str_part2), 'success')

                                for chunk_error in chunks_errors:
                                    flash(chunk_error, 'danger')
                            else:
                                flash('Unable to connect to the API right now to get Data, please try again later.', 'danger')

                        elif r.status_code == 401:
                            flash('Invalid API key, the API refused to authorize your request.', 'danger')
                        else:
                            flash('The API cannot process your request now, please try again later, if the problem is not resolved, please report to us.', 'danger')
                    else:
                        flash(f'You Can not make more requests right now, please wait for {tomorrow_str} and try again', 'warning')
                else:
                    flash('Invalid API Key.', 'danger')
            else:
                flash('Please update or configure bestbuy API settings first, by clicking on same import button clicked.', 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not import offers Please restart page and try again", "danger")
                    continue
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
    except Exception as e:
        flash('System Error, Could not process your request right now', 'danger')
        print('System error in api_offers_import, info: {}'.format(sys.exc_info()))
        raise e

    finally:
        return redirect(url_for('routes.listings'))


    
@main.route('/import_orders_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def api_import_orders():
    results = []
    try:
        
        tomorrow_str = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)).strftime('%Y-%m-%d')
        form = importOrdersAPIForm()
        if form.validate_on_submit():
            bestbuy_instaled = bestbuy_ready()
            bestbuy_request_max = UserMeta.query.filter_by(key='bestbuy_request_max', user_id=current_user.id).first()
            if bestbuy_instaled and bestbuy_request_max is not None:
                user_remaining_requests = get_remaining_requests()
                bestbuy_request_max = int(bestbuy_request_max.value)                
                request_max = bestbuy_request_max if bestbuy_request_max <= 100 and bestbuy_request_max >= 0 else 100

                # created date sent by user
                start_date_parameter = '&start_date={}'.format(form.date_from.data.strftime("%Y-%m-%dT%H:%M:%SZ")) if form.date_from.data else ''
                # secure api key
                apikey = apikey_or_none(form.api_key.data)
                req_url = f'https://marketplace.bestbuy.ca/api/orders?max={request_max}{start_date_parameter}'
                if apikey:
                    if not form.order_ids.data:
                        if user_remaining_requests > 0:
                            headers = {'Authorization': apikey}
                            chunks_errors = []
                            successful = 0

                            r = requests.get(req_url, headers=headers)
                            new_request_meta = UserMeta(key='bestbuy_request', user_id=current_user.id, value=r.status_code)
                            new_request_meta.insert()
                            
                            if r.status_code == 200:
    
                                response_content = json.loads(r.content) if r and r.content else None
                                # get total count of requests
                                total_count = None
                                remaing_data = 0
                                try:
                                    remaing_data = int(int(response_content['total_count']) - request_max) if int(response_content['total_count']) >= request_max else 0
                                    total_count = math.ceil(remaing_data/request_max)
                                except:
                                    print("API not sending total_count, or sending invalid int")
                                    pass
    
                                # if total_count of required requests to imported less or equal to user_remaining_requests allow else make him send only requests with count of his reamning not block all
                                total_requests = total_count if total_count is not None and user_remaining_requests >= total_count else user_remaining_requests
                                current_upload_result0 = upload_orders(json.loads(r.content)['orders'], current_user, db)
                                results.append(current_upload_result0)
                                user_remaining_requests = get_remaining_requests()
                                if user_remaining_requests > 0:
                                    # start loop to add cooldown sleep between requests and get all data
                                    for i in range(0,total_requests):
                                        current_max = (i+2) * request_max
                                        # wait 5 seconds between each request
                                        time.sleep(5)
                                        try:
                                            # chunks remaning
                                            next_url = r.links.get('next').get('url') if r.links and r.links.get('next', None) and r.links.get('next').get('url', None) else None
                                            # even if the calcuation goes wrong for any reson this if acts like while next_url and will ignore looping and not send additional requests not needed
                                            if next_url:
                                                r = requests.get(next_url, headers=headers)
                                                new_request_meta = UserMeta(key='bestbuy_request', user_id=current_user.id, value=r.status_code)
                                                new_request_meta.insert()
    
                                                if r.status_code == 200:
                                                    if remaing_data > 0:
                                                        remaing_data = remaing_data - request_max if (remaing_data - request_max) > 0 else 0
                                                    current_upload_result = upload_orders(json.loads(r.content)['orders'], current_user, db)
                                                    results.append(current_upload_result)
                                                    successful += 1
    
                                        except Exception as e:
                                            print("Error in one of chunks at api_import_orders: {}".format(sys.exc_info()))
                                            chunks_errors.append("Some Of data Could not be imported, Error occured in request number {}: start from {} to {}".format((i+2), current_max, (current_max-request_max)))
    
                                else:
                                    chunks_errors.append("Could not import the Remaining {} data at the moment, you exceded the limit of requests, not all data imported".format(remaing_data))
                            
                                result = calc_orders_result(results)
                                str_part1 = 'total uploaded: {}, total updated: {}, total not changed: {}, total invalid quantity: {}, total missing listing: {}, total upload error: {}'.format(result['total_uploaded'], result['total_updated'], result['not_changed'], result['total_invalid'], result['total_missing'], result['total_errors'])
                                total_data = result['total_uploaded'] + result['total_updated'] + result['not_changed'] + result['total_invalid'] + result['total_missing'] + result['total_errors']


                                if len(chunks_errors) == 0:
                                    flash('Succsefully Imported All Data from total ({}), Import Report: {}'.format(total_data, str_part1), 'success')
                                else:
                                    # one or more request blocked, but not all, inform user which requests have issue (API later automatic will handle when import data, but notify user with his stuiation)
                                    flash('Succsefully Imported some of Data from total ({}), one or more requests failed, Import Report: {}'.format(total_data, str_part1), 'success')
                                    for chunk_error in chunks_errors:
                                        flash(chunk_error, 'danger')
    
                                # update dashboard orders totals after all inserts
                                updateDashboardOrders(db, current_user.dashboard)
    
                                # handle ignored values
                                #if len(result['invalid_quantity']) > 0 or len(result['missing_listing']) > 0 or len(result['errors']) > 0:
                                session['import_orders_report'] = 'Report of ignored data, you may need this ids to able to get the same data later from API, invalid quantity ids: [{}], missing listing ids: [{}], errors ids: [{}]'.format(','.join(result['invalid_quantity']), ','.join(result['missing_listing']), ','.join(result['errors']))
    
                            elif r.status_code == 401:
                                flash('Invalid API key, the API refused to authorize your request.', 'danger')
                            else:
                                flash('The API cannot process your request now, please try again later, if the problem is not resolved, please report to us.', 'danger')
                        else:
                            flash(f'You Can not make more requests right now, please wait for {tomorrow_str} and try again', 'warning')
                    else:
                        order_ids = form.order_ids.data.split(",")
                        speacfic_orders = import_orders(db, apikey, order_ids, bestbuy_request_max, user_remaining_requests, tomorrow_str)

                        if not speacfic_orders['error']:
                            results = speacfic_orders['results']
                            chunks_errors = speacfic_orders['chunks_errors']

                            # import speacfic order ids
                            result = calc_orders_result(results)
                            str_part1 = 'total uploaded: {}, total updated: {}, total not changed: {}, total invalid quantity: {}, total missing listing: {}, total upload error: {}'.format(result['total_uploaded'], result['total_updated'], result['not_changed'], result['total_invalid'], result['total_missing'], result['total_errors'])

                            total_data = result['total_uploaded'] + result['total_updated'] + result['not_changed'] + result['total_invalid'] + result['total_missing'] + result['total_errors']

                            if len(chunks_errors) == 0:
                                flash('Succsefully Imported All Data from total ({}), Import Report: {}'.format(total_data, str_part1), 'success')
                            else:
                                # one or more request blocked, but not all, inform user which requests have issue (API later automatic will handle when import data, but notify user with his stuiation)
                                flash('Succsefully Imported some of Data from total ({}), one or more requests failed, Import Report: {}'.format(total_data, str_part1), 'success')
                                for chunk_error in chunks_errors:
                                    flash(chunk_error, 'danger')
    
                            # update dashboard orders totals after all inserts
                            updateDashboardOrders(db, current_user.dashboard)
    
                            # handle ignored values
                            #if len(result['invalid_quantity']) > 0 or len(result['missing_listing']) > 0 or len(result['errors']) > 0:
                            session['import_orders_report'] = 'Report of ignored data, you may need this ids to able to get the same data later from API, invalid quantity ids: [{}], missing listing ids: [{}], errors ids: [{}]'.format(','.join(result['invalid_quantity']), ','.join(result['missing_listing']), ','.join(result['errors']))
                        else:
                            flash(speacfic_orders['error'], 'danger')
                else:
                    flash('Invalid API Key.', 'danger')
            else:
                flash('Please update or configure bestbuy API settings first, by clicking on same import button clicked.', 'danger')
        else:
            for field, errors in form.errors.items():
                if field == 'csrf_token':
                    flash("Error can not import orders Please restart page and try again", "danger")
                    continue
                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
    except Exception as e:
        flash('System Error, Could not process your request right now', 'danger')
        print('System error in api_import_orders, info: {}'.format(sys.exc_info()))

    finally:
        return redirect(url_for('routes.orders'))

def generate_redirect(redirect_url):
    try:
        allowed_redirects = {
            'view_catalogue': lambda catalogue_id : url_for('routes.view_catalogue', catalogue_id=catalogue_id)
        }
        if redirect_url and ',' in redirect_url:
            redirect_parts = redirect_url.split(',')
            if redirect_parts[0] in allowed_redirects and redirect_parts[1]:
                safe_url = allowed_redirects[redirect_parts[0]](redirect_parts[1])
        return safe_url
    except:
        return url_for('routes.index')


# this end point for catalogue if diffrent class use diffrent endpoint
@main.route('/generate_barcode/<int:catalogue_id>', methods=['POST', 'GET'])
@login_required
@vendor_permission.require()
def generate_barcode(catalogue_id):
    try:
        form = generateCatalogueBarcodeForm()
        if form.validate_on_submit():
            selected_catalogue = Catalogue.query.filter_by(id=catalogue_id, user_id=current_user.id).one_or_none()
            if selected_catalogue is not None:
                barcode_name = 'catalogue_{}_{}.svg'.format(selected_catalogue.id, current_user.id)
                barcode_path = os.path.join(current_app.root_path, 'static', 'uploads', 'barcodes', barcode_name)
                with open(barcode_path, "wb") as f:
                    Code128(u'{}'.format(form.data.data), writer=SVGWriter()).write(f)
                selected_catalogue.barcode = barcode_name
                selected_catalogue.update()
                flash('Successfully created barcode', 'success')
            else:
                flash('Unable to create barcode, catalogue not found', 'danger')
        else:
            for field, errors in form.errors:
                if field == 'csrf_token':
                    flash('Unable to create barcode please refresh page and try again', 'warning')
                else:
                    flash('{}:{}'.format(field, ','.join(errors)), 'danger')
    except Exception as e:
        flash('Unknown error Unable to create barcode', 'danger')
    finally:
        return redirect(url_for('routes.view_catalogue', catalogue_id=catalogue_id))


