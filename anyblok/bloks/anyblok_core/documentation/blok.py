# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.blok import BlokManager


@Declarations.register(Declarations.Model.Documentation)
class Blok:

    def __init__(self, blok):
        self.blok = blok

    def exist(self):
        return BlokManager.has(self.blok.name)

    @classmethod
    def filterBloks(cls, query):
        Blok = cls.registry.System.Blok
        return query.filter(Blok.state == 'installed').order_by(Blok.order)

    @classmethod
    def getelements(cls):
        Blok = cls.registry.System.Blok
        query = Blok.query()
        query = cls.filterBloks(query)
        return query.all()

    @classmethod
    def header2RST(cls, doc):
        doc.write("Bloks\n=====\n\n")

    @classmethod
    def footer2RST(cls, doc):

        pass

    def toRST(self, doc):
        doc.write(self.blok.name + '\n' + '-' * len(self.blok.name) + '\n\n')
        doc.write(self.blok.short_description + '\n\n')
        self.toRST_write_params(doc)
        doc.write(self.blok.long_description + '\n\n')

    def toRST_get_field(self):
        return ('version', 'installed_version')

    def toRST_write_params(self, doc):
        fields = self.toRST_get_field()
        msg = "Paramater:\n\n* "
        msg += '\n* '.join('**%s** = %s' % (f, getattr(self.blok, f))
                           for f in fields)
        doc.write(msg + '\n\n')
