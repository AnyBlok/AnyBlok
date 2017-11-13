# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase
from anyblok.column import DateTime
from anyblok.mapper import ModelMapper
from datetime import datetime


class AutoUpdatePlugin(ModelPluginBase):

    def initialisation_tranformation_properties(self, properties,
                                                transformation_properties):
        """ Initialise the transform properties: auto_update_field_datetime

        :param properties: the properties declared in the model
        :param new_type_properties: param to add in a new base if need
        """
        if 'auto_update_field_datetime' not in transformation_properties:
            transformation_properties['auto_update_field_datetime'] = []

    def declare_field(self, name, field, namespace, properties,
                      transformation_properties):
        """Detect if the field is a DateTime with auto_update = True

        :param name: field name
        :param field: field instance
        :param namespace: the namespace of the model
        :param properties: the properties of the model
        :param transformation_properties: the transformation properties
        """
        f = self.registry.loaded_namespaces_first_step[namespace].get(name)
        if f and isinstance(f, DateTime) and f.auto_update:
            transformation_properties['auto_update_field_datetime'].append(
                name)

    def after_model_construction(self, base, namespace,
                                 transformation_properties):
        """Add the sqlalchemy event

        :param base: the Model class
        :param namespace: the namespace of the model
        :param transformation_properties: the properties of the model
        """
        if transformation_properties['auto_update_field_datetime']:
            e = ModelMapper(namespace, 'after_update')
            fields = transformation_properties['auto_update_field_datetime']

            def auto_update_listen(mapper, connection, target):
                now = datetime.now()
                for field in fields:
                    setattr(target, field, now)

            self.registry._sqlalchemy_known_events.append(
                (e, namespace, auto_update_listen))
