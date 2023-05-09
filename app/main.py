import json
import sys
import os
from flask import Flask, Blueprint, session, redirect, url_for, flash, Response, request, render_template, jsonify, Request
from .models import User, Dashboard, Catalogue, Listing
from .forms import CatalogueExcelForm, defaultDashboardForm
from . import vendor_permission, admin_permission, db, excel
from .functions import get_mapped_catalogues_dicts
from flask_login import login_required, current_user
import flask_excel
import pyexcel
#from app import excel


main = Blueprint('main', __name__, template_folder='templates', static_folder='static')


# this bridge route to redirect to the default dashboard if any else it return to dashboards page to let user create new dashboard, and it will set as default by default
@main.route('/home', methods=['GET'])
@login_required
@vendor_permission.require()
def home():
    default_dashboard = None
    try:
        default_dashboard = Dashboard.query.filter_by(default=True, user_id=current_user.id).first()
    except Exception as e:
        print('System Error home: {} , info: {}'.format(e, sys.exc_info()))
    finally:
        if default_dashboard is not None:
            return redirect(url_for('routes.view_dashboard', dashboard_id=default_dashboard.id))
        else:
            flash('Unable To find the Default Dashboard, Please Add New Dashboard', 'info')
            return redirect(url_for('routes.index'))



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
            # convert flask_excel request.get_array to mapped db rows dicts with same name of sqlalchemy class **
            # this simpler and more professional than request.save_to_database  and clear add or not add this row
            imported_rows = request.get_array(field_name='excel_file')
            
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

                    if db_row['sku'] not in uploaded_skus:
                        try:
                            
                            catalogue_exist = Catalogue.query.filter_by(sku=db_row['sku']).first()
                            #return str(catalogue_exist)

                            if catalogue_exist:
                                # daynmic update existing catalogue data with new imported
                                for key, value in db_row.items():
                                    setattr(catalogue_exist, key, value)
                                    catalogue_exist.update()
                            else:
                                newCatalogue = Catalogue(user_id=current_user.id, **db_row)
                                newCatalogue.insert()

                            uploaded_skus.append(db_row['sku'])

                        except Exception as e:
                            # if error it broke the next rows rollback and continue
                            db.session.rollback()
                            print('System Error row ignored, import_catalogues_excel : {} , info: {}'.format(e, sys.exc_info()))
                            invalid_rows.append(str(row_index+1))
                            continue
                    else:
                        duplicated_skus.append(str)
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
        print('System Error import_catalogues_excel: {} , info: {}'.format(e, sys.exc_info()))
        message = 'Unable to import excel data please try again later'
        success = False 
        raise e
    
    finally:
        status = 'success' if success else 'danger'
        flash(message, status)
        return redirect(url_for('routes.catalogues'))
    
# export listing
@main.route('/export_listings/<string:dashboard_id>', methods=['GET'])
@login_required
@vendor_permission.require()
def listing_export(dashboard_id):
    try:
        selected_listings = db.session.query(Listing).join(Dashboard).filter(Listing.dashboard_id==dashboard_id, Dashboard.user_id==current_user.id).all()
        # this do 2 things, incase there are no data error may raised, also for performance as there no data no need call this heavy function
        if selected_listings:
            column_names = Listing.__table__.columns.keys()
            # column_names also used to exclude names for example you may not need id, so if not provided will not exported
            excel_response = flask_excel.make_response_from_query_sets(selected_listings, column_names, 'csv', file_name='inventory_listings')
            return excel_response
        else:
            flash('There is no data to be exported.', 'warning')
            return redirect(url_for('routes.view_dashboard', dashboard_id=dashboard_id))
    except Exception as e:
        # redirect used to display the flash message incase of error , becuase this GET request and it processed in the same rendered page (so flash can not displayed without refresh)
        print('System Error listing_export: {} , info: {}'.format(e, sys.exc_info()))
        flash('Unknown error Your request could not be processed right now, please try again later.', 'danger')
        return redirect(url_for('routes.view_dashboard', dashboard_id=dashboard_id))

# make dashboard default
@main.route('/default_dashboard/<string:dashboard_id>', methods=['POST'])
@login_required
@vendor_permission.require()
def set_default_dashboard(dashboard_id):
    message = ''
    success = False
    try:
        default_form = defaultDashboardForm()
        if default_form.validate_on_submit():
            selected_dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).one_or_none()
            if selected_dashboard is not None:
                # it always will be 1 default dashboard, but this action can fix the app if more than dashboard seleected by db or somethign
                default_dashboards = Dashboard.query.filter_by(default=True, user_id=current_user.id).all()
                for default_bashboard in default_dashboards:
                    default_bashboard.default = False
                    default_bashboard.update()
                # update selected dashboard default status
                selected_dashboard.default = True
                selected_dashboard.update()
                message = 'Dashboard with ID: {} has been successfully set as the default dashboard.'.format(dashboard_id)
                success = True
            else:
                message = 'The specified dashboard was not found, it may have been deleted.'
                success = False
        else:
            message = 'Unable to process your Request.'
            success = False   
    except Exception as e:
        print('System Error set_default_dashboard: {} , info: {}'.format(e, sys.exc_info()))
        message = 'Unknown error Your request could not be processed right now, please try again later.'
        success = False
    finally:
        message_status = 'success' if success else 'danger'
        flash(message, message_status)
        return redirect(url_for('routes.index'))


@main.route('/reports_tool', methods=['POST', 'GET'])
@login_required
@admin_permission.require()
def reports_tool():
    from sqlalchemy.inspection import inspect
    thing_relations = inspect(User).relationships.items()

    #return str(thing_relations)
    return render_template('admin/reports_tool.html')