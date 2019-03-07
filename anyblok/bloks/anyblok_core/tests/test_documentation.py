# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest  # noqa
from anyblok._graphviz import ModelSchema, SQLSchema
from anyblok.config import Configuration


class TestDocumentation:

    def test_autodoc(self, rollback_registry):
        registry = rollback_registry
        doc = registry.Documentation()
        doc.auto_doc()

    def test_to_rst(self, rollback_registry):
        registry = rollback_registry
        doc = registry.Documentation()
        doc.auto_doc()
        with open('test_doc_output', 'w') as fp:
            doc.toRST(fp)

    def test_to_uml(self, rollback_registry):
        registry = rollback_registry
        doc = registry.Documentation()
        doc.auto_doc()
        format_ = Configuration.get('schema_format')
        dot = ModelSchema('test', format=format_)
        doc.toUML(dot)
        dot.save()

    def test_to_sql(self, rollback_registry):
        registry = rollback_registry
        doc = registry.Documentation()
        doc.auto_doc()
        format_ = Configuration.get('schema_format')
        dot = SQLSchema('test', format=format_)
        doc.toSQL(dot)
        dot.save()
