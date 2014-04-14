class DeclarationsException(Exception):
    """ Simple Exception for MetaData """


class Declarations:
    """ Represente the ``Univers`` of all the data loaded by AnyBlok

    ::

        from anyblok import MetaData

    """

    current_blok = None

    declaration_types = {}

    @classmethod
    def target_registry(cls, parent, cls_=None, **kwargs):
        """ Method to add in a world of the MetaData

            :param parent: An existing AnyBlok class in the Declaration
            :param ``cls_``: The ``class`` object to add in the Declaration
            :rtype: ``cls_``
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
    def remove_registry(cls, parent, cls_, **kwargs):
        """ Method to remove from a world of the MetaData

            :param parent: An existing AnyBlok class in the Declaration
            :param ``cls_``: The ``class`` object to remove from the
                Declaration
            :rtype: ``cls_``
        """
        declaration = cls.declaration_types[parent.__declaration_type__]
        name = kwargs.get('name_', cls_.__name__)
        declaration.remove_registry(parent, name, cls_, **kwargs)

        return cls_

    @classmethod
    def add_declaration_type(cls, cls_=None, isAnEntry=False, mustbeload=False):
        """ Method to add a adapter

        :param cls_: The ``class`` object to add as a world of the MetaData
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

                callback = None
                if hasattr(self, 'mustbeload_callback'):
                    callback = getattr(self, 'mustbeload_callback')

                RegistryManager.declare_entry(name, mustbeload=mustbeload,
                                              callback=callback)

            return self

        if cls_:
            return wrapper(cls_)
        else:
            return wrapper
