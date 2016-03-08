# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import String, Boolean


register = Declarations.register
System = Declarations.Model.System
Mixin = Declarations.Mixin


@register(System)
class Column(System.Field):

    name = String(primary_key=True)
    model = String(primary_key=True)
    autoincrement = Boolean(label="Auto increment")
    foreign_key = String()
    primary_key = Boolean()
    unique = Boolean()
    nullable = Boolean()
    remote_model = String()

    def _description(self):
        res = super(Column, self)._description()
        res.update(nullable=self.nullable, primary_key=self.primary_key,
                   model=self.remote_model)
        return res

    @classmethod
    def get_cname(self, field, cname):
        """ Return the real name of the column

        :param field: the instance of the column
        :param cname: Not use here
        :rtype: string of the real column name
        """
        return cname

    @classmethod
    def add_field(cls, cname, column, model, table, ftype):
        """ Insert a column definition

        :param cname: name of the column
        :param column: instance of the column
        :param model: namespace of the model
        :param table: name of the table of the model
        :param ftype: type of the AnyBlok Field
        """
        c = column.property.columns[0]
        vals = dict(autoincrement=c.autoincrement,
                    code=table + '.' + cname,
                    model=model, name=cname,
                    foreign_key=c.info.get('foreign_key'),
                    label=c.info.get('label'),
                    nullable=c.nullable,
                    primary_key=c.primary_key,
                    ftype=ftype,
                    remote_model=c.info.get('remote_model'),
                    unique=c.unique)
        cls.insert(**vals)

    @classmethod
    def alter_field(cls, column, meta_column, ftype):
        """ Update an existing column

        :param column: instance of the Column model to update
        :param meta_column: instance of the SqlAlchemy column
        :param ftype: type of the AnyBlok Field
        """
        c = meta_column.property.columns[0]
        for col in ('autoincrement', 'nullable', 'primary_key', 'unique'):
            if getattr(column, col) != getattr(c, col):
                setattr(column, col, getattr(c, col))

        for col in ('foreign_key', 'label', 'remote_model'):
            if getattr(column, col) != c.info.get(col):
                setattr(column, col, c.info.get(col))

        if column.ftype != ftype:
            column.ftype = ftype
