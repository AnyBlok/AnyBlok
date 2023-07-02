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
    def __init__(self, model, parent):
        self.model = model
        self.fields = []
        self.attributes = []
        if self.exist():
            self._auto_doc(
                self.anyblok.Documentation.Model.Field, self.fields, self
            )
            self._auto_doc(
                self.anyblok.Documentation.Model.Attribute,
                self.attributes,
                self,
            )

    def exist(self):
        return self.anyblok.has(self.model)

    @classmethod
    def filterModel(cls, models):  # noqa: C901
        wanted_models = Configuration.get("doc_wanted_models") or []
        if wanted_models:  # pragma: no cover
            new_models = []
            for model in models:
                for wanted_model in wanted_models:
                    if wanted_model[-1] == "*" and model.startswidth(
                        wanted_model[:-1]
                    ):
                        new_models.append(model)
                    elif wanted_model == model:
                        new_models.append(model)
            models = new_models

        unwanted_models = Configuration.get("doc_unwanted_models") or []
        if unwanted_models:  # pragma: no cover
            unwanted_models = [
                x for x in unwanted_models if x not in wanted_models
            ]
            new_models = []
            for model in models:
                for unwanted_model in unwanted_models:
                    if unwanted_model[-1] == "*" and model.startswidth(
                        unwanted_model[:-1]
                    ):
                        continue
                    elif unwanted_model == model:
                        continue

                    new_models.append(model)

            models = new_models

        return models

    @classmethod
    def getelements(cls):
        return cls.filterModel(
            [x for x in cls.anyblok.loaded_namespaces.keys()]
        )

    @classmethod
    def header2RST(cls, doc):
        doc.write(
            "Models\n======\n\n"
            "This the differents models defined "
            "on the project" + ("\n" * 2)
        )

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write(self.model + "\n" + "-" * len(self.model) + "\n\n")
        self.toRST_docstring(doc)
        self.toRST_properties(doc)
        self.toRST_field(doc)
        self.toRST_method(doc)

    def toRST_field(self, doc):
        if self.fields:
            self._toRST(
                doc, self.anyblok.Documentation.Model.Field, self.fields
            )

    def toRST_method(self, doc):
        if self.attributes:
            self._toRST(
                doc, self.anyblok.Documentation.Model.Attribute, self.attributes
            )

    def toRST_docstring(self, doc):
        Model = self.anyblok.get(self.model)
        if hasattr(Model, "__doc__") and Model.__doc__:
            doc.write(Model.__doc__ + "\n\n")

    def toRST_properties_get(self):
        Model = self.anyblok.get(self.model)
        tablename = getattr(Model, "__tablename__", "No table")
        return {
            "table name": tablename,
        }

    def toRST_properties(self, doc):
        properties = self.toRST_properties_get()
        msg = "Properties:\n\n* " + "\n* ".join(
            "**%s** : %s" % (x, y) for x, y in properties.items()
        )
        doc.write(msg + "\n\n")

    def toUML_add_model(self, dot):
        dot.add_class(self.model)

    def toUML_add_attributes(self, dot):
        for f in self.fields:
            f.toUML(dot)

        for attr in self.attributes:
            attr.toUML(dot, self.model)

    def toSQL_add_table(self, dot):
        Model = self.anyblok.get(self.model)
        if hasattr(Model, "__tablename__"):
            dot.add_table(Model.__tablename__)

    def toSQL_add_fields(self, dot):
        Model = self.anyblok.get(self.model)
        if hasattr(Model, "__tablename__"):
            for f in self.fields:
                f.toSQL(dot)


from . import field  # noqa

reload_module_if_blok_is_reloading(field)
from . import attribute  # noqa

reload_module_if_blok_is_reloading(attribute)
