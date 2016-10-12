# This file is a part of the AnyBlok project
#
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .field import Field, FieldException
from .mapper import ModelAttributeAdapter
from sqlalchemy.schema import Sequence as SA_Sequence, Column as SA_Column
from sqlalchemy import types
from sqlalchemy_utils.types.color import ColorType
from sqlalchemy_utils.types.encrypted import EncryptedType
from sqlalchemy_utils.types.password import PasswordType, Password as SAU_PWD
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.url import URLType
from datetime import datetime, date
from dateutil.parser import parse
import json
from copy import deepcopy
from inspect import ismethod
from anyblok.config import Configuration
import time
import pytz
import decimal
from logging import getLogger
logger = getLogger(__name__)


def wrap_default(registry, namespace, default_val):

    def wrapper():
        Model = registry.get(namespace)
        if hasattr(Model, default_val):
            func = getattr(Model, default_val)
            if ismethod(func):
                if default_val not in Model.loaded_columns:
                    if default_val not in Model.loaded_fields:
                        return func()
                    else:
                        logger.warn("On a Model %r the attribute %r is "
                                    "declared as a default value, a field "
                                    "with the same name exist" % (namespace,
                                                                  default_val))
                else:
                    logger.warn("On a Model %r the attribute %r is declared "
                                "as a default value, a column with the same "
                                "name exist" % (namespace, default_val))
            else:
                logger.warn("On a Model %r the attribute %r is declared as a "
                            "default value, a instance method with the same "
                            "name exist" % (namespace, default_val))

        return default_val

    return wrapper


class ColumnDefaultValue:

    def __init__(self, callable):
        self.callable = callable

    def get_default_callable(self, registry, namespace, fieldname, properties):
        return self.callable(registry, namespace, fieldname, properties)


class NoDefaultValue:
    pass


class Column(Field):
    """ Column class

    This class can't be instanciated
    """

    use_hybrid_property = True
    foreign_key = None
    sqlalchemy_type = None

    def __init__(self, *args, **kwargs):
        """ Initialize the column

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
        res = super(Column, self).autodoc_get_properties()
        res['foreign_key'] = self.foreign_key
        res['DB column name'] = self.db_column_name
        res['default'] = self.default_val
        res['is crypted'] = True if self.encrypt_key else False
        return res

    def native_type(cls):
        """ Return the native SqlAlchemy type """
        return cls.sqlalchemy_type

    def format_foreign_key(self, registry, args, kwargs):
        if self.foreign_key:
            args = args + (self.foreign_key.get_fk(registry),)
            kwargs['info'].update({
                'foreign_key': self.foreign_key.get_fk_name(registry),
                'remote_model': self.foreign_key.model_name,
            })

        return args

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

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
        args = self.format_foreign_key(registry, args, kwargs)
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

        sqlalchemy_type = self.sqlalchemy_type
        if self.encrypt_key:
            encrypt_key = self.format_encrypt_key(registry, namespace)
            sqlalchemy_type = EncryptedType(sqlalchemy_type, encrypt_key)

        return SA_Column(db_column_name, sqlalchemy_type, *args, **kwargs)

    def format_encrypt_key(self, registry, namespace):
        encrypt_key = self.encrypt_key
        if encrypt_key is True:
            encrypt_key = Configuration.get('default_encrypt_key')

        if not encrypt_key:
            raise FieldException("No encrypt_key define in the "
                                 "configuration")

        def wrapper():
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
        """ Return True if the column have a foreign key to a remote column """
        if self.foreign_key is not None:
            return True

        return False


class Integer(Column):
    """ Integer column

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


class SmallInteger(Column):
    """ Small integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import SmallInteger


        @Declarations.register(Declarations.Model)
        class Test:

            x = SmallInteger(default=1)

    """
    sqlalchemy_type = types.SmallInteger


class BigInteger(Column):
    """ Big integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import BigInteger


        @Declarations.register(Declarations.Model)
        class Test:

            x = BigInteger(default=1)

    """
    sqlalchemy_type = types.BigInteger


class Boolean(Column):
    """ Boolean column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Boolean


        @Declarations.register(Declarations.Model)
        class Test:

            x = Boolean(default=True)

    """
    sqlalchemy_type = types.Boolean


class Float(Column):
    """ Float column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Float


        @Declarations.register(Declarations.Model)
        class Test:

            x = Float(default=1.0)

    """
    sqlalchemy_type = types.Float


