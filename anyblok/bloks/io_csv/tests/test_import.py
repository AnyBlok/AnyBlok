# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase
from ..exceptions import CSVImporterException
from os import urandom
from csv import DictReader
from io import StringIO


class TestImportCSV(BlokTestCase):

    def create_importer(self, file_to_import=None, **kwargs):
        CSV = self.registry.IO.Importer.CSV
        if 'model' not in kwargs:
            kwargs['model'] = 'Model.IO.Importer'

        if file_to_import is None:
            file_to_import = urandom(100000)
        return CSV.insert(file_to_import=file_to_import, **kwargs)

    def create_csv_importer(self, **kwargs):
        CSV = self.registry.IO.Importer.CSV
        return CSV(self.create_importer(**kwargs))

    def get_file_to_import(self):
        return '''"A","B","C"\n"1","2","3"\n"4","5","6"'''.encode('utf-8')

    def test_commit_if_error_found(self):
        importer = self.create_csv_importer()
        importer.error_found.append('Mock error')
        self.assertEqual(importer.commit(), False)

    def test_commit(self):
        importer = self.create_csv_importer()
        csvfile = StringIO()
        importer.reader = DictReader(csvfile)
        self.assertEqual(importer.commit(), True)

    def test_get_reader(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        self.assertEqual(isinstance(importer.reader, DictReader), True)

    def assertNbLines(self, importer, nb_line_wanted):
        rows = [row for row in importer.reader]
        self.assertEqual(len(rows), nb_line_wanted)

    def test_consume_without_offset(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        importer.consume_offset()
        self.assertNbLines(importer, 2)

    def test_consume_offset(self):
        importer = self.create_csv_importer(
            offset=1,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        importer.consume_offset()
        self.assertNbLines(importer, 1)

    def test_consume_offset_equal(self):
        importer = self.create_csv_importer(
            offset=2,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        importer.consume_offset()
        self.assertNbLines(importer, 0)

    def test_consume_offset_greater_than_nb_lines(self):
        importer = self.create_csv_importer(
            offset=3,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        importer.consume_offset()
        self.assertNbLines(importer, 0)

    def test_consume_nb_grouped_lines(self):
        importer = self.create_csv_importer(
            nb_grouped_lines=1,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        rows = importer.consume_nb_grouped_lines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {'A': '1', 'B': '2', 'C': '3'})
        rows = importer.consume_nb_grouped_lines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {'A': '4', 'B': '5', 'C': '6'})

    def test_consume_nb_grouped_lines_same_number(self):
        importer = self.create_csv_importer(
            nb_grouped_lines=2,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        rows = importer.consume_nb_grouped_lines()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {'A': '1', 'B': '2', 'C': '3'})
        self.assertEqual(rows[1], {'A': '4', 'B': '5', 'C': '6'})

    def test_consume_nb_group_lines_greater_than_nb_lines(self):
        importer = self.create_csv_importer(
            nb_grouped_lines=3,
            file_to_import=self.get_file_to_import())
        importer.get_reader()
        rows = importer.consume_nb_grouped_lines()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {'A': '1', 'B': '2', 'C': '3'})
        self.assertEqual(rows[1], {'A': '4', 'B': '5', 'C': '6'})

    def get_exporter_file_to_import(self, withmapping=False):
        if not withmapping:
            res = '''"model","mode"\n'''
            res += '''"Model.IO.Exporter","Model.IO.Exporter.CSV"'''
        else:
            res = '''"model/EXTERNAL_ID","mode"\n'''
            res += '''"exporter_mapping","Model.IO.Exporter.CSV"'''
            exporter = self.registry.IO.Exporter.CSV.insert(
                model="Model.IO.Importer")
            self.registry.IO.Mapping.set('exporter_mapping', exporter)

        return res.encode('utf-8')

    def get_model_file_to_import(self, withmapping=False, short=False):
        if not withmapping:
            res = '''"name","table"\n'''
            res += '''"Model.IO.Test","io_test"'''
        else:
            if short:
                res = '''"/EXTERNAL_ID","table"\n'''
            else:
                res = '''"name/EXTERNAL_ID","table"\n'''
            res += '''"exporter_mapping","io_test"'''

            model = self.registry.System.Model.insert(
                name="Model.IO.Test", table='io_other_table')
            self.registry.IO.Mapping.set('exporter_mapping', model)

        return res.encode('utf-8')

    def get_column_file_to_import(self, withmapping=False):
        if not withmapping:
            res = '''"model","name","nullable"\n'''
            res += '''"Model.IO.Importer","test","1"'''
        else:
            res = '''"model/EXTERNAL_ID","name/EXTERNAL_ID","nullable"\n'''
            res += '''"exporter_mapping","exporter_mapping","1"'''
            column = self.registry.System.Column.insert(
                model="Model.IO.Importer", name="test", nullable=False)
            self.registry.IO.Mapping.set('exporter_mapping', column)

        return res.encode('utf-8')

    def test_get_header_without_mapping_and_without_pks(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_exporter_file_to_import())
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, [])
        self.assertEqual(importer.header_external_id, None)
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 2)
        for header in ('mode', 'model'):
            self.assertIn(header, importer.fields_description.keys())
            self.assertIn(header, importer.header_fields)

    def test_get_header_with_pks(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_model_file_to_import(),
            model='Model.System.Model')
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, ['name'])
        self.assertEqual(importer.header_external_id, None)
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 2)
        for header in ('name', 'table'):
            self.assertIn(header, importer.fields_description.keys())

        self.assertNotIn('name', importer.header_fields)
        self.assertIn('table', importer.header_fields)

    def test_get_header_with_multi_pks(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_column_file_to_import(),
            model='Model.System.Column')
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, ['model', 'name'])
        self.assertEqual(importer.header_external_id, None)
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 3)
        for header in ('model', 'name', 'nullable'):
            self.assertIn(header, importer.fields_description.keys())

        self.assertNotIn('name', importer.header_fields)
        self.assertIn('nullable', importer.header_fields)

    def test_get_header_with_pks_mapping(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_model_file_to_import(withmapping=True),
            model='Model.System.Model')
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, [])
        self.assertEqual(importer.header_external_id, 'name/EXTERNAL_ID')
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 2)
        for header in ('name', 'table'):
            self.assertIn(header, importer.fields_description.keys())

        self.assertNotIn('name', importer.header_fields)
        self.assertIn('table', importer.header_fields)

    def test_get_header_with_pks_mapping_short_external_id(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_model_file_to_import(withmapping=True,
                                                         short=True),
            model='Model.System.Model')
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, [])
        self.assertEqual(importer.header_external_id, '/EXTERNAL_ID')
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 1)
        self.assertIn('table', importer.fields_description.keys())
        self.assertNotIn('name', importer.header_fields)
        self.assertIn('table', importer.header_fields)

    def test_get_header_with_multi_pks_mapping(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_column_file_to_import(withmapping=True),
            model='Model.System.Column')
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, [])
        self.assertEqual(importer.header_external_id, 'name/EXTERNAL_ID')
        self.assertEqual(importer.header_external_ids, {})
        self.assertEqual(len(importer.fields_description.keys()), 3)
        for header in ('model', 'name', 'nullable'):
            self.assertIn(header, importer.fields_description.keys())

        self.assertNotIn('name', importer.header_fields)
        self.assertIn('nullable', importer.header_fields)

    def test_get_header_with_mapping(self):
        importer = self.create_csv_importer(
            file_to_import=self.get_exporter_file_to_import(withmapping=True))
        importer.get_reader()
        importer.get_header()
        self.assertEqual(importer.header_pks, [])
        self.assertEqual(importer.header_external_id, None)
        self.assertEqual(importer.header_external_ids,
                         {'model/EXTERNAL_ID': 'model'})
        self.assertEqual(len(importer.fields_description.keys()), 2)
        for header in ('model', 'mode'):
            self.assertIn(header, importer.fields_description.keys())

        self.assertNotIn('model', importer.header_fields)
        self.assertIn('mode', importer.header_fields)

    def test_parse_row_on_error_raise(self):
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Exporter',
                                            csv_on_error='raise_now')
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Importer.fields_description(
            fields=importer.header_fields)
        with self.assertRaises(CSVImporterException):
            importer.parse_row({'mode': 'Model.IO.Exporter.CSV'})

    def test_parse_row(self):
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Exporter')
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Importer.fields_description(
            fields=importer.header_fields)
        importer.parse_row({'model': 'Model.IO.Importer',
                            'mode': 'Model.IO.Exporter.CSV'})
        self.assertEqual(len(importer.created_entries), 1)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_parse_row_with_raise(self):
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Exporter',
                                            csv_if_does_not_exist='raise')
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Importer.fields_description(
            fields=importer.header_fields)
        importer.parse_row({'model': 'Model.IO.Importer',
                            'mode': 'Model.IO.Exporter.CSV'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 1)

    def test_parse_row_with_pass(self):
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Exporter',
                                            csv_if_does_not_exist='pass')
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Importer.fields_description(
            fields=importer.header_fields)
        importer.parse_row({'model': 'Model.IO.Importer',
                            'mode': 'Model.IO.Exporter.CSV'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_parse_row_with_existing_pks_update(self):
        Model = self.registry.System.Model
        importer = self.create_csv_importer(model='Model.System.Model')
        importer.header_pks = ['name']
        importer.header_fields = ['table']
        importer.fields_description = Model.fields_description(
            fields=['name', 'table'])
        Model.insert(name='Model.IO.Test', table='io_test')
        importer.parse_row({'name': 'Model.IO.Test',
                            'table': 'io_test_other_table'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 1)
        self.assertEqual(len(importer.error_found), 0)
        self.assertEqual(importer.updated_entries[0].table,
                         'io_test_other_table')

    def test_parse_row_with_existing_pks_create(self):
        Exporter = self.registry.IO.Exporter
        importer = self.create_csv_importer(model='Model.IO.Exporter',
                                            csv_if_exist='create')
        importer.header_pks = ['id']
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Exporter.fields_description(
            fields=['id', 'model', 'mode'])
        exporter = Exporter.CSV.insert(model='Model.IO.Importer')
        importer.parse_row({'id': str(exporter.id),
                            'model': 'Model.System.Model',
                            'mode': "Model.IO.Exporter.CSV"})
        self.assertEqual(len(importer.created_entries), 1)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_parse_row_with_existing_pks_pass(self):
        Model = self.registry.System.Model
        importer = self.create_csv_importer(model='Model.System.Model',
                                            csv_if_exist="pass")
        importer.header_pks = ['name']
        importer.header_fields = ['table']
        importer.fields_description = Model.fields_description(
            fields=['name', 'table'])
        Model.insert(name='Model.IO.Test', table='io_test')
        importer.parse_row({'name': 'Model.IO.Test',
                            'table': 'io_test_other_table'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_parse_row_with_existing_pks_raise(self):
        Model = self.registry.System.Model
        importer = self.create_csv_importer(model='Model.System.Model',
                                            csv_if_exist="raise")
        importer.header_pks = ['name']
        importer.header_fields = ['table']
        importer.fields_description = Model.fields_description(
            fields=['name', 'table'])
        Model.insert(name='Model.IO.Test', table='io_test')
        importer.parse_row({'name': 'Model.IO.Test',
                            'table': 'io_test_other_table'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 1)

    def test_parse_row_with_unexting_multi_pks(self):
        Column = self.registry.System.Column
        importer = self.create_csv_importer(model='Model.System.Column')
        importer.header_pks = ['name', 'model']
        importer.header_fields = ['nullable']
        importer.fields_description = Column.fields_description(
            fields=['name', 'model', 'nullable'])
        importer.parse_row({'name': 'test',
                            'model': 'Model.System.Model',
                            'nullable': True})
        self.assertEqual(len(importer.created_entries), 1)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_parse_row_with_mapping_pks(self):
        Model = self.registry.System.Model
        importer = self.create_csv_importer(model='Model.System.Model')
        importer.header_external_id = 'name/EXTERNAL_ID'
        importer.header_fields = ['table']
        importer.fields_description = Model.fields_description(
            fields=['name', 'table'])
        model = Model.insert(name='Model.IO.Test', table='io_test')
        self.registry.IO.Mapping.set('import_mapping', model)
        importer.parse_row({'name/EXTERNAL_ID': 'import_mapping',
                            'table': 'io_test_other_table'})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 1)
        self.assertEqual(len(importer.error_found), 0)
        self.assertEqual(importer.updated_entries[0].table,
                         'io_test_other_table')

    def test_parse_row_with_unexisting_mapping_pks(self):
        Exporter = self.registry.IO.Exporter
        importer = self.create_csv_importer(model='Model.IO.Exporter')
        importer.header_external_id = 'id/EXTERNAL_ID'
        importer.header_fields = ['model', 'mode']
        importer.fields_description = Exporter.fields_description(
            fields=['id', 'model', 'mode'])
        importer.parse_row({'id/EXTERNAL_ID': 'import_mapping',
                            'model': 'Model.IO.Exporter',
                            'mode': 'Model.IO.Exporter.CSV'})
        self.assertEqual(len(importer.created_entries), 1)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)
        exporter = self.registry.IO.Mapping.get('Model.IO.Exporter',
                                                'import_mapping')
        self.assertEqual(exporter.mode, 'Model.IO.Exporter.CSV')
        self.assertEqual(exporter.model, 'Model.IO.Exporter')

    def test_parse_row_with_mapping(self):
        Model = self.registry.System.Model
        model = Model.insert(name='Model.IO.Test', table='io_test')
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Exporter')
        exporter = self.registry.IO.Exporter.CSV.insert(
            model='Model.IO.Exporter')
        importer.header_pks = ['id']
        importer.header_external_ids = {'model/EXTERNAL_ID': 'model'}
        importer.header_fields = ['mode']
        importer.fields_description = Importer.fields_description(
            fields=['id', 'model', 'mode'])
        self.registry.IO.Mapping.set('import_mapping', model)
        importer.parse_row({'id': str(exporter.id),
                            'model/EXTERNAL_ID': 'import_mapping',
                            'mode': "Model.IO.Exporter.CSV"})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 1)
        self.assertEqual(len(importer.error_found), 0)
        self.assertEqual(importer.updated_entries[0].model, 'Model.IO.Test')

    def test_parse_row_with_unexisting_mapping(self):
        Importer = self.registry.IO.Importer
        importer = self.create_csv_importer(model='Model.IO.Importer')
        importer.header_pks = ['id']
        importer.header_external_ids = {'model/EXTERNAL_ID': 'model'}
        importer.header_fields = ['mode']
        importer.fields_description = Importer.fields_description(
            fields=['id', 'model', 'mode'])
        importer.parse_row({'id': str(importer.importer.id),
                            'model/EXTERNAL_ID': 'import_mapping',
                            'mode': "Model.IO.Importer.CSV"})
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 1)

    def test_run(self):
        importer = self.create_csv_importer(
            model='Model.IO.Exporter',
            file_to_import=self.get_exporter_file_to_import())
        importer.run()
        self.assertEqual(len(importer.created_entries), 1)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 0)

    def test_run_raise_at_end(self):
        importer = self.create_csv_importer()
        with self.assertRaises(CSVImporterException):
            importer.run()

        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 1)

    def test_run_raise_ignored(self):
        importer = self.create_csv_importer(csv_on_error='ignore')
        importer.run()
        self.assertEqual(len(importer.created_entries), 0)
        self.assertEqual(len(importer.updated_entries), 0)
        self.assertEqual(len(importer.error_found), 1)
