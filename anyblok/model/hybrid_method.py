# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.ext.hybrid import hybrid_method

from .plugins import ModelPluginBase


class HybridMethodPlugin(ModelPluginBase):
    def initialisation_tranformation_properties(
        self, properties, transformation_properties
    ):
        """Initialise the transform properties: hybrid_method

        :param properties: the properties declared in the model
        :param new_type_properties: param to add in a new base if need
        """
        if "hybrid_method" not in transformation_properties:
            transformation_properties["hybrid_method"] = set()

    def transform_base(self, namespace, base, transformation_properties):
        if hasattr(base, "__declared_hybrid_method__"):
            s = transformation_properties["hybrid_method"].union(
                base.__declared_hybrid_method__
            )
            transformation_properties["hybrid_method"] = s

    def after_model_construction(
        self, base, namespace, transformation_properties
    ):
        def apply_wrapper(attr):
            def wrapper(self, *args, **kwargs):
                if self is base:
                    return getattr(super(base, self), attr)(
                        self, *args, **kwargs
                    )
                elif hasattr(self, "_aliased_insp"):
                    return getattr(
                        super(base, self._aliased_insp._target), attr
                    )(self, *args, **kwargs)
                else:
                    return getattr(super(base, self), attr)(*args, **kwargs)

            setattr(base, attr, hybrid_method(wrapper))

        if transformation_properties["hybrid_method"]:
            for attr in transformation_properties["hybrid_method"]:
                apply_wrapper(attr)
