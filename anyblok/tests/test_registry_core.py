# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.environment import EnvironmentManager


class TestRegistryCore(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryCore, cls).setUpClass()
        RegistryManager.init_blok('testCore')
        EnvironmentManager.set('current_blok', 'testCore')

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryCore, cls).tearDownClass()
        EnvironmentManager.set('current_blok', None)
        del RegistryManager.loaded_bloks['testCore']

    def setUp(self):
        super(TestRegistryCore, self).setUp()
        blokname = 'testCore'
        RegistryManager.loaded_bloks[blokname]['Core']['test'] = []

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

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        def has_test_in_removed():
            core = RegistryManager.loaded_bloks['testCore']['removed']
            if test in core:
                return True

            return False

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(has_test_in_removed(), False)
        RegistryManager.remove_in_target_registry(test)
        self.assertEqual(has_test_in_removed(), True)
