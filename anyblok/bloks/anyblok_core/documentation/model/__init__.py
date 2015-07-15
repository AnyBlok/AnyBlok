# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloading


@Declarations.register(Declarations.Model.Documentation)
class Model(Declarations.Mixin.DocElement):

    def __init__(self, model):
        self.model = model
        self.fields = []
        self.methods = []
        self._auto_doc(
            self.registry.Documentation.Model.Field, self.fields, model.name)
        self._auto_doc(
            self.registry.Documentation.Model.Method, self.methods, model.name)

    @classmethod
    def filterModel(cls, query):
        return query

    @classmethod
    def getelements(cls):
        return cls.filterModel(cls.registry.System.Model.query()).all()

    @classmethod
    def header2RST(cls, doc):
        doc.write("Models\n======\n\n"
                  "This the differents models defined "
                  "on the project" + ('\n' * 2))

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write(self.model.name + '\n' + '-' * len(self.model.name) + '\n\n')
        self.toRST_docstring(doc)
        self.toRST_properties(doc)
        self.toRST_field(doc)
        self.toRST_method(doc)

    def toRST_field(self, doc):
        if self.fields:
            self._toRST(
                doc, self.registry.Documentation.Model.Field, self.fields)

    def toRST_method(self, doc):
        if self.methods:
            self._toRST(
                doc, self.registry.Documentation.Model.Method,
                self.methods)

    def toRST_docstring(self, doc):
        Model = self.registry.get(self.model.name)
        if hasattr(Model, '__doc__') and Model.__doc__:
            doc.write(Model.__doc__ + '\n\n')

    def toRST_properties_get(self):
        Model = self.registry.get(self.model.name)
        tablename = getattr(Model, '__tablename__', 'No table')
        return {
            'table name': tablename,
        }

    def toRST_properties(self, doc):
        properties = self.toRST_properties_get()
        msg = 'Properties:\n\n* ' + '\n* '.join('**%s** : %s' % (x, y)
                                                for x, y in properties.items())
        doc.write(msg + '\n\n')


from . import field
reload_module_if_blok_is_reloading(field)
from . import method
reload_module_if_blok_is_reloading(method)
