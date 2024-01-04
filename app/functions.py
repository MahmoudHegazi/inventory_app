import sys
import os
import re
import datetime
import math
import time
import requests
import json
import re
import secrets
import validators
from dateutil import parser
from urllib.parse import urlparse, urljoin
from flask import request, current_app, url_for
from flask_login import current_user
from sqlalchemy import func
from .models import Supplier, Dashboard, Listing, Catalogue, Purchase, Order, Platform, CatalogueLocations, CatalogueLocationsBins,\
    WarehouseLocations, LocationBins, Category, UserMeta, OrderTaxes, Condition, OurApiKeys, ApiKeysLogs
from sqlalchemy.sql import extract
from sqlalchemy import or_, and_, func , asc, desc
from datetime import datetime, timedelta
from uuid import uuid4


def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )

def get_safe_redirect(url=''):
    if url and is_safe_redirect_url(url):
        return url
    return ''



#### main functions ####
def valid_catalogues(excel_array):
    try:
        required_columns = [
        "sku","product_name","product_description","brand","category_code","category","price","sale_price","quantity","product_model","condition","upc", "location"]
        columns_missing = []
        if len(excel_array) == 0:
            return {'success': True, 'message': ''}
        
        headears = excel_array[0]
        for required_column in required_columns:
            required_column = str(required_column).strip().lower()
            if required_column not in headears:
                columns_missing.append(required_column)
                message = 'Missing one or more required columns: {}'.format(','.join(columns_missing))
                return {'success': False, 'message': message}
        
        arrays_len = len(headears)
        for row in excel_array:
            if len(row) != arrays_len:
                message = 'one or more headings are misssing, please make sure all columns have a title no matter if there additional column, only every column must have a title'
                return {'success': False, 'message': message}
        
        return {'success': True, 'message': ''}
    except Exception as e:
        print('System Error valid_catalogues: {}'.format(sys.exc_info()))
        raise e
    
#{ "sku",  "product_name",  "product_description",  "brand",  "category_code",  "price",  "sale_price",  "quantity",  "product_model",  "condition",  "upc",  "location", }
def get_mapped_catalogues_dicts(excel_array):
    try:
        catalogues_valid = valid_catalogues(excel_array)
        if catalogues_valid['success']:
            # valid catagories confirms there must be this keys so no key must be -1 after the first row in loop
            catalogues_columns = {
            "sku": -1, 
            "product_name": -1, 
            "product_description": -1, 
            "brand": -1, 
            "category_code": -1,
            "category": -1,
            "price": -1, 
            "sale_price": -1, 
            "quantity": -1, 
            "product_model": -1, 
            "condition": -1, 
            "upc": -1,
            "location": -1
            }
            
            db_rows = []
            db_rows_locations = []
            db_rows_bins = []
            for i in range(len(excel_array)):
                current_row = excel_array[i]
                if i == 0:
                    # headings
                    for headingIndex in range(len(current_row)):
                        heading = str(current_row[headingIndex]).strip().lower()
                        if heading in catalogues_columns:
                            catalogues_columns[heading] = headingIndex
                            continue
                else:
                    price_type = type(current_row[catalogues_columns['price']])
                    sale_price_type = type(current_row[catalogues_columns['sale_price']])
                    
                    price_n = current_row[catalogues_columns['price']] if price_type is float or price_type is int else 0.00
                    sale_price_n = current_row[catalogues_columns['sale_price']] if sale_price_type is float or sale_price_type is int else 0.00 

                    """ fastest way can done to convert get_array to db sqlalchemy objects,index (dynamic mapping) by client's excel file uploaded, sku title in first column or in last ignore additonal columns for flexiblty just 1 loop (validation for ux) """
                    db_row = {
                    "sku": current_row[catalogues_columns['sku']], 
                    "product_name": current_row[catalogues_columns['product_name']], 
                    "product_description": current_row[catalogues_columns['product_description']], 
                    "brand": current_row[catalogues_columns['brand']], 
                    "category_code": current_row[catalogues_columns['category_code']],
                    "category": current_row[catalogues_columns['category']],
                    "price": price_n, 
                    "sale_price": sale_price_n, 
                    "quantity": current_row[catalogues_columns['quantity']], 
                    "product_model": current_row[catalogues_columns['product_model']], 
                    "condition": current_row[catalogues_columns['condition']], 
                    "upc": current_row[catalogues_columns['upc']]
                    }
                    db_rows.append(db_row)
                    # location relational data array
                    db_rows_locations.append(current_row[catalogues_columns['location']])
                    
            return {'success': True, 'message': '', 'db_rows': db_rows, 'db_rows_locations': db_rows_locations}
        else:
            return catalogues_valid
           
    except Exception as e:
        print('System Error get_mapped_catalogues_dicts: {}'.format(sys.exc_info()))
        raise e

def updateDashboardListings(user_dashboard):
    # +1 and -1 has no way to be fixed and not synced, this way do what +1 and -1 do and it will fix incase indexing broken
    try:
        if user_dashboard:
            user_dashboard.num_of_listings = len(user_dashboard.listings)
            user_dashboard.update()
            return user_dashboard.num_of_listings
        else:
            return False
    except Exception as e:
        print('System Error updateDashboardListings: {}'.format(sys.exc_info()))
        raise e
    


def updateDashboardOrders(db, user_dashboard):
    try:
        # updated could be order_estate != 'refunded,etc'
        total_dashboard_orders = db.session.query(
                    func.sum(Order.quantity)
                ).join(
                    Listing
                ).filter(
                    Listing.dashboard_id == user_dashboard.id,
                ).scalar()
        user_dashboard.num_of_orders = total_dashboard_orders
        user_dashboard.update()
        return total_dashboard_orders
    except Exception as e:
        print('System Error updateDashboardOrders: {}'.format(sys.exc_info()))
        raise e

def updateDashboardPurchasesSum(db, Purchase, Listing, user_dashboard):
    try:
        sum_dashboard_purchases = db.session.query(
                    func.sum((Purchase.quantity*Listing.price))
                ).join(
                    Listing
                ).filter(
                    Listing.dashboard_id == user_dashboard.id,
                ).scalar()
        user_dashboard.sum_of_monthly_purchases = sum_dashboard_purchases
        user_dashboard.update()
        return sum_dashboard_purchases
    except Exception as e:
        print('System Error updateDashboardPurchasesSum: {}'.format(sys.exc_info()))
        raise e

def getAllowedColumns(column_names=[], ignored_columns=[]):
    result = []
    try:
        for column_name in column_names:
            if column_name not in ignored_columns:
                result.append(column_name)
        return result
    except Exception as e:
        raise e
    
def getTableColumns(tableClass, expetColumns=[]):
    try:
        ignoredIndexes = []
        result = []
        table_name = tableClass.__tablename__.capitalize()
        columns = ['{}.{}'.format(table_name, col) for col in tableClass.__table__.columns.keys()]
        # remove unwanted column names
        for except_col in expetColumns:
            for col_index in range(len(columns)):
                colsplited = columns[col_index].split('.')
                valid_col = True
                for col_part in colsplited:
                    if except_col == col_part:
                        valid_col = False
                if valid_col == False and col_index not in ignoredIndexes:
                    ignoredIndexes.append(col_index)
        """
        if returnClass == True:
            columns = tableClass.__table__.columns
            raise 'error'
        """
        for i in range(len(columns)):
            if i not in ignoredIndexes:
                result.append(columns[i])

        return result
    except Exception as e:
        print('System Error getTableColumns: {}'.format(sys.exc_info()))
        raise (e)
    
def secureRedirect(redirect_url):
    try:
        allowed_redirect = [
            url_for('routes.index'),
            url_for('routes.orders'),
            url_for('routes.listings'),
            url_for('routes.catalogues'),
            url_for('routes.suppliers'),
            url_for('main.reports'),
            url_for('routes.setup')
            ]
        # to set how it works try  set redirect url to /catalogue/3808/edit remaning will not be the ids (note as urls parent relation child so this check works for listings or orders as orders is inhirted from
        lambdas = [
            redirect_url if str(redirect_url).startswith('/') and str(str(''.join(str(''.join(redirect_url.split('/listings'))).split('/orders'))).replace('/', '')).isnumeric() else False
        ]

        for rul in range(len(allowed_redirect)):
            if str(allowed_redirect[rul]).lower() == str(redirect_url).lower():
                return allowed_redirect[rul]
        
        for alambda_string in lambdas:
            if alambda_string:
                return redirect_url
          
    except Exception as e:
        raise e
        print("error in secureRedirect: {}".format(sys.exc_info()))

    return '/home'

