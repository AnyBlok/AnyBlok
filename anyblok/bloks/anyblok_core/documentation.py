# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from io import StringIO
from inspect import getmembers, ismethod, isfunction, signature


@Declarations.register(Declarations.Model)
class Documentation:

    def __init__(self):
        self.doc = StringIO()

    def write_title(self):
        title = 'Documentation of the %s project' % self.Env.get('db_name')
        quote = "=" * len(title)
        self.doc.write('\n'.join([quote, title, quote, '\n']))

    def write_header(self):
        self.doc.write('..content::' + ('\n' * 2))

    def write_footer(self):
        pass

    def write_chapters(self):
        self.write_models()
        self.write_bloks_readme()

    def write_models(self):
        self.doc.write("Models\n======\n\n"
                       "This the differents models defined "
                       "on the project" + ('\n' * 2))
        models = list(self.registry.loaded_namespaces.keys())
        models.sort()
        for model in models:
            self.write_model(model)

    def write_bloks_readme(self):
        self.doc.write("Bloks\n=====\n\n")
        Blok = self.registry.System.Blok
        for blok in Blok.query().filter(Blok.state == 'installed').all():
            self.write_blok_readme(blok)

    def write_blok_readme(self, blok):
        self.doc.write(blok.name + '\n' + '-' * len(blok.name) + '\n\n')
        self.doc.write(blok.short_description + '\n\n')
        self.doc.write(blok.long_description + '\n\n')

    def write_model(self, model):
        self.doc.write('\n'.join([model, '-' * len(model), '\n']))
        Model = self.registry.get(model)
        self.write_model_header(Model)
        self.write_model_fields(model)
        self.write_model_members(model)

    def get_model_attributes(self, Model):
        tablename = getattr(Model, '__tablename__', 'No table')
        attributes = {
            'table name': tablename,
        }
        return attributes

    def write_model_header(self, Model):
        self.write_model_header_docstring(Model)
        self.write_attributes(self.get_model_attributes(Model), 'Properties')

    def write_model_header_docstring(self, Model):
        if hasattr(Model, '__doc__') and Model.__doc__:
            self.doc.write(Model.__doc__ + ('\n' * 2))

    def write_model_fields(self, model):

        def format_name(x):
            if x == 'ftype':
                return 'type'
            return x

        for Field in (self.registry.System.Field,
                      self.registry.System.Column,
                      self.registry.System.RelationShip):
            fields = Field.query().filter(Field.model == model).dictall()
            if fields:
                self.doc.write(
                    Field.__registry_name__.split('.')[-1] + ':\n\n')
            for field in fields:
                self.doc.write("* **%s**\n    - " % field['name'])
                self.doc.write('\n    - '.join(
                    '``%s``: %s' % (format_name(x), y)
                    for x, y in field.items()
                    if x not in ('name', 'model')))
                self.doc.write('\n')

            self.doc.write('\n')

        self.doc.write('\n')

    def write_model_members(self, model):
        Model = self.registry.get(model)
        self.doc.write("Methods and class methods:\n\n")
        try:
            for k, v in getmembers(Model):
                if not (ismethod(v) or isfunction(v)):
                    continue

                if self.unwanted_model_members(model, k):
                    continue

                self.doc.write('**' + k + '**\n\n')
                if hasattr(v, '__doc__') and v.__doc__:
                    self.doc.write(v.__doc__ + '\n')
                else:
                    self.doc.write(str(signature(v)) + '\n')

                self.doc.write('\n')
        except Exception:
            pass

    def unwanted_model_members(self, model, name):
        if name in ('insert', 'update', 'to_primary_keys',
                    'to_dict', 'sqlalchemy_query_update',
                    'sqlalchemy_query_delete', 'query',
                    'precommit_hook', 'multi_insert', 'initialize_model',
                    'has_perm', 'has_model_perm',
                    'get_where_clause_from_primary_keys', 'get_primary_keys',
                    'get_model', 'from_primary_keys',
                    'from_multi_primary_keys', 'fire', 'fields_description',
                    '_fields_description', 'delete', 'aliased', '__init__'):
            return True

        return False

    def write_attributes(self, attributes, title):
        self.doc.write('%s:\n\n* %s\n\n' % (title, '\n* '.join(
            '**%s**: %s ' % (x, y) for x, y in attributes.items())))

    def create(self):
        self.write_title()
        self.write_header()
        self.write_chapters()
        self.write_footer()

    def toRST(self):
        self.doc.seek(0)
        return self.doc.read()
