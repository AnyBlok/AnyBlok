# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.relationship import Many2One
from anyblok.column import String, Selection
from io import StringIO
from csv import DictWriter
from .exceptions import CSVExporterException


register = Declarations.register
IO = Declarations.Model.IO
Mixin = Declarations.Mixin


@register(IO)
class Exporter(Mixin.IOCSVMixin):

    @classmethod
    def get_mode_choices(cls):
        res = super(Exporter, cls).get_mode_choices()
        res.update({'Model.IO.Exporter.CSV': 'CSV'})
        return res


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

    def _get_fields_description(self, name, entry):
        Model = self.get_model(entry.__registry_name__)
        fields_description = Model.fields_description(fields=[name])
        if name not in fields_description:
            raise CSVExporterException(
                "unknow field %r in exporter field %r" % (
                    name, self.name))

        return fields_description[name]

    def _value2str(self, exporter, name, entry, external_id):
        fields_description = self._get_fields_description(name, entry)
        if fields_description['primary_key'] and external_id:
            return self.registry.IO.Exporter.get_key_mapping(entry)

        ctype = fields_description['type']
        model = fields_description['model']
        return exporter.value2str(getattr(entry, name), ctype,
                                  external_id=external_id, model=model)

    def _rc_get_sub_entry(self, name, entry):
        fields_description = self._get_fields_description(name, entry)
        if fields_description['type'] in ('Many2One', 'One2One'):
            return getattr(entry, name)

        elif fields_description['model']:
            model = fields_description['model']
            Model = self.registry.get(model)
            pks = Model.get_primary_keys()
            if len(pks) == 1:
                pks = {pks[0]: getattr(entry, name)}
            else:
                raise CSVExporterException(
                    "Not implemented yet")

            return Model.from_primary_keys(**pks)

        else:
            raise CSVExporterException(
                "the field %r of %r is not in (Many2One, One2One) "
                "or has not a foreign key")

    def value2str(self, exporter, entry):

        def _rc_get_value(names, entry):
            if not names:
                return ''
            elif len(names) == 1:
                external_id = False if self.mode == 'any' else True
                return self._value2str(exporter, names[0], entry, external_id)
            else:
                return _rc_get_value(
                    names[1:], self._rc_get_sub_entry(names[0], entry))

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
    def insert(cls, delimiter=None, quotechar=None, fields=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if 'model' in kwargs:
            if not isinstance(kwargs['model'], str):
                kwargs['model'] = kwargs['model'].__registry_name__

        if delimiter is not None:
            kwargs['csv_delimiter'] = delimiter

        if quotechar is not None:
            kwargs['csv_quotechar'] = quotechar

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
            writer.writerow(
                {field.format_header(): field.value2str(self.exporter, entry)
                 for field in self.exporter.fields_to_export})

        csvfile.seek(0)
        return csvfile
