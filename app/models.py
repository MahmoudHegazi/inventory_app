import datetime
import sys
import decimal
import enum
import secrets
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
from dateutil.relativedelta import *
from datetime import timedelta
Base = declarative_base()


################################ ---------- Enums (Start) ---------------- #########################
class AllowedPermissions(enum.Enum):    
    read = 'read'
    add = 'add'
    update = 'update'
    delete = 'delete'


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    code = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, default=None)
    join_pass = db.Column(db.String(255), nullable=False, default='')
    salat = db.Column(db.String(255), nullable=False, default='')
    max_pending = db.Column(db.Integer, nullable=False, default=50)
    private = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    exportable = db.Column(db.Boolean, nullable=False, default=True)
    deletable = db.Column(db.Boolean, nullable=False, default=True)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    admin = db.relationship("User", backref="inv", foreign_keys=[added_by])
    #users = db.relationship("User", foreign_keys=[User.inventory_id])

    def __init__(self, added_by, name, join_pass='', salat='', max_pending=50, active=True, private=False, exportable=True, deletable=True):
        self.code = self.generate_code()
        self.name = name
        self.join_pass = join_pass
        self.salat = salat
        self.max_pending = max_pending
        self.active = active
        self.private = private
        self.exportable = exportable
        self.deletable = deletable
        self.added_by = added_by

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def generate_code(self):
        code = secrets.token_urlsafe(3)
        try:
            if not self.query.filter_by(code=code).first():
                return code
            else:
                unique_found = False
                for i in range(2000):
                    code = secrets.token_urlsafe(3)
                    if not self.query.filter_by(code=code).first():
                        return code
                    else:
                        continue
                if not unique_found:
                    code = None
                    # instead of return None and also prevent by sql, here know error
                    raise ValueError('Unable to generate unique code for inventory.')
            return None
        except Exception as e:
            raise e

    def total_users(self):
        return db.session.query(func.count(User.id)).join(Inventory, User.inventory_id==Inventory.id).filter(User.inventory_id==self.id, User.approved==True).scalar()
    
    def total_requests(self):
        return db.session.query(func.count(User.id)).join(Inventory, User.inventory_id==Inventory.id).filter(User.inventory_id==self.id, User.approved==False).scalar()
    
    def user_requests(self):
        return db.session.query(User.id, User.uname).join(Inventory, User.inventory_id==Inventory.id).filter(User.inventory_id==self.id, User.approved==False).all()
    
    def format(self):
        return {
        'id': self.id,
        'code': self.code,
        'name': self.name,
        'max_pending': self.max_pending,
        'private': self.private,
        'active': self.active,
        'exportable': self.exportable,
        'deletable': self.deletable,
        'added_by': self.added_by,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }


