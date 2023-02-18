# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.ext.hybrid import hybrid_property
from anyblok.common import anyblok_column_prefix
from anyblok.mapper import ModelRepr


class FieldException(Exception):
    """ Simple Exception for Field """


class Field:
    """ Field class

    This class must not be instanciated
    """

    use_hybrid_property = False

    def __init__(self, *args, **kwargs):
        """ Initialize the field

        :param label: label of this field
        :type label: str
        """
        self.forbid_instance(Field)
        self.label = None
        self.ignore_migration = kwargs.pop('ignore_migration', False)

        if 'label' in kwargs:
            self.label = kwargs.pop('label')

        self.context = kwargs.pop('context', {})
        self.args = args
        self.kwargs = kwargs

    def forbid_instance(self, cls):
        """ Raise an exception if the cls is an instance of this __class__

        :param cls: instance of the class
        :exception: FieldException
        """
        if self.__class__ is cls:
            raise FieldException(
                "%r class must not be instanciated use a sub class" % cls)

    def update_description(self, registry, model, res):
        res.update(self.context)

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Update the propertie use to add new column

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """
        if self.ignore_migration:
            table = registry.loaded_namespaces_first_step[
                namespace]['__tablename__']
            ignore_migration_for = registry.ignore_migration_for.get(table)
            if ignore_migration_for is True:
                return  # pragma: no cover
            elif not ignore_migration_for:
                registry.ignore_migration_for[table] = [fieldname]
            else:
                ignore_migration_for.append(fieldname)  # pragma: no cover

    def get_property(self, registry, namespace, fieldname, properties):
        """Return the property of the field

        .. warning::

            In the case of the get is called in classattribute,
            SQLAlchemy wrap for each call the column, the id of the wrapper
            is not the same

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """
        fget = self.wrap_getter_column(fieldname)
        fset = self.wrap_setter_column(fieldname)
        fexp = self.wrap_expr_column(fieldname)

        for func in (fget, fset, fexp):
            func.__name__ = fieldname

        hybrid = hybrid_property(fget)
        hybrid = hybrid.setter(fset)
        hybrid = hybrid.expression(fexp)
        return hybrid

    def getter_format_value(self, value):
        return value

    def wrap_getter_column(self, fieldname):
        """Return a default getter for the field

        :param fieldname: name of the field
        """
        attr_name = anyblok_column_prefix + fieldname

        def getter_column(model_self):
            return self.getter_format_value(getattr(model_self, attr_name))

        return getter_column

    def wrap_expr_column(self, fieldname):
        """Return a default expr for the field

        :param fieldname: name of the field
        """
        attr_name = anyblok_column_prefix + fieldname

        def expr_column(model_self):
            return getattr(model_self, attr_name)

        return expr_column

    def expire_related_attribute(self, model_self, action_todos):
        for action_todo in action_todos:
            if len(action_todo) == 1:
                obj = model_self
                attrs = [action_todo[0]]
            else:
                obj = getattr(model_self, action_todo[0])
                attrs = [action_todo[1]]
                if obj is None:
                    continue

            if obj in model_self.anyblok.session:
                if obj._sa_instance_state.persistent:
                    model_self.anyblok.expire(obj, attrs)

    def setter_format_value(self, value):
        return value

    def wrap_setter_column(self, fieldname):
        attr_name = anyblok_column_prefix + fieldname

        def setter_column(model_self, value):
            action_todos = set()
            if fieldname in model_self.loaded_columns:
                action_todos = model_self.anyblok.expire_attributes.get(
                    model_self.__registry_name__, {}).get(fieldname, set())

            self.expire_related_attribute(model_self, action_todos)
            value = self.setter_format_value(value)
            res = setattr(model_self, attr_name, value)
            self.expire_related_attribute(model_self, action_todos)
            return res

        return setter_column

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: instance of Field
        """
        self.format_label(fieldname)
        return self

    def format_label(self, fieldname):
        """ Return the label for this field

        :param fieldname: if no label filled, the fieldname will be capitalized
            and returned
        :rtype: the label for this field
        """
        if not self.label:
            label = fieldname.replace('_', ' ')
            self.label = label.capitalize()

    def native_type(self, registry):
        """ Return the native SqlAlchemy type

        :exception: FieldException
        """
        raise FieldException(
            "No native type for this field")  # pragma: no cover

    def must_be_declared_as_attr(self):
        """ Return False, it is the default value """
        return False

    def must_be_copied_before_declaration(self):
        """ Return False, it is the default value """
        return False

    def autodoc_get_properties(self):
        res = {'Type': self.__class__}
        res['Context'] = self.context
        res['Label'] = self.label
        res.update(self.kwargs)
        return res

    autodoc_omit_property_values = set((
        ('Label', None),
        ('Context', None),
        ))

    def autodoc_format_dict(self, key, value, level=0):
        bullets = ['*', '+', '•', '‣']
        bullet = bullets[level]
        padding = '  ' * level
        key = key.strip()
        if isinstance(value, dict):  # pragma: no cover
            res = padding + '%c ``%s``:\n\n' % (bullet, key)
            res += '\n'.join(
                [self.autodoc_format_dict(x, y, level=level + 1)
                 for x, y in value.items()])
            res += '\n'
            return res
        elif isinstance(value, (list, tuple)):  # pragma: no cover
            res = padding + '%c ``%s``:\n\n' % (bullet, key)
            next_bullet = bullets[level + 1]
            res += '\n'.join(padding + '  %c ``%r``' % (next_bullet, x)
                             for x in value)
            res += '\n'
            return res
        else:
            if isinstance(value, type):
                rst_val = ':class:`%s.%s`' % (value.__module__,
                                              value.__name__)
            elif isinstance(value, ModelRepr):  # pragma: no cover
                rst_val = value.model_name
            else:
                rst_val = '``%r``' % value
            return padding + '%c ``%s`` - %s' % (bullet, key, rst_val)

    def autodoc_do_omit(self, k, v):
        """Maybe convert, then check in :attr:`autodoc_omit_property_values`

        Mutable types aren't hashable, and usually, if not empty, it makes
        sense to display them. Therefore, we replace them by None if
        empty to decide and let through otherwise.

        Hence, to exclude empty Context from autodoc, is done by putting
        ``('Context', None)`` in :attr:`autodoc_omit_property_values`
        """
        if isinstance(v, list) or isinstance(v, dict) or isinstance(v, set):
            if v:
                return True
            v = None
        return (k, v) in self.autodoc_omit_property_values

    def autodoc(self):
        return '\n'.join(self.autodoc_format_dict(x, y)
                         for x, y in self.autodoc_get_properties().items()
                         if not self.autodoc_do_omit(x, y))


