# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloading


@Declarations.register(Declarations.Mixin)
class DocElement:

    def _auto_doc(self, Model, elements, *args, **kwargs):
        for el in Model.getelements(*args, **kwargs):
            _el = Model(el)
            if _el.exist(*args, **kwargs):
                elements.append(_el)

    def _toRST(self, doc, Model, elements):
        Model.header2RST(doc)
        for el in elements:
            el.toRST(doc)

        Model.footer2RST(doc)


@Declarations.register(Declarations.Model)
class Documentation(Declarations.Mixin.DocElement):

    def __init__(self):
        self.bloks = []
        self.models = []

    def auto_doc_blok(self):
        self._auto_doc(self.registry.Documentation.Blok, self.bloks)

    def auto_doc_model(self):
        self._auto_doc(self.registry.Documentation.Model, self.models)

    def auto_doc(self):
        self.auto_doc_blok()
        self.auto_doc_model()

    def header2RST(self, doc):
        pass

    def footer2RST(self, doc):
        pass

    def chapter2RST(self, doc):
        self.toRST_blok(doc)
        self.toRST_model(doc)

    def toRST(self, doc):
        title = 'Documentation of the %s project' % self.Env.get('db_name')
        quote = "=" * len(title)
        doc.write('\n'.join([quote, title, quote, '\n']))
        self.header2RST(doc)
        self.chapter2RST(doc)
        self.footer2RST(doc)

    def toUML(self, dot):
        for m in self.models:
            m.toUML_add_model(dot)

        for m in self.models:
            m.toUML_add_attributes(dot)

    def toSQL(self, dot):
        for m in self.models:
            m.toSQL_add_table(dot)

        for m in self.models:
            m.toSQL_add_fields(dot)

    def toRST_blok(self, doc):
        self._toRST(doc, self.registry.Documentation.Blok, self.bloks)

    def toRST_model(self, doc):
        self._toRST(doc, self.registry.Documentation.Model, self.models)


from . import blok  # noqa
reload_module_if_blok_is_reloading(blok)
from . import model  # noqa
reload_module_if_blok_is_reloading(model)
