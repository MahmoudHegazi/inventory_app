import requests
import sys
from flask import Flask, app, Blueprint, session, redirect, url_for, Response, request, jsonify, Request, Response, current_app
from functools import wraps
from .models import *
from sqlalchemy import or_, and_, func , asc, desc, text, select
from datetime import datetime, timedelta
from .functions import valid_ourapi_key, get_filter_params, pass_api_request, getQueryLimit

api = Blueprint('api', __name__)

# this handle everything before reach api endpoints, small check fo session stored value for safe in endpoints
def apikey_required(fn):
    # get the name of given function
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            param_apikey = request.args.get('apikey', None)
            if param_apikey is not None:
                db_apikey = OurApiKeys.query.filter_by(key=param_apikey).one_or_none()
                if db_apikey is not None and db_apikey.user and db_apikey.user.id:
                    #return str(request.remote_addr)
                    # check if key expired or not
                    if datetime.utcnow() < db_apikey.expiration_date:
                        # to achive the target anti simple bot and block bot forever you need insert logs for invalid right now better for db, right now max 2 minutes as no new log created new requests will not calcauted
                        # simple advanced anti scraper, anti api abuse, anti bots (max delay 2 minutes always but with bots or not follow rules will blocked for ever no db recoreds added for block also block happend in inner before even any action done in db, all done is 2 sqlalchemy check, so if bot keep resend and block it not effect performance or db much )
                        can_pass = pass_api_request(db_apikey.id, db)
                        if can_pass:
                            if valid_ourapi_key(db_apikey, db):
                                # if everything valid, incerse the total requests of this key by 1 or if for any reason mistake it pass previous if and total >= limit it will set total to limit so next time after check blocked before reach here, if for any reason error happend it will not assign session var and will raise exception
                                total_requests = int(db_apikey.total_requests)
                                requests_limit = int(db_apikey.key_limit)
                                db_apikey.total_requests = int(total_requests + 1) if (total_requests < requests_limit) else requests_limit
                                db_apikey.update()
                                session['ourapi_apikey_id'] = db_apikey.id

                                return fn(*args, **kwargs)
                            else:
                                return jsonify({'code': 400, 'message': 'You exceeded the limit for that key try again tomorrow, or try another key.'}), 422
                        else:
                            return jsonify({'code': 422, 'message': 'Please wait a while between requests, you have been blocked for 2 minutes, continue refreshing will incerse the wait time.'}), 422
                    else:
                        return jsonify({'code': 403, 'message': 'The key has expired, please renew it.'}), 403
                
                # not logged in user redirect to sign_in
        except:
            print('error in api_login_required {}'.format(sys.exc_info()))
            return jsonify({'code': 500, 'message': 'system error.'}), 500

        return jsonify({'code': 400, 'message': 'please provide valid apikey.'}), 400
    return decorator


### todo using api_keys_logs.created_date to delay user requests every  (also there are limit in db usally it 100 requests so even is 100 will not take one time as he free user)
# 15 requets within 2 min (ddos reducer) wait for 2 min, need cal actualy how long the query takes to know how many min, but goal reduce ddos and better performance by let user wait bettwen 10 requests if intented to get all data
### todo continue logs in all endpoints new_log.insert()
@api.route('/api/get_suppliers', methods=['GET'])
@apikey_required
def get_suppliers():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    
    try:
        filters = {
            'id': Supplier.id==request.args.get('id') if request.args.get('id', None) else None,
            'address': Supplier.address.like('%{}%'.format(request.args.get('address'))) if request.args.get('address', None) else None,
            'name': Supplier.name.like('%{}%'.format(request.args.get('name'))) if request.args.get('name', None) else None,
            'phone': Supplier.phone==request.args.get('phone') if request.args.get('phone', None) else None,
            'created_date': Supplier.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = Supplier.query
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)


            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))
            
            data = [supplier.format() for supplier in query.all()]
            status = 200
            # insert only log if have apikey and user not invalid apikey 
            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_suppliers'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in supplier_endpoint {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status


