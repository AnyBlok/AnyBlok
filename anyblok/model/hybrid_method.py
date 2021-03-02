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

    def initialisation_tranformation_properties(self, properties,
                                                transformation_properties):
        """ Initialise the transform properties: hybrid_method

        :param properties: the properties declared in the model
        :param new_type_properties: param to add in a new base if need
        """
        if 'hybrid_method' not in transformation_properties:
            transformation_properties['hybrid_method'] = []

    def transform_base_attribute(self, attr, method, namespace, base,
                                 transformation_properties,
                                 new_type_properties):
        """ Find the sqlalchemy hybrid methods in the base to save the
        namespace and the method in the registry

        :param attr: attribute name
        :param method: method pointer of the attribute
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param new_type_properties: param to add in a new base if need
        """
        if not hasattr(method, 'is_an_hybrid_method'):
            return
        elif method.is_an_hybrid_method is True:
            if attr not in transformation_properties['hybrid_method']:
                transformation_properties['hybrid_method'].append(attr)

    def insert_in_bases(self, new_base, namespace, properties,
                        transformation_properties):
        """ Create overload to define the write declaration of sqlalchemy
        hybrid method, add the overload in the declared bases of the
        namespace

        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        :param properties: the properties declared in the model
        :param transformation_properties: the properties of the model
        """
        type_properties = {}

        def apply_wrapper(attr):

            def wrapper(self, *args, **kwargs):
                self_ = self.anyblok.loaded_namespaces[self.__registry_name__]
                if self is self_:
                    return getattr(super(new_base, self), attr)(
                        self, *args, **kwargs)
                elif hasattr(self, '_aliased_insp'):
                    return getattr(super(new_base, self._aliased_insp._target),
                                   attr)(self, *args, **kwargs)
                else:
                    return getattr(super(new_base, self), attr)(
                        *args, **kwargs)

            setattr(new_base, attr, hybrid_method(wrapper))

        if transformation_properties['hybrid_method']:
            for attr in transformation_properties['hybrid_method']:
                apply_wrapper(attr)

        return type_properties