"""  Filter Class and its function (this class access direct functions deacleard in functions.py) (this can used for both act as API to export system data with any dynamic column name as query paramter or as main export csv both code already done) """
class ExportSqlalchemyFilter():
    # user sqlalchemy to create secure sqlalchemy filters arugments list (controlled easy)
    supplier_columns = []
    catalogue_columns = []
    listing_columns = []
    purchase_columns = []
    order_columns = []
    platform_columns = []

    catalogue_table_filters = []
    listing_table_filters = []
    purchase_table_filters = []
    order_table_filters = []
    supplier_table_filters = []
    platform_table_filters = []
    allowed_tables = {}
    tables_data = {}
    opeartors = ['=', '!=', '>', '<', '>=', '<=', 'val%', '%val', '%val%']
    
    def __init__(self):
        self.catalogue_columns = getTableColumns(Catalogue, ['user_id', 'product_image'])
        self.listing_columns = getTableColumns(Listing, expetColumns=['image', 'platform', 'dashboard_id'])
        self.purchase_columns = getTableColumns(Purchase)
        self.order_columns = getTableColumns(Order)
        self.supplier_columns = getTableColumns(Supplier, ['user_id'])
        self.platform_columns = getTableColumns(Platform, ['dashboard_id'])        
        
        # locations tables (now it can used by vistors only not admin or developer or tester (tool can modifed for testing and anlaysis app))
        self.warehouse_locations_columns = getTableColumns(WarehouseLocations, ['id', 'dashboard_id', 'created_date', 'updated_date'])
        self.location_bins_columns = getTableColumns(LocationBins, ['id', 'location_id', 'created_date', 'updated_date'])

        self.catalogue_locations_columns = getTableColumns(CatalogueLocations, ['id', 'created_date', 'updated_date', 'catalogue_id', 'location_id'])
        self.catalogue_locations_bins_columns = getTableColumns(CatalogueLocationsBins, ['id', 'created_date', 'updated_date', 'location_id', 'bin_id'])

        self.categories_columns = getTableColumns(Category, ['dashboard_id', 'created_date', 'updated_date'])
        self.conditions_columns = getTableColumns(Condition, ['dashboard_id', 'created_date', 'updated_date'])
        self.ordertaxes_columns = getTableColumns(OrderTaxes, ['id', 'created_date', 'updated_date'])

        # rendered with same order in js (filters_args_list ...(args))  (can change order of display in frontend)
        catalogue_table_filters = [
            *self.catalogue_columns,
            *self.warehouse_locations_columns,
            *self.location_bins_columns,
            *self.catalogue_locations_columns,
            *self.catalogue_locations_bins_columns,
            *self.categories_columns,
            *self.conditions_columns
            ]
        # call function here becuase i need custom ignored duplicated columns in Catalogue not the default (changed that for make test way for user without code, he can validate if catalogues data not changed) (actions done by event listeners)
        listing_table_filters = [
            *self.listing_columns,
            *self.catalogue_columns,
            *self.platform_columns,
            *self.warehouse_locations_columns,
            *self.location_bins_columns,
            *self.catalogue_locations_columns,
            *self.catalogue_locations_bins_columns,
            *self.categories_columns,
            *self.ordertaxes_columns,
            *self.conditions_columns
            ]
        # *getTableColumns(Catalogue, ['user_id', 'sku', 'product_name', 'product_description', 'brand', 'category_code', 'price', 'sale_price', 'quantity'])
        purchase_table_filters = [*self.purchase_columns, *self.supplier_columns, *self.listing_columns, *self.catalogue_columns]
        order_table_filters = [*self.order_columns, *self.listing_columns, *self.catalogue_columns]
        supplier_table_filters = [*self.supplier_columns]
        platform_table_filters = [*self.platform_columns]

        # each export button have predefined group of allowed tables, can controled from here
        self.allowed_tables = {
            'catalogue': [Catalogue, WarehouseLocations, LocationBins, CatalogueLocations, CatalogueLocationsBins, Category, Condition],
            'listing': [Listing, Catalogue, Platform, WarehouseLocations, LocationBins, CatalogueLocations, CatalogueLocationsBins, Category, OrderTaxes, Condition],
            'purchase': [Purchase, Supplier, Listing, Catalogue],
            'order': [Order, Listing, Catalogue],
            'supplier': [Supplier]
        }

        # all posible columns can used in filter acording also to allowed
        self.tables_data = {
            'catalogue': catalogue_table_filters,
            'listing': listing_table_filters,
            'purchase': purchase_table_filters,
            'order': order_table_filters,
            'supplier': supplier_table_filters,
            'platform': platform_table_filters
        }   

    def getSqlalchemyClassByName(self, classname, target_table):
        # encryption of name can happend here
        try:
            target_class = None
            
            # (secure) validate if table class included in filter conidtions provided, example (purchase.id, supplier.id) but not supplier.user_id (vailidate recived column_name in allowed columns for current query) (each export button has group of allowed tables not allowed user to modify table names even if it works in other button, like order in listing or new way user create)
            table_classes = self.allowed_tables[target_table] if target_table in self.allowed_tables else None
            if table_classes is None:
                # secuirty
                raise ValueError('Unknown Table error')
            
            for table_class in table_classes:
                 table_name = table_class.__tablename__.capitalize()
                 if table_name == classname:
                     target_class = table_class
                     break

            # all provided columns and tables must be vaild and renewed with ajax incase given class not found in alllowed some one try change inspect and provid unallowed table like user
            if target_class is None:
                raise ValueError('invalid table asked to exported')
        except Exception as e:
            print('error in getSqlalchemyClassByName, {}'.format(sys.exc_info()))
            raise e
        return target_class
    
    # fixed work around the group of button opened (secuirty only not logic)
    def getSqlalchemyColumnByName(self, colname, table_name, target_table):
        target_column = None
        try:
            table_class = self.getSqlalchemyClassByName(table_name, target_table)
            if not table_class:
                raise ValueError('found unknown table')
            
            # column_full_name = 'Supplier.user_id' # secuirty check
            column_full_name = '{}.{}'.format(table_name, colname)
            # check if Table.colname provided exist current table filters allowed option provided when init this class (work around target_table selected to exported not the searched one which is part of join query)
            secuirty_check = column_full_name in self.tables_data[target_table]
            if not secuirty_check:
                # secuirty
                raise ValueError('invalid column provided')
            

            # handle each table ignore columns speartly most secure only given excuted else error
            for sqlalchemy_column in table_class.__table__.columns:
                if sqlalchemy_column.name == colname:                    
                    target_column = sqlalchemy_column
                
            if target_column is None:
                raise ValueError('column not found')
            
        except Exception as e:
            print('error in getSqlalchemyColumnByName, {}'.format(sys.exc_info()))
            raise e
        
        return target_column

    def createSqlalchemyConidtion(self, column_class, operator, value):
                
        opeartors = ['=', '!=', '>', '<', '>=', '<=', 'val%', '%val', '%val%']

        condition = False
        if operator not in opeartors:
            # always raise refere to secuirty issue or code issue, operators sent to form are in this array
            raise 'invalid operator found'
        # filter calc options text search (is basically case-insensitive, with no option for case-sensitive search)
        if operator == '=':
            column_class = func.lower(column_class) == func.lower(value)

        elif operator == '!=':
            column_class = column_class != value

        elif operator == '>':
            column_class = column_class > value

        elif operator == '<':
            column_class = column_class < value

        elif operator == '>=':
            column_class = column_class >= value

        elif operator == '<=':
            column_class = column_class <= value

        elif operator == 'val%':
            search = f'{value}%'
            column_class = column_class.like(search)

        elif operator == '%val':
            search = f'%{value}'
            column_class = column_class.like(search)

        else:
            # based on condition if operator not in opeartors this else must only %val% as all previous covered
            search = f'%{value}%'
            column_class = column_class.like(search)
        return column_class

# this most secure export filter no sql full sqlalchemy+full dynamic uses sqlalchmy core classes 
def getFilterBooleanClauseList(columns, operators, values, condition, target_table):
    try:
        # validate equal lists (3 lists have same length, check columns with operators must equal length, and also columns which equal to operators with values must equals, so operators and values equal)
        if len(columns) != len(operators) or len(columns) != len(values):
            raise ValueError('Submited not equal inputs')
        
        export_sqlalchemy = ExportSqlalchemyFilter()
        
        expertion_tuple = ()
        for col in range(len(columns)):
            column = columns[col]
            operator = operators[col]
            value = values[col]
            # any column must have parent.column
            if '.' in column:
                column_data = str(column).split('.')
                table_name = column_data[0]
                column_name = column_data[1]

                # securely get table column
                column_class = export_sqlalchemy.getSqlalchemyColumnByName(column_name, table_name, target_table)

                # add new binary expertion 'sqlalchemy.sql.elements.binaryexpression'
                sqlalchemy_binaryexpression = export_sqlalchemy.createSqlalchemyConidtion(column_class, operator, value)

                expertion_tuple = (sqlalchemy_binaryexpression,*expertion_tuple)
                
        # all done is by sqlalchemy, and_,or_ sqlalchemy's functions and return list of expertion 'sqlalchemy.sql.elements.booleanclauselist', can passed direct to filter (this way performance friendly) and,or set one time at end
        filterBooleanClauseList = or_(*expertion_tuple) if condition == 'or' else and_(*expertion_tuple)
        return filterBooleanClauseList
    except Exception as e:
        print('System Error getFilterBooleanClauseList: {}'.format(sys.exc_info()))
        raise e


