# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from logging import getLogger

from anyblok import Declarations

logger = getLogger(__name__)


@Declarations.register(Declarations.Model.Documentation.Model)
class Field:
    mappers = {
        ("Many2One", True): ("m2o", "o2m"),
        ("Many2One", False): ("m2o", None),
        ("Many2Many", True): ("m2m", "m2m"),
        ("Many2Many", False): ("m2m", None),
        ("One2Many", True): ("o2m", "m2o"),
        ("One2Many", False): ("o2m", None),
        ("One2One", True): ("o2o", "o2o"),
        ("One2One", False): ("o2o", "o2o"),
    }

    def __init__(self, field, parent):
        self.field = field
        self.model = parent.model

    @classmethod
    def getelements(cls, model):
        Model = cls.anyblok.get(model.model)
        if Model.is_sql:
            return Model.fields_description().values()

        return []

    @classmethod
    def header2RST(cls, doc):
        doc.write("Fields\n~~~~~~\n\n")

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write("* " + self.field["id"] + "\n\n")
        self.toRST_docstring(doc)
        self.toRST_properties(doc)

    def toRST_docstring(self, doc):
        if hasattr(self.field, "__doc__") and self.field.__doc__:
            doc.write(self.field.__doc__ + "\n\n")  # pragma: no cover

    def toRST_properties_get(self):
        return {x: y for x, y in self.field.items() if x != "id"}

    def toRST_properties(self, doc):
        properties = self.toRST_properties_get()
        msg = ", ".join(" **%s** (%s)" % (x, y) for x, y in properties.items())
        doc.write(msg + "\n\n")

    def toUML(self, dot):
        if "remote_name" in self.field:
            self.toUML_relationship(dot)  # pragma: no cover
        else:
            self.toUML_column(dot)

    def toUML_column(self, dot):
        model = dot.get_class(self.model)
        name = self.field["id"]
        if self.field["primary_key"]:
            name = "+PK+ " + name

        if self.field["model"]:  # pragma: no cover
            remote_model = dot.get_class(self.field["model"])
            multiplicity = "1"
            if self.field["nullable"]:
                multiplicity = "0..1"

            model.aggregate(
                remote_model, label_from=name, multiplicity_from=multiplicity
            )
        else:
            name += " (%s)" % self.field["type"]
            model.add_column(name)

    def toUML_relationship(self, dot):  # pragma: no cover
        if self.field.remote:
            return

        model = dot.get_class(self.field.model)
        multiplicity, multiplicity_to = self.mappers[
            (self.field.ftype, True if self.field.remote_name else False)
        ]
        model.associate(
            self.field.remote_model,
            label_from=self.field.name,
            label_to=self.field.remote_name,
            multiplicity_from=multiplicity,
            multiplicity_to=multiplicity_to,
        )

    def toSQL(self, dot):
        if "remote_name" in self.field:
            self.toSQL_relationship(dot)  # pragma: no cover
        else:
            self.toSQL_column(dot)

    def toSQL_relationship(self, dot):
        # TODO
        pass  # pragma: no cover

    def toSQL_column(self, dot):
        Model = self.anyblok.get(self.model)
        if self.field["id"] in Model.loaded_fields:
            return

        table = dot.get_table(self.anyblok.get(self.model).__tablename__)
        if self.field.get("foreign_key"):  # pragma: no cover
            remote_table = dot.get_table(self.field.foreign_key.split(".")[0])
            if remote_table is None:
                remote_table = dot.add_label(
                    self.field.foreign_key.split(".")[0]
                )

            table.add_foreign_key(
                remote_table,
                label=self.field.name,
                nullable=self.field.nullable,
            )
        else:
            table.add_column(
                self.field["id"],
                self.field["type"],
                primary_key=self.field["primary_key"],
            )
