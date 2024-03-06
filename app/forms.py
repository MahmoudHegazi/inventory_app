import phonenumbers
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,HiddenField, DecimalField, SelectField,
                     RadioField, SubmitField, PasswordField, validators, SelectMultipleField)
from wtforms.validators import InputRequired, Length, Email, NumberRange, ValidationError, optional
from wtforms.fields import DateTimeLocalField, FieldList 
from wtforms.widgets import NumberInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
import datetime
from datetime import timedelta
from dateutil.relativedelta import *



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
    
    inventory_code = StringField('Inventory Code', validators=[InputRequired(),
                                            Length(min=1, max=255)])
    
    join_password = PasswordField('Inventory Join Password', validators=[optional(),
                                            Length(min=1, max=255)])
    is_private = BooleanField('private', default=False, render_kw={'style': 'display:none;'})

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
    platform_id = SelectField('Platform',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
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
    upc = StringField('UPC',validators=[Length(max=255)])
    condition = SelectField('Condition',choices=[], validators=[InputRequired()], coerce=int, validate_choice=True)
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

class generateCatalogueBarcodeForm(FlaskForm):
    columns = SelectMultipleField('Catalogue Columns', choices=[],validate_choice=False)
    data = TextAreaField('Barcode Data',validators=[Length(max=48), InputRequired()], render_kw={'rows': 2})
    generate = SubmitField('Generate')


# Using wtforms in all app + prevent any unknown delet request that can delete catalogues of system By depend on wtforms
class removeAllCataloguesForm(FlaskForm):
    delete_all = SubmitField('Delete All Catalgoues')

# important note boolean input will not sent to server if it not checked 
class AddMultipleListingForm(FlaskForm):
    # select platform choice here do 2 things one for ux second as fieldList.data return None instead of empty list if not selected value in select, by adding 0 force it add list with 0, !!! if not added it will broke the two lists order and access with indexs of two lists 
    """
    platforms_selects = FieldList(SelectMultipleField(u'Select Platform', coerce=int,
                                    validate_choice=True,
                                    validators=[optional()],
                                    choices=[(0, 'Select Platform')],
                                    render_kw={'style': 'display:none;', 'title': 'Select Platforms'}))
    """
    platforms_selects = FieldList(SelectField('Platform', choices=[(1,'hi')], validators=[InputRequired()], coerce=int, validate_choice=True))
    catalogue_ids = FieldList(IntegerField(validators=[optional(), NumberRange(min=1)], render_kw={'style': 'display:none;'}))

    active = FieldList(SelectField('Active', validators=[optional()], choices=[(0, 'False'), (1, 'True')], default=0, coerce=int, validate_choice=True))
    discount_end_date = FieldList(DateTimeLocalField('Discount End Date', validators=[optional()], format="%Y-%m-%dT%H:%M"))
    discount_start_date = FieldList(DateTimeLocalField('Discount Start Date', validators=[optional()], format="%Y-%m-%dT%H:%M"))
    unit_discount_price = FieldList(DecimalField('Unit Discount Price', validators=[optional()], default=0.00))
    unit_origin_price = FieldList(DecimalField('Unit Origin Price', validators=[optional()], default=0.00))
    quantity_threshold = FieldList(IntegerField('Quantity Threshold', validators=[optional()], default=0))
    currency_iso_code = FieldList(StringField('Currency ISO code', validators=[optional(), Length(max=45)]))
    shop_sku = FieldList(StringField('Shop SKU', validators=[optional(), Length(max=45)]))
    offer_id = FieldList(IntegerField('Offer ID', validators=[optional()]))
    reference = FieldList(StringField('Reference', validators=[optional(), Length(max=255)]))
    reference_type = FieldList(StringField('Reference Type', validators=[optional(), Length(max=255)]))
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

    phone = StringField('Phone', validators=[Length(max=45)])
    commercial_id = StringField('Commercial id', validators=[Length(max=255)])
    currency_iso_code = StringField('Currency iso code', validators=[Length(max=45)])
    street_1 = StringField('Street 1', validators=[Length(max=255)])
    street_2 = StringField('Street 2', validators=[Length(max=255)])
    zip_code = StringField('Zip code', validators=[Length(max=45)])
    city = StringField('City', validators=[Length(max=100)])
    country = StringField('Country', validators=[Length(max=80)])
    fully_refunded = BooleanField('Fully refunded')
    can_refund = BooleanField('Can refund')
    order_id = StringField('order id', validators=[Length(max=45)])
    order_state = StringField('Order state', validators=[Length(max=50)])
    order_tax_codes = HiddenField()
    order_tax_amounts = HiddenField()
    shiping_tax_codes = HiddenField()
    shiping_tax_amounts = HiddenField()


class addOrderForm(OrderForm):
    action_redirect = HiddenField()
    add = SubmitField('Add')

class editOrderForm(OrderForm):
    action_redirect = HiddenField()
    order_tax_ids = HiddenField()
    shiping_tax_ids = HiddenField()
    edit = SubmitField('Edit')

class removeOrderForm(FlaskForm):
    action_redirect = HiddenField()
    order_id = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Order')

class importOrdersAPIForm(FlaskForm):
    api_key = StringField('SHOP KEY', validators=[InputRequired(), Length(max=500)], render_kw={'title': 'You can get that key from your marketplace, in the API section'})
    date_from = DateTimeLocalField('Import From', validators=[optional()], format="%Y-%m-%dT%H:%M", render_kw={'title': 'Orders will be imported starting from this date'})
    order_ids = TextAreaField('Order IDS', validators=[optional()], render_kw={'title': 'You can speacfiy speacfic order ids to be imported order ids must be separated by a comma, usually you can use this if you recive ignored order ids after importing all orders', 'placeholder': 'You can speacfiy speacfic order ids to be imported order ids must be separated by a comma, usually you can use this if you recive ignored order ids after importing all orders'})
    import_data = SubmitField('Import Data')

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
    delete = SubmitField('Delete Platform')

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

# Condition forms
class addConditionForm(FlaskForm):
    name_add = StringField('Name', id='condition_name_add', validators=[InputRequired(), Length(max=255)])
    add = SubmitField('Add')

class editConditionForm(FlaskForm):    
    name_edit = StringField('Name', id='condition_name_edit', validators=[InputRequired(), Length(max=255)])
    condition_id_edit = HiddenField()
    edit = SubmitField('Edit')

class removeConditionForm(FlaskForm):
    condition_id_remove = HiddenField(validators=[InputRequired()])
    delete = SubmitField('Delete Condition')

###############################  main Forms ###############################################
class CatalogueExcelForm(FlaskForm):
    excel_file = FileField('Catalogues Excel File', validators=[FileAllowed(['csv', 'tsv', 'xls', 'xlsx'], 'Please Upload Valid Excel File'), FileSizeLimit(20)])
    submit = SubmitField('Import Data')

class ExportDataForm(FlaskForm):
    table_name = HiddenField(validators=[InputRequired()])
    condition = SelectField('Condition:',choices=['and', 'or'], validators=[InputRequired()], validate_choice=True)
    export = SubmitField('Export')

class SetupBestbuyForm(FlaskForm):
    redirect = StringField('', render_kw={'style': 'display:none;'})
    setup = SubmitField('Setup API')

###############################  Profile Forms ###############################################
class UpdateNameForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=1, max=45)])
    update = SubmitField('Update Name', id="update_name")

class UpdateEmailForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min=1, max=255)])
    update = SubmitField('Update Email', id="update_email")

class UpdateUsernameForm(FlaskForm):
    username = StringField('Username', id='username_update', validators=[InputRequired(), Length(min=1, max=45)])
    update = SubmitField('Update Username', id="update_username")


class UpdatePasswordForm(FlaskForm):
    username_hidden = StringField(validators=[optional()], id='username', name='username', render_kw={'autocomplete': 'username', 'hidden': 'hidden', 'style': 'display:none!important;'})
    current_pwd = PasswordField('Current Password', 
                                validators=[InputRequired()], name='password')
    
    pwd = PasswordField('Password',
                                validators=[InputRequired(),
                                            validators.EqualTo('pwd_confirm', message='Passwords must match'),
                                            Length(min=8, max=255)])

    pwd_confirm = PasswordField('Password Confirm', 
                                validators=[InputRequired(), 
                                            Length(min=8, max=255)])
    update = SubmitField('Update Password', id="update_password")

class setupAPIForm(FlaskForm):
    setup = SubmitField('Setup', id="setup_api")

class addKeyForm(FlaskForm):
    key_limit = IntegerField('Key limit', validators=[InputRequired()], default=0)
    expiration_date =  DateTimeLocalField('Expiration date', id="expiration_date_create",
                                          validators=[InputRequired()],
                                          format="%Y-%m-%dT%H:%M", default=datetime.datetime.utcnow,
                                          render_kw={
                                              'min': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
                                              'max': str((datetime.datetime.utcnow()+relativedelta(months=+6)).strftime("%Y-%m-%dT%H:%M")),
                                              }
                                        )

    def validate_expiration_date(form, field):
        try:
            # note 1 hour even is more than wtforms expires and client side prevent it even if he nasa user 1 hour is ok to me, but now start date is active once created and validated correctly no mater when form submited so real better ux
            min = (datetime.datetime.utcnow()+relativedelta(hours=-1))
            max = (datetime.datetime.utcnow()+relativedelta(months=+6))
            valid = True if ((form.expiration_date.data >= min) and (form.expiration_date.data <= max)) else False
            if not valid:
                raise ValidationError('Please enter valid UTC date within 6 months.')
        except Exception as e:
            raise e

    add = SubmitField('Add', id="add_api_key")