################################ ---------- Tables for Authentication (Start) ---------------- #########################

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
    conditions = db.relationship("Condition", backref="dashboard", cascade="all, delete", passive_deletes=True)
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
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True, default=None)

    api_keys = db.relationship("OurApiKeys", backref="user", cascade="all, delete", passive_deletes=True)
    suppliers = db.relationship("Supplier", backref="user", cascade="all, delete", passive_deletes=True)
    roles = db.relationship("UserRoles", backref="user", cascade="all, delete", passive_deletes=True)
    meta = db.relationship("UserMeta", back_populates='user', cascade="all, delete", passive_deletes=True)
    catalogues = db.relationship('Catalogue', backref='user', cascade="all, delete", lazy='dynamic', passive_deletes=True)
    keys_logs = db.relationship("ApiKeysLogs", backref="user", cascade="all, delete", passive_deletes=True)
    company = db.relationship("Inventory", foreign_keys=[inventory_id], backref='users')

    def __init__(self, name, uname, email, upass, dashboard_id=None, inventory_id=None, image='default_user.png', approved=True):
        if dashboard_id:
            self.dashboard_id = dashboard_id
        if inventory_id:
            self.inventory_id = inventory_id

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

    def is_super(self):
        # use superuser for auto say is super for all roles that is superuser first one for performance
        issuper = False
        for urole in self.roles:
            if urole.role.superuser == True:
                issuper = True
                break
        return issuper
    
    def isInventoryAdmin(self):
        return True if db.session.query(UserRoles
            ).join(Role, UserRoles.role_id==Role.id
            ).filter(UserRoles.user_id==self.id, Role.name=='inventory_admin').first() else False
    
    def get_roles(self):
        return db.session.query(Role).join(UserRoles, UserRoles.role_id==Role.id).join(User, UserRoles.user_id==User.id).filter(Role.system==False, UserRoles.user_id==self.id).all()
    
    def admin_requests_alert(self):
        current_time = datetime.datetime.utcnow()
        two_month_ago = current_time - timedelta(weeks=8)
        return db.session.query(func.count(User.id)).join(
                    Inventory, User.inventory_id==Inventory.id
                    ).join(
                        UserRoles, UserRoles.user_id==User.id
                        ).join(
                            Role, UserRoles.role_id==Role.id
                            ).filter(
                                User.approved==False, Inventory.added_by==self.id,
                                User.created_date<two_month_ago
                            ).scalar()

    
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
    system = db.Column(db.Boolean, nullable=True, default=False)
    superuser = db.Column(db.Boolean, nullable=True, default=False)

    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    users = db.relationship("UserRoles", backref="role", cascade="all, delete", passive_deletes=True)
    permissions = db.relationship("RolePermissions", backref="role", cascade="all, delete", passive_deletes=True)

    def __init__(self, name, system=False, superuser=False):
        self.name = name
        self.system = system
        self.superuser = superuser

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_permissions(self):
        return [up.permission for up in self.permissions]

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
    def __init__(self, user_id=None, role_id=None):
        if user_id:
            self.user_id = user_id
        if role_id:
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

class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    permission = db.Column(Enum(AllowedPermissions), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    all_users_permissions = db.relationship("RolePermissions", backref="permission", cascade="all, delete", passive_deletes=True)

    def __init__(self, permission):
        self.permission = permission

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
            'permission': self.permission,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }

