class ExportSqlalchemyFilter():
    # user sqlalchemy to create secure sqlalchemy filters arugments list (controlled easy)
    supplier_columns = []
    catalogue_columns = []
    listing_columns = []
    purchase_columns = []
    order_columns = []
    catalogue_table_filters = []
    listing_table_filters = []
    purchase_table_filters = []
    order_table_filters = []
    supplier_table_filters = []
    allowed_tables = {}
    tables_data = {}
    opeartors = ['=', '!=', '>', '<', '>=', '<=', 'val%', '%val', '%val%']
    
    def __init__(self):
        self.supplier_columns = getTableColumns(Supplier, ['user_id'])
        self.catalogue_columns = getTableColumns(Catalogue, ['user_id'])
        self.listing_columns = getTableColumns(Listing, expetColumns=['image', 'platform'])
        self.purchase_columns = getTableColumns(Purchase)
        self.order_columns = getTableColumns(Order)

        # rendered with same order in js (filters_args_list ...(args))
        catalogue_table_filters = [*self.catalogue_columns]
        listing_table_filters = [*self.listing_columns, *self.catalogue_columns]
        purchase_table_filters = [*self.purchase_columns, *self.listing_columns, *self.supplier_columns]
        order_table_filters = [*self.order_columns, *self.listing_columns, *self.catalogue_columns]
        supplier_table_filters = [*self.supplier_columns]
        table_classes = [Order, Purchase, Listing, Catalogue, Supplier]
        tables_data = {}

        self.allowed_tables = {
            'catalogue': [Catalogue],
            'listing': [Listing, Catalogue],
            'purchase': [Purchase, Listing, Catalogue],
            'order': [Order, Listing, Catalogue],
            'supplier': [Supplier]
        }

        # all posible columns can used in filter acording also to allowed
        self.tables_data = {
            'catalogue': catalogue_table_filters,
            'listing': listing_table_filters,
            'purchase': purchase_table_filters,
            'order': order_table_filters,
            'supplier': supplier_table_filters
        }


    def getSqlalchemyClassByName(self, classname):
        # encryption of name can happend here
        try:
            target_class = None
            classname_str = str(classname).strip().lower()

            # (secure) validate if table class included in filter conidtions provided, example (purchase.id, supplier.id) but not supplier.user_id (vailidate recived column_name in allowed columns for current query)
            table_classes = self.allowed_tables[classname_str] if classname_str in self.allowed_tables else None
            if table_classes is None:
                raise ValueError('Unknown Table error')
            
            for table_class in table_classes:
                 table_name = table_class.__tablename__.capitalize()
                 if table_name == classname:
                     target_class = table_class
                     break
            # all provided columns and tables must be vaild and renewed with ajax incase given class not found in alllowed some one try change inspect and provid unallowed table like user
            if target_class is None:
                raise ValueError('invalid table asked to exported')
        except Exception as e:
            print('error in getSqlalchemyClassByName, {}, {}'.format(e, sys.exc_info()))
            raise e
        return target_class

    def getSqlalchemyColumnByName(self, colname, table_name):
        target_column = None
        try:
            # table_name is tipical to class Order
            tablename_lower = str(table_name).strip().lower()
            current_columns = []

            table_class = self.getSqlalchemyClassByName(table_name)
            if not table_class:
                raise ValueError('found unknown table')

            # column_full_name = 'Supplier.user_id' # secuirty check
            column_full_name = '{}.{}'.format(table_name, colname)
            # check if Table.colname provided exist current table filters allowed option provided when init this class
            secuirty_check = column_full_name in self.tables_data[tablename_lower]
            if not secuirty_check:
                raise ValueError('invalid column provided')


            # handle each table ignore columns speartly most secure only given excuted else error
            for sqlalchemy_column in table_class.__table__.columns:
                if sqlalchemy_column.name == colname:                    
                    target_column = sqlalchemy_column
                
            if target_column is None:
                raise ValueError('column not found')
        except Exception as e:
            print('error in getSqlalchemyClassByName, {}, {}'.format(e, sys.exc_info()))
            raise e
        
        return target_column

    def createSqlalchemyConidtion(self, column_class, operator, value):
        
        opeartors = ['=', '!=', '>', '<', '>=', '<=', 'val%', '%val', '%val%']

        condition = False
        if operator not in opeartors:
            # always raise refere to secuirty issue or code issue, operators sent to form are in this array
            raise 'invalid operator found'
        
        if operator == '=':
            column_class = column_class == value
        elif operator == '!=':
            column_class = column_class != value
        elif operator == '>':
            column_class = column_class >= value
        elif operator == '<':
            column_class = column_class <= value
        elif operator == '>=':
            column_class = column_class >= value
        elif operator == '<=':
            column_class = column_class <= value
        elif operator == 'val%':
            search = f'{value}%'
            column_class = column_class.like(search)
        elif operator == '%val':
            search = f'%{value}'
            column_class = column_class.like(search)
        else:
            # based on condition if operator not in opeartors this else must only %val% as all previous covered
            search = f'%{value}%'
            column_class = column_class.like(search)
        return column_class
