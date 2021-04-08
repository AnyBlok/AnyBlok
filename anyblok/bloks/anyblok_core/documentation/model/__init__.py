# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloading
from anyblok.config import Configuration


@Declarations.register(Declarations.Model.Documentation)
class Model(Declarations.Mixin.DocElement):

    def __init__(self, model):
        self.model = model
        self.fields = []
        self.attributes = []
        if self.exist():
            self._auto_doc(
                self.anyblok.Documentation.Model.Field, self.fields, self)
            self._auto_doc(self.anyblok.Documentation.Model.Attribute,
                           self.attributes, self)

    def exist(self):
        return self.anyblok.has(self.model.name)

    @classmethod
    def get_all_models(cls, models):  # pragma: no cover
        Model = cls.anyblok.System.Model
        res = []
        for model in models:
            if model[-2:] == '.*':
                query = Model.query().filter(Model.name.like(model[:-1] + '%'))
                res.extend(query.all().name)
            else:
                res.append(model)

        return res

    @classmethod
    def filterModel(cls, query):
        Model = cls.anyblok.System.Model
        wanted_models = Configuration.get('doc_wanted_models')
        if wanted_models:  # pragma: no cover
            wanted_models = cls.get_all_models(wanted_models)
            query = query.filter(Model.name.in_(wanted_models))
        else:
            wanted_models = []

        unwanted_models = Configuration.get('doc_unwanted_models')
        if unwanted_models:  # pragma: no cover
            unwanted_models = cls.get_all_models(unwanted_models)
            unwanted_models = [x for x in unwanted_models
                               if x not in wanted_models]
            query = query.filter(Model.name.notin_(unwanted_models))

        return query

    @classmethod
    def getelements(cls):
        return cls.filterModel(cls.anyblok.System.Model.query()).all()

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
                doc, self.anyblok.Documentation.Model.Field, self.fields)

    def toRST_method(self, doc):
        if self.attributes:
            self._toRST(
                doc, self.anyblok.Documentation.Model.Attribute,
                self.attributes)

    def toRST_docstring(self, doc):
        Model = self.anyblok.get(self.model.name)
        if hasattr(Model, '__doc__') and Model.__doc__:
            doc.write(Model.__doc__ + '\n\n')

    def toRST_properties_get(self):
        Model = self.anyblok.get(self.model.name)
        tablename = getattr(Model, '__tablename__', 'No table')
        return {
            'table name': tablename,
        }

    def toRST_properties(self, doc):
        properties = self.toRST_properties_get()
        msg = 'Properties:\n\n* ' + '\n* '.join('**%s** : %s' % (x, y)
                                                for x, y in properties.items())
        doc.write(msg + '\n\n')

    def toUML_add_model(self, dot):
        dot.add_class(self.model.name)

    def toUML_add_attributes(self, dot):
        for f in self.fields:
            f.toUML(dot)

        for attr in self.attributes:
            attr.toUML(dot, self.model.name)

    def toSQL_add_table(self, dot):
        Model = self.anyblok.get(self.model.name)
        if hasattr(Model, '__tablename__'):
            dot.add_table(Model.__tablename__)

    def toSQL_add_fields(self, dot):
        Model = self.anyblok.get(self.model.name)
        if hasattr(Model, '__tablename__'):
            for f in self.fields:
                f.toSQL(dot)


from . import field  # noqa
reload_module_if_blok_is_reloading(field)
from . import attribute  # noqa
reload_module_if_blok_is_reloading(attribute)
