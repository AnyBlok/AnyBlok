# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from logging import getLogger
logger = getLogger(__name__)


@Declarations.register(Declarations.Model.Documentation.Model)
class Field:

    mappers = {
        ('Many2One', True): ("m2o", "o2m"),
        ('Many2One', False): ("m2o", None),
        ('Many2Many', True): ("m2m", "m2m"),
        ('Many2Many', False): ("m2m", None),
        ('One2Many', True): ("o2m", "m2o"),
        ('One2Many', False): ("o2m", None),
        ('One2One', True): ("o2o", "o2o"),
        ('One2One', False): ("o2o", "o2o"),
    }

    def exist(self, model):
        if not model.exist():
            return False

        M = self.registry.get(model.model.name)
        if self.field.name in M.loaded_columns:
            return True

        return False

    def __init__(self, field):
        self.field = field

    @classmethod
    def filterField(cls, query):
        return query

    @classmethod
    def getelements(cls, model):
        query = cls.filterField(cls.registry.System.Field.query())
        return query.filter(
            cls.registry.System.Field.model == model.model.name).all()

    @classmethod
    def header2RST(cls, doc):
        doc.write("Fields\n~~~~~~\n\n")

    @classmethod
    def footer2RST(cls, doc):
        pass

    def toRST(self, doc):
        doc.write('* ' + self.field.name + '\n\n')
        self.toRST_docstring(doc)
        self.toRST_properties(doc)

    def toRST_docstring(self, doc):
        if hasattr(self.field, '__doc__') and self.field.__doc__:
            doc.write(self.field.__doc__ + '\n\n')

    def toRST_properties_get(self):
        return {x: y for x, y in self.field.to_dict().items() if x != 'name'}

    def toRST_properties(self, doc):
        properties = self.toRST_properties_get()
        msg = ', '.join(' **%s** (%s)' % (x, y) for x, y in properties.items())
        doc.write(msg + '\n\n')

    def toUML(self, dot):
        if self.field.entity_type == 'Model.System.Field':
            self.toUML_field(dot)
        elif self.field.entity_type == 'Model.System.Column':
            self.toUML_column(dot)
        elif self.field.entity_type == 'Model.System.RelationShip':
            self.toUML_relationship(dot)
        else:
            logger.warn("Unknown entity type %r" % self.field.entity_type)

    def toUML_field(self, dot):
        model = dot.get_class(self.field.model)
        model.add_column(self.field.name)

    def toUML_column(self, dot):
        model = dot.get_class(self.field.model)
        name = self.field.name
        if self.field.primary_key:
            name = '+PK+ ' + name

        if self.field.remote_model:
            remote_model = dot.get_class(self.field.remote_model)
            multiplicity = "1"
            if self.field.nullable:
                multiplicity = "0..1"

            model.agregate(remote_model, label_from=name,
                           multiplicity_from=multiplicity)
        else:
            name += ' (%s)' % self.field.ftype
            model.add_column(name)

    def toUML_relationship(self, dot):
        if self.field.remote:
            return

        model = dot.get_class(self.field.model)
        multiplicity, multiplicity_to = self.mappers[(
            self.field.ftype, True if self.field.remote_name else False)]
        model.associate(self.field.remote_model, label_from=self.field.name,
                        label_to=self.field.remote_name,
                        multiplicity_from=multiplicity,
                        multiplicity_to=multiplicity_to)

    def toSQL(self, dot):
        if self.field.entity_type == 'Model.System.Field':
            self.toSQL_field(dot)
        elif self.field.entity_type == 'Model.System.Column':
            self.toSQL_column(dot)
        elif self.field.entity_type == 'Model.System.RelationShip':
            self.toSQL_relationship(dot)
        else:
            logger.warn("Unknown entity type %r" % self.field.entity_type)

    def toSQL_field(self, dot):
        # DO NOTHING
        pass

    def toSQL_relationship(self, dot):
        # TODO
        pass

    def toSQL_column(self, dot):
        table = dot.get_table(self.registry.get(
            self.field.model).__tablename__)
        if self.field.foreign_key:
            remote_table = dot.get_table(self.field.foreign_key.split('.')[0])
            if remote_table is None:
                remote_table = dot.add_label(
                    self.field.foreign_key.split('.')[0])

            table.add_foreign_key(remote_table, label=self.field.name,
                                  nullable=self.field.nullable)
        else:
            table.add_column(self.field.name, self.field.ftype,
                             primary_key=self.field.primary_key)
