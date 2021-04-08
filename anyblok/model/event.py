# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase
from anyblok.mapper import ModelAttribute, ModelMapper


class ORMEventException(Exception):
    pass


class EventPlugin(ModelPluginBase):

    def __init__(self, registry):
        if not hasattr(registry, 'events'):
            registry.events = {}

        super(EventPlugin, self).__init__(registry)

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
                events[model][event] = []  # pragma: no cover

            val = (namespace, attr)
            ev = events[model][event]
            if val not in ev:
                ev.append(val)


class SQLAlchemyEventPlugin(ModelPluginBase):

    def transform_base_attribute(self, attr, method, namespace, base,
                                 transformation_properties,
                                 new_type_properties):
        """declare in the registry the sqlalchemy event

        :param attr: attribute name
        :param method: method pointer of the attribute
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param new_type_properties: param to add in a new base if need
        """
        if not hasattr(method, 'is_an_sqlalchemy_event_listener'):
            return
        elif method.is_an_sqlalchemy_event_listener is True:
            self.registry._sqlalchemy_known_events.append(
                (method.sqlalchemy_listener,
                 namespace,
                 ModelAttribute(namespace, attr)))


class AutoSQLAlchemyORMEventPlugin(ModelPluginBase):

    def after_model_construction(self, base, namespace,
                                 transformation_properties):
        for eventtype in ('before_insert', 'after_insert',
                          'before_update', 'after_update',
                          'before_delete', 'after_delete'):
            attr = eventtype + '_orm_event'
            if hasattr(base, attr):
                if not hasattr(getattr(base, attr), '__self__'):
                    raise ORMEventException(
                        "On %s %s is not a classmethod" % (base, attr))

                self.registry._sqlalchemy_known_events.append((
                    ModelMapper(base, eventtype), namespace,
                    ModelAttribute(namespace, attr)))
