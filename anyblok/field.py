# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.ext.hybrid import hybrid_property
from .mapper import ModelAttribute, ModelAttributeMapper


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

    def native_type(self):
        """ Return the native SqlAlchemy type

        :exception: FieldException
        """
        raise FieldException("No native type for this field")

    def must_be_declared_as_attr(self):
        """ Return False, it is the default value """
        return False

    def must_be_duplicate_before_added(self):
        """ Return False, it is the default value """
        return False

    def autodoc_get_properties(self):
        res = {'Field type': str(self.__class__),
               'Context': self.context,
               'Label': self.label}
        res.update(self.kwargs)
        return res

    def autodoc_format_dict(self, key, value, padding=0):
        key = key.strip()
        if isinstance(value, dict):
            res = ' * ``%s``:\n' % key
            res += '\n'.join(
                [self.autodoc_format_dict(x, y, padding=padding + 1)
                 for x, y in value.items()])
            res += '\n'
            return res
        elif isinstance(value, (list, tuple)):
            res = ' * ``%s``:\n' % key
            res += '\n'.join([' ' * padding + ' * %s' % str(x)
                              for x in value])
            res += '\n'
            return res
        else:
            return ' ' * padding + ' * ``%s`` - %s' % (key, str(value))

    def autodoc(self):
        return '\n'.join([self.autodoc_format_dict(x, y)
                          for x, y in self.autodoc_get_properties().items()])

    def add_field_event(self, registry, namespace, fieldname, event, method,
                        *args, **kwargs):
        attr = ModelAttribute(namespace, fieldname)
        mapper = ModelAttributeMapper(attr, event, *args, **kwargs)
        registry._sqlalchemy_field_events.append(
            (mapper, namespace, method))


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
                try:
                    return getattr(model_self, m)(*args, **kwargs)
                except TypeError:
                    if method == 'fget':
                        raise FieldException("You must declare 'fexp' for "
                                             "'%s: %s' field" % (namespace,
                                                                 fieldname))
                    else:
                        raise

            return function_method

        fget = wrap('fget')
        fset = wrap('fset')
        fdel = wrap('fdel')
        fexpr = wrap('fexpr')

        self.format_label(fieldname)
        properties['loaded_fields'][fieldname] = self.label
        return hybrid_property(fget, fset, fdel=fdel, expr=fexpr)
