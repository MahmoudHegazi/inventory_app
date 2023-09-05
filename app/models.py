import datetime
import sys
import decimal
#from sqlalchemy.types import TypeDecorator
from sqlalchemy import desc, asc
from sqlalchemy.orm import relationship, backref
#from bcrypt import gensalt, hashpw, checkpw
from sqlalchemy import DateTime, Enum, func
from sqlalchemy.dialects.mysql import FLOAT
from sqlalchemy.ext.declarative import declarative_base
from app import db
from flask_login import UserMixin
from sqlalchemy.orm.attributes import get_history
################################ ---------- Tables for Authentication (Start) ---------------- #########################

Base = declarative_base()


class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(45), nullable=True, default='Dashboard')
    num_of_listings = db.Column(db.Integer, nullable=True, default=0)
    num_of_orders = db.Column(db.Integer, nullable=True, default=0)
    sum_of_monthly_purchases = db.Column(db.DECIMAL(precision=12, scale=2, asdecimal=True), nullable=True, default=0.00)    
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    listings = db.relationship("Listing", backref="dashboard", cascade="all, delete", passive_deletes=True)
    platforms = db.relationship("Platform", backref="dashboard", cascade="all, delete", passive_deletes=True)
    locations = db.relationship("WarehouseLocations", backref="dashboard", cascade="all, delete", passive_deletes=True)
    categories = db.relationship("Category", backref="dashboard", cascade="all, delete", passive_deletes=True)
    user = db.relationship("User", backref="dashboard", cascade="all, delete", passive_deletes=True, uselist=False)


    def __init__(self, title='Dashboard', num_of_listings=0, num_of_orders=0, sum_of_monthly_purchases=0.00):
        self.title = title
        self.num_of_listings = num_of_listings
        self.num_of_orders = num_of_orders
        self.sum_of_monthly_purchases = sum_of_monthly_purchases        

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'title': self.title,
        'num_of_listings': self.num_of_listings,
        'num_of_orders': self.num_of_orders,
        'sum_of_monthly_purchases': self.sum_of_monthly_purchases,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }


#, autoincrement=True email
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(45), nullable=False)
    uname = db.Column(db.String(45), nullable=False, unique=True)
    upass = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)    
    image = db.Column(db.String(150), default='default_user.png')
    approved = db.Column(db.Boolean, nullable=False, default=True)
    authenticated = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)    
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    suppliers = db.relationship("Supplier", backref="user", cascade="all, delete", passive_deletes=True)
    roles = db.relationship("UserRoles", backref="user", cascade="all, delete", passive_deletes=True)
    meta = db.relationship("UserMeta", back_populates='user', cascade="all, delete", passive_deletes=True)
    catalogues = db.relationship('Catalogue', backref='user', cascade="all, delete", lazy='dynamic', passive_deletes=True)

    def __init__(self, dashboard_id, name, uname, email, upass, image='default_user.png', approved=True):
        self.dashboard_id = dashboard_id
        self.name = name
        self.uname = uname
        self.email = email
        self.upass = upass
        self.image = image
        self.approved = approved

    def is_active(self):
        """True, as all users are active."""
        return True if self.approved else False

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email
    
    def isAdmin(self):
        if 'admin' in [role.role.name for role in self.roles]:
            return True
        else:
            return False

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def getRoles(self):
        return [userrole.role.name for userrole in self.roles]

    def __repr__(self):
        return f'User: ID: {self.id}, Username: {self.uname}'
    
    def format(self):
        return {
        'id': self.id,
        'dashboard_id': self.dashboard_id,
        'name': self.name,
        'uname': self.uname,
        'email': self.email,
        'image': self.image,
        'approved': self.approved,
        'authenticated': self.authenticated,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class UserMeta(db.Model):
    __tablename__ = 'usermeta'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    key = db.Column(db.String(45), nullable=False)
    value = db.Column(db.String(255), nullable=True, default=None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    user = db.relationship('User', back_populates='meta')
    def __init__(self, user_id, key, value=None):
        self.user_id = user_id
        self.key = key
        self.value = value

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'user_id': self.user_id,
        'key': self.key,
        'value': self.value,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }
    

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(45), nullable=False, unique=True)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    users = db.relationship("UserRoles", backref="role", cascade="all, delete", passive_deletes=True)
    def __init__(self, name):
        self.name = name

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'name': self.name,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'user_id': self.user_id,
        'role_id': self.role_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }


