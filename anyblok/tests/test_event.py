# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.declarations import Declarations, listen
from anyblok.column import Integer, Boolean, String


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