class Decimal(Column):
    """ Decimal column

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
        if value is not None:
            if not isinstance(value, decimal.Decimal):
                value = decimal.Decimal(value)

        return value


class Date(Column):
    """ Date column

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
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        return parse(value)

    return value


class DateTimeType(types.TypeDecorator):

    impl = types.DateTime(timezone=True)

    def process_bind_param(self, value, engine):
        value = convert_string_to_datetime(value)
        if value is not None:
            if value.tzinfo is None:
                timezone = pytz.timezone(time.tzname[0])
                value = timezone.localize(value)

        return value

    @property
    def python_type(self):
        return datetime


class DateTime(Column):
    """ DateTime column

    ::

        from datetime import datetime
        from anyblok.declarations import Declarations
        from anyblok.column import DateTime


        @Declarations.register(Declarations.Model)
        class Test:

            x = DateTime(default=datetime.now)

    """
    sqlalchemy_type = DateTimeType

    def setter_format_value(self, value):
        value = convert_string_to_datetime(value)
        if value is not None:
            if value.tzinfo is None:
                timezone = pytz.timezone(time.tzname[0])
                value = timezone.localize(value)

        return value


class Time(Column):
    """ Time column

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
    """ Datetime interval column

    ::

        from datetime import timedelta
        from anyblok.declarations import Declarations
        from anyblok.column import Interval


        @Declarations.register(Declarations.Model)
        class Test:

            x = Interval(default=timedelta(days=5))

    """
    sqlalchemy_type = types.Interval


class StringType(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value


class String(Column):
    """ String column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import String


        @Declarations.register(Declarations.Model)
        class Test:

            x = String(default='test')

    """
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', 64)
        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        self.sqlalchemy_type = StringType(self.size)
        super(String, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        res = super(String, self).autodoc_get_properties()
        res['size'] = self.size
        return res


class Password(Column):
    """ String column

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
        size = kwargs.pop('size', 64)
        crypt_context = kwargs.pop('crypt_context', {})
        self.crypt_context = crypt_context

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            raise FieldException("Column Password can not have a foreign key")

        self.sqlalchemy_type = PasswordType(max_length=size, **crypt_context)
        super(Password, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        value = self.sqlalchemy_type.context.encrypt(value).encode('utf8')
        value = SAU_PWD(value, context=self.sqlalchemy_type.context)
        return value

    def autodoc_get_properties(self):
        res = super(Password, self).autodoc_get_properties()
        res['Crypt context'] = self.crypt_context
        return res


class uStringType(types.TypeDecorator):

    impl = types.Unicode

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value


class uString(Column):
    """ Unicode column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import uString


        @Declarations.register(Declarations.Model)
        class Test:

            x = uString(de", default=u'test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')
            self.size = size

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        self.sqlalchemy_type = uStringType(size)

        super(uString, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        res = super(uString, self).autodoc_get_properties()
        res['size'] = self.size
        return res


class TextType(types.TypeDecorator):

    impl = types.Text

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value


class Text(Column):
    """ Text column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Text


        @Declarations.register(Declarations.Model)
        class Test:

            x = Text(default='test')

    """
    sqlalchemy_type = TextType


class UnicodeTextType(types.TypeDecorator):

    impl = types.UnicodeText

    def process_bind_param(self, value, engine):
        if value is False:
            value = ''

        return value


class uText(Column):
    """ Unicode text column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import uText


        @Declarations.register(Declarations.Model)
        class Test:

            x = uText(default=u'test')

    """
    sqlalchemy_type = UnicodeTextType


class StrSelection(str):
    """ Class representing the data of one column Selection """
    selections = {}
    registry = None
    namespace = None

    def get_selections(self):
        if isinstance(self.selections, dict):
            return self.selections
        if isinstance(self.selections, str):
            m = self.registry.get(self.namespace)
            return dict(getattr(m, self.selections)())

    def validate(self):
        a = super(StrSelection, self).__str__()
        return a in self.get_selections().keys()

    @property
    def label(self):
        a = super(StrSelection, self).__str__()
        return self.get_selections()[a]


class SelectionType(types.TypeDecorator):
    """ Generic type for Column Selection """

    impl = types.String

    def __init__(self, selections, size, registry=None, namespace=None):
        super(SelectionType, self).__init__(length=size)
        self.size = size
        if isinstance(selections, (dict, str)):
            self.selections = selections
        elif isinstance(selections, (list, tuple)):
            self.selections = dict(selections)
        else:
            raise FieldException(
                "selection wainting 'dict', get %r" % type(selections))

        if isinstance(self.selections, dict):
            for k in self.selections.keys():
                if not isinstance(k, str):
                    raise FieldException('The key must be a str')
                if len(k) > 64:
                    raise Exception(
                        '%r is too long %r, waiting max %s or use size arg' % (
                            k, len(k), size))

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


class Selection(Column):
    """ Selection column

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
        self.size = 64
        if 'selections' in kwargs:
            self.selections = kwargs.pop('selections')

        if 'size' in kwargs:
            self.size = kwargs.pop('size')

        self.sqlalchemy_type = 'tmp value for assert'

        super(Selection, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        res = super(Selection, self).autodoc_get_properties()
        res['selections'] = self.selections
        res['size'] = self.size
        return res

    def getter_format_value(self, value):
        if value is None:
            return None

        return self.sqlalchemy_type.python_type(value)

    def setter_format_value(self, value):
        if value is not None:
            val = self.sqlalchemy_type.python_type(value)
            if not val.validate():
                raise FieldException('%r is not in the selections (%s)' % (
                    value, ', '.join(val.get_selections())))

        return value

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        self.sqlalchemy_type = SelectionType(
            self.selections, self.size, registry=registry, namespace=namespace)
        return super(Selection, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def update_description(self, registry, model, res):
        super(Selection, self).update_description(registry, model, res)
        sqlalchemy_type = SelectionType(
            self.selections, self.size, registry=registry, namespace=model)
        values = sqlalchemy_type._StrSelection().get_selections()
        res['selections'] = [(k, v) for k, v in values.items()]

    def must_be_duplicate_before_added(self):
        """ Return True because the field selection in a mixin must be copied
        else the selection method can be wrond
        """
        if isinstance(self.selections, str):
            return True
        else:
            return False


json_null = object()


class JsonType(types.TypeDecorator):
    """ Generic type for Column JSON """
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is json_null:
            value = None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

    def copy_value(self, value):
        return deepcopy(value)

    def compare_values(self, x, y):
        return x == y

    @property
    def python_type(self):
        return object


class Json(Column):
    """ JSON column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Json


        @Declarations.register(Declarations.Model)
        class Test:

            x = Json()

    """
    sqlalchemy_type = JsonType
    Null = json_null


class LargeBinary(Column):
    """ Large binary column

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


class Sequence(String):
    """ Sequence column

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
        self.formater = kwargs.pop(
            'formater') if 'formater' in kwargs else None

        super(Sequence, self).__init__(*args, **kwargs)

    def autodoc_get_properties(self):
        res = super(Sequence, self).autodoc_get_properties()
        res['formater'] = self.formater
        return res

    def wrap_default(self, registry, namespace, fieldname, properties):
        if not hasattr(registry, '_need_sequence_to_create_if_not_exist'):
            registry._need_sequence_to_create_if_not_exist = []
        elif registry._need_sequence_to_create_if_not_exist is None:
            registry._need_sequence_to_create_if_not_exist = []

        code = self.code if self.code else "%s=>%s" % (namespace, fieldname)
        registry._need_sequence_to_create_if_not_exist.append(
            {'code': code, 'formater': self.formater})

        def default_value():
            return registry.System.Sequence.nextvalBy(code=code)

        return default_value


class Color(Column):
    """Color column.
    `See coulour pakage <https://pypi.python.org/pypi/colour/>`_

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Color


        @Declarations.register(Declarations.Model)
        class Test:

            x = Color(default='green')

    """
    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('size', 20)

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        self.sqlalchemy_type = ColorType(max_length)
        super(Color, self).__init__(*args, **kwargs)

    def setter_format_value(self, value):
        if isinstance(value, str):
            value = self.sqlalchemy_type.python_type(value)

        return value


class UUID(String):
    """ Sequence column

    ::

        from anyblok.column import UUID


        @Declarations.register(Declarations.Model)
        class Test:

            x = UUID()

    """
    def __init__(self, *args, **kwargs):
        uuid_kwargs = {}
        for kwarg in ('binary', 'native'):
            if kwarg in kwargs:
                uuid_kwargs[kwarg] = kwargs.pop(kwarg)

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        self.sqlalchemy_type = UUIDType(**uuid_kwargs)
        super(String, self).__init__(*args, **kwargs)


class URL(Column):
    """ Integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import URL


        @Declarations.register(Declarations.Model)
        class Test:

            x = URL(default='doc.anyblok.org')

    """
    sqlalchemy_type = URLType

    def setter_format_value(self, value):
        from furl import furl

        if value is not None:
            if isinstance(value, str):
                value = furl(value)

        return value