################################ ---------- Tables for Authentication (End) ---------------- #########################

################################ ---------- Tables for Inventory (Start) ---------------- #########################
class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(45), nullable=False)
    address = db.Column(db.String(125), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    purchases = db.relationship("Purchase", backref="supplier", cascade="all, delete", passive_deletes=True)
    
    def __init__(self, name, user_id, phone, address):
        self.name = name
        self.user_id = user_id
        self.phone = phone
        self.address = address

    def __repr__(self):
        return f'{self.name}'

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'name': self.name,
        'user_id': self.user_id,
        'phone': self.phone,
        'address': self.address,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }


################################ ---------- Tables for Dashboard Catagories (Sart) ---------------- #########################
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, autoincrement=True, nullable=False, primary_key=True)
    code = db.Column(db.String(45), nullable=False, unique=True)
    label = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Integer, nullable=True, default=0)
    parent_code = db.Column(db.String(45), nullable=True, default='')
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    catalogues = db.relationship("Catalogue", backref="category")

    def __init__(self, dashboard_id, code, label, level=0, parent_code=''):
        self.dashboard_id = dashboard_id
        self.code = code
        self.label = label
        self.level = level
        self.parent_code = parent_code

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'code': self.code,
        'label': self.label,
        'level': self.level,
        'parent_code': self.parent_code,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

################################ ---------- Tables for Dashboard Catagories (End) ---------------- #########################

# sku, product_name, product_description, product_name, product_description, brand, category_code, price, sale_price, quantity, product_model,
# condition, upc, location, product_image, 
# uselist=False make the one-to-one not return list of classes 
class Catalogue(db.Model): # catelouge
    __tablename__ = 'catalogue'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sku = db.Column(db.String(45), nullable=False)
    product_name = db.Column(db.String(500), nullable=True)
    product_description = db.Column(db.String(5000), nullable=True)
    brand = db.Column(db.String(255), nullable=True)
    category_code = db.Column(db.String(45), db.ForeignKey('category.code', ondelete="SET NULL", onupdate="CASCADE"), nullable=True, default=None)
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    sale_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity = db.Column(db.Integer, nullable=True)
    product_model = db.Column(db.String(255), nullable=True)
    condition = db.Column(db.String(255), nullable=True)
    upc = db.Column(db.String(255), nullable=True)
    product_image = db.Column(db.String(45), nullable=True, default='default_product.png')
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    listings = db.relationship("Listing", backref="catalogue", cascade="all, delete", passive_deletes=True)
    locations = db.relationship("CatalogueLocations", backref='catalogue', cascade="all, delete", passive_deletes=True)

    def __init__(self, sku, user_id, product_name=None, product_description=None, brand=None, category_code=None, price=0.00, sale_price=0.00, quantity=None, product_model=None, condition=None, upc=None):
        self.sku = sku
        self.product_name = product_name
        self.user_id = user_id
        self.product_description = product_description
        self.brand = brand
        self.category_code = category_code
        self.price = price
        self.sale_price = sale_price
        self.quantity = quantity
        self.product_model = product_model
        self.condition = condition
        self.upc = upc

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        # update listings data when update done with event after_update (no use event)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def format(self):      
        return {
        'id': self.id,
        'sku': self.sku,
        'product_name': self.product_name,
        'product_description': self.product_description,
        'brand': self.brand,
        'category_code': self.category_code,
        'price': str(self.price),
        'sale_price': str(self.sale_price),
        'quantity': self.quantity,
        'product_model': self.product_model,
        'condition': self.condition,
        'product_image': self.product_image,
        'upc': self.upc,
        'location': ",".join([loc.warehouse_location.name for loc in self.locations]),
        'locations': [{'location_name': catalogue_loc.warehouse_location.name, 'bins': [catalogue_loc_bin.bin.name for catalogue_loc_bin in catalogue_loc.bins]} for catalogue_loc in self.locations]
        }


class Listing(db.Model):
    __tablename__ = 'listing'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sku = db.Column(db.String(45), nullable=False)
    product_name = db.Column(db.String(500), nullable=True)
    product_description = db.Column(db.String(5000), nullable=True)
    brand = db.Column(db.String(255), nullable=True)    
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    sale_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity = db.Column(db.Integer, nullable=True)
    category_code = db.Column(db.String(255), nullable=True)
    category_label = db.Column(db.String(255), nullable=True, default=None)
    # new    
    active = db.Column(db.Boolean, nullable=True, default=None)
    discount_end_date = db.Column(DateTime, nullable=True, default=None)
    discount_start_date = db.Column(DateTime, nullable=True, default=None)
    unit_discount_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    unit_origin_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity_threshold = db.Column(db.Integer, nullable=True, default=None)
    currency_iso_code = db.Column(db.String(45), nullable=True, default=None)
    shop_sku = db.Column(db.String(45), nullable=True, default=None)
    offer_id = db.Column(db.Integer, nullable=True, default=None)
    reference = db.Column(db.String(255), nullable=True, default=None)
    reference_type = db.Column(db.String(255), nullable=True, default=None)
    

    image = db.Column(db.String(45), nullable=True, default='default_listing.png')
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    catalogue_id = db.Column(db.Integer, db.ForeignKey('catalogue.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    purchases = db.relationship("Purchase", backref="listing", cascade="all, delete", passive_deletes=True)
    orders = db.relationship("Order", backref="listing", cascade="all, delete", passive_deletes=True)
    platforms = db.relationship("ListingPlatform", backref="listing", cascade="all, delete", passive_deletes=True)

    def __init__(self, dashboard_id, catalogue_id, active=None, discount_start_date=None, discount_end_date=None, unit_discount_price=None, unit_origin_price=None, quantity_threshold=None, currency_iso_code=None, shop_sku=None, offer_id=None, reference=None, reference_type=None, image='default_listing.png'):
        self.dashboard_id = dashboard_id
        self.catalogue_id = catalogue_id
        self.active = active
        self.discount_start_date = discount_start_date
        self.discount_end_date = discount_end_date        
        self.unit_discount_price = unit_discount_price
        self.unit_origin_price = unit_origin_price
        self.quantity_threshold = quantity_threshold
        self.currency_iso_code = currency_iso_code
        self.shop_sku = shop_sku
        self.offer_id = offer_id
        self.reference = reference
        self.reference_type = reference_type
        self.image = image

        # automatic fill catalogue data in listing data, also incase catalogue not found stop initalize and throw error which captured by route try and except and print the flash message for user inform him error in creating which right
        try:
            target_catalogue = Catalogue.query.filter_by(id=self.catalogue_id).one_or_none()
            if target_catalogue is not None:
                self.sku = target_catalogue.sku
                self.product_name = target_catalogue.product_name
                self.product_description = target_catalogue.product_description
                self.brand = target_catalogue.brand
                self.category_code = target_catalogue.category_code
                if target_catalogue.category:
                    self.category_label = target_catalogue.category.label
                self.price = target_catalogue.price
                self.sale_price = target_catalogue.sale_price
                self.quantity = target_catalogue.quantity
            else:
                raise ValueError('unable to find the target catalogue')
        except Exception as e:
            print('error while setting default listing data {}'.format(e))
            raise e         
        
        
    def insert(self):        
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()
        # here catalogue id not changed but listing need update (only can effect listing)
        #if self.quantity != self.catalogue.quantity:
        #    self.catalogue.quantity = self.quantity
        #    self.catalogue.update()

    def sync_listing(self):
        print("synced")
        if self.sku != self.catalogue.sku:
            self.sku = self.catalogue.sku
        if self.product_name != self.catalogue.product_name:
            self.product_name = self.catalogue.product_name
        if self.product_description != self.catalogue.product_description:
            self.product_description = self.catalogue.product_description
        if self.brand != self.catalogue.brand:
            self.brand = self.catalogue.brand
        if self.category_code != self.catalogue.category_code:
            self.category_code = self.catalogue.category_code
        if self.catalogue.category and self.catalogue.category.label != self.category_label:
            self.category_label = self.catalogue.category.label
        if self.price != self.catalogue.price:
            self.price = self.catalogue.price
        if self.sale_price != self.catalogue.sale_price:
            self.sale_price = self.catalogue.sale_price
        if self.quantity != self.catalogue.quantity:
            self.quantity = self.catalogue.quantity
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        listing_platforms = [listing_platform.platform.name for listing_platform in self.platforms]
        # for all locations string of this listing
        listing_location_strings = []
        # for looping in js over location data objects
        listing_locations = []
        listing_bins_arr = []
        for catalogue_loc in self.catalogue.locations:
            loc_name = catalogue_loc.warehouse_location.name
            loc_obj = {'location': loc_name, 'bins': [catalogue_loc_bin.bin.name for catalogue_loc_bin in catalogue_loc.bins]}
            listing_location_strings.append(loc_name)
            listing_locations.append(loc_obj)
            listing_bins_arr = [*listing_bins_arr, *loc_obj['bins']]

        return {
        'id': self.id,
        'dashboard_id': self.dashboard_id,
        'catalogue_id': self.catalogue_id,
        'sku': self.sku,
        'product_name': self.product_name,
        'product_description': self.product_description,
        'brand': self.brand,
        'category_code': self.category_code,
        'price': str(self.price),
        'sale_price': str(self.sale_price),
        'quantity': self.quantity,
        'image': self.image,
        'platform': ",".join(listing_platforms),
        'platforms': listing_platforms,
        'location': ",".join(listing_location_strings),
        'locations': listing_locations,
        'bin': ",".join(listing_bins_arr),
        'category': self.catalogue.category.label if self.catalogue.category and self.catalogue.category.label else '',
        }

class Purchase(db.Model):
    __tablename__ = 'purchase'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    

    def __init__(self, quantity, date, supplier_id, listing_id):
        self.quantity = quantity
        self.date = date
        self.supplier_id = supplier_id
        self.listing_id = listing_id
        

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'quantity': self.quantity,
        'date': self.date,
        'supplier_name': self.supplier.name,
        'supplier_id': self.supplier_id,
        'listing_id': self.listing_id,        
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=True, default=0)
    date = db.Column(db.DateTime, nullable=True, default=None)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    customer_firstname = db.Column(db.String(50), nullable=True, default='')
    customer_lastname = db.Column(db.String(50), nullable=True, default='')
    tax = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    shipping = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    shipping_tax = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    commission = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    total_cost = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)


    def __init__(self, listing_id, quantity=0, date=None, customer_firstname='', customer_lastname='', tax=0.0, shipping=0.0, shipping_tax=0.0, commission=0.0, total_cost=0.0):
        self.listing_id = listing_id
        self.quantity = quantity
        self.date = date
        self.customer_firstname = customer_firstname
        self.customer_lastname = customer_lastname
        self.tax = tax
        self.shipping = shipping
        self.shipping_tax = shipping_tax
        self.commission = commission
        self.total_cost = total_cost

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    # important convert date to string when sent to js in json format to get the same date displayed by jinja2
    def format(self):
        return {
        'id': self.id,
        'listing_id': self.listing_id,
        'quantity': self.quantity,
        'date': str(self.date),
        'customer_firstname': self.customer_firstname,
        'customer_lastname': self.customer_lastname,
        'tax': str(self.tax),
        'shipping': str(self.shipping),
        'shipping_tax': str(self.shipping_tax),
        'commission': str(self.commission),
        'total_cost': str(self.total_cost),
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }
    


