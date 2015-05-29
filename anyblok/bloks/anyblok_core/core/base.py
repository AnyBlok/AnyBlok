# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from ..exceptions import CoreBaseException
register = Declarations.register


@register(Declarations.Core)
class Base:
    """ Inherited by all the models
    """

    is_sql = False

    @classmethod
    def initialize_model(cls):
        """ This method is called to initialize a model during the creation of
        the registry
        """
        pass

    @classmethod
    def fire(cls, event, *args, **kwargs):
        """ Call a specific event on the model

        :param event: Name of the event
        """
        events = cls.registry.events
        if cls.__registry_name__ in events:
            if event in events[cls.__registry_name__]:
                for model, method in events[cls.__registry_name__][event]:
                    m = cls.registry.get(model)
                    getattr(m, method)(*args, **kwargs)

    @classmethod
    def get_model(cls, model):
        return cls.registry.get(model)

    @classmethod
    def get_primary_keys(cls, **pks):
        """ No SQL Model has not primary key """
        raise CoreBaseException("No primary key for No SQL Model")

    @classmethod
    def from_primary_keys(cls, **pks):
        """ No SQL Model has not primary key """
        raise CoreBaseException("No primary key for No SQL Model")

    def to_primary_keys(self):
        """ No SQL Model has not primary key """
        raise CoreBaseException("No primary key for No SQL Model")

    def has_perm(self, principals, permission):
        """Check that one of principals has permission on given record.

        Since this is an ordinary instance method, it can't be used on the
        model class itself. For this use case, see :meth:`has_model_perm`
        """
        return self.registry.check_permission(self, principals, permission)

    @classmethod
    def has_model_perm(cls, principals, permission):
        """Check that one of principals has permission on given model.

        Since this is a classmethod, even if called on a record, only its
        model class will be considered for the permission check.
        """
        return cls.registry.check_permission(cls, principals, permission)