@api.route('/api/get_categories', methods=['GET'])
@apikey_required
def get_categories():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    filters = {}
    user_id = None
    try:
        filters = {
            'id': Category.id==request.args.get('id') if request.args.get('id', None) else None,
            'level': Category.level==request.args.get('level') if request.args.get('level', None) else None,
            'label': Category.label.like('%{}%'.format(request.args.get('label'))) if request.args.get('label', None) else None,
            'code': Category.code==request.args.get('code') if request.args.get('code', None) else None,
            'parent_code': Category.parent_code==request.args.get('parent_code') if request.args.get('parent_code', None) else None,
            'created_date': Category.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        

        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            query = Category.query
            filter_params = get_filter_params(filters)
            # if any params add only sqlalchemy binaryexpression objects
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            user_id = db_apikey.user.id
            data = [category.format() for category in query.all()]
            status = 200
            # insert only log if have apikey and user not invalid apikey 
            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_categories'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_categories {}'.format(sys.exc_info()))
        status = 500

    finally:            
        return jsonify(data), status


@api.route('/api/get_catalogues', methods=['GET'])
@apikey_required
def get_catalogues():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Catalogue.id==request.args.get('id') if request.args.get('id', None) else None,
            'sku': Catalogue.sku==request.args.get('sku') if request.args.get('sku', None) else None,
            'product_name': Catalogue.product_name==request.args.get('product_name') if request.args.get('product_name', None) else None,
            'product_description': Catalogue.product_description.like('%{}%'.format(request.args.get('product_description'))) if request.args.get('product_description', None) else None,
            'brand': Catalogue.brand==request.args.get('brand') if request.args.get('brand', None) else None,
            'category_id': Catalogue.category_id==request.args.get('category_id') if request.args.get('category_id', None) else None,
            'price': Catalogue.price==request.args.get('price') if request.args.get('price', None) else None,
            'quantity': Catalogue.quantity==request.args.get('quantity') if request.args.get('quantity', None) else None,
            'product_model': Catalogue.product_model==request.args.get('product_model') if request.args.get('product_model', None) else None,
            'upc': Catalogue.upc==request.args.get('upc') if request.args.get('upc', None) else None,
            'reference_type': Catalogue.reference_type==request.args.get('reference_type') if request.args.get('reference_type', None) else None,
            'created_date': Catalogue.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:

            query = Catalogue.query
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [catalogue.format() for catalogue in query.all()]
            status = 200
            # insert only log if have apikey and user not invalid apikey 
            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_catalogues'))
            new_log.insert()

        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_categories {}'.format(sys.exc_info()))
        status = 500
    finally:
        return jsonify(data), status

@api.route('/api/get_listings', methods=['GET'])
@apikey_required
def get_listings():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Catalogue.id==request.args.get('id') if request.args.get('id', None) else None,
            'catalogue_id': Catalogue.catalogue_id==request.args.get('catalogue_id') if request.args.get('catalogue_id', None) else None,
            'currency_iso_code': Catalogue.currency_iso_code==request.args.get('currency_iso_code') if request.args.get('currency_iso_code', None) else None,
            'quantity_threshold': Catalogue.quantity_threshold==request.args.get('quantity_threshold') if request.args.get('quantity_threshold', None) else None,
            'offer_id': Catalogue.offer_id==request.args.get('offer_id') if request.args.get('offer_id', None) else None,
            'created_date': Catalogue.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            query = Listing.query
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [catalogue.format() for catalogue in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_listings'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_listings {}'.format(sys.exc_info()))
        status = 500
    finally:
        return jsonify(data), status


@api.route('/api/get_purchases', methods=['GET'])
@apikey_required
def get_purchases():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Purchase.id==request.args.get('id') if request.args.get('id', None) else None,
            'quantity': Purchase.quantity==request.args.get('quantity') if request.args.get('quantity', None) else None,
            'date': Purchase.date==request.args.get('date') if request.args.get('date', None) else None,
            'supplier_id': Purchase.supplier_id==request.args.get('supplier_id') if request.args.get('supplier_id', None) else None,
            'listing_id': Purchase.listing_id==request.args.get('listing_id') if request.args.get('listing_id', None) else None,
            'created_date': Purchase.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(Purchase)

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [purchase.format() for purchase in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_purchases'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_purchase {}'.format(sys.exc_info()))
        status = 500
    finally:
        return jsonify(data), status




