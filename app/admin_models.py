from .models import User, Role, UserRoles, Dashboard, Listing, Catalogue, Purchase, Order, Supplier
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, request, flash
from flask_login import login_required, current_user
from . import admin_permission, db, admin, bcrypt
from wtforms import PasswordField, FileField, StringField

from wtforms.validators import InputRequired, Length, Email
from flask_admin.menu import MenuLink


class InventoryModelView(ModelView):
    can_export = True
    page_size = 50
    @admin_permission.require(http_exception=403)
    @login_required
    def is_accessible(self):
        return current_user and current_user.is_authenticated and current_user.isAdmin()
                
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))

######################## Authentication Start #########################################

class AdminPasswordField(PasswordField):
    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] != '':
            self.data = bcrypt.generate_password_hash(valuelist[0])
        elif self.data is None:
            self.data = ''

class UserModalView(InventoryModelView):
    column_exclude_list = ['upass', ]
    column_searchable_list = ['name', 'email', 'uname']
    column_filters = ['name', 'email', 'uname', 'created_date', 'updated_date']
    column_editable_list = ['name', 'approved']

    form_excluded_columns = ['created_date', 'updated_date', 'roles', 'suppliers', 'dashboards', 'authenticated']
    form_overrides = {
        'upass': AdminPasswordField
    }
    form_args = {
    'name': {
        'validators': [InputRequired(), Length(min=1, max=45)]
    },
    'username': {
        'validators': [InputRequired(), Length(min=1, max=45)]
    },
    'email': {
        'validators': [InputRequired(), Length(max=255), Email()]
    },
    'upass': {
        'validators': [InputRequired(), Length(min=8, max=255)]
    }
    }

class UserRolesModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'role', 'user']
    column_searchable_list = ['user_id', 'role_id']

    form_excluded_columns = ['created_date', 'updated_date']

class RoleModalView(InventoryModelView):
    can_edit = False
    can_delete = False
    form_excluded_columns = ['created_date', 'updated_date', 'users']

######################## Authentication END #########################################

######################## Vendor Start #########################################

class DashboardModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'num_of_listings', 'num_of_orders', 'sum_of_monthly_purchases', 'user']
    column_searchable_list = ['title']
    column_editable_list = ['title']
    form_excluded_columns = ['created_date', 'updated_date', 'listings']

class catalogueModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'sku', 'product_name', 'product_description', 'brand', 'category', 'price', 'sale_price','quantity', 'product_model', 'condition', 'upc', 'location', 'user']
    column_searchable_list = ['sku', 'product_name', 'brand', 'category', 'price', 'product_model', 'location']
    column_editable_list = ['product_name', 'brand', 'category', 'price', 'sale_price', 'quantity', 'product_model', 'condition', 'upc', 'location']
    form_excluded_columns = ['created_date', 'updated_date']


class ListingModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'catalogue_id', 'sku', 'product_name', 'product_description', 'brand', 'category', 'price', 'sale_price','quantity', 'catalogue']
    column_searchable_list = ['sku', 'catalogue_id', 'product_name', 'brand', 'category', 'price']
    column_editable_list = ['product_name', 'brand', 'category', 'price', 'sale_price', 'quantity']
    # exclude skue, etc from forms as it updated by sqlalchemy event automatic when catalogue update,and in insert it filled up automatic with on_model_change
    form_excluded_columns = ['created_date', 'updated_date', 'purchases', 'orders', 'sku', 'product_name', 'product_description', 'brand', 'category', 'price', 'sale_price','quantity']

    # on event or model change when create, set automatic the data based on parent catalogue
    def on_model_change(self, form, model, is_created):
        if is_created == True:
            if model.catalogue:
                model.sku = model.catalogue.sku
                model.product_name = model.catalogue.product_name
                model.product_description = model.catalogue.product_description
                model.brand = model.catalogue.brand
                model.category = model.catalogue.category
                model.price = model.catalogue.price
                model.sale_price = model.catalogue.sale_price
                model.quantity = model.catalogue.quantity


class PurchaseModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'date', 'quantity', 'supplier', 'listing']
    column_searchable_list = ['date', 'supplier_id', 'listing_id']
    column_editable_list = ['quantity', 'date']
    form_excluded_columns = ['created_date', 'updated_date']


class OrderModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'quantity', 'date', 'customer_firstname', 'customer_lastname', 'listing']
    column_searchable_list = ['listing_id', 'customer_firstname', 'customer_lastname']
    column_editable_list = ['customer_firstname', 'customer_lastname', 'quantity', 'date']
    form_excluded_columns = ['created_date', 'updated_date']



######################## Vendor End #########################################

######################## Supplier Start #########################################

class SupplierModalView(InventoryModelView):
    column_filters = ['created_date', 'updated_date', 'name', 'user']
    column_searchable_list = ['name']
    column_editable_list = ['name']
    form_excluded_columns = ['created_date', 'updated_date', 'purchases']

######################## Supplier End #########################################

class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("routes.index")
    
userModalView = UserModalView(User, db.session, category='Authentication')
roleModalView = RoleModalView(Role, db.session, category='Authentication')
userRolesModalView = UserRolesModalView(UserRoles, db.session, category='Authentication')
dashboardModalView = DashboardModalView(Dashboard, db.session, category='Vendor')
listingModalView = ListingModalView(Listing, db.session, category='Vendor')
cataloguedModalView = catalogueModalView(Catalogue, db.session, category='Vendor')
purchaseModalView = PurchaseModalView(Purchase, db.session, category='Vendor')
orderModalView = OrderModalView(Order, db.session, category='Vendor')
supplierModalView = SupplierModalView(Supplier, db.session)

backlink = MainIndexLink(name="Back to app")



