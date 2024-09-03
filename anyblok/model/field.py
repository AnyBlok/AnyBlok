# This file is a part of the AnyBlok project
#
#    Copyright (C) 2024 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

from .plugins import ModelPluginBase


class FieldPlugin(ModelPluginBase):
    def initialize_properties(self, properties):
        properties.update(
            {
                "fields": {},
                "columns": {},
                "relationships": {},
            }
        )

    def merge_properties(self, properties, base_properties):
        for key in ("fields", "columns", "relationships"):
            declared_key = f"__declared_{key}__"
            if key in base_properties:
                properties[key].update(base_properties[key])
            elif declared_key in base_properties:
                properties[key].update(base_properties[declared_key])

    def initialisation_tranformation_properties(
        self, properties, transformation_properties
    ):
        if "__declared_fields__" not in transformation_properties:
            transformation_properties.update(
                {
                    "__declared_fields__": {},
                    "__declared_columns__": {},
                    "__declared_relationships__": {},
                }
            )

    def transform_base(self, namespace, base, transformation_properties):
        for key in (
            "__declared_fields__",
            "__declared_columns__",
            "__declared_relationships__",
        ):
            transformation_properties[key].update(base.__dict__.get(key, {}))
