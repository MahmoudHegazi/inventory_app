import json
import sys
import os
from flask import Flask, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify, Request
from .models import *
from .forms import CatalogueExcelForm, ExportDataForm
from . import vendor_permission, admin_permission, db, excel
from .functions import get_mapped_catalogues_dicts, getTableColumns, getFilterBooleanClauseList, ExportSqlalchemyFilter, get_export_data, get_charts, get_excel_rows, get_sheet_row_locations
from flask_login import login_required, current_user
import flask_excel
import pyexcel
from sqlalchemy import or_, and_, func , asc, desc, text
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
@admin_permission.require()
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
@admin_permission.require()
def reports_export():
    message = ''
    success = True
    excel_response = None
    data = []
    column_names = []
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


