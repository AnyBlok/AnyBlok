# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.column import Integer
from anyblok.relationship import Many2Many, One2Many, Many2One


class TestInstrumentedList(DBTestCase):

    def test_all_method_on_query_return_InstrumentedList(self):
        registry = self.init_registry(None)
        check = isinstance(registry.System.Blok.query().all(),
                           registry.InstrumentedList)
        self.assertTrue(check)

    def test_empty_result_on_query_return_InstrumentedList(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        bloks = Blok.query().filter(Blok.name == 'Unexisting blok').all()
        check = isinstance(bloks, registry.InstrumentedList)
        self.assertTrue(check)
        self.assertEqual(bloks.name, [])

    def test_M2M_with_InstrumentedList(self):

        def m2m_with_instrumentedlist():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test:
                id = Integer(primary_key=True)

            @Declarations.register(Model)
            class Test2:
                id = Integer(primary_key=True)
                tests = Many2Many(model=Model.Test, many2many="tests2")

        registry = self.init_registry(m2m_with_instrumentedlist)

        t = registry.Test.insert()
        t2 = registry.Test2.insert()
        t.tests2.append(t2)
        self.assertEqual(t2.tests, [t])
        check = isinstance(t.tests2, registry.InstrumentedList)
        self.assertTrue(check)
        check = isinstance(t2.tests, registry.InstrumentedList)
        self.assertTrue(check)

    def test_O2M_is_InstrumentedList(self):

        def o2m_with_instrumentedlist():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test2:
                id = Integer(primary_key=True)

            @Declarations.register(Model)
            class Test:
                id = Integer(primary_key=True)
                test2 = Integer(foreign_key=Model.Test2.use('id'))

            @Declarations.register(Model)  # noqa
            class Test2:
                tests = One2Many(model=Model.Test)

        registry = self.init_registry(o2m_with_instrumentedlist)

        t = registry.Test.insert()
        t2 = registry.Test2.insert()
        t2.tests.append(t)
        check = isinstance(t2.tests, registry.InstrumentedList)
        self.assertTrue(check)

    def test_O2M_linked_is_InstrumentedList(self):

        def o2m_with_instrumentedlist():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test:
                id = Integer(primary_key=True)

            @Declarations.register(Model)
            class Test2:
                id = Integer(primary_key=True)
                test = Many2One(model=Model.Test, one2many="tests2")

        registry = self.init_registry(o2m_with_instrumentedlist)

        t = registry.Test.insert()
        t2 = registry.Test2.insert()
        t.tests2.append(t2)
        check = isinstance(t.tests2, registry.InstrumentedList)
        self.assertTrue(check)

    def test_call_column(self):

        def call_column():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test:
                id = Integer(primary_key=True)

        registry = self.init_registry(call_column)

        t = registry.Test.insert()
        self.assertEqual(registry.Test.query().all().id, [t.id])

    def test_call_method(self):

        def call_method():

            from anyblok import Declarations
            Model = Declarations.Model

            @Declarations.register(Model)
            class Test:
                id = Integer(primary_key=True)

                def foo(self):
                    return self.id

        registry = self.init_registry(call_method)

        t = registry.Test.insert()
        self.assertEqual(registry.Test.query().all().foo(), [t.id])

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.register(Core)
            class InstrumentedList:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        self.assertTrue(registry.System.Blok.query().all().foo())