class removeKeyForm(FlaskForm):
    remove_key_id = HiddenField(validators=[InputRequired()])
    remove_key = SubmitField('Remove Key')

class updateKeyForm(FlaskForm):
    update_key_id = HiddenField(validators=[InputRequired()])
    update_key_limit = IntegerField('Key limit', validators=[InputRequired()])
    # note key will be activate after 1 minute, as well max time for keep open form 1 minute or your key must logical have min time you submit on it not open form, js too onsubmit
    expiration_date =  DateTimeLocalField('Expiration date', id="expiration_date_update",
                                          validators=[optional()], 
                                          format="%Y-%m-%dT%H:%M", default=datetime.datetime.utcnow,
                                          render_kw={
                                              'max': str((datetime.datetime.utcnow()+relativedelta(months=+6)).strftime("%Y-%m-%dT%H:%M")),
                                              }
                                        )
    update_key = SubmitField('Update Key')

    def validate_expiration_date(form, field):
        try:
            utf_now = datetime.datetime.utcnow()
            max = (utf_now+relativedelta(months=+6, hours=+1))
            valid = True if form.expiration_date.data <= max else False
            if not valid:
                raise ValidationError('Please enter valid UTC date within 6 months.')
        except Exception as e:
            raise e

class renewKeyForm(FlaskForm):
    renew = SubmitField('Renew Key')

class addWhiteListIPsForm(FlaskForm):
    white_ips = TextAreaField('White Listed IPS',validators=[Length(max=5000)], render_kw={
        'placeholder': 'Enter White List IP addresses separated by a comma.'
        })
    add_ips = SubmitField('Add IPs', id='add_white_list')

class addBlackListIPsForm(FlaskForm):
    black_ips = TextAreaField('Black Listed IPS',validators=[Length(max=5000)], render_kw={
        'placeholder': 'Enter Black List IP addresses separated by a comma.'
        })
    add_ips = SubmitField('Add IPs', id='add_black_list')

class addNewUserForm(FlaskForm):
    
    name = StringField('Name', id="add_name", validators=[InputRequired(), Length(min=1, max=45)])
    uname = StringField('User Name', id="add_uname",  validators=[InputRequired(), Length(min=1, max=45)], render_kw={'autocomplete': 'username'})
    pwd = PasswordField('Password', id="add_pwd", 
                                validators=[InputRequired(),
                                            validators.EqualTo('pwd_confirm', message='Passwords must match'),
                                            Length(min=8, max=255)], render_kw={'autocomplete': 'new-password'})

    pwd_confirm = PasswordField('Password Confirm', id="add_pwd_confirm", 
                                validators=[InputRequired(), 
                                            Length(min=8, max=255)], render_kw={'autocomplete': 'new-password'})
    
    email = StringField('Email', id="add_email",
                            validators=[InputRequired(), Email(),
                                        Length(min=5, max=255, message='Please enter a valid email.')])
    add = SubmitField('Add User', id='add_user_submit')
    
    def validate_uname(self, uname):
        from .models import User
        self.userClass = User
        try:
            
            uname_exist = self.userClass.query.filter_by(uname=uname.data).first()
            if uname_exist:
                raise ValidationError("{} User Name Is Taken.".format(uname.data))
        except:
            raise ValidationError("Unable to validate username right now.{}".format(self.userClass))
        
    def validate_email(self, email):        
        try:
            if not self.userClass:
               from .models import User
               self.userClass = User           
               email_exist =  self.userClass.query.filter_by(email=email.data).first()
               if email_exist:
                   raise ValidationError("{} Email Is Taken.".format(email.data))
        except:
            raise ValidationError("Unable to validate Email right now.")


