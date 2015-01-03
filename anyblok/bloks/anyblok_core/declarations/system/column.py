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


@register(System)
class Column(Mixin.Field):

    autoincrement = Boolean(label="Auto increment")
    foreign_key = String()
    primary_key = Boolean()
    ctype = String(label="Type")
    unique = Boolean()
    nullable = Boolean()

    @classmethod
    def get_cname(self, field, cname):
        """ Return the real name of the column

        :param field: the instance of the column
        :param cname: Not use here
        :rtype: string of the real column name
        """
        return field.property.columns[0].name

    @classmethod
    def add_field(cls, cname, column, model, table):
        """ Insert a column definition

        :param cname: name of the column
        :param column: instance of the column
        :param model: namespace of the model
        :param table: name of the table of the model
        """
        c = column.property.columns[0]
        vals = dict(autoincrement=c.autoincrement,
                    code=table + '.' + cname,
                    model=model, name=cname,
                    foreign_key=c.info.get('foreign_key'),
                    label=c.info['label'],
                    nullable=c.nullable,
                    primary_key=c.primary_key,
                    ctype=str(c.type),
                    unique=c.unique)
        cls.insert(**vals)

    @classmethod
    def alter_field(cls, column, meta_column):
        """ Update an existing column

        :param column: instance of the Column model to update
        :param meta_column: instance of the SqlAlchemy column
        """
        c = meta_column.property.columns[0]
        for col in ('autoincrement', 'nullable', 'primary_key', 'unique'):
            if getattr(column, col) != getattr(c, col):
                setattr(column, col, getattr(c, col))

        for col in ('foreign_key', 'label'):
            if getattr(column, col) != c.info.get(col):
                setattr(column, col, c.info.get(col))

        ctype = str(c.type)
        if column.ctype != ctype:
            column.ctype = ctype
