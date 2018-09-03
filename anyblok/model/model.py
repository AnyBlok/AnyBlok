# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase
from .common import has_sql_fields, MODEL


class ModelPlugin(ModelPluginBase):

    def insert_core_bases(self, bases, properties):
        if properties['__model_type__'] == MODEL:
            if has_sql_fields(bases):
                bases.extend(
                    [x for x in self.registry.loaded_cores['SqlBase']])
                bases.append(self.registry.declarativebase)
            else:
                # remove tablename to inherit from a sqlmodel
                del properties['__tablename__']

            bases.extend([x for x in self.registry.loaded_cores['Base']])

    def build_base(self, modelname, bases, properties):
        if properties['__model_type__'] == MODEL:
            return type(modelname, tuple(bases), properties)
