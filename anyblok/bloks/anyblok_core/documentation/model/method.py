# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.field import FieldException
from inspect import getmembers, ismethod, isfunction


@Declarations.register(Declarations.Model.Documentation.Model)
class Method:

    def __init__(self, method):
        self.name, self.method = method

    @classmethod
    def filterMethod(cls, model, name):
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

    @classmethod
    def getelements(cls, model):
        res = []
        Model = cls.registry.get(model)
        try:
            for k, v in getmembers(Model):
                if not (ismethod(v) or isfunction(v)):
                    continue

                if cls.filterMethod(model, k):
                    continue

                res.append((k, v))
        except FieldException:
            pass

        return res

    @classmethod
    def header2RST(cls, doc):
        title = "Methods and class methods"
        doc.write("%s\n%s\n\n" % (title, '~' * len(title)))

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write('* ' + self.name + '\n\n')
        self.toRST_docstring(doc)

    def toRST_docstring(self, doc):
        if hasattr(self.method, '__doc__') and self.method.__doc__:
            doc.write(self.method.__doc__ + '\n\n')
