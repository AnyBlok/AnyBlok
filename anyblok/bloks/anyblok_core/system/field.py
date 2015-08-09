# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import String
from sqlalchemy import ForeignKeyConstraint


register = Declarations.register
System = Declarations.Model.System
Mixin = Declarations.Mixin


@register(System)  # noqa
class Field:

    name = String(primary_key=True)
    code = String(nullable=True)
    model = String(primary_key=True)
    # FIXME, foreign_key=System.Model.use('name'))
    label = String()
    ftype = String(label="Type", nullable=True)
    entity_type = String(nullable=True)

    @classmethod
    def define_table_args(cls):
        table_args = super(Field, cls).define_table_args()
        if cls.__registry_name__ != System.Field.__registry_name__:
            F = cls.registry.System.Field
            return table_args + (ForeignKeyConstraint([cls.name, cls.model],
                                                      [F.name, F.model]),)

        return table_args

    @classmethod
    def define_mapper_args(cls):
        mapper_args = super(Field, cls).define_mapper_args()
        if cls.__registry_name__ == System.Field.__registry_name__:
            mapper_args.update({
                'polymorphic_identity': cls.__registry_name__,
                'polymorphic_on': cls.entity_type,
            })
        else:
            mapper_args.update({
                'polymorphic_identity': cls.__registry_name__,
            })
        return mapper_args

    @classmethod
    def get_cname(self, field, cname):
        return cname

    def _description(self):
        return {
            'id': self.name,
            'label': self.label,
            'type': self.ftype,
            'nullable': True,
            'primary_key': False,
            'model': None,
        }

    @classmethod
    def add_field(cls, rname, label, model, table, ftype):
        """ Insert a field definition

        :param rname: name of the field
        :param label: label of the field
        :param model: namespace of the model
        :param table: name of the table of the model
        :param ftype: type of the AnyBlok Field
        """
        cls.insert(code=table + '.' + rname, model=model, name=rname,
                   label=label, ftype=ftype)

    @classmethod
    def alter_field(cls, field, label, ftype):
        """ Update an existing field

        :param field: instance of the Field model to update
        :param label: label of the field
        :param ftype: type of the AnyBlok Field
        """
        field.update({'label': label, 'ftype': ftype})