class RolePermissions(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)

    def __init__(self, role_id, permission_id):
        self.role_id = role_id
        self.permission_id = permission_id

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
            'role_id': self.role_id,
            'permission_id': self.permission_id,
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
    code = db.Column(db.String(45), nullable=False)
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
# uselist=False make the one-to-one not return list of classes
class Catalogue(db.Model): # catelouge
    __tablename__ = 'catalogue'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sku = db.Column(db.String(45), nullable=False)
    product_name = db.Column(db.String(500), nullable=True)
    product_description = db.Column(db.String(5000), nullable=True)
    brand = db.Column(db.String(255), nullable=True)
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    sale_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity = db.Column(db.Integer, nullable=True, default=0)
    product_model = db.Column(db.String(255), nullable=True)
    upc = db.Column(db.String(255), nullable=True)
    reference_type = db.Column(db.String(50), nullable=True, default=None)
    product_image = db.Column(db.String(45), nullable=True, default='default_product.png')
    barcode = db.Column(db.String(100), nullable=True, default=None)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True, default=None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey('condition.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True, default=None)
    listings = db.relationship("Listing", backref="catalogue", cascade="all, delete", passive_deletes=True, order_by='Listing.platform_id.asc()')
    locations = db.relationship("CatalogueLocations", backref='catalogue', cascade="all, delete", passive_deletes=True)
    meta = db.relationship("CatalogueMeta", backref='catalogue', cascade="all, delete", passive_deletes=True)

    def __init__(self, sku, user_id, product_name=None, product_description=None, brand=None, category_id=None, price=0.00, sale_price=0.00, quantity=0, product_model=None, upc=None, condition_id=None, reference_type=None, barcode=None):
        self.sku = sku
        self.product_name = product_name
        self.user_id = user_id
        self.product_description = product_description
        self.brand = brand
        self.category_id = category_id
        self.price = price
        self.sale_price = sale_price
        self.quantity = quantity
        self.product_model = product_model
        self.upc = upc
        self.condition_id = condition_id
        self.barcode = barcode
        self.reference_type = reference_type

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
        'category_id': self.category_id,
        'price': str(self.price),
        'sale_price': str(self.sale_price),
        'quantity': self.quantity,
        'product_model': self.product_model,
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
    active = db.Column(db.Boolean, nullable=True, default=False)
    discount_end_date = db.Column(DateTime, nullable=True, default=None)
    discount_start_date = db.Column(DateTime, nullable=True, default=None)
    unit_discount_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    unit_origin_price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    quantity_threshold = db.Column(db.Integer, nullable=True, default=0)
    currency_iso_code = db.Column(db.String(45), nullable=True, default='')
    shop_sku = db.Column(db.String(45), nullable=True, default='')
    offer_id = db.Column(db.Integer, nullable=True, default=0)
    reference = db.Column(db.String(255), nullable=True, default='')
    reference_type = db.Column(db.String(255), nullable=True, default='')
    

    image = db.Column(db.String(45), nullable=True, default='default_listing.png')
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    catalogue_id = db.Column(db.Integer, db.ForeignKey('catalogue.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    purchases = db.relationship("Purchase", backref="listing", cascade="all, delete", passive_deletes=True)
    orders = db.relationship("Order", backref="listing", cascade="all, delete", passive_deletes=True)

    def __init__(self, dashboard_id, catalogue_id, platform_id, active=None, discount_start_date=None, discount_end_date=None, unit_discount_price=None, unit_origin_price=None, quantity_threshold=None, currency_iso_code=None, shop_sku=None, offer_id=None, reference=None, reference_type=None, image='default_listing.png'):
        self.dashboard_id = dashboard_id
        self.catalogue_id = catalogue_id
        self.platform_id = platform_id
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
                if target_catalogue.category:
                    self.category_code = target_catalogue.category.code
                    self.category_label = target_catalogue.category.label
                else:
                    self.category_code = None
                    self.category_label = None

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
        #print("synced")
        if self.sku != self.catalogue.sku:
            self.sku = self.catalogue.sku
        if self.product_name != self.catalogue.product_name:
            self.product_name = self.catalogue.product_name
        if self.product_description != self.catalogue.product_description:
            self.product_description = self.catalogue.product_description
        if self.brand != self.catalogue.brand:
            self.brand = self.catalogue.brand
        if self.catalogue.category and self.catalogue.category.code != self.category_code:
            self.category_code = self.catalogue.category.code
        else:
            self.category_code = None

        if self.catalogue.category and self.catalogue.category.label != self.category_label:
            self.category_label = self.catalogue.category.label
        else:
            self.category_label = None

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
        'platform': self.platform.name,
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
    # new
    commercial_id = db.Column(db.String(255), nullable=True, default=None)
    currency_iso_code = db.Column(db.String(45), nullable=True, default=None)
    phone = db.Column(db.String(45), nullable=True, default=None)
    street_1 = db.Column(db.String(255), nullable=True, default=None)
    street_2 = db.Column(db.String(255), nullable=True, default=None)
    zip_code = db.Column(db.String(45), nullable=True, default=None)
    city = db.Column(db.String(100), nullable=True, default=None)
    country = db.Column(db.String(80), nullable=True, default=None)
    fully_refunded = db.Column(db.Boolean, nullable=True, default=False)
    can_refund = db.Column(db.Boolean, nullable=True, default=False)
    order_id = db.Column(db.String(45), nullable=True, default=None)
    category_code = db.Column(db.String(45), nullable=True, default=None)
    price = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0.00)
    product_title = db.Column(db.String(500), nullable=True, default=None)
    product_sku = db.Column(db.String(45), nullable=True, default=None)
    order_state = db.Column(db.String(50), nullable=True, default=None)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    taxes = db.relationship("OrderTaxes", backref="order", cascade="all, delete", passive_deletes=True)

    def __init__(self, listing_id, quantity=0, date=None, customer_firstname='', customer_lastname='', tax=0.0, shipping=0.0, shipping_tax=0.0, commission=0.0, total_cost=0.0, commercial_id=None, currency_iso_code=None, phone=None, street_1=None, street_2=None, zip_code=None, city=None, country=None, fully_refunded=False, can_refund=False, order_id=None, category_code=None, price=0, product_title=None, product_sku=None, order_state=None):
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
        self.commercial_id = commercial_id
        self.currency_iso_code = currency_iso_code
        self.phone = phone
        self.street_1 = street_1
        self.street_2 = street_2
        self.zip_code = zip_code
        self.city = city
        self.country = country
        self.fully_refunded = fully_refunded
        self.can_refund = can_refund
        self.order_id = order_id
        self.category_code = category_code
        self.price = price
        self.product_title = product_title
        self.product_sku = product_sku
        self.order_state = order_state
        

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
        'commercial_id': self.commercial_id,
        'currency_iso_code': self.currency_iso_code,
        'phone': self.phone,
        'street_1': self.street_1,
        'street_2': self.street_2,
        'zip_code': self.zip_code,
        'city': self.city,
        'country': self.country,
        'fully_refunded': self.fully_refunded,
        'can_refund': self.can_refund,
        'order_id': self.order_id,
        'category_code': self.category_code,
        'price': str(self.price),
        'product_title': self.product_title,
        'product_sku': self.product_sku,
        'order_state': self.order_state,
        'created_date': self.created_date,
        'updated_date': self.updated_date,
        'taxes': [ordertax.format() for ordertax in self.taxes]
        }
    

class OrderTaxes(db.Model):
    __tablename__ = 'order_taxes'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    amount = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=True, default=0)
    code = db.Column(db.String(255), nullable=True, default=None)
    type = db.Column(db.String(45), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)    
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)

    def __init__(self, type, order_id=None, amount=0, code=None):
        self.type = type
        self.order_id = order_id
        self.amount = amount
        self.code = code


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
        'order_id': self.order_id,
        'amount': str(self.amount),
        'code': self.code,
        'type': self.type,
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
    listings = db.relationship("Listing", backref='platform', cascade="all, delete", passive_deletes=True)

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

