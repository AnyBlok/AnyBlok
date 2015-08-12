# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .field import Field, FieldException
from .mapper import ModelAttributeAdapter
from sqlalchemy.schema import Sequence as SA_Sequence, Column as SA_Column
from sqlalchemy import types
from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer as SA_Integer
from sqlalchemy.types import SmallInteger as SA_SmallInteger
from sqlalchemy.types import BigInteger as SA_BigInteger
from sqlalchemy.types import Boolean as SA_Boolean
from sqlalchemy.types import Float as SA_Float
from sqlalchemy.types import DECIMAL as SA_Decimal
from sqlalchemy.types import Date as SA_Date
from sqlalchemy.types import DateTime as SA_DateTime
from sqlalchemy.types import Time as SA_Time
from sqlalchemy.types import Interval as SA_Interval
from sqlalchemy.types import String as SA_String
from sqlalchemy.types import Unicode
from sqlalchemy.types import Text as SA_Text
from sqlalchemy.types import UnicodeText
from sqlalchemy.types import LargeBinary as SA_LargeBinary
import json
from copy import deepcopy
from inspect import ismethod
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

        super(Column, self).__init__(*args, **kwargs)

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
            kwargs['info']['use_db_column_name'] = db_column_name
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

        return SA_Column(db_column_name, self.sqlalchemy_type, *args, **kwargs)

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
    sqlalchemy_type = SA_Integer


class SmallInteger(Column):
    """ Small integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import SmallInteger


        @Declarations.register(Declarations.Model)
        class Test:

            x = SmallInteger(default=1)

    """
    sqlalchemy_type = SA_SmallInteger


class BigInteger(Column):
    """ Big integer column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import BigInteger


        @Declarations.register(Declarations.Model)
        class Test:

            x = BigInteger(default=1)

    """
    sqlalchemy_type = SA_BigInteger


class Boolean(Column):
    """ Boolean column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Boolean


        @Declarations.register(Declarations.Model)
        class Test:

            x = Boolean(default=True)

    """
    sqlalchemy_type = SA_Boolean


class Float(Column):
    """ Float column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Float


        @Declarations.register(Declarations.Model)
        class Test:

            x = Float(default=1.0)

    """
    sqlalchemy_type = SA_Float


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
    sqlalchemy_type = SA_Decimal


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
    sqlalchemy_type = SA_Date


class DateTime(Column):
    """ DateTime column

    ::

        from datetime import datetime
        from anyblok.declarations import Declarations
        from anyblok.column import DateTime


        @Declarations.register(Declarations.Model)
        class Test:

            x = DateTime(default=datetime.now())

    """
    sqlalchemy_type = SA_DateTime


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
    sqlalchemy_type = SA_Time


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
    sqlalchemy_type = SA_Interval


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
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')
            self.size = size

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        self.sqlalchemy_type = SA_String(size)

        super(String, self).__init__(*args, **kwargs)


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

        self.sqlalchemy_type = Unicode(size)

        super(uString, self).__init__(*args, **kwargs)


class Text(Column):
    """ Text column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import Text


        @Declarations.register(Declarations.Model)
        class Test:

            x = Text(default='test')

    """
    sqlalchemy_type = SA_Text


class uText(Column):
    """ Unicode text column

    ::

        from anyblok.declarations import Declarations
        from anyblok.column import uText


        @Declarations.register(Declarations.Model)
        class Test:

            x = uText(default=u'test')

    """
    sqlalchemy_type = UnicodeText


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


class SelectionType(types.UserDefinedType):
    """ Generic type for Column Selection """

    def __init__(self, selections, size, registry=None, namespace=None):
        super(SelectionType, self).__init__()
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

    def compare_type(self, other):
        """ return True if the types are different,
            False if not, or None to allow the default implementation
            to compare these types
        """
        if isinstance(other, sqltypes.VARCHAR):
            return False

        return None

    def get_col_spec(self):
        return "VARCHAR(%r)" % self.size

    @property
    def python_type(self):
        return self._StrSelection


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

    def update_properties(self, registry, namespace, fieldname, properties):
        field = properties[fieldname]
        if '_' + fieldname in properties.keys():
            raise Exception('Exception')

        properties['_' + fieldname] = field

        def selection_get(model_self):
            return self.sqlalchemy_type.python_type(
                getattr(model_self, '_' + fieldname))

        def selection_set(model_self, value):
            val = self.sqlalchemy_type.python_type(value)
            if not val.validate():
                raise FieldException('%r is not in the selections (%s)' % (
                    value, ', '.join(val.get_selections())))

            setattr(model_self, '_' + fieldname, value)

        def selection_expression(model_self):
            return getattr(model_self, '_' + fieldname)

        properties[fieldname] = hybrid_property(
            selection_get, selection_set, expr=selection_expression)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        self.sqlalchemy_type = SelectionType(
            self.selections, self.size, registry=registry, namespace=namespace)
        return super(Selection, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

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
    sqlalchemy_type = SA_LargeBinary


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
