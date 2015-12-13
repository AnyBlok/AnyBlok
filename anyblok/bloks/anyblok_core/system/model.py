# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.declarations import Declarations, listen
from anyblok.field import Function
from anyblok.column import String, Boolean
from logging import getLogger

logger = getLogger(__name__)

register = Declarations.register
System = Declarations.Model.System


@register(System)
class Model:
    """Models assembled"""

    def __str__(self):
        if self.description:
            return self.description

        return self.name

    name = String(size=256, primary_key=True)
    table = String(size=256)
    is_sql_model = Boolean(label="Is a SQL model")
    description = Function(fget='get_model_doc_string')

    def get_model_doc_string(self):
        """ Return the docstring of the model
        """
        m = self.registry.get(self.name)
        if hasattr(m, '__doc__'):
            return m.__doc__ or ''

        return ''

    @listen('Model.System.Model', 'Update Model')
    def listener_update_model(cls, model):
        cls.registry.System.Cache.invalidate(model, '_fields_description')

    @classmethod
    def get_field_model(cls, field):
        ftype = field.property.__class__.__name__
        if ftype == 'ColumnProperty':
            return cls.registry.System.Column
        elif ftype == 'RelationshipProperty':
            return cls.registry.System.RelationShip
        else:
            raise Exception('Not implemented yet')

    @classmethod
    def get_field(cls, model, cname):
        if cname in model.loaded_fields.keys():
            field = model.loaded_fields[cname]
            Field = cls.registry.System.Field
        else:
            field = getattr(model, cname)
            Field = cls.get_field_model(field)

        return field, Field

    @classmethod
    def update_fields(cls, model, table):
        fsp = cls.registry.loaded_namespaces_first_step
        m = cls.registry.get(model)
        for cname in m.loaded_columns:
            ftype = fsp[model][cname].__class__.__name__
            field, Field = cls.get_field(m, cname)
            cname = Field.get_cname(field, cname)
            query = Field.query()
            query = query.filter(Field.model == model)
            query = query.filter(Field.name == cname)
            if query.count():
                Field.alter_field(query.first(), field, ftype)
            else:
                Field.add_field(cname, field, model, table, ftype)

    @classmethod
    def add_fields(cls, model, table):
        fsp = cls.registry.loaded_namespaces_first_step
        m = cls.registry.get(model)
        is_sql_model = len(m.loaded_columns) > 0
        cls.insert(name=model, table=table,
                   is_sql_model=is_sql_model)
        for cname in m.loaded_columns:
            field, Field = cls.get_field(m, cname)
            cname = Field.get_cname(field, cname)
            ftype = fsp[model][cname].__class__.__name__
            Field.add_field(cname, field, model, table, ftype)

    @classmethod
    def update_list(cls):
        """ Insert and update the table of models

        :exception: Exception
        """
        for model in cls.registry.loaded_namespaces.keys():
            try:
                # TODO need refactor, then try except pass whenever refactor
                # not apply
                m = cls.registry.get(model)
                table = ''
                if hasattr(m, '__tablename__'):
                    table = m.__tablename__

                _m = cls.query('name').filter(cls.name == model)
                if _m.count():
                    cls.update_fields(model, table)
                else:
                    cls.add_fields(model, table)

                if m.loaded_columns:
                    cls.fire('Update Model', model)

            except Exception as e:
                logger.error(str(e))
