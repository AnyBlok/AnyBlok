# This file is a part of the AnyBlok project
#
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from base64 import b64encode, b64decode
from .field import Field, FieldException
from .mapper import ModelAttributeAdapter, ModelAttribute
from sqlalchemy.schema import Sequence as SA_Sequence, Column as SA_Column
from sqlalchemy import types, CheckConstraint
from sqlalchemy_utils.types.color import ColorType
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType
from sqlalchemy_utils.types.password import PasswordType, Password as SAU_PWD
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.url import URLType
from sqlalchemy_utils.types.phone_number import PhoneNumberType
from sqlalchemy_utils.types.email import EmailType
from sqlalchemy_utils.types.scalar_coercible import ScalarCoercible
from sqlalchemy_utils import JSONType
from datetime import datetime, date, timedelta
from dateutil.parser import parse
from inspect import ismethod
from anyblok.config import Configuration
from .common import sgdb_in
from json import dumps, loads
import time
import pytz
import decimal
from logging import getLogger
from hashlib import md5


pycountry = None
python_pycountry_type = None
try:
    import pycountry
    if not pycountry.countries._is_loaded:
        pycountry.countries._load()

    python_pycountry_type = pycountry.countries.data_class
except ImportError:
    pass


logger = getLogger(__name__)


def wrap_default(registry, namespace, default_val):
    """Return default wrapper

    :param registry: the current registry
    :param namespace: the namespace of the model
    :param default_val:
    :return: default wrapper
    """
    def wrapper():
        """Return wrapper

        :return: default val
        """
        Model = registry.get(namespace)
        if hasattr(Model, default_val):
            func = getattr(Model, default_val)
            if ismethod(func):
                if default_val not in Model.loaded_columns:
                    if default_val not in Model.loaded_fields:
                        return func()
                    else:
                        logger.warning(
                            "The attribute %r is already declared as a default "
                            "value on the Model %r, a field with the same name "
                            "already exists" % (default_val, namespace))
                else:
                    logger.warning(
                        "The attribute %r is already declared as a default "
                        "value on the Model %r, a column with the same name "
                        "already exists" % (default_val, namespace))
            else:
                logger.warning(
                    "The attribute %r is already declared as a default "
                    "value on the Model %r, an instance method with the same "
                    "name already exists" % (default_val, namespace))

        return default_val

    return wrapper


class ColumnDefaultValue:

    def __init__(self, callable):
        self.callable = callable

    def get_default_callable(self, registry, namespace, fieldname, properties):
        """Get default callable

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param fieldname: the fieldname of the model
        :param properties: the properties of the model
        :return: default callable
        """
        return self.callable(registry, namespace, fieldname, properties)


class CompareType:

    comparators = []

    @classmethod
    def default_comparator(cls, col1, type1, col2, type2):
        if type1.__class__ is not type2.__class__:
            raise FieldException(
                "You can't add a foreign key using columns with different "
                "types {model1!s}.{col1!s}` pointing to `{model2!s}.{col2!s}` "
                "have different types  {type1!r} -> {type2!r}".format(
                    model1=col1.model_name,
                    col1=col1.attribute_name,
                    model2=col2.model_name,
                    col2=col2.attribute_name,
                    type1=type1.__class__,
                    type2=type2.__class__
                )
            )

    @classmethod
    def add_comparator(cls, type1, type2):

        def wrapper(funct):
            cls.comparators.append((type1, type2, funct))
            return funct

        return wrapper

    @classmethod
    def validate(cls, col1, type1, col2, type2):
        for (cls1, cls2, funct) in cls.comparators:
            if type1.__class__ is cls1 and type2.__class__ is cls2:
                funct(col1, type1, col2, type2)
                return

        cls.default_comparator(col1, type1, col2, type2)


class NoDefaultValue:
    pass


