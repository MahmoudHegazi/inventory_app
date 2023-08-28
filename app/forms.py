import phonenumbers
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,HiddenField, DecimalField, SelectField,
                     RadioField, SubmitField, PasswordField, validators, SelectMultipleField)
from wtforms.validators import InputRequired, Length, Email, NumberRange, ValidationError, optional
from wtforms.fields import DateTimeLocalField, FieldList 
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


# Listings Forms
class listingForm(FlaskForm):
    catalogue_id = SelectField('Catalogue',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
    platforms = SelectMultipleField('Platforms', choices=[], coerce=int, validate_choice=True)
    active = BooleanField('Active', validators=[optional()])
    discount_end_date = DateTimeLocalField('Discount End Date', validators=[optional()], format="%Y-%m-%dT%H:%M")
    discount_start_date = DateTimeLocalField('Discount Start Date', validators=[optional()], format="%Y-%m-%dT%H:%M")
    unit_discount_price = DecimalField('Unit Discount Price', validators=[optional()], default=0.00)
    unit_origin_price = DecimalField('Unit Origin Price', validators=[optional()], default=0.00)
    quantity_threshold = IntegerField('Quantity Threshold', validators=[optional()], default=0)
    currency_iso_code = StringField('Currency ISO code', validators=[optional(), Length(max=45)])
    shop_sku = StringField('Shop SKU', validators=[optional(), Length(max=45)])
    offer_id = IntegerField('Offer ID', validators=[optional()])
    reference = StringField('Reference', validators=[optional(), Length(max=255)])
    reference_type = StringField('Reference Type', validators=[optional(), Length(max=255)])


class addListingForm(listingForm):
    add = SubmitField('Add')


class editListingForm(listingForm):
    edit = SubmitField('Edit')


class removeListingForm(FlaskForm):
    listing_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete')

class removeListingsForm(FlaskForm):
    listings_ids = HiddenField()
    delete_listings = SubmitField('Delete')

class importOffersAPIForm(FlaskForm):
    api_key = StringField('SHOP KEY', validators=[InputRequired(), Length(max=500)], render_kw={'title': 'You can get that key from your marketplace, in the API section'})
    import_data = SubmitField('Import Data')

# Product Forms
class catalogueModal(FlaskForm):
    sku = StringField('SKU', validators=[InputRequired(), Length(max=45)])
    product_name = StringField('Product Name',validators=[Length(max=500)])
    product_description = TextAreaField('Product Description',validators=[Length(max=5000)])
    brand = StringField('Brand',validators=[Length(max=255)])
    category_code = SelectField('Category Code',choices=[], validators=[InputRequired()], validate_choice=True)
    quantity = IntegerField('Quantity')
    product_model = StringField('Product Model',validators=[Length(max=255)])
    condition = StringField('Condition',validators=[Length(max=255)])
    upc = StringField('UPC',validators=[Length(max=255)])
    warehouse_locations = SelectMultipleField('Warehouses Locations', choices=[], coerce=int, validate_choice=True)
    locations_bins = SelectMultipleField('Bins', choices=[], coerce=int, validate_choice=True, render_kw={'style': 'visibility:hidden;'})

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


class removeCataloguesForm(FlaskForm):
    catalogues_ids = HiddenField()
    delete_catalogues = SubmitField('Delete Catalgoues')

# Using wtforms in all app + prevent any unknown delet request that can delete catalogues of system By depend on wtforms
class removeAllCataloguesForm(FlaskForm):
    delete_all = SubmitField('Delete All Catalgoues')

class AddMultipleListingForm(FlaskForm):
    # select platform choice here do 2 things one for ux second as fieldList.data return None instead of empty list if not selected value in select, by adding 0 force it add list with 0, !!! if not added it will broke the two lists order and access with indexs of two lists 
    platforms_selects = FieldList(SelectMultipleField(u'Select Platform', coerce=int,
                                    validate_choice=True,
                                    validators=[optional()],
                                    choices=[(0, 'Select Platform')],
                                    render_kw={'style': 'display:none;', 'title': 'Select Platforms'}))
    catalogue_ids = FieldList(IntegerField(validators=[optional(), NumberRange(min=1)], render_kw={'style': 'display:none;'}))
    add = SubmitField('Add')

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
    tax = DecimalField(
        'tax',
        validators=[],
        default=0.00
    )
    shipping = DecimalField(
        'shipping',
        validators=[],
        default=0.00
    )
    shipping_tax = DecimalField(
        'shipping_tax',
        validators=[],
        default=0.00
    )
    commission = DecimalField(
        'commission',
        validators=[],
        default=0.00
    )
    total_cost = DecimalField(
        'total_cost',
        validators=[],
        default=0.00
    )

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
class addPlatformForm(FlaskForm):
    name_add = StringField('Name', validators=[InputRequired(), Length(max=100)])
    add = SubmitField('Add')

class editPlatformForm(FlaskForm):    
    name_edit = StringField('Name', validators=[InputRequired(), Length(max=100)])
    platform_id_edit = HiddenField()
    edit = SubmitField('Edit')

class removePlatformForm(FlaskForm):
    platform_id_remove = HiddenField()
    delete = SubmitField('Delete Order')

# Locations forms
class addLocationForm(FlaskForm):
    location_name_add = StringField('Name', validators=[InputRequired(), Length(max=255)])
    add = SubmitField('Add')

class editLocationForm(FlaskForm):    
    location_name_edit = StringField('Name', validators=[InputRequired(), Length(max=255)])
    location_id_edit = HiddenField()
    edit = SubmitField('Edit')

class removeLocationForm(FlaskForm):
    location_id_remove = HiddenField()
    delete = SubmitField('Delete Location')

# Bins forms
class addBinForm(FlaskForm):
    bin_name_add = StringField('Name', validators=[InputRequired(), Length(max=255)])
    location_id = HiddenField()
    add = SubmitField('Add')

class editBinForm(FlaskForm):    
    bin_name_edit = StringField('Name', validators=[InputRequired(), Length(max=255)])
    bin_id_edit = HiddenField()
    edit = SubmitField('Edit')

class removeBinForm(FlaskForm):
    bin_id_remove = HiddenField()
    delete = SubmitField('Delete Bin')


# Category Forms
class addCategoryForm(FlaskForm):
    code = StringField('Category Code', validators=[InputRequired(), Length(max=45)])
    label = StringField('Label', validators=[InputRequired(), Length(max=255)])
    level = IntegerField('Level', validators=[optional()], default=0)
    parent_code = StringField('Parent Code', validators=[optional(), Length(max=45)])
    add = SubmitField('Add')

class editCategoryForm(FlaskForm):
    category_id_edit = HiddenField()
    code_edit = StringField('Category Code', validators=[InputRequired(), Length(max=45)])
    label_edit = StringField('Label', validators=[InputRequired(), Length(max=255)])
    level_edit = IntegerField('Level', validators=[optional()])
    parent_code_edit = StringField('Parent Code', validators=[optional(), Length(max=45)])
    edit = SubmitField('Edit')

class removeCategoryForm(FlaskForm):
    category_id = HiddenField()
    delete = SubmitField('Delete Category')

class importCategoriesAPIForm(FlaskForm):
    api_key = StringField('SHOP KEY', validators=[InputRequired(), Length(max=500)], render_kw={'title': 'You can get that key from your marketplace, in the API section'})
    import_data = SubmitField('Import Data')

###############################  main Forms ###############################################
class CatalogueExcelForm(FlaskForm):
    excel_file = FileField('Catalogues Excel File', validators=[FileAllowed(['csv', 'tsv', 'xls', 'xlsx'], 'Please Upload Valid Excel File'), FileSizeLimit(20)])
    submit = SubmitField('Import Data')

class ExportDataForm(FlaskForm):
    table_name = HiddenField(validators=[InputRequired()])
    condition = SelectField('Condition:',choices=['and', 'or'], validators=[InputRequired()], validate_choice=True)
    export = SubmitField('Export')
    