# this function automatic identify required sqlalchemy classes, and columns and return query data result with response
def get_export_data(db, flask_excel, current_user_id, table_name, columns, operators, values, condition, usejson=False):
    # this is list of sqlalchemy filter conidtions recived from message (sqlalchemy.sql.elements.booleanclauselist) (incase no values it will not make issues)
    filterBooleanClauseList = getFilterBooleanClauseList(columns, operators, values, condition, target_table=table_name)
    export_tables = ['catalogue', 'listing', 'purchase', 'order', 'supplier']
    response =  {'success': True, 'message': '', 'data': [], 'column_names': [], 'excel_response': None}

    if table_name not in export_tables:
        return {'success': False, 'message': 'Invalid Table Selected'}
    
    # catalogue
    if table_name == 'catalogue':
        # my sqlalchemy export filter lib simple as filter query, and it makes user securly by clicking btns create any sqlalchemy result securely with simple words, it can used in create custom charts dynamic
        response['data'] = db.session.query(Catalogue).outerjoin(
            CatalogueLocations, CatalogueLocations.catalogue_id == Catalogue.id
        ).outerjoin(
            WarehouseLocations, CatalogueLocations.location_id == WarehouseLocations.id
        ).outerjoin(            
            CatalogueLocationsBins, CatalogueLocations.id == CatalogueLocationsBins.location_id
        ).outerjoin(
            LocationBins, CatalogueLocationsBins.bin_id == LocationBins.id
        ).outerjoin(
            Category, Category.id == Catalogue.category_id
        ).outerjoin(
            Condition, Condition.id == Catalogue.condition_id
        ).filter(and_(Catalogue.user_id==current_user_id), filterBooleanClauseList).all()
        if response['data']:
            export_data = []
            
            # response['column_names'] = getAllowedColumns(column_names=Catalogue.__table__.columns.keys(), ignored_columns=['user_id', 'product_image', 'created_date', 'updated_date'])
            # response['column_names'] = [*response['column_names'], 'location']

            response['column_names'] = ['id', 'sku', 'product_name', 'product_description', 'brand', 'category_code', 'category', 'price', 'sale_price', 'quantity', 'product_model', 'condition', 'upc', 'location']
            export_data.append(response['column_names'])

            for item in response['data']:
                locations_arr = []
                # easy can export bins too if needed
                for cat_location in item.locations:
                    locations_arr.append(str(cat_location.warehouse_location.name))
                locations = ','.join(locations_arr)
                categoryCode = item.category.code if item.category else ''
                categoryLabel = item.category.label if item.category else ''
                export_data.append([item.id, item.sku, item.product_name, item.product_description, item.brand, categoryCode, categoryLabel, item.price, item.sale_price, item.quantity, item.product_model, item.condition.name, item.upc, locations])
            # modfied array to return the addiontal relational data like locations or bins
            response['data'] = export_data
            
            if usejson == False:                
                response['excel_response'] = flask_excel.make_response_from_array(response['data'], 'csv', file_name='catalogues')
                # response['excel_response'] = flask_excel.make_response_from_query_sets(response['data'], response['column_names'], 'csv', file_name='catalogues')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (catalogues)'
        return response
    # listing
    elif table_name == 'listing':
        response['data'] = db.session.query(Listing).join(
            Catalogue, Listing.catalogue_id==Catalogue.id
        ).outerjoin(
            Platform, Listing.platform_id==Platform.id
        ).outerjoin(
            CatalogueLocations, CatalogueLocations.catalogue_id == Catalogue.id
        ).outerjoin(
            WarehouseLocations, CatalogueLocations.location_id == WarehouseLocations.id
        ).outerjoin(
            CatalogueLocationsBins, CatalogueLocations.id == CatalogueLocationsBins.location_id
        ).outerjoin(
            LocationBins, CatalogueLocationsBins.bin_id == LocationBins.id
        ).outerjoin(
            Category, Catalogue.category_id == Category.id
        ).outerjoin(
            Condition, Condition.id == Catalogue.condition_id
        ).outerjoin(
            Order, Order.listing_id == Listing.id
        ).outerjoin(
            OrderTaxes, OrderTaxes.order_id == Order.id
        ).filter(
            and_(Catalogue.user_id == current_user_id),
            filterBooleanClauseList
        ).all()                    
        if response['data']:
            export_data = []

            response['column_names'] = [
                'id', 'sku', 'product_name', 'product_description',
                'brand', 'category_code', 'category', 'price', 'sale_price',
                'quantity', 'condition', 'product_model',  'upc' ,'created_date',
                'updated_date', 'dashboard_id', 'catalogue_id', 'platform'
                ]
            export_data.append(response['column_names'])
            for item in response['data']:
                # if deleted condition, all condition.catalogues will have condition None (on delete set Null) so condition not always exist
                item_condition = item.catalogue.condition.name if item.catalogue.condition else ''
                export_data.append(
                    [
                        item.id, item.sku, item.product_name,
                        item.product_description, item.brand,
                        item.category_code, item.category_label,
                        item.price, item.sale_price, item.quantity,
                        item_condition,
                        item.catalogue.product_model, item.catalogue.upc,
                        item.created_date, item.updated_date,
                        item.dashboard_id, item.catalogue_id, item.platform.name
                        ])
            
            response['data'] = export_data
            if usejson == False:
                response['excel_response'] = flask_excel.make_response_from_array(response['data'], 'csv', file_name='listings')
                #response['excel_response'] = flask_excel.make_response_from_query_sets(x, response['column_names'], 'csv', file_name='listings')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (listings).'
        return response

    elif table_name == 'purchase':
        # it's required to have supplier, listing, catalogue, to get purchases object so it faster and better to keep join not outerjoin
        response['data'] = db.session.query(
            Purchase
        ).join(
            Supplier
        ).join(
            Listing, Purchase.listing_id == Listing.id
        ).join(
            Catalogue, Listing.catalogue_id == Catalogue.id
        ).filter(
            and_(Catalogue.user_id == current_user_id),
            filterBooleanClauseList
        ).all()
        if response['data']:
            response['column_names'] = Purchase.__table__.columns.keys()
            if usejson == False:
               response['excel_response'] = flask_excel.make_response_from_query_sets(response['data'], response['column_names'], 'csv', file_name='purchases')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (purchases).'

    elif table_name == 'order':
        response['data'] = db.session.query(
            Order
        ).join(
            Listing
        ).join(
            Catalogue
        ).filter(
            and_(Catalogue.user_id == current_user_id),
            filterBooleanClauseList
        ).all()
        if response['data']:
            response['column_names'] = Order.__table__.columns.keys()
            # set flask response in respons obj only if usejson == False as default (for performance in json response)
            if usejson == False:
                response['excel_response'] = flask_excel.make_response_from_query_sets(response['data'], response['column_names'], 'csv', file_name='orders')                 
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (orders).'
    # supplier
    elif table_name == 'supplier':
        response['data'] = db.session.query(Supplier).filter(and_(Supplier.user_id==current_user_id), filterBooleanClauseList).all()
        if response['data']:
            response['column_names'] = Supplier.__table__.columns.keys()
            if usejson == False:
                response['excel_response'] = flask_excel.make_response_from_query_sets(response['data'], response['column_names'], 'csv', file_name='suppliers')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (suppliers).'
        return response
    else:
        response['success'] = False
        response['message'] = 'Table requested can not be exported right now'
        return response
    
    return response

# charts

def getChartData(chart_query_result, label_i=0, data_i=1):
    labels = []
    data = []
    for chartItem in chart_query_result:        
        labels.append(str(chartItem[label_i]))
        data.append(str(chartItem[data_i]))

    return {'labels': labels, 'data': data}