# order taxes included with each order
@api.route('/api/get_orders', methods=['GET'])
@apikey_required
def get_orders():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Order.id==request.args.get('id') if request.args.get('id', None) else None,
            'listing_id': Order.listing_id==request.args.get('listing_id') if request.args.get('listing_id', None) else None,
            'date': Order.date==request.args.get('date') if request.args.get('date', None) else None,
            'customer_firstname': Order.customer_firstname==request.args.get('customer_firstname') if request.args.get('customer_firstname', None) else None,
            'customer_lastname': Order.customer_lastname==request.args.get('customer_lastname') if request.args.get('customer_lastname', None) else None,
            'total_cost': Order.total_cost==request.args.get('total_cost') if request.args.get('total_cost', None) else None,
            'commercial_id': Order.commercial_id==request.args.get('commercial_id') if request.args.get('commercial_id', None) else None,
            'commission': Order.commission==request.args.get('commission') if request.args.get('commission', None) else None,
            'currency_iso_code': Order.currency_iso_code==request.args.get('currency_iso_code') if request.args.get('currency_iso_code', None) else None,
            'phone': Order.phone==request.args.get('phone') if request.args.get('phone', None) else None,
            'street_1': Order.street_1.like('%{}%'.format(request.args.get('street_1'))) if request.args.get('street_1', None) else None,
            'street_2': Order.street_2.like('%{}%'.format(request.args.get('street_2'))) if request.args.get('street_2', None) else None,
            'zip_code': Order.zip_code==request.args.get('zip_code') if request.args.get('zip_code', None) else None,
            'city': Order.city==request.args.get('city') if request.args.get('city', None) else None,
            'country': Order.country==request.args.get('country') if request.args.get('country', None) else None,
            'can_refund': Order.can_refund==request.args.get('can_refund') if request.args.get('can_refund', None) else None,
            'order_id': Order.order_id==request.args.get('order_id') if request.args.get('order_id', None) else None,
            'product_title': Order.product_title==request.args.get('product_title') if request.args.get('product_title', None) else None,
            'product_sku': Order.product_sku==request.args.get('product_sku') if request.args.get('product_sku', None) else None,
            'created_date': Order.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(Order)

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [order.format() for order in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_orders'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_orders {}'.format(sys.exc_info()))
        status = 500
    finally:
        return jsonify(data), status


