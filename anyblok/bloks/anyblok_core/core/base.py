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
        events = cls.anyblok.events
        if cls.__registry_name__ in events:
            if event in events[cls.__registry_name__]:
                for model, method in events[cls.__registry_name__][event]:
                    m = cls.anyblok.get(model)
                    getattr(m, method)(*args, **kwargs)

    @classmethod
    def get_model(cls, model):
        return cls.anyblok.get(model)

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
        return self.anyblok.check_permission(self, principals, permission)

    @classmethod
    def has_model_perm(cls, principals, permission):
        """Check that one of principals has permission on given model.

        Since this is a classmethod, even if called on a record, only its
        model class will be considered for the permission check.
        """
        return cls.anyblok.check_permission(cls, principals, permission)

    @classmethod
    def precommit_hook(cls, method, *args, **kwargs):
        """ Same in the registry a hook to call just before the commit

        .. warning::

            Only one instance with same parameters of the hook is called before
            the commit

        :param method: the method to call on this model
        :param put_at_the_end_if_exist: If ``True`` the hook is move at the end
        """
        cls.anyblok.precommit_hook(
            cls.__registry_name__, method, *args, **kwargs)

    @classmethod
    def postcommit_hook(cls, method, *args, **kwargs):
        """ Same in the registry a hook to call just after the commit

        you can choice if the hook is called in function of ``call_only_if``:

        * ``commited``: Call if the commit is done without exception
        * ``raised``: Call if one exception was raised
        * ``always``: Always call

        .. warning::

            Only one instance with same paramters of the hook is called
            after the commit

        :param method: the method to call on this model
        :param put_at_the_end_if_exist: If ``True`` the hook is move at the end
        :param call_only_if: ['commited' (default), 'raised', 'always']
        """
        cls.anyblok.postcommit_hook(
            cls.__registry_name__, method, *args, **kwargs)