class Function(Field):
    """ Function Field

    ::

        from anyblok.declarations import Declarations
        from anyblok.field import Function


        @Declarations.register(Declarations.Model)
        class Test:
            x = Function(fget='fget', fset='fset', fdel='fdel', fexp='fexpr')

        ..warning::

            fexp must be a classmethod

    """

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """Return the property of the field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """

        def wrap(method):
            m = self.kwargs.get(method)
            if m is None:
                return None

            def function_method(model_self, *args, **kwargs):
                if method == 'fget':
                    cls = registry.get(model_self.__registry_name__)
                    if model_self is cls:
                        return hasattr(model_self, m)

                return getattr(model_self, m)(*args, **kwargs)

            function_method.__name__ = fieldname
            return function_method

        fget = wrap('fget')
        fset = wrap('fset')
        fdel = wrap('fdel')
        fexpr = wrap('fexpr')

        hybrid = hybrid_property(fget)
        hybrid = hybrid.setter(fset)
        hybrid = hybrid.deleter(fdel)
        hybrid = hybrid.expression(fexpr)

        self.format_label(fieldname)
        properties['loaded_fields'][fieldname] = self.label
        return hybrid


def format_struc(entry, keys):
    key = keys[0]
    if len(keys) == 1:
        if key not in entry:
            entry[key] = None
    else:
        if key not in entry:
            entry[key] = {}

        format_struc(entry[key], keys[1:])


class JsonRelated(Field):
    """ Json Related Field

    ::

        from anyblok.declarations import Declarations
        from anyblok.field import JsonRelated
        from anyblok.column import Json


        @Declarations.register(Declarations.Model)
        class Test:
            properties = Json()
            x = JsonRelated(json_column='properties', keys=['x'])

    """
    def __init__(self, *args, **kwargs):
        self.json_column = kwargs.pop('json_column', None)
        if self.json_column is None:
            raise FieldException(
                "json_column is a required attribute for "
                "JsonRelated"
            )
        self.keys = kwargs.pop('keys', None)
        if self.keys is None:
            raise FieldException(
                "keys is a required attribute for JsonRelated"
            )
        self.get_adapter = kwargs.pop('get_adapter', None)
        self.set_adapter = kwargs.pop('set_adapter', None)
        super(JsonRelated, self).__init__(*args, **kwargs)

    def get_fget(self):
        def fget(model_self):
            json_column = getattr(model_self, self.json_column)
            if json_column is None:
                json_column = {}

            format_struc(json_column, self.keys)
            entry = json_column
            for key in self.keys:
                entry = entry[key]

            if entry and self.get_adapter:
                get_adapter = self.get_adapter
                if isinstance(get_adapter, str):
                    get_adapter = getattr(model_self, get_adapter)

                entry = get_adapter(entry)

            return entry

        return fget

    def get_fset(self):
        def fset(model_self, value):
            json_column = getattr(model_self, self.json_column)
            if json_column is None:
                json_column = {}

            format_struc(json_column, self.keys)
            entry = json_column
            for key in self.keys[:-1]:
                entry = entry[key]

            if value and self.set_adapter:
                set_adapter = self.set_adapter
                if isinstance(set_adapter, str):
                    set_adapter = getattr(model_self, set_adapter)

                value = set_adapter(value)

            entry[self.keys[-1]] = value
            setattr(model_self, self.json_column, json_column)

        return fset

    def get_fdel(self):
        def fdel(model_self):
            json_column = getattr(model_self, self.json_column)
            if json_column is None:
                json_column = {}

            format_struc(json_column, self.keys)
            entry = json_column
            for key in self.keys[:-1]:
                entry = entry[key]

            entry[self.keys[-1]] = None
            setattr(model_self, self.json_column, json_column)

        return fdel

    def get_fexpr(self):
        def fexpr(model_self):
            entry = getattr(model_self, self.json_column)
            for key in self.keys:
                entry = entry[key]

            return entry

        return fexpr

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """Return the property of the field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """
        self.format_label(fieldname)
        properties['loaded_fields'][fieldname] = self.label

        fget = self.get_fget()
        fset = self.get_fset()
        fdel = self.get_fdel()
        fexpr = self.get_fexpr()

        for func in (fget, fset, fdel, fexpr):
            func.__name__ = fieldname

        hybrid = hybrid_property(fget)
        hybrid = hybrid.setter(fset)
        hybrid = hybrid.deleter(fdel)
        hybrid = hybrid.expression(fexpr)
        return hybrid

    def autodoc_get_properties(self):
        res = super(JsonRelated, self).autodoc_get_properties()
        res.update({
            'json_column': self.json_column,
            'keys': ' -> '.join(self.keys),
        })
        return res
