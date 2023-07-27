import sys
from urllib.parse import urlparse, urljoin
from flask import request
from sqlalchemy import func
from .models import Supplier, Dashboard, Listing, Catalogue, Purchase, Order, Platform, ListingPlatform
from sqlalchemy.sql import extract
from sqlalchemy import or_, and_, func , asc, desc

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
        "sku","product_name","product_description","brand","category","price","sale_price","quantity","product_model","condition","upc", "location"]
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
    
#{ "sku",  "product_name",  "product_description",  "brand",  "category",  "price",  "sale_price",  "quantity",  "product_model",  "condition",  "upc",  "location", }
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
    


def updateDashboardOrders(db, Order, Listing, user_dashboard):
    try:
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
    allowed_redirect = ['/home']
    if redirect_url in allowed_redirect:
        return redirect_url
    else:
        return '/home'

"""  Filter Class and its function (this class access direct functions deacleard in functions.py) """

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


        # rendered with same order in js (filters_args_list ...(args))  (can change order of display in frontend)
        catalogue_table_filters = [*self.catalogue_columns]
        # call function here becuase i need custom ignored duplicated columns in Catalogue not the default (changed that for make test way for user without code, he can validate if catalogues data not changed) (actions done by event listeners)
        listing_table_filters = [
            *self.listing_columns,
            *self.catalogue_columns,
            *self.platform_columns
            ]
        # *getTableColumns(Catalogue, ['user_id', 'sku', 'product_name', 'product_description', 'brand', 'category', 'price', 'sale_price', 'quantity'])
        purchase_table_filters = [*self.purchase_columns, *self.supplier_columns, *self.listing_columns, *self.catalogue_columns]
        order_table_filters = [*self.order_columns, *self.listing_columns, *self.catalogue_columns]
        supplier_table_filters = [*self.supplier_columns]
        platform_table_filters = [*self.platform_columns]

        self.allowed_tables = {
            'catalogue': [Catalogue],
            'listing': [Listing, Catalogue, Platform],
            'purchase': [Purchase, Supplier, Listing, Catalogue],
            'order': [Order, Listing, Catalogue],
            'supplier': [Supplier],
            'platform': [Platform]
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
    


    def getSqlalchemyClassByName(self, classname):
        # encryption of name can happend here
        try:
            target_class = None
            classname_str = str(classname).strip().lower()

            # (secure) validate if table class included in filter conidtions provided, example (purchase.id, supplier.id) but not supplier.user_id (vailidate recived column_name in allowed columns for current query)
            table_classes = self.allowed_tables[classname_str] if classname_str in self.allowed_tables else None
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

    def getSqlalchemyColumnByName(self, colname, table_name):
        target_column = None
        try:
            # table_name is tipical to class Order
            tablename_lower = str(table_name).strip().lower()
            current_columns = []

            table_class = self.getSqlalchemyClassByName(table_name)
            if not table_class:
                raise ValueError('found unknown table')

            # column_full_name = 'Supplier.user_id' # secuirty check
            column_full_name = '{}.{}'.format(table_name, colname)
            # check if Table.colname provided exist current table filters allowed option provided when init this class
            secuirty_check = column_full_name in self.tables_data[tablename_lower]
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
def getFilterBooleanClauseList(columns, operators, values, condition):
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
                column_class = export_sqlalchemy.getSqlalchemyColumnByName(column_name, table_name)

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
    from .models import Supplier, Catalogue, Listing, Purchase, Order, Platform, ListingPlatform
    
    # this is list of sqlalchemy filter conidtions recived from message (sqlalchemy.sql.elements.booleanclauselist) (incase no values it will not make issues)
    filterBooleanClauseList = getFilterBooleanClauseList(columns, operators, values, condition)
    export_tables = ['catalogue', 'listing', 'purchase', 'order', 'supplier']
    response =  {'success': True, 'message': '', 'data': [], 'column_names': [], 'excel_response': None}

    if table_name not in export_tables:
        return {'success': False, 'message': 'Invalid Table Selected'}
    
    # catalogue
    if table_name == 'catalogue':
        # my sqlalchemy export filter lib simple as filter query, and it makes user securly by clicking btns create any sqlalchemy result securely with simple words, it can used in create custom charts dynamic
        response['data'] = db.session.query(Catalogue).filter(and_(Catalogue.user_id==current_user_id), filterBooleanClauseList).all()
        if response['data']:
            response['column_names'] = getAllowedColumns(column_names=Catalogue.__table__.columns.keys(), ignored_columns=['user_id', 'product_image'])
            
            if usejson == False:
                response['excel_response'] = flask_excel.make_response_from_query_sets(response['data'], response['column_names'], 'csv', file_name='catalogues')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (catalogues)'
        return response
    # listing
    elif table_name == 'listing':
        response['data'] = db.session.query(Listing).join(
            Catalogue
        ).join(
            ListingPlatform, Listing.id==ListingPlatform.listing_id
        ).join(
            Platform, ListingPlatform.platform_id==Platform.id
        ).filter(
            and_(Catalogue.user_id == current_user_id),
            filterBooleanClauseList
        ).all()                    
        if response['data']:
            export_data = []

            response['column_names'] = ['id', 'sku', 'product_name', 'product_description', 'brand', 'category', 'price', 'sale_price', 'quantity', 'created_date', 'updated_date', 'dashboard_id', 'catalogue_id', 'platform']
            export_data.append(response['column_names'])
            
            for item in response['data']:
                platforms = ",".join(["{}.{}".format(listing_platform.platform.id, listing_platform.platform.name) for listing_platform in item.platforms])
                export_data.append([item.id, item.sku, item.product_name, item.product_description, item.brand, item.category, item.price, item.sale_price, item.quantity, item.created_date, item.updated_date, item.dashboard_id, item.catalogue_id, platforms])
            
            response['data'] = export_data
            if usejson == False:
                response['excel_response'] = flask_excel.make_response_from_array(response['data'], 'csv', file_name='listings')
                #response['excel_response'] = flask_excel.make_response_from_query_sets(x, response['column_names'], 'csv', file_name='listings')
        else:
            response['success'] = False
            response['message'] = 'No Matched Results Found (listings).'
        return response

    elif table_name == 'purchase':
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
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Top Ordered Products',
                        'background_colors': [ 'rgba(255, 99, 132, 0.2)', 'rgba(255, 159, 64, 0.2)', 'rgba(255, 205, 86, 0.2)', 'rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(201, 203, 207, 0.2)'],
                        'border_colors': [ 'rgb(255, 99, 132)', 'rgb(255, 159, 64)', 'rgb(255, 205, 86)', 'rgb(75, 192, 192)', 'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(201, 203, 207)' ],
                        'description': 'Products with the largest number of orders'
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
                        'type': 'pie',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'least demanded products',
                        'background_colors': [ 'rgba(255, 99, 132, 0.2)', 'rgba(255, 159, 64, 0.2)', 'rgba(255, 205, 86, 0.2)', 'rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(201, 203, 207, 0.2)'],
                        'border_colors': [ 'rgb(255, 99, 132)', 'rgb(255, 159, 64)', 'rgb(255, 205, 86)', 'rgb(75, 192, 192)', 'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(201, 203, 207)' ],
                        'description': 'Products with the lowest number of orders'
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
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'Most purchased products',
                        'description': 'Products with the largest number of purchases'
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
                        'type': 'bar',
                        'data': chartdata['data'],
                        'labels': chartdata['labels'],
                        'label': 'least purchased products',
                        'description': 'Products with the lowest number of purchases'
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
            print(type(locations_string))
            print(locations_string)
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