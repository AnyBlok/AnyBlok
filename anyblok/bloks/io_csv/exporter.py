# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
register = Declarations.register
IO = Declarations.Model.IO
Mixin = Declarations.Mixin
Many2One = Declarations.RelationShip.Many2One
String = Declarations.Column.String
Selection = Declarations.Column.Selection


@register(IO)
class Exporter(Mixin.IOCSVMixin):
    pass


@register(IO.Exporter)
class Field(Mixin.IOCSVFieldMixin):

    exporter = Many2One(model=IO.Exporter, nullable=False,
                        one2many='fields_to_export')
    mode = Selection(selections='get_selection', nullable=False, default='any')
    mapping = String()

    @classmethod
    def get_selection(cls):
        return {
            'any': '',
            'simple': 'Simple',
            'counter': 'With counter',
        }


@register(IO.Exporter)
class CSV:

    def __init__(self, exporter):
        self.exporter = exporter

    @classmethod
    def insert(cls, model=None, delimiter=None, fields=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if model is not None:
            if isinstance(model, str):
                kwargs['csv_model'] = model
            else:
                kwargs['csv_model'] = model.__registry_name__

        if delimiter is not None:
            kwargs['csv_delimiter'] = delimiter

        exporter = cls.registry.IO.Exporter.insert(**kwargs)
        if fields:
            for field in fields:
                field['exporter'] = exporter

            cls.registry.IO.Exporter.Field.multi_insert(*fields)

        return exporter

    def get_header(self):
        res = []
        for field in self.exporter.fields_to_export:
            if field.mode == 'any':
                res.append(field.name)
            else:
                res.append(field.name + '/EXTERNAL_ID')

        return res