# all taxes
@api.route('/api/get_ordertaxes', methods=['GET'])
@apikey_required
def get_ordertaxes():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': OrderTaxes.id==request.args.get('id') if request.args.get('id', None) else None,
            'type': OrderTaxes.type==request.args.get('type') if request.args.get('type', None) else None,
            'order_id': OrderTaxes.order_id==request.args.get('order_id') if request.args.get('order_id', None) else None,
            'amount': OrderTaxes.amount==request.args.get('amount') if request.args.get('amount', None) else None,
            'code': OrderTaxes.code==request.args.get('code') if request.args.get('code', None) else None,
            'created_date': OrderTaxes.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(OrderTaxes)

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [ordertax.format() for ordertax in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_ordertaxes'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_ordertaxes {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status


@api.route('/api/get_platform', methods=['GET'])
@apikey_required
def get_platform():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Platform.id==request.args.get('id') if request.args.get('id', None) else None,
            'name': Platform.name==request.args.get('name') if request.args.get('name', None) else None,
            'created_date': Platform.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(Platform)
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [platform.format() for platform in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_platform'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_platform {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status

@api.route('/api/get_condition', methods=['GET'])
@apikey_required
def get_condition():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': Condition.id==request.args.get('id') if request.args.get('id', None) else None,
            'name': Condition.name==request.args.get('name') if request.args.get('name', None) else None,
            'created_date': Condition.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(Condition)
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [condition.format() for condition in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_condition'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except:
        print('error in get_condition {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status



@api.route('/api/get_warehouse_locations', methods=['GET'])
@apikey_required
def get_warehouse_locations():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': WarehouseLocations.id==request.args.get('id') if request.args.get('id', None) else None,
            'name': WarehouseLocations.name==request.args.get('name') if request.args.get('name', None) else None,
            'created_date': WarehouseLocations.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(WarehouseLocations)
            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [warehouse_loc.format() for warehouse_loc in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_warehouse_locations'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_warehouse_locations {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status

@api.route('/api/get_location_bins', methods=['GET'])
@apikey_required
def get_location_bins():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': LocationBins.id==request.args.get('id') if request.args.get('id', None) else None,
            'name': LocationBins.name==request.args.get('name') if request.args.get('name', None) else None,
            'created_date': LocationBins.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(LocationBins)

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [locationbin.format() for locationbin in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_location_bins'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_location_bins {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status


@api.route('/api/get_catalogue_locations', methods=['GET'])
@apikey_required
def get_catalogue_locations():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': CatalogueLocations.id==request.args.get('id') if request.args.get('id', None) else None,
            'name': WarehouseLocations.name==request.args.get('name') if request.args.get('name', None) else None,
            'created_date': CatalogueLocations.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(CatalogueLocations).join(
                WarehouseLocations, CatalogueLocations.location_id==WarehouseLocations.id
                )

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [catalogue_location.format() for catalogue_location in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_catalogue_locations'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_catalogue_locations {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status

@api.route('/api/get_catalogue_locations_bins', methods=['GET'])
@apikey_required
def get_catalogue_locations_bins():
    data = {'code': 400, 'message': 'bad request'}
    status = 400
    try:
        filters = {
            'id': CatalogueLocationsBins.id==request.args.get('id') if request.args.get('id', None) else None,
            'created_date': CatalogueLocationsBins.created_date==request.args.get('created_date') if request.args.get('created_date', None) else None
            }
        ourapi_apikey_id = session.get('ourapi_apikey_id', None)
        db_apikey = OurApiKeys.query.filter_by(id=ourapi_apikey_id).one_or_none()
        if ourapi_apikey_id and db_apikey and db_apikey.user.id:
            
            query = db.session.query(CatalogueLocationsBins)

            filter_params = get_filter_params(filters)
            if filter_params:
                query = query.filter(*filter_params)

            # sqlalchemy limit
            max = getQueryLimit(request)
            if max is not None:
                query = query.limit(max)
            else:
                # default limit then if user not speacfiy valid max, or 100 if not speacfied in init
                query = query.limit(current_app.config.get('OURAPI_LIMIT', 100))

            data = [catalogue_locations_bins.format() for catalogue_locations_bins in query.all()]
            status = 200

            new_log = ApiKeysLogs(db_apikey.user.id, db_apikey.id, status=status, endpoint=url_for('api.get_catalogue_locations_bins'))
            new_log.insert()
        else:
            data = {'code': 400, 'message': 'please provide valid apikey.'}
            status = 400
    except Exception as e:
        print('error in get_catalogue_locations_bins {}'.format(sys.exc_info()))
        status = 500

    finally:
        return jsonify(data), status

######################################## API Guide and Health_check and test endpoint for apps for all endpoints #################################################
@api.route('/api', methods=['GET'])
@apikey_required
def api_index():
    endpoints_urls = []
    error = None
    try:
        endpoints_urls = [
            {'url': url_for('api.get_catalogue_locations_bins'), 'methods':['GET'], 'params': ['id', 'created_date']},
            {'url': url_for('api.get_warehouse_locations'), 'methods':['GET'], 'params': ['id', 'name', 'created_date']},
            {'url': url_for('api.get_catalogue_locations'), 'methods':['GET'], 'params': ['id', 'name', 'created_date']},
            {'url': url_for('api.get_location_bins'), 'methods':['GET'], 'params': ['id', 'name', 'created_date']},
            {'url': url_for('api.get_categories'), 'methods':['GET'], 'params': ['id', 'level', 'label', 'code', 'parent_code', 'created_date']},
            {'url': url_for('api.get_catalogues'), 'methods':['GET'], 'params': ['id', 'sku', 'product_name', 'product_description', 'brand', 'category_id', 'price', 'quantity', 'product_model', 'upc', 'reference_type', 'created_date']},
            {'url': url_for('api.get_ordertaxes'), 'methods':['GET'], 'params': ['id', 'type', 'order_id', 'amount', 'code', 'created_date']},
            {'url': url_for('api.get_suppliers'), 'methods':['GET'], 'params': ['id', 'address', 'name', 'phone', 'created_date']},
            {'url': url_for('api.get_purchases'), 'methods':['GET'], 'params': ['id', 'quantity', 'date', 'supplier_id', 'listing_id', 'created_date']},
            {'url': url_for('api.get_condition'), 'methods':['GET'], 'params': ['id', 'name', 'created_date']},
            {'url': url_for('api.get_listings'), 'methods':['GET'], 'params': ['id', 'catalogue_id', 'currency_iso_code', 'quantity_threshold', 'offer_id', 'created_date']},
            {'url': url_for('api.get_platform'), 'methods':['GET'], 'params': ['id', 'name', 'created_date']},
            {'url': url_for('api.get_orders'), 'methods':['GET'], 'params': ['id', 'listing_id', 'date', 'customer_firstname', 'customer_lastname', 'total_cost', 'commercial_id', 'commission', 'currency_iso_code', 
             'phone', 'street_1', 'street_2', 'zip_code', 'city', 'country', 'can_refund', 'order_id', 'product_title', 'product_sku', 'created_date']}
            ]
    except:
        error = {'code': 500, 'message': 'internal server error'}
    finally:
        if error is None:
            return jsonify(endpoints_urls)
        else:
            return jsonify(error)


