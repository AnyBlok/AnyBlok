# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.declarations import Declarations, listen
from anyblok.column import Integer, Boolean, String
from anyblok.model.event import ORMEventException


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


class TestEvent(DBTestCase):

    def check_event(self, registry):
        self.assertEqual(registry.Test.x, 0)
        registry.Event.fire('fireevent')
        self.assertEqual(registry.Test.x, 1)
        registry.Event.fire('fireevent', a=2, b=2)
        self.assertEqual(registry.Test.x, 4)
        registry.Event.fire('fireevent')
        self.assertEqual(registry.Test.x, 1)

    def test_simple_event_from_model(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Model)
            class Test:

                x = 0

                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

        registry = self.init_registry(add_in_registry)
        self.check_event(registry)

    def test_simple_event_from_model_by_name(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Model)
            class Test:

                x = 0

                @listen('Model.Event', 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

        registry = self.init_registry(add_in_registry)
        self.assertEqual(len(registry.events['Model.Event']['fireevent']),
                         1)
        self.check_event(registry)

    def test_simple_event_from_mixin(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Mixin)
            class MTest:

                x = 0

                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

            @register(Model)
            class Test(Mixin.MTest):
                pass

        registry = self.init_registry(add_in_registry)
        self.assertEqual(len(registry.events['Model.Event']['fireevent']),
                         1)
        self.check_event(registry)

    def test_simple_event_from_core(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Core)
            class Base:

                x = 0

                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

            @register(Model)
            class Test:
                pass

        registry = self.init_registry(add_in_registry)
        self.check_event(registry)

    def add_in_registry_inherited(self, withcore=False, withmixin=False,
                                  withmodel=False):

        @register(Model)
        class Event:
            pass

        @register(Core)
        class Base:

            x = 0

            if withcore:
                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    pass

        @register(Mixin)
        class MTest:

            if withmixin:
                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    pass

        @register(Model)
        class Test(Mixin.MTest):

            if withmodel:
                @listen(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b
            else:
                @classmethod
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

    def test_inherited_without_event(self):
        registry = self.init_registry(self.add_in_registry_inherited)
        self.assertEqual(registry.Test.x, 0)
        registry.Event.fire('fireevent')
        self.assertEqual(registry.Test.x, 0)
        registry.Event.fire('fireevent', a=2, b=2)
        self.assertEqual(registry.Test.x, 0)
        registry.Event.fire('fireevent')
        self.assertEqual(registry.Test.x, 0)

    def test_inherited_with_event_on_core(self):
        registry = self.init_registry(self.add_in_registry_inherited,
                                      withcore=True)
        self.check_event(registry)

    def test_inherited_with_event_on_mixin(self):
        registry = self.init_registry(self.add_in_registry_inherited,
                                      withmixin=True)
        self.assertEqual(
            len(registry.events['Model.Event']['fireevent']), 1)
        self.check_event(registry)

    def test_inherited_with_event_on_core_and_mixin(self):
        registry = self.init_registry(self.add_in_registry_inherited,
                                      withcore=True, withmixin=True)
        self.check_event(registry)

    def test_inherited_with_event_on_mixin_and_model(self):
        registry = self.init_registry(self.add_in_registry_inherited,
                                      withmodel=True, withmixin=True)
        self.assertEqual(len(registry.events['Model.Event']['fireevent']), 1)
        self.check_event(registry)

    def test_sqlalchemy_listen_on_model(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = Boolean(default=False)

                @listen('Model.Test', 'before_insert')
                def my_event(cls, mapper, connection, target):
                    target.val = True

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertTrue(t.val)

    def test_sqlalchemy_listen_on_column(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String()

                @listen('Model.Test=>val', 'set', retval=True)
                def my_event(cls, target, value, oldvalue, initiator):
                    return 'test_' + value

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertIsNone(t.val)
        t.val = 'test'
        registry.flush()
        self.assertEqual(t.val, 'test_test')


class TestAutoORMEvent(DBTestCase):

    def test_before_insert_orm_event(self):

        listen_called = False
        id_value = 0

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

                @classmethod
                def before_insert_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called, id_value
                    listen_called = True
                    id_value = target.id

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        self.assertEqual(id_value, 0)
        registry.Test.insert()
        self.assertTrue(listen_called)
        self.assertIsNone(id_value)

    def test_before_insert_orm_event_on_mixin(self):

        listen_called = False
        id_value = 0

        def add_in_registry():

            @register(Mixin)
            class MTest:

                @classmethod
                def before_insert_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called, id_value
                    listen_called = True
                    id_value = target.id

            @register(Model)
            class Test(Mixin.MTest):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        self.assertEqual(id_value, 0)
        registry.Test.insert()
        self.assertTrue(listen_called)
        self.assertIsNone(id_value)

    def test_before_insert_orm_event_on_core(self):

        def add_in_registry():

            @register(Core)
            class SqlBase:

                @classmethod
                def before_insert_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called
                    listen_called = True

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        listen_called = False
        self.assertFalse(listen_called)
        registry.Test.insert()
        self.assertTrue(listen_called)

    def test_before_insert_orm_event_is_not_metaclass(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

                def before_insert_orm_event(cls, mapper, connection, target):
                    pass

        with self.assertRaises(ORMEventException):
            self.init_registry(add_in_registry)

    def test_after_insert_orm_event(self):

        listen_called = False
        id_value = 0

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

                @classmethod
                def after_insert_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called, id_value
                    listen_called = True
                    id_value = target.id

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        self.assertEqual(id_value, 0)
        t = registry.Test.insert()
        self.assertTrue(listen_called)
        self.assertEqual(id_value, t.id)

    def test_before_update_orm_event(self):

        listen_called = False

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                name = String()

                @classmethod
                def before_update_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called
                    listen_called = True

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        t = registry.Test.insert()
        self.assertFalse(listen_called)
        t.name = 'test'
        registry.flush()
        self.assertTrue(listen_called)

    def test_after_update_orm_event(self):

        listen_called = False

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                name = String()

                @classmethod
                def after_update_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called
                    listen_called = True

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        t = registry.Test.insert()
        self.assertFalse(listen_called)
        t.name = 'test'
        registry.flush()
        self.assertTrue(listen_called)

    def test_before_delete_orm_event(self):

        listen_called = False

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

                @classmethod
                def before_delete_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called
                    listen_called = True

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        t = registry.Test.insert()
        self.assertFalse(listen_called)
        t.delete()
        self.assertTrue(listen_called)

    def test_after_delete_orm_event(self):

        listen_called = False

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

                @classmethod
                def after_delete_orm_event(cls, mapper, connection, target):
                    nonlocal listen_called
                    listen_called = True

        registry = self.init_registry(add_in_registry)
        self.assertFalse(listen_called)
        t = registry.Test.insert()
        self.assertFalse(listen_called)
        t.delete()
        self.assertTrue(listen_called)