class Column(Field):
    """Column class

    This class can't be instantiated
    """

    use_hybrid_property = True
    foreign_key = None
    sqlalchemy_type = None
    type = None

    def __init__(self, *args, **kwargs):
        """Initialize the column

        :param label: label of this field
        :type label: str
        """
        self.forbid_instance(Column)
        assert self.sqlalchemy_type
        self.sequence = None

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = ModelAttributeAdapter(kwargs.pop('foreign_key'))

        if 'sequence' in kwargs:
            self.sequence = SA_Sequence(kwargs.pop('sequence'))

        self.db_column_name = None
        if 'db_column_name' in kwargs:
            self.db_column_name = kwargs.pop('db_column_name')

        self.default_val = NoDefaultValue
        if 'default' in kwargs:
            self.default_val = kwargs.pop('default')

        self.encrypt_key = kwargs.pop('encrypt_key', None)
        super(Column, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties list for autodoc

        :return: autodoc properties
        """
        res = super(Column, self).autodoc_get_properties()
        res['foreign_key'] = self.foreign_key
        res['DB column name'] = self.db_column_name
        res['default'] = self.default_val
        res['is crypted'] = True if self.encrypt_key else False
        return res

    autodoc_omit_property_values = Field.autodoc_omit_property_values.union((
        ('foreign_key', None),
        ('DB column name', None),
        ('default', None),
        ('is crypted', False),
    ))

    def native_type(self, registry):
        """Return the native SqlAlchemy type

        :param registry:
        :rtype: sqlalchemy native type
        """
        return self.sqlalchemy_type

    def format_foreign_key(self, registry, namespace, fieldname, args, kwargs):
        """Format a foreign key

        :param registry: the current registry
        :param args:
        :param kwargs:
        :return:
        """
        if self.foreign_key:
            CompareType.validate(
                ModelAttribute(namespace, fieldname), self,
                self.foreign_key, self.foreign_key.get_type(registry)
            )
            args = args + (self.foreign_key.get_fk(registry),)
            kwargs['info'].update({
                'foreign_key': self.foreign_key.get_fk_name(registry),
                'remote_model': self.foreign_key.model_name,
            })

        return args

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: known properties of the model
        :rtype: sqlalchemy column instance
        """
        self.format_label(fieldname)
        args = self.args
        kwargs = self.kwargs.copy()
        if 'info' not in kwargs:
            kwargs['info'] = {}
        args = self.format_foreign_key(
            registry, namespace, fieldname, args, kwargs)

        kwargs['info']['label'] = self.label
        if self.sequence:
            args = (self.sequence,) + args

        if self.db_column_name:
            db_column_name = self.db_column_name
        else:
            db_column_name = fieldname

        if self.default_val is not NoDefaultValue:
            if isinstance(self.default_val, str):
                kwargs['default'] = wrap_default(registry, namespace,
                                                 self.default_val)
            elif isinstance(self.default_val, ColumnDefaultValue):
                kwargs['default'] = self.default_val.get_default_callable(
                    registry, namespace, fieldname, properties)
            else:
                kwargs['default'] = self.default_val

        sqlalchemy_type = self.native_type(registry)

        if self.encrypt_key:
            encrypt_key = self.format_encrypt_key(registry, namespace)
            sqlalchemy_type = self.get_encrypt_key_type(
                registry, sqlalchemy_type, encrypt_key)

        return SA_Column(db_column_name, sqlalchemy_type, *args, **kwargs)

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.String(64)

        return sqlalchemy_type

    def format_encrypt_key(self, registry, namespace):
        """Format and return the encyption key

        :param registry: the current registry
        :param namespace: the namespace of the model
        :return: encrypt key
        """
        encrypt_key = self.encrypt_key
        if encrypt_key is True:
            encrypt_key = Configuration.get('default_encrypt_key')

        if not encrypt_key:
            raise FieldException(  # pragma: no cover
                "No encrypt_key defined in the configuration")

        def wrapper():
            """Return encrypt_key wrapper

            :return:
            """
            Model = registry.get(namespace)
            if hasattr(Model, encrypt_key):
                func = getattr(Model, encrypt_key)
                if ismethod(func):
                    if encrypt_key not in Model.loaded_columns:
                        if encrypt_key not in Model.loaded_fields:
                            return func()

            return encrypt_key

        return wrapper

    def must_be_declared_as_attr(self):
        """Return True if the column have a foreign key to a remote column """
        if self.foreign_key is not None:
            return True

        return False


class Integer(Column):
    """Integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Integer


        @Declarations.register(Declarations.Model)
        class Test:

            x = Integer(default=1)

    """

    def __init__(self, *args, **kwargs):
        super(Integer, self).__init__(*args, **kwargs)
        if self.kwargs.get('primary_key') is True:
            if 'autoincrement' not in self.kwargs:
                self.kwargs['autoincrement'] = True

    sqlalchemy_type = types.Integer


class BigInteger(Column):
    """Big integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import BigInteger


        @Declarations.register(Declarations.Model)
        class Test:

            x = BigInteger(default=1)

    """
    sqlalchemy_type = types.BigInteger


class Boolean(Column):
    """Boolean column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Boolean


        @Declarations.register(Declarations.Model)
        class Test:

            x = Boolean(default=True)

    """
    sqlalchemy_type = types.Boolean


class Float(Column):
    """Float column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Float


        @Declarations.register(Declarations.Model)
        class Test:

            x = Float(default=1.0)

    """
    sqlalchemy_type = types.Float


"""
    Added *process_result_value* at the class *DECIMAL*, because
    this method is necessary for encrypt the column
"""
types.DECIMAL.process_result_value = lambda self, value, dialect: value


class Decimal(Column):
    """Decimal column

    ::

        from decimal import Decimal as D
        from anyblok.declarations import Declarations
        from anyblok.column import Decimal


        @Declarations.register(Declarations.Model)
        class Test:

            x = Decimal(default=D('1.1'))

    """
    sqlalchemy_type = types.DECIMAL

    def setter_format_value(self, value):
        """Format the given value to decimal if needed

        :param value:
        :return: decimal value
        """
        if value is not None:
            if self.encrypt_key:
                value = str(value)
            elif not isinstance(value, decimal.Decimal):
                value = decimal.Decimal(value)

        return value

    def getter_format_value(self, value):
        if value is None:
            return None  # pragma: no cover

        if self.encrypt_key:
            value = decimal.Decimal(value)

        return value


class Date(Column):
    """Date column

    ::

        from datetime import date
        from anyblok.declarations import Declarations
        from anyblok.column import Date


        @Declarations.register(Declarations.Model)
        class Test:

            x = Date(default=date.today())

    """
    sqlalchemy_type = types.Date


def convert_string_to_datetime(value):
    """Convert a given value to datetime

    :param value:
    :return: datetime value
    """
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        return parse(value)

    raise FieldException(
        "We can't convert this value %s to datetime")


def add_timezone_on_datetime(dt, default_timezone):
    """Convert a datetime considering the default timezone

    :param dt:
    :param default_timezone:
    :return:
    """
    if dt is not None:
        if dt.tzinfo is None:
            dt = default_timezone.localize(dt)

    return dt


class DateTimeType(types.TypeDecorator):

    impl = types.DateTime(timezone=True)
    cache_ok = True

    def __init__(self, field):
        self.default_timezone = field.default_timezone
        self.field = field

    def process_bind_param(self, value, engine):
        value = convert_string_to_datetime(value)
        value = add_timezone_on_datetime(value, self.default_timezone)
        if self.field.encrypt_key:
            return value.isoformat()

        return value

    def process_result_value(self, value, dialect):
        if self.field.encrypt_key:
            return convert_string_to_datetime(value)

        return value

    @property
    def python_type(self):
        return datetime  # pragma: no cover


class DateTime(Column):
    """DateTime column

    ::

        from datetime import datetime
        from anyblok.declarations import Declarations
        from anyblok.column import DateTime


        @Declarations.register(Declarations.Model)
        class Test:

            x = DateTime(default=datetime.now)

    """

    def __init__(self, *args, **kwargs):
        self.auto_update = kwargs.pop('auto_update', False)
        default_timezone = kwargs.pop(
            'default_timezone',
            Configuration.get('default_timezone')
        )
        if not default_timezone:
            default_timezone = time.tzname[0]

        if isinstance(default_timezone, str):
            default_timezone = pytz.timezone(default_timezone)

        self.default_timezone = default_timezone
        self.sqlalchemy_type = DateTimeType(self)
        super(DateTime, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        """Return converted and formatted value

        :param value:
        :return:
        """
        value = convert_string_to_datetime(value)
        return add_timezone_on_datetime(value, self.default_timezone)

    def getter_format_value(self, value):
        value = convert_string_to_datetime(value)
        return add_timezone_on_datetime(value, self.default_timezone)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Column, self).autodoc_get_properties()
        res['is auto updated'] = self.auto_update
        if self.default_timezone:
            res['default timezone'] = self.default_timezone

        return res


class TimeStamp(DateTime):
    """ TimeStamp column

    ::

        from datetime import datetime
        from anyblok.declarations import Declarations
        from anyblok.column import DateTime


        @Declarations.register(Declarations.Model)
        class Test:

            x = TimeStamp(default=datetime.now)

    """

    def __init__(self, *args, **kwargs):
        super(TimeStamp, self).__init__(*args, **kwargs)
        self.sqlalchemy_type = types.TIMESTAMP(timezone=True)

    def getter_format_value(self, value):
        value = convert_string_to_datetime(value)
        return add_timezone_on_datetime(value, self.default_timezone)


class Time(Column):
    """Time column

    ::

        from datetime import time
        from anyblok.declarations import Declarations
        from anyblok.column import Time


        @Declarations.register(Declarations.Model)
        class Test:

            x = Time(default=time())

    """
    sqlalchemy_type = types.Time


class Interval(Column):
    """Datetime interval column

    ::

        from datetime import timedelta
        from anyblok.declarations import Declarations
        from anyblok.column import Interval


        @Declarations.register(Declarations.Model)
        class Test:

            x = Interval(default=timedelta(days=5))

    """
    sqlalchemy_type = types.Interval

    def native_type(self, registry):
        if self.encrypt_key:
            return types.VARCHAR(1024)

        return self.sqlalchemy_type

    def setter_format_value(self, value):
        if self.encrypt_key:
            value = dumps({
                x: getattr(value, x)
                for x in ['days', 'seconds', 'microseconds']})

        return value

    def getter_format_value(self, value):
        if self.encrypt_key:
            value = timedelta(**loads(value))

        return value


class StringType(types.TypeDecorator):

    impl = types.String
    cache_ok = True

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value

    def process_result_value(self, value, dialect):
        return value


class String(Column):
    """String column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import String


        @Declarations.register(Declarations.Model)
        class Test:

            x = String(default='test')

    """
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', 64)
        kwargs.pop('type_', None)
        self.sqlalchemy_type = StringType(self.size)
        super(String, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(String, self).autodoc_get_properties()
        res['size'] = self.size
        return res

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.String(max(self.size, 64))

        return sqlalchemy_type


class Enum(Column):
    """Enum column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Enum
        import enum


        class MyEnumClass(enum.Enum):
            one = 1
            two = 2
            three = 3


        @Declarations.register(Declarations.Model)
        class Test:

            x = Enum(enum_cls=MyEnumClass, default='test')

    enum_cls should be an enum class
    """
    def __init__(self, *args, **kwargs):
        self.enum_cls = kwargs.pop('enum_cls')
        self.sqlalchemy_type = types.Enum(self.enum_cls)
        super(Enum, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Enum, self).autodoc_get_properties()
        res['enum_cls'] = repr(self.enum_cls)
        return res


class MsSQLPasswordType(PasswordType):
    impl = types.VARCHAR(1024)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(self.length))


class Password(Column):
    """String column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Password


        @Declarations.register(Declarations.Model)
        class Test:

            x = Password(crypt_context={'schemes': ['md5_crypt']})

        =========================================

        test = Test.insert()
        test.x = 'mypassword'

        test.x
        ==> Password object with encrypt value, the value can not be read

        test.x == 'mypassword'
        ==> True

    ..warning::

        the column type Password can not be querying::

            Test.query().filter(Test.x == 'mypassword').count()
            ==> 0
    """
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', 64)
        crypt_context = kwargs.pop('crypt_context', {})
        self.crypt_context = crypt_context
        kwargs.pop('type_', None)

        if 'foreign_key' in kwargs:
            raise FieldException("Column Password can not have a foreign key")

        self.sqlalchemy_type = PasswordType(
            max_length=self.size, **crypt_context)
        super(Password, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        """Return formatted value

        :param value:
        :return:
        """
        value = self.sqlalchemy_type.context.hash(value).encode('utf8')
        value = SAU_PWD(value, context=self.sqlalchemy_type.context)
        return value

    def native_type(self, registry):
        """ Return the native SqlAlchemy type """
        if sgdb_in(registry.engine, ['MsSQL']):
            return MsSQLPasswordType(max_length=self.size, **self.crypt_context)

        return self.sqlalchemy_type

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Password, self).autodoc_get_properties()
        res['size'] = self.size
        res['Crypt context'] = self.crypt_context
        return res


class TextType(types.TypeDecorator):

    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value

    def process_result_value(self, value, dialect):
        return value


class Text(Column):
    """Text column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Text


        @Declarations.register(Declarations.Model)
        class Test:

            x = Text(default='test')

    """
    sqlalchemy_type = TextType

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.Text()

        return sqlalchemy_type


class StrSelection(str):
    """Class representing the data of one column Selection """
    selections = dumps({})
    registry = None
    namespace = None

    def get_selections(self):
        """Return a dict of selections

        :return: selections dict
        """
        selections = loads(self.selections)
        if isinstance(selections, dict):
            return selections
        if isinstance(selections, str):
            m = self.registry.get(self.namespace)
            return dict(getattr(m, selections)())

    def validate(self):
        """Validate if the key is in the selections

        :return: True or False
        """
        a = super(StrSelection, self).__str__()
        return a in self.get_selections().keys()

    @property
    def label(self):
        """Return the label corresponding to the selection key

        :return:
        """
        a = super(StrSelection, self).__str__()
        return self.get_selections()[a]


class SelectionType(types.TypeDecorator):
    """Generic type for Column Selection """

    impl = types.String
    cache_ok = True

    def __init__(self, selections, size, registry=None, namespace=None):
        super(SelectionType, self).__init__(length=size)
        self.size = size
        if isinstance(selections, (dict, str)):
            self.selections = selections
        elif isinstance(selections, (list, tuple)):
            self.selections = dict(selections)
        else:
            raise FieldException(  # pragma: no cover
                "selection wainting 'dict', get %r" % type(selections))

        if isinstance(self.selections, dict):
            for k in self.selections.keys():
                if not isinstance(k, str):
                    raise FieldException('The key must be a str')
                if len(k) > 64:
                    raise Exception(  # pragma: no cover
                        '%r is too long %r, waiting max %s or use size arg' % (
                            k, len(k), size))

        self.selections = dumps(self.selections)
        self._StrSelection = type('StrSelection', (StrSelection,),
                                  {'selections': self.selections,
                                   'registry': registry,
                                   'namespace': namespace})

    @property
    def python_type(self):
        return self._StrSelection

    def process_bind_param(self, value, engine):
        if value is not None:
            value = self.python_type(value)

        return value

    def process_result_value(self, value, dialect):
        return value


class Selection(Column):
    """Selection column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Selection


        @Declarations.register(Declarations.Model)
        class Test:
            STATUS = (
                (u'draft', u'Draft'),
                (u'done', u'Done'),
            )

            x = Selection(selections=STATUS, size=64, default=u'draft')

    """
    def __init__(self, *args, **kwargs):
        self.selections = tuple()
        if 'selections' in kwargs:
            self.selections = kwargs.pop('selections')

        self.size = kwargs.pop('size', 64)
        self.sqlalchemy_type = 'tmp value for assert'

        super(Selection, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Selection, self).autodoc_get_properties()
        res['selections'] = self.selections
        res['size'] = self.size
        return res

    def getter_format_value(self, value):
        """Return formatted value

        :param value:
        :return:
        """
        if value is None:
            return None

        return self.sqlalchemy_type.python_type(value)

    def setter_format_value(self, value):
        """Return value or raise exception if the given value is invalid

        :param value:
        :exception FieldException
        :return:
        """
        if value is not None:
            val = self.sqlalchemy_type.python_type(value)
            if not val.validate():
                raise FieldException('%r is not in the selections (%s)' % (
                    value, ', '.join(val.get_selections())))

        return value

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """Return sqlalchmy mapping

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param fieldname: the fieldname of the model
        :param properties: the properties of the model
        :return: instance of the real field
        """
        self.sqlalchemy_type = SelectionType(
            self.selections, self.size, registry=registry, namespace=namespace)
        return super(Selection, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def update_description(self, registry, model, res):
        """Update model description

        :param registry: the current registry
        :param model:
        :param res:
        """
        super(Selection, self).update_description(registry, model, res)
        sqlalchemy_type = SelectionType(
            self.selections, self.size, registry=registry, namespace=model)
        values = sqlalchemy_type._StrSelection().get_selections()
        res['selections'] = [(k, v) for k, v in values.items()]

    def must_be_copied_before_declaration(self):
        """Return True if selections is an instance of str.
        In the case of the field selection is a mixin, it must be copied or the
        selection method can fail
        """
        if isinstance(self.selections, str):
            return True
        else:
            return False

    def update_properties(self, registry, namespace, fieldname, properties):
        """Update column properties

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param fieldname: the fieldname of the model
        :param properties: the properties of the model
        """
        super(Selection, self).update_properties(registry, namespace,
                                                 fieldname, properties)
        self.fieldname = fieldname
        properties['add_in_table_args'].append(self)

    def update_table_args(self, registry, Model):
        """Return check constraints to limit the value

        :param registry:
        :param Model:
        :return: list of checkConstraint
        """
        if self.encrypt_key:
            # dont add constraint because the state is crypted and nobody
            # can add new entry
            return []

        if sgdb_in(registry.engine, ['MariaDB', 'MsSQL']):
            # No check constraint in MariaDB
            return []

        selections = loads(self.sqlalchemy_type.selections)
        if isinstance(selections, dict):
            enum = selections.keys()
        else:
            enum = getattr(Model, selections)()
            if isinstance(enum, (list, tuple)):
                enum = dict(enum)

            enum = enum.keys()

        if len(enum) > 1:
            constraint = """"%s" in ('%s')""" % (
                self.fieldname, "', '".join(enum))
        elif enum:
            constraint = """"%s" = '%s'""" % (self.fieldname, list(enum)[0])
        else:
            constraint = None

        if constraint:
            enum = list(enum)
            enum.sort()
            key = md5()
            key.update(str(enum).encode('utf-8'))
            name = self.fieldname + '_' + key.hexdigest() + '_types'
            return [CheckConstraint(constraint, name=name)]

        return []

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.String(max(self.size, 64))

        return sqlalchemy_type


"""
    Added *process_result_value* at the class *JSON*, because
    this method is necessary for encrypt the column
"""
types.JSON.process_result_value = lambda self, value, dialect: value


class Json(Column):
    """JSON column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Json


        @Declarations.register(Declarations.Model)
        class Test:

            x = Json()

    """
    sqlalchemy_type = types.JSON(none_as_null=True)

    def native_type(self, registry):
        """ Return the native SqlAlchemy type """
        if sgdb_in(registry.engine, ['MariaDB', 'MsSQL']):
            return JSONType

        return self.sqlalchemy_type

    def setter_format_value(self, value):
        if self.encrypt_key:
            value = dumps(value)

        return value

    def getter_format_value(self, value):
        if value is None:
            return None

        if self.encrypt_key:
            value = loads(value)

        return value

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.Text()

        return sqlalchemy_type


class LargeBinary(Column):
    """Large binary column

    ::

        from os import urandom
        from anyblok.declarations import Declarations
        from anyblok.column import LargeBinary


        blob = urandom(100000)


        @Declarations.register(Declarations.Model)
        class Test:

            x = LargeBinary(default=blob)

    """
    sqlalchemy_type = types.LargeBinary

    def native_type(self, registry):
        if self.encrypt_key:
            return types.Text

        return self.sqlalchemy_type

    def setter_format_value(self, value):
        if self.encrypt_key:
            value = b64encode(value).decode('utf-8')

        return value

    def getter_format_value(self, value):
        if self.encrypt_key:
            value = b64decode(value.encode('utf-8'))

        return value

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.Text()

        return sqlalchemy_type


class Sequence(String):
    """Sequence column

    ::

        from anyblok.column import Sequence


        @Declarations.register(Declarations.Model)
        class Test:

            x = Sequence()

    """
    def __init__(self, *args, **kwargs):
        if 'foreign_key' in kwargs:
            raise FieldException("Sequence column can not define a foreign key"
                                 " %r" % kwargs['foreign_key'])
        if 'default' in kwargs:
            raise FieldException("Sequence column can not define a default "
                                 "value")
        kwargs['default'] = ColumnDefaultValue(self.wrap_default)

        self.code = kwargs.pop('code') if 'code' in kwargs else None
        self.start = kwargs.pop('start', 1)
        self.formater = kwargs.pop(
            'formater') if 'formater' in kwargs else None

        super(Sequence, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Sequence, self).autodoc_get_properties()
        res['formater'] = self.formater
        return res

    def wrap_default(self, registry, namespace, fieldname, properties):
        """Return default wrapper

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param fieldname: the fieldname of the model
        :return:
        """
        if not hasattr(
            registry, '_need_sequence_to_create_if_not_exist'
        ):  # pragma: no cover
            registry._need_sequence_to_create_if_not_exist = []
        elif registry._need_sequence_to_create_if_not_exist is None:
            registry._need_sequence_to_create_if_not_exist = []

        code = self.code if self.code else "%s=>%s" % (namespace, fieldname)
        registry._need_sequence_to_create_if_not_exist.append(
            {'code': code, 'formater': self.formater, 'start': self.start})

        def default_value():
            """Return next sequence value

            :return:
            """
            return registry.System.Sequence.nextvalBy(code=code)

        return default_value


class Color(Column):
    """Color column.
    `See colour package on pypi <https://pypi.python.org/pypi/colour/>`_

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Color


        @Declarations.register(Declarations.Model)
        class Test:

            x = Color(default='green')

    """
    def __init__(self, *args, **kwargs):
        self.max_length = max_length = kwargs.pop('size', 20)
        kwargs.pop('type_', None)
        self.sqlalchemy_type = ColorType(max_length)
        super(Color, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        """Format the given value

        :param value:
        :return:
        """
        if isinstance(value, str):
            value = self.sqlalchemy_type.python_type(value)

        return value

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Color, self).autodoc_get_properties()
        res['size'] = self.max_length
        return res

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.String(max(self.max_length, 64))

        return sqlalchemy_type


class UUID(Column):
    """UUID column

    ::

        from anyblok.column import UUID


        @Declarations.register(Declarations.Model)
        class Test:

            x = UUID()

    """
    def __init__(self, *args, **kwargs):
        uuid_kwargs = {}
        self.binary = None
        self.native = None
        for kwarg in ('binary', 'native'):
            if kwarg in kwargs:
                uuid_kwargs[kwarg] = kwargs.pop(kwarg)
                setattr(self, kwarg, uuid_kwargs[kwarg])

        self.sqlalchemy_type = UUIDType(**uuid_kwargs)
        super(UUID, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(UUID, self).autodoc_get_properties()
        res['binary'] = self.binary
        res['native'] = self.native
        return res


URLType.cache_ok = True  # waiting fix from sqlalchemy_utils


class URL(Column):
    """URL column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import URL


        @Declarations.register(Declarations.Model)
        class Test:

            x = URL(default='doc.anyblok.org')

    """
    sqlalchemy_type = URLType

    def setter_format_value(self, value):
        """Return formatted url value

        :param value:
        :return:
        """
        from furl import furl

        if value is not None:
            if isinstance(value, str):
                value = furl(value)

        return value


class PhoneNumber(Column):
    """PhoneNumber column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import PhoneNumber


        @Declarations.register(Declarations.Model)
        class Test:

            x = PhoneNumber(default='+120012301')


    .. note:: ``phonenumbers`` >= **8.9.5** distribution is required

    """
    def __init__(self, region='FR', max_length=20, *args, **kwargs):
        self.region = region
        self.max_length = max_length
        kwargs.pop('type_', None)

        self.sqlalchemy_type = PhoneNumberType(
            region=region, max_length=max_length)
        super(PhoneNumber, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        """Return formatted phone number value

        :param value:
        :return:
        """
        if value and isinstance(value, str):
            value = self.sqlalchemy_type.python_type(value, self.region)

        return value

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(PhoneNumber, self).autodoc_get_properties()
        res['region'] = self.region
        res['max_length'] = self.max_length
        return res

    def get_encrypt_key_type(self, registry, sqlalchemy_type, encrypt_key):
        sqlalchemy_type = StringEncryptedType(sqlalchemy_type, encrypt_key)
        if sgdb_in(registry.engine, ['MySQL', 'MariaDB']):
            sqlalchemy_type.impl = types.String(max(self.max_length, 64))

        return sqlalchemy_type


"""
    Added *process_result_value* at the class *EmailType*, because
    this method is necessary for encrypt the column
"""
EmailType.process_result_value = lambda self, value, dialect: value
EmailType.cache_ok = True  # waiting fix from sqlalchemy_utils


class Email(Column):
    """Email column

    ::

        from anyblok.column import Email


        @Declarations.register(Declarations.Model)
        class Test:

            x = Email()

    """
    sqlalchemy_type = EmailType

    def setter_format_value(self, value):
        """Return formatted email value

        :param value:
        :return:
        """
        if value is not None:
            return value.lower()

        return value  # pragma: no cover


class CountryType(types.TypeDecorator, ScalarCoercible):
    """Generic type for Column Country """

    impl = types.Unicode(3)
    cache_ok = True
    python_type = python_pycountry_type

    def process_bind_param(self, value, dialect):
        if value and isinstance(value, self.python_type):
            return value.alpha_3

        return value

    def process_result_value(self, value, dialect):
        return self._coerce(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, self.python_type):
            return pycountry.countries.get(alpha_3=value)

        return value  # pragma: no cover


class Country(Column):
    """Country column.

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Country
        from pycountry import countries


        @Declarations.register(Declarations.Model)
        class Test:

            x = Country(default=countries.get(alpha_2='FR'))

    """
    sqlalchemy_type = CountryType

    def __init__(self, mode='alpha_2', *args, **kwargs):
        self.mode = mode
        if pycountry is None:
            raise FieldException(  # pragma: no cover
                "'pycountry' package is required for use 'CountryType'")

        self.choices = {getattr(country, mode): country.name
                        for country in pycountry.countries}
        super(Country, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        """Return formatted country value

        :param value:
        :return:
        """
        if value and not isinstance(value, self.sqlalchemy_type.python_type):
            value = pycountry.countries.get(
                **{
                    self.mode: value,
                    'default': pycountry.countries.lookup(value)
                })

        return value

    def autodoc_get_properties(self):
        """Return properties for autodoc

        :return: autodoc properties
        """
        res = super(Country, self).autodoc_get_properties()
        res['mode'] = self.mode
        res['choices'] = self.choices
        return res

    def update_properties(self, registry, namespace, fieldname, properties):
        """Update column properties

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param fieldname: the fieldname of the model
        :param properties: the properties of the model
        """
        super(Country, self).update_properties(registry, namespace,
                                               fieldname, properties)
        self.fieldname = fieldname
        properties['add_in_table_args'].append(self)

    def update_table_args(self, registry, Model):
        """Return check constraints to limit the value

        :param registry:
        :param Model:
        :return: list of checkConstraint
        """
        if self.encrypt_key:
            # dont add constraint because the state is crypted and nobody
            # can add new entry
            return []

        if sgdb_in(registry.engine, ['MariaDB', 'MsSQL']):
            # No Check constraint in MariaDB
            return []

        enum = [country.alpha_3 for country in pycountry.countries]
        constraint = """"%s" in ('%s')""" % (self.fieldname, "', '".join(enum))
        enum.sort()
        key = md5()
        key.update(str(enum).encode('utf-8'))
        name = self.fieldname + '_' + key.hexdigest() + '_types'
        return [CheckConstraint(constraint, name=name)]


@CompareType.add_comparator(String, String)
@CompareType.add_comparator(String, Selection)
@CompareType.add_comparator(String, Sequence)
def compare_strings(col1, type1, col2, type2):
    if type1.size != type2.size:
        raise FieldException(
            "You can't add a foreign key using based String columns with "
            "different size `{model1!s}.{col1!s}` pointing to "
            "`{model2!s}.{col2!s}` have different sizes  {type1!r}({size1:d}) "
            "-> ({type2!r}){size2:d}".format(
                model1=col1.model_name,
                col1=col1.attribute_name,
                model2=col2.model_name,
                col2=col2.attribute_name,
                type1=type1.__class__,
                type2=type2.__class__,
                size1=type1.size,
                size2=type2.size
            )
        )


@CompareType.add_comparator(String, Color)
def compare_string_to_color(col1, type1, col2, type2):
    if type1.size != type2.max_length:
        raise FieldException(
            "You can't add a foreign key using based String columns with "
            "different size `{model1!s}.{col1!s}` pointing to "
            "`{model2!s}.{col2!s}` have different sizes  {type1!r}({size1:d}) "
            "-> ({type2!r}){size2:d}".format(
                model1=col1.model_name,
                col1=col1.attribute_name,
                model2=col2.model_name,
                col2=col2.attribute_name,
                type1=type1.__class__,
                type2=type2.__class__,
                size1=type1.size,
                size2=type2.max_length
            )
        )
