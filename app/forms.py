from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,HiddenField, DecimalField, SelectField,
                     RadioField, SubmitField, PasswordField, validators)
from wtforms.validators import InputRequired, Length, Email, NumberRange, ValidationError
from wtforms.fields import DateTimeLocalField
from wtforms.widgets import NumberInput

from flask_wtf.file import FileField, FileAllowed, FileRequired

def FileSizeLimit(max_size_in_mb):
    
    max_bytes = max_size_in_mb*1024*1024
    def file_length_check(form, field):
        if field.data:
            filesize = len(field.data.read())
            if filesize > max_bytes:
                raise ValidationError(f"File size must be less than {max_size_in_mb}MB")
            field.data.seek(0)
    return file_length_check


class SignupForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(),
                                            Length(min=1, max=45)])
    username = StringField('Username',
                                validators=[InputRequired(),
                                            Length(min=1, max=45)])

    email = StringField('Email',
                                validators=[InputRequired(), Email(),
                                            Length(min=5, max=255, message='Please enter a valid email.')])

    pwd = PasswordField('Password', 
                                validators=[InputRequired(),
                                            validators.EqualTo('pwd_confirm', message='Passwords must match'),
                                            Length(min=8, max=255)])

    pwd_confirm = PasswordField('Password Confirm', 
                                validators=[InputRequired(), 
                                            Length(min=8, max=255)])
    signup = SubmitField('Signup')


class LoginForm(FlaskForm):
    username = StringField('Username',
                                validators=[InputRequired(),
                                            Length(min=1, max=45)])
    pwd = PasswordField('Password', 
                                validators=[InputRequired()])
    remember = BooleanField('Remeber Me')
    login = SubmitField('Login')


# Dashboard Forms
class DashboardForm(FlaskForm):
    title = StringField('Title', default='New Dashboard')
    num_of_listings = IntegerField('Total listings', widget=NumberInput(step=1), default=0)
    num_of_orders = IntegerField('Total Orders', widget=NumberInput(step=1), default=0)
    sum_of_monthly_purchases = DecimalField(
        'Total monthly purchases',
        validators=[NumberRange(min=0, max=12)],
        default=0.00
    )

class addDashboardForm(DashboardForm):
    redirect = HiddenField()
    add = SubmitField('Add')


class editDashboardForm(DashboardForm):
    edit = SubmitField('Edit')


class removeDashboardForm(FlaskForm):
    dashboard_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Dashboard')



# Listings Forms
class listingForm(FlaskForm):
    catalogue_id = SelectField('Catalogue',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    platform = StringField('Platform',validators=[Length(max=45)])

class addListingForm(listingForm):
    add = SubmitField('Add')


class editListingForm(listingForm):
    edit = SubmitField('Edit')


class removeListingForm(FlaskForm):
    listing_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete')


# Product Forms
class catalogueModal(FlaskForm):
    sku = StringField('SKU', validators=[InputRequired(), Length(max=16)])
    product_name = StringField('Product Name',validators=[Length(max=255)])
    product_description = TextAreaField('Product Description',validators=[Length(max=1000)])
    brand = StringField('Brand',validators=[Length(max=45)])
    category = StringField('Category',validators=[Length(max=45)])
    quantity = IntegerField('Quantity')
    product_model = StringField('Product Model',validators=[Length(max=45)])
    condition = StringField('Condition',validators=[Length(max=45)])
    upc = StringField('UPC',validators=[Length(max=255)])
    location = StringField('Location',validators=[Length(max=255)])
    price = DecimalField(
        'Price',
        validators=[],
        default=0.00
    )    
    sale_price = DecimalField(
        'Sale Price',
        validators=[],
        default=0.00
    )
class addCatalogueForm(catalogueModal):
    add = SubmitField('Add')

class editCatalogueForm(catalogueModal):
    edit = SubmitField('Edit')


class removeCatalogueForm(FlaskForm):
    catalogue_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete')


# signup = SubmitField('Signup', default='checked')

# Supplier Forms
class supplierForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=80)])

class addSupplierForm(supplierForm):
    add = SubmitField('Add')

class editSupplierForm(supplierForm):
    edit = SubmitField('Edit')


class removeSupplierForm(FlaskForm):
    supplier_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Supplier')


# Purchases Forms
class PurchaseForm(FlaskForm):
    supplier_id = SelectField('Supplier',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    listing_id = SelectField('Listing',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    quantity = IntegerField('Quantity', validators=[InputRequired()], default=0)
    date = DateTimeLocalField('Date', validators=[InputRequired()], format="%Y-%m-%dT%H:%M")

class addPurchaseForm(PurchaseForm):
    add = SubmitField('Add')

class editPurchaseForm(PurchaseForm):
    edit = SubmitField('Edit')

class removePurchaseForm(FlaskForm):
    purchase_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Purchase')


# Orders Forms
class OrderForm(FlaskForm):
    listing_id = SelectField('Listing',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    quantity = IntegerField('Quantity', validators=[InputRequired()], default=0)
    date = DateTimeLocalField('Date', validators=[InputRequired()], format="%Y-%m-%dT%H:%M")
    customer_firstname = StringField('Customer Name Name', validators=[Length(max=50)])
    customer_lastname = StringField('Customer Last Name', validators=[Length(max=50)])

class addOrderForm(OrderForm):
    add = SubmitField('Add')

class editOrderForm(OrderForm):
    edit = SubmitField('Edit')

class removeOrderForm(FlaskForm):
    order_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Order')

class addDashboardForm(DashboardForm):
    redirect = HiddenField()
    add = SubmitField('Add')


###############################  main Forms ###############################################

class CatalogueExcelForm(FlaskForm):
    excel_file = FileField('Catalogues Excel File', validators=[FileAllowed(['csv', 'tsv', 'xls', 'xlsx'], 'Please Upload Valid Excel File'), FileSizeLimit(20)])
    submit = SubmitField('Import Data')