class addInventoryForm(FlaskForm):
    a_name = StringField('Name',validators=[InputRequired(), Length(min=1, max=255)])
    a_max_pending = IntegerField('Max Pending Requests Limit', id='amax_pending_update', validators=[Length(min=1)])
    a_active = BooleanField('active',validators=[], default=True)
    a_private = BooleanField('private',validators=[], default=False)
    a_exportable = BooleanField('exportable',validators=[], default=True)
    a_deletable = BooleanField('deletable',validators=[], default=True)
    joinpass = PasswordField('Join Password (Optional)', id='a_joinpass', validators=[optional()], 
                            render_kw={
                                    'title': 'Add an extra layer of security Enter the required password for private inventory user logins. The inventory must be private for the password to be applied.',
                                    'style': 'display:none;',
                                    'autocomplete': 'off'
                                }
                            )
    pass_salat = StringField('One Time Secert Keyword (Optional)', id="a_pass_salat", render_kw={
        'title': 'Keyword required to generate strong password'
        })
    add_inv = SubmitField('add')

class updateInventoryForm(FlaskForm):
    inventory_id = HiddenField(id='u_inventory_id', validators=[InputRequired()])
    name = StringField('Name', id='u_name', validators=[InputRequired(), Length(min=1, max=255)])
    active = BooleanField('active', id='u_active', validators=[])
    private = BooleanField('private', id='u_private', validators=[])
    joinpass = PasswordField('Join Password (Optional)', id='u_joinpass', validators=[optional()],
                            render_kw={
                                    'title': 'Add an extra layer of security Enter the required password for private inventory user logins. The inventory must be private for the password to be applied.',
                                    'style': 'display:none;',
                                    'autocomplete': 'off'
                                }
                            )
    
    pass_salat = StringField('One Time Secert Keyword (Optional)', id="u_pass_salat", render_kw={'title': 'Keyword required to generate strong password'})
    update_inventory = SubmitField('update', id='u_update_inventory')

class adminUpdateInventoryForm(FlaskForm):
    inventory_id = HiddenField(id='au_inventory_id', validators=[InputRequired()])
    max_pending = IntegerField('Max Pending Requests Limit', id='max_pending_update')
    name = StringField('Name', id='au_name', validators=[InputRequired(), Length(min=1, max=255)])
    active = BooleanField('active', id='au_active', validators=[])
    private = BooleanField('private', id='au_private', validators=[])
    exportable = BooleanField('exportable', id='au_exportable', validators=[])
    deletable = BooleanField('deletable', id='au_deletable', validators=[])
    added_by = SelectField('Select Inventory Admin', id='au_addedby',  choices=[], coerce=int, validators=[InputRequired()])
    joinpass = PasswordField('Join Password (Optional)', id='au_joinpass', validators=[optional()],
                            render_kw={
                                    'title': 'Add an extra layer of security Enter the required password for private inventory user logins. The inventory must be private for the password to be applied.',
                                    'style': 'display:none;',
                                    'autocomplete': 'off'
                                }
                            )
    pass_salat = StringField('One Time Secert Keyword (Optional)', id="au_pass_salat", render_kw={'title': 'Keyword required to generate strong password'})
    update_inventory = SubmitField('update')

class deleteInventoriesForm(FlaskForm):
    inventory_remove_id = HiddenField(validators=[InputRequired()])
    delete_inventory = SubmitField('delete', id="inventories_delete")

class makeInvAdmin(FlaskForm):
    user = SelectField('Select User: ', id='mka_user',  choices=[], coerce=int, validators=[InputRequired()])
    action = SelectField('Make Admin: ', id='mka_action',  choices=[(1, 'No'), (2, 'Yes')], coerce=int, validators=[InputRequired()])
    update = SubmitField('Update User', id='mka_update')


class approveUserForm(FlaskForm):
    user_id = HiddenField(id='approve_uid', validators=[InputRequired()])
    approve = SubmitField('Approve User', id='approve_user')

class removeUserForm(FlaskForm):
    user_id = HiddenField(id='remove_uid', validators=[InputRequired()])
    remove = SubmitField('Remove User', id='remove_user')

class warningToManyUsers(FlaskForm):
    submit = SubmitField('Clear Data', id='warning_submit')

class adminChangeUserInv(FlaskForm):
    user = SelectField('Select User: ', id='c_uinv_admin',  choices=[], validators=[InputRequired()])
    inv = SelectField('Select Inventory: ', id='c_inv_admin',  choices=[], validators=[InputRequired()])
    change = SubmitField('Change Inventory', id='admin_change_submit')

class invAdminChangeUserInv(FlaskForm):
    user = SelectField('Select User: ', id='c_uinv_invadmin',  choices=[], validators=[InputRequired()])
    inv = SelectField('Select Inventory: ', id='c_inv_invadmin',  choices=[], validators=[InputRequired()])
    change = SubmitField('Change Inventory', id='invadmin_change_submit')