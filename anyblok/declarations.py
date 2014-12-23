# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.


class DeclarationsException(Exception):
    """ Simple Exception for Declarations """


class Declarations:
    """ Represente all the declarations done by the bloks

    .. warning::
        It is a global information, during the execution you must use the
        registry. The registry is the real assembler of the python classes
        in function of the installed bloks

    ::

        from anyblok import Declarations

    """
    declaration_types = {}

    @classmethod
    def target_registry(cls, parent, cls_=None, **kwargs):
        """ Method to add in a type of declaration

        :param parent: An existing anyblok class in the Declaration
        :param ``cls_``: The ``class`` object to add in the Declaration
        :rtype: ``cls_``
        :exception: DeclarationsException
        """

        def wrapper(self):
            name = kwargs.get('name_', self.__name__)
            if parent.__declaration_type__ not in cls.declaration_types:
                raise DeclarationsException(
                    "No parent %r for %s" % (parent, name))

            declaration = cls.declaration_types[parent.__declaration_type__]
            declaration.target_registry(parent, name, self, **kwargs)

            node = getattr(parent, name)
            setattr(node, '__declaration_type__', parent.__declaration_type__)
            setattr(node, '__registry_name__',
                    parent.__registry_name__ + '.' + name)

            return self

        if cls_:
            return wrapper(cls_)
        else:
            return wrapper

    @classmethod
    def remove_registry(cls, entry, cls_):
        """ Method to remove from a type of declaration

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param ``cls_``: The ``class`` object to remove from the
            Declaration
        :rtype: ``cls_``
        """
        declaration = cls.declaration_types[entry.__declaration_type__]
        declaration.remove_registry(entry, cls_)

        return cls_

    @classmethod
    def cache(cls, size=128):
        def wrapper(method):
            method.is_cache_method = True
            method.is_cache_classmethod = False
            method.size = size
            return method

        return wrapper

    @classmethod
    def classmethod_cache(cls, size=128):
        def wrapper(method):
            method.is_cache_method = True
            method.is_cache_classmethod = True
            method.size = size
            return method

        return wrapper

    @classmethod
    def addListener(cls, model, event):
        if not isinstance(model, str):
            model = model.__registry_name__

        def wrapper(method):
            method.is_an_event_listener = True
            method.model = model
            method.event = event
            return classmethod(method)

        return wrapper

    @classmethod
    def hybrid_method(cls, method=None):
        if method:
            method.is_an_hybrid_method = True
            return method
        else:

            def wrapper(method):
                method.is_an_hybrid_method = True
                return method

            return wrapper

    @classmethod
    def add_declaration_type(cls, cls_=None, isAnEntry=False,
                             assemble=None, initialize=None):
        """ Method to add a type of declaration

        :param cls_: The ``class`` object to add as a world of the MetaData
        :param isAnEntry: if true the type will be assembling by the registry
        :param assemble: name of the method callback to call (classmethod)
        :param initialize: name of the method callback to call (classmethod)
        :exception: DeclarationsException
        """

        def wrapper(self):
            name = self.__name__
            if name in cls.declaration_types:
                raise DeclarationsException(
                    "The declaration type %r are already defined" % name)

            cls.declaration_types[name] = self

            setattr(self, '__registry_name__', name)
            setattr(self, '__declaration_type__', name)
            setattr(cls, name, self)

            if isAnEntry:
                from anyblok.registry import RegistryManager

                assemble_callback = initialize_callback = None
                if assemble and hasattr(self, assemble):
                    assemble_callback = getattr(self, assemble)

                if initialize and hasattr(self, initialize):
                    initialize_callback = getattr(self, initialize)

                RegistryManager.declare_entry(
                    name, assemble_callback=assemble_callback,
                    initialize_callback=initialize_callback)

            return self

        if cls_:
            return wrapper(cls_)
        else:
            return wrapper
