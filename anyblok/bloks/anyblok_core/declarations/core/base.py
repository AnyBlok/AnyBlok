# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Core)
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
                    m = cls.registry.loaded_namespaces[model]
                    getattr(m, method)(*args, **kwargs)
