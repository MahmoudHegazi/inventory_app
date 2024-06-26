import json
import sys
import os
import requests
import time
import re
import math
import cryptocode
from flask import Flask, app, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify, Request, Response, current_app
from .models import *
from .forms import *
from . import vendor_permission, admin_permission, inventory_admin_permission, app_permissions, db, excel, bcrypt
from .functions import get_mapped_catalogues_dicts, getTableColumns, getFilterBooleanClauseList, ExportSqlalchemyFilter,\
get_export_data, get_charts, get_excel_rows, chunks, apikey_or_none, upload_catalogues, calc_chunks_result, \
bestbuy_ready, get_remaining_requests, get_requests_before_1minute, upload_orders, calc_orders_result, updateDashboardListings,\
updateDashboardOrders, import_orders, order_ids_chunks, download_order_image, get_errors_message, generate_ourapi_key,\
get_activity_dateobjs, complete_activity_date, get_charts_data, get_hashed_sqlalchemycol, ExportSqlalchemyFilter, get_unencrypted_cols,\
get_sqlalchemy_filters, get_ordered_dicts, handle_crud_action, user_have_permissions, inv, insert_locs_bins, get_logs_queries,\
create_log
from flask_login import login_required, current_user
import flask_excel
import pyexcel
from sqlalchemy import or_, and_, func , asc, desc, text, not_
from datetime import datetime, timedelta
from barcode import EAN13, Code128
import barcode
from barcode.writer import SVGWriter
from dateutil.relativedelta import *
from sqlalchemy import select

#from app import excel

main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