################################ ---------- Tables for Dashboard Plateforms (End) ---------------- #########################

################################ ---------- Tables for Dashboard Conditions (Start) ---------------- #########################
class Condition(db.Model):
    __tablename__ = 'condition'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)    
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    catalogues = db.relationship("Catalogue", backref='condition')

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
    
    def __repr__(self):
        return '{}: {}'.format(self.id, self.name)

################################ ---------- Tables for Dashboard Conditions (End) ---------------- #########################

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
        'updated_date': self.updated_date,
        'bins': [locbin.format() for locbin in self.bins],
        'catalogue_locations': [catalogue_location.format() for catalogue_location in self.catalogues_locations]
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
    bins = db.relationship("CatalogueLocationsBins", backref="catalogue_location", cascade="all, delete", passive_deletes=True)

    def __init__(self, location_id, catalogue_id=None):
        self.location_id = location_id
        # some times use append to insert locations bins, incase not use it can accept direct insert
        if catalogue_id:
            self.catalogue_id = catalogue_id

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
        'location': self.warehouse_location.name,
        'created_date': self.created_date,
        'updated_date': self.updated_date,
        'bins': [catalogue_locations_bin.format() for catalogue_locations_bin in self.bins]
        }

class CatalogueLocationsBins(db.Model):
    __tablename__ = 'catalogue_locations_bins'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('catalogue_locations.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('location_bins.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)


    def __init__(self, location_id, bin_id):
        self.location_id = location_id 
        self.bin_id = bin_id

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
    