def get_charts(db, current_user, charts_ids=[]):
    result = {}
    result_array = []
    index = 0
    try:
        for chart_id in charts_ids:
            index += 1
            if chart_id not in result:            
                if chart_id == 'top_ordered_products':
                    # chart 1
                    chart_query = db.session.query(
                        Listing.product_name,
                        func.sum(Order.quantity).label('total_quantities')
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ).join(
                        Order, Listing.id == Order.listing_id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(Listing.id).order_by(desc('total_quantities')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'top_ordered_products',
                        'type': 'html',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Top Ordered Products',
                        'background_colors': [ 'rgba(255, 99, 132, 0.2)', 'rgba(255, 159, 64, 0.2)', 'rgba(255, 205, 86, 0.2)', 'rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(201, 203, 207, 0.2)'],
                        'border_colors': [ 'rgb(255, 99, 132)', 'rgb(255, 159, 64)', 'rgb(255, 205, 86)', 'rgb(75, 192, 192)', 'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(201, 203, 207)' ],
                        'description': 'Products with the largest number of orders',
                        'col': 12
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'less_ordered_products':
                    # chart 1
                    chart_query = db.session.query(
                        Listing.product_name,
                        func.sum(Order.quantity).label('total_quantities')
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ).join(
                        Order, Listing.id == Order.listing_id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(Listing.id).order_by(asc('total_quantities')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'less_ordered_products',
                        'type': 'html',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'least demanded products',
                        'background_colors': [ 'rgba(255, 99, 132, 0.2)', 'rgba(255, 159, 64, 0.2)', 'rgba(255, 205, 86, 0.2)', 'rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(201, 203, 207, 0.2)'],
                        'border_colors': [ 'rgb(255, 99, 132)', 'rgb(255, 159, 64)', 'rgb(255, 205, 86)', 'rgb(75, 192, 192)', 'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(201, 203, 207)' ],
                        'description': 'Products with the lowest number of orders',
                        'col': 12
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
    
                elif chart_id == 'most_purchased_products':
                    # chart 2
                    chart_query = db.session.query(
                        Listing.product_name,
                        func.sum(Purchase.quantity).label('total_quantities')
                    ).join(
                        Purchase, Listing.id == Purchase.listing_id
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(Listing.id).order_by(desc('total_quantities')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'most_purchased_products',
                        'type': 'html',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Most purchased products',
                        'background_colors': [ 'rgba(255, 99, 132, 0.2)', 'rgba(255, 159, 64, 0.2)', 'rgba(255, 205, 86, 0.2)', 'rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(201, 203, 207, 0.2)'],
                        'description': 'Products with the largest number of purchases',
                        'col': 12
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'less_purchased_products':
    
                    # chart 3
                    chart_query = db.session.query(
                        Listing.product_name,
                        func.sum(Purchase.quantity).label('total_quantities')
                    ).join(
                        Purchase, Listing.id == Purchase.listing_id
                    ).join(
                        Catalogue, Listing.catalogue_id == Catalogue.id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(Listing.id).order_by(asc('total_quantities')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'less_purchased_products',
                        'type': 'pie',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'least purchased products',
                        'description': 'Products with the lowest number of purchases',
                        'col': 12
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'top_purchases_suppliers':
    
                    # chart 4
                    chart_query = db.session.query(
                        Supplier.name,
                        func.sum(Purchase.quantity).label('total_purchases')
                    ).join(
                        Purchase, Supplier.id==Purchase.supplier_id
                    ).filter(
                        Supplier.user_id == current_user.id
                    ).group_by(Purchase.supplier_id).order_by(desc('total_purchases')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'top_purchases_suppliers',
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Top Purchases Suppliers',
                        'description': 'The supplier with the most number of purchases'
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'less_purchases_suppliers':
    
                    # chart 5 (type of this charts matters later when have alot of suppliers and purchases will define who suppliers not work with him alot)
                    chart_query = db.session.query(
                        Supplier.name,
                        func.sum(Purchase.quantity).label('total_purchases')
                    ).join(
                        Purchase, Supplier.id==Purchase.supplier_id
                    ).filter(
                        Supplier.user_id == current_user.id
                    ).group_by(Purchase.supplier_id).order_by(asc('total_purchases')).limit(5).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'less_purchases_suppliers',
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Less Purchases Suppliers',
                        'description': 'The supplier with the less number of purchases'
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'suppliers_purchases':
    
                    # chart 6
                    chart_query = db.session.query(
                        Supplier.name,
                        func.sum(Purchase.quantity).label('total_purchases')
                    ).join(
                        Purchase, Supplier.id==Purchase.supplier_id
                    ).filter(
                        Supplier.user_id == current_user.id
                    ).group_by(Purchase.supplier_id).order_by(desc('total_purchases')).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'suppliers_purchases',
                        'type': 'doughnut',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'purchases from suppliers',
                        'description': 'the number of purchases from suppliers'
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue
                
                elif chart_id == 'orders_yearly_performance':
                
                    # chart 7
                    chart_query = db.session.query(
                        extract('year', Order.date),
                        func.sum(Order.quantity).label('total_orders')
                    ).join(
                        Listing, Order.listing_id==Listing.id
                    ).join(
                        Catalogue, Listing.catalogue_id==Catalogue.id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(extract('year', Order.date)).order_by(asc('total_orders')).all()
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'orders_yearly_performance',
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Orders Per Year',
                        'description': 'The number of orders per year',
                        'col': '6'
                    }
                    # 'year_picker_ajax': {'years': [2012, 2013, 2014]}, add dynamic ajax year input in chart, remaning
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue

                elif chart_id == 'purchases_yearly_performance':
                
                    # chart 8 (Remaning monthly with ajax select for month)
                    chart_query = db.session.query(
                        extract('year', Purchase.date),
                        func.sum(Purchase.quantity).label('total_purchases')
                    ).join(
                        Listing, Purchase.listing_id==Listing.id
                    ).join(
                        Catalogue, Listing.catalogue_id==Catalogue.id
                    ).filter(
                        Catalogue.user_id == current_user.id
                    ).group_by(extract('year', Purchase.date)).order_by(asc('total_purchases')).all()
                    # perfere for performance line chart as it up and down, but prefere for years bar
                    chartdata = getChartData(chart_query, label_i=0, data_i=1)
                    chart_data = {
                        'id': 'purchases_yearly_performance',
                        'type': 'line',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Purchases Per Year',
                        'description': 'The number of Purchases per year',
                        'col': 12
                    }
                    result[chart_id] = True
                    result_array.append(chart_data)
                    continue

                else:
                    # id provided not exist
                    result[chart_id] = False
                    result_array.append({})
                    continue
            else:
                # duplicated id provided
                result[str(index)] = False
                result_array.append({})
    except Exception as e:
        print('System Error get_filter_columns: {}'.format(sys.exc_info()))
        result[str(index)] = False
        result_array.append({})
    finally:
        return result_array

# function uses flask excel to get uploaded excel data rows by tring diffrent known encoding methods
def get_excel_rows(request, field_name=''):
    imported_rows = None
    avail_encodings = ['utf-8', 'ISO-8859-1', 'latin', 'mac_cyrillic', 'cp1252', 'latin1', 'latin2', 'utf_16']
    for encoding_method in avail_encodings:
        try:
           imported_rows = request.get_array(field_name=field_name, encoding=encoding_method)
           break
        except Exception as e:
            imported_rows = None
            continue
    # if none of all encoding worked raise error cus can not read the uploaded file with any method
    if imported_rows is None:
        raise ValueError('can not import file unknown encoded used try convert it to xlsx')
    
    return imported_rows
# get zero, one, or multiple locations names from string return list
def get_locations_arr(locations_string):
    locations_string = str(locations_string)
    row_locations = []
    try:
        if ',' in locations_string:
            row_locations = locations_string.split(",")
        else:
            row_locations.append(locations_string)
    except Exception as e:
        print('Error from get_locations_arr {}'.format(sys.exc_info()))
    return row_locations

def get_sheet_row_locations(mapped_catalogues_dict, row_index):
    row_locations = []
    try:
        # insert catalogue locations if not exist create locations
        if 'db_rows_locations' in mapped_catalogues_dict and len(mapped_catalogues_dict['db_rows_locations']) > row_index:
            
            sheet_location_str = mapped_catalogues_dict['db_rows_locations'][row_index]                                    
            # add 0, one or multiple db locations from excel
            row_locations = get_locations_arr(sheet_location_str)
    except Exception as e:
        print("Error in get_sheet_locations row index: {}, error_info: {}".format(row_index, sys.exc_info()))
    return row_locations


"""
(About this regex used): this regex says, string must start with english character or number, and followed by any of english characters or numbers or - and must end by english characters or number only and not \n --- note $ diffrent than \Z, \Z means match exact what given and not ignore the \n so if string end with \n will considered not matched, $ will ignore the \n becuase it dynamic handle both re.MULTILINE and normal first match so $ will match anything the string end with before the new line, ---note: []+ here means continue to the end like we say some pattern until end of match + new pattern--in this example ^[a-z0-9]+ means take any character or number until you reach of end where no more characters or numbers, then move to next pattern part which look for any character or number or - until end, using + important incase search here first + can ignored as next pattern part will match any number or character, but if ignored this will match only first char and leave rest for next part (+)!! it near equal to , or and start with part and part etc---match unlike find and search, this not search for example test\Z in string hello test match require pattern to begning part of string you can not say re.match("test\Z",txt) this invalid as missing hello\s or the pattern equal to it \w+ , [a-z]+ .* , etc 
"""
# secure and validate apikey return valid secure apikey value to inserted in request headers or None if invalid key and sub could not fix it
def apikey_or_none(apikey):
    result = None
    try:
        apikey = re.sub('[\s\n\r]', "", apikey)
        # repeat (az09)- unlimited and end with (az09) (accept dynamic change on key)
        valid = re.match("^([a-z0-9]+\-){1,}[a-z0-9]+\Z", apikey, re.IGNORECASE)
        if valid:
            result = valid.group()
    except:
        print("System error in apikey_or_none: {}".format(sys.exc_info()))
    return result
    
# divide lists into lists of length
def chunks(data, step):
    for i in range(0,len(data),step):
        yield data[i: i+step]
    
def float_or_none(float_num):
    try:
        return float(float_num)
    except:
        return None

def float_or_zero(float_num):
    try:
        return float(float_num)
    except:
        return 0
    
def int_or_none(int_num):
    try:
        return int(int_num)
    except:
        return None

def datestr_or_none(datestr):
    try:
        return datestr.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return None

def mysql_strdate(timestr=''):
    try:
        if timestr:
            datetime_obj = parser.parse(timestr)
            return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return None
    except:
        print('Error in mysql_strdate {}'.format(sys.exc_info()))
        return None
    
# this function insert only what needed to be inserted, and update only column that needed to updated, nothing more nothing less (+ uses performances to reduce db commit if required)
def upload_catalogues(offers_data, current_user):
    try:        
        result = {'total': len(offers_data), 'uploaded': 0, 'updated': 0, 'not_changed': 0, 'luploaded': 0, 'lupdated': 0, 'lnot_changed': 0, 'new_categories': 0}
        # create platform for best buy if not exist
        best_buy_platform = Platform.query.filter_by(name='bestbuy', dashboard_id=current_user.dashboard.id).first()
        if not best_buy_platform:
            best_buy_platform = Platform(dashboard_id=current_user.dashboard.id, name='bestbuy')
            best_buy_platform.insert()
        
        for offer in offers_data:
            if 'product_sku' in offer and 'product_title' in offer:
                product_sku = offer['product_sku']
                product_title = offer['product_title']
                product_description = offer['product_description'] if 'product_description' in offer else ''
                product_brand = offer['product_brand'] if 'product_brand' in offer else ''
                
                quantity = offer['quantity'] if 'quantity' in offer else 0
                active = offer['active'] if 'active' in offer else None
                shop_sku = offer['shop_sku'] if 'shop_sku' in offer else None
                category_code = offer['category_code'] if 'category_code' in offer else None
                category_label = offer['category_label'] if 'category_label' in offer else None
                currency_iso_code = offer['currency_iso_code'] if 'currency_iso_code' in offer else None
                offer_id = offer['offer_id'] if 'offer_id' in offer else None
                price = offer['price'] if 'price' in offer else 0.00

                # it big but confirm 0 errors (risk managment rules)
                reference = offer['product_references'][0]['reference'] if 'product_references' in offer and isinstance(offer['product_references'], list) and len(offer['product_references']) > 0 and isinstance(offer['product_references'][0], dict) and 'reference' in offer['product_references'][0] else None
                # ex UPC-A UPC-E that part of UPC barcodes (that can help knows which barcode type used based on countries and global systems)
                reference_type = offer['product_references'][0]['reference_type'] if 'product_references' in offer and isinstance(offer['product_references'], list) and len(offer['product_references']) > 0 and isinstance(offer['product_references'][0], dict) and 'reference_type' in offer['product_references'][0] else None
                
                quantity_threshold = offer['all_prices'][0]['volume_prices'][0]['quantity_threshold'] if 'all_prices' in offer and isinstance(offer['all_prices'], list) and len(offer['all_prices']) > 0 and isinstance(offer['all_prices'][0], dict) and 'volume_prices' in offer['all_prices'][0] and isinstance(offer['all_prices'][0]['volume_prices'], list) and len(offer['all_prices'][0]['volume_prices']) > 0 and isinstance(offer['all_prices'][0]['volume_prices'][0], dict) and 'quantity_threshold' in offer['all_prices'][0]['volume_prices'][0] else None
                unit_discount_price = offer['all_prices'][0]['volume_prices'][0]['unit_discount_price'] if 'all_prices' in offer and isinstance(offer['all_prices'], list) and len(offer['all_prices']) > 0 and isinstance(offer['all_prices'][0], dict) and 'volume_prices' in offer['all_prices'][0] and isinstance(offer['all_prices'][0]['volume_prices'], list) and len(offer['all_prices'][0]['volume_prices']) > 0 and isinstance(offer['all_prices'][0]['volume_prices'][0], dict) and 'unit_discount_price' in offer['all_prices'][0]['volume_prices'][0] else None
                unit_origin_price = offer['all_prices'][0]['volume_prices'][0]['unit_origin_price'] if 'all_prices' in offer and isinstance(offer['all_prices'], list) and len(offer['all_prices']) > 0 and isinstance(offer['all_prices'][0], dict) and 'volume_prices' in offer['all_prices'][0] and isinstance(offer['all_prices'][0]['volume_prices'], list) and len(offer['all_prices'][0]['volume_prices']) > 0 and isinstance(offer['all_prices'][0]['volume_prices'][0], dict) and 'unit_origin_price' in offer['all_prices'][0]['volume_prices'][0] else None

                discount_price = offer['discount']['discount_price'] if 'discount' in offer and isinstance(offer['discount'], dict) and 'discount_price' in offer['discount'] else None
                discount_start_date = mysql_strdate(offer['discount']['start_date']) if 'discount' in offer and isinstance(offer['discount'], dict) and 'start_date' in offer['discount'] else None
                discount_end_date = mysql_strdate(offer['discount']['end_date']) if 'discount' in offer and isinstance(offer['discount'], dict) and 'end_date' in offer['discount'] else None

                selected_category = Category.query.filter_by(dashboard_id=current_user.dashboard.id, code=category_code).first()
                if not selected_category:
                    selected_category = Category(dashboard_id=current_user.dashboard.id, code=category_code, label=category_label, level=0, parent_code='')
                    selected_category.insert()
                    result['new_categories'] += 1

                selected_catalogue = Catalogue.query.filter_by(sku=product_sku, user_id=current_user.id).first()
                not_changed = False
                if selected_catalogue:
                    update_require = False
                    # update catalogue data from api
                    if selected_catalogue.product_name != product_title:
                        selected_catalogue.product_name = product_title
                        update_require = True

                    if selected_catalogue.product_description != product_description:
                        selected_catalogue.product_description = product_description
                        update_require = True

                    if selected_catalogue.brand != product_brand:
                        selected_catalogue.brand = product_brand
                        update_require = True

                    if selected_catalogue.category_id != selected_category.id:
                        selected_catalogue.category_id = selected_category.id
                        update_require = True

                    if float_or_none(selected_catalogue.price) != price:                        
                        selected_catalogue.price = price
                        update_require = True

                    if float_or_none(selected_catalogue.sale_price) != discount_price:
                        selected_catalogue.sale_price = discount_price
                        update_require = True

                    if int_or_none(selected_catalogue.quantity) != quantity:
                        selected_catalogue.quantity = quantity
                        update_require = True

                    if selected_catalogue.upc != reference:
                        selected_catalogue.upc = reference
                        update_require = True

                    if selected_catalogue.reference_type != reference_type:
                        selected_catalogue.upc = reference_type
                        update_require = True

                    if update_require:
                        selected_catalogue.update()
                        result['updated'] += 1
                    else:
                        result['not_changed'] += 1
                        # this to help decide in next step, sync listing with changed catalogue data or not sync if catalogue not changed
                        not_changed = True
                else:
                    selected_catalogue = Catalogue(sku=product_sku, user_id=current_user.id, product_name=product_title, product_description=product_description, brand=product_brand, category_id=selected_category.id, price=price, sale_price=discount_price, quantity=quantity, product_model=None, condition_id=None, upc=reference, reference_type=reference_type)
                    selected_catalogue.insert()
                    result['uploaded'] += 1

                # check if listing exist in same platform
                selected_listing = Listing.query.filter_by(
                    dashboard_id=current_user.dashboard.id, catalogue_id=selected_catalogue.id,
                    sku=selected_catalogue.sku, platform_id=best_buy_platform.id
                ).first()

                if selected_listing:
                    update_require2 = False

                    if selected_listing.active != active:
                        selected_listing.active = active
                        update_require2 = True
                       
                       
                    if datestr_or_none(selected_listing.discount_start_date) != discount_start_date:
                        update_require2 = True
                        selected_listing.discount_start_date = discount_start_date

                    if datestr_or_none(selected_listing.discount_end_date) != discount_end_date:
                        selected_listing.discount_end_date = discount_end_date
                        update_require2 = True

                    if float_or_none(selected_listing.unit_discount_price) != unit_discount_price:
                        selected_listing.unit_discount_price = unit_discount_price
                        update_require2 = True

                    if float_or_none(selected_listing.unit_origin_price) != unit_origin_price:
                        selected_listing.unit_origin_price = unit_origin_price
                        update_require2 = True

                    if int_or_none(selected_listing.quantity_threshold) != quantity_threshold:
                        selected_listing.quantity_threshold = quantity_threshold
                        update_require2 = True

                    if selected_listing.currency_iso_code != currency_iso_code:
                        selected_listing.currency_iso_code = currency_iso_code
                        update_require2 = True

                    if selected_listing.shop_sku != shop_sku:
                        selected_listing.shop_sku = shop_sku
                        update_require2 = True

                    if int_or_none(selected_listing.offer_id) != offer_id:
                        selected_listing.offer_id = offer_id
                        update_require2 = True

                    if selected_listing.reference != reference:
                        selected_listing.reference = reference
                        update_require2 = True

                    if selected_listing.reference_type != reference_type:
                        selected_listing.reference_type = reference_type
                        update_require2 = True

                    if update_require2:
                        selected_listing.update()
                    
                    # is catalogue when updated changed or not, (default false) only if catalogue exist but it's data not updated not_changed will be True
                    if not_changed == False:
                        # this for sync listing with catalogue (also update listing data) (performance)
                        selected_listing.sync_listing()

                    # no updates happend, and catalogue not changed so the listing not asynced too
                    if not update_require2 and not_changed == True:
                        result['lnot_changed'] += 1

                    if update_require2 or not_changed == False:
                        result['lupdated'] += 1
                else:
                    new_listing = Listing(dashboard_id=current_user.dashboard.id, catalogue_id=selected_catalogue.id, platform_id=best_buy_platform.id, active=active, discount_start_date=discount_start_date, discount_end_date=discount_end_date, unit_discount_price=unit_discount_price, unit_origin_price=unit_origin_price, quantity_threshold=quantity_threshold, currency_iso_code=currency_iso_code, shop_sku=shop_sku, offer_id=offer_id, reference=reference, reference_type=reference_type)
                    new_listing.insert()
                    result['luploaded'] += 1
        
        return result
    except Exception as e:
        raise e

def upload_orders(orders, current_user, db):
    try:
        result = {'missing_listing': [], 'invalid_quantity': [], 'errors': [], 'total_errors': 0, 'total_uploaded': 0, 'total_updated': 0, 'total_missing': 0, 'total_invalid': 0, 'not_changed': 0}
        
        user_dashboard = current_user.dashboard

        best_buy_platform = Platform.query.filter_by(name='bestbuy', dashboard_id=user_dashboard.id).first()
        if not best_buy_platform:
            best_buy_platform = Platform(dashboard_id=current_user.dashboard.id, name='bestbuy')
            best_buy_platform.insert()

        for order in orders:
            order_id = None
            try:
                update_require = False
                quantity_updated = False
                update_log_require = False

                order_id = order['order_id'] if 'order_id' in order else None
                # order_lines
                order_lines_obj = order['order_lines'][0] if 'order_lines' in order and isinstance(order['order_lines'], list) and len(order['order_lines']) > 0 else None
                # imp
                offer_id = order_lines_obj['offer_id'] if 'offer_id' in order_lines_obj else None
                quantity = order_lines_obj['quantity'] if order_lines_obj and 'quantity' in order_lines_obj else None
                order_quantity = int_or_none(quantity)

                # to import an order you must first have listing and catalogue for it in same platform (catalogue_id not none so if listing there must be parent catalogue)
                target_listing = Listing.query.filter_by(offer_id=offer_id, platform_id=best_buy_platform.id).first()
                if target_listing:

                    # check if quantity accept new order (Later can improved calcas for refunded, dates! but dates crtical as if no real action done by user to provide order will lead into invalid calcuation)
                    catalogue_quantity = int_or_none(target_listing.catalogue.quantity)
                    int_order_quantity = order_quantity if order_quantity is not None else 0
                    int_catalogue_quantity = catalogue_quantity if catalogue_quantity is not None else 0

                    can_refund = order_lines_obj['can_refund'] if order_lines_obj and 'can_refund' in order_lines_obj else None
                    category_code = order_lines_obj['category_code'] if order_lines_obj and 'category_code' in order_lines_obj else None
                    product_title = order_lines_obj['product_title'] if order_lines_obj and 'product_title' in order_lines_obj else None
                    shipping_price = order_lines_obj['shipping_price'] if order_lines_obj and 'shipping_price' in order_lines_obj else None
                    product_sku = order_lines_obj['product_sku'] if order_lines_obj and 'product_sku' in order_lines_obj else None

                    # customer data
                    customer = order['customer'] if 'customer' in order and isinstance(order['customer'], dict) else None
                    firstname = customer['firstname'] if customer and 'firstname' in customer else None
                    lastname = customer['lastname'] if customer and 'lastname' in customer else None
                    # billing_address and shipping address
                    billing_address = customer['billing_address'] if customer and 'billing_address' in customer and isinstance(customer['billing_address'], dict) else None
                    shipping_address = customer['shipping_address'] if customer and 'shipping_address' in customer and isinstance(customer['shipping_address'], dict) else None
                    # try to get phone, street_1, street_2 from billing or shipping data
                    phone = billing_address['phone'] if billing_address and 'phone' in billing_address else None
                    if phone is None:
                        phone = shipping_address['phone'] if shipping_address and 'phone' in shipping_address else None
                    street_1 = billing_address['street_1'] if billing_address and 'street_1' in billing_address else None
                    if street_1 is None:
                        street_1 = shipping_address['street_1'] if shipping_address and 'street_1' in shipping_address else None
                    street_2 = billing_address['street_2'] if billing_address and 'street_2' in billing_address else None
                    if street_2 is None:
                        street_2 = shipping_address['street_2'] if shipping_address and 'street_2' in shipping_address else None
                    zip_code = billing_address['zip_code'] if billing_address and 'zip_code' in billing_address else None
                    if zip_code is None:
                        zip_code = shipping_address['zip_code'] if shipping_address and 'zip_code' in shipping_address else None
                    city = billing_address['city'] if billing_address and 'city' in billing_address else None
                    if city is None:
                        city = shipping_address['city'] if shipping_address and 'city' in shipping_address else None
                    country = billing_address['country'] if billing_address and 'country' in billing_address else None
                    if country is None:
                        country = shipping_address['country'] if shipping_address and 'country' in shipping_address else None

                    # taxes list
                    api_taxes = order_lines_obj['taxes'] if order_lines_obj and 'taxes' in order_lines_obj else []
                    taxes = []
                    for tax in api_taxes:
                        # make sure any dict provided contains both amount and code
                        if 'amount' in tax and 'code' in tax:
                            taxes.append({'amount': tax['amount'], 'code': tax['code']})
    
                    shping_taxes_api = order_lines_obj['shipping_taxes'] if order_lines_obj and 'shipping_taxes' in order_lines_obj else []
                    shipping_taxes = []
                    for stax in shping_taxes_api:
                        if 'amount' in stax and 'code' in stax:
                            shipping_taxes.append({'amount': stax['amount'], 'code': stax['code']})
    
                    
                    commercial_id = order['commercial_id'] if 'commercial_id' in order else None
                    created_date = mysql_strdate(order['created_date'] if 'created_date' in order else None)
                    currency_iso_code = order['currency_iso_code'] if 'currency_iso_code' in order else None
                    fully_refunded = order['fully_refunded'] if 'fully_refunded' in order else None
                    price = order['price'] if 'price' in order else None
                    total_commission = order['total_commission'] if 'total_commission' in order else None
                    total_price = order['total_price'] if 'total_price' in order else None
                    order_state = order['order_state'] if 'order_state' in order else None
    
                    new_order = db.session.query(Order).join(Listing, Order.listing_id==Listing.id).filter(
                        Listing.dashboard_id == user_dashboard.id,
                        Listing.platform_id == best_buy_platform.id,
                        Order.order_id != None,
                        Order.order_id == order_id,
                    ).first()
    
                    if new_order:
                        # update existing order data
                        # 1-back catalogue qauntity as it was and check if the new quantity <= original catalogue qunatity or not (if added in quantity check it will not acurate data so ignore all order data or accept all else it may edit part of data and keep invalid quantity and not report that order ignored as invalid quantity)
                        current_order_quantity = int_or_none(new_order.quantity)
                        # catalogue db not accept null or string val, order must have quantity so incase one of both is null there are error and order must ignored
                        original_catalogue_quantity = int(int_catalogue_quantity + current_order_quantity) if current_order_quantity is not None else None

                        if original_catalogue_quantity is not None and int_order_quantity <= original_catalogue_quantity:
                            if new_order.quantity != order_quantity:
                                new_order.quantity = order_quantity
                                # here set the int of catalogue.qunatity to the original before any subtrict for new quantity only when quantity changed
                                int_catalogue_quantity = original_catalogue_quantity
                                update_require = True
                                quantity_updated = True

                            if datestr_or_none(new_order.date) != created_date:
                                new_order.date = created_date
                                update_require = True

                            if new_order.customer_firstname != firstname:
                                new_order.customer_firstname = firstname
                                update_require = True

                            if new_order.customer_lastname != lastname:
                                new_order.customer_lastname = lastname
                                update_require = True

                            if float_or_none(new_order.shipping) != shipping_price:
                                new_order.shipping = shipping_price
                                update_require = True

                            if float_or_none(new_order.commission) != total_commission:
                                new_order.commission = total_commission
                                update_require = True                         

                            if float_or_none(new_order.total_cost) != total_price:
                                new_order.total_cost = total_price
                                update_require = True

                            if new_order.commercial_id != commercial_id:
                                new_order.commercial_id = commercial_id
                                update_require = True

                            if new_order.currency_iso_code != currency_iso_code:
                                new_order.currency_iso_code = currency_iso_code
                                update_require = True

                            if new_order.phone != phone:
                                new_order.phone = phone
                                update_require = True

                            if new_order.street_1 != street_1:
                                new_order.street_1 = street_1
                                update_require = True

                            if new_order.street_2 != street_2:
                                new_order.street_2 = street_2
                                update_require = True

                            if new_order.zip_code != zip_code:
                                new_order.zip_code = zip_code
                                update_require = True

                            if new_order.city != city:
                                new_order.city = city
                                update_require = True

                            if new_order.country != country:
                                new_order.country = country
                                update_require = True

                            if new_order.fully_refunded != fully_refunded:
                                new_order.fully_refunded = fully_refunded
                                update_require = True

                            if new_order.can_refund != can_refund:
                                new_order.can_refund = can_refund
                                update_require = True

                            if new_order.order_id != order_id:
                                new_order.order_id = order_id
                                update_require = True

                            if new_order.category_code != category_code:
                                new_order.category_code = category_code
                                update_require = True

                            if float_or_none(new_order.price) != price:
                                new_order.price = price
                                update_require = True

                            if new_order.product_title != product_title:
                                new_order.product_title = product_title
                                update_require = True

                            if new_order.product_sku != product_sku:
                                new_order.product_sku = product_sku
                                update_require = True

                            if new_order.order_state != order_state:
                                new_order.order_state = order_state
                                update_require = True

                            
                            for order_tax in taxes:
                                order_tax_exist = OrderTaxes.query.filter_by(order_id=new_order.id, type='order', code=order_tax['code']).first()
                                if not order_tax_exist:
                                    # insert order tax if not exist
                                    new_order.taxes.append(OrderTaxes(type='order', amount=order_tax['amount'], code=order_tax['code']))
                                    update_require = True
                                else:
                                    # update existing order tax if the amount changed
                                    if float_or_none(order_tax_exist.amount) != order_tax['amount']:
                                        order_tax_exist.amount = order_tax['amount']
                                        update_log_require = True
                                        order_tax_exist.update()

                            for shipping_tax in shipping_taxes:
                                shipping_tax_exist = OrderTaxes.query.filter_by(order_id=new_order.id, type='shipping', code=shipping_tax['code']).first()
                                if not shipping_tax_exist:
                                    # insert order tax if not exist
                                    new_order.taxes.append(OrderTaxes(type='shipping', amount=shipping_tax['amount'], code=shipping_tax['code']))
                                    update_require = True
                                else:
                                    # update existing order tax if the amount changed
                                    if float_or_none(shipping_tax_exist.amount) != shipping_tax['amount']:
                                        shipping_tax_exist.amount = shipping_tax['amount']
                                        update_log_require = True
                                        shipping_tax_exist.update()
                        
                            if update_require:
                                new_order.update()
                                result['total_updated'] += 1
                            elif update_log_require:
                                result['total_updated'] += 1
                            else:
                                result['not_changed'] += 1
                        else:
                            if order_id:
                                result['missing_listing'].append(order_id)
                            result['total_missing'] += 1

                    else:
                        # create new order
                        if int_order_quantity <= int_catalogue_quantity:
                            new_order = Order(
                                listing_id=target_listing.id,
                                quantity=order_quantity,
                                date=created_date,
                                customer_firstname=firstname,
                                customer_lastname=lastname,
                                tax=0.0,
                                shipping=shipping_price,
                                shipping_tax=0.0,
                                commission=total_commission,
                                total_cost=total_price,
                                commercial_id=commercial_id,
                                currency_iso_code=currency_iso_code,
                                phone=phone,
                                street_1=street_1,
                                street_2=street_2,
                                zip_code=zip_code,
                                city=city,
                                country=country,
                                fully_refunded=fully_refunded,
                                can_refund=can_refund,
                                order_id=order_id,
                                category_code=category_code,
                                price=price,
                                product_title=product_title,
                                product_sku=product_sku,
                                order_state=order_state
                            )
                            # insert order taxes
                            for order_tax in taxes:
                                new_order.taxes.append(OrderTaxes(type='order', amount=order_tax['amount'], code=order_tax['code']))

                            for shipping_tax in shipping_taxes:
                                new_order.taxes.append(OrderTaxes(type='shipping', amount=shipping_tax['amount'], code=shipping_tax['code']))

                            new_order.insert()
                            quantity_updated = True
                            result['total_uploaded'] += 1
                        else:
                            # API can later accept list of order_ids so user can use the invalid order_ids after fix
                            if order_id:
                                result['invalid_quantity'].append(order_id)
                            result['total_invalid'] += 1                            

                    # update catalogue quantity if quantity updated or new order inserted (better performance and reduce db calls incase of update)
                    if quantity_updated:
                        # note incase of quantity changed by update action int_catalogue_quantity will back to original catalogue quantity then from begning start subtsrict the new order quantity, ex: catalogue 0 quantity and have x order with 3, when update x order and make it 2, catalogue quantity will back 3 as it was then substrict new quantity which is 2 result new remaning quantity is 1
                        new_quantity = int(int_catalogue_quantity - int_order_quantity)
                        # note I checked in previous nested if int_order_quantity <= int_catalogue_quantity so incase came here and found nagtive it python bug can not vaildate <= so this always have right value even if python got error in check <= this will not accept nagtive value
                        new_quantity = new_quantity if new_quantity >= 0 else 0
                        target_listing.catalogue.quantity = new_quantity
                        target_listing.catalogue.update()
                else:
                    if order_id:
                        result['missing_listing'].append(order_id)
                    result['total_missing'] += 1

            except Exception as e:
                print("error while import one of orders {}".format(sys.exc_info()))
                if order_id:
                    result['errors'].append(order_id)

                result['total_errors'] += 1

        return result

    except Exception as e:
        raise e

def calc_orders_result(results):
    result = {'missing_listing': [], 'invalid_quantity': [], 'errors': [], 'total_errors': 0, 'total_uploaded': 0, 'total_updated': 0, 'total_missing': 0, 'total_invalid': 0, 'not_changed': 0}
    for res in results:
        result['missing_listing'] = [*result['missing_listing'], *res['missing_listing']]
        result['invalid_quantity'] = [*result['invalid_quantity'], *res['invalid_quantity']]
        result['errors'] = [*result['errors'], *res['errors']]

        result['total_errors'] += res['total_errors']
        result['total_uploaded'] += res['total_uploaded']
        result['total_updated'] += res['total_updated']
        result['total_missing'] += res['total_missing']
        result['total_invalid'] += res['total_invalid']
        result['not_changed'] += res['not_changed']
    return result

def calc_chunks_result(results):
    try:
        final_result = {'total': 0, 'uploaded': 0, 'updated': 0, 'not_changed': 0, 'luploaded': 0, 'lupdated': 0, 'lnot_changed': 0, 'new_categories': 0}
        for result in results:
            final_result['total'] += result['total']
            final_result['uploaded'] += result['uploaded']
            final_result['updated'] += result['updated']
            final_result['not_changed'] += result['not_changed']
            final_result['luploaded'] += result['luploaded']
            final_result['lnot_changed'] += result['lnot_changed']
            final_result['new_categories'] += result['new_categories']
        return final_result
    except Exception as e:
        raise e

# bestbuy api
def bestbuy_ready():
    try:
        # track both new setup first time , or updated global config value
        return len(UserMeta.query.filter(
            and_(UserMeta.user_id==current_user.id),
            or_(
                and_(UserMeta.key=='bestbuy_remaining_requests'),
                and_(UserMeta.key=='bestbuy_request_max')
                )
        ).all()) >= 2
    except Exception as e:
        raise e

"""
# this only allow fixed max requests for all users and not allow diffrent users to have diffrent max
def bestbuy_ready():
    try:
        # track both new setup first time , or updated global config value
        return len(UserMeta.query.filter(
            and_(UserMeta.user_id==current_user.id),
            or_(
                and_(UserMeta.key=='bestbuy_remaining_requests', UserMeta.value==current_app.config.get('BESTBUY_RAMAINING')),
                and_(UserMeta.key=='bestbuy_request_max', UserMeta.value==current_app.config.get('BESTBUY_MAX'))
                )
        ).all()) >= 2
    except Exception as e:
        raise e
"""
def get_remaining_requests()->int:
    remaining_requests = 0
    try:
        now_dt = datetime.utcnow()
        # two days today need be yasterday instead
        today = now_dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        now = now_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        now_requests = len(UserMeta.query.filter(
            UserMeta.key=='bestbuy_request',
            UserMeta.user_id==current_user.id,
            and_(UserMeta.created_date>=today, UserMeta.created_date<=now)
        ).all())
    
        user_remaining_requests = UserMeta.query.filter_by(key='bestbuy_remaining_requests', user_id=current_user.id).first()
        if user_remaining_requests:
            # db_remaning_requests = int(user_remaining_requests.value) if int(user_remaining_requests.value) == int(current_app.config.get('BESTBUY_RAMAINING')) else int(current_app.config.get('BESTBUY_RAMAINING'))             
            db_remaning_requests = int(user_remaining_requests.value)
            remaining_requests = db_remaning_requests - now_requests
        else:
            raise ValueError('bestbuy_remaining_requests not exist while bestbuy_ready true')

        # remove old requests meta for yestaerday and before to small db
        before_today_requests = UserMeta.query.filter(
            UserMeta.key=='bestbuy_request',
            UserMeta.user_id==current_user.id,
            and_(UserMeta.created_date<today)
        ).all()
        for old_request_meta in before_today_requests:
            old_request_meta.delete()

        return remaining_requests
    except:
        print('error in get_remaining_requests: {}'.format(sys.exc_info()))
        return 0
    
def get_requests_before_1minute():
    requests_before_1minute = 0
    try:
        now_dt = datetime.utcnow()
        before_1minute = (now_dt - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        now = now_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # remove old requests meta for yestaerday and before to small db
        requests_before_1minute = len(UserMeta.query.filter(
            UserMeta.key=='bestbuy_request',
            UserMeta.user_id==current_user.id,
            and_(UserMeta.created_date>before_1minute, UserMeta.created_date<=now)
        ).all())

        remanining_timeq = UserMeta.query.filter(
            UserMeta.key=='bestbuy_request',
            UserMeta.user_id==current_user.id,
            and_(UserMeta.created_date>before_1minute)
        ).order_by(desc(UserMeta.created_date)).first()

        remanining_time = '60'
        if remanining_timeq:
            # remanining_timeq is last made request before 1 minute, eg made on 9/5/2023 9:00:00, after 1 minute 9:01:00, check now - last request date +1minute
            last_after_1m = (remanining_timeq.created_date + timedelta(minutes=1))
            remanining_time = str(int((last_after_1m - now_dt).total_seconds()))
        return (requests_before_1minute, remanining_time)
    except:
        print('error in get_requests_before_1minute: {}'.format(sys.exc_info()))
        return (requests_before_1minute, '60')

# # advanced codeless Function, this function do repeated action which is get db objects from same length lists (so it easy to insert into db without alot of validations and with single loop)
def get_ordered_dicts(keys=[], *lists):
    try:
        list_of_dicts = []
        if not lists:
            return list_of_dicts
        # notice incase of providing invalid keys not equal to lists
        if len(lists) != len(keys):
            raise ValueError("Keys and lists length not equal")

        # as previous check , checks for the length of the keys vs length of data lists , this check is deep 1 level it check for each list values and make sure all data lists have same length
        if len(set(list(map(lambda l : len(l), lists)))) > 1:
            raise ValueError("Data lists length not equal")
        
        zip_lists = list(zip(*lists))
        for l in zip_lists:
            list_of_dicts.append(dict(zip(keys, l)))

        return list_of_dicts
    except Exception as e:
        print("unknown error in get_ordered_dicts, {}".format(sys.exc_info()))
        raise e

def download_order_image(image_name='', image_url='', static_folder=''):
    # simple function to download image by url with name secure
    data = {'content_type': None, 'ext': None, 'filename': ''}
    if image_name and image_url:
        image_name = image_name.strip().lower()
        image_url = image_url.strip()
        r = requests.get(image_url, headers={'Authorization': 'a750a16c-054e-407c-9825-3da7d4b2a9c1'})
        content = r.content
        data['content_type'] = r.headers.get('Content-Type', None) if getattr(r, 'headers') else None
        content_type_splited = data['content_type'].split('/')
        allowed_exts = ['png', 'jpg', 'jpeg', 'gif', 'webp']
        data['ext'] = str(content_type_splited[-1]).strip().lower() if (len(content_type_splited) >= 2) and (content_type_splited[-1] in allowed_exts) else None

        if data['ext']:
            data['filename'] = '{}.{}'.format(image_name, data['ext'])
            p = os.path.join(static_folder, 'downloads', 'order_images', data['filename'])
            data
            with open(p, mode='wb') as f:
                f.write(r.content)
        else:
            data = None
    else:
        data = None

    return data

# import orders
def order_ids_chunks(lst, n):
    result = []
    try:
        for i in range(0, len(lst), n):
            result.append(",".join(lst[i:i+n]))
        return result
    except Exception as e:
        raise e
# new
def import_orders(db, apikey='', order_ids=[], bestbuy_request_max=0, user_remaining_requests=0, tomorrow_str=''):
    results = []
    chunks_errors = []
    successful = 0
    error = ''

    if user_remaining_requests > 0:
        bestbuy_request_max = int(bestbuy_request_max)
        request_max = bestbuy_request_max if bestbuy_request_max <= 100 and bestbuy_request_max >= 0 else 100
        headers = {'Authorization': apikey}
        
        order_ids_params = order_ids_chunks(order_ids, 100)
    
        for order_ids_group in order_ids_params:

            req_url = f'https://marketplace.bestbuy.ca/api/orders?max={request_max}&order_ids={order_ids_group}'
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
                            print("Error in one of chunks at import_orders func: {}".format(sys.exc_info()))
                            chunks_errors.append("Some Of data Could not be imported, Error occured in request number {}: start from {} to {}".format((i+2), current_max, (current_max-request_max)))
    
                else:
                    chunks_errors.append("Could not import the Remaining {} data at the moment, you exceded the limit of requests, not all data imported".format(remaing_data))
                    break
            elif r.status_code == 401:
                error = 'Invalid API key, the API refused to authorize your request.'
                break
            else:
                error = 'The API cannot process your request now, please try again later, if the problem is not resolved, please report to us.'
                break
    else:
        error = f'You Can not make more requests right now, please wait for {tomorrow_str} and try again'

    return {'results': results, 'chunks_errors': chunks_errors, 'error': error}

# js component handle sqlalchemy update order taxes (remove, insert, update) -> result in edit table action of db for child sqlalchemy table rows
def get_orders_and_shippings(form):
    try:
        order_tax_codes = list(form.order_tax_codes.data.split('-_-'))
        order_tax_amounts = list(form.order_tax_amounts.data.split('-_-'))
        shiping_tax_codes = list(form.shiping_tax_codes.data.split('-_-'))
        shiping_tax_amounts = list(form.shiping_tax_amounts.data.split('-_-'))
    
        order_tax_ids = form.order_tax_ids.data.split(',') if form.order_tax_ids.data else []
        shiping_tax_ids = form.shiping_tax_ids.data.split(',') if form.shiping_tax_ids.data else []
    
        order_taxes = []
        shipping_taxes = []
        if order_tax_codes and order_tax_amounts and order_tax_ids:
            type_arr = ['order' for i in range(len(order_tax_ids))]
            order_taxes = get_ordered_dicts(['code', 'amount', 'id', 'type'], order_tax_codes, order_tax_amounts, order_tax_ids, type_arr)
        

        if shiping_tax_codes and shiping_tax_amounts and shiping_tax_ids:
            type_arr = ['shipping' for i in range(len(shiping_tax_ids))]
            shipping_taxes = get_ordered_dicts(['code', 'amount', 'id', 'type'], shiping_tax_codes, shiping_tax_amounts, shiping_tax_ids, type_arr)
        
        return {'order_taxes': order_taxes, 'shipping_taxes':shipping_taxes}
    
    except Exception as e:
        raise e

def update_order_taxes(form, target_order):
    try:
        data =get_orders_and_shippings(form)
        order_taxes = data['order_taxes']
        shipping_taxes = data['shipping_taxes']
        # this short code return edited and new objects and used to get removed current rows ids
        order_taxes_allrows = [
            {'current': OrderTaxes.query.filter_by(id=taxobj['id'], order_id=target_order.id).one_or_none(), 'new': {'code': taxobj['code'], 'amount': taxobj['amount']}} if OrderTaxes.query.filter(OrderTaxes.id==taxobj['id'], OrderTaxes.order_id==target_order.id).one_or_none() else 
            OrderTaxes(order_id=target_order.id, code=taxobj['code'], amount=float_or_zero(taxobj['amount']), type=taxobj['type'])
            for taxobj in [*order_taxes, *shipping_taxes]
        ]

        # sperate results, get ids that exist after updates (updated rows ids list), new objects to inserts and list for updated rows (current sqlalchemy class and new dict of data)
        submited_ids = []
        new_objects = []
        update_objects = []
        for submited_order_tax in order_taxes_allrows:
            #return str(submited_order_tax)
            if submited_order_tax and isinstance(submited_order_tax, dict) and 'current' in submited_order_tax and hasattr(submited_order_tax['current'], 'id') and submited_order_tax['current'].id and hasattr(submited_order_tax['current'], 'update'):
                # updated rows
                update_objects.append(submited_order_tax)
                submited_ids.append(submited_order_tax['current'].id)
            elif submited_order_tax and hasattr(submited_order_tax, 'insert') and hasattr(submited_order_tax, 'code') and submited_order_tax.code:
                # new rows
                new_objects.append(submited_order_tax)
            else:
                continue

        # get removed rows, current order rows that have id not in the updated rows ids submited by user
        removed = []
        removed_rows = OrderTaxes.query.filter(OrderTaxes.order_id==target_order.id, OrderTaxes.id.notin_(submited_ids)).all()
        for removed_ordertax in removed_rows:
            removed.append(removed_ordertax.code)
            removed_ordertax.delete()
        
        

        # update orders that user updated
        updates = []
        updates_new = []
        for order_to_update in update_objects:
            
            sqlalchemy_ob = order_to_update['current']
            data_dict = order_to_update['new']
            updated = False
            if sqlalchemy_ob.code != data_dict['code'] and data_dict['code'].strip() != '':
                updates.append(sqlalchemy_ob.code)
                sqlalchemy_ob.code = data_dict['code']
                updates_new.append(sqlalchemy_ob.code)
                updated = True
            if float_or_none(sqlalchemy_ob.amount) != float_or_none(data_dict['amount']):
                # to calc if change happed of all func or not and info about changes       
                updates.append(sqlalchemy_ob.amount) 
                sqlalchemy_ob.amount = float_or_zero(data_dict['amount'])
                updates_new.append(sqlalchemy_ob.amount)
                # to run commit or no
                updated = True
                
            if updated == True:
                sqlalchemy_ob.update()

        # insert the new rows only if code not empty
        inserted = []
        for new_order_tax in new_objects:
            if new_order_tax and hasattr(new_order_tax, 'insert') and hasattr(new_order_tax, 'code') and new_order_tax.code.strip() != '' and hasattr(new_order_tax, 'order_id') and new_order_tax.order_id == target_order.id:
                # insert not empty code taxes
                inserted.append(new_order_tax.code)
                new_order_tax.insert()

        changed = len(removed) > 0 or len(updates) > 0 or len(inserted) > 0
        return {'removed': removed, 'updated': {'old': updates, 'new': updates_new}, 'inserted': inserted , 'changed': changed}
    except Exception as e:
        raise e


def get_separate_order_taxes(target_order):
    order_taxes = []
    shipping_taxes = []
    try:
        for target_order_tax in target_order.taxes:
            if target_order_tax.type == 'order':
                order_taxes.append(target_order_tax)
            elif target_order_tax.type == 'shipping':
                shipping_taxes.append(target_order_tax)
            else:
                continue
    except:
        print("error in get_separate_order_taxes: {}".format(sys.exc_info()))

    return {'order_taxes': order_taxes, 'shipping_taxes': shipping_taxes}

def format_name(col):
    return re.sub( r'(^[a-z]|\_[a-z])', lambda x : x.group().upper(), col, re.IGNORECASE).replace('_',' ')

# can used to fill barcode form for any table/multiple endpoints
def fill_generate_barcode(form, table_class, itemid, excluded=[], relations={}, customs=[]):
    new_choices = []
    data_attrs = {}
    table_cols = table_class.__table__.columns.keys()
    db_class = table_class.query.filter_by(id=itemid).first()
    if db_class:
        for col in table_cols:
            if col not in excluded:
                if col in relations and callable(relations[col]):
                    # custom set relational value of used class (can used with any table eg i do not need category_id i need category name etc)
                    cb = relations[col]
                    choice = cb(db_class)
                    if choice:
                        for choice_tup in choice:
                            if len(choice_tup) == 2:
                                new_choices.append((choice_tup[0],format_name(choice_tup[0])))
                                data_attrs['data-{}'.format(choice_tup[0])] = choice_tup[1]
                else:
                    new_choices.append((col, format_name(col)))
                    # dynamic set required javascript data attribute with wtforms
                    data_attrs['data-{}'.format(col)] = getattr(db_class, col)

        # use for both un relational data and custom options it can also be for relation property of class for example access catalogue.locations , note table_class.__table__.columns.keys() returns only direct columns of db not relations like locations, parent_user, etc
        for custom in customs:
            if callable(custom):
                choice = custom(db_class)
                if choice:
                    for choice_tup in choice:
                        if len(choice_tup) == 2:
                            new_choices.append((choice_tup[0],format_name(choice_tup[0])))
                            data_attrs['data-{}'.format(choice_tup[0])] = choice_tup[1]

        form.columns.choices = new_choices
        form.columns.render_kw = data_attrs

# profile functions
def get_errors_message(form):
    error = ''
    errorsl = []
    for field, errors in form.errors.items():
        if field == 'csrf_token':
            errorsl.append('Form expired please try again')
        else:
            errorsl.append('{}:{}'.format(field, ','.join(errors)))
    error = '|'.join(errorsl)
    return error

def generate_ourapi_key(bcrypt):
    secure_salat = secrets.token_hex(7)
    unique_key = hash(bcrypt.generate_password_hash(str(datetime.now().strftime('%Y%m%d%H%M%S-') + secure_salat + str(uuid4()))).decode('utf-8'))
    if unique_key < 0:
        unique_key = str(unique_key).replace('-', 'n')
    else:
        unique_key = 'p{}'.format(unique_key)
    return str(unique_key)


###################### api endpoints functions

def limit_resetter(db_apikey):
    now_day = datetime.utcnow().date()
    if db_apikey.key_update_date < now_day:
        # update only the key we work with, performance, ux, and do what needed
        db_apikey.total_requests = 0
        db_apikey.key_update_date = now_day
        # clear logs optional when rest
        for log in db_apikey.logs:
            log.delete()
            
        db_apikey.update()
        return True
    else:
        return False
    
def valid_ourapi_key(db_apikey, db):
    valid = False
    try:
        key_user_id = db_apikey.user.id
        if key_user_id:
            # check if user api meta already set or it deleted? or not exist!!
            ourapi_requests_limit = UserMeta.query.filter_by(key='ourapi_requests_limit', user_id=key_user_id).first()
            ourapi_keys_max = UserMeta.query.filter_by(key='ourapi_keys_max', user_id=key_user_id).first()
            if ourapi_requests_limit and ourapi_keys_max:
                # check if need reset limit and do it
                limit_resetter(db_apikey)

                # requests_limit is total requests available for this user as all keys
                requests_limit = int(ourapi_requests_limit.value)

                # current keys requests made and limit per today
                key_total_requests = int(db_apikey.total_requests)
                key_requests_limit = int(db_apikey.key_limit)

                sum_totals = int(db.session.query(func.sum(OurApiKeys.total_requests)).filter(OurApiKeys.user_id==key_user_id).scalar())
                if (sum_totals < requests_limit) and (key_total_requests < key_requests_limit):
                    valid = True
    except Exception as e:
        print('error in valid_ourapi_key {}'.format(sys.exc_info()))

    return valid

def get_filter_params(filters):
    sqlalchemy_filters = []
    for key, val in filters.items():
        if filters[key] is not None:
            sqlalchemy_filters.append(filters[key])
    return sqlalchemy_filters


# (ISO time used in both db.created_date and pass_api_request, small delay for performance, and block largest ddos, anti scraper bots if u bot u will not get more than 25 responses and blocked forever, if u human will wait very small seconds usally if u not send 25 requests within 2 min
def pass_api_request(apikey_id, db):
    db_today = datetime.utcnow()
    before_2m = db_today - timedelta(hours=0, minutes=2)
    today_formated = db_today.strftime("%Y-%m-%d %H:%M:%S")
    before_2m_formated = before_2m.strftime("%Y-%m-%d %H:%M:%S")
    total_within_2_min = db.session.query(func.count(ApiKeysLogs.id)).filter(ApiKeysLogs.key_id==apikey_id, ApiKeysLogs.created_date >= before_2m_formated, ApiKeysLogs.created_date <= today_formated).scalar()
    return True if isinstance(total_within_2_min, int) and (total_within_2_min < 25) else False