@main.route('/import_catalogues_excel', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def import_catalogues_excel():
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
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
                #return str(mapped_catalogues)

                if mapped_catalogues['success']:
                    # generate static system category code (get last number part of category code identifer) 
                    category_incrementer = max([0, *list(filter(lambda x:x, [int(code[0].replace('INV_', '').strip()) if re.match("^INV_\d{1,}$", code[0]) else False for code in db.session.query(Category.code).all()]))])


                    for row_index in range(len(mapped_catalogues['db_rows'])):
                        
                        db_row = mapped_catalogues['db_rows'][row_index]
                        
                        # as both provided category_code and category_label in excel file create the category if not exist
                        categoryCode = None
                        categoryLabel = None
                        location = None
                        bin = None
                        if 'category_code' in db_row:
                            categoryCode = db_row['category_code']
                            del db_row['category_code']
                        else:
                            # category code not provided
                            category_incrementer += 1
                            categoryCode = 'INV_{}'.format(category_incrementer)
                        
                        if 'category' in db_row:
                            categoryLabel = db_row['category']
                            del db_row['category']

                        if 'location' in db_row and db_row['location']:
                            location = db_row['location']
                            del db_row['location']
                        if 'bin' in db_row and db_row['bin']:
                            bin = db_row['bin']
                            del db_row['bin']


                        if categoryCode is not None and categoryLabel is not None:
                            selected_category = inv(Category.query.filter_by(code=categoryCode), User.dashboard_id, Category.dashboard_id).first()
                            # as in final line will insert using **db_row so must have valid column names
                            if selected_category:
                                db_row['category_id'] = selected_category.id
                            else:
                                # to not end with duplicated label only create category if label and code not exist else leave it None and user update his category manual (as label should not duplicated) (only create new category if label not exist)
                                exist_label = inv(Category.query.filter_by(label=categoryLabel), User.dashboard_id, Category.dashboard_id).first()
                                if not exist_label:
                                    selected_category = Category(dashboard_id=current_user.dashboard.id, code=categoryCode, label=categoryLabel, level=0, parent_code='')
                                    selected_category.insert()
                                    db_row['category_id'] = selected_category.id


                        # condition
                        if 'condition' in db_row:
                            condition_name = db_row['condition']
                            del db_row['condition']
                            # note condition not allow duplicate for same condition
                            selected_condition = inv(Condition.query.filter_by(name=condition_name), User.dashboard_id, Condition.dashboard_id).first()
                            if selected_condition:
                                db_row['condition_id'] = selected_condition.id
                            else:
                                new_condition = Condition(dashboard_id=current_user.dashboard.id, name=condition_name)
                                new_condition.insert()
                                db_row['condition_id'] = new_condition.id

                        row_info = "{}|{}".format(row_index+1, db_row['sku'])
                        if db_row['sku'] not in uploaded_skus:
                            try:
                                
                                catalogue_exist = inv(Catalogue.query.filter_by(sku=db_row['sku']), User.id, Catalogue.user_id).first()                      
                                if catalogue_exist:

                                    # check if new quantity fit current catalogue orders
                                    total_orders = 0
                                    for catalogue_listing in catalogue_exist.listings:
                                        for order in catalogue_listing.orders:
                                            total_orders += order.quantity

                                    
                                    valid_quantity = True
                                    if 'quantity' in db_row and db_row['quantity']<total_orders:
                                        flash("Ignored row: {}, the catalogue quantity can not updated, becuase the new quantity exported from excel is less that current catalogue's orders, try update quantity or edit orders of current catalogue".format(str(row_index+1)), "danger")
                                        valid_quantity = False
                                    
                                    
                                    
                                    # update only if new quantity is accept current orders of catalogue
                                    if valid_quantity:
                                        # daynmic update existing catalogue data with new imported
                                        for key, value in db_row.items():
                                            setattr(catalogue_exist, key, value)
                                            catalogue_exist.update()

                                        insert_locs_bins(location, bin, catalogue_exist, current_user.dashboard.id, db)

                                        uploaded_skus.append(db_row['sku'])
                                    else:
                                        invalid_rows.append(row_info)

                                else:
                                    newCatalogue = Catalogue(user_id=current_user.id, **db_row)

                                    newCatalogue.insert()

                                    # insert catalogue locations if not exist create locations
                                    insert_locs_bins(location, bin, newCatalogue, current_user.dashboard.id, db)

                                    uploaded_skus.append(db_row['sku'])

                            except Exception as theerror:
                                # sometimes this error encoding is can not passed to print so ignore issues for it or ignore print it and enogh exc_info
                                # if error it broke the next rows rollback and continue
                                utf8_encoded_error = str(theerror).encode('utf-8', 'ignore')          
                                db.session.rollback()
                                invalid_rows.append(row_info)
                                print('System Error row ignored, import_catalogues_excel: {} , info: {}'.format(utf8_encoded_error, sys.exc_info()))
                                continue
                        else:
                            catalogue_exist = inv(Catalogue.query.filter_by(sku=db_row['sku']), User.id, Catalogue.user_id).first()
                            if catalogue_exist:
                                insert_locs_bins(location, bin, catalogue_exist, current_user.dashboard.id, db)
                                
                            duplicated_skus.append(str(db_row['product_name']))
                            continue
                        
                    # response message with report what data uploaded and what have issues and where issues
                    total_ignored = len(duplicated_skus) + len(invalid_rows)
                    total_uploaded = len(mapped_catalogues['db_rows']) - total_ignored
                    message = 'Successfully Imported Catalogues From Excel File, Total processed: {}, Total Ignored: {}, Empty Rows: {}, Duplicateds: [{}], invalids: [{}]'.format(total_uploaded, total_ignored,empty_rows, ','.join(duplicated_skus), ','.join(invalid_rows))
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
    else:
        flash('You do not have permissions to import the catalogues from excel file.', 'danger')
        return redirect(url_for('routes.catalogues'))

# export listing
@main.route('/export_listings', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def listing_export():
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            selected_listings = inv(Listing.query, User.dashboard_id, Listing.dashboard_id).all()
            # this do 2 things, incase there are no data error may raised, also for performance as there no data no need call this heavy function
            if selected_listings:
                column_names = Listing.__table__.columns.keys()
                # column_names also used to exclude names for example you may not need id, so if not provided will not exported
                excel_response = flask_excel.make_response_from_query_sets(selected_listings, column_names, 'csv', file_name='inventory_listings')
                return excel_response
            else:
                flash('There is no data to be exported.', 'warning')
                return redirect(url_for('routes.index'))
        else:
            flash('You do not have permissions to export the listings.', 'danger')
            return redirect(url_for('routes.index'))
    except Exception as e:
        # redirect used to display the flash message incase of error , becuase this GET request and it processed in the same rendered page (so flash can not displayed without refresh)
        print('System Error listing_export: {}'.format(sys.exc_info()))
        flash('Unknown error Your request could not be processed right now, please try again later.', 'danger')
        return redirect(url_for('routes.index'))

@main.route('/reports', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def reports():
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
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
        else:
            flash('You do not have permissions to access the reports page.', 'danger')
            return redirect(url_for('routes.index'))
    except Exception as e:
        print('System Error: {}'.format(sys.exc_info()))
        flash('unable to display reports page', 'danger')
        return redirect(url_for('routes.index'))


@main.route('/get_filter_columns', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def get_filter_columns():
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            requested_table = request.args.get('table', '')
            # consts (usefor secuirty) getSqlalchemyColumnByName
            export_sqlalchemy_filter = ExportSqlalchemyFilter()
            # return all or only requested 
            data = export_sqlalchemy_filter.tables_data[requested_table] if requested_table in export_sqlalchemy_filter.tables_data else None
            return jsonify({'code': 200, 'data': data})
        else:
            return jsonify({'code': 403, 'message': 'You do not have permissions to view the filters data'})
    except Exception as e:
        print('System Error get_filter_columns: {}'.format(sys.exc_info()))
        flash('Unknown error Your request could not be processed right now, please try again later.', 'danger')
        return jsonify({'code': 500, 'message': 'system error'})


# full sqlalchemy dynamic export table data
@main.route('/reports/export', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def reports_export():
    can = user_have_permissions(app_permissions, permissions=['read'])
    if can:
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
            # raise e
            print('System Error reports_export: {}'.format(sys.exc_info()))
            message = message if message != '' else 'Unknown Error Found While process your request'
            success = False

        finally:
            if success == True and excel_response:
                return excel_response
            else:
                flash(message, 'danger')
                return redirect(url_for('main.reports'))
    else:
        flash('You do not have permissions to export data.', 'danger')
        return redirect(url_for('main.reports'))


# this search function works with js search component dynamic for all app searchs
@main.route('/search', methods=['GET', 'POST'])
@login_required
@vendor_permission.require(http_exception=403)
def search():
    can = user_have_permissions(app_permissions, permissions=['read'])
    if can:
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
                    'created_date': Catalogue.created_date,
                    'location': WarehouseLocations.name,
                    'bin': LocationBins.name
                }
                if column in direct_search_columns:
                    search_val = '%{}%'.format(value)
                    sqlalchemy_expression = direct_search_columns[column].ilike(search_val)
                    data = [data_obj.format() for data_obj in inv(db.session.query(Catalogue).outerjoin(
                        CatalogueLocations, Catalogue.id == CatalogueLocations.catalogue_id
                    ).outerjoin(
                        WarehouseLocations, CatalogueLocations.location_id == WarehouseLocations.id
                    ).outerjoin(
                        CatalogueLocationsBins, CatalogueLocations.id == CatalogueLocationsBins.location_id
                    ).outerjoin(
                        LocationBins, CatalogueLocationsBins.bin_id == LocationBins.id
                    ), User.id, Catalogue.user_id).filter(
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
                    
                    data = [data_obj.format() for data_obj in inv(db.session.query(Listing).join(
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
                    ), User.dashboard_id, Listing.dashboard_id).filter(
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
                    data = [data_obj.format() for data_obj in inv(db.session.query(Order).join(
                        Listing, Order.listing_id == Listing.id
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ), User.id, Catalogue.user_id).filter(
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
                    data = [data_obj.format() for data_obj in inv(db.session.query(Order).join(
                        Listing, Order.listing_id == Listing.id
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ), User.id, Catalogue.user_id).filter(
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
                    data = [data_obj.format() for data_obj in inv(db.session.query(Purchase).join(
                        Listing, Purchase.listing_id == Listing.id
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ).outerjoin(
                        Supplier, Purchase.supplier_id == Supplier.id
                    ), User.id, Catalogue.user_id).filter(
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
    else:
        return jsonify({'code': 403, 'message': 'You do not have permissions to search data'})


# store limit in session with ajax
# this search function works with js search component dynamic for all app searchs
@main.route('/save_limit', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
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
@vendor_permission.require(http_exception=403)
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
@vendor_permission.require(http_exception=403)
def get_remaining_requests_func():
    return str(get_remaining_requests())

# import categories using API (user securly provide API key)  (this main API endpoint for categories, so incase you first imported catalogues and it created the categories for you, any time you can back here to update the categories created (eg: to setup level and parent code, or incase in future label of category changed so this endpoint will handle the update also for you)) best practice if started with offers import, come here and import categories to have level and parent code if
@main.route('/import_categories_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def api_import_categories():
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
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
                                                category_exist = inv(db.session.query(Category).filter(Category.code==hierarchy['code']), User.dashboard_id, Category.dashboard_id).first()
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
    else:
        flash('You do not have permissions to import categories from bestbuy API.', 'danger')
        return redirect(url_for('routes.setup'))

# remaning listing info report
# import categories using API (user securly provide API key)
@main.route('/import_offers_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def api_offers_import():
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
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

        
        finally:
            return redirect(url_for('routes.listings'))
    else:
        flash('You do not have permissions to import listings from bestbuy API.', 'danger')
        return redirect(url_for('routes.listings'))

@main.route('/test', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def test():
    """
    # Order.query.all()

    #r = requests.get('https://marketplace.bestbuy.ca/api/orders/documents/download?order_ids=216549197-A,216585560-A,216590959-A,216597478-A,216599230-A', headers={'Authorization': 'a750a16c-054e-407c-9825-3da7d4b2a9c1', 'Accept': 'application/octet-stream'})
    

    data = download_order_image(
        image_name='helloworld', 
        image_url='https://marketplace.bestbuy.ca/media/product/image/a363e27f-d2a4-4acb-97b4-3e657ce62aa8',
        static_folder=main.static_folder)
    return str(data)
    """
    """
    return jsonify(json.loads(json.dumps(getattr(r, 'headers'), indent=4, default=str)))
    #return r.headers.get('Content-Type', None) if r.headers
    data_obj = vars(r)
    del data_obj['_content']
    data_json = json.dumps(dict(data_obj), indent=4, default=str)
    return data_json
     
    #return str(p)
    with open(p, mode='wb') as f:
        f.write(r.content)
    """
    
    return str('hi')

    
@main.route('/import_orders_api', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def api_import_orders():
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
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
    else:
        flash('You do not have permissions to import orders from bestbuy API.', 'danger')
        return redirect(url_for('routes.orders'))


"""
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
"""


# this end point for catalogue if diffrent class use diffrent endpoint
@main.route('/generate_barcode/<int:catalogue_id>', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def generate_barcode(catalogue_id):
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
        try:
            form = generateCatalogueBarcodeForm()
            if form.validate_on_submit():
                selected_catalogue = inv(Catalogue.query.filter_by(id=catalogue_id), User.id, Catalogue.user_id).one_or_none()
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
    else:
        flash('You do not have permissions to generate barcode.', 'danger')
        return redirect(url_for('routes.view_catalogue', catalogue_id=catalogue_id))


################################### Profile ######################################
@main.route('/profile', methods=['GET'])
@login_required
@vendor_permission.require(http_exception=403)
def profile():
    can = user_have_permissions(app_permissions, permissions=['read'])
    if can:
        success = True
        try:
            update_username = UpdateUsernameForm(username=current_user.uname)
            update_password = UpdatePasswordForm()
            udate_name = UpdateNameForm(name=current_user.name)
            update_email = UpdateEmailForm(email=current_user.email)
            setup_api = setupAPIForm()
            add_key = addKeyForm()
            delete_key = removeKeyForm()
            update_key = updateKeyForm()
            renew_key = renewKeyForm()
            white_list = addWhiteListIPsForm()
            black_list = addBlackListIPsForm()
            add_inventory = None
            aupdate_inv = None
            update_inventory = updateInventoryForm()
            remove_inventory = deleteInventoriesForm()
            requests_warning = warningToManyUsers()
            make_admin = None
            change_uadmin = None

            approve_form = None
            remove_form = None

            add_user = None
            admin_inventories = []
            change_invadmin = None
            
            inventories = []

            logs = {'data': [], 'total': 0, 'isAdmin': False, 'users': [], 'url': '', 'removeUrl': '', 'categories': [item.value for item in LogsCategories]}
            if current_user.isAdmin():
                admin_inventories = Inventory.query.all()
                all_users = User.query.order_by('uname').all()
                
                addedby_users_choices = list(filter(lambda u:u, [(u.id, u.uname) if u.isInventoryAdmin() else False for u in all_users]))
                # note super users (can toggle user make it inventory admin or not new type forms)
                mka_users_choices = list(filter(lambda u:u, [(u.id, u.uname) for u in all_users]))

                add_inventory = addInventoryForm()
                add_user = addNewUserForm()                
                make_admin = makeInvAdmin()
                aupdate_inv = adminUpdateInventoryForm()

                aupdate_inv.added_by.choices = addedby_users_choices
                make_admin.user.choices = mka_users_choices

                # incase decide remove inventoryAdmin from admin for some reason make sure form not None
                approve_form = approveUserForm()
                remove_form = removeUserForm()

                change_uadmin = adminChangeUserInv()
                change_uadmin.user.choices = [('', 'Select User'), *[(u.id, u.uname) for u in all_users]]
                change_uadmin.inv.choices = [('', 'Select Inventory'), *[(inv.id, inv.name) for inv in admin_inventories]]

                
            if current_user.isInventoryAdmin():
                # only 1 manager for inventory except will need new related table and more complex query or complex action by comma sperated value
                inventories = Inventory.query.filter_by(added_by=current_user.id).all()

                approve_form = approveUserForm()
                remove_form = removeUserForm()
                change_invadmin = invAdminChangeUserInv()

                invadmin_users = db.session.query(User).join(Inventory, User.inventory_id==Inventory.id).filter(Inventory.added_by==current_user.id).all()

                change_invadmin.user.choices = [('', 'Select User'), *[(u.id, u.uname) for u in invadmin_users]]
                change_invadmin.inv.choices = [('', 'Select Inventory'), *[(inv.id, inv.name) for inv in inventories]]

            logs_limit = 50
            if current_user.isAdmin():
                # logs
                logs['data'] = [{'id': log.id, 'content': log.message} for log in Logs.query.order_by(desc(Logs.id)).limit(logs_limit).all()]
                logs['users'] = [{'id': u.id, 'user': u.uname} for u in all_users]
                logs['isAdmin'] = True
                logs['total'] = db.session.query(func.count(Logs.id)).scalar()
                logs['url'] = url_for('main.activity_logs_admin')
                logs['removeUrl'] = url_for('main.delete_log_admin')

            elif current_user.isInventoryAdmin():
                logs['data'] = [{'id': log.id, 'content': log.message} for log in inv(Logs.query, User.id, Logs.user_id).order_by(desc(Logs.id)).limit(logs_limit).all()]
                # every user have only 1 inventory belong to, user can add multiple invetories, user can add mutltiple inventory and be admin to it without join it thats why i added current user as logicaly if all created right by admin, the inventory admin must join the inventory he manage
                logs['users'] = [{'id': u.id, 'user': u.uname} for u in invadmin_users]
                logs['isAdmin'] = True
                logs['total'] = inv(db.session.query(func.count(Logs.id)), User.id, Logs.user_id).scalar()
                logs['url'] = url_for('main.activity_logs_invadmin')
                logs['removeUrl'] = url_for('main.delete_log_invadmin')

            else:
                # logs
                logs['data'] = [{'id': log.id, 'content': log.message} for log in Logs.query.filter_by(user_id=current_user.id).order_by(desc(Logs.id)).limit(logs_limit).all()]
                logs['isAdmin'] = False
                logs['total'] = db.session.query(func.count(Logs.id)).filter_by(user_id=current_user.id).scalar()
                logs['url'] = url_for('main.activity_logs')                
                logs['removeUrl'] = ''

            ourapi_requests_limit = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_requests_limit').first()
            ourapi_keys_max = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_keys_max').first()
            # dynamic get valid number of user keys if any, else look for init else set default number 10
            user_keys_max = ourapi_keys_max.value if ourapi_keys_max else current_app.config.get('OURAPI_KEYS_MAX', 10)


        except Exception as e:
            print('error from profile {}'.format(sys.exc_info()))
            flash('unable to display profile page', 'danger')
            success = False
        finally:
            if success:
                return render_template(
                    'profile.html', update_username=update_username,
                    update_password=update_password, udate_name=udate_name, update_email=update_email, setup_api=setup_api, add_key=add_key,
                    delete_key=delete_key, update_key=update_key, renew_key=renew_key, white_list=white_list, black_list=black_list,
                    ourapi_requests_limit=ourapi_requests_limit, ourapi_keys_max=ourapi_keys_max, user_keys_max=user_keys_max, add_user=add_user,
                    add_inventory=add_inventory, update_inventory=update_inventory, remove_inventory=remove_inventory, admin_inventories=admin_inventories, 
                    inventories=inventories, aupdate_inv=aupdate_inv, make_admin=make_admin, approve_form=approve_form, remove_form=remove_form, requests_warning=requests_warning,
                    change_uadmin=change_uadmin, change_invadmin=change_invadmin, logs=logs)
            else:
                return redirect(url_for('routes.index'))



    else:
        flash('You do not have permissions view profile page.', 'danger')
        return redirect(url_for('routes.index'))


@main.route('/proccess_chart_filters/<string:chart_id>', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def proccess_chart_filters(chart_id):
    can = user_have_permissions(app_permissions, permissions=['read'])
    if can:
        res = {'code': 400, 'message': 'Invalid Data.'}
        try:
            cols = request.form.getlist('cols[]')
            bys = request.form.getlist('bys[]')
            values = request.form.getlist('values[]')

            encrypted_cols = get_unencrypted_cols(cols)
            if len(cols) > 0 and len(cols) == len(bys) and len(bys) == len(values) and encrypted_cols is not None:
                request_filters = get_ordered_dicts(['col', 'by', 'value'], encrypted_cols, bys, values)
                if len(request_filters) > 0:
                    sqlalchemy_filters = get_sqlalchemy_filters(request_filters)
                    if len(sqlalchemy_filters) > 0:
                        chartdata_after_filter = get_charts(db, current_user, charts_ids=[chart_id], filter_args=sqlalchemy_filters)
                        if isinstance(chartdata_after_filter, list) and len(chartdata_after_filter) == 1:
                            if len(chartdata_after_filter[0]['data']) > 0 and len(chartdata_after_filter[0]['labels']) > 0:
                                res = {
                                    'code': 200,
                                    'chart_id': chart_id,
                                    'data': chartdata_after_filter[0]['data'],
                                    'labels': chartdata_after_filter[0]['labels']
                                    }
                            else:
                                res = {'code': 404, 'message': 'No data found for applied filters, please change/remove the filters.'}
                        else:
                            res = {'code': 404, 'message': 'Chart Not Found, unable to apply filters.'}
                    else:
                        res = {'code': 400, 'message': 'Invalid Data.'}
                else:
                    res = {'code': 404, 'message': 'No Changes Detected.'}
        except Exception as e:
            res = {'code': 400, 'message': 'Invalid Data.'}
            print('error from proccess_chart_filters {}'.format(sys.exc_info()))
        finally:
            return jsonify(res)
    else:
        return jsonify({'code': 400, 'message': 'You do not have permissions to read chart filters.'})

### charts avitvties
@main.route('/proccess_chart_activity/<string:chart_id>', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def proccess_chart_activity(chart_id):
    can = user_have_permissions(app_permissions, permissions=['read'])
    if can:
        result = {'code': 400, 'message': 'Invalid Data.'}
        try:
            value = request.form.get('value', None)
            filterby = request.form.get('filterby', None)
            date_type = request.form.get('data_type', None)

            if value and chart_id and isinstance(value, str) and isinstance(filterby, str) and filterby and isinstance(date_type, str) and date_type:
                start_and_end = value.strip()
                if ',' not in start_and_end:
                    # default utc (note custom is send 1 value user selected and from python i get the now not from js client side so all dates and format and timezone valid and no abuse)
                    start_and_end = complete_activity_date(start_and_end, type_format='date', utc=False)

                date_objs = get_activity_dateobjs(activity_dates=start_and_end, type_format='date', utc=False)
                if date_objs and isinstance(date_objs, list) and len(date_objs) == 2:
                    # should be ultimate secure return sqlalchemy column not direct get value from client of db info and column , also note column client is encrypted only in client but selected un unecrypted from python
                    sqlalchemy_column_or_none = get_hashed_sqlalchemycol(recived_hash=filterby, chart_id=chart_id)
                    if sqlalchemy_column_or_none:
                        time_format = "%Y-%m-%d" if date_type else "%Y-%m-%d %H:%M:%S"
                        # (all acitivty is between only) (work with datetime dates objects better it valid for dates and datetime dynamic)
                        now_date = date_objs[0].strftime(time_format)
                        prev_date = date_objs[1].strftime(time_format)

                        # get list sqlalchemy BinaryExpression of filters same as client requested but secure and full from backend only client data not used if used like dates it hard validated and if reach here it valid datetime objects two
                        sqlalchemy_date_filters = [sqlalchemy_column_or_none.between(date_objs[1], date_objs[0])]

                        chartdata_after_filter = get_charts(db, current_user, charts_ids=[chart_id], filter_args=sqlalchemy_date_filters)
                        # final check , check if data returned and label as get_charts smart if no data return empty array
                        if isinstance(chartdata_after_filter, list) and len(chartdata_after_filter) == 1:
                            if len(chartdata_after_filter[0]['data']) > 0 and len(chartdata_after_filter[0]['labels']) > 0:
                                # success result
                                result = {
                                    'code': 200,
                                    'chart_id': chart_id,
                                    'data': chartdata_after_filter[0]['data'],
                                    'labels': chartdata_after_filter[0]['labels'],
                                    'message': 'Between ({})-({})'.format(now_date, prev_date)
                                    }
                            else:
                                result = {'code': 404, 'message': 'No data to display Between ({})-({}) no action.'.format(prev_date, now_date)}
                        else:
                            result = {'code': 404, 'message': 'Chart Not Found, unable to apply activity filter.'}
        except Exception as e:
            print('error from proccess_chart_activity {}'.format(sys.exc_info()))
            result = {'code': 500, 'message': 'Unable to process your request, please try again later.{}'.format(sys.exc_info())}
            
        finally:
            return jsonify(result)
    else:
        return jsonify({'code': 403, 'message': 'You do not have permssions to view apply activities'})

# cancel all chart filters
@main.route('/cancel_chart', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def cancel_chart():
    res = {'code': 400, 'message': 'Invalid Data.'}
    try:
        chart_id = request.form.get('chart_id', None)
        if chart_id:
            original_charts_data =  get_charts(db, current_user, charts_ids=[chart_id])
            if isinstance(original_charts_data, list) and len(original_charts_data) == 1 and len(original_charts_data[0]['data']) > 0 and len(original_charts_data[0]['labels']) > 0:
                res = {
                    'code': 200,
                    'data': original_charts_data[0]['data'],
                    'labels': original_charts_data[0]['labels'],
                    'message': 'All filters and activity have been cancelled.'
                    }
    except Exception as e:
        res = {'code': 500, 'message': 'Unable to cancel filters right now.'}
        print('system error {}'.format(sys.exc_info()))
    finally:
        return jsonify(res)


# Create users admin
@main.route('/add_user', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def admin_add_user():
    try:
        # check if vendor role found else create it
        vendor_role = Role.query.filter_by(name='vendor').one_or_none()
        if vendor_role is None:
            vendor_role = Role(name='vendor')
            vendor_role.insert()

        form = addNewUserForm()
        if form.validate_on_submit():
            user_exist = User.query.filter_by(uname=form.uname.data).one_or_none()
            email_exist = User.query.filter_by(email=form.email.data).one_or_none()
            if user_exist is None and email_exist is None:

                # this add all user relational tables all togther or fail togther and also 1 commit
                user_dashboard = Dashboard()
                new_user = User(
                    name=form.name.data, 
                    uname=form.uname.data,
                    upass=bcrypt.generate_password_hash(form.pwd.data),
                    email=form.email.data
                    )
                # create new vendor default role for the user
                new_user.roles.append(UserRoles(role_id=vendor_role.id))
                user_dashboard.user = new_user
                user_dashboard.insert()

                flash('Successfully Created New User', 'success')
            else:
                flashes = []
                if user_exist is not None:
                    flashes.append('Username is taken, please try something else.')
                
                if email_exist is not None:
                    flashes.append('Email is taken, please try something else.') 
                
                if len(flashes) > 0:
                    flash(','.join(flashes), 'danger')

        else:
            flash(get_errors_message(form), 'danger')
        
    except Exception as e:
        print('System Error: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unable to create new users right now, please try again later.', 'danger')

    finally:
        return redirect(url_for('main.profile', movetocomponent='users'))
    
@main.route('/update_name', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def update_name():
    can = user_have_permissions(app_permissions, permissions=['update'])
    if can:
        try:
            form = UpdateNameForm()
            if form.validate_on_submit():
                if current_user.name != form.name.data:
                    current_user.name = form.name.data
                    current_user.update()
                    flash('Successfully updated the name.', 'success')
                else:
                    flash('No changes detected.', 'success')
            else:
                flash(get_errors_message(form), 'danger')
        except Exception as e:
            flash('unable to update the name right now.', 'danger')
            print('system error {}'.format(sys.exc_info()))
        finally:
            return redirect(url_for('main.profile', movetocomponent='user_details'))
    else:
        flash('You do not have permissions to update name.', 'danger')
        return redirect(url_for('main.profile', movetocomponent='user_details'))

@main.route('/update_email', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def update_email():
    can = user_have_permissions(app_permissions, permissions=['update'])
    if can:
        try:
            form = UpdateEmailForm()
            if form.validate_on_submit():
                if current_user.email != form.email.data:
                    exist_email = User.query.filter_by(email=form.email.data).first()
                    if not exist_email:
                        current_user.email = form.email.data
                        current_user.update()
                        flash('Successfully updated the email', 'success')
                    else:
                        flash('Email is taken', 'danger')
                else:
                    flash('No changes detected.', 'success')
            else:
                flash(get_errors_message(form), 'danger')
        except Exception as e:
            flash('unable to update the email right now.', 'danger')
            print('system error {}'.format(sys.exc_info()))
        finally:
            return redirect(url_for('main.profile', movetocomponent='user_details'))
    else:
        flash('You do not have permissions to update email.', 'danger')
        return redirect(url_for('main.profile', movetocomponent='user_details'))

@main.route('/update_username', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def update_username():
    try:
        can = user_have_permissions(app_permissions, permissions=['update'])
        if can:
            form = UpdateUsernameForm()
            if form.validate_on_submit():
                if current_user.uname != form.username.data:
                    exist_username = User.query.filter_by(uname=form.username.data).first()
                    if not exist_username:
                        current_user.uname = form.username.data
                        current_user.update()
                        flash('Successfully updated the username', 'success')
                    else:
                        flash('Username is taken', 'danger')
                else:
                    flash('No changes detected.', 'success')
            else:
                flash(get_errors_message(form), 'danger')
        else:
            flash('You do not have permissions to update username.', 'danger')
    except Exception as e:
        flash('unable to update the username right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('main.profile', movetocomponent='user_credentials'))

@main.route('/update_password', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def update_password():
    try:
        can = user_have_permissions(app_permissions, permissions=['update'])
        if can:
            form = UpdatePasswordForm()
            if form.validate_on_submit():
                if form.current_pwd.data != form.pwd.data:
                    valid_pass = bcrypt.check_password_hash(current_user.upass, form.current_pwd.data)
                    if valid_pass == True:
                        hashed_pass = bcrypt.generate_password_hash(form.pwd.data)
                        current_user.upass = hashed_pass
                        current_user.update()
                        flash('Successfully updated the password', 'success')
                    else:
                        flash('Invalid password', 'danger')
                else:
                    flash('No changes detected.', 'success')
            else:
                flash(get_errors_message(form), 'danger')
        else:
            flash('You do not have permissions to update password.', 'danger')
    except Exception as e:
        flash('unable to update the password right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('main.profile', movetocomponent='user_credentials'))

@main.route('/manage_admins', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def manage_super_users():
    can = user_have_permissions(app_permissions, permissions=['update'])
    if can:

        
        try:
            # as 1 form if is admin and saw the button he can submit delete from the two forms no mater it backend deletable or not, but if not superadmin and submit he will not able to delete
            form = makeInvAdmin()
            form.user.choices = list(filter(lambda u:u, [(u.id, u.uname) for u in User.query.order_by('uname').all()]))
            if form.validate_on_submit():
                user = User.query.filter_by(id=form.user.data).one_or_none()
                if user:
                    action_done = False

                    if form.action.data == 1:
                        # (remove action)
                        inventory_admin_roles = db.session.query(UserRoles
                        ).join(Role, UserRoles.role_id==Role.id
                        ).filter(UserRoles.user_id==user.id, Role.name=='inventory_admin').all()
                        
                        for inventory_admin_role in inventory_admin_roles:
                            inventory_admin_role.delete()
                            action_done = True

                    else:
                        # (add action) check if user have the inventory admin role or not
                        inventory_admin_role = db.session.query(UserRoles
                                                ).join(Role, UserRoles.role_id==Role.id
                                                ).filter(UserRoles.user_id==user.id, Role.name=='inventory_admin').all()
                        
                        # if user not have inventory admin role
                        if not inventory_admin_role:
                            # get or add inventory admin system role
                            inventory_admin = Role.query.filter_by(name='inventory_admin').first()
                            if not inventory_admin:
                                inventory_admin = Role(name='inventory_admin', system=True, superuser=True)
                                inventory_admin.insert()
                            # insert new inventory admin role
                            UserRoles(user_id=user.id, role_id=inventory_admin.id).insert()
                            action_done = True

                    if action_done:
                        flash('Successfully updated {} user permssions'.format(user.uname))
                    else:
                        flash('No Action done for {} permssions'.format(user.uname))
                else:
                    flash('User not found', 'danger')
            else:
                flash(get_errors_message(form), 'danger')
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown error unable to delete location', 'danger')

        finally:
            return redirect(url_for('main.profile', movetocomponent='users'))
    else:
        flash("You do not have permissions to delete inventory.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='users'))
    

###########################  Inventories  ##############################
@main.route('/inventories/add', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def add_inventory():
    can = user_have_permissions(app_permissions, permissions=['add'])
    if can:
        try:
            form = addInventoryForm()
            if form.validate_on_submit():
                # category code and label are uniques for the dashboard (eg you can not have to categories with same title in invetory sidebar and random some here and some here)
                exist_inventory = Inventory.query.filter_by(name=form.a_name.data).one_or_none()
                if not exist_inventory:

                    new_inventory = Inventory(
                        added_by=current_user.id,
                        name=form.a_name.data,
                        active=form.a_active.data,
                        private=form.a_private.data,
                        exportable=form.a_exportable.data,
                        deletable=form.a_deletable.data,
                        salat=form.pass_salat.data,
                        max_pending=form.a_max_pending.data
                        )

                    if form.joinpass.data:
                        new_inventory.join_pass = cryptocode.encrypt(form.joinpass.data, form.pass_salat.data)
                    
                    # decoded = cryptocode.decrypt(encoded, "")
                    new_inventory.insert()
                    flash('Successfully Created New Inventory', 'success')
                else:
                    flash('Can not add Inventory, Category with same name [{}] already exist'.format(form.a_name.data), 'danger')
            else:
                for field, errors in form.errors.items():
                    if field == 'csrf_token':
                        flash("Error can not create Inventory Please restart page and try again", "danger")
                        continue
                    else:
                        flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')

        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown Error unable to create new inventory', 'danger')
        finally:
            return redirect(url_for('main.profile', movetocomponent='inventories'))
    else:
        flash("You do not have permissions to add category.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='inventories'))

@main.route('/inventories/<int:inventory_id>/update/<int:lvl>', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def update_inventory(inventory_id, lvl):
    can = user_have_permissions(app_permissions, permissions=['update'])
    if can:
        error_msg = 'Unknown error unable to update inventory'
        try:
            form = None
            target_inventory = False
            if lvl == 2 and current_user.isAdmin():
                # full secure front, backend
                target_inventory = Inventory.query.filter_by(id=inventory_id).one_or_none()
                form = adminUpdateInventoryForm(
                    name=target_inventory.name, active=target_inventory.active,
                    private=target_inventory.private, exportable=target_inventory.exportable,
                    deletable=target_inventory.deletable,
                )
                form.added_by.choices = list(filter(lambda u:u, [(u.id, u.uname) if u.is_super() else False for u in User.query.order_by('uname').all()]))
            else:
                if lvl == 1:
                    target_inventory = Inventory.query.filter_by(id=inventory_id).one_or_none()
                    form = updateInventoryForm(
                        name=target_inventory.name, active=target_inventory.active,
                        private=target_inventory.private
                    )
                else:
                    form = None
                    target_inventory = False

            if form and target_inventory != False:
                # form is not None and target inventory not with inital value incase var not asigned and async if all must
                if target_inventory is not None:
                    if form.validate_on_submit():
                        nochange = target_inventory.name == form.name.data and target_inventory.active == form.active.data and target_inventory.private == form.private.data and target_inventory.salat == form.pass_salat.data and target_inventory.join_pass == form.joinpass.data

                        target_inventory.name = form.name.data
                        target_inventory.active = form.active.data
                        target_inventory.private = form.private.data

                        if target_inventory.salat == form.pass_salat.data:
                            # if salat not changed
                            if target_inventory.join_pass != form.joinpass.data:
                                # if pass changed
                                if form.joinpass.data != '':
                                    # lib will encrypt empty strings
                                    target_inventory.join_pass = cryptocode.encrypt(form.joinpass.data, target_inventory.salat)
                                else:
                                    target_inventory.join_pass = form.joinpass.data

                        else:
                            # if salat changed
                            if target_inventory.join_pass == form.joinpass.data:

                                if form.joinpass.data != '':
                                    # if pass not changed back pass as it encrypted and encrypt it again with the new selected salat
                                    back_pass = cryptocode.decrypt(target_inventory.join_pass, target_inventory.salat)
                                    if back_pass == False:
                                        # next line will raise exception
                                        error_msg = 'Broken Password Update password is required'
                                        raise ValueError('update_inventory error Can not backup previous password')
                                    
                                    target_inventory.join_pass = cryptocode.encrypt(back_pass, form.pass_salat.data)
                                else:
                                    target_inventory.join_pass = form.joinpass.data

                                target_inventory.salat = form.pass_salat.data
                            else:
                                if form.joinpass.data != '':
                                    target_inventory.join_pass = cryptocode.encrypt(form.joinpass.data, form.pass_salat.data)
                                else:
                                    target_inventory.join_pass = form.joinpass.data
                                    
                                target_inventory.salat = form.pass_salat.data

                        # dynamic security also jinja2 and js strict and passed arugments in endpoint view
                        if lvl == 2 and current_user.isAdmin():
                            # confirm lvl2 only not enogh to pass or assign a virable 
                            nochange = nochange and target_inventory.exportable == form.exportable.data and target_inventory.deletable == form.deletable.data and target_inventory.added_by == form.added_by.data and target_inventory.max_pending == form.max_pending.data
                            target_inventory.exportable = form.exportable.data
                            target_inventory.deletable = form.deletable.data
                            target_inventory.max_pending = form.max_pending.data
                            if target_inventory.added_by != form.added_by.data:
                                # as this forgien key change it heavy process so not do it unless real need
                                target_inventory.added_by = form.added_by.data


                        target_inventory.update()

                        if nochange:
                            flash('No change detected', 'info')
                        else:
                            flash('Successfully updated Inventory data Id: {}'.format(inventory_id), 'success')
                    else:
                        for field, errors in form.errors.items():
                            if field == 'csrf_token':
                                 flash("form no longer valid Please restart page and try again", "danger")
                            else:
                                flash('Error in {} : {}'.format(field, ','.join(errors)), 'danger')
                else:
                    flash('Inventory not found', 'danger')
            else:
                flash('Unable to process your request', 'danger')
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash(error_msg, 'danger')
        finally:
            return redirect(url_for('main.profile', movetocomponent='inventories'))
    else:
        flash("You do not have permissions to update Inventory.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='inventories'))
    
@main.route('/inventories/<int:inventory_id>/delete', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def delete_inventory(inventory_id):
    can = user_have_permissions(app_permissions, permissions=['delete'])
    if can:
        try:
            # as 1 form if is admin and saw the button he can submit delete from the two forms no mater it backend deletable or not, but if not superadmin and submit he will not able to delete
            form = deleteInventoriesForm()
            target_inventory = Inventory.query.filter_by(id=inventory_id).first()
            if target_inventory is not None:
                if (current_user.isInventoryAdmin() or current_user.isAdmin()) and (
                        (target_inventory.deletable) or (not target_inventory.deletable and current_user.isAdmin())
                    ):
                    if form.validate_on_submit():
                        target_inventory.delete()
                        flash('Successfully deleted Location ID: {}'.format(inventory_id), 'success')
                    else:
                        flash('Unable to delete Location, ID: {}'.format(inventory_id), 'danger')
                else:
                    flash('Unable to process your request', 'danger')
            else:
                flash('Location not found it maybe deleted, ID: {}'.format(inventory_id), 'danger')
        except Exception as e:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown error unable to delete location', 'danger')
        finally:
            return redirect(url_for('main.profile', movetocomponent='inventories'))
    else:
        flash("You do not have permissions to delete inventory.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='inventories'))


@main.route('/view_joinpass', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def view_joinpass():
    data = {'code': 0}
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            json_data = request.get_json()
            if (isinstance(json_data, dict) and json_data.get('inv')):
                inv_id = json_data.get('inv')
                inventory = Inventory.query.filter_by(id=inv_id).one_or_none()
                if inventory:
                    join_pass = inventory.join_pass
                    if join_pass:
                        join_salat = ''
                        if inventory.salat:
                            join_salat = inventory.salat
                        
                        pass_val = cryptocode.decrypt(join_pass, join_salat)
                        if pass_val != False:
                            data = {'code': 200, 'val': pass_val}
                        else:
                             data = {'code': 500, 'message': 'Unable to load your password, please try change it as it may solve this issue.'}
                    else:
                        data = {'code': 200, 'val': ''}
                else:
                    data = {'code': 404, 'message': 'Inventory not found or deleted.'}
            else:
                data = {'code': 404, 'message': 'unable to load data, invalid data sent.'}
        else:
            data = {'code': 403, 'message': 'You are not allowed to view data.'}
    except:
        print('System Error: {}'.format(sys.exc_info()))
        data = {'code': 500, 'message': 'unknown error, unable to load password'}
    finally:
        return jsonify(data)

@main.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def approve_user(user_id):
    can = user_have_permissions(app_permissions, permissions=['update'])
    if can:
        try:
            # as 1 form if is admin and saw the button he can submit delete from the two forms no mater it backend deletable or not, but if not superadmin and submit he will not able to delete
            form = approveUserForm()
            if form.validate_on_submit():

                target_user = None
                if current_user.isAdmin():
                    target_user = User.query.filter_by(id=form.user_id.data).one_or_none()
                else:
                    target_user = db.session.query(User).join(
                        Inventory, User.inventory_id==Inventory.id
                        ).filter(
                            Inventory.added_by==current_user.id,
                            User.id==form.user_id.data
                        ).one_or_none()
                
                if target_user:
                    if not target_user.approved:
                        target_user.approved = True
                        target_user.update()
                        flash("User with id: {} is successfully approved".format(user_id), 'success')
                    else:
                        flash("User with id: {} is already approved".format(user_id), 'info')
                else:
                    flash('User with id: {} is not found or removed'.format(user_id), 'danger')
            else:
                flash('Form has been expired please try again', 'danger')
        except:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown error unable to approve user', 'danger')
        finally:
            return redirect(url_for('main.profile', movetocomponent='inventories'))
    else:
        flash("You do not have permissions to approve users.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='inventories'))

@main.route('/remove_user/<int:user_id>', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def remove_user(user_id):
    can = user_have_permissions(app_permissions, permissions=['delete'])
    if can:
        try:
            # as 1 form if is admin and saw the button he can submit delete from the two forms no mater it backend deletable or not, but if not superadmin and submit he will not able to delete
            form = approveUserForm()
            if form.validate_on_submit():

                target_user = None
                if current_user.isAdmin():
                    target_user = User.query.filter_by(id=form.user_id.data).one_or_none()
                else:
                    target_user = db.session.query(User).join(
                        Inventory, User.inventory_id==Inventory.id
                        ).filter(
                            Inventory.added_by==current_user.id,
                            User.id==form.user_id.data
                        ).one_or_none()
                
                if target_user:
                    target_user.delete()
                    flash('User with id: {} is successfully deleted.'.format(user_id), 'success')
                else:
                    flash('User with id: {} is not found or removed'.format(user_id), 'danger')
            else:
                flash('Form has been expired please try again', 'danger')
        except:
            print('System Error: {}'.format(sys.exc_info()))
            flash('Unknown error unable to approve user', 'danger')
        finally:
            return redirect(url_for('main.profile', movetocomponent='inventories'))
    else:
        flash("You do not have permissions to approve users.", 'danger')
        return redirect(url_for('main.profile', movetocomponent='inventories'))

# Change inventory users
@main.route('/change_inv', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def change_inv():
    try:
        can = user_have_permissions(app_permissions, permissions=['update'])
        if can:
            invadmin_users = db.session.query(User).join(Inventory, User.inventory_id==Inventory.id).filter(Inventory.added_by==current_user.id).all()
            inventories = Inventory.query.filter_by(added_by=current_user.id).all()
        
            form = invAdminChangeUserInv()
            form.user.choices = [('', 'Select User'), *[(u.id, u.uname) for u in invadmin_users]]
            form.inv.choices = [('', 'Select Inventory'), *[(inv.id, inv.name) for inv in inventories]]

            if form.validate_on_submit():
                user = db.session.query(User).join(Inventory, User.inventory_id==Inventory.id).filter(Inventory.added_by==current_user.id, User.id==form.user.data).first()
                if user:
                    # better performance as if user not exist no need run 2 query
                    inv = Inventory.query.filter_by(id=form.inv.data, added_by=current_user.id).one_or_none()
                    if inv:
                        user.inventory_id = inv.id
                        user.update()
                        flash("User: {} inventory has changed.".format(user.uname), 'success')
                    else:
                        flash("Inventory not found, unable to update inventory.", 'danger')
                else:
                    flash("User not found, unable to update inventory.", 'danger')
            else:
                flash("Form expired please try again:{}".format(form.errors), 'danger')
        else:
            flash("You do not have permissions to update user's inventory.", 'danger')
    except:
        print('System Error: {}'.format(sys.exc_info()))
        flash("Unkown error, unable to update user inventory.", 'danger')
    finally:
        return redirect(url_for('main.profile', movetocomponent='inventories'))

@main.route('/admin_change_inv', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def admin_change_inv():
    try:
        can = user_have_permissions(app_permissions, permissions=['update'])
        if can:
            form = adminChangeUserInv()
            form.user.choices = [('', 'Select User'), *[(u.id, u.uname) for u in User.query.order_by('uname').all()]]
            form.inv.choices = [('', 'Select Inventory'), *[(inv.id, inv.name) for inv in Inventory.query.all()]]
            
            if form.validate_on_submit():
                user = User.query.filter_by(id=form.user.data).one_or_none()
                if user:
                    inv = Inventory.query.filter_by(id=form.inv.data).one_or_none()
                    if inv:
                        user.inventory_id = inv.id
                        user.update()
                        flash("User: {} inventory has changed.".format(user.uname), 'success')
                    else:
                        flash("Inventory not found, unable to update inventory.", 'danger')
                else:
                    flash("User not found, unable to update inventory.", 'danger')
            else:
                flash("Form expired please try again", 'danger')
        else:
            flash("You do not have permissions to update inventory of user.", 'danger')
    except:
        print('System Error: {}'.format(sys.exc_info()))
        flash("Unkown error, unable to update user inventory.", 'danger')
    finally:
        return redirect(url_for('main.profile', movetocomponent='inventories'))


@main.route('/remove_old_pending', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def remove_old_pending():
    can = user_have_permissions(app_permissions, permissions=['delete'])
    if can:
        try:
            form = warningToManyUsers()
            if form.validate_on_submit():
                current_time = datetime.utcnow()
                two_months_ago = current_time - timedelta(weeks=8)
                before_2_months = db.session.query(User.id).join(
                            Inventory, User.inventory_id==Inventory.id
                            ).join(
                                UserRoles, UserRoles.user_id==User.id
                                ).join(
                                    Role, UserRoles.role_id==Role.id
                                    ).filter(
                                        User.approved==False, Inventory.added_by==current_user.id,
                                        User.created_date<two_months_ago
                                    ).all()
                for user in before_2_months:
                    user.delete()
                flash('Succssfully removed old users', 'successfully')
            else:
                flash('Form expired please try again.', 'danger')
        except Exception as e:
            flash('unable to process your request right now.', 'danger')
            print('system error {}'.format(sys.exc_info()))
        finally:
            return redirect(url_for('main.profile'))
    else:
        flash('You have no permission to reject users.', 'danger')
        return redirect(url_for('main.profile'))
    
# updates good
# 1 active False remove inventory from signup mean not allow signup requests and create on hold users for secuirty and allow signup when required or admin see it completed number no need more users ! not done 
# public means no users can signup direct without passwords
# private users must enter passwords to join the inventory
# require new column require_approval for both private and public so users can join direct if provided pass in private without approved by admin
# one option good 2 codes one for direct join without approved (None if not set by user and prevent random) and one for normal join with approval
# 2 so direct_join_code (if generated this code it can used so users direct start signup without wait to be approved)
# late feature not now, admin may ask to add captcha to signup lvl1 or 2 (require enter code first in signup to display page os signup not code part of page)
# late feature not now, admin may require 2 key auth must done in order to login his users, so when user login check his inv and settings of it and if it require custom things
# small note on hold users will hold usernames as well, and incrase db users speacily who not use system, admin can delete and reject users, as no corn job and not reliable on thing like that not sure option1, add date only and leave choice for admin to delete or inventory admin, on speacfic action delete the old requests like when logged as system admin or admin display must accept or reject or accept these users or will deleted but that action if not happend no delete and issue still, other option would add that action on new any signup but also may no signup and will delay real signup request with no reason, usally based on goal anything can done other bad soultiom simple corn job using while but will effect performance and sleep not know about its performance as it reduce or leave a hidden c++ or any lang while or for loop 
#     solution other one create simple fast language like c++ that all do is loop and sleep and run corn job use time to async and stop loop after period or if it not save previous, ex simple part 2 options as it app run with while i can use only variables also it faster instead of json file, for example array contain object per task and time run it so sleep1day, check last task in variable could make it async with its time for example if app closed and run but this may go in same way timer or other things have un needed alot thing effect performance so use it will not benfit, simple check if array empty or last time of last corn job 4 or 5 or 6 days so it since app started takes 5 or 6 days keep not save anything maybe permssion some app delete or wrong happend with app and it run without action or loop broken issue if app clear this file every day or user clear the how
# no way done as all variables in direct run app nothing deleted, or files , so do while , run python app.py that act as function as service app as it no flask just python connect to the db and delete the not approved user with date 15
# can walk in many dir, ex block 1 every 1 day run check if speacfic inventory recive high number of pendding users list this as inactive until admin must make it active again so check the numbers of requests as well and if he not the reason of abuse he will reject and delete this users else every day will block the inventory as inactive so not recive may also save number treat from this inventory or precentage for admin this advanced work if it helloworld, and every 15 days remove the first requests until make max 10 for each inventory this fear so less db, and less free usernames for new good users also prevent attack on random guess inventory code even random gues pass of if if it  private
# Step1: max_pendding_pday column of inventory controlled by admin (this number controll how many pendding users per day that not responded by admin for example max 50 pending users without approve for whole day over that number the inventory will listed as inactive and next day if back 50 or less it back active and may block admin of inventory from make it active again so it system and admin only and control if he the abuse, easy admin can make this default 1000000k per day or 50 users as default so no issue, also maybe the admin of inventory himself set this number so he block unsessery requests as he know his size)
# add max number in db of inventory controlled by admin so it based on their pay they have limit and make sure not harm pc and also increase even the performance so no issue most best
# Step2: small corn job or 1 simple task repeated line of code with one of fastest language so it not effect performance while runing do while also not like the timmer or other libraries sure they complex and use save and alot things to make more advanced requirments and complex so 100% this 10c++ lines will be faster alot and performance as nothing run and cheapest than lambda or any other service but require real full stack not hello world full stack reactdeveloper computer full stack is nice term for me 
# c++ app repeat simple run command to "python app.py may better no flask for many reasons" excute python app, that do 2things
# c++1 have variable for time of repeat 1
# c++2 have variable for last execute miliseconds (if everything was good as not need deep check compare time to handle when close c++ and open again as this require now json atleast or txt to update sleep so when it run check last time done and 2 day after that time is the next sleep, when run check last time ex last time was yesterday so it excute task of today and set next time sleep after 2 days from yasterday so it tomrrow right for real accuracy if check last day in found it today so set time only for tomorrow, if yester day 11:59PM and checked at 12:01AM so it will say that tomrrow so nice make speacfic hours and minutes and sec as id of time so if it last time was 11:59PM and user close c++ and run it again at 12:30AM so when started only make that sleep variable fix so it check time of last time 11:59PM and check first if it today or yesterday ->  if yesterday-> check if date is bigger than or equal than 11:30:00PM -> before anything fix the sleep require last day with 1 day -> check i issue we need 2 sleep 1 for remaning sleep and val like normal back sleep                                     and no close this should in next time it loop )
# when open 12:30AM last_sleep=11:30PM   fix required sleep from 12:30AM nextday x 11:30pm-12:30AM current and in while loop normal next sleep will be curn day after 1 day, so before do while fix sleep, if no sleep before so run code 1 time even this sleep before do while nice! no 99 if or yester day and tomorow
# most important noob step setup this noob old lang which should done by helloworld command (hello world runcpp the wisgi no ver) no even need its just python app.py if creator of timer or anyone never make solution for this fast and cheap resources thanthis excpt i searhch noob google and said c++ fast less performance so complier not issue
# better performance and easy work send api request to this flask to run the task as python app.py not easy logicaly also require alot vms and things not neeed also very nice make corn job run from the flask also run only if flask running

    
###### ----- Profile API Keys ----- ######
@main.route('/setup_ourapi', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def setup_ourapi():
    try:
        actions = 0
        form = setupAPIForm()
        if form.validate_on_submit():
            # technique called this variable will exist at end
            ourapi_requests_limit = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_requests_limit').first()
            if not ourapi_requests_limit:
                actions += 1
                default_limit = current_app.config.get('OURAPI_REQUESTS_LIMIT', 100)
                ourapi_requests_limit = UserMeta(user_id=current_user.id, key='ourapi_requests_limit', value=default_limit)
                ourapi_requests_limit.insert()
            
            ourapi_keys_max = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_keys_max').first()
            if not ourapi_keys_max:
                actions += 1
                default_max_keys = current_app.config.get('OURAPI_KEYS_MAX', 10)
                ourapi_keys_max = UserMeta(user_id=current_user.id, key='ourapi_keys_max', value=default_max_keys)
                ourapi_keys_max.insert()

            if actions > 0:
                flash('The API has been set up successfully.', 'success')
            else:
                flash('No changed detected.', 'info')
        else:
            flash('The form has expired, please try again.', 'danger')
    except Exception as e:
        flash('unable to setup the API right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('main.profile', movetocomponent='api'))

@main.route('/add_key', methods=['POST', 'GET'])
@login_required
@vendor_permission.require(http_exception=403)
def add_key():
    try:
        can = user_have_permissions(app_permissions, permissions=['add'])
        if can:
            form = addKeyForm()
            if form.validate_on_submit():
                ourapi_requests_limit = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_requests_limit').first()
                ourapi_keys_max = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_keys_max').first()
                # numbers can be 0 so must check if is not None
                if ourapi_requests_limit is not None and ourapi_keys_max is not None:
                    requests_limit = int(ourapi_requests_limit.value)
                    keys_max = int(ourapi_keys_max.value)
                    current_keys = int(db.session.query(func.count(OurApiKeys.id)).filter(OurApiKeys.user_id==current_user.id).scalar())
                    if current_keys < keys_max:
                        submited_limit = int(form.key_limit.data)
                        #if submited_limit <= 
                        # faster get count of keys
                        
                        # get sum of all keys limit for that user/Allinventory, eg key1 limit, 10, key2 limit 20 so sum he have 30 requests mapped, and remaning is 70
                        keys_requests_sum = 0
                        if current_keys > 0:
                            keys_requests_sum = int(db.session.query(func.sum(OurApiKeys.key_limit)).filter(OurApiKeys.user_id==current_user.id).scalar())
                        
                        
                        remaning_requests = 0
                        # check if sum is lower or equal to user limit and the new key limit submited_limit is less than the remaning requests to be mapped
                        valid_limit = False
                        if (submited_limit <= requests_limit) and (keys_requests_sum <= requests_limit) and (int(requests_limit - keys_requests_sum) >= submited_limit):
                            valid_limit = True

                        if keys_requests_sum <= requests_limit:
                            # avoid get unexcpted nagtive value if declared this var outside if and used in if, it valid result at end but better know every possible value
                            remaning_requests = int(requests_limit - keys_requests_sum)
                            
                        if valid_limit:
                            # save loop with fixed trials to try get unique usally never this value should returned same, as u can see time and secure salat and uuid, but if done which 0.00000048848484848484884848% option i think 10 trials for that is more than good
                            target_key = ''
                            for i in range(10):
                                target_key = generate_ourapi_key(bcrypt)
                                if target_key:
                                    # note the key like multiple user id so must be unique
                                    key_exist = OurApiKeys.query.filter_by(key=target_key).first()
                                    if not key_exist:
                                        # key is unique now
                                        break
                                    else:
                                        continue
                                else:
                                    break
                            if target_key:
                                new_key = OurApiKeys(user_id=current_user.id, key=target_key, key_limit=submited_limit, expiration_date=form.expiration_date.data)
                                new_key.insert()
                                create_log(user=current_user, category=LogsCategories.api_key.value, action=LogsActions.create.value, action_ids=[new_key.id])
                                flash('Successfully added new key.', 'success')
                            else:
                                flash("Unable to generate a valid key now, please try again.", 'danger')
                        else:
                            flash('Invalid key limit sent, maximum number of new key requests allowed is {}.'.format(remaning_requests), 'danger')
                    else:
                        flash("Can\'t add a new key, you have exceeded your limit", 'danger')
                else:
                    flash('The API is not set up yet, please set it up first and then try adding a new key.', 'danger')
            else:
                flash('The form has expired, please try again.', 'danger')
        else:
            flash('You do not have permissions to add API key.', 'danger')
    except Exception as e:
        flash('unable to add new key right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))

    finally:
        return redirect(url_for('main.profile', movetocomponent='api'))


# note this means user will not able to delete API keys he added right now only admin or role in future with delete and its vendor
@main.route('/remove_key/<int:id>', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def remove_key(id):
    try:
        # we can both outside and inside as nothing in expction can lead to leak of permssions but incase there is so must be outside like it wraper
        can = user_have_permissions(app_permissions, permissions=['delete'])
        if can:
            form = removeKeyForm()
            if form.validate_on_submit():
                # both secuirty confirm and check if key exist
                key_exist = OurApiKeys.query.filter_by(id=id, user_id=current_user.id).one_or_none()
                if key_exist is not None:
                    key_exist.delete()
                    create_log(user=current_user, category=LogsCategories.api_key.value, action=LogsActions.delete.value, action_ids=[id])
                    flash('Successfully deleted key with id:{}.'.format(id), 'success')
                else:
                    flash('Key not found', 'danger')
            else:
                flash('The form has expired, please try again.', 'danger')
        else:
            flash('You do not have permissions to delete API key.', 'danger')
    except Exception as e:
        flash('unable to delete key right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('main.profile', movetocomponent='api'))


@main.route('/update_key/<int:id>', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def update_key(id):
    try:
        can = user_have_permissions(app_permissions, permissions=['update'])
        if can:
            form = updateKeyForm()
            if form.validate_on_submit():
                changes = 0
                submited_limit = int(form.update_key_limit.data)
                selected_key = OurApiKeys.query.filter_by(id=id, user_id=current_user.id).one_or_none()
                if selected_key is not None:
                    ourapi_requests_limit = UserMeta.query.filter_by(user_id=current_user.id, key='ourapi_requests_limit').first()
                    if ourapi_requests_limit:
                        if form.expiration_date.data != selected_key.expiration_date:
                            selected_key.expiration_date = form.expiration_date.data
                            changes += 1

                        valid_limit = False
                        limit_changed = False
                        if int(selected_key.key_limit) != submited_limit:    
                                limit_changed = True

                                requests_limit = int(ourapi_requests_limit.value)

                                # sum of all except the key will updated now that do alot of calc fix
                                keys_requests_sum = db.session.query(func.sum(OurApiKeys.key_limit)).filter(OurApiKeys.id != id, OurApiKeys.user_id==current_user.id).scalar()
                                if keys_requests_sum is None:
                                    keys_requests_sum = 0
                                else:
                                    keys_requests_sum = int(keys_requests_sum)

                                remaning_requests = 0
                                if (submited_limit <= requests_limit) and (keys_requests_sum <= requests_limit) and (int(requests_limit-keys_requests_sum) >= submited_limit):
                                    valid_limit = True

                                if keys_requests_sum <= requests_limit:
                                    remaning_requests = int(requests_limit-keys_requests_sum)

                                if valid_limit:
                                    selected_key.key_limit = submited_limit
                                    changes += 1
                                    

                        if limit_changed and not valid_limit:
                            # limit changed, but invalid limit, so no update done
                            flash('Invalid key limit sent, maximum number of key requests allowed is {}.'.format(remaning_requests), 'danger')
                        elif changes > 0:
                            # limit maybe changed, and if it changed it valid limit, so update done, if limit_changed = false so it come here so if only date changed it update as well or any new val
                            selected_key.update()
                            create_log(user=current_user, category=LogsCategories.api_key.value, action=LogsActions.update.value, action_ids=[selected_key.id])
                            flash('Successfully updated key with id:{}.'.format(id), 'success')
                        else:
                            flash('No changed detected.', 'info')

                    else:
                        flash('API not setup, please re-setup it.', 'danger')
                else:
                    flash('Key not found', 'danger')
            else:
                message = ','.join(['{}:{}'.format(label, ','.join(errors)) if label != 'csrf_token' else 'System: The form has expired, please try again.' for label, errors in form.errors.items()])
                message = message if message else 'Unknown error Please try again.'
                flash(message, 'danger')
        else:
            flash('You do not have permissions to update API key.', 'danger')
    except Exception as e:
        flash('unable to update key right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))
    finally:
        return redirect(url_for('main.profile', movetocomponent='api'))



@main.route('/renew_key/<int:id>', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def renew_key(id):
    try:
        form = renewKeyForm()
        if form.validate_on_submit():
            # both secuirty confirm and check if key exist
            key_exist = OurApiKeys.query.filter_by(id=id, user_id=current_user.id).one_or_none()
            if key_exist is not None:
                target_key = ''
                for i in range(10):
                    target_key = generate_ourapi_key(bcrypt)
                    if target_key:
                        # note the key like multiple user id so must be unique per all users
                        key_exist_db = OurApiKeys.query.filter_by(key=target_key).first()
                        if not key_exist_db:
                            # key is unique now
                            break
                        else:
                            continue
                    else:
                        break
                if target_key:
                    key_exist.key = target_key
                    now = datetime.utcnow()
                    # use last expiration date used in last update or when inserted if no updates, to be consider
                    if key_exist.expiration_seconds > float(0):
                        key_exist.expiration_date = now + timedelta(seconds=int(key_exist.expiration_seconds))
                    else:
                        key_exist.expiration_date = now + relativedelta(months=+1)
                        
                    key_exist.update()
                    create_log(user=current_user, category=LogsCategories.api_key.value, action=LogsActions.update.value, action_ids=[key_exist.id])
                    flash('Successfully renew the key with id:({}).'.format(id), 'success')
                else:
                    flash("Unable to renew the key with id:({}), Please try again.".format(id), 'danger')
            else:
                flash('Key not found', 'danger')
        else:
            flash('The form has expired, please try again.', 'danger')
    except Exception as e:
        flash('unable to renew key right now.', 'danger')
        print('system error {}'.format(sys.exc_info()))

    finally:
        return redirect(url_for('main.profile', movetocomponent='api'))
    

# activity Logs
@main.route('/activity_logs', methods=['POST'])
@login_required
@vendor_permission.require(http_exception=403)
def activity_logs():
    res = {}
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            limit = 50
            data = request.get_json()
            categories = data['filters']['categories'] if isinstance(data, dict) and 'filters' in data and 'categories' in data['filters'] else None
            minid = data['minId'] if isinstance(data, dict) and 'minId' in data else None
            maxid = data['maxId'] if isinstance(data, dict) and 'maxId' in data else None
            if isinstance(categories, list) and isinstance(minid, int) and isinstance(maxid, int):
                query = None
                total_query = None
                if 'all' in categories:
                    query = db.session.query(Logs).filter(Logs.user_id==current_user.id, not_(Logs.id.between(minid, maxid))).order_by(desc(Logs.id))
                    total_query = db.session.query(func.count(Logs.id)).filter(Logs.user_id==current_user.id)
                else:
                    query = db.session.query(Logs).filter(Logs.user_id==current_user.id, Logs.category.in_(categories), not_(Logs.id.between(minid, maxid)))
                    total_query = db.session.query(func.count(Logs.id)).filter(Logs.user_id==current_user.id, Logs.category.in_(categories))

                res['data'] = [{'id': log.id, 'content': log.message} for log in query.order_by(desc(Logs.id)).limit(limit).all()]
                res['total'] = total_query.scalar()
                res['code'] = 200
            else:
                res = {'code': 400, 'message': 'Unable to process your request.'}
        else:
            res = {'code': 400, 'message': 'You have no premssions to access data.'}
    except:
        print("error from activity_logs: {}".format(sys.exc_info()))
        res = {'code': 500, 'message': 'Unable to load data system error.'}
    finally:
        return jsonify(res)

@main.route('/activity_logs_invadmin', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def activity_logs_invadmin():
    res = {}
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            limit = 50
            data = request.get_json()
            categories = data['filters']['categories'] if isinstance(data, dict) and 'filters' in data and 'categories' in data['filters'] else None
            users = data['filters']['users'] if isinstance(data, dict) and 'filters' in data and 'users' in data['filters'] else None
            minid = data['minId'] if isinstance(data, dict) and 'minId' in data else None
            maxid = data['maxId'] if isinstance(data, dict) and 'maxId' in data else None
            if isinstance(categories, list) and isinstance(users, list) and isinstance(minid, int) and isinstance(maxid, int):
                # secuirty
                invadmin_users = [uidt[0] for uidt in db.session.query(User.id).join(Inventory, User.inventory_id==Inventory.id).filter(Inventory.added_by==current_user.id).all()]
                allowed_users = []
                for uid in users:
                    if uid in invadmin_users:
                        allowed_users.append(uid)
                
                queries = get_logs_queries(db, categories, allowed_users, minid, maxid)
                res['data'] = [{'id': log.id, 'content': log.message} for log in inv(queries['query'], User.id, Logs.user_id).order_by(desc(Logs.id)).limit(limit).all()]
                res['total'] = inv(queries['total_query'], User.id, Logs.user_id).scalar()
                res['code'] = 200
            else:
                res = {'code': 400, 'message': 'Unable to process your request.'}
        else:
            res = {'code': 400, 'message': 'You have no premssions to access data.'}
    except:
        print("error from activity_logs_admin: {}".format(sys.exc_info()))
        res = {'code': 500, 'message': 'Unable to load data system error.'}
    finally:
        return jsonify(res)

@main.route('/activity_logs_admin', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def activity_logs_admin():
    res = {}
    # 2 options 1- asc order the new added will be at end so offset has no issue if new items added after load all data, option 2 send all loaded ids and exculde it in query but when done found query string have limit and even not reached 199 ids so not good solution even if big dbsettings large data will get issue, option 3 (done) Use Not Between min loaded id AND max loaded id always get what between but in my target not between usally it will target in issue case the after but even within the load for example new items added within 50% only this case will get before and after then get offset (done) also if 0 items NOT BETWEEN 0 AND 0 has no issue and performance solution not only friendly (note while i solve issue i removed offset as no offset needed now) also small note it logical always between start with min and max
    try:
        can = user_have_permissions(app_permissions, permissions=['read'])
        if can:
            limit = 50
            data = request.get_json()
            categories = data['filters']['categories'] if isinstance(data, dict) and 'filters' in data and 'categories' in data['filters'] else None
            users = data['filters']['users'] if isinstance(data, dict) and 'filters' in data and 'users' in data['filters'] else None
            minid = data['minId'] if isinstance(data, dict) and 'minId' in data else None
            maxid = data['maxId'] if isinstance(data, dict) and 'maxId' in data else None
            if isinstance(categories, list) and isinstance(users, list) and isinstance(minid, int) and isinstance(maxid, int):
                queries = get_logs_queries(db, categories, users, minid, maxid)
                res['data'] = [{'id': log.id, 'content': log.message} for log in queries['query'].order_by(desc(Logs.id)).limit(limit).all()]
                res['total'] = queries['total_query'].scalar()
                res['code'] = 200
            else:
                res = {'code': 400, 'message': 'Unable to process your request.'}
        else:
            res = {'code': 400, 'message': 'You have no premssions to access data.'}
    except:
        print("error from activity_logs_admin: {}".format(sys.exc_info()))
        res = {'code': 500, 'message': 'Unable to load data system error'}
    finally:
        return jsonify(res)


@main.route('/delete_log_invadmin', methods=['POST'])
@login_required
@inventory_admin_permission.require(http_exception=403)
def delete_log_invadmin():
    res = {}
    try:
        can = user_have_permissions(app_permissions, permissions=['delete'])
        if can:
            data = request.get_json()
            log_id = data['id'] if isinstance(data, dict) and 'id' in data else None
            if isinstance(log_id, int):
                log = Logs.query.filter_by(id=log_id).one_or_none()
                # secuirty
                if log is not None:
                    invadmin_users = [uidt[0] for uidt in db.session.query(User.id).join(Inventory, User.inventory_id==Inventory.id).filter(Inventory.added_by==current_user.id).all()]
                    if log.user_id in invadmin_users:
                        # res_logid (risk cover not send what client sent to you (injections))
                        message = 'successfully deleted log with id: {}'.format(log.id)
                        log.delete()
                        res = {'code': 200, 'message': message}
                    else:
                        res = {'code': 403, 'message': 'You have no premssions to manage logs for that user or user not exist.'}
                else:
                    res = {'code': 404, 'message': 'Unable to delete the log is not found, please restart the page and try again.'}
            else:
                res = {'code': 400, 'message': 'Unable to process your request.'}
        else:
            res = {'code': 400, 'message': 'You have no premssions to delete data.'}
    except:
        print("error from delete_log_invadmin: {}".format(sys.exc_info()))
        res = {'code': 500, 'message': 'Unable to delete log system error.'}
    finally:
        return jsonify(res)


@main.route('/delete_log_admin', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_log_admin():
    res = {}
    try:
        can = user_have_permissions(app_permissions, permissions=['delete'])
        if can:
            data = request.get_json()
            log_id = data['id'] if isinstance(data, dict) and 'id' in data else None
            if isinstance(log_id, int):
                log = Logs.query.filter_by(id=log_id).one_or_none()
                if log is not None:
                    message = 'successfully deleted log with id: {}'.format(log.id)
                    log.delete()
                    res = {'code': 200, 'message': message}
                else:
                    res = {'code': 404, 'message': 'Unable to delete the log is not found, please restart the page and try again.'}
            else:
                res = {'code': 400, 'message': 'Unable to process your request. {}'.format(log_id)}
        else:
            res = {'code': 400, 'message': 'You have no premssions to delete data.'}
    except:
        print("error from delete_log_admin: {}".format(sys.exc_info()))
        res = {'code': 500, 'message': 'Unable to delete log system error'}
    finally:
        return jsonify(res)
