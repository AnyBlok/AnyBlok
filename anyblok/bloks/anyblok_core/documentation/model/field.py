# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Model.Documentation.Model)
class Field:

    def __init__(self, field):
        self.field = field

    @classmethod
    def filterField(cls, query):
        return query

    @classmethod
    def getelements(cls, model):
        query = cls.filterField(cls.registry.System.Field.query())
        return query.filter(cls.registry.System.Field.model == model).all()

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
