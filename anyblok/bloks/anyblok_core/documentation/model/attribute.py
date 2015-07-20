# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.field import FieldException
from inspect import getmembers, ismethod, isfunction, ismodule, isclass


@Declarations.register(Declarations.Model.Documentation.Model)
class Attribute:

    def __init__(self, attribute):
        self.name, self.attribute = attribute

    def exist(self, model):
        return model.exist()

    @classmethod
    def filterAttribute(cls, model, name):
        if name in ('insert', 'update', 'to_primary_keys',
                    'to_dict', 'sqlalchemy_query_update',
                    'sqlalchemy_query_delete', 'query',
                    'precommit_hook', 'multi_insert', 'initialize_model',
                    'has_perm', 'has_model_perm',
                    'get_where_clause_from_primary_keys', 'get_primary_keys',
                    'get_model', 'from_primary_keys',
                    'from_multi_primary_keys', 'fire', 'fields_description',
                    '_fields_description', 'delete', 'aliased', '__init__',
                    'loaded_columns', 'loaded_fields', 'registry',
                    '_sa_class_manager', '_decl_class_registry'):
            return True

        return False

    @classmethod
    def getelements(cls, model):
        res = []
        Model = cls.registry.get(model.model.name)
        try:
            for k, v in getmembers(Model):
                if ismodule(v) or isclass(v):
                    continue

                if k.startswith('__'):
                    continue

                if cls.filterAttribute(model, k):
                    continue

                res.append((k, v))
        except FieldException:
            pass

        return res

    @classmethod
    def header2RST(cls, doc):
        title = "Attributes, methods and class methods"
        doc.write("%s\n%s\n\n" % (title, '~' * len(title)))

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write('* ' + self.name + '\n\n')
        self.toRST_docstring(doc)

    def toRST_docstring(self, doc):
        if hasattr(self.attribute, '__doc__') and self.attribute.__doc__:
            doc.write(self.attribute.__doc__ + '\n\n')

    def toUML(self, dot, modelname):
        model = dot.get_class(modelname)
        if ismethod(self.attribute) or isfunction(self.attribute):
            model.add_method(self.name)
        else:
            model.add_property(self.name)
