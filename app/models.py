import datetime
import sys
#from sqlalchemy.types import TypeDecorator
from sqlalchemy import desc, asc
from sqlalchemy.orm import relationship, backref
#from bcrypt import gensalt, hashpw, checkpw
from sqlalchemy import DateTime, Enum
from sqlalchemy.dialects.mysql import FLOAT
from sqlalchemy.ext.declarative import declarative_base
from app import db
from flask_login import UserMixin
################################ ---------- Tables for Authentication (Start) ---------------- #########################

Base = declarative_base()

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
    dashboards = db.relationship("Dashboard", backref="user", cascade="all, delete", lazy='dynamic', passive_deletes=True)
    suppliers = db.relationship("Supplier", backref="user", cascade="all, delete", passive_deletes=True)
    roles = db.relationship("UserRoles", backref="user", cascade="all, delete", passive_deletes=True)
    catalogues = db.relationship('Catalogue', backref='user', cascade="all, delete", lazy='dynamic', passive_deletes=True)
    def __init__(self, name, uname, email, upass, image='default_user.png', approved=True):
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
        'name': self.name,
        'uname': self.uname,
        'email': self.email,
        'image': self.image,
        'approved': self.approved,
        'authenticated': self.authenticated,
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    purchases = db.relationship("Purchase", backref="supplier", cascade="all, delete", passive_deletes=True)
    
    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

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
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(45), nullable=True, default='New Dashboard')
    num_of_listings = db.Column(db.Integer, nullable=True, default=0)
    num_of_orders = db.Column(db.Integer, nullable=True, default=0)
    sum_of_monthly_purchases = db.Column(db.DECIMAL(precision=12, scale=2, asdecimal=True), nullable=True, default=0.00)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    listings = db.relationship("Listing", backref="dashboard", cascade="all, delete", passive_deletes=True)

    def __init__(self, user_id, title='New Dashboard', num_of_listings=0, num_of_orders=0, sum_of_monthly_purchases=0.00):
        self.user_id = user_id
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

# sku, product_name, product_description, product_name, product_description, brand, category, price, sale_price, quantity, product_model,
# condition, upc, location, product_image, 

# uselist=False make the one-to-one not return list of classes 
class Catalogue(db.Model): # catelouge
    __tablename__ = 'catalogue'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sku = db.Column(db.String(16), nullable=False)
    product_name = db.Column(db.String(255), nullable=True)
    product_description = db.Column(db.String(1000), nullable=True)
    brand = db.Column(db.String(45), nullable=True)
    category = db.Column(db.String(45), nullable=True)
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    sale_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity = db.Column(db.Integer, nullable=True)
    product_model = db.Column(db.String(45), nullable=True)
    condition = db.Column(db.String(45), nullable=True)
    upc = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    product_image = db.Column(db.String(45), nullable=True, default='default_product.png')
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    listings = db.relationship("Listing", backref="catalogue", cascade="all, delete", passive_deletes=True)

    def __init__(self, sku, user_id, product_name=None, product_description=None, brand=None, category=None, price=0.00, sale_price=0.00, quantity=None, product_model=None, condition=None, upc=None, location=None):
        self.sku = sku
        self.product_name = product_name
        self.user_id = user_id
        self.product_description = product_description
        self.brand = brand
        self.category = category
        self.price = price
        self.sale_price = sale_price
        self.quantity = quantity
        self.product_model = product_model
        self.condition = condition
        self.upc = upc
        self.location = location


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
        'sku': self.sku,
        'product_name': self.product_name,
        'product_description': self.product_description,
        'brand': self.brand,
        'category': self.category,
        'price': self.price,
        'sale_price': self.sale_price,
        'quantity': self.quantity,
        'product_model': self.product_model,
        'condition': self.condition,
        'upc': self.upc,
        'location': self.location,
        'product_image': self.product_image,
        }

