# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.mapper import ModelAttribute, ModelMapper

from .plugins import ModelPluginBase


class ORMEventException(Exception):
    pass


class EventPlugin(ModelPluginBase):
    def __init__(self, registry):
        if not hasattr(registry, "events"):
            registry.events = {}

        super(EventPlugin, self).__init__(registry)

    def transform_base(
        self,
        namespace,
        base,
        transformation_properties,
    ):
        if hasattr(base, "__declared_events__"):
            events = self.registry.events
            for mapper, attr in base.__declared_events__:
                model = mapper.model.model_name
                event = mapper.event

                ev1 = events.setdefault(model, {})
                ev2 = ev1.setdefault(event, [])

                val = (namespace, attr)
                if val not in ev2:
                    ev2.append(val)


class SQLAlchemyEventPlugin(ModelPluginBase):
    def transform_base(
        self,
        namespace,
        base,
        transformation_properties,
    ):
        if hasattr(base, "__declared_sqlalchemy_events__"):
            for mapper, attr in base.__declared_sqlalchemy_events__:
                self.registry._sqlalchemy_known_events.append(
                    (
                        mapper,
                        namespace,
                        ModelAttribute(namespace, attr),
                    )
                )


class AutoSQLAlchemyORMEventPlugin(ModelPluginBase):
    def after_model_construction(
        self, base, namespace, transformation_properties
    ):
        for eventtype in (
            "before_insert",
            "after_insert",
            "before_update",
            "after_update",
            "before_delete",
            "after_delete",
        ):
            attr = eventtype + "_orm_event"
            if hasattr(base, attr):
                if not hasattr(getattr(base, attr), "__self__"):
                    raise ORMEventException(
                        "On %s %s is not a classmethod" % (base, attr)
                    )

                self.registry._sqlalchemy_known_events.append(
                    (
                        ModelMapper(base, eventtype),
                        namespace,
                        ModelAttribute(namespace, attr),
                    )
                )