class CatalogueMeta(db.Model):
    __tablename__ = 'catalogue_meta'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(255), nullable=True, default=None)
    catalogue_id = db.Column(db.Integer, db.ForeignKey('catalogue.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    
    def __init__(self, catalogue_id, key, value):
        self.catalogue_id = catalogue_id 
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
        'catalogue_id': self.catalogue_id,
        'key': self.key,
        'value': self.value,
        'created_date': self.created_date,
        'updated_date': self.updated_date
        }


    
################################ ---------- Tables for Dashboard Warehouse Locations (End) ---------------- #########################   
def get_expiration_date(expiration_date):
    valid_expiry = False
    now = datetime.datetime.utcnow()

    final_expiration_date = (now+relativedelta(months=+1)).strftime("%Y-%m-%dT%H:%M")
    diff = now - now
    # happend here as it db releated action to store value, not asked from user to calc seconds and utc date time he selected
    try:
        valid_expiry = True if expiration_date is not None and expiration_date <= (now+relativedelta(months=+6)) else False
        if valid_expiry:
            diff = expiration_date - now
        else:
            diff = (now+relativedelta(months=+1)) - now
    except Exception as e:
        valid_expiry = False
        diff = now - now
    
    return {'final_expiration_date': final_expiration_date, 'diff': diff, 'valid_expiry': valid_expiry}

################################ ---------- Tables for OUR API (Start) ---------------- #########################
class OurApiKeys(db.Model):
    __tablename__ = 'our_api_keys'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    key = db.Column(db.String(255), nullable=False)
    total_requests = db.Column(db.Integer, nullable=False, default=0)
    key_limit = db.Column(db.Integer, nullable=False, default=0)
    key_update_date = db.Column(db.Date, nullable=True, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    white_ips = db.Column(db.String(5000), nullable=True, default='')
    black_ips = db.Column(db.String(5000), nullable=True, default='')
    # 8 should be max as it 6 month max but ok 11
    expiration_seconds = db.Column(db.DECIMAL(precision=10, scale=2, asdecimal=True), nullable=False, default=0.00)
    expiration_date = db.Column(DateTime, nullable=False, default=None)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)
    logs = db.relationship("ApiKeysLogs", backref="key", cascade="all, delete", passive_deletes=True)

    def __init__(self, user_id, key, key_limit=0, expiration_date=None, key_update_date=None, white_ips='', black_ips=''):
        self.user_id = user_id
        self.key = key
        self.key_limit = key_limit
        # this allow set that start of using the API, ex set last update to day after 7 days from now, so it will not allow update until this 7 also total requests to limit of keys
        self.key_update_date = key_update_date
        self.white_ips = white_ips
        self.black_ips = black_ips

        # add valid expirey date + fix any backend covered by front gap added in form (also default if no expiery code or it broken)
        expiration_date_data = get_expiration_date(expiration_date)

        # no if u abused html attr and updated client max and added  1 hour will consider bigger date and will max insert 6 months
        if expiration_date_data['valid_expiry']:
            self.expiration_date = expiration_date
        else:
            self.expiration_date = expiration_date_data['final_expiration_date']

        # why this, answer is logical, when renew , renew same period user selected, this high level of ux and also achive my goal not change desgin and 1 button for renwew, this also important to know how much user decide and save in db so get it fast
        self.expiration_seconds = max(expiration_date_data['diff'].total_seconds(), 0)  # not allow nagtive


    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        # make sure is valid update value , as well renew the seconds, fast db is not need change mysql, final we now know excatly how many seconds user selected for the expire, so when renew set same seconds, without that never able to know the estamited from form open time and the expiration date lol or if u magican u do

        # add valid expirey date + fix any backend covered by front gap added in form (also default if no expiery code or it broken)
        expiration_date_data = get_expiration_date(self.expiration_date)

        # no if u abused html attr and updated client max and added  1 hour will consider bigger date and will max insert 6 months
        if expiration_date_data['valid_expiry']:
            self.expiration_date = self.expiration_date
        else:
            self.expiration_date = expiration_date_data['final_expiration_date']

        # why this, answer is logical, when renew , renew same period user selected, this high level of ux and also achive my goal not change desgin and 1 button for renwew, this also important to know how much user decide and save in db so get it fast
        self.expiration_seconds = max(expiration_date_data['diff'].total_seconds(), 0)  # not allow nagtive

        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_white_ips(self):
        white_ips_list = []
        try:
            if self.white_ips and isinstance(self.white_ips, str):
                white_ips_list = list(set(list(filter(lambda x: True if str(x).strip() != '' else False ,self.white_ips.split(',')))))
        except:
            print('error in get_white_ips, {}'.format(sys.exc_info()))
        return white_ips_list

    def add_white_ips(self, ipaddresses=''):
        try:
            ipaddresses = ipaddresses.strip()
            changes = 0
            if self.white_ips and ipaddresses:
                white_ips_list = list(set(list(filter(lambda x: True if str(x).strip() != '' else False ,self.white_ips.split(',')))))
                # unique not empty new ip addresses list
                ipaddresses_list = list(set(list(filter(lambda x: True if str(x).strip() != '' else False ,ipaddresses.split(',')))))
                for ip_address in ipaddresses_list:
                    ip_address = ip_address.strip()
                    if ip_address and ip_address not in white_ips_list:
                        changes += 1
                        white_ips_list.append(ip_address.strip())
                ipaddresses_result = ','.join(white_ips_list)

                self.white_ips = ipaddresses_result
                self.update()

                if changes:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print('error in add_white_ips: {}'.format(sys.exc_info()))
            return None
        
    def remove_white_ip(self, ipaddresses=''):
        try:
            changes = 0
            ipaddresses_list = list(set(list(filter(lambda x: True if str(x).strip() != '' else False ,ipaddresses.split(',')))))
            current_ip_address = self.white_ips.split(',')
            for ip_address in ipaddresses_list:
                ip_address = ip_address.strip()
                if ip_address and ip_address in self.white_ips:
                    self.white_ips = self.white_ips.replace(ip_address, '')
                    changes += 1

            result_ips = list(set(list(filter(lambda x: True if str(x).strip() != '' else False ,self.white_ips.split(',')))))
            self.white_ips = ','.join(result_ips)

            if len(current_ip_address) != len(result_ips) or changes > 0:
                self.update()
                return True
            else:
                return False

        except Exception as e:
            print('error in remove_white_ip: {}'.format(sys.exc_info()))
            return None


    def is_expired(self):
        try:
            now = datetime.datetime.utcnow()
            return True if self.expiration_date <= now else False
        except:
            print('error in is_expired, {}'.format(sys.exc_info()))
            return True
    
    def get_expiration_days(self):
        beganing = ''
        expiration_days = 0
        extension = 'days'
        try:
            time = self.expiration_seconds
            zero = float(0.00)
            # Calculate the number of full days in the given time duration.
            days = time / (24 * 3600)
            floored = int(days)
            after_dot = days % 1

            if time > zero:
                if floored > 0:
                    expiration_days = floored
                    if after_dot > 0:
                        beganing = 'bigger than '                    
                else:
                    if time > zero:
                        expiration_days = 1
                        beganing = 'less than '
                    else:
                        expiration_days = 0
            else:
                return 0
            
            if expiration_days == 1:
                extension = 'day'
        except:
            print('error in get_expiration_seconds, {}'.format(sys.exc_info()))
        finally:
            return '{}{} {}'.format(beganing, expiration_days, extension)
        
    
    def format(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key': self.key,
            'total_requests': self.total_requests,
            'key_limit': self.key_limit,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }

class ApiKeysLogs(db.Model):
    __tablename__ = 'api_keys_logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    status = db.Column(db.String(45), nullable=True, default=None)
    endpoint = db.Column(db.String(45), nullable=True, default=None)
    key_id = db.Column(db.Integer, db.ForeignKey('our_api_keys.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_date = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_date = db.Column(DateTime, nullable=True, default=None, onupdate=datetime.datetime.utcnow)

    def __init__(self, user_id, key_id, status=None, endpoint=None):
        self.user_id = user_id
        self.key_id = key_id
        self.status = status
        self.endpoint = endpoint

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
            'key_id': self.key_id,
            'status': self.status,
            'endpoint': self.endpoint,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }

################################ ---------- Tables for OUR API (End) ---------------- #########################

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
                if target.category:
                    list_to_update.category_code = target.category.code
                    list_to_update.category_label = target.category.label
                else:
                    list_to_update.category_code = None
                    list_to_update.category_label = None
                    
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
