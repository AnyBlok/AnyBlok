# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase


class EventPlugin(ModelPluginBase):

    def __init__(self, registry):
        self.registry = registry
        if not hasattr(registry, 'events'):
            registry.events = {}

    def transform_base_attribute(self, attr, method, namespace, base,
                                 transformation_properties,
                                 new_type_properties):
        """ Find the event listener methods in the base to save the
        namespace and the method in the registry

        :param attr: attribute name
        :param method: method pointer of the attribute
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param new_type_properties: param to add in a new base if need
        """
        if not hasattr(method, 'is_an_event_listener'):
            return
        elif method.is_an_event_listener is True:
            model = method.model
            event = method.event
            events = self.registry.events
            if model not in events:
                events[model] = {event: []}
            elif event not in events[model]:
                events[model][event] = []

            val = (namespace, attr)
            ev = events[model][event]
            if val not in ev:
                ev.append(val)
