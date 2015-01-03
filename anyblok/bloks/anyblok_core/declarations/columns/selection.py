# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy import types
from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.hybrid import hybrid_property


FieldException = Declarations.Exception.FieldException


class StrSelection(str):
    selections = {}
    registry = None
    namespace = None

    def get_selections(self):
        if isinstance(self.selections, dict):
            return self.selections
        if isinstance(self.selections, str):
            m = self.registry.loaded_namespaces[self.namespace]
            return dict(getattr(m, self.selections)())

    def validate(self):
        a = super(StrSelection, self).__str__()
        return a in self.get_selections().keys()

    @property
    def label(self):
        a = super(StrSelection, self).__str__()
        return self.get_selections()[a]


class SelectionType(types.UserDefinedType):

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


@Declarations.register(Declarations.Column)
class Selection(Declarations.Column):
    """ Selection column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Selection = Declarations.Column.Selection

        @register(Model)
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
                    value, ', '.join(val.selections)))

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
