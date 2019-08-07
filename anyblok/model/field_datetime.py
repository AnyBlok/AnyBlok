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

    def after_model_construction(self, base, namespace,
                                 transformation_properties):
        """Add the sqlalchemy event

        :param base: the Model class
        :param namespace: the namespace of the model
        :param transformation_properties: the properties of the model
        """
        namespaces = [namespace]
        namespaces.extend(list(base.__depends__))
        fields = []
        for ns in namespaces:
            for c in self.registry.get(ns).loaded_columns:
                f = self.registry.loaded_namespaces_first_step[namespace].get(c)
                if isinstance(f, DateTime) and f.auto_update:
                    # TimeStamp inherit of DateTime so it works too
                    fields.append(c)

        if fields:
            e = ModelMapper(namespace, 'after_update')

            def auto_update_listen(mapper, connection, target):
                now = datetime.now()
                for field in fields:
                    setattr(target, field, now)

            self.registry._sqlalchemy_known_events.append(
                (e, namespace, auto_update_listen))
