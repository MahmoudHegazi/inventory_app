from urllib.parse import urlparse, urljoin
from flask import request

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
                   """ fastest way can done to convert get_array to db sqlalchemy objects,index (dynamic mapping) by client's excel file uploaded, sku title in first column or in last ignore additonal columns for flexiblty just 1 loop (validation for ux) """
                   db_row = {
                   "sku": current_row[catalogues_columns['sku']], 
                   "product_name": current_row[catalogues_columns['product_name']], 
                   "product_description": current_row[catalogues_columns['product_description']], 
                   "brand": current_row[catalogues_columns['brand']], 
                   "category": current_row[catalogues_columns['category']], 
                   "price": current_row[catalogues_columns['price']], 
                   "sale_price": current_row[catalogues_columns['sale_price']], 
                   "quantity": current_row[catalogues_columns['quantity']], 
                   "product_model": current_row[catalogues_columns['product_model']], 
                   "condition": current_row[catalogues_columns['condition']], 
                   "upc": current_row[catalogues_columns['upc']],
                   "location": current_row[catalogues_columns['location']]
                   }
                   db_rows.append(db_row)
                   
           return {'success': True, 'message': '', 'db_rows': db_rows}
       else:
           return catalogues_valid
           
    except Exception as e:
        raise e