################################ ---------- Tables for Dashboard Plateforms (Start) ---------------- #########################

class Platform(db.Model):
    __tablename__ = 'platform'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)    
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    plateforms = db.relationship("ListingPlatform", backref="platform", cascade="all, delete", passive_deletes=True)

    def __init__(self, dashboard_id, name):
        self.dashboard_id = dashboard_id
        self.name = name


    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'dashboard_id': self.dashboard_id,
        'name': self.name,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }
    

class ListingPlatform(db.Model):
    __tablename__ = 'listing_platform'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)

    def __init__(self, listing_id, platform_id):
        self.listing_id = listing_id
        self.platform_id = platform_id

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'listing_id': self.listing_id,
        'platform_id': self.platform_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

################################ ---------- Tables for Dashboard Plateforms (End) ---------------- #########################

################################ ---------- Tables for Dashboard Warehouse Locations (Sart) ---------------- #########################
class WarehouseLocations(db.Model):
    __tablename__ = 'warehouse_locations'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    default = db.Column(db.Boolean, nullable=True, default=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    bins = db.relationship("LocationBins", backref="warehouse_location", cascade="all, delete", passive_deletes=True)
    catalogues_locations = db.relationship("CatalogueLocations", backref="warehouse_location", cascade="all, delete", passive_deletes=True)

    def __init__(self, name, dashboard_id, default=False):
        self.name = name
        self.dashboard_id = dashboard_id
        self.default = False

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'name': self.name,
        'dashboard_id': self.dashboard_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class LocationBins(db.Model):
    __tablename__ = 'location_bins'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    catalogues_bins = db.relationship("CatalogueLocationsBins", backref="bin", cascade="all, delete", passive_deletes=True)

    def __init__(self, name, location_id=None):
        self.name = name
        # some times use append to insert locations bins, incase not use it can accept direct insert
        if location_id:
            self.location_id = location_id
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'name': self.name,
        'location_id': self.location_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }



