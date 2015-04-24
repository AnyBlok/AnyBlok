# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.environment import EnvironmentManager


class TestRegistryCore(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryCore, cls).setUpClass()
        RegistryManager.declare_core('test')
        RegistryManager.init_blok('testCore')
        EnvironmentManager.set('current_blok', 'testCore')

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryCore, cls).tearDownClass()
        EnvironmentManager.set('current_blok', None)
        del RegistryManager.loaded_bloks['testCore']
        RegistryManager.undeclare_core('test')

    def tearDown(self):
        super(TestRegistryCore, self).tearDown()
        RegistryManager.loaded_bloks['testCore']['Core']['test'] = []

    def assertInCore(self, *args):
        blokname = 'testCore'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Core']['test']), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Core']['test']
            self.assertEqual(hasCls, True)

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_core_in_register('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_register('testCore', 'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        def has_test_in_removed():
            core = RegistryManager.loaded_bloks['testCore']['removed']
            if test in core:
                return True

            return False

        RegistryManager.add_core_in_register('test', test)
        self.assertInCore(test)
        self.assertEqual(has_test_in_removed(), False)
        RegistryManager.remove_in_register(test)
        self.assertEqual(has_test_in_removed(), True)
