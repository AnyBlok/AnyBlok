# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from io import StringIO
from csv import DictWriter


register = Declarations.register
IO = Declarations.Model.IO
Mixin = Declarations.Mixin
Many2One = Declarations.RelationShip.Many2One
String = Declarations.Column.String
Selection = Declarations.Column.Selection
ExporterException = Declarations.Exception.ExporterException


@register(ExporterException)
class CSVExporterException(Exception):
    """ Simple exception for exporter """


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
            'external_id': 'External ID',
        }

    def get_value_for(self, entry):

        def _rc_get_sub_entry(name, entry):
            Model = self.get_model(entry.__registry_name__)
            fields_description = Model.fields_description(fields=[name])
            if name not in fields_description:
                raise ExporterException.CSVExporterException(
                    "unknow field %r in exporter field %r" % (
                        name, self.name))

            fields_description = fields_description[name]
            if fields_description['type'] == 'Many2One':
                return getattr(entry, name)

            elif fields_description['primary_key']:
                return entry
            elif fields_description['model']:
                model = fields_description['model']
                Model = self.registry.get(model)
                pks = Model.get_primary_keys()
                if len(pks) == 1:
                    pks = {pks[0]: getattr(entry, name)}
                else:
                    raise Exception("Not implemented yet")

                return Model.from_primary_keys(**pks)

        def _rc_get_value(names, entry):
            if len(names) == 0:
                return self.registry.IO.Exporter.get_key_maping(entry)
            elif len(names) == 1:
                if self.mode == 'any':
                    return getattr(entry, names[0])

                return _rc_get_value(
                    names[1:], _rc_get_sub_entry(names[0], entry))
            else:
                return _rc_get_value(
                    names[1:], _rc_get_sub_entry(names[0], entry))

        return _rc_get_value(self.name.split('.'), entry)

    def format_header(self):
        if self.mode == 'any':
            return self.name
        else:
            return self.name + '/EXTERNAL_ID'


@register(IO.Exporter)
class CSV:

    def __init__(self, exporter):
        self.exporter = exporter

    @classmethod
    def insert(cls, delimiter=None, fields=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if 'model' in kwargs:
            if not isinstance(kwargs['model'], str):
                kwargs['model'] = kwargs['model'].__registry_name__

        if delimiter is not None:
            kwargs['csv_delimiter'] = delimiter

        exporter = cls.registry.IO.Exporter.insert(**kwargs)
        if fields:
            for field in fields:
                field['exporter'] = exporter

            cls.registry.IO.Exporter.Field.multi_insert(*fields)

        return exporter

    def get_header(self):
        return [field.format_header() for
                field in self.exporter.fields_to_export]

    def run(self, entries):
        csvfile = StringIO()
        writer = DictWriter(csvfile, fieldnames=self.get_header(),
                            delimiter=self.exporter.csv_delimiter,
                            quotechar=self.exporter.csv_quotechar)
        writer.writeheader()
        for entry in entries:
            writer.writerow({field.format_header(): field.get_value_for(entry)
                             for field in self.exporter.fields_to_export})

        csvfile.seek(0)
        return csvfile
