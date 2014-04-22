# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager


class TestRegistry(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistry, cls).setUpClass()
        cls.init_argsparse_manager()
        cls.createdb()
        BlokManager.load('AnyBlok')

    def setUp(self):
        super(TestRegistry, self).setUp()
        self.registry = self.getRegistry()

    @classmethod
    def tearDownClass(cls):
        super(TestRegistry, cls).tearDownClass()
        BlokManager.unload()
        cls.dropdb()

    def tearDown(self):
        super(TestRegistry, self).tearDown()
        RegistryManager.clear()

    def test_get(self):
        self.registry.close()
        self.registry = self.getRegistry()

    def test_get_model(self):
        System = self.registry.get('Model.System')
        self.assertEqual(self.registry.System, System)

    def test_get_the_same_registry(self):
        registry = self.getRegistry()
        self.assertEqual(self.registry, registry)

    def test_reload(self):
        bloks_before_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.registry.reload()
        bloks_after_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)

    def test_get_bloks_to_load(self):
        bloks = self.registry.get_bloks_to_load()
        have_anyblokcore = 'anyblok-core' in bloks
        self.assertEqual(have_anyblokcore, True)

    def test_load_entry(self):
        RegistryManager.loaded_bloks['blok'] = {
            'entry': {
                'registry_names': ['key'],
                'key': {'properties': {'property': True}, 'bases': [TestCase]},
            },
        }
        self.registry.load_entry('blok', 'entry')
        self.assertEqual(self.registry.loaded_registries['key'],
                         {'properties': {'property': True},
                          'bases': [TestCase]})

    def test_load_core(self):
        RegistryManager.loaded_bloks['blok'] = {
            'Core': {'Session': [TestCase]},
        }
        self.registry.load_core('blok', 'Session')
        have_session = TestCase in self.registry.loaded_cores['Session']
        self.assertEqual(have_session, True)
