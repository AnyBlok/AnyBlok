# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.column import Integer


class TestException(Exception):
    pass


class TestCoreQuery(DBTestCase):

    def test_update(self):
        def inherit_update():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test:

                id = Integer(primary_key=True)
                id2 = Integer()

                @classmethod
                def sqlalchemy_query_update(cls, query, *args, **kwargs):
                    raise TestException('test')

        registry = self.init_registry(inherit_update)
        try:
            registry.Test.query().update({'id2': 1})
            self.fail('Update must fail')
        except TestException:
            pass

        try:
            t = registry.System.Blok.query().first()
            t.update({registry.System.Blok.state: 'undefined'})
        except TestException:
            pass

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.register(Core)
            class Query:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        self.assertEqual(registry.System.Blok.query().foo(), True)