class Listing(db.Model):
    __tablename__ = 'listing'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sku = db.Column(db.String(16), nullable=False)
    product_name = db.Column(db.String(255), nullable=True)
    product_description = db.Column(db.String(1000), nullable=True)
    brand = db.Column(db.String(45), nullable=True)
    category = db.Column(db.String(45), nullable=True)
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    sale_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity = db.Column(db.Integer, nullable=True)
    platform = db.Column(db.String(45), nullable=True)
    image = db.Column(db.String(45), nullable=True, default='default_listing.png') 
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    catalogue_id = db.Column(db.Integer, db.ForeignKey('catalogue.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    purchases = db.relationship("Purchase", backref="listing", cascade="all, delete", passive_deletes=True)
    orders = db.relationship("Order", backref="listing", cascade="all, delete", passive_deletes=True)

    def __init__(self, dashboard_id, catalogue_id, platform=None, image='default_listing.png'):
        self.dashboard_id = dashboard_id
        self.catalogue_id = catalogue_id        
        self.platform = platform
        self.image = image

        # automatic fill catalogue data in listing data, also incase catalogue not found stop initalize and throw error which captured by route try and except and print the flash message for user inform him error in creating which right
        try:
            target_catalogue = Catalogue.query.filter_by(id=self.catalogue_id).one_or_none()
            if target_catalogue is not None:
                self.sku = target_catalogue.sku
                self.product_name = target_catalogue.product_name
                self.product_description = target_catalogue.product_description
                self.brand = target_catalogue.brand
                self.category = target_catalogue.category
                self.price = target_catalogue.price
                self.sale_price = target_catalogue.sale_price
                self.quantity = target_catalogue.quantity
            else:
                raise 'unable to find the target catalogue'
        except Exception as e:
            print('error while setting default listing data {}'.format(e))
            raise e            
        
        
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
        'catalogue_id': self.catalogue_id,
        'sku': self.sku,
        'product_name': self.product_name,
        'product_description': self.product_description,
        'brand': self.brand,
        'category': self.category,
        'price': self.price,
        'sale_price': self.sale_price,
        'quantity': self.quantity,
        'platform': self.platform,
        'image': self.image
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
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)


    def __init__(self, listing_id, quantity=0, date=None, customer_firstname='', customer_lastname=''):
        self.listing_id = listing_id
        self.quantity = quantity
        self.date = date
        self.customer_firstname = customer_firstname
        self.customer_lastname = customer_lastname

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
        'quantity': self.quantity,
        'date': self.date,
        'customer_firstname': self.customer_firstname,
        'customer_lastname': self.customer_lastname,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }

################################ ---------- Tables for Inventory (End) ---------------- #########################
# some functions for automation
"""
@db.event.listens_for(Dashboard, "after_insert")
def insert_order_to_printer(mapper, connection, target):
    print("hi")
"""
# automatic after update Catalogue update it's listings data if any change on shared cells
@db.event.listens_for(Catalogue, "after_update")
def update_listing_on_catalogue_update(mapper, connection, target):
    try:
        if target and target.listings:
            for listing in target.listings:
                the_table = listing.__table__
                updates = {}
                if listing.sku != target.sku:
                    updates['sku'] = target.sku

                if listing.product_name != target.product_name:
                    updates['product_name'] = target.product_name

                if listing.product_description != target.product_description:
                    updates['product_description'] = target.product_description

                if listing.brand != target.brand:
                    updates['brand'] = target.brand

                if listing.category != target.category:
                    updates['category'] = target.category

                if listing.price != target.price:
                    updates['price'] = target.price

                if listing.sale_price != target.sale_price:
                    updates['sale_price'] = target.sale_price

                if listing.quantity != target.quantity:
                    updates['quantity'] = target.quantity
            
                if len(updates) > 0:
                    connection.execute(the_table.update().values(**updates))
    except Exception as e:
        print('Error in Updating catalogue event db function (update_listing_on_catalogue_update): {}'.format(e, sys.exc_error()))

# event db on listing updated maybe user changed catalogue id, so if any shared data diffrent from parent catalgoue update it revese of above step (need add in admin)
@db.event.listens_for(Listing, "after_update")
def update_listing_on_catalogue_change(mapper, connection, target):
    try:
        if target and target.catalogue:
            the_table = target.__table__
            updates = {}
            if target.sku != target.catalogue.sku:
                updates['sku'] = target.catalogue.sku

            if target.product_name != target.catalogue.product_name:
                updates['product_name'] = target.catalogue.product_name

            if target.product_description != target.catalogue.product_description:
                updates['product_description'] = target.catalogue.product_description

            if target.brand != target.catalogue.brand:
                updates['brand'] = target.catalogue.brand

            if target.category != target.catalogue.category:
                updates['category'] = target.catalogue.category

            if target.price != target.catalogue.price:
                updates['price'] = target.catalogue.price

            if target.sale_price != target.catalogue.sale_price:
                updates['sale_price'] = target.catalogue.sale_price

            if target.quantity != target.catalogue.quantity:
                updates['quantity'] = target.catalogue.quantity
            
            if len(updates) > 0:
                connection.execute(the_table.update().values(**updates))

    except Exception as e:
        print('Error in Updating catalogue event db function (update_listing_on_catalogue_change): {}'.format(e, sys.exc_error()))
