# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.environment import (EnvironmentManager,
                                 ThreadEnvironment,
                                 EnvironmentException)


class MockEnvironment:

    values = {}

    @classmethod
    def scoped_function_for_session(cls):
        return cls.__name__

    @classmethod
    def setter(cls, key, value):
        cls.values[key] = value

    @classmethod
    def getter(cls, key, default):
        return cls.values.get(key, default)


class TestEnvironment:

    @pytest.fixture(autouse=True)
    def wrapper(self, request):

        def reset():
            EnvironmentManager.define_environment_cls(ThreadEnvironment)

        request.addfinalizer(reset)
        EnvironmentManager.define_environment_cls(MockEnvironment)

    def test_set_and_get_variable(self):
        db_name = 'test db name'
        EnvironmentManager.set('db_name', db_name)
        assert EnvironmentManager.get('db_name') == db_name

    def test_without_environment_for_set(self):
        # don't use define_environment_cls, because she must be verify
        EnvironmentManager.environment = None
        try:
            EnvironmentManager.set('db_name', 'test')
            self.fail('No watchdog for None environment')
        except EnvironmentException:
            pass

    def test_without_environment_for_get(self):
        # don't use define_environment_cls, because she must be verify
        EnvironmentManager.environment = None
        try:
            EnvironmentManager.get('db_name')
            self.fail('No watchdog for None environment')
        except EnvironmentException:
            pass

    def test_scoped_function_session(self):
        getted = EnvironmentManager.scoped_function_for_session()
        wanted = MockEnvironment.scoped_function_for_session
        assert getted == wanted

    def check_bad_define_environment(self, env):
        try:
            EnvironmentManager.define_environment_cls(env)
            self.fail("Bad environment class")
        except EnvironmentException:
            pass

    def test_bad_define_environment_scoped_function_session(self):

        class Env:

            @classmethod
            def setter(cls, key, value):
                pass

            @classmethod
            def getter(cls, key, default):
                pass

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            scoped_function_for_session = 'other'

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            def scoped_function_for_session(self):
                pass

        self.check_bad_define_environment(Env)

    def test_bad_define_environment_setter(self):

        class Env:

            @classmethod
            def scoped_function_for_session(cls):
                pass

            @classmethod
            def getter(cls, key, default):
                pass

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            setter = None

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            def setter(self, key, value):
                pass

        self.check_bad_define_environment(Env)

    def test_bad_define_environment_getter(self):

        class Env:

            @classmethod
            def scoped_function_for_session(cls):
                pass

            @classmethod
            def setter(cls, key, value):
                pass

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            getter = None

        self.check_bad_define_environment(Env)

        class Env(MockEnvironment):

            def getter(self, key, default):
                pass

        self.check_bad_define_environment(Env)


class TestThreadEnvironment:

    def test_set_and_get_variable(self):
        db_name = 'test db name'
        EnvironmentManager.set('db_name', db_name)
        assert EnvironmentManager.get('db_name') == db_name

    def test_scoped_function_session(self):
        assert EnvironmentManager.scoped_function_for_session() is None