class CatalogueLocations(db.Model):
    __tablename__ = 'catalogue_locations'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    catalogue_id = db.Column(db.Integer, db.ForeignKey('catalogue.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    bins = db.relationship("CatalogueLocationsBins", backref="catalogue_locations", cascade="all, delete", passive_deletes=True)



    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'catalogue_id': self.catalogue_id,
        'location_id': self.location_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class CatalogueLocationsBins(db.Model):
    __tablename__ = 'catalogue_locations_bins'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('catalogue_locations.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('location_bins.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
        'id': self.id,
        'location_id': self.location_id,
        'bin_id': self.bin_id,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

################################ ---------- Tables for Dashboard Warehouse Locations (End) ---------------- #########################


################################ ---------- Tables for Inventory (End) ---------------- #########################
# some functions for automation
# before insert will let me able to set the columns values (done before commit) and after init (all working around init function and what passed)
@db.event.listens_for(Order, "before_insert")
def insert_order_hock(mapper, connection, target):
    try:
        scoped_session = db.create_scoped_session()
        target_listing = scoped_session.query(Listing).filter_by(id=target.listing_id).one_or_none()
        if target_listing is not None:
            listing_price = decimal.Decimal(target_listing.price)
            # handle for now static, tax is final number of tax for that item, shipping is price for shipping to the country, shipping_tax is fixed number added to result, commission fixed
            tax = decimal.Decimal(target.tax)
            shipping = decimal.Decimal(target.shipping)
            shipping_tax = decimal.Decimal(target.shipping_tax)
            commission = decimal.Decimal(target.commission)
            total_cost = decimal.Decimal(target.total_cost)
            # if total cost any number except 0 that's mean user decided to add it manual so not calcuate (in insert)
            if total_cost == 0:
                total_cost = (listing_price + tax + shipping + shipping_tax + commission)
                target.total_cost = total_cost
    except Exception as e:
        scoped_session.rollback()
        raise e
    finally:
        scoped_session.close()


# automatic after update Catalogue update it's listings data if any change on shared cells (1 side cascade)
@db.event.listens_for(Catalogue, "after_update")
def update_listing_on_catalogue_update(mapper, connection, target):    
    try:
        # there are already session within that event, and can not commited within this event, to keep app use sqlalchemy you need create new session and use it
        scoped_session = db.create_scoped_session()
        for alisting in target.listings:
            list_to_update = scoped_session.query(Listing).filter_by(id=alisting.id).one_or_none()
            if list_to_update:
                print('print executed {}'.format(target.sku))
                list_to_update.sku = target.sku
                list_to_update.product_name = target.product_name
                list_to_update.product_description = target.product_description
                list_to_update.brand = target.brand
                list_to_update.category_code = target.category_code
                if target.category:
                    list_to_update.category_label = target.category.label
                list_to_update.price = target.price
                list_to_update.sale_price = target.sale_price
                list_to_update.quantity = target.quantity
        scoped_session.commit()
    except Exception as e:
        scoped_session.rollback()
        print('Error in Updating catalogue event db function (update_listing_on_catalogue_update): {}'.format(e, sys.exc_info()))
        raise e
    finally:
        scoped_session.close()
"""
@db.event.listens_for(Order, "after_delete")
def after_delete_order(mapper, connection, target):    
    try:
        # there are already session within that event, and can not commited within this event, to keep app use sqlalchemy you need create new session and use it
        
        scoped_session = db.create_scoped_session()

        orders_total = sum([order.quantity for order in Listing.orders])

        # back catalogue quantity as it was before the deleted order quantity
        target_catalogue = scoped_session.query(Catalogue).filter_by(id=target.listing.catalogue.id).one_or_none()
        if target_catalogue:
            target_catalogue_quantity = target_catalogue.quantity
            target_catalogue_quantity += int(orders_total)
            target_catalogue.quantity = target_catalogue_quantity        
            scoped_session.commit()
        else:
            print('target_catalogue in after_delete_order not found, {}'.format(str(target_catalogue)))    

    except Exception as e:
        scoped_session.rollback()
        raise e
        print('Error in Updating catalogue event db function (update_listing_on_catalogue_update): {}'.format(e, sys.exc_info()))
    finally:
        scoped_session.close()
""" 
