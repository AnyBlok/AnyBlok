# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


FieldException = Declarations.Exception.FieldException


@Declarations.register(Declarations.RelationShip)
class One2One(Declarations.RelationShip.Many2One):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2One(label="The relationship",
                                   model=Model.RemoteModel,
                                   remote_column="The remote column",
                                   column_name="The column which have the "
                                               "foreigh key",
                                   nullable=False,
                                   backref="themodels")

    If the remote_column are not define then, the system take the primary key
    of the remote model

    If the column doesn't exist, then the column will be create. Use the
    nullable option.
    If the name is not filled then the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_column: the column name on the remote model
    :param column_name: the column on the model which have the foreign key
    :param nullable: If the column_name is nullable
    :param backref: create the one2one link with this one2one
    """

    def __init__(self, **kwargs):
        super(One2One, self).__init__(**kwargs)

        if 'backref' not in kwargs:
            raise FieldException("backref is a required argument")

        if 'one2many' in kwargs:
            raise FieldException("Unknow argmument 'one2many'")

        self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option uselist = False

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        self.backref_properties.update({'uselist': False})
