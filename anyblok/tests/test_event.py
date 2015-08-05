# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


class TestEvent(DBTestCase):

    def check_event(self):
        self.assertEqual(self.registry.Test.x, 0)
        self.registry.Event.fire('fireevent')
        self.assertEqual(self.registry.Test.x, 1)
        self.registry.Event.fire('fireevent', a=2, b=2)
        self.assertEqual(self.registry.Test.x, 4)
        self.registry.Event.fire('fireevent')
        self.assertEqual(self.registry.Test.x, 1)

    def test_simple_event_from_model(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Model)
            class Test:

                x = 0

                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

        self.reload_registry_with(add_in_registry)
        self.check_event()

    def test_simple_event_from_model_by_name(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Model)
            class Test:

                x = 0

                @Declarations.addListener('Model.Event', 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

        self.reload_registry_with(add_in_registry)
        self.assertEqual(len(self.registry.events['Model.Event']['fireevent']),
                         1)
        self.check_event()

    def test_simple_event_from_mixin(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Mixin)
            class MTest:

                x = 0

                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

            @register(Model)
            class Test(Mixin.MTest):
                pass

        self.reload_registry_with(add_in_registry)
        self.assertEqual(len(self.registry.events['Model.Event']['fireevent']),
                         1)
        self.check_event()

    def test_simple_event_from_core(self):

        def add_in_registry():

            @register(Model)
            class Event:
                pass

            @register(Core)
            class Base:

                x = 0

                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

            @register(Model)
            class Test:
                pass

        self.reload_registry_with(add_in_registry)
        self.check_event()

    def add_in_registry_inherited(self, withcore=False, withmixin=False,
                                  withmodel=False):

        @register(Model)
        class Event:
            pass

        @register(Core)
        class Base:

            x = 0

            if withcore:
                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    pass

        @register(Mixin)
        class MTest:

            if withmixin:
                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    pass

        @register(Model)
        class Test(Mixin.MTest):

            if withmodel:
                @Declarations.addListener(Model.Event, 'fireevent')
                def my_event(cls, a=1, b=1):
                    cls.x = a * b
            else:
                @classmethod
                def my_event(cls, a=1, b=1):
                    cls.x = a * b

    def test_inherited_without_event(self):
        self.reload_registry_with(self.add_in_registry_inherited)
        self.assertEqual(self.registry.Test.x, 0)
        self.registry.Event.fire('fireevent')
        self.assertEqual(self.registry.Test.x, 0)
        self.registry.Event.fire('fireevent', a=2, b=2)
        self.assertEqual(self.registry.Test.x, 0)
        self.registry.Event.fire('fireevent')
        self.assertEqual(self.registry.Test.x, 0)

    def test_inherited_with_event_on_core(self):
        self.reload_registry_with(self.add_in_registry_inherited,
                                  withcore=True)
        self.check_event()

    def test_inherited_with_event_on_mixin(self):
        self.reload_registry_with(self.add_in_registry_inherited,
                                  withmixin=True)
        self.assertEqual(
            len(self.registry.events['Model.Event']['fireevent']), 1)
        self.check_event()

    def test_inherited_with_event_on_core_and_mixin(self):
        self.reload_registry_with(self.add_in_registry_inherited,
                                  withcore=True, withmixin=True)
        self.check_event()

    def test_inherited_with_event_on_mixin_and_model(self):
        self.reload_registry_with(self.add_in_registry_inherited,
                                  withmodel=True, withmixin=True)
        self.assertEqual(
            len(self.registry.events['Model.Event']['fireevent']), 1)
        self.check_event()
