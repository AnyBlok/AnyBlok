# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
register = Declarations.register
System = Declarations.Model.System
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean
Json = Declarations.Column.Json


@register(Mixin)
class Field:

    name = String(primary_key=True)
    code = String()
    model = String(primary_key=True)
    label = String()

    @classmethod
    def get_cname(self, field, cname):
        return cname

    @classmethod
    def add_field(cls, name, field, model, table):
        pass

    @classmethod
    def alter_field(cls, field, meta_field):
        pass


@register(System)  # noqa
class Field(Mixin.Field):

    info = Json()

    @classmethod
    def add_field(cls, rname, properties, model, table):
        """ Insert a field definition

        :param rname: name of the field
        :param properties: properties of the field
        :param model: namespace of the model
        :param table: name of the table of the model
        """
        vals = dict(code=table + '.' + rname, model=model, name=rname)
        vals.update(properties)
        cls.insert(**vals)

    @classmethod
    def alter_field(cls, field, properties):
        """ Update an existing field

        :param field: instance of the Field model to update
        :param properties: properties of the field
        """
        field.update(properties)
