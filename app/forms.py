from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,HiddenField, DecimalField, SelectField,
                     RadioField, SubmitField, PasswordField, validators, SelectMultipleField)
from wtforms.validators import InputRequired, Length, Email, NumberRange, ValidationError
from wtforms.fields import DateTimeLocalField
from wtforms.widgets import NumberInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
import phonenumbers

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


# Listings Forms
class listingForm(FlaskForm):
    catalogue_id = SelectField('Catalogue',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)


class addListingForm(listingForm):
    platforms = SelectMultipleField('Platforms', choices=[], coerce=int, validate_choice=True)
    add = SubmitField('Add')


class editListingForm(listingForm):
    platforms = SelectMultipleField('Platforms', choices=[], coerce=int, validate_choice=True)
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
    address = StringField('Address', validators=[InputRequired(), Length(max=125)])

class addSupplierForm(supplierForm):
    phone_add = StringField('Phone', validators=[InputRequired(), Length(max=45)], render_kw={'type': 'tel'})
    # as the fronend lib kind of broken return number without country code and only added flags image add another input to fix this flags images lib
    full_phone_add = HiddenField(validators=[InputRequired(), Length(max=45)])
    add = SubmitField('Add')

    def validate_full_phone_add(self, full_phone_add):
        try:
            parsed_phone = phonenumbers.parse(full_phone_add.data)
            valid_number = phonenumbers.is_valid_number(parsed_phone)
            if not valid_number:
                raise ValidationError("{} is Invalid Phone Number.".format(full_phone_add.data))
        except:
            raise ValidationError("{} is Invalid Phone Number.".format(full_phone_add.data))


class editSupplierForm(supplierForm):
    phone_edit = StringField('Phone', validators=[InputRequired(), Length(max=45)], render_kw={'type': 'tel'})
    full_phone_edit = HiddenField('Phone', validators=[InputRequired(), Length(max=45)])
    edit = SubmitField('Edit')
    def validate_full_phone_edit(self, full_phone_edit):
        try:
            parsed_phone = phonenumbers.parse(full_phone_edit.data)
            valid_number = phonenumbers.is_valid_number(parsed_phone)
            if not valid_number:
                raise ValidationError("{} is Invalid Phone Number.".format(full_phone_edit.data))
        except:
            raise ValidationError("{} is Invalid Phone Number.".format(full_phone_edit.data))

class removeSupplierForm(FlaskForm):
    supplier_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Supplier')


# Purchases Forms
class PurchaseForm(FlaskForm):
    action_redirect = HiddenField()
    supplier_id = SelectField('Supplier',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    listing_id = SelectField('Listing',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=1)], default=1)
    date = DateTimeLocalField('Date', validators=[InputRequired()], format="%Y-%m-%dT%H:%M")

class addPurchaseForm(PurchaseForm):
    add = SubmitField('Add')

class editPurchaseForm(PurchaseForm):
    edit = SubmitField('Edit')

class removePurchaseForm(FlaskForm):
    action_redirect = HiddenField()
    purchase_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Purchase')


# Orders Forms
class OrderForm(FlaskForm):
    listing_id = SelectField('Listing',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=1)], default=1)
    date = DateTimeLocalField('Date', validators=[InputRequired()], format="%Y-%m-%dT%H:%M")
    customer_firstname = StringField('Customer Name Name', validators=[Length(max=50)])
    customer_lastname = StringField('Customer Last Name', validators=[Length(max=50)])

class addOrderForm(OrderForm):
    action_redirect = HiddenField()
    add = SubmitField('Add')

class editOrderForm(OrderForm):
    action_redirect = HiddenField()
    edit = SubmitField('Edit')

class removeOrderForm(FlaskForm):
    action_redirect = HiddenField()
    order_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Order')


# Platforms Forms
class PlatformForm(FlaskForm):    
    action_redirect = HiddenField()

class addPlatformForm(PlatformForm):
    dashboard_id = HiddenField(validators=[InputRequired()])
    name_add = StringField('Name', validators=[InputRequired(), Length(max=100)])
    add = SubmitField('Add')

class editPlatformForm(PlatformForm):    
    name_edit = StringField('Name', validators=[InputRequired(), Length(max=100)])
    platform_id_edit = HiddenField()
    edit = SubmitField('Edit')

class removePlatformForm(PlatformForm):
    platform_id_remove = HiddenField()
    delete = SubmitField('Delete Order')


###############################  main Forms ###############################################
class CatalogueExcelForm(FlaskForm):
    excel_file = FileField('Catalogues Excel File', validators=[FileAllowed(['csv', 'tsv', 'xls', 'xlsx'], 'Please Upload Valid Excel File'), FileSizeLimit(20)])
    submit = SubmitField('Import Data')

class ExportDataForm(FlaskForm):
    table_name = HiddenField(validators=[InputRequired()])
    condition = SelectField('Condition:',choices=['and', 'or'], validators=[InputRequired()], validate_choice=True)
    export = SubmitField('Export')
    