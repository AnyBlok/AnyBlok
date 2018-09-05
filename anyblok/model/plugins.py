# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pkg_resources import iter_entry_points
from logging import getLogger

logger = getLogger(__name__)


def get_model_plugins(registry):
    res = []
    for i in iter_entry_points('anyblok.model.plugin'):
        logger.info('AnyBlok Load model plugin: %r' % i)
        res.append(i.load()(registry))

    return res


class ModelPluginBase:

    def __init__(self, registry):
        self.registry = registry

    # def initialisation_tranformation_properties(self, properties,
    #                                             transformation_properties):
    #     """ Initialise the transform properties

    #     :param properties: the properties declared in the model
    #     :param new_type_properties: param to add in a new base if need
    #     """

    # def declare_field(self, name, field, namespace, properties,
    #                   transformation_properties):
    #     """Declare a field in the model

    #     :param name: field name
    #     :param field: field instance
    #     :param namespace: the namespace of the model
    #     :param properties: the properties of the model
    #     :param transformation_properties: the transformation properties
    #     """

    # def transform_base_attribute(self, attr, method, namespace, base,
    #                              transformation_properties,
    #                              new_type_properties):
    #     """ transform the attribute for the final Model

    #     :param attr: attribute name
    #     :param method: method pointer of the attribute
    #     :param namespace: the namespace of the model
    #     :param base: One of the base of the model
    #     :param transformation_properties: the properties of the model
    #     :param new_type_properties: param to add in a new base if need
    #     """

    # def transform_base(self, namespace, base,
    #                    transformation_properties,
    #                    new_type_properties):
    #     """ transform the base for the final Model

    #     :param namespace: the namespace of the model
    #     :param base: One of the base of the model
    #     :param transformation_properties: the properties of the model
    #     :param new_type_properties: param to add in a new base if need
    #     """

    # def insert_in_bases(self, new_base, namespace, properties,
    #                     transformation_properties):
    #     """Insert in a base the overload

    #     :param new_base: the base to be put on front of all bases
    #     :param namespace: the namespace of the model
    #     :param properties: the properties declared in the model
    #     :param transformation_properties: the properties of the model
    #     """

    # def after_model_construction(self, base, namespace,
    #                              transformation_properties):
    #     """Do some action with the constructed Model

    #     :param base: the Model class
    #     :param namespace: the namespace of the model
    #     :param transformation_properties: the properties of the model
    #     """
