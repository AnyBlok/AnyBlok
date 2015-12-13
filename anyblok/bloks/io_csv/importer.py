# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import Selection
from csv import DictReader
from io import StringIO
from .exceptions import CSVImporterException


register = Declarations.register
Mixin = Declarations.Mixin
IO = Declarations.Model.IO


@register(IO)
class Importer(Mixin.IOCSVMixin):

    csv_on_error = Selection(
        selections=[('raise_now', 'Raise now'),
                    ('raise_at_the_end', 'Raise at the end'),
                    ('ignore', 'Ignore and continue')],
        default='raise_at_the_end')
    csv_if_exist = Selection(selections=[('pass', 'Pass to the next record'),
                                         ('overwrite', 'Update the record'),
                                         ('create', 'Create another record'),
                                         ('raise', 'Raise an exception')],
                             default='overwrite')
    csv_if_does_not_exist = Selection(selections=[
        ('pass', 'Pass to the next record'),
        ('create', 'Create the record'),
        ('raise', 'Raise an exception')], default='create')

    @classmethod
    def get_mode_choices(cls):
        res = super(Importer, cls).get_mode_choices()
        res.update({'Model.IO.Importer.CSV': 'CSV'})
        return res


@register(IO.Importer)
class CSV:

    def __init__(self, importer):
        self.importer = importer
        self.error_found = []
        self.reader = None
        self.created_entries = []
        self.updated_entries = []
        self.header_pks = []
        self.header_external_id = None
        self.header_external_ids = {}
        self.header_fields = []
        self.fields_description = {}

    def commit(self):
        if self.error_found:
            return False

        self.importer.offset = self.reader.line_num - 1
        self.importer.commit()
        return True

    def get_reader(self):
        csvfile = StringIO()
        csvfile.write(self.importer.file_to_import.decode('utf-8'))
        csvfile.seek(0)
        self.reader = DictReader(csvfile,
                                 delimiter=self.importer.csv_delimiter,
                                 quotechar=self.importer.csv_quotechar)

    def consume_offset(self):
        try:
            for offset in range(self.importer.offset):
                next(self.reader)
        except StopIteration:
            pass

    def consume_nb_grouped_lines(self):
        res = []
        try:
            for offset in range(self.importer.nb_grouped_lines):
                res.append(next(self.reader))
        except StopIteration:
            pass

        return res

    def get_header(self):
        headers = self.reader.fieldnames
        Model = self.registry.get(self.importer.model)
        self.fields_description = Model.fields_description(
            fields=[h.split('/')[0] for h in headers])

        for header in headers:
            if '/' in header:
                name = header.split('/')[0]
                external_id = True
            else:
                name = header
                external_id = False

            if external_id:
                if not name or self.fields_description[name]['primary_key']:
                    self.header_external_id = header
                else:
                    self.header_external_ids[header] = name
            else:
                if self.fields_description[name]['primary_key']:
                    self.header_pks.append(header)
                else:
                    self.header_fields.append(name)

    def _parse_row_if_entry(self, row, entry, values, Model):
        if self.importer.csv_if_exist == 'overwrite':
            entry.update(values)
            self.updated_entries.append(entry)
        elif self.importer.csv_if_exist == 'create':
            entry = Model.insert(**values)
            self.created_entries.append(entry)
        elif self.importer.csv_if_exist == 'raise':
            raise CSVImporterException(
                "Row %r already an entry %r " % (
                    row, entry.to_primary_keys()))

    def _parse_row_if_not_entry(self, row, pks, values, Model):
        Mapping = self.registry.IO.Mapping
        if self.importer.csv_if_does_not_exist == 'create':
            if pks:
                values.update(pks)

            entry = Model.insert(**values)
            self.created_entries.append(entry)
            if self.header_external_id:
                Mapping.set(row[self.header_external_id], entry)

        elif self.importer.csv_if_does_not_exist == 'raise':
            raise CSVImporterException(
                "Create row are not allowed")

    def _parse_row(self, row, entry, pks, values, Model):
        if entry:
            self._parse_row_if_entry(row, entry, values, Model)
        else:
            self._parse_row_if_not_entry(row, pks, values, Model)

    def parse_row(self, row):
        try:
            entry = pks = None
            Model = self.registry.get(self.importer.model)
            values = {}
            for field in self.header_fields:
                ctype = self.fields_description[field]['type']
                values[field] = self.importer.str2value(row[field], ctype)

            for external_field, field in self.header_external_ids.items():
                ctype = self.fields_description[field]['type']
                model = self.fields_description[field]['model']
                values[field] = self.importer.str2value(
                    row[external_field], ctype, external_id=True, model=model)

            if self.header_external_id:
                entry = self.importer.get_key_mapping(
                    row[self.header_external_id])
            elif self.header_pks:
                pks = {}
                for field in self.header_pks:
                    ctype = self.fields_description[field]['type']
                    pks[field] = self.importer.str2value(row[field], ctype)

                entry = Model.from_primary_keys(**pks)

            self._parse_row(row, entry, pks, values, Model)
        except Exception as e:
            msg = '%r: %r' % (e.__class__.__name__, e)
            self.error_found.append(msg)
            if self.importer.csv_on_error == 'raise_now':
                raise CSVImporterException(msg)

    def run(self):
        try:
            self.get_reader()
            self.get_header()
            self.consume_offset()
            while True:
                rows = self.consume_nb_grouped_lines()
                if not rows:
                    break

                for row in rows:
                    self.parse_row(row)

                self.commit()
        except Exception as e:
            msg = '%r: %r' % (e.__class__.__name__, e)
            self.error_found.append(msg)

        if self.error_found:
            if self.importer.csv_on_error == 'raise_at_the_end':
                msg = "Exception found : \n %s" % '\n'.join(self.error_found)
                raise CSVImporterException(msg)

        return {
            'error': self.error_found,
            'created_entries': self.created_entries,
            'updated_entries': self.updated_entries,
        }

    @classmethod
    def insert(cls, delimiter=None, quotechar=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if 'model' not in kwargs:
            raise CSVImporterException("The column 'model' is required")

        if not isinstance(kwargs['model'], str):
            kwargs['model'] = kwargs['model'].__registry_name__

        if delimiter is not None:
            kwargs['csv_delimiter'] = delimiter

        if quotechar is not None:
            kwargs['csv_quotechar'] = quotechar

        return cls.registry.IO.Importer.insert(**kwargs)